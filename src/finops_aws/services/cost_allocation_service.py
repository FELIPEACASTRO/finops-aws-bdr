"""
FinOps AWS - Cost Allocation Service
Serviço de Alocação de Custos com Scorecard

Este serviço implementa:
- Cost Allocation Engine com mapeamento de tags e cost categories
- Scorecard de alocação com garantia de ≥50%/≥80% de recursos alocados
- Integração com Tag Governance para compliance
- Showback por BU/projeto

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Composite: Agregação hierárquica de custos
- Observer: Notificação de mudanças em alocação
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


class AllocationLevel(Enum):
    """Níveis de maturidade de alocação"""
    CRAWL = "crawl"
    WALK = "walk"
    RUN = "run"
    FLY = "fly"


@dataclass
class CostAllocationRule:
    """Regra de alocação de custos"""
    rule_id: str
    name: str
    tag_key: str
    tag_values: List[str]
    cost_category: str
    business_unit: str
    project: str
    owner: str
    allocation_percent: float = 100.0
    priority: int = 1
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'tag_key': self.tag_key,
            'tag_values': self.tag_values,
            'cost_category': self.cost_category,
            'business_unit': self.business_unit,
            'project': self.project,
            'owner': self.owner,
            'allocation_percent': self.allocation_percent,
            'priority': self.priority,
            'active': self.active
        }


@dataclass
class AllocationResult:
    """Resultado de alocação de um recurso"""
    resource_id: str
    resource_type: str
    cost: float
    allocated: bool
    allocation_method: str
    business_unit: str
    project: str
    cost_category: str
    owner: str
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'cost': round(self.cost, 2),
            'allocated': self.allocated,
            'allocation_method': self.allocation_method,
            'business_unit': self.business_unit,
            'project': self.project,
            'cost_category': self.cost_category,
            'owner': self.owner,
            'tags': self.tags
        }


@dataclass
class AllocationScorecard:
    """Scorecard de alocação de custos"""
    period_start: datetime
    period_end: datetime
    total_cost: float
    allocated_cost: float
    unallocated_cost: float
    allocation_percent: float
    maturity_level: str
    target_percent: float
    gap_percent: float
    by_business_unit: Dict[str, float] = field(default_factory=dict)
    by_project: Dict[str, float] = field(default_factory=dict)
    by_cost_category: Dict[str, float] = field(default_factory=dict)
    by_owner: Dict[str, float] = field(default_factory=dict)
    unallocated_by_service: Dict[str, float] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'totals': {
                'total_cost': round(self.total_cost, 2),
                'allocated_cost': round(self.allocated_cost, 2),
                'unallocated_cost': round(self.unallocated_cost, 2)
            },
            'metrics': {
                'allocation_percent': round(self.allocation_percent, 2),
                'maturity_level': self.maturity_level,
                'target_percent': self.target_percent,
                'gap_percent': round(self.gap_percent, 2)
            },
            'breakdown': {
                'by_business_unit': {k: round(v, 2) for k, v in self.by_business_unit.items()},
                'by_project': {k: round(v, 2) for k, v in self.by_project.items()},
                'by_cost_category': {k: round(v, 2) for k, v in self.by_cost_category.items()},
                'by_owner': {k: round(v, 2) for k, v in self.by_owner.items()},
                'unallocated_by_service': {k: round(v, 2) for k, v in self.unallocated_by_service.items()}
            },
            'recommendations': self.recommendations
        }


@dataclass
class ShowbackReport:
    """Relatório de Showback por BU/Projeto"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    business_unit: str
    total_cost: float
    by_project: Dict[str, float] = field(default_factory=dict)
    by_service: Dict[str, float] = field(default_factory=dict)
    by_environment: Dict[str, float] = field(default_factory=dict)
    trend_vs_previous: float = 0.0
    budget_variance: float = 0.0
    top_cost_drivers: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at.isoformat(),
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'business_unit': self.business_unit,
            'total_cost': round(self.total_cost, 2),
            'breakdown': {
                'by_project': {k: round(v, 2) for k, v in self.by_project.items()},
                'by_service': {k: round(v, 2) for k, v in self.by_service.items()},
                'by_environment': {k: round(v, 2) for k, v in self.by_environment.items()}
            },
            'analysis': {
                'trend_vs_previous_percent': round(self.trend_vs_previous, 2),
                'budget_variance_percent': round(self.budget_variance, 2),
                'top_cost_drivers': self.top_cost_drivers
            }
        }


