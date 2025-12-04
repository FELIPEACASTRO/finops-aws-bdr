"""
Q Business Report Handler

Lambda handler para geração de relatórios FinOps com Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from .q_business import QBusinessClient, QBusinessConfig, QBusinessChat, QBusinessDataSource
from .prompts import PromptBuilder, PromptPersona
from .processors import DataFormatter, ResponseParser, ReportStructurer
from .delivery import EmailSender, SlackNotifier
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class QReportHandler:
    """
    Handler para geração de relatórios com Amazon Q Business
    
    Orquestra o fluxo completo:
    1. Recebe dados de custo do Aggregator
    2. Formata e envia para Q Business
    3. Parseia resposta
    4. Estrutura relatório
    5. Entrega (S3, email, Slack)
    """
    
    def __init__(
        self,
        config: Optional[QBusinessConfig] = None,
        q_client: Optional[QBusinessClient] = None
    ):
        """
        Inicializa handler
        
        Args:
            config: Configuração Q Business
            q_client: Cliente Q Business injetado
        """
        self.config = config or QBusinessConfig.from_env()
        self.client = q_client or QBusinessClient(self.config)
        self.chat = QBusinessChat(self.config, self.client)
        self.data_source = QBusinessDataSource(self.config)
        
        self.formatter = DataFormatter()
        self.parser = ResponseParser()
        self.structurer = ReportStructurer()
        
        self.email_sender = EmailSender()
        self.slack = SlackNotifier()
    
    def handle(self, event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        Handler principal do Lambda
        
        Args:
            event: Evento Lambda com dados de custo
            context: Contexto Lambda
            
        Returns:
            Dict com resultado da geração
        """
        logger.info("Iniciando geração de relatório Q Business")
        
        try:
            request_type = event.get('type', 'full_report')
            cost_data = event.get('cost_data', {})
            period = event.get('period', self._get_default_period())
            persona = self._get_persona(event.get('persona', 'executive'))
            
            formatted_data = self.formatter.format_cost_report(cost_data)
            
            if request_type == 'full_report':
                result = self._generate_full_report(formatted_data, period, persona)
            elif request_type == 'quick_analysis':
                result = self._generate_quick_analysis(formatted_data, period)
            elif request_type == 'question':
                question = event.get('question', 'Analise os custos')
                result = self._answer_question(formatted_data, question)
            else:
                result = self._generate_full_report(formatted_data, period, persona)
            
            self._deliver_report(result, event)
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "SUCCESS",
                    "report_id": result.get('report_id'),
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": result.get('executive_summary', '')[:500]
                }, default=str)
            }
            
        except Exception as e:
            logger.error(f"Erro na geração de relatório: {e}")
            
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "ERROR",
                    "error": str(e)
                })
            }
    
    def _generate_full_report(
        self,
        formatted_data,
        period: str,
        persona: PromptPersona
    ) -> Dict[str, Any]:
        """Gera relatório completo"""
        from .q_business.chat import FinOpsAnalysisRequest
        
        request = FinOpsAnalysisRequest(
            cost_data=formatted_data.to_dict(),
            period=period,
            persona=persona,
            include_recommendations=True,
            include_trends=True,
            include_anomalies=True
        )
        
        response = self.chat.analyze_costs(request)
        
        parsed = self.parser.parse(response.report)
        
        structured = self.structurer.to_markdown(parsed.to_dict())
        
        import uuid
        report_id = str(uuid.uuid4())[:8]
        
        return {
            "report_id": report_id,
            "executive_summary": parsed.executive_summary,
            "recommendations": parsed.recommendations,
            "quick_wins": parsed.quick_wins,
            "risks": parsed.risks,
            "full_report": structured.content,
            "format": "markdown",
            "conversation_id": response.conversation_id
        }
    
    def _generate_quick_analysis(
        self,
        formatted_data,
        period: str
    ) -> Dict[str, Any]:
        """Gera análise rápida"""
        prompt = PromptBuilder().build_analysis_prompt(
            cost_data=formatted_data.to_dict(),
            period=period,
            persona=PromptPersona.EXECUTIVE,
            include_recommendations=True,
            include_trends=False,
            include_anomalies=False
        )
        
        prompt = prompt[:2000]
        
        response = self.client.chat(prompt)
        
        import uuid
        
        return {
            "report_id": str(uuid.uuid4())[:8],
            "executive_summary": response.message[:500],
            "recommendations": [],
            "quick_wins": [],
            "risks": [],
            "full_report": response.message,
            "format": "text"
        }
    
    def _answer_question(
        self,
        formatted_data,
        question: str
    ) -> Dict[str, Any]:
        """Responde pergunta específica"""
        response = self.chat.ask_question(
            question=question,
            context=formatted_data.to_dict()
        )
        
        import uuid
        
        return {
            "report_id": str(uuid.uuid4())[:8],
            "answer": response.message,
            "full_report": response.message,
            "format": "text"
        }
    
    def _deliver_report(
        self,
        result: Dict[str, Any],
        event: Dict[str, Any]
    ) -> None:
        """Entrega relatório pelos canais configurados"""
        delivery_config = event.get('delivery', {})
        
        if delivery_config.get('s3', True):
            self._save_to_s3(result)
        
        email_recipients = delivery_config.get('email', [])
        if email_recipients:
            html_report = self.structurer.to_html({
                "executive_summary": result.get('executive_summary'),
                "recommendations": result.get('recommendations', []),
                "quick_wins": result.get('quick_wins', []),
                "risks": result.get('risks', [])
            })
            
            self.email_sender.send_report(
                report_html=html_report.content,
                subject=f"Relatório FinOps - {result.get('report_id')}",
                recipients=email_recipients
            )
        
        if delivery_config.get('slack', False):
            summary = event.get('cost_data', {}).get('summary', {})
            
            self.slack.send_report_summary(
                total_cost=summary.get('total_cost', 0),
                change_pct=summary.get('change_percentage', 0),
                period=event.get('period', 'N/A'),
                top_recommendations=result.get('recommendations', [])[:3]
            )
    
    def _save_to_s3(self, result: Dict[str, Any]) -> str:
        """Salva relatório no S3"""
        import boto3
        
        if not self.config.s3_bucket:
            logger.warning("S3 bucket não configurado")
            return ""
        
        s3 = boto3.client('s3')
        
        report_id = result.get('report_id', 'unknown')
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        s3_key = f"reports/{date_prefix}/report_{report_id}.md"
        
        try:
            s3.put_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key,
                Body=result.get('full_report', '').encode('utf-8'),
                ContentType='text/markdown',
                Metadata={
                    'report-id': report_id,
                    'generated-at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Relatório salvo: s3://{self.config.s3_bucket}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Erro ao salvar relatório no S3: {e}")
            return ""
    
    def _get_default_period(self) -> str:
        """Retorna período padrão (últimos 30 dias)"""
        from datetime import timedelta
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        return f"{start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}"
    
    def _get_persona(self, persona_str: str) -> PromptPersona:
        """Converte string para PromptPersona"""
        persona_map = {
            'executive': PromptPersona.EXECUTIVE,
            'ceo': PromptPersona.EXECUTIVE,
            'cfo': PromptPersona.EXECUTIVE,
            'cto': PromptPersona.CTO,
            'devops': PromptPersona.DEVOPS,
            'sre': PromptPersona.DEVOPS,
            'analyst': PromptPersona.ANALYST,
            'finops': PromptPersona.ANALYST
        }
        
        return persona_map.get(persona_str.lower(), PromptPersona.EXECUTIVE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Entry point do Lambda
    
    Args:
        event: Evento Lambda
        context: Contexto Lambda
        
    Returns:
        Resposta do Lambda
    """
    handler = QReportHandler()
    return handler.handle(event, context)
