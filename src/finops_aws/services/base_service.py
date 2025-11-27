"""
Base Service - Classe base para todos os serviços AWS

FASE 2 do Roadmap FinOps AWS
Objetivo: Padronizar interface e comportamento de todos os serviços

Autor: FinOps AWS Team
Data: Novembro 2025
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Protocol
from botocore.exceptions import ClientError

from ..utils.logger import setup_logger, log_api_call
from ..utils.aws_helpers import handle_aws_error, get_aws_region

logger = setup_logger(__name__)


@dataclass
class ServiceCost:
    """Representa custos de um serviço AWS"""
    service_name: str
    total_cost: float
    period_days: int
    cost_by_resource: Dict[str, float] = field(default_factory=dict)
    cost_by_region: Dict[str, float] = field(default_factory=dict)
    daily_costs: List[Dict[str, Any]] = field(default_factory=list)
    trend: str = "STABLE"
    currency: str = "USD"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_name': self.service_name,
            'total_cost': self.total_cost,
            'period_days': self.period_days,
            'cost_by_resource': self.cost_by_resource,
            'cost_by_region': self.cost_by_region,
            'daily_costs': self.daily_costs,
            'trend': self.trend,
            'currency': self.currency
        }


@dataclass
class ServiceMetrics:
    """Representa métricas de um serviço AWS"""
    service_name: str
    resource_count: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    utilization: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_name': self.service_name,
            'resource_count': self.resource_count,
            'metrics': self.metrics,
            'utilization': self.utilization
        }


@dataclass
class ServiceRecommendation:
    """Representa uma recomendação de otimização"""
    resource_id: str
    resource_type: str
    recommendation_type: str
    description: str
    estimated_savings: float = 0.0
    priority: str = "MEDIUM"
    implementation_effort: str = "MEDIUM"
    details: Dict[str, Any] = field(default_factory=dict)
    title: str = ""
    action: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'recommendation_type': self.recommendation_type,
            'title': self.title,
            'description': self.description,
            'estimated_savings': self.estimated_savings,
            'priority': self.priority,
            'implementation_effort': self.implementation_effort,
            'action': self.action,
            'details': self.details
        }


class BaseAWSService(ABC):
    """
    Classe base abstrata para todos os serviços AWS
    
    Define interface padrão para:
    - Coleta de custos
    - Coleta de métricas
    - Geração de recomendações
    - Health check
    
    Todas as implementações de serviços devem herdar desta classe.
    """
    
    SERVICE_NAME: str = "Unknown"
    SERVICE_FILTER: str = ""
    
    def __init__(
        self,
        cost_client=None,
        cloudwatch_client=None
    ):
        """
        Inicializa o serviço base
        
        Args:
            cost_client: Cliente Cost Explorer injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
        """
        self.region = get_aws_region()
        self._cost_client = cost_client
        self._cloudwatch_client = cloudwatch_client
    
    @property
    def cost_client(self):
        """Lazy loading do cliente Cost Explorer"""
        if self._cost_client is None:
            import boto3
            self._cost_client = boto3.client('ce', region_name='us-east-1')
        return self._cost_client
    
    @property
    def cloudwatch_client(self):
        """Lazy loading do cliente CloudWatch"""
        if self._cloudwatch_client is None:
            import boto3
            self._cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
        return self._cloudwatch_client
    
    def get_service_name(self) -> str:
        """Retorna nome do serviço"""
        return self.SERVICE_NAME
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        pass
    
    @abstractmethod
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista recursos do serviço"""
        pass
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """
        Obtém custos do serviço
        
        Args:
            period_days: Período de análise em dias
            
        Returns:
            ServiceCost com dados de custos
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            params = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': 'DAILY',
                'Metrics': ['UnblendedCost'],
                'GroupBy': [
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            }
            
            if self.SERVICE_FILTER:
                params['Filter'] = {
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [self.SERVICE_FILTER]
                    }
                }
            
            response = self.cost_client.get_cost_and_usage(**params)
            
            total_cost = 0.0
            daily_costs = []
            cost_by_resource = {}
            
            for result in response.get('ResultsByTime', []):
                daily_total = 0.0
                date = result['TimePeriod']['Start']
                
                for group in result.get('Groups', []):
                    usage_type = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    daily_total += cost
                    total_cost += cost
                    
                    if usage_type not in cost_by_resource:
                        cost_by_resource[usage_type] = 0.0
                    cost_by_resource[usage_type] += cost
                
                daily_costs.append({
                    'date': date,
                    'cost': daily_total
                })
            
            trend = self._calculate_trend(daily_costs)
            
            logger.info(f"{self.SERVICE_NAME} cost for {period_days} days: ${total_cost:.2f}")
            
            return ServiceCost(
                service_name=self.SERVICE_NAME,
                total_cost=total_cost,
                period_days=period_days,
                cost_by_resource=cost_by_resource,
                daily_costs=daily_costs,
                trend=trend
            )
            
        except ClientError as e:
            handle_aws_error(e, f"get_{self.SERVICE_NAME.lower()}_costs")
            return ServiceCost(
                service_name=self.SERVICE_NAME,
                total_cost=0.0,
                period_days=period_days
            )
    
    def _calculate_trend(self, daily_costs: List[Dict[str, Any]]) -> str:
        """Calcula tendência de custos"""
        if len(daily_costs) < 7:
            return "STABLE"
        
        recent_avg = sum(d['cost'] for d in daily_costs[-7:]) / 7
        older_avg = sum(d['cost'] for d in daily_costs[:7]) / 7
        
        if older_avg == 0:
            return "STABLE"
        
        change_pct = (recent_avg - older_avg) / older_avg * 100
        
        if change_pct > 10:
            return "INCREASING"
        elif change_pct < -10:
            return "DECREASING"
        return "STABLE"
    
    def get_cloudwatch_metric(
        self,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict[str, str]],
        period_days: int = 7,
        statistics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtém métricas do CloudWatch
        
        Args:
            namespace: Namespace do CloudWatch
            metric_name: Nome da métrica
            dimensions: Dimensões da métrica
            period_days: Período de análise
            statistics: Estatísticas desejadas
            
        Returns:
            Dicionário com dados da métrica
        """
        if statistics is None:
            statistics = ['Average', 'Maximum']
        
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=period_days)
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=statistics
            )
            
            datapoints = response.get('Datapoints', [])
            
            if not datapoints:
                return {
                    'average': 0,
                    'maximum': 0,
                    'latest': 0,
                    'datapoints': 0
                }
            
            sorted_points = sorted(datapoints, key=lambda x: x['Timestamp'])
            
            return {
                'average': sum(dp.get('Average', 0) for dp in sorted_points) / len(sorted_points),
                'maximum': max(dp.get('Maximum', 0) for dp in sorted_points),
                'latest': sorted_points[-1].get('Average', 0) if sorted_points else 0,
                'datapoints': len(sorted_points)
            }
            
        except ClientError as e:
            handle_aws_error(e, f"get_cloudwatch_metric_{metric_name}")
            return {'average': 0, 'maximum': 0, 'latest': 0, 'datapoints': 0}
    
    @abstractmethod
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas do serviço"""
        pass
    
    @abstractmethod
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Obtém recomendações de otimização"""
        pass
    
    def get_full_analysis(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Análise completa do serviço
        
        Returns:
            Dicionário com custos, métricas e recomendações
        """
        return {
            'service': self.SERVICE_NAME,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'costs': self.get_costs(period_days).to_dict(),
            'metrics': self.get_metrics().to_dict(),
            'recommendations': [r.to_dict() for r in self.get_recommendations()],
            'health': self.health_check()
        }