class CostAllocationService(BaseAWSService):
    """
    Serviço de Alocação de Custos
    
    Funcionalidades:
    - Define regras de alocação por tag, cost category, conta
    - Calcula scorecard de alocação com metas por nível de maturidade
    - Gera relatórios de showback por BU/projeto
    - Identifica custos não alocados e sugere melhorias
    
    AWS APIs utilizadas:
    - ce:GetCostAndUsage (com GroupBy por tags)
    - ce:GetCostAndUsageWithResources
    - ce:GetCostCategories
    - resourcegroupstaggingapi:GetResources
    """
    
    MATURITY_TARGETS = {
        AllocationLevel.CRAWL: 50.0,
        AllocationLevel.WALK: 80.0,
        AllocationLevel.RUN: 90.0,
        AllocationLevel.FLY: 95.0
    }
    
    DEFAULT_ALLOCATION_TAGS = [
        'CostCenter',
        'Project',
        'Environment',
        'Owner',
        'Application',
        'Team',
        'BusinessUnit'
    ]
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "cost_allocation"
        self._cache = FinOpsCache(default_ttl=300)
        self._allocation_rules: List[CostAllocationRule] = []
        self._load_default_rules()
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce', region_name='us-east-1')
        return boto3.client('ce', region_name='us-east-1')
    
    def _get_tagging_client(self, region: str = None):
        """Obtém cliente boto3 para Resource Groups Tagging API"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('resourcegroupstaggingapi', region_name=region)
        return boto3.client('resourcegroupstaggingapi', region_name=region)
    
    def _load_default_rules(self):
        """Carrega regras padrão de alocação"""
        self._allocation_rules = [
            CostAllocationRule(
                rule_id="rule_costcenter",
                name="Alocação por Cost Center",
                tag_key="CostCenter",
                tag_values=["*"],
                cost_category="direct",
                business_unit="",
                project="",
                owner="",
                priority=1
            ),
            CostAllocationRule(
                rule_id="rule_project",
                name="Alocação por Projeto",
                tag_key="Project",
                tag_values=["*"],
                cost_category="project",
                business_unit="",
                project="",
                owner="",
                priority=2
            ),
            CostAllocationRule(
                rule_id="rule_environment",
                name="Alocação por Ambiente",
                tag_key="Environment",
                tag_values=["production", "prod", "staging", "development", "dev"],
                cost_category="operational",
                business_unit="",
                project="",
                owner="",
                priority=3
            )
        ]
    
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
        """Retorna regras de alocação configuradas"""
        return [rule.to_dict() for rule in self._allocation_rules]
    
    def add_allocation_rule(self, rule: CostAllocationRule):
        """Adiciona regra de alocação"""
        self._allocation_rules.append(rule)
        self._allocation_rules.sort(key=lambda r: r.priority)
    
    def calculate_allocation_scorecard(
        self,
        period_days: int = 30,
        target_level: AllocationLevel = AllocationLevel.WALK
    ) -> AllocationScorecard:
        """
        Calcula scorecard de alocação de custos
        
        Args:
            period_days: Período de análise em dias
            target_level: Nível de maturidade alvo
            
        Returns:
            AllocationScorecard com métricas de alocação
        """
        cache_key = f"allocation_scorecard_{period_days}_{target_level.value}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        total_cost = self._get_total_cost(start_date, end_date)
        
        by_business_unit, allocated_by_bu = self._get_costs_by_tag(
            start_date, end_date, 'BusinessUnit'
        )
        by_project, allocated_by_project = self._get_costs_by_tag(
            start_date, end_date, 'Project'
        )
        by_cost_category, allocated_by_cc = self._get_costs_by_tag(
            start_date, end_date, 'CostCenter'
        )
        by_owner, allocated_by_owner = self._get_costs_by_tag(
            start_date, end_date, 'Owner'
        )
        
        max_allocated = max(
            allocated_by_bu,
            allocated_by_project,
            allocated_by_cc,
            allocated_by_owner
        )
        
        if not by_business_unit:
            by_business_unit = by_cost_category if by_cost_category else {'Unallocated': total_cost}
        
        allocated_cost = max_allocated
        unallocated_cost = total_cost - allocated_cost
        
        if total_cost > 0:
            allocation_percent = (allocated_cost / total_cost) * 100
        else:
            allocation_percent = 0.0
        
        target_percent = self.MATURITY_TARGETS[target_level]
        gap_percent = max(0, target_percent - allocation_percent)
        
        if allocation_percent >= self.MATURITY_TARGETS[AllocationLevel.FLY]:
            maturity_level = AllocationLevel.FLY.value
        elif allocation_percent >= self.MATURITY_TARGETS[AllocationLevel.RUN]:
            maturity_level = AllocationLevel.RUN.value
        elif allocation_percent >= self.MATURITY_TARGETS[AllocationLevel.WALK]:
            maturity_level = AllocationLevel.WALK.value
        else:
            maturity_level = AllocationLevel.CRAWL.value
        
        unallocated_by_service = self._get_unallocated_by_service(start_date, end_date)
        
        recommendations = self._generate_allocation_recommendations(
            allocation_percent,
            target_percent,
            unallocated_by_service
        )
        
        scorecard = AllocationScorecard(
            period_start=start_date,
            period_end=end_date,
            total_cost=total_cost,
            allocated_cost=allocated_cost,
            unallocated_cost=unallocated_cost,
            allocation_percent=allocation_percent,
            maturity_level=maturity_level,
            target_percent=target_percent,
            gap_percent=gap_percent,
            by_business_unit=by_business_unit,
            by_project=by_project,
            by_cost_category=by_cost_category,
            by_owner=by_owner,
            unallocated_by_service=unallocated_by_service,
            recommendations=recommendations
        )
        
        self._cache.set(cache_key, scorecard, ttl=1800)
        return scorecard
    
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
    
    def _get_costs_by_tag(
        self,
        start_date: datetime,
        end_date: datetime,
        tag_key: str
    ) -> Tuple[Dict[str, float], float]:
        """
        Obtém custos agrupados por tag
        
        Returns:
            Tuple (dict por valor de tag, custo total alocado)
        """
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
                    {'Type': 'TAG', 'Key': tag_key}
                ]
            )
            
            by_tag: Dict[str, float] = {}
            total_allocated = 0.0
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    tag_value = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if tag_value.startswith(f'{tag_key}$'):
                        tag_value = tag_value.split('$', 1)[1] or 'Untagged'
                    
                    if tag_value and tag_value.lower() not in ['', 'untagged', 'none']:
                        by_tag[tag_value] = by_tag.get(tag_value, 0) + cost
                        total_allocated += cost
            
            return by_tag, total_allocated
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos por tag {tag_key}: {e}")
            return {}, 0.0
    
    def _get_unallocated_by_service(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Obtém custos não alocados por serviço"""
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
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'TAG', 'Key': 'CostCenter'}
                ]
            )
            
            unallocated: Dict[str, float] = {}
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    keys = group['Keys']
                    service = keys[0]
                    tag_value = keys[1] if len(keys) > 1 else ''
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if not tag_value or tag_value.lower() in ['', 'costcenter$', 'untagged']:
                        unallocated[service] = unallocated.get(service, 0) + cost
            
            return dict(sorted(unallocated.items(), key=lambda x: x[1], reverse=True)[:10])
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos não alocados: {e}")
            return {}
    
    def _generate_allocation_recommendations(
        self,
        current_percent: float,
        target_percent: float,
        unallocated_by_service: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Gera recomendações para melhorar alocação"""
        recommendations = []
        
        if current_percent < target_percent:
            gap = target_percent - current_percent
            recommendations.append({
                'type': 'ALLOCATION_GAP',
                'priority': 'HIGH',
                'title': f'Aumentar alocação de custos em {gap:.1f}%',
                'description': f'Alocação atual: {current_percent:.1f}%. Meta: {target_percent:.1f}%.',
                'action': 'Aplicar tags de alocação aos recursos não tagueados'
            })
        
        for service, cost in list(unallocated_by_service.items())[:3]:
            if cost > 10:
                recommendations.append({
                    'type': 'UNALLOCATED_COST',
                    'priority': 'MEDIUM',
                    'title': f'Alocar custos de {service}',
                    'description': f'${cost:.2f} em custos de {service} não estão alocados',
                    'action': f'Adicionar tags CostCenter/Project aos recursos {service}',
                    'savings': 0,
                    'unallocated_cost': round(cost, 2)
                })
        
        if current_percent < 50:
            recommendations.append({
                'type': 'TAG_POLICY',
                'priority': 'HIGH',
                'title': 'Implementar política de tagging obrigatório',
                'description': 'Alocação abaixo de 50% indica falta de governança de tags',
                'action': 'Ativar AWS Tag Policies e SCPs para enforcement'
            })
        
        return recommendations
    
    def generate_showback_report(
        self,
        business_unit: str,
        period_days: int = 30
    ) -> ShowbackReport:
        """
        Gera relatório de Showback para uma BU
        
        Args:
            business_unit: Nome da Business Unit
            period_days: Período de análise
            
        Returns:
            ShowbackReport com custos detalhados
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date
        
        by_project, _ = self._get_costs_by_tag(start_date, end_date, 'Project')
        by_service = self._get_service_costs_for_bu(start_date, end_date, business_unit)
        by_environment, _ = self._get_costs_by_tag(start_date, end_date, 'Environment')
        
        current_total = sum(by_project.values()) or sum(by_service.values())
        
        previous_by_project, _ = self._get_costs_by_tag(previous_start, previous_end, 'Project')
        previous_total = sum(previous_by_project.values())
        
        if previous_total > 0:
            trend = ((current_total - previous_total) / previous_total) * 100
        else:
            trend = 0.0
        
        top_drivers = []
        for project, cost in sorted(by_project.items(), key=lambda x: x[1], reverse=True)[:5]:
            prev_cost = previous_by_project.get(project, 0)
            if prev_cost > 0:
                change = ((cost - prev_cost) / prev_cost) * 100
            else:
                change = 100.0
            
            top_drivers.append({
                'project': project,
                'cost': round(cost, 2),
                'change_percent': round(change, 2)
            })
        
        return ShowbackReport(
            report_id=f"showback_{business_unit}_{end_date.strftime('%Y%m%d')}",
            generated_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            business_unit=business_unit,
            total_cost=current_total,
            by_project=by_project,
            by_service=by_service,
            by_environment=by_environment,
            trend_vs_previous=trend,
            budget_variance=0.0,
            top_cost_drivers=top_drivers
        )
    
    def _get_service_costs_for_bu(
        self,
        start_date: datetime,
        end_date: datetime,
        business_unit: str
    ) -> Dict[str, float]:
        """Obtém custos por serviço filtrados por BU"""
        try:
            client = self._get_ce_client()
            
            filter_expression = None
            if business_unit:
                filter_expression = {
                    'Tags': {
                        'Key': 'BusinessUnit',
                        'Values': [business_unit],
                        'MatchOptions': ['EQUALS']
                    }
                }
            
            params = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': 'MONTHLY',
                'Metrics': ['UnblendedCost'],
                'GroupBy': [
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            }
            
            if filter_expression:
                params['Filter'] = filter_expression
            
            response = client.get_cost_and_usage(**params)
            
            by_service: Dict[str, float] = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_service[service] = by_service.get(service, 0) + cost
            
            return by_service
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos por serviço para BU: {e}")
            return {}
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        scorecard = self.calculate_allocation_scorecard(period_days)
        return {
            'service': 'cost_allocation',
            'period_days': period_days,
            'total_cost': scorecard.total_cost,
            'allocated_cost': scorecard.allocated_cost,
            'allocation_percent': scorecard.allocation_percent,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        scorecard = self.calculate_allocation_scorecard(30)
        return {
            'service': 'cost_allocation',
            'allocation_percent': scorecard.allocation_percent,
            'maturity_level': scorecard.maturity_level,
            'rules_count': len(self._allocation_rules),
            'cache_stats': self._cache.get_stats()
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de alocação"""
        scorecard = self.calculate_allocation_scorecard(30)
        return scorecard.recommendations
