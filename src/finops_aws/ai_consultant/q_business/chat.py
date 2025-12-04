"""
Amazon Q Business Chat Service

Serviço especializado para chat com Amazon Q Business
com suporte a diferentes tipos de análise FinOps.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .client import QBusinessClient, ChatResponse
from .config import QBusinessConfig
from ..prompts import PromptBuilder, PromptPersona
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class FinOpsAnalysisRequest:
    """Requisição de análise FinOps"""
    cost_data: Dict[str, Any]
    period: str
    persona: PromptPersona = PromptPersona.EXECUTIVE
    include_recommendations: bool = True
    include_trends: bool = True
    include_anomalies: bool = True
    custom_questions: List[str] = field(default_factory=list)


@dataclass
class FinOpsAnalysisResponse:
    """Resposta da análise FinOps"""
    report: str
    executive_summary: str
    recommendations: List[Dict[str, Any]]
    quick_wins: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    generated_at: str
    conversation_id: Optional[str]
    raw_response: Optional[ChatResponse]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report": self.report,
            "executive_summary": self.executive_summary,
            "recommendations": self.recommendations,
            "quick_wins": self.quick_wins,
            "risks": self.risks,
            "generated_at": self.generated_at,
            "conversation_id": self.conversation_id
        }


class QBusinessChat:
    """
    Serviço de chat especializado para análises FinOps
    
    Combina o QBusinessClient com PromptBuilder para gerar
    análises e relatórios de otimização de custos.
    
    Example:
        ```python
        chat = QBusinessChat()
        
        request = FinOpsAnalysisRequest(
            cost_data={"total": 47523.89, ...},
            period="2024-11-01 to 2024-11-30",
            persona=PromptPersona.EXECUTIVE
        )
        
        response = chat.analyze_costs(request)
        print(response.executive_summary)
        ```
    """
    
    def __init__(
        self,
        config: Optional[QBusinessConfig] = None,
        client: Optional[QBusinessClient] = None
    ):
        """
        Inicializa serviço de chat
        
        Args:
            config: Configuração Q Business
            client: Cliente Q Business injetado
        """
        self.config = config or QBusinessConfig.from_env()
        self.client = client or QBusinessClient(self.config)
        self.prompt_builder = PromptBuilder()
    
    def analyze_costs(
        self,
        request: FinOpsAnalysisRequest
    ) -> FinOpsAnalysisResponse:
        """
        Analisa custos e gera relatório FinOps
        
        Args:
            request: Requisição de análise
            
        Returns:
            FinOpsAnalysisResponse com relatório completo
        """
        logger.info(f"Iniciando análise FinOps para período: {request.period}")
        
        prompt = self.prompt_builder.build_analysis_prompt(
            cost_data=request.cost_data,
            period=request.period,
            persona=request.persona,
            include_recommendations=request.include_recommendations,
            include_trends=request.include_trends,
            include_anomalies=request.include_anomalies
        )
        
        for question in request.custom_questions:
            prompt += f"\n\nPergunta adicional: {question}"
        
        try:
            chat_response = self.client.chat(prompt)
            
            parsed = self._parse_analysis_response(chat_response.message)
            
            return FinOpsAnalysisResponse(
                report=chat_response.message,
                executive_summary=parsed.get("executive_summary", ""),
                recommendations=parsed.get("recommendations", []),
                quick_wins=parsed.get("quick_wins", []),
                risks=parsed.get("risks", []),
                generated_at=datetime.utcnow().isoformat(),
                conversation_id=chat_response.conversation_id,
                raw_response=chat_response
            )
            
        except Exception as e:
            logger.error(f"Erro na análise FinOps: {e}")
            raise
    
    def ask_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Faz pergunta específica sobre custos
        
        Args:
            question: Pergunta do usuário
            context: Contexto adicional (dados de custo)
            conversation_id: ID de conversa existente
            
        Returns:
            ChatResponse com resposta
        """
        if context:
            full_message = self.prompt_builder.build_question_prompt(
                question=question,
                context=context
            )
        else:
            full_message = question
        
        return self.client.chat(
            message=full_message,
            conversation_id=conversation_id
        )
    
    def explain_cost_increase(
        self,
        service_name: str,
        current_cost: float,
        previous_cost: float,
        period: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Explica aumento de custo em um serviço
        
        Args:
            service_name: Nome do serviço AWS
            current_cost: Custo atual
            previous_cost: Custo período anterior
            period: Período de análise
            details: Detalhes adicionais (recursos, métricas)
            
        Returns:
            ChatResponse com explicação
        """
        change_pct = ((current_cost - previous_cost) / previous_cost * 100) if previous_cost > 0 else 0
        
        context = {
            "service": service_name,
            "current_cost": current_cost,
            "previous_cost": previous_cost,
            "change_percentage": round(change_pct, 2),
            "period": period,
            "details": details or {}
        }
        
        prompt = self.prompt_builder.build_cost_explanation_prompt(context)
        
        return self.client.chat(prompt)
    
    def get_optimization_plan(
        self,
        cost_data: Dict[str, Any],
        target_reduction: float = 20.0,
        timeframe_days: int = 90
    ) -> ChatResponse:
        """
        Gera plano de otimização personalizado
        
        Args:
            cost_data: Dados de custo atuais
            target_reduction: Meta de redução em percentual
            timeframe_days: Prazo em dias
            
        Returns:
            ChatResponse com plano de otimização
        """
        prompt = self.prompt_builder.build_optimization_plan_prompt(
            cost_data=cost_data,
            target_reduction=target_reduction,
            timeframe_days=timeframe_days
        )
        
        return self.client.chat(prompt)
    
    def compare_periods(
        self,
        current_period_data: Dict[str, Any],
        previous_period_data: Dict[str, Any],
        period_labels: tuple = ("Atual", "Anterior")
    ) -> ChatResponse:
        """
        Compara custos entre dois períodos
        
        Args:
            current_period_data: Dados do período atual
            previous_period_data: Dados do período anterior
            period_labels: Labels para os períodos
            
        Returns:
            ChatResponse com análise comparativa
        """
        prompt = self.prompt_builder.build_comparison_prompt(
            current_data=current_period_data,
            previous_data=previous_period_data,
            labels=period_labels
        )
        
        return self.client.chat(prompt)
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extrai seções estruturadas da resposta
        
        Args:
            response_text: Texto da resposta do Q Business
            
        Returns:
            Dict com seções parseadas
        """
        result = {
            "executive_summary": "",
            "recommendations": [],
            "quick_wins": [],
            "risks": []
        }
        
        lines = response_text.split('\n')
        current_section = None
        section_content = []
        
        section_markers = {
            "resumo executivo": "executive_summary",
            "executive summary": "executive_summary",
            "recomendações": "recommendations",
            "recommendations": "recommendations",
            "oportunidades": "recommendations",
            "opportunities": "recommendations",
            "quick wins": "quick_wins",
            "ações imediatas": "quick_wins",
            "riscos": "risks",
            "risks": "risks",
            "alertas": "risks"
        }
        
        for line in lines:
            line_lower = line.lower().strip()
            
            for marker, section_name in section_markers.items():
                if marker in line_lower and line.startswith('#'):
                    if current_section and section_content:
                        self._store_section(result, current_section, section_content)
                    current_section = section_name
                    section_content = []
                    break
            else:
                if current_section and line.strip():
                    section_content.append(line)
        
        if current_section and section_content:
            self._store_section(result, current_section, section_content)
        
        if not result["executive_summary"] and lines:
            intro_lines = []
            for line in lines[:10]:
                if line.strip() and not line.startswith('#'):
                    intro_lines.append(line)
                elif line.startswith('#') and intro_lines:
                    break
            result["executive_summary"] = '\n'.join(intro_lines)
        
        return result
    
    def _store_section(
        self,
        result: Dict[str, Any],
        section_name: str,
        content: List[str]
    ) -> None:
        """Armazena conteúdo de seção no resultado"""
        if section_name == "executive_summary":
            result[section_name] = '\n'.join(content)
        else:
            items = []
            current_item = []
            
            for line in content:
                if line.strip().startswith(('-', '*', '•', '1', '2', '3', '4', '5')):
                    if current_item:
                        items.append({
                            "description": '\n'.join(current_item),
                            "priority": "MEDIUM"
                        })
                    current_item = [line.lstrip('-*•0123456789. ')]
                elif current_item:
                    current_item.append(line)
            
            if current_item:
                items.append({
                    "description": '\n'.join(current_item),
                    "priority": "MEDIUM"
                })
            
            result[section_name] = items
