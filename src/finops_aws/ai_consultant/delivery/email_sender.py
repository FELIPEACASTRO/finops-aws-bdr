"""
Email Sender

Envia relatórios FinOps por email via AWS SES.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailSender:
    """
    Enviador de emails via AWS SES
    
    Envia relatórios FinOps formatados para destinatários
    configurados.
    
    Example:
        ```python
        sender = EmailSender()
        
        sender.send_report(
            report_html="<html>...</html>",
            subject="Relatório FinOps - Novembro 2024",
            recipients=["cfo@empresa.com"]
        )
        ```
    """
    
    def __init__(
        self,
        sender_email: Optional[str] = None,
        region: str = "us-east-1",
        ses_client: Optional[Any] = None
    ):
        """
        Inicializa sender
        
        Args:
            sender_email: Email do remetente (verificado no SES)
            region: Região AWS
            ses_client: Cliente SES injetado
        """
        self.sender_email = sender_email or os.environ.get(
            'FINOPS_SENDER_EMAIL',
            'finops@empresa.com'
        )
        self.region = region
        self._ses_client = ses_client
    
    @property
    def ses_client(self):
        """Lazy loading do cliente SES"""
        if self._ses_client is None:
            self._ses_client = boto3.client(
                'ses',
                region_name=self.region
            )
        return self._ses_client
    
    def send_report(
        self,
        report_html: str,
        subject: str,
        recipients: List[str],
        cc: Optional[List[str]] = None,
        report_text: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Envia relatório por email
        
        Args:
            report_html: Conteúdo HTML do relatório
            subject: Assunto do email
            recipients: Lista de destinatários
            cc: Lista de cópias
            report_text: Versão texto do relatório
            attachments: Anexos (não suportado por SES simples)
            
        Returns:
            Dict com resultado do envio
        """
        if not recipients:
            raise ValueError("Pelo menos um destinatário é obrigatório")
        
        try:
            destination = {'ToAddresses': recipients}
            if cc:
                destination['CcAddresses'] = cc
            
            body = {'Html': {'Data': report_html, 'Charset': 'UTF-8'}}
            if report_text:
                body['Text'] = {'Data': report_text, 'Charset': 'UTF-8'}
            
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination=destination,
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': body
                }
            )
            
            message_id = response.get('MessageId')
            
            logger.info(
                f"Email enviado: {message_id} para {len(recipients)} destinatários"
            )
            
            return {
                "status": "SUCCESS",
                "message_id": message_id,
                "recipients": recipients,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_msg = e.response.get('Error', {}).get('Message', '')
            
            logger.error(f"Erro ao enviar email: {error_code} - {error_msg}")
            
            return {
                "status": "FAILED",
                "error_code": error_code,
                "error_message": error_msg,
                "recipients": recipients
            }
    
    def send_alert(
        self,
        alert_type: str,
        message: str,
        recipients: List[str],
        severity: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Envia alerta de custo por email
        
        Args:
            alert_type: Tipo do alerta (ANOMALY, BUDGET, THRESHOLD)
            message: Mensagem do alerta
            recipients: Destinatários
            severity: Severidade (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            Dict com resultado do envio
        """
        severity_colors = {
            "LOW": "#28a745",
            "MEDIUM": "#ffc107",
            "HIGH": "#fd7e14",
            "CRITICAL": "#dc3545"
        }
        
        color = severity_colors.get(severity, "#6c757d")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{ 
                    border-left: 4px solid {color}; 
                    padding: 15px; 
                    background: #f8f9fa;
                    margin: 20px 0;
                }}
                .severity {{ 
                    color: {color}; 
                    font-weight: bold; 
                    text-transform: uppercase;
                }}
            </style>
        </head>
        <body>
            <h2>🚨 Alerta FinOps AWS</h2>
            
            <div class="alert-box">
                <p><strong>Tipo:</strong> {alert_type}</p>
                <p><strong>Severidade:</strong> <span class="severity">{severity}</span></p>
                <p><strong>Mensagem:</strong></p>
                <p>{message}</p>
            </div>
            
            <p><small>Gerado em {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')} 
            por FinOps AWS AI Consultant</small></p>
        </body>
        </html>
        """
        
        subject = f"[{severity}] Alerta FinOps: {alert_type}"
        
        return self.send_report(
            report_html=html_content,
            subject=subject,
            recipients=recipients
        )
    
    def send_weekly_digest(
        self,
        summary: Dict[str, Any],
        recipients: List[str]
    ) -> Dict[str, Any]:
        """
        Envia digest semanal
        
        Args:
            summary: Resumo da semana
            recipients: Destinatários
            
        Returns:
            Dict com resultado do envio
        """
        total_cost = summary.get('total_cost', 0)
        change_pct = summary.get('change_percentage', 0)
        top_services = summary.get('top_services', [])[:5]
        recommendations = summary.get('recommendations', [])[:3]
        
        services_html = ""
        for svc in top_services:
            services_html += f"""
            <tr>
                <td>{svc.get('name', 'N/A')}</td>
                <td>${svc.get('cost', 0):,.2f}</td>
                <td>{svc.get('percentage', 0):.1f}%</td>
            </tr>
            """
        
        recs_html = ""
        for rec in recommendations:
            recs_html += f"""
            <li>
                <strong>{rec.get('title', rec.get('description', '')[:50])}</strong><br>
                Economia estimada: ${rec.get('estimated_savings', 0):,.2f}/mês
            </li>
            """
        
        change_color = "#dc3545" if change_pct > 0 else "#28a745"
        change_icon = "📈" if change_pct > 0 else "📉"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #232f3e; }}
                .metric {{ display: inline-block; margin: 10px; text-align: center; padding: 15px; background: #f7f7f7; border-radius: 8px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #232f3e; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>📊 Digest Semanal FinOps</h1>
            
            <div>
                <div class="metric">
                    <div class="metric-value">${total_cost:,.2f}</div>
                    <div class="metric-label">Custo Total</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: {change_color}">
                        {change_icon} {change_pct:+.1f}%
                    </div>
                    <div class="metric-label">vs Semana Anterior</div>
                </div>
            </div>
            
            <h2>Top 5 Serviços</h2>
            <table>
                <tr>
                    <th>Serviço</th>
                    <th>Custo</th>
                    <th>% Total</th>
                </tr>
                {services_html}
            </table>
            
            <h2>Top Recomendações</h2>
            <ol>
                {recs_html}
            </ol>
            
            <hr>
            <p><small>FinOps AWS AI Consultant - {datetime.utcnow().strftime('%d/%m/%Y')}</small></p>
        </body>
        </html>
        """
        
        subject = f"📊 Digest Semanal FinOps - ${total_cost:,.0f} ({change_pct:+.1f}%)"
        
        return self.send_report(
            report_html=html_content,
            subject=subject,
            recipients=recipients
        )
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verifica email no SES
        
        Args:
            email: Email para verificar
            
        Returns:
            Dict com status
        """
        try:
            self.ses_client.verify_email_identity(
                EmailAddress=email
            )
            
            return {
                "status": "VERIFICATION_SENT",
                "email": email
            }
            
        except ClientError as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
