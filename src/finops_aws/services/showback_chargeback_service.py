"""
FinOps AWS - Showback/Chargeback Service
Serviço de Showback e Chargeback para FinOps

Este serviço implementa:
- Showback: Relatórios de custos por BU/projeto (informativo)
- Chargeback: Workflow de faturamento interno com invoices
- Integração com Cost Allocation para dados de alocação
- Geração automática de relatórios mensais

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Builder: Construção de invoices/relatórios
- Observer: Notificação de novos relatórios
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import uuid
import json

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class InvoiceStatus(Enum):
    """Status de uma invoice de chargeback"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    PAID = "paid"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class ChargebackType(Enum):
    """Tipos de chargeback"""
    DIRECT = "direct"
    PROPORTIONAL = "proportional"
    FIXED = "fixed"
    TIERED = "tiered"


@dataclass
class ChargebackRule:
    """Regra de chargeback"""
    rule_id: str
    name: str
    business_unit: str
    chargeback_type: ChargebackType
    allocation_tag: str
    rate_multiplier: float = 1.0
    fixed_amount: float = 0.0
    tiers: List[Dict[str, float]] = field(default_factory=list)
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'business_unit': self.business_unit,
            'chargeback_type': self.chargeback_type.value,
            'allocation_tag': self.allocation_tag,
            'rate_multiplier': self.rate_multiplier,
            'fixed_amount': self.fixed_amount,
            'tiers': self.tiers,
            'active': self.active
        }


@dataclass
class ChargebackInvoice:
    """Invoice de chargeback"""
    invoice_id: str
    invoice_number: str
    business_unit: str
    period_start: datetime
    period_end: datetime
    created_at: datetime
    status: InvoiceStatus
    subtotal: float
    adjustments: float
    total: float
    currency: str = "USD"
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice_number,
            'business_unit': self.business_unit,
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'amounts': {
                'subtotal': round(self.subtotal, 2),
                'adjustments': round(self.adjustments, 2),
                'total': round(self.total, 2)
            },
            'currency': self.currency,
            'line_items': self.line_items,
            'notes': self.notes,
            'approval': {
                'approved_by': self.approved_by,
                'approved_at': self.approved_at.isoformat() if self.approved_at else None
            }
        }


@dataclass
class ShowbackSummary:
    """Resumo de Showback"""
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    total_cost: float
    by_business_unit: Dict[str, float] = field(default_factory=dict)
    by_project: Dict[str, float] = field(default_factory=dict)
    by_environment: Dict[str, float] = field(default_factory=dict)
    by_owner: Dict[str, float] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'generated_at': self.generated_at.isoformat(),
            'total_cost': round(self.total_cost, 2),
            'breakdown': {
                'by_business_unit': {k: round(v, 2) for k, v in self.by_business_unit.items()},
                'by_project': {k: round(v, 2) for k, v in self.by_project.items()},
                'by_environment': {k: round(v, 2) for k, v in self.by_environment.items()},
                'by_owner': {k: round(v, 2) for k, v in self.by_owner.items()}
            },
            'trend_analysis': self.trend_analysis
        }


