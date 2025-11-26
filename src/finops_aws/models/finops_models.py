"""
FinOps AWS Data Models
Modelos de dados para representar custos, uso e recomendações de otimização.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class CostData:
    """Dados de custo por serviço AWS"""
    service_name: str
    amount: float
    currency: str = "USD"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


@dataclass
class EC2InstanceUsage:
    """Dados de uso de instância EC2"""
    instance_id: str
    instance_type: str
    avg_cpu_7d: Optional[float] = None
    avg_cpu_15d: Optional[float] = None
    avg_cpu_30d: Optional[float] = None
    state: Optional[str] = None
    availability_zone: Optional[str] = None


@dataclass
class LambdaFunctionUsage:
    """Dados de uso de função Lambda"""
    function_name: str
    invocations_7d: Optional[int] = None
    avg_duration_7d: Optional[float] = None
    errors_7d: Optional[int] = None
    throttles_7d: Optional[int] = None


@dataclass
class OptimizationRecommendation:
    """Recomendação de otimização do Compute Optimizer"""
    resource_id: str
    resource_type: str
    current_configuration: str
    recommended_configurations: List[str]
    estimated_monthly_savings: Optional[float] = None
    finding: Optional[str] = None
    utilization_metrics: Optional[Dict[str, float]] = None


@dataclass
class FinOpsReport:
    """Relatório consolidado de FinOps"""
    account_id: str
    generated_at: datetime
    costs: Dict[str, Dict[str, float]]
    usage: Dict[str, List[Any]]
    optimizer: Dict[str, List[OptimizationRecommendation]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o relatório para dicionário para serialização JSON"""
        return {
            "account_id": self.account_id,
            "generated_at": self.generated_at.isoformat(),
            "costs": self.costs,
            "usage": {
                service: [
                    item.__dict__ if hasattr(item, '__dict__') else item 
                    for item in items
                ]
                for service, items in self.usage.items()
            },
            "optimizer": {
                service: [rec.__dict__ for rec in recommendations]
                for service, recommendations in self.optimizer.items()
            }
        }