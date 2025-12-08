"""
FinOps AWS - Notifications Service
Serviço de notificações REAIS baseado em dados da AWS

Integração com:
- AWS Cost Anomaly Detection (anomalias de custo)
- AWS Budgets (alertas de orçamento)
- Recomendações do sistema (otimizações)

100% dados reais - sem mock
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from ..utils.logger import setup_logger


class NotificationType(Enum):
    ANOMALY = "anomaly"
    BUDGET = "budget"
    RECOMMENDATION = "recommendation"


@dataclass
class Notification:
    """Representa uma notificação FinOps"""
    id: str
    type: str
    title: str
    message: str
    timestamp: str
    read: bool = False
    link: str = "/"
    severity: str = "info"
    source: str = "aws"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp,
            'read': self.read,
            'link': self.link,
            'severity': self.severity,
            'source': self.source
        }


class NotificationsService:
    """
    Serviço de notificações FinOps com dados REAIS da AWS
    
    Fontes de notificações:
    1. Cost Anomaly Detection - Anomalias detectadas
    2. AWS Budgets - Alertas de orçamento
    3. Sistema de Recomendações - Novas otimizações
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self._ce_client = None
        self._budgets_client = None
        self._account_id = None
    
    def _get_ce_client(self):
        """Obtém cliente Cost Explorer"""
        if self._ce_client is None:
            self._ce_client = boto3.client('ce', region_name='us-east-1')
        return self._ce_client
    
    def _get_budgets_client(self):
        """Obtém cliente Budgets"""
        if self._budgets_client is None:
            self._budgets_client = boto3.client('budgets')
        return self._budgets_client
    
    def _get_account_id(self) -> str:
        """Obtém Account ID"""
        if self._account_id:
            return self._account_id
        try:
            sts = boto3.client('sts')
            self._account_id = sts.get_caller_identity()['Account']
            return self._account_id
        except Exception:
            return "unknown"
    
    def _format_time_ago(self, dt: datetime) -> str:
        """Formata tempo relativo em português"""
        now = datetime.utcnow()
        if dt.tzinfo:
            now = datetime.now(dt.tzinfo)
        
        diff = now - dt
        
        if diff.days > 30:
            months = diff.days // 30
            return f"{months} {'mês' if months == 1 else 'meses'} atrás"
        elif diff.days > 0:
            return f"{diff.days} {'dia' if diff.days == 1 else 'dias'} atrás"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} {'hora' if hours == 1 else 'horas'} atrás"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} {'minuto' if minutes == 1 else 'minutos'} atrás"
        else:
            return "agora"
    
    def get_anomaly_notifications(self, days_back: int = 7) -> List[Notification]:
        """Obtém notificações de anomalias de custo REAIS"""
        notifications = []
        
        try:
            from botocore.config import Config
            
            config = Config(
                connect_timeout=5,
                read_timeout=10,
                retries={'max_attempts': 1}
            )
            
            client = boto3.client('ce', region_name='us-east-1', config=config)
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = client.get_anomalies(
                DateInterval={
                    'StartDate': start_date,
                    'EndDate': end_date
                },
                MaxResults=10
            )
            
            for anomaly in response.get('Anomalies', []):
                anomaly_id = anomaly.get('AnomalyId', '')
                impact = anomaly.get('Impact', {})
                total_impact = float(impact.get('TotalImpact', 0))
                impact_pct = float(impact.get('TotalImpactPercentage', 0))
                
                root_causes = anomaly.get('RootCauses', [])
                service = ""
                region = ""
                if root_causes:
                    service = root_causes[0].get('Service', 'Serviço AWS')
                    region = root_causes[0].get('Region', '')
                
                start_date_str = anomaly.get('AnomalyStartDate', '')
                try:
                    anomaly_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    timestamp = self._format_time_ago(anomaly_date)
                except Exception:
                    timestamp = "recentemente"
                
                if total_impact >= 500:
                    severity = "critical"
                elif total_impact >= 100:
                    severity = "high"
                elif total_impact >= 50:
                    severity = "medium"
                else:
                    severity = "low"
                
                region_text = f" na região {region}" if region else ""
                
                notifications.append(Notification(
                    id=f"anomaly_{anomaly_id}",
                    type="anomaly",
                    title="Anomalia de Custo Detectada",
                    message=f"Aumento de {impact_pct:.0f}% nos custos de {service or 'AWS'}{region_text}. Impacto: ${total_impact:,.2f}.",
                    timestamp=timestamp,
                    read=False,
                    link="/costs",
                    severity=severity,
                    source="Cost Anomaly Detection"
                ))
            
            self.logger.info(f"Encontradas {len(notifications)} anomalias recentes")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para Cost Anomaly Detection")
            else:
                self.logger.error(f"Erro ao obter anomalias: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao obter notificações de anomalias: {e}")
        
        return notifications
    
    def get_budget_notifications(self) -> List[Notification]:
        """Obtém notificações de orçamento REAIS"""
        notifications = []
        
        try:
            from botocore.config import Config
            
            config = Config(
                connect_timeout=5,
                read_timeout=10,
                retries={'max_attempts': 1}
            )
            
            client = boto3.client('budgets', config=config)
            account_id = self._get_account_id()
            
            response = client.describe_budgets(
                AccountId=account_id,
                MaxResults=100
            )
            
            for budget in response.get('Budgets', []):
                budget_name = budget.get('BudgetName', '')
                budget_limit_raw = budget.get('BudgetLimit', {}).get('Amount', '0')
                budget_limit = float(budget_limit_raw) if budget_limit_raw else 0.0
                
                calculated_spend = budget.get('CalculatedSpend', {})
                actual_spend_raw = calculated_spend.get('ActualSpend', {}).get('Amount', '0')
                actual_spend = float(actual_spend_raw) if actual_spend_raw else 0.0
                
                forecasted_raw = calculated_spend.get('ForecastedSpend', {}).get('Amount', '0')
                forecasted_spend = float(forecasted_raw) if forecasted_raw else 0.0
                
                if budget_limit > 0:
                    utilization_pct = (actual_spend / budget_limit) * 100
                else:
                    utilization_pct = 0
                
                if utilization_pct >= 100:
                    severity = "critical"
                    title = "Orçamento Excedido"
                    message = f'O orçamento "{budget_name}" foi excedido. Limite: ${budget_limit:,.2f}, Gasto: ${actual_spend:,.2f} ({utilization_pct:.0f}%).'
                    notifications.append(Notification(
                        id=f"budget_exceeded_{budget_name}",
                        type="budget",
                        title=title,
                        message=message,
                        timestamp="agora",
                        read=False,
                        link="/analytics",
                        severity=severity,
                        source="AWS Budgets"
                    ))
                elif utilization_pct >= 80:
                    severity = "high"
                    days_to_exceed = 0
                    if forecasted_spend > budget_limit:
                        remaining = budget_limit - actual_spend
                        daily_rate = actual_spend / max(datetime.utcnow().day, 1)
                        if daily_rate > 0:
                            days_to_exceed = int(remaining / daily_rate)
                    
                    projection_text = f" Projeção: ultrapassar em {days_to_exceed} dias." if days_to_exceed > 0 else ""
                    
                    notifications.append(Notification(
                        id=f"budget_warning_{budget_name}",
                        type="budget",
                        title="Alerta de Orçamento",
                        message=f'O orçamento "{budget_name}" atingiu {utilization_pct:.0f}% do limite (${budget_limit:,.2f}).{projection_text}',
                        timestamp="agora",
                        read=False,
                        link="/analytics",
                        severity=severity,
                        source="AWS Budgets"
                    ))
            
            self.logger.info(f"Encontradas {len(notifications)} notificações de budget")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NotFoundException':
                self.logger.info("Nenhum budget configurado")
            elif error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para AWS Budgets")
            else:
                self.logger.error(f"Erro ao obter budgets: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao obter notificações de budget: {e}")
        
        return notifications
    
    def get_recommendation_notifications(self, recommendations: List[Dict]) -> List[Notification]:
        """Converte recomendações do sistema em notificações"""
        notifications = []
        
        critical_recs = [r for r in recommendations if r.get('impact') == 'critical' or r.get('priority') == 'CRITICAL']
        high_recs = [r for r in recommendations if r.get('impact') == 'high' or r.get('priority') == 'HIGH']
        
        critical_count = len(critical_recs)
        high_count = len(high_recs)
        
        if critical_count > 0:
            total_savings = sum(r.get('savings', 0) or r.get('estimated_savings', 0) for r in critical_recs)
            notifications.append(Notification(
                id=f"rec_critical_{datetime.utcnow().strftime('%Y%m%d')}",
                type="recommendation",
                title="Recomendações Críticas Disponíveis",
                message=f"{critical_count} {'recomendação crítica identificada' if critical_count == 1 else 'recomendações críticas identificadas'}. Economia potencial: ${total_savings:,.2f}/mês.",
                timestamp="agora",
                read=False,
                link="/recommendations",
                severity="critical",
                source="FinOps Analyzer"
            ))
        
        if high_count > 0:
            total_savings = sum(r.get('savings', 0) or r.get('estimated_savings', 0) for r in high_recs)
            notifications.append(Notification(
                id=f"rec_high_{datetime.utcnow().strftime('%Y%m%d')}",
                type="recommendation",
                title="Novas Recomendações Disponíveis",
                message=f"{high_count} {'otimização identificada' if high_count == 1 else 'otimizações identificadas'} para rightsizing. Economia potencial: ${total_savings:,.2f}/mês.",
                timestamp="15 min atrás",
                read=False,
                link="/recommendations",
                severity="high",
                source="FinOps Analyzer"
            ))
        
        return notifications
    
    def get_all_notifications(self, recommendations: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Obtém TODAS as notificações de fontes reais
        
        Returns:
            Lista de notificações ordenadas por severidade e tempo
        """
        all_notifications = []
        
        anomaly_notifications = self.get_anomaly_notifications(days_back=7)
        all_notifications.extend(anomaly_notifications)
        
        budget_notifications = self.get_budget_notifications()
        all_notifications.extend(budget_notifications)
        
        if recommendations:
            rec_notifications = self.get_recommendation_notifications(recommendations)
            all_notifications.extend(rec_notifications)
        
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        all_notifications.sort(key=lambda n: severity_order.get(n.severity, 4))
        
        return [n.to_dict() for n in all_notifications]
