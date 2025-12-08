"""
FinOps AWS - Budgets Service
Análise de custos e otimização para AWS Budgets

Integração REAL com AWS Budgets API:
- Lista todos os budgets da conta
- Analisa utilização vs limite
- Detecta budgets próximos do limite
- Gera recomendações de ajuste

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Template Method: Fluxo padrão de análise
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger


@dataclass
class BudgetData:
    """Representa um budget AWS"""
    budget_name: str
    budget_type: str
    budget_limit: float
    actual_spend: float
    forecasted_spend: float
    time_unit: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    utilization_percent: float = 0.0
    status: str = "OK"
    alert_thresholds: List[float] = field(default_factory=list)
    cost_filters: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'budget_name': self.budget_name,
            'budget_type': self.budget_type,
            'budget_limit': self.budget_limit,
            'actual_spend': self.actual_spend,
            'forecasted_spend': self.forecasted_spend,
            'time_unit': self.time_unit,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'utilization_percent': self.utilization_percent,
            'status': self.status,
            'alert_thresholds': self.alert_thresholds,
            'cost_filters': self.cost_filters
        }


@dataclass 
class BudgetAlert:
    """Representa um alerta de budget"""
    budget_name: str
    alert_type: str
    threshold: float
    actual_value: float
    status: str
    notification_state: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'budget_name': self.budget_name,
            'alert_type': self.alert_type,
            'threshold': self.threshold,
            'actual_value': self.actual_value,
            'status': self.status,
            'notification_state': self.notification_state
        }


class BudgetsService(BaseAWSService):
    """
    Serviço FinOps para AWS Budgets
    
    Funcionalidades:
    - Lista budgets da conta
    - Analisa utilização e projeções
    - Detecta budgets em risco
    - Gera recomendações de ajuste
    
    AWS APIs utilizadas:
    - budgets:DescribeBudgets
    - budgets:DescribeBudgetPerformanceHistory
    - budgets:DescribeNotificationsForBudget
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "budgets"
        self._account_id = None
    
    def _get_client(self):
        """Obtém cliente boto3 para Budgets"""
        if self._client_factory:
            return self._client_factory.get_client('budgets')
        return boto3.client('budgets')
    
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
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_client()
            account_id = self._get_account_id()
            client.describe_budgets(AccountId=account_id, MaxResults=1)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para acessar AWS Budgets")
            return False
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Obtém todos os budgets da conta"""
        budgets = []
        try:
            client = self._get_client()
            account_id = self._get_account_id()
            
            paginator = client.get_paginator('describe_budgets')
            for page in paginator.paginate(AccountId=account_id):
                for budget in page.get('Budgets', []):
                    budget_data = self._parse_budget(budget)
                    budgets.append(budget_data.to_dict())
            
            self.logger.info(f"Encontrados {len(budgets)} budgets")
            return budgets
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NotFoundException':
                self.logger.info("Nenhum budget configurado na conta")
            elif error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: budgets:DescribeBudgets")
            else:
                self.logger.error(f"Erro ao listar budgets: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter recursos: {e}")
            return []
    
    def _parse_budget(self, budget: Dict) -> BudgetData:
        """Parse de um budget AWS para BudgetData"""
        budget_name = budget.get('BudgetName', '')
        budget_type = budget.get('BudgetType', '')
        time_unit = budget.get('TimeUnit', 'MONTHLY')
        
        budget_limit_raw = budget.get('BudgetLimit', {}).get('Amount', '0')
        budget_limit = float(budget_limit_raw) if budget_limit_raw else 0.0
        
        calculated_spend = budget.get('CalculatedSpend', {})
        actual_spend_raw = calculated_spend.get('ActualSpend', {}).get('Amount', '0')
        actual_spend = float(actual_spend_raw) if actual_spend_raw else 0.0
        
        forecasted_raw = calculated_spend.get('ForecastedSpend', {}).get('Amount', '0')
        forecasted_spend = float(forecasted_raw) if forecasted_raw else 0.0
        
        utilization_percent = (actual_spend / budget_limit * 100) if budget_limit > 0 else 0.0
        
        if utilization_percent >= 100:
            status = "EXCEEDED"
        elif utilization_percent >= 80:
            status = "WARNING"
        elif utilization_percent >= 50:
            status = "ON_TRACK"
        else:
            status = "OK"
        
        cost_filters = {}
        if 'CostFilters' in budget:
            cost_filters = budget['CostFilters']
        
        time_period = budget.get('TimePeriod', {})
        start_date = None
        end_date = None
        if 'Start' in time_period:
            try:
                start_date = datetime.fromisoformat(str(time_period['Start']).replace('Z', '+00:00'))
            except Exception:
                pass
        if 'End' in time_period:
            try:
                end_date = datetime.fromisoformat(str(time_period['End']).replace('Z', '+00:00'))
            except Exception:
                pass
        
        return BudgetData(
            budget_name=budget_name,
            budget_type=budget_type,
            budget_limit=budget_limit,
            actual_spend=actual_spend,
            forecasted_spend=forecasted_spend,
            time_unit=time_unit,
            start_date=start_date,
            end_date=end_date,
            utilization_percent=round(utilization_percent, 2),
            status=status,
            cost_filters=cost_filters
        )
    
    def get_budget_alerts(self, budget_name: str) -> List[BudgetAlert]:
        """Obtém alertas configurados para um budget"""
        alerts = []
        try:
            client = self._get_client()
            account_id = self._get_account_id()
            
            response = client.describe_notifications_for_budget(
                AccountId=account_id,
                BudgetName=budget_name
            )
            
            for notification in response.get('Notifications', []):
                alert = BudgetAlert(
                    budget_name=budget_name,
                    alert_type=notification.get('NotificationType', ''),
                    threshold=notification.get('Threshold', 0),
                    actual_value=0,
                    status=notification.get('NotificationState', 'OK'),
                    notification_state=notification.get('NotificationState', 'OK')
                )
                alerts.append(alert)
                
        except Exception as e:
            self.logger.error(f"Erro ao obter alertas do budget {budget_name}: {e}")
        
        return alerts
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """Obtém resumo de custos dos budgets"""
        budgets = self.get_resources()
        
        total_actual_spend = sum(b.get('actual_spend', 0) for b in budgets)
        
        cost_by_resource = {
            b.get('budget_name', 'unknown'): b.get('actual_spend', 0)
            for b in budgets
        }
        
        exceeded_count = len([b for b in budgets if b.get('status') == 'EXCEEDED'])
        warning_count = len([b for b in budgets if b.get('status') == 'WARNING'])
        
        if exceeded_count > 0:
            trend = "INCREASING"
        elif warning_count > 0:
            trend = "STABLE"
        else:
            trend = "STABLE"
        
        return ServiceCost(
            service_name='budgets',
            total_cost=round(total_actual_spend, 2),
            period_days=period_days,
            cost_by_resource=cost_by_resource,
            trend=trend,
            currency='USD'
        )
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas dos budgets"""
        budgets = self.get_resources()
        
        if not budgets:
            return ServiceMetrics(
                service_name='budgets',
                resource_count=0,
                metrics={},
                utilization=None
            )
        
        utilizations = [b.get('utilization_percent', 0) for b in budgets]
        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        
        statuses = {}
        for b in budgets:
            status = b.get('status', 'UNKNOWN')
            statuses[status] = statuses.get(status, 0) + 1
        
        return ServiceMetrics(
            service_name='budgets',
            resource_count=len(budgets),
            metrics={
                'avg_utilization_percent': round(avg_utilization, 2),
                'max_utilization_percent': max(utilizations) if utilizations else 0,
                'min_utilization_percent': min(utilizations) if utilizations else 0,
                'budgets_by_status': statuses,
                'exceeded_budgets': statuses.get('EXCEEDED', 0),
                'warning_budgets': statuses.get('WARNING', 0)
            },
            utilization=round(avg_utilization, 2)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para budgets"""
        recommendations: List[ServiceRecommendation] = []
        budgets = self.get_resources()
        
        for budget in budgets:
            budget_name = budget.get('budget_name', '')
            status = budget.get('status', '')
            utilization = budget.get('utilization_percent', 0)
            actual_spend = budget.get('actual_spend', 0)
            budget_limit = budget.get('budget_limit', 0)
            forecasted = budget.get('forecasted_spend', 0)
            
            if status == 'EXCEEDED':
                recommendations.append(ServiceRecommendation(
                    resource_id=budget_name,
                    resource_type='budget',
                    recommendation_type='BUDGET_EXCEEDED',
                    description=(
                        f'O budget "{budget_name}" foi excedido. '
                        f'Limite: ${budget_limit:,.2f}, Gasto atual: ${actual_spend:,.2f} '
                        f'({utilization:.1f}% do limite). '
                        f'Ação imediata necessária para controlar custos.'
                    ),
                    estimated_savings=actual_spend - budget_limit,
                    priority='CRITICAL',
                    title=f'Budget "{budget_name}" EXCEDIDO',
                    action='Revisar gastos e implementar controles de custo imediatamente'
                ))
            
            elif status == 'WARNING':
                recommendations.append(ServiceRecommendation(
                    resource_id=budget_name,
                    resource_type='budget',
                    recommendation_type='BUDGET_WARNING',
                    description=(
                        f'O budget "{budget_name}" está em {utilization:.1f}% do limite. '
                        f'Limite: ${budget_limit:,.2f}, Gasto atual: ${actual_spend:,.2f}. '
                        f'Previsão: ${forecasted:,.2f}. '
                        f'Recomenda-se revisar gastos para evitar exceder o limite.'
                    ),
                    estimated_savings=forecasted - budget_limit if forecasted > budget_limit else 0,
                    priority='HIGH',
                    title=f'Budget "{budget_name}" próximo do limite',
                    action='Revisar e otimizar gastos antes do fim do período'
                ))
            
            if forecasted > budget_limit * 1.1:
                recommendations.append(ServiceRecommendation(
                    resource_id=budget_name,
                    resource_type='budget',
                    recommendation_type='FORECAST_RISK',
                    description=(
                        f'A previsão de gastos (${forecasted:,.2f}) excede o limite '
                        f'(${budget_limit:,.2f}) em ${forecasted - budget_limit:,.2f}. '
                        f'Intervenção proativa recomendada.'
                    ),
                    estimated_savings=forecasted - budget_limit,
                    priority='HIGH',
                    title=f'Budget "{budget_name}" com previsão de estouro',
                    action='Implementar medidas de redução de custos'
                ))
        
        if not budgets:
            recommendations.append(ServiceRecommendation(
                resource_id='account',
                resource_type='budget',
                recommendation_type='NO_BUDGETS',
                description=(
                    'A conta AWS não possui budgets configurados. '
                    'Budgets são essenciais para controle de custos e '
                    'prevenção de gastos inesperados.'
                ),
                estimated_savings=0,
                priority='MEDIUM',
                title='Nenhum budget configurado',
                action='Configurar budgets para serviços críticos'
            ))
        
        return recommendations
    
    def analyze_usage(self) -> Dict[str, Any]:
        """Analisa padrões de uso dos budgets"""
        budgets = self.get_resources()
        metrics = self.get_metrics()
        recommendations = self.get_recommendations()
        
        at_risk_budgets = [
            b for b in budgets 
            if b.get('status') in ['EXCEEDED', 'WARNING']
        ]
        
        healthy_budgets = [
            b for b in budgets 
            if b.get('status') in ['OK', 'ON_TRACK']
        ]
        
        return {
            'service': 'budgets',
            'summary': {
                'total_budgets': len(budgets),
                'at_risk_budgets': len(at_risk_budgets),
                'healthy_budgets': len(healthy_budgets),
                'avg_utilization': metrics.metrics.get('avg_utilization_percent', 0)
            },
            'at_risk_budgets': at_risk_budgets,
            'healthy_budgets': healthy_budgets,
            'recommendations_count': len(recommendations),
            'optimization_opportunities': [r.title for r in recommendations]
        }
