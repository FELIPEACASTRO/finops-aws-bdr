"""
FinOps AWS - Savings Plans Service
Análise completa de Savings Plans AWS

Integração REAL com AWS Savings Plans API:
- Lista todos os Savings Plans ativos
- Calcula utilização e cobertura
- Detecta SP subutilizados ou expirando
- Gera recomendações de otimização

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Template Method: Fluxo padrão de análise
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger


class SavingsPlanState(Enum):
    """Estados de um Savings Plan"""
    ACTIVE = "active"
    PAYMENT_PENDING = "payment-pending"
    PAYMENT_FAILED = "payment-failed"
    QUEUED = "queued"
    QUEUED_DELETED = "queued-deleted"
    RETIRED = "retired"


class SavingsPlanType(Enum):
    """Tipos de Savings Plans"""
    COMPUTE_SP = "Compute"
    EC2_INSTANCE_SP = "EC2Instance"
    SAGEMAKER_SP = "SageMaker"


@dataclass
class SavingsPlanData:
    """Representa um Savings Plan"""
    savings_plan_id: str
    savings_plan_arn: str
    savings_plan_type: str
    payment_option: str
    offering_id: str
    region: str
    ec2_instance_family: str
    commitment: float
    upfront_payment_amount: float
    recurring_payment_amount: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    state: str = "active"
    currency: str = "USD"
    term_duration_hours: int = 0
    utilization_percent: float = 0.0
    coverage_percent: float = 0.0
    days_until_expiry: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'savings_plan_id': self.savings_plan_id,
            'savings_plan_arn': self.savings_plan_arn,
            'savings_plan_type': self.savings_plan_type,
            'payment_option': self.payment_option,
            'offering_id': self.offering_id,
            'region': self.region,
            'ec2_instance_family': self.ec2_instance_family,
            'commitment': self.commitment,
            'upfront_payment_amount': self.upfront_payment_amount,
            'recurring_payment_amount': self.recurring_payment_amount,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'state': self.state,
            'currency': self.currency,
            'term_duration_hours': self.term_duration_hours,
            'utilization_percent': self.utilization_percent,
            'coverage_percent': self.coverage_percent,
            'days_until_expiry': self.days_until_expiry,
            'tags': self.tags
        }


@dataclass
class SavingsPlanUtilization:
    """Dados de utilização de Savings Plans"""
    time_period_start: str
    time_period_end: str
    total_commitment: float
    used_commitment: float
    unused_commitment: float
    utilization_percentage: float
    net_savings: float
    on_demand_cost_equivalent: float
    savings_plans_cost: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_period': {
                'start': self.time_period_start,
                'end': self.time_period_end
            },
            'total_commitment': self.total_commitment,
            'used_commitment': self.used_commitment,
            'unused_commitment': self.unused_commitment,
            'utilization_percentage': self.utilization_percentage,
            'net_savings': self.net_savings,
            'on_demand_cost_equivalent': self.on_demand_cost_equivalent,
            'savings_plans_cost': self.savings_plans_cost
        }


@dataclass
class SavingsPlanCoverage:
    """Dados de cobertura de Savings Plans"""
    time_period_start: str
    time_period_end: str
    on_demand_cost: float
    spend_covered_by_sp: float
    total_cost: float
    coverage_percentage: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_period': {
                'start': self.time_period_start,
                'end': self.time_period_end
            },
            'on_demand_cost': self.on_demand_cost,
            'spend_covered_by_sp': self.spend_covered_by_sp,
            'total_cost': self.total_cost,
            'coverage_percentage': self.coverage_percentage
        }


class SavingsPlansService(BaseAWSService):
    """
    Serviço FinOps para AWS Savings Plans
    
    Funcionalidades:
    - Lista Savings Plans ativos
    - Calcula utilização e cobertura
    - Detecta SP subutilizados
    - Alerta SP expirando
    - Gera recomendações de otimização
    
    AWS APIs utilizadas:
    - savingsplans:DescribeSavingsPlans
    - ce:GetSavingsPlansUtilization
    - ce:GetSavingsPlansCoverage
    - ce:GetSavingsPlansPurchaseRecommendation
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "savingsplans"
    
    def _get_sp_client(self):
        """Obtém cliente boto3 para Savings Plans"""
        if self._client_factory:
            return self._client_factory.get_client('savingsplans')
        return boto3.client('savingsplans')
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce')
        return boto3.client('ce', region_name='us-east-1')
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_sp_client()
            client.describe_savings_plans(maxResults=1)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para acessar Savings Plans")
            return False
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            return False
    
    def get_savings_plans(self, states: Optional[List[str]] = None) -> List[SavingsPlanData]:
        """Obtém todos os Savings Plans"""
        savings_plans = []
        try:
            client = self._get_sp_client()
            
            params = {}
            if states:
                params['states'] = states
            
            next_token = None
            while True:
                if next_token:
                    params['nextToken'] = next_token
                params['maxResults'] = 100
                
                response = client.describe_savings_plans(**params)
                
                for sp in response.get('savingsPlans', []):
                    parsed = self._parse_savings_plan(sp)
                    savings_plans.append(parsed)
                
                next_token = response.get('nextToken')
                if not next_token:
                    break
            
            self.logger.info(f"Encontrados {len(savings_plans)} Savings Plans")
            return savings_plans
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: savingsplans:DescribeSavingsPlans")
            else:
                self.logger.error(f"Erro ao listar Savings Plans: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter Savings Plans: {e}")
            return []
    
    def _parse_savings_plan(self, sp: Dict) -> SavingsPlanData:
        """Parse de um Savings Plan"""
        start_time = None
        end_time = None
        
        if 'start' in sp:
            try:
                start_time = datetime.fromisoformat(str(sp['start']).replace('Z', '+00:00'))
            except Exception:
                pass
        if 'end' in sp:
            try:
                end_time = datetime.fromisoformat(str(sp['end']).replace('Z', '+00:00'))
            except Exception:
                pass
        
        days_until_expiry = 0
        if end_time:
            delta = end_time - datetime.now(end_time.tzinfo)
            days_until_expiry = max(0, delta.days)
        
        tags = {}
        for tag in sp.get('tags', {}).items():
            tags[tag[0]] = tag[1]
        
        return SavingsPlanData(
            savings_plan_id=sp.get('savingsPlanId', ''),
            savings_plan_arn=sp.get('savingsPlanArn', ''),
            savings_plan_type=sp.get('savingsPlanType', ''),
            payment_option=sp.get('paymentOption', ''),
            offering_id=sp.get('offeringId', ''),
            region=sp.get('region', ''),
            ec2_instance_family=sp.get('ec2InstanceFamily', ''),
            commitment=float(sp.get('commitment', 0)),
            upfront_payment_amount=float(sp.get('upfrontPaymentAmount', 0)),
            recurring_payment_amount=float(sp.get('recurringPaymentAmount', 0)),
            start_time=start_time,
            end_time=end_time,
            state=sp.get('state', 'active'),
            currency=sp.get('currency', 'USD'),
            term_duration_hours=int(sp.get('termDurationInSeconds', 0)) // 3600,
            days_until_expiry=days_until_expiry,
            tags=tags
        )
    
    def get_utilization(self, days_back: int = 30) -> SavingsPlanUtilization:
        """Obtém dados de utilização de Savings Plans"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = client.get_savings_plans_utilization(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            total = response.get('Total', {})
            utilization = total.get('Utilization', {})
            amortized = total.get('AmortizedCommitment', {})
            savings = total.get('Savings', {})
            
            return SavingsPlanUtilization(
                time_period_start=start_date,
                time_period_end=end_date,
                total_commitment=float(utilization.get('TotalCommitment', 0)),
                used_commitment=float(utilization.get('UsedCommitment', 0)),
                unused_commitment=float(utilization.get('UnusedCommitment', 0)),
                utilization_percentage=float(utilization.get('UtilizationPercentage', 0)),
                net_savings=float(savings.get('NetSavings', 0)),
                on_demand_cost_equivalent=float(savings.get('OnDemandCostEquivalent', 0)),
                savings_plans_cost=float(amortized.get('TotalAmortizedCommitment', 0))
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'DataUnavailableException':
                self.logger.info("Dados de utilização de SP não disponíveis")
            else:
                self.logger.error(f"Erro ao obter utilização SP: {e}")
            return SavingsPlanUtilization(
                time_period_start="", time_period_end="",
                total_commitment=0, used_commitment=0, unused_commitment=0,
                utilization_percentage=0, net_savings=0,
                on_demand_cost_equivalent=0, savings_plans_cost=0
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter utilização: {e}")
            return SavingsPlanUtilization(
                time_period_start="", time_period_end="",
                total_commitment=0, used_commitment=0, unused_commitment=0,
                utilization_percentage=0, net_savings=0,
                on_demand_cost_equivalent=0, savings_plans_cost=0
            )
    
    def get_coverage(self, days_back: int = 30) -> SavingsPlanCoverage:
        """Obtém dados de cobertura de Savings Plans"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = client.get_savings_plans_coverage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            total = response.get('Total', {})
            coverage = total.get('Coverage', {})
            
            return SavingsPlanCoverage(
                time_period_start=start_date,
                time_period_end=end_date,
                on_demand_cost=float(coverage.get('OnDemandCost', 0)),
                spend_covered_by_sp=float(coverage.get('SpendCoveredBySavingsPlans', 0)),
                total_cost=float(coverage.get('TotalCost', 0)),
                coverage_percentage=float(coverage.get('CoveragePercentage', 0))
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'DataUnavailableException':
                self.logger.info("Dados de cobertura de SP não disponíveis")
            else:
                self.logger.error(f"Erro ao obter cobertura SP: {e}")
            return SavingsPlanCoverage(
                time_period_start="", time_period_end="",
                on_demand_cost=0, spend_covered_by_sp=0,
                total_cost=0, coverage_percentage=0
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter cobertura: {e}")
            return SavingsPlanCoverage(
                time_period_start="", time_period_end="",
                on_demand_cost=0, spend_covered_by_sp=0,
                total_cost=0, coverage_percentage=0
            )
    
    def get_purchase_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de compra de Savings Plans"""
        recommendations = []
        try:
            client = self._get_ce_client()
            
            for sp_type in ['COMPUTE_SP', 'EC2_INSTANCE_SP']:
                try:
                    response = client.get_savings_plans_purchase_recommendation(
                        SavingsPlansType=sp_type,
                        LookbackPeriodInDays='SIXTY_DAYS',
                        TermInYears='ONE_YEAR',
                        PaymentOption='NO_UPFRONT'
                    )
                    
                    rec = response.get('SavingsPlansPurchaseRecommendation', {})
                    details = rec.get('SavingsPlansPurchaseRecommendationDetails', [])
                    
                    for detail in details[:5]:
                        hourly_commitment = float(detail.get('HourlyCommitmentToPurchase', 0))
                        monthly_savings = float(detail.get('EstimatedMonthlySavingsAmount', 0))
                        roi = float(detail.get('EstimatedROI', 0))
                        on_demand_cost = float(detail.get('CurrentOnDemandSpend', 0))
                        
                        if monthly_savings > 0:
                            recommendations.append({
                                'type': sp_type,
                                'hourly_commitment': hourly_commitment,
                                'monthly_savings': monthly_savings,
                                'roi_percentage': roi * 100,
                                'current_on_demand_spend': on_demand_cost,
                                'upfront_cost': float(detail.get('UpfrontCost', 0)),
                                'estimated_savings_percentage': float(detail.get('EstimatedSavingsPercentage', 0))
                            })
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao obter recomendações de {sp_type}: {e}")
                    continue
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Erro ao obter recomendações de SP: {e}")
            return []
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Obtém Savings Plans como recursos"""
        savings_plans = self.get_savings_plans(states=['active', 'queued'])
        utilization = self.get_utilization()
        
        for sp in savings_plans:
            sp.utilization_percent = utilization.utilization_percentage
        
        return [sp.to_dict() for sp in savings_plans]
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """Obtém resumo de custos dos Savings Plans"""
        savings_plans = self.get_savings_plans(states=['active'])
        utilization = self.get_utilization(days_back=period_days)
        
        total_commitment = sum(sp.commitment for sp in savings_plans)
        
        cost_by_resource = {
            sp.savings_plan_id: sp.commitment * 730
            for sp in savings_plans
        }
        
        trend = "STABLE"
        if utilization.unused_commitment > 0:
            trend = "DECREASING"
        
        return ServiceCost(
            service_name='savingsplans',
            total_cost=round(total_commitment * 730, 2),
            period_days=period_days,
            cost_by_resource=cost_by_resource,
            trend=trend,
            currency='USD'
        )
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Savings Plans"""
        savings_plans = self.get_savings_plans(states=['active'])
        utilization = self.get_utilization()
        coverage = self.get_coverage()
        
        by_type: Dict[str, int] = {}
        expiring_30d = 0
        expiring_60d = 0
        expiring_90d = 0
        
        for sp in savings_plans:
            by_type[sp.savings_plan_type] = by_type.get(sp.savings_plan_type, 0) + 1
            if sp.days_until_expiry <= 30:
                expiring_30d += 1
            elif sp.days_until_expiry <= 60:
                expiring_60d += 1
            elif sp.days_until_expiry <= 90:
                expiring_90d += 1
        
        return ServiceMetrics(
            service_name='savingsplans',
            resource_count=len(savings_plans),
            metrics={
                'utilization_percent': round(utilization.utilization_percentage, 2),
                'coverage_percent': round(coverage.coverage_percentage, 2),
                'unused_commitment_usd': round(utilization.unused_commitment, 2),
                'net_savings_usd': round(utilization.net_savings, 2),
                'by_type': by_type,
                'expiring_30d': expiring_30d,
                'expiring_60d': expiring_60d,
                'expiring_90d': expiring_90d
            },
            utilization=round(utilization.utilization_percentage, 2)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização de Savings Plans"""
        recommendations: List[ServiceRecommendation] = []
        savings_plans = self.get_savings_plans(states=['active'])
        utilization = self.get_utilization()
        coverage = self.get_coverage()
        purchase_recs = self.get_purchase_recommendations()
        
        if utilization.utilization_percentage < 80 and utilization.unused_commitment > 0:
            recommendations.append(ServiceRecommendation(
                resource_id='savings_plans',
                resource_type='savings_plan',
                recommendation_type='LOW_UTILIZATION',
                description=(
                    f'A utilização dos Savings Plans está em apenas {utilization.utilization_percentage:.1f}%. '
                    f'Commitment não utilizado: ${utilization.unused_commitment:,.2f}. '
                    f'Isso representa desperdício de capacidade contratada. '
                    f'Revise se os workloads estão adequados aos SP contratados.'
                ),
                estimated_savings=utilization.unused_commitment,
                priority='HIGH',
                title=f'Savings Plans com {utilization.utilization_percentage:.1f}% de utilização',
                action='Revisar workloads e considerar ajustar SP no próximo ciclo'
            ))
        
        if coverage.coverage_percentage < 50 and coverage.on_demand_cost > 100:
            recommendations.append(ServiceRecommendation(
                resource_id='savings_plans_coverage',
                resource_type='savings_plan',
                recommendation_type='LOW_COVERAGE',
                description=(
                    f'Apenas {coverage.coverage_percentage:.1f}% do gasto elegível está coberto por SP. '
                    f'Custo On-Demand: ${coverage.on_demand_cost:,.2f}. '
                    f'Aumentar cobertura pode gerar economia significativa.'
                ),
                estimated_savings=coverage.on_demand_cost * 0.3,
                priority='MEDIUM',
                title=f'Apenas {coverage.coverage_percentage:.1f}% de cobertura de Savings Plans',
                action='Avaliar compra de Savings Plans adicionais'
            ))
        
        for sp in savings_plans:
            if sp.days_until_expiry <= 30 and sp.days_until_expiry > 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=sp.savings_plan_id,
                    resource_type='savings_plan',
                    recommendation_type='EXPIRING_SOON',
                    description=(
                        f'O Savings Plan {sp.savings_plan_id} ({sp.savings_plan_type}) '
                        f'expira em {sp.days_until_expiry} dias. '
                        f'Commitment: ${sp.commitment:.4f}/hora. '
                        f'Planeje renovação para manter economia.'
                    ),
                    estimated_savings=sp.commitment * 730 * 0.3,
                    priority='CRITICAL',
                    title=f'Savings Plan expira em {sp.days_until_expiry} dias',
                    action='Renovar ou substituir Savings Plan antes da expiração'
                ))
            elif sp.days_until_expiry <= 60:
                recommendations.append(ServiceRecommendation(
                    resource_id=sp.savings_plan_id,
                    resource_type='savings_plan',
                    recommendation_type='EXPIRING_60D',
                    description=(
                        f'O Savings Plan {sp.savings_plan_id} ({sp.savings_plan_type}) '
                        f'expira em {sp.days_until_expiry} dias. '
                        f'Avalie a renovação.'
                    ),
                    estimated_savings=sp.commitment * 730 * 0.3,
                    priority='HIGH',
                    title=f'Savings Plan expira em {sp.days_until_expiry} dias',
                    action='Planejar renovação do Savings Plan'
                ))
        
        for rec in purchase_recs[:3]:
            if rec.get('monthly_savings', 0) > 50:
                recommendations.append(ServiceRecommendation(
                    resource_id=f"new_{rec['type']}",
                    resource_type='savings_plan',
                    recommendation_type='PURCHASE_RECOMMENDATION',
                    description=(
                        f"Recomendação AWS: Comprar {rec['type']} com commitment de "
                        f"${rec['hourly_commitment']:.4f}/hora para economizar "
                        f"${rec['monthly_savings']:,.2f}/mês ({rec['estimated_savings_percentage']:.1f}%). "
                        f"ROI estimado: {rec['roi_percentage']:.1f}%."
                    ),
                    estimated_savings=rec['monthly_savings'] * 12,
                    priority='MEDIUM',
                    title=f"Comprar {rec['type']}: economia de ${rec['monthly_savings']:,.2f}/mês",
                    action=f"Comprar {rec['type']} via Console AWS"
                ))
        
        if not savings_plans and not purchase_recs:
            recommendations.append(ServiceRecommendation(
                resource_id='account',
                resource_type='savings_plan',
                recommendation_type='NO_SAVINGS_PLANS',
                description=(
                    'A conta não possui Savings Plans ativos. '
                    'Savings Plans podem oferecer até 72% de desconto '
                    'em relação a preços On-Demand. '
                    'Avalie seu uso para identificar oportunidades.'
                ),
                estimated_savings=0,
                priority='MEDIUM',
                title='Nenhum Savings Plan ativo',
                action='Usar Cost Explorer para analisar recomendações de SP'
            ))
        
        return recommendations
    
    def analyze_usage(self) -> Dict[str, Any]:
        """Analisa padrões de uso dos Savings Plans"""
        savings_plans = self.get_savings_plans(states=['active'])
        utilization = self.get_utilization()
        coverage = self.get_coverage()
        recommendations = self.get_recommendations()
        
        by_type: Dict[str, Dict[str, Any]] = {}
        for sp in savings_plans:
            sp_type = sp.savings_plan_type
            if sp_type not in by_type:
                by_type[sp_type] = {'count': 0, 'total_commitment': 0}
            by_type[sp_type]['count'] += 1
            by_type[sp_type]['total_commitment'] += sp.commitment
        
        expiring_soon = [sp.to_dict() for sp in savings_plans if sp.days_until_expiry <= 90]
        
        return {
            'service': 'savingsplans',
            'summary': {
                'active_sp_count': len(savings_plans),
                'utilization_percent': round(utilization.utilization_percentage, 2),
                'coverage_percent': round(coverage.coverage_percentage, 2),
                'unused_commitment_usd': round(utilization.unused_commitment, 2),
                'net_savings_usd': round(utilization.net_savings, 2)
            },
            'by_type': by_type,
            'expiring_within_90d': expiring_soon,
            'recommendations_count': len(recommendations),
            'optimization_opportunities': [r.title for r in recommendations[:5]]
        }
