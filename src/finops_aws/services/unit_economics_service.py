"""
FinOps AWS - Unit Economics Service
Serviço de Unit Economics para FinOps

Este serviço implementa:
- Cost per Customer
- Cost per Transaction
- Cost per Revenue Dollar
- Margin Analysis
- Business metric integration

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Adapter: Adapta diferentes fontes de métricas de negócio
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class MetricSource(Enum):
    """Fonte de métricas de negócio"""
    MANUAL = "manual"
    CLOUDWATCH = "cloudwatch"
    DATABASE = "database"
    API = "api"


@dataclass
class BusinessMetrics:
    """Métricas de negócio para Unit Economics"""
    period_start: datetime
    period_end: datetime
    customers_count: int = 0
    active_customers: int = 0
    new_customers: int = 0
    churned_customers: int = 0
    transactions_count: int = 0
    orders_count: int = 0
    api_calls_count: int = 0
    revenue: float = 0.0
    gross_profit: float = 0.0
    data_source: str = "manual"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'customers': {
                'total': self.customers_count,
                'active': self.active_customers,
                'new': self.new_customers,
                'churned': self.churned_customers
            },
            'transactions': {
                'total': self.transactions_count,
                'orders': self.orders_count,
                'api_calls': self.api_calls_count
            },
            'financial': {
                'revenue': round(self.revenue, 2),
                'gross_profit': round(self.gross_profit, 2)
            },
            'data_source': self.data_source
        }


@dataclass
class UnitEconomicsResult:
    """Resultado de Unit Economics"""
    period_start: datetime
    period_end: datetime
    calculated_at: datetime
    total_cloud_cost: float
    cost_per_customer: float
    cost_per_active_customer: float
    cost_per_transaction: float
    cost_per_order: float
    cost_per_api_call: float
    cost_per_revenue_dollar: float
    cloud_cost_margin_percent: float
    customer_acquisition_cost: float
    customer_lifetime_value_estimate: float
    ltv_cac_ratio: float
    efficiency_score: float
    trend_vs_previous: Dict[str, float] = field(default_factory=dict)
    by_service: Dict[str, Dict[str, float]] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'calculated_at': self.calculated_at.isoformat(),
            'total_cloud_cost': round(self.total_cloud_cost, 2),
            'unit_costs': {
                'cost_per_customer': round(self.cost_per_customer, 4),
                'cost_per_active_customer': round(self.cost_per_active_customer, 4),
                'cost_per_transaction': round(self.cost_per_transaction, 6),
                'cost_per_order': round(self.cost_per_order, 4),
                'cost_per_api_call': round(self.cost_per_api_call, 8)
            },
            'financial_metrics': {
                'cost_per_revenue_dollar': round(self.cost_per_revenue_dollar, 4),
                'cloud_cost_margin_percent': round(self.cloud_cost_margin_percent, 2),
                'customer_acquisition_cost': round(self.customer_acquisition_cost, 2),
                'customer_lifetime_value': round(self.customer_lifetime_value_estimate, 2),
                'ltv_cac_ratio': round(self.ltv_cac_ratio, 2)
            },
            'efficiency_score': round(self.efficiency_score, 2),
            'trend_vs_previous': {k: round(v, 2) for k, v in self.trend_vs_previous.items()},
            'by_service': self.by_service,
            'recommendations': self.recommendations
        }


@dataclass
class ServiceUnitCost:
    """Custo unitário por serviço"""
    service_name: str
    total_cost: float
    cost_per_customer: float
    cost_per_transaction: float
    percentage_of_total: float
    trend_vs_previous: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_name': self.service_name,
            'total_cost': round(self.total_cost, 2),
            'cost_per_customer': round(self.cost_per_customer, 4),
            'cost_per_transaction': round(self.cost_per_transaction, 6),
            'percentage_of_total': round(self.percentage_of_total, 2),
            'trend_vs_previous': round(self.trend_vs_previous, 2)
        }


class UnitEconomicsService(BaseAWSService):
    """
    Serviço de Unit Economics
    
    Funcionalidades:
    - Calcula custos unitários (por cliente, transação, etc.)
    - Integra métricas de negócio de várias fontes
    - Analisa margem e eficiência de custos
    - Projeta LTV e CAC baseados em custos cloud
    
    AWS APIs utilizadas:
    - ce:GetCostAndUsage
    - cloudwatch:GetMetricStatistics (para métricas de negócio)
    """
    
    EFFICIENCY_THRESHOLDS = {
        'excellent': 0.10,
        'good': 0.20,
        'acceptable': 0.35,
        'needs_improvement': 0.50
    }
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "unit_economics"
        self._cache = FinOpsCache(default_ttl=300)
        self._business_metrics: Optional[BusinessMetrics] = None
        self._metric_sources: Dict[str, MetricSource] = {}
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce', region_name='us-east-1')
        return boto3.client('ce', region_name='us-east-1')
    
    def _get_cloudwatch_client(self, region: str = None):
        """Obtém cliente boto3 para CloudWatch"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('cloudwatch', region_name=region)
        return boto3.client('cloudwatch', region_name=region)
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_ce_client()
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Retorna configuração de fontes de métricas"""
        return {
            'metric_sources': {k: v.value for k, v in self._metric_sources.items()},
            'business_metrics_configured': self._business_metrics is not None
        }
    
    def set_business_metrics(
        self,
        customers_count: int = 0,
        active_customers: int = 0,
        new_customers: int = 0,
        transactions_count: int = 0,
        orders_count: int = 0,
        api_calls_count: int = 0,
        revenue: float = 0.0,
        gross_profit: float = 0.0,
        period_days: int = 30
    ):
        """
        Define métricas de negócio manualmente
        
        Args:
            customers_count: Total de clientes
            active_customers: Clientes ativos no período
            new_customers: Novos clientes no período
            transactions_count: Total de transações
            orders_count: Total de pedidos
            api_calls_count: Total de chamadas API
            revenue: Receita do período
            gross_profit: Lucro bruto
            period_days: Período das métricas
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        self._business_metrics = BusinessMetrics(
            period_start=start_date,
            period_end=end_date,
            customers_count=customers_count,
            active_customers=active_customers or customers_count,
            new_customers=new_customers,
            transactions_count=transactions_count,
            orders_count=orders_count or transactions_count,
            api_calls_count=api_calls_count,
            revenue=revenue,
            gross_profit=gross_profit or revenue * 0.3,
            data_source="manual"
        )
        
        self.logger.info(f"Métricas de negócio configuradas: {customers_count} clientes, {transactions_count} transações")
    
    def fetch_metrics_from_cloudwatch(
        self,
        namespace: str,
        metric_mappings: Dict[str, str],
        period_days: int = 30
    ):
        """
        Obtém métricas de negócio do CloudWatch
        
        Args:
            namespace: Namespace do CloudWatch
            metric_mappings: Mapeamento de métricas (nome_campo: nome_metrica_cw)
            period_days: Período de coleta
        """
        try:
            client = self._get_cloudwatch_client()
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=period_days)
            
            metrics_data = {}
            
            for field_name, metric_name in metric_mappings.items():
                response = client.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=period_days * 24 * 3600,
                    Statistics=['Sum', 'Average']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    metrics_data[field_name] = datapoints[0].get('Sum', 0)
            
            self._business_metrics = BusinessMetrics(
                period_start=start_time,
                period_end=end_time,
                customers_count=int(metrics_data.get('customers_count', 0)),
                active_customers=int(metrics_data.get('active_customers', 0)),
                transactions_count=int(metrics_data.get('transactions_count', 0)),
                orders_count=int(metrics_data.get('orders_count', 0)),
                api_calls_count=int(metrics_data.get('api_calls_count', 0)),
                revenue=float(metrics_data.get('revenue', 0)),
                data_source="cloudwatch"
            )
            
            self._metric_sources['customers'] = MetricSource.CLOUDWATCH
            self._metric_sources['transactions'] = MetricSource.CLOUDWATCH
            
        except Exception as e:
            self.logger.error(f"Erro ao obter métricas do CloudWatch: {e}")
    
    def calculate_unit_economics(
        self,
        period_days: int = 30,
        include_service_breakdown: bool = True
    ) -> UnitEconomicsResult:
        """
        Calcula Unit Economics completo
        
        Args:
            period_days: Período de análise
            include_service_breakdown: Incluir breakdown por serviço
            
        Returns:
            UnitEconomicsResult com todas as métricas
        """
        cache_key = f"unit_economics_{period_days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        total_cost = self._get_total_cost(start_date, end_date)
        
        if not self._business_metrics:
            self._estimate_business_metrics(total_cost, period_days)
        
        metrics = self._business_metrics
        
        cost_per_customer = 0.0
        cost_per_active_customer = 0.0
        cost_per_transaction = 0.0
        cost_per_order = 0.0
        cost_per_api_call = 0.0
        cost_per_revenue_dollar = 0.0
        margin_percent = 0.0
        cac = 0.0
        ltv = 0.0
        ltv_cac_ratio = 0.0
        
        if metrics.customers_count > 0:
            cost_per_customer = total_cost / metrics.customers_count
        
        if metrics.active_customers > 0:
            cost_per_active_customer = total_cost / metrics.active_customers
        
        if metrics.transactions_count > 0:
            cost_per_transaction = total_cost / metrics.transactions_count
        
        if metrics.orders_count > 0:
            cost_per_order = total_cost / metrics.orders_count
        
        if metrics.api_calls_count > 0:
            cost_per_api_call = total_cost / metrics.api_calls_count
        
        if metrics.revenue > 0:
            cost_per_revenue_dollar = total_cost / metrics.revenue
            margin_percent = ((metrics.revenue - total_cost) / metrics.revenue) * 100
        
        if metrics.new_customers > 0:
            marketing_cost = total_cost * 0.15
            cac = marketing_cost / metrics.new_customers
        
        avg_revenue_per_customer = 0.0
        if metrics.active_customers > 0:
            avg_revenue_per_customer = metrics.revenue / metrics.active_customers
        
        avg_lifespan_months = 24
        ltv = avg_revenue_per_customer * avg_lifespan_months
        
        if cac > 0:
            ltv_cac_ratio = ltv / cac
        
        efficiency_score = self._calculate_efficiency_score(
            cost_per_revenue_dollar,
            margin_percent,
            ltv_cac_ratio
        )
        
        trend = self._calculate_trend(period_days)
        
        by_service = {}
        if include_service_breakdown:
            by_service = self._calculate_service_unit_costs(
                start_date,
                end_date,
                metrics.customers_count,
                metrics.transactions_count,
                total_cost
            )
        
        recommendations = self._generate_recommendations(
            cost_per_customer,
            cost_per_transaction,
            margin_percent,
            efficiency_score
        )
        
        result = UnitEconomicsResult(
            period_start=start_date,
            period_end=end_date,
            calculated_at=datetime.utcnow(),
            total_cloud_cost=total_cost,
            cost_per_customer=cost_per_customer,
            cost_per_active_customer=cost_per_active_customer,
            cost_per_transaction=cost_per_transaction,
            cost_per_order=cost_per_order,
            cost_per_api_call=cost_per_api_call,
            cost_per_revenue_dollar=cost_per_revenue_dollar,
            cloud_cost_margin_percent=margin_percent,
            customer_acquisition_cost=cac,
            customer_lifetime_value_estimate=ltv,
            ltv_cac_ratio=ltv_cac_ratio,
            efficiency_score=efficiency_score,
            trend_vs_previous=trend,
            by_service=by_service,
            recommendations=recommendations
        )
        
        self._cache.set(cache_key, result, ttl=1800)
        return result
    
    def _get_total_cost(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Obtém custo total do período"""
        try:
            client = self._get_ce_client()
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            total = 0.0
            for result in response.get('ResultsByTime', []):
                total += float(result.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0))
            
            return total
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custo total: {e}")
            return 0.0
    
    def _estimate_business_metrics(self, total_cost: float, period_days: int):
        """Estima métricas de negócio quando não fornecidas"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        estimated_customers = max(100, int(total_cost * 10))
        estimated_transactions = max(1000, int(total_cost * 100))
        estimated_revenue = max(total_cost * 5, 1000)
        
        self._business_metrics = BusinessMetrics(
            period_start=start_date,
            period_end=end_date,
            customers_count=estimated_customers,
            active_customers=int(estimated_customers * 0.7),
            new_customers=int(estimated_customers * 0.1),
            transactions_count=estimated_transactions,
            orders_count=int(estimated_transactions * 0.3),
            api_calls_count=estimated_transactions * 10,
            revenue=estimated_revenue,
            gross_profit=estimated_revenue * 0.3,
            data_source="estimated"
        )
        
        self.logger.warning("Usando métricas de negócio estimadas - configure valores reais para análise precisa")
    
    def _calculate_efficiency_score(
        self,
        cost_per_revenue: float,
        margin_percent: float,
        ltv_cac_ratio: float
    ) -> float:
        """Calcula score de eficiência (0-100)"""
        score = 0.0
        
        if cost_per_revenue <= self.EFFICIENCY_THRESHOLDS['excellent']:
            score += 40
        elif cost_per_revenue <= self.EFFICIENCY_THRESHOLDS['good']:
            score += 30
        elif cost_per_revenue <= self.EFFICIENCY_THRESHOLDS['acceptable']:
            score += 20
        else:
            score += 10
        
        if margin_percent >= 50:
            score += 30
        elif margin_percent >= 30:
            score += 20
        elif margin_percent >= 10:
            score += 10
        
        if ltv_cac_ratio >= 3:
            score += 30
        elif ltv_cac_ratio >= 2:
            score += 20
        elif ltv_cac_ratio >= 1:
            score += 10
        
        return min(100, score)
    
    def _calculate_trend(self, period_days: int) -> Dict[str, float]:
        """Calcula tendência comparando com período anterior"""
        try:
            end_date = datetime.utcnow()
            current_start = end_date - timedelta(days=period_days)
            previous_start = current_start - timedelta(days=period_days)
            previous_end = current_start
            
            current_cost = self._get_total_cost(current_start, end_date)
            previous_cost = self._get_total_cost(previous_start, previous_end)
            
            if previous_cost > 0:
                cost_trend = ((current_cost - previous_cost) / previous_cost) * 100
            else:
                cost_trend = 0.0
            
            return {
                'cost_change_percent': cost_trend,
                'current_period': current_cost,
                'previous_period': previous_cost
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular tendência: {e}")
            return {}
    
    def _calculate_service_unit_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        customers: int,
        transactions: int,
        total_cost: float
    ) -> Dict[str, Dict[str, float]]:
        """Calcula custos unitários por serviço"""
        try:
            client = self._get_ce_client()
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            by_service = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if cost > 0:
                        by_service[service] = {
                            'total_cost': round(cost, 2),
                            'cost_per_customer': round(cost / customers, 4) if customers > 0 else 0,
                            'cost_per_transaction': round(cost / transactions, 6) if transactions > 0 else 0,
                            'percentage_of_total': round((cost / total_cost) * 100, 2) if total_cost > 0 else 0
                        }
            
            return dict(sorted(by_service.items(), key=lambda x: x[1]['total_cost'], reverse=True)[:10])
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular custos por serviço: {e}")
            return {}
    
    def _generate_recommendations(
        self,
        cost_per_customer: float,
        cost_per_transaction: float,
        margin: float,
        efficiency_score: float
    ) -> List[Dict[str, Any]]:
        """Gera recomendações baseadas em Unit Economics"""
        recommendations = []
        
        if efficiency_score < 50:
            recommendations.append({
                'type': 'EFFICIENCY_LOW',
                'priority': 'HIGH',
                'title': 'Eficiência de custos abaixo do ideal',
                'description': f'Score de eficiência: {efficiency_score:.0f}/100. Meta: >70',
                'action': 'Revisar arquitetura e otimizar recursos subutilizados'
            })
        
        if margin < 20:
            recommendations.append({
                'type': 'MARGIN_LOW',
                'priority': 'HIGH',
                'title': 'Margem de cloud muito baixa',
                'description': f'Custos cloud consomem {100-margin:.1f}% da receita',
                'action': 'Implementar rightsizing e Savings Plans para reduzir custos'
            })
        
        if cost_per_customer > 10:
            recommendations.append({
                'type': 'HIGH_COST_PER_CUSTOMER',
                'priority': 'MEDIUM',
                'title': 'Alto custo por cliente',
                'description': f'${cost_per_customer:.2f}/cliente pode impactar escalabilidade',
                'action': 'Otimizar arquitetura para reduzir custo marginal por cliente'
            })
        
        return recommendations
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        result = self.calculate_unit_economics(period_days, include_service_breakdown=False)
        return {
            'service': 'unit_economics',
            'period_days': period_days,
            'total_cost': result.total_cloud_cost,
            'cost_per_customer': result.cost_per_customer,
            'cost_per_transaction': result.cost_per_transaction,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        result = self.calculate_unit_economics(30, include_service_breakdown=False)
        return {
            'service': 'unit_economics',
            'efficiency_score': result.efficiency_score,
            'margin_percent': result.cloud_cost_margin_percent,
            'ltv_cac_ratio': result.ltv_cac_ratio,
            'data_source': self._business_metrics.data_source if self._business_metrics else 'none'
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de Unit Economics"""
        result = self.calculate_unit_economics(30)
        return result.recommendations