class ShowbackChargebackService(BaseAWSService):
    """
    Serviço de Showback e Chargeback
    
    Funcionalidades:
    - Gera relatórios de showback por BU/projeto/owner
    - Cria invoices de chargeback com workflow de aprovação
    - Aplica regras de chargeback (direct, proportional, tiered)
    - Rastreia histórico de faturamento
    
    AWS APIs utilizadas:
    - ce:GetCostAndUsage
    - ce:GetCostAndUsageWithResources
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "showback_chargeback"
        self._cache = FinOpsCache(default_ttl=300)
        self._chargeback_rules: List[ChargebackRule] = []
        self._invoices: Dict[str, ChargebackInvoice] = {}
        self._load_default_rules()
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce', region_name='us-east-1')
        return boto3.client('ce', region_name='us-east-1')
    
    def _load_default_rules(self):
        """Carrega regras padrão de chargeback"""
        self._chargeback_rules = [
            ChargebackRule(
                rule_id="rule_direct_costcenter",
                name="Chargeback Direto por Cost Center",
                business_unit="*",
                chargeback_type=ChargebackType.DIRECT,
                allocation_tag="CostCenter",
                rate_multiplier=1.0
            ),
            ChargebackRule(
                rule_id="rule_shared_infrastructure",
                name="Infraestrutura Compartilhada",
                business_unit="*",
                chargeback_type=ChargebackType.PROPORTIONAL,
                allocation_tag="shared",
                rate_multiplier=1.0
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
        """Retorna regras de chargeback e invoices"""
        return {
            'rules': [rule.to_dict() for rule in self._chargeback_rules],
            'invoices_count': len(self._invoices),
            'pending_invoices': len([i for i in self._invoices.values() 
                                    if i.status == InvoiceStatus.PENDING_APPROVAL])
        }
    
    def generate_showback_summary(
        self,
        period_days: int = 30
    ) -> ShowbackSummary:
        """
        Gera resumo de showback para o período
        
        Args:
            period_days: Período de análise
            
        Returns:
            ShowbackSummary com custos por dimensão
        """
        cache_key = f"showback_summary_{period_days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date
        
        by_bu = self._get_costs_by_tag('BusinessUnit', start_date, end_date)
        by_project = self._get_costs_by_tag('Project', start_date, end_date)
        by_env = self._get_costs_by_tag('Environment', start_date, end_date)
        by_owner = self._get_costs_by_tag('Owner', start_date, end_date)
        
        total_cost = self._get_total_cost(start_date, end_date)
        
        previous_total = self._get_total_cost(previous_start, previous_end)
        if previous_total > 0:
            trend_percent = ((total_cost - previous_total) / previous_total) * 100
        else:
            trend_percent = 0.0
        
        trend_analysis = {
            'current_period_total': round(total_cost, 2),
            'previous_period_total': round(previous_total, 2),
            'change_percent': round(trend_percent, 2),
            'trend': 'increasing' if trend_percent > 5 else 'decreasing' if trend_percent < -5 else 'stable'
        }
        
        summary = ShowbackSummary(
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.utcnow(),
            total_cost=total_cost,
            by_business_unit=by_bu,
            by_project=by_project,
            by_environment=by_env,
            by_owner=by_owner,
            trend_analysis=trend_analysis
        )
        
        self._cache.set(cache_key, summary, ttl=1800)
        return summary
    
    def _get_costs_by_tag(
        self,
        tag_key: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Obtém custos agrupados por tag"""
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
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    tag_value = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if tag_value.startswith(f'{tag_key}$'):
                        tag_value = tag_value.split('$', 1)[1] or 'Untagged'
                    
                    if tag_value and cost > 0:
                        by_tag[tag_value] = by_tag.get(tag_value, 0) + cost
            
            return dict(sorted(by_tag.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos por tag {tag_key}: {e}")
            return {}
    
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
    
    def create_chargeback_invoice(
        self,
        business_unit: str,
        period_start: datetime,
        period_end: datetime
    ) -> ChargebackInvoice:
        """
        Cria invoice de chargeback para uma BU
        
        Args:
            business_unit: Nome da Business Unit
            period_start: Início do período
            period_end: Fim do período
            
        Returns:
            ChargebackInvoice criada
        """
        invoice_id = str(uuid.uuid4())
        invoice_number = f"CB-{business_unit[:3].upper()}-{period_end.strftime('%Y%m')}-{invoice_id[:8].upper()}"
        
        by_service = self._get_costs_by_service_for_bu(business_unit, period_start, period_end)
        by_project = self._get_costs_by_project_for_bu(business_unit, period_start, period_end)
        
        line_items = []
        subtotal = 0.0
        
        for service, cost in by_service.items():
            if cost > 0:
                line_items.append({
                    'description': f'AWS {service}',
                    'category': 'compute' if 'EC2' in service or 'Lambda' in service else 'storage' if 'S3' in service else 'other',
                    'quantity': 1,
                    'unit_price': round(cost, 2),
                    'total': round(cost, 2)
                })
                subtotal += cost
        
        adjustments = self._calculate_adjustments(business_unit, subtotal)
        total = subtotal + adjustments
        
        invoice = ChargebackInvoice(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            business_unit=business_unit,
            period_start=period_start,
            period_end=period_end,
            created_at=datetime.utcnow(),
            status=InvoiceStatus.DRAFT,
            subtotal=subtotal,
            adjustments=adjustments,
            total=total,
            line_items=line_items
        )
        
        self._invoices[invoice_id] = invoice
        self.logger.info(f"Invoice criada: {invoice_number} para {business_unit}: ${total:.2f}")
        
        return invoice
    
    def _get_costs_by_service_for_bu(
        self,
        business_unit: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Obtém custos por serviço para uma BU"""
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
                ],
                Filter={
                    'Tags': {
                        'Key': 'BusinessUnit',
                        'Values': [business_unit],
                        'MatchOptions': ['EQUALS']
                    }
                }
            )
            
            by_service: Dict[str, float] = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_service[service] = by_service.get(service, 0) + cost
            
            return by_service
            
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'ValidationException':
                return self._get_costs_by_service_fallback(start_date, end_date)
            self.logger.error(f"Erro ao obter custos por serviço para BU: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Erro ao obter custos por serviço para BU: {e}")
            return {}
    
    def _get_costs_by_service_fallback(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Fallback para obter custos por serviço sem filtro de BU"""
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
            
            by_service: Dict[str, float] = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_service[service] = by_service.get(service, 0) + cost
            
            return by_service
            
        except Exception as e:
            self.logger.error(f"Erro no fallback de custos por serviço: {e}")
            return {}
    
    def _get_costs_by_project_for_bu(
        self,
        business_unit: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Obtém custos por projeto para uma BU"""
        return self._get_costs_by_tag('Project', start_date, end_date)
    
    def _calculate_adjustments(
        self,
        business_unit: str,
        subtotal: float
    ) -> float:
        """Calcula ajustes baseados em regras de chargeback"""
        adjustments = 0.0
        
        for rule in self._chargeback_rules:
            if rule.active and (rule.business_unit == "*" or rule.business_unit == business_unit):
                if rule.chargeback_type == ChargebackType.FIXED:
                    adjustments += rule.fixed_amount
                elif rule.chargeback_type == ChargebackType.PROPORTIONAL:
                    adjustments += subtotal * (rule.rate_multiplier - 1.0)
        
        return adjustments
    
    def submit_invoice_for_approval(self, invoice_id: str) -> bool:
        """Submete invoice para aprovação"""
        if invoice_id not in self._invoices:
            return False
        
        invoice = self._invoices[invoice_id]
        if invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.PENDING_APPROVAL
            self.logger.info(f"Invoice {invoice.invoice_number} submetida para aprovação")
            return True
        
        return False
    
    def approve_invoice(self, invoice_id: str, approver: str) -> bool:
        """Aprova uma invoice"""
        if invoice_id not in self._invoices:
            return False
        
        invoice = self._invoices[invoice_id]
        if invoice.status == InvoiceStatus.PENDING_APPROVAL:
            invoice.status = InvoiceStatus.APPROVED
            invoice.approved_by = approver
            invoice.approved_at = datetime.utcnow()
            self.logger.info(f"Invoice {invoice.invoice_number} aprovada por {approver}")
            return True
        
        return False
    
    def get_invoice(self, invoice_id: str) -> Optional[ChargebackInvoice]:
        """Obtém invoice por ID"""
        return self._invoices.get(invoice_id)
    
    def get_invoices_by_bu(self, business_unit: str) -> List[ChargebackInvoice]:
        """Lista invoices de uma BU"""
        return [inv for inv in self._invoices.values() if inv.business_unit == business_unit]
    
    def get_pending_invoices(self) -> List[ChargebackInvoice]:
        """Lista invoices pendentes de aprovação"""
        return [inv for inv in self._invoices.values() 
                if inv.status == InvoiceStatus.PENDING_APPROVAL]
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        summary = self.generate_showback_summary(period_days)
        return {
            'service': 'showback_chargeback',
            'period_days': period_days,
            'total_cost': summary.total_cost,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        summary = self.generate_showback_summary(30)
        return {
            'service': 'showback_chargeback',
            'business_units_count': len(summary.by_business_unit),
            'projects_count': len(summary.by_project),
            'invoices_total': len(self._invoices),
            'invoices_pending': len(self.get_pending_invoices()),
            'rules_count': len(self._chargeback_rules)
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de showback/chargeback"""
        recommendations = []
        
        summary = self.generate_showback_summary(30)
        
        if 'Untagged' in summary.by_business_unit:
            untagged_cost = summary.by_business_unit['Untagged']
            if untagged_cost > 100:
                recommendations.append({
                    'type': 'UNTAGGED_COSTS',
                    'priority': 'HIGH',
                    'title': 'Custos sem Business Unit definida',
                    'description': f'${untagged_cost:.2f} em custos não podem ser cobrados de BUs',
                    'savings': 0,
                    'action': 'Aplicar tag BusinessUnit aos recursos'
                })
        
        trend = summary.trend_analysis.get('change_percent', 0)
        if trend > 20:
            recommendations.append({
                'type': 'COST_SPIKE',
                'priority': 'MEDIUM',
                'title': f'Aumento de {trend:.1f}% nos custos',
                'description': 'Custos aumentaram significativamente no período',
                'savings': 0,
                'action': 'Revisar novos recursos e otimizar onde possível'
            })
        
        return recommendations
