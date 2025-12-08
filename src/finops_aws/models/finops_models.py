"""
FinOps AWS Data Models
Modelos de dados para representar custos, uso e recomendações de otimização.

Conformidade com Framework FinOps:
- 13 tabelas do modelo universal (Nível 2)
- Campos do CUR expandidos
- Suporte a Unit Economics
- Tag Governance
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class CommitmentType(Enum):
    """Tipos de compromissos AWS"""
    RESERVED_INSTANCE = "RI"
    SAVINGS_PLAN = "SP"
    EDP = "EDP"
    PRIVATE_OFFER = "PrivateOffer"
    MARKETPLACE_SUB = "MarketplaceSub"


class AnomalyType(Enum):
    """Tipos de anomalias de custo"""
    SPIKE = "spike"
    DRIFT = "drift"
    UNEXPECTED = "unexpected"


class BudgetStatus(Enum):
    """Status de budget"""
    OK = "OK"
    ON_TRACK = "ON_TRACK"
    WARNING = "WARNING"
    EXCEEDED = "EXCEEDED"


@dataclass
class CostData:
    """Dados de custo por serviço AWS"""
    service_name: str
    amount: float
    currency: str = "USD"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    amortized_cost: float = 0.0
    net_cost: float = 0.0
    effective_rate: float = 0.0
    discount_type: str = ""


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
class Account:
    """Tabela: accounts - Estrutura de contas AWS"""
    payer_account_id: str
    linked_account_id: str
    account_name: str
    organization_unit: str = ""
    business_owner: str = ""
    environment: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'payer_account_id': self.payer_account_id,
            'linked_account_id': self.linked_account_id,
            'account_name': self.account_name,
            'organization_unit': self.organization_unit,
            'business_owner': self.business_owner,
            'environment': self.environment,
            'tags': self.tags
        }


@dataclass
class ServiceInfo:
    """Tabela: services - Catálogo de serviços AWS"""
    service_code: str
    service_name: str
    product_family: str = ""
    category: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_code': self.service_code,
            'service_name': self.service_name,
            'product_family': self.product_family,
            'category': self.category
        }


@dataclass
class Resource:
    """Tabela: resources - Recursos AWS"""
    resource_id: str
    service_code: str
    account_id: str
    region: str
    resource_type: str
    creation_time: Optional[datetime] = None
    state: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'service_code': self.service_code,
            'account_id': self.account_id,
            'region': self.region,
            'resource_type': self.resource_type,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'state': self.state,
            'tags': self.tags
        }


@dataclass
class UsageRecord:
    """Tabela: usage - Dados de uso derivados do CUR"""
    usage_id: str
    service_code: str
    usage_type: str
    operation: str
    usage_start_time: datetime
    usage_end_time: datetime
    usage_amount: float
    usage_unit: str
    unblended_cost: float
    amortized_cost: float
    net_cost: float = 0.0
    region: str = ""
    availability_zone: str = ""
    resource_id: str = ""
    account_id: str = ""
    pricing_term: str = "on-demand"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'usage_id': self.usage_id,
            'service_code': self.service_code,
            'usage_type': self.usage_type,
            'operation': self.operation,
            'usage_start_time': self.usage_start_time.isoformat(),
            'usage_end_time': self.usage_end_time.isoformat(),
            'usage_amount': self.usage_amount,
            'usage_unit': self.usage_unit,
            'unblended_cost': self.unblended_cost,
            'amortized_cost': self.amortized_cost,
            'net_cost': self.net_cost,
            'region': self.region,
            'availability_zone': self.availability_zone,
            'resource_id': self.resource_id,
            'account_id': self.account_id,
            'pricing_term': self.pricing_term
        }


@dataclass
class MetricRecord:
    """Tabela: metrics - Métricas técnicas"""
    resource_id: str
    metric_name: str
    metric_unit: str
    avg_value: float
    p95_value: float = 0.0
    max_value: float = 0.0
    collection_period: str = ""
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'metric_name': self.metric_name,
            'metric_unit': self.metric_unit,
            'avg_value': self.avg_value,
            'p95_value': self.p95_value,
            'max_value': self.max_value,
            'collection_period': self.collection_period,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class Recommendation:
    """Tabela: recommendations - Recomendações FinOps"""
    recommendation_id: str
    resource_id: str
    service_code: str
    category: str
    description: str
    estimated_saving_month: float = 0.0
    priority: str = "MEDIUM"
    owner_team: str = ""
    approval_status: str = "proposed"
    approved_by: str = ""
    due_date: Optional[datetime] = None
    implemented_on: Optional[datetime] = None
    jira_ticket: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'recommendation_id': self.recommendation_id,
            'resource_id': self.resource_id,
            'service_code': self.service_code,
            'category': self.category,
            'description': self.description,
            'estimated_saving_month': self.estimated_saving_month,
            'priority': self.priority,
            'owner_team': self.owner_team,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'implemented_on': self.implemented_on.isoformat() if self.implemented_on else None,
            'jira_ticket': self.jira_ticket
        }


@dataclass
class Commitment:
    """Tabela: commitments - RI, Savings Plans, EDP"""
    commitment_id: str
    commitment_type: str
    service_scope: str
    region_scope: str = ""
    instance_family: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    hourly_commitment: float = 0.0
    payment_option: str = ""
    utilization_percent: float = 0.0
    coverage_percent: float = 0.0
    unused_commitment_cost: float = 0.0
    expiry_risk: str = "LOW"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'commitment_id': self.commitment_id,
            'commitment_type': self.commitment_type,
            'service_scope': self.service_scope,
            'region_scope': self.region_scope,
            'instance_family': self.instance_family,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'hourly_commitment': self.hourly_commitment,
            'payment_option': self.payment_option,
            'utilization_percent': self.utilization_percent,
            'coverage_percent': self.coverage_percent,
            'unused_commitment_cost': self.unused_commitment_cost,
            'expiry_risk': self.expiry_risk
        }


@dataclass
class BusinessDimension:
    """Tabela: business_dimensions - Unit Economics"""
    domain: str
    product_name: str
    customer_segment: str = ""
    environment_type: str = ""
    unit_metric: str = ""
    unit_cost: float = 0.0
    transactions_count: int = 0
    revenue: float = 0.0
    margin: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'domain': self.domain,
            'product_name': self.product_name,
            'customer_segment': self.customer_segment,
            'environment_type': self.environment_type,
            'unit_metric': self.unit_metric,
            'unit_cost': self.unit_cost,
            'transactions_count': self.transactions_count,
            'revenue': self.revenue,
            'margin': self.margin
        }


@dataclass
class BillingExtra:
    """Tabela: billing_extras - Support, Tax, Credits, Marketplace"""
    billing_item_id: str
    item_type: str
    amount: float
    currency: str = "USD"
    billing_period: str = ""
    description: str = ""
    linked_account_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'billing_item_id': self.billing_item_id,
            'item_type': self.item_type,
            'amount': self.amount,
            'currency': self.currency,
            'billing_period': self.billing_period,
            'description': self.description,
            'linked_account_id': self.linked_account_id
        }


@dataclass
class Budget:
    """Tabela: budgets - Orçamentos"""
    budget_id: str
    scope: str
    amount_monthly: float
    alert_thresholds: List[float] = field(default_factory=list)
    owner: str = ""
    period: str = "mensal"
    actual_spend: float = 0.0
    forecasted_spend: float = 0.0
    status: str = "OK"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'budget_id': self.budget_id,
            'scope': self.scope,
            'amount_monthly': self.amount_monthly,
            'alert_thresholds': self.alert_thresholds,
            'owner': self.owner,
            'period': self.period,
            'actual_spend': self.actual_spend,
            'forecasted_spend': self.forecasted_spend,
            'status': self.status
        }


@dataclass
class Anomaly:
    """Tabela: anomalies - Anomalias de custo"""
    anomaly_id: str
    scope: str
    anomaly_type: str
    detected_on: Optional[datetime] = None
    expected_cost: float = 0.0
    actual_cost: float = 0.0
    delta_percent: float = 0.0
    root_cause_hint: str = ""
    status: str = "OPEN"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            'scope': self.scope,
            'anomaly_type': self.anomaly_type,
            'detected_on': self.detected_on.isoformat() if self.detected_on else None,
            'expected_cost': self.expected_cost,
            'actual_cost': self.actual_cost,
            'delta_percent': self.delta_percent,
            'root_cause_hint': self.root_cause_hint,
            'status': self.status
        }


@dataclass
class TagPolicy:
    """Tabela: tag_policies - Políticas de tags"""
    policy_id: str
    required_tags: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    scope: str = "account"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'required_tags': self.required_tags,
            'validation_rules': self.validation_rules,
            'scope': self.scope
        }


@dataclass
class TagCoverage:
    """Tabela: tag_coverage - Cobertura de tags"""
    scope: str
    total_resources: int
    tagged_resources: int
    percent_tagged: float = 0.0
    percent_complete: float = 0.0
    missing_tags: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scope': self.scope,
            'total_resources': self.total_resources,
            'tagged_resources': self.tagged_resources,
            'percent_tagged': self.percent_tagged,
            'percent_complete': self.percent_complete,
            'missing_tags': self.missing_tags
        }


@dataclass
class FinOpsKPIs:
    """KPIs oficiais FinOps (12+)"""
    total_spend: float = 0.0
    waste_percent: float = 0.0
    idle_cost: float = 0.0
    shadow_cost: float = 0.0
    commitment_loss: float = 0.0
    cost_per_customer: float = 0.0
    cost_per_transaction: float = 0.0
    margin: float = 0.0
    forecast_7d: float = 0.0
    forecast_30d: float = 0.0
    forecast_90d: float = 0.0
    ri_coverage_percent: float = 0.0
    ri_utilization_percent: float = 0.0
    sp_coverage_percent: float = 0.0
    sp_utilization_percent: float = 0.0
    cost_growth_mom: float = 0.0
    cost_growth_yoy: float = 0.0
    economic_health_index: float = 0.0
    tag_coverage_percent: float = 0.0
    savings_captured: float = 0.0
    savings_potential: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_spend': self.total_spend,
            'waste_percent': round(self.waste_percent, 2),
            'idle_cost': self.idle_cost,
            'shadow_cost': self.shadow_cost,
            'commitment_loss': self.commitment_loss,
            'cost_per_customer': self.cost_per_customer,
            'cost_per_transaction': self.cost_per_transaction,
            'margin': self.margin,
            'forecast_7d': self.forecast_7d,
            'forecast_30d': self.forecast_30d,
            'forecast_90d': self.forecast_90d,
            'ri_coverage_percent': round(self.ri_coverage_percent, 2),
            'ri_utilization_percent': round(self.ri_utilization_percent, 2),
            'sp_coverage_percent': round(self.sp_coverage_percent, 2),
            'sp_utilization_percent': round(self.sp_utilization_percent, 2),
            'cost_growth_mom': round(self.cost_growth_mom, 2),
            'cost_growth_yoy': round(self.cost_growth_yoy, 2),
            'economic_health_index': round(self.economic_health_index, 2),
            'tag_coverage_percent': round(self.tag_coverage_percent, 2),
            'savings_captured': self.savings_captured,
            'savings_potential': self.savings_potential
        }


@dataclass
class FinOpsReport:
    """Relatório consolidado de FinOps"""
    account_id: str
    generated_at: datetime
    costs: Dict[str, Dict[str, float]]
    usage: Dict[str, List[Any]]
    optimizer: Dict[str, List[OptimizationRecommendation]]
    kpis: Optional[FinOpsKPIs] = None
    commitments: List[Commitment] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)
    budgets: List[Budget] = field(default_factory=list)
    tag_coverage: Optional[TagCoverage] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o relatório para dicionário para serialização JSON"""
        result = {
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
        
        if self.kpis:
            result["kpis"] = self.kpis.to_dict()
        if self.commitments:
            result["commitments"] = [c.to_dict() for c in self.commitments]
        if self.anomalies:
            result["anomalies"] = [a.to_dict() for a in self.anomalies]
        if self.budgets:
            result["budgets"] = [b.to_dict() for b in self.budgets]
        if self.tag_coverage:
            result["tag_coverage"] = self.tag_coverage.to_dict()
            
        return result
