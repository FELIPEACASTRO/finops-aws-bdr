"""
Slack Notifier

Envia notificações FinOps para Slack via Webhooks.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import urllib.request
import urllib.error

from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class SlackNotifier:
    """
    Notificador Slack para FinOps
    
    Envia mensagens formatadas com blocos ricos
    para canais Slack via Webhooks.
    
    Example:
        ```python
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/...")
        
        notifier.send_report_summary(
            total_cost=47523.89,
            change_pct=12.3,
            top_recommendations=[...]
        )
        ```
    """
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        channel: Optional[str] = None,
        username: str = "FinOps AWS Bot"
    ):
        """
        Inicializa notificador
        
        Args:
            webhook_url: URL do webhook Slack
            channel: Canal destino (opcional, usa padrão do webhook)
            username: Nome do bot
        """
        self.webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK_URL')
        self.channel = channel
        self.username = username
    
    def send_message(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem para Slack
        
        Args:
            text: Texto fallback da mensagem
            blocks: Blocos ricos (opcional)
            
        Returns:
            Dict com resultado do envio
        """
        if not self.webhook_url:
            logger.warning("Slack webhook não configurado")
            return {"status": "SKIPPED", "reason": "No webhook configured"}
        
        payload = {
            "text": text,
            "username": self.username,
            "icon_emoji": ":chart_with_upwards_trend:"
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        if blocks:
            payload["blocks"] = blocks
        
        try:
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_text = response.read().decode('utf-8')
            
            logger.info("Mensagem Slack enviada com sucesso")
            
            return {
                "status": "SUCCESS",
                "response": response_text,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except urllib.error.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar para Slack: {e.code}")
            return {
                "status": "FAILED",
                "error_code": e.code,
                "error_message": str(e)
            }
        except urllib.error.URLError as e:
            logger.error(f"Erro de conexão com Slack: {e.reason}")
            return {
                "status": "FAILED",
                "error_message": str(e.reason)
            }
        except Exception as e:
            logger.error(f"Erro ao enviar para Slack: {e}")
            return {
                "status": "FAILED",
                "error_message": str(e)
            }
    
    def send_report_summary(
        self,
        total_cost: float,
        change_pct: float,
        period: str,
        top_recommendations: List[Dict[str, Any]],
        quick_wins: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Envia resumo do relatório FinOps
        
        Args:
            total_cost: Custo total do período
            change_pct: Variação percentual
            period: Período do relatório
            top_recommendations: Top recomendações
            quick_wins: Quick wins identificados
            
        Returns:
            Dict com resultado do envio
        """
        change_emoji = "📈" if change_pct > 0 else "📉"
        change_color = "#dc3545" if change_pct > 5 else ("#28a745" if change_pct < -5 else "#ffc107")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Relatório FinOps AWS",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Período:* {period}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Custo Total:*\n${total_cost:,.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Variação:*\n{change_emoji} {change_pct:+.1f}%"
                    }
                ]
            },
            {"type": "divider"}
        ]
        
        if top_recommendations:
            rec_text = "*💡 Top Oportunidades de Economia:*\n"
            for i, rec in enumerate(top_recommendations[:3], 1):
                savings = rec.get('estimated_savings', 0)
                desc = rec.get('description', '')[:50]
                rec_text += f"{i}. {desc} - *${savings:,.2f}/mês*\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": rec_text}
            })
        
        if quick_wins:
            qw_text = "*⚡ Quick Wins (7 dias):*\n"
            for qw in quick_wins[:3]:
                qw_text += f"• {qw.get('description', '')[:40]}\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": qw_text}
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Gerado por FinOps AWS AI Consultant • {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}"
                }
            ]
        })
        
        text = f"Relatório FinOps: ${total_cost:,.2f} ({change_pct:+.1f}%)"
        
        return self.send_message(text=text, blocks=blocks)
    
    def send_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "MEDIUM",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envia alerta de custo
        
        Args:
            alert_type: Tipo do alerta
            message: Mensagem do alerta
            severity: Severidade
            details: Detalhes adicionais
            
        Returns:
            Dict com resultado
        """
        severity_emojis = {
            "LOW": "💚",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }
        
        emoji = severity_emojis.get(severity, "⚪")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Alerta FinOps: {alert_type}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Severidade:* {severity}\n\n{message}"
                }
            }
        ]
        
        if details:
            detail_text = "*Detalhes:*\n"
            for key, value in details.items():
                detail_text += f"• {key}: {value}\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": detail_text}
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"⏰ {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}"}
            ]
        })
        
        text = f"[{severity}] Alerta FinOps: {alert_type}"
        
        return self.send_message(text=text, blocks=blocks)
    
    def send_anomaly_alert(
        self,
        service: str,
        expected_cost: float,
        actual_cost: float,
        anomaly_score: float
    ) -> Dict[str, Any]:
        """
        Envia alerta de anomalia de custo
        
        Args:
            service: Serviço afetado
            expected_cost: Custo esperado
            actual_cost: Custo real
            anomaly_score: Score da anomalia (0-100)
            
        Returns:
            Dict com resultado
        """
        variance = ((actual_cost - expected_cost) / expected_cost * 100) if expected_cost > 0 else 0
        
        severity = "LOW"
        if anomaly_score > 80:
            severity = "CRITICAL"
        elif anomaly_score > 60:
            severity = "HIGH"
        elif anomaly_score > 40:
            severity = "MEDIUM"
        
        message = (
            f"*Serviço:* {service}\n"
            f"*Custo esperado:* ${expected_cost:,.2f}\n"
            f"*Custo real:* ${actual_cost:,.2f}\n"
            f"*Variação:* {variance:+.1f}%\n"
            f"*Score de anomalia:* {anomaly_score:.0f}/100"
        )
        
        return self.send_alert(
            alert_type="Anomalia de Custo",
            message=message,
            severity=severity,
            details={
                "Serviço": service,
                "Impacto": f"${actual_cost - expected_cost:,.2f}"
            }
        )
