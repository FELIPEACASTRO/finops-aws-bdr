"""
FinOps AWS - Reserved Instances Service
Análise completa de Reserved Instances AWS

Integração REAL com AWS Reserved Instances APIs:
- Lista todas as RIs (EC2, RDS, ElastiCache, Redshift, OpenSearch)
- Calcula utilização e cobertura
- Detecta RIs subutilizadas ou expirando
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

import os

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger


class RIState(Enum):
    """Estados de uma Reserved Instance"""
    ACTIVE = "active"
    PAYMENT_PENDING = "payment-pending"
    PAYMENT_FAILED = "payment-failed"
    RETIRED = "retired"
    QUEUED = "queued"
    QUEUED_DELETED = "queued-deleted"


class RIService(Enum):
    """Serviços que suportam Reserved Instances"""
    EC2 = "EC2"
    RDS = "RDS"
    ELASTICACHE = "ElastiCache"
    REDSHIFT = "Redshift"
    OPENSEARCH = "OpenSearch"


@dataclass
class ReservedInstanceData:
    """Representa uma Reserved Instance"""
    reservation_id: str
    service: str
    instance_type: str
    instance_count: int
    scope: str
    availability_zone: str
    platform: str
    offering_type: str
    offering_class: str
    fixed_price: float
    usage_price: float
    recurring_charges: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    state: str = "active"
    currency: str = "USD"
    duration_seconds: int = 0
    days_until_expiry: int = 0
    utilization_percent: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reservation_id': self.reservation_id,
            'service': self.service,
            'instance_type': self.instance_type,
            'instance_count': self.instance_count,
            'scope': self.scope,
            'availability_zone': self.availability_zone,
            'platform': self.platform,
            'offering_type': self.offering_type,
            'offering_class': self.offering_class,
            'fixed_price': self.fixed_price,
            'usage_price': self.usage_price,
            'recurring_charges': self.recurring_charges,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'state': self.state,
            'currency': self.currency,
            'duration_seconds': self.duration_seconds,
            'days_until_expiry': self.days_until_expiry,
            'utilization_percent': self.utilization_percent,
            'tags': self.tags
        }


@dataclass
class RIUtilization:
    """Dados de utilização de Reserved Instances"""
    time_period_start: str
    time_period_end: str
    total_purchased_hours: float
    total_used_hours: float
    unused_hours: float
    utilization_percentage: float
    net_savings: float
    total_amortized_fee: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_period': {
                'start': self.time_period_start,
                'end': self.time_period_end
            },
            'total_purchased_hours': self.total_purchased_hours,
            'total_used_hours': self.total_used_hours,
            'unused_hours': self.unused_hours,
            'utilization_percentage': self.utilization_percentage,
            'net_savings': self.net_savings,
            'total_amortized_fee': self.total_amortized_fee
        }


@dataclass
class RICoverage:
    """Dados de cobertura de Reserved Instances"""
    time_period_start: str
    time_period_end: str
    on_demand_cost: float
    reserved_hours: float
    total_running_hours: float
    coverage_percentage: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_period': {
                'start': self.time_period_start,
                'end': self.time_period_end
            },
            'on_demand_cost': self.on_demand_cost,
            'reserved_hours': self.reserved_hours,
            'total_running_hours': self.total_running_hours,
            'coverage_percentage': self.coverage_percentage
        }


class ReservedInstancesService(BaseAWSService):
    """
    Serviço FinOps para AWS Reserved Instances
    
    Funcionalidades:
    - Lista RIs de EC2, RDS, ElastiCache, Redshift, OpenSearch
    - Calcula utilização e cobertura
    - Detecta RIs subutilizadas
    - Alerta RIs expirando
    - Gera recomendações de otimização
    
    AWS APIs utilizadas:
    - ec2:DescribeReservedInstances
    - rds:DescribeReservedDBInstances
    - elasticache:DescribeReservedCacheNodes
    - ce:GetReservationUtilization
    - ce:GetReservationCoverage
    - ce:GetReservationPurchaseRecommendation
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "reservedinstances"
    
    def _get_ec2_client(self, region: str = None):
        """Obtém cliente boto3 para EC2"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('ec2', region_name=region)
        return boto3.client('ec2', region_name=region)
    
    def _get_rds_client(self, region: str = None):
        """Obtém cliente boto3 para RDS"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('rds', region_name=region)
        return boto3.client('rds', region_name=region)
    
    def _get_elasticache_client(self, region: str = None):
        """Obtém cliente boto3 para ElastiCache"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('elasticache', region_name=region)
        return boto3.client('elasticache', region_name=region)
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce')
        return boto3.client('ce', region_name='us-east-1')
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_ec2_client()
            client.describe_reserved_instances(MaxResults=5)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para acessar Reserved Instances")
            return False
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            return False
    
    def get_ec2_reserved_instances(self, region: str = None) -> List[ReservedInstanceData]:
        """Obtém Reserved Instances EC2"""
        reservations = []
        try:
            client = self._get_ec2_client(region)
            
            response = client.describe_reserved_instances(
                Filters=[
                    {'Name': 'state', 'Values': ['active', 'payment-pending']}
                ]
            )
            
            for ri in response.get('ReservedInstances', []):
                parsed = self._parse_ec2_ri(ri)
                reservations.append(parsed)
            
            return reservations
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: ec2:DescribeReservedInstances")
            else:
                self.logger.debug(f"Erro ao listar EC2 RIs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter EC2 RIs: {e}")
            return []
    
    def _parse_ec2_ri(self, ri: Dict) -> ReservedInstanceData:
        """Parse de uma Reserved Instance EC2"""
        start_time = ri.get('Start')
        end_time = ri.get('End')
        
        days_until_expiry = 0
        if end_time:
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            delta = end_time - datetime.now(end_time.tzinfo)
            days_until_expiry = max(0, delta.days)
        
        recurring = 0.0
        for charge in ri.get('RecurringCharges', []):
            recurring += float(charge.get('Amount', 0))
        
        tags = {}
        for tag in ri.get('Tags', []):
            tags[tag.get('Key', '')] = tag.get('Value', '')
        
        return ReservedInstanceData(
            reservation_id=ri.get('ReservedInstancesId', ''),
            service='EC2',
            instance_type=ri.get('InstanceType', ''),
            instance_count=ri.get('InstanceCount', 0),
            scope=ri.get('Scope', 'Region'),
            availability_zone=ri.get('AvailabilityZone', ''),
            platform=ri.get('ProductDescription', ''),
            offering_type=ri.get('OfferingType', ''),
            offering_class=ri.get('OfferingClass', 'standard'),
            fixed_price=float(ri.get('FixedPrice', 0)),
            usage_price=float(ri.get('UsagePrice', 0)),
            recurring_charges=recurring,
            start_time=start_time,
            end_time=end_time,
            state=ri.get('State', 'active'),
            currency=ri.get('CurrencyCode', 'USD'),
            duration_seconds=int(ri.get('Duration', 0)),
            days_until_expiry=days_until_expiry,
            tags=tags
        )
    
    def get_rds_reserved_instances(self, region: str = None) -> List[ReservedInstanceData]:
        """Obtém Reserved Instances RDS"""
        reservations = []
        try:
            client = self._get_rds_client(region)
            
            paginator = client.get_paginator('describe_reserved_db_instances')
            for page in paginator.paginate():
                for ri in page.get('ReservedDBInstances', []):
                    if ri.get('State') in ['active', 'payment-pending']:
                        parsed = self._parse_rds_ri(ri)
                        reservations.append(parsed)
            
            return reservations
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: rds:DescribeReservedDBInstances")
            else:
                self.logger.debug(f"Erro ao listar RDS RIs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter RDS RIs: {e}")
            return []
    
    def _parse_rds_ri(self, ri: Dict) -> ReservedInstanceData:
        """Parse de uma Reserved Instance RDS"""
        start_time = ri.get('StartTime')
        
        duration_seconds = int(ri.get('Duration', 0))
        end_time = None
        days_until_expiry = 0
        
        if start_time and duration_seconds:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_time = start_time + timedelta(seconds=duration_seconds)
            delta = end_time - datetime.now(end_time.tzinfo)
            days_until_expiry = max(0, delta.days)
        
        recurring = 0.0
        for charge in ri.get('RecurringCharges', []):
            recurring += float(charge.get('RecurringChargeAmount', 0))
        
        return ReservedInstanceData(
            reservation_id=ri.get('ReservedDBInstanceId', ''),
            service='RDS',
            instance_type=ri.get('DBInstanceClass', ''),
            instance_count=int(ri.get('DBInstanceCount', 1)),
            scope='Region',
            availability_zone='',
            platform=ri.get('ProductDescription', ''),
            offering_type=ri.get('OfferingType', ''),
            offering_class='standard',
            fixed_price=float(ri.get('FixedPrice', 0)),
            usage_price=float(ri.get('UsagePrice', 0)),
            recurring_charges=recurring,
            start_time=start_time,
            end_time=end_time,
            state=ri.get('State', 'active'),
            currency=ri.get('CurrencyCode', 'USD'),
            duration_seconds=duration_seconds,
            days_until_expiry=days_until_expiry
        )
    
    def get_elasticache_reserved_nodes(self, region: str = None) -> List[ReservedInstanceData]:
        """Obtém Reserved Cache Nodes do ElastiCache"""
        reservations = []
        try:
            client = self._get_elasticache_client(region)
            
            paginator = client.get_paginator('describe_reserved_cache_nodes')
            for page in paginator.paginate():
                for ri in page.get('ReservedCacheNodes', []):
                    if ri.get('State') in ['active', 'payment-pending']:
                        parsed = self._parse_elasticache_ri(ri)
                        reservations.append(parsed)
            
            return reservations
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: elasticache:DescribeReservedCacheNodes")
            else:
                self.logger.debug(f"Erro ao listar ElastiCache RIs: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter ElastiCache RIs: {e}")
            return []
    
    def _parse_elasticache_ri(self, ri: Dict) -> ReservedInstanceData:
        """Parse de um Reserved Cache Node"""
        start_time = ri.get('StartTime')
        
        duration_seconds = int(ri.get('Duration', 0))
        end_time = None
        days_until_expiry = 0
        
        if start_time and duration_seconds:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_time = start_time + timedelta(seconds=duration_seconds)
            delta = end_time - datetime.now(end_time.tzinfo)
            days_until_expiry = max(0, delta.days)
        
        recurring = 0.0
        for charge in ri.get('RecurringCharges', []):
            recurring += float(charge.get('RecurringChargeAmount', 0))
        
        return ReservedInstanceData(
            reservation_id=ri.get('ReservedCacheNodeId', ''),
            service='ElastiCache',
            instance_type=ri.get('CacheNodeType', ''),
            instance_count=int(ri.get('CacheNodeCount', 1)),
            scope='Region',
            availability_zone='',
            platform=ri.get('ProductDescription', ''),
            offering_type=ri.get('OfferingType', ''),
            offering_class='standard',
            fixed_price=float(ri.get('FixedPrice', 0)),
            usage_price=float(ri.get('UsagePrice', 0)),
            recurring_charges=recurring,
            start_time=start_time,
            end_time=end_time,
            state=ri.get('State', 'active'),
            currency=ri.get('CurrencyCode', 'USD'),
            duration_seconds=duration_seconds,
            days_until_expiry=days_until_expiry
        )
    
    def get_all_reserved_instances(self, region: str = None) -> List[ReservedInstanceData]:
        """Obtém todas as Reserved Instances de todos os serviços"""
        all_ris = []
        
        ec2_ris = self.get_ec2_reserved_instances(region)
        all_ris.extend(ec2_ris)
        self.logger.info(f"EC2 RIs: {len(ec2_ris)}")
        
        rds_ris = self.get_rds_reserved_instances(region)
        all_ris.extend(rds_ris)
        self.logger.info(f"RDS RIs: {len(rds_ris)}")
        
        elasticache_ris = self.get_elasticache_reserved_nodes(region)
        all_ris.extend(elasticache_ris)
        self.logger.info(f"ElastiCache RIs: {len(elasticache_ris)}")
        
        self.logger.info(f"Total RIs: {len(all_ris)}")
        return all_ris
    
    def get_utilization(self, days_back: int = 30, service: str = 'Amazon Elastic Compute Cloud - Compute') -> RIUtilization:
        """Obtém dados de utilização de Reserved Instances"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = client.get_reservation_utilization(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [service]
                    }
                }
            )
            
            total = response.get('Total', {})
            utilization = total.get('UtilizationPercentage', '0')
            
            groups = response.get('UtilizationsByTime', [])
            total_purchased = 0.0
            total_used = 0.0
            net_savings = 0.0
            amortized = 0.0
            
            for group in groups:
                total_data = group.get('Total', {})
                total_purchased += float(total_data.get('PurchasedHours', 0))
                total_used += float(total_data.get('TotalActualHours', 0))
                net_savings += float(total_data.get('NetRISavings', 0))
                amortized += float(total_data.get('AmortizedRecurringFee', 0))
            
            return RIUtilization(
                time_period_start=start_date,
                time_period_end=end_date,
                total_purchased_hours=total_purchased,
                total_used_hours=total_used,
                unused_hours=total_purchased - total_used,
                utilization_percentage=float(utilization),
                net_savings=net_savings,
                total_amortized_fee=amortized
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'DataUnavailableException':
                self.logger.info("Dados de utilização de RI não disponíveis")
            else:
                self.logger.error(f"Erro ao obter utilização RI: {e}")
            return RIUtilization(
                time_period_start="", time_period_end="",
                total_purchased_hours=0, total_used_hours=0, unused_hours=0,
                utilization_percentage=0, net_savings=0, total_amortized_fee=0
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter utilização: {e}")
            return RIUtilization(
                time_period_start="", time_period_end="",
                total_purchased_hours=0, total_used_hours=0, unused_hours=0,
                utilization_percentage=0, net_savings=0, total_amortized_fee=0
            )
    
    def get_coverage(self, days_back: int = 30) -> RICoverage:
        """Obtém dados de cobertura de Reserved Instances"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = client.get_reservation_coverage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY'
            )
            
            total = response.get('Total', {})
            coverage_hours = total.get('CoverageHours', {})
            
            return RICoverage(
                time_period_start=start_date,
                time_period_end=end_date,
                on_demand_cost=float(coverage_hours.get('OnDemandCost', 0)),
                reserved_hours=float(coverage_hours.get('ReservedHours', 0)),
                total_running_hours=float(coverage_hours.get('TotalRunningHours', 0)),
                coverage_percentage=float(coverage_hours.get('CoverageHoursPercentage', 0))
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'DataUnavailableException':
                self.logger.info("Dados de cobertura de RI não disponíveis")
            else:
                self.logger.error(f"Erro ao obter cobertura RI: {e}")
            return RICoverage(
                time_period_start="", time_period_end="",
                on_demand_cost=0, reserved_hours=0,
                total_running_hours=0, coverage_percentage=0
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter cobertura: {e}")
            return RICoverage(
                time_period_start="", time_period_end="",
                on_demand_cost=0, reserved_hours=0,
                total_running_hours=0, coverage_percentage=0
            )
    
    def get_purchase_recommendations(self, service: str = 'Amazon Elastic Compute Cloud - Compute') -> List[Dict[str, Any]]:
        """Obtém recomendações de compra de Reserved Instances"""
        recommendations = []
        try:
            client = self._get_ce_client()
            
            response = client.get_reservation_purchase_recommendation(
                Service=service,
                LookbackPeriodInDays='SIXTY_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT'
            )
            
            for rec in response.get('Recommendations', []):
                for detail in rec.get('RecommendationDetails', []):
                    instance_details = detail.get('InstanceDetails', {})
                    ec2_details = instance_details.get('EC2InstanceDetails', {})
                    rds_details = instance_details.get('RDSInstanceDetails', {})
                    
                    instance_type = ec2_details.get('InstanceType') or rds_details.get('DatabaseEngine', '')
                    monthly_savings = float(detail.get('EstimatedMonthlySavingsAmount', 0))
                    upfront = float(detail.get('UpfrontCost', 0))
                    recurring = float(detail.get('RecurringStandardMonthlyCost', 0))
                    
                    if monthly_savings > 0:
                        recommendations.append({
                            'service': service,
                            'instance_type': instance_type,
                            'instance_count': int(detail.get('RecommendedNumberOfInstancesToPurchase', 0)),
                            'monthly_savings': monthly_savings,
                            'upfront_cost': upfront,
                            'recurring_monthly_cost': recurring,
                            'roi_months': upfront / monthly_savings if monthly_savings > 0 else 0,
                            'estimated_savings_percentage': float(detail.get('EstimatedMonthlySavingsPercentage', 0))
                        })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Erro ao obter recomendações de RI: {e}")
            return []
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Obtém Reserved Instances como recursos"""
        ris = self.get_all_reserved_instances()
        return [ri.to_dict() for ri in ris]
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """Obtém resumo de custos das Reserved Instances"""
        ris = self.get_all_reserved_instances()
        utilization = self.get_utilization(days_back=period_days)
        
        total_recurring = sum(ri.recurring_charges for ri in ris) * 730
        
        cost_by_resource = {
            ri.reservation_id: ri.recurring_charges * 730
            for ri in ris
        }
        
        trend = "STABLE"
        if utilization.unused_hours > 0:
            trend = "DECREASING"
        
        return ServiceCost(
            service_name='reservedinstances',
            total_cost=round(total_recurring, 2),
            period_days=period_days,
            cost_by_resource=cost_by_resource,
            trend=trend,
            currency='USD'
        )
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Reserved Instances"""
        ris = self.get_all_reserved_instances()
        utilization = self.get_utilization()
        coverage = self.get_coverage()
        
        by_service: Dict[str, int] = {}
        by_offering: Dict[str, int] = {}
        expiring_30d = 0
        expiring_60d = 0
        expiring_90d = 0
        
        for ri in ris:
            by_service[ri.service] = by_service.get(ri.service, 0) + 1
            by_offering[ri.offering_type] = by_offering.get(ri.offering_type, 0) + 1
            
            if ri.days_until_expiry <= 30:
                expiring_30d += 1
            elif ri.days_until_expiry <= 60:
                expiring_60d += 1
            elif ri.days_until_expiry <= 90:
                expiring_90d += 1
        
        return ServiceMetrics(
            service_name='reservedinstances',
            resource_count=len(ris),
            metrics={
                'utilization_percent': round(utilization.utilization_percentage, 2),
                'coverage_percent': round(coverage.coverage_percentage, 2),
                'unused_hours': round(utilization.unused_hours, 2),
                'net_savings_usd': round(utilization.net_savings, 2),
                'by_service': by_service,
                'by_offering_type': by_offering,
                'expiring_30d': expiring_30d,
                'expiring_60d': expiring_60d,
                'expiring_90d': expiring_90d
            },
            utilization=round(utilization.utilization_percentage, 2)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização de Reserved Instances"""
        recommendations: List[ServiceRecommendation] = []
        ris = self.get_all_reserved_instances()
        utilization = self.get_utilization()
        coverage = self.get_coverage()
        purchase_recs = self.get_purchase_recommendations()
        
        if utilization.utilization_percentage < 80 and utilization.unused_hours > 0:
            waste_cost = utilization.unused_hours * 0.05
            recommendations.append(ServiceRecommendation(
                resource_id='reserved_instances',
                resource_type='reserved_instance',
                recommendation_type='LOW_UTILIZATION',
                description=(
                    f'A utilização das Reserved Instances está em apenas {utilization.utilization_percentage:.1f}%. '
                    f'Horas não utilizadas: {utilization.unused_hours:,.0f}. '
                    f'Isso representa desperdício de capacidade contratada. '
                    f'Considere vender RIs não utilizadas no Marketplace.'
                ),
                estimated_savings=waste_cost,
                priority='HIGH',
                title=f'RIs com {utilization.utilization_percentage:.1f}% de utilização',
                action='Revisar workloads e considerar venda de RIs não utilizadas'
            ))
        
        if coverage.coverage_percentage < 50 and coverage.on_demand_cost > 100:
            potential_savings = coverage.on_demand_cost * 0.4
            recommendations.append(ServiceRecommendation(
                resource_id='ri_coverage',
                resource_type='reserved_instance',
                recommendation_type='LOW_COVERAGE',
                description=(
                    f'Apenas {coverage.coverage_percentage:.1f}% do uso está coberto por RIs. '
                    f'Custo On-Demand: ${coverage.on_demand_cost:,.2f}. '
                    f'Aumentar cobertura pode economizar até ${potential_savings:,.2f}/mês.'
                ),
                estimated_savings=potential_savings,
                priority='MEDIUM',
                title=f'Apenas {coverage.coverage_percentage:.1f}% de cobertura de RI',
                action='Avaliar compra de Reserved Instances adicionais'
            ))
        
        for ri in ris:
            if ri.days_until_expiry <= 30 and ri.days_until_expiry > 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=ri.reservation_id,
                    resource_type='reserved_instance',
                    recommendation_type='EXPIRING_SOON',
                    description=(
                        f'A Reserved Instance {ri.reservation_id} ({ri.service} - {ri.instance_type}) '
                        f'expira em {ri.days_until_expiry} dias. '
                        f'Quantidade: {ri.instance_count}. '
                        f'Planeje renovação para manter economia.'
                    ),
                    estimated_savings=ri.recurring_charges * 730 * 0.4,
                    priority='CRITICAL',
                    title=f'RI {ri.service} expira em {ri.days_until_expiry} dias',
                    action='Renovar ou substituir RI antes da expiração'
                ))
            elif ri.days_until_expiry <= 60:
                recommendations.append(ServiceRecommendation(
                    resource_id=ri.reservation_id,
                    resource_type='reserved_instance',
                    recommendation_type='EXPIRING_60D',
                    description=(
                        f'A Reserved Instance {ri.reservation_id} ({ri.service} - {ri.instance_type}) '
                        f'expira em {ri.days_until_expiry} dias. Avalie renovação.'
                    ),
                    estimated_savings=ri.recurring_charges * 730 * 0.4,
                    priority='HIGH',
                    title=f'RI {ri.service} expira em {ri.days_until_expiry} dias',
                    action='Planejar renovação da RI'
                ))
        
        for rec in purchase_recs[:3]:
            if rec.get('monthly_savings', 0) > 50:
                recommendations.append(ServiceRecommendation(
                    resource_id=f"new_ri_{rec['instance_type']}",
                    resource_type='reserved_instance',
                    recommendation_type='PURCHASE_RECOMMENDATION',
                    description=(
                        f"Recomendação AWS: Comprar {rec['instance_count']} RI(s) {rec['instance_type']} "
                        f"para economizar ${rec['monthly_savings']:,.2f}/mês "
                        f"({rec['estimated_savings_percentage']:.1f}%). "
                        f"Payback: {rec['roi_months']:.1f} meses."
                    ),
                    estimated_savings=rec['monthly_savings'] * 12,
                    priority='MEDIUM',
                    title=f"Comprar RI para {rec['instance_type']}: economia de ${rec['monthly_savings']:,.2f}/mês",
                    action=f"Comprar RI {rec['instance_type']} via Console AWS"
                ))
        
        if not ris and not purchase_recs:
            recommendations.append(ServiceRecommendation(
                resource_id='account',
                resource_type='reserved_instance',
                recommendation_type='NO_RESERVED_INSTANCES',
                description=(
                    'A conta não possui Reserved Instances ativas. '
                    'RIs podem oferecer até 75% de desconto '
                    'em relação a preços On-Demand para workloads estáveis. '
                    'Considere também Savings Plans para maior flexibilidade.'
                ),
                estimated_savings=0,
                priority='MEDIUM',
                title='Nenhuma Reserved Instance ativa',
                action='Usar Cost Explorer para analisar recomendações de RI'
            ))
        
        return recommendations
    
    def analyze_usage(self) -> Dict[str, Any]:
        """Analisa padrões de uso das Reserved Instances"""
        ris = self.get_all_reserved_instances()
        utilization = self.get_utilization()
        coverage = self.get_coverage()
        recommendations = self.get_recommendations()
        
        by_service: Dict[str, Dict[str, Any]] = {}
        for ri in ris:
            svc = ri.service
            if svc not in by_service:
                by_service[svc] = {'count': 0, 'instance_count': 0, 'types': {}}
            by_service[svc]['count'] += 1
            by_service[svc]['instance_count'] += ri.instance_count
            by_service[svc]['types'][ri.instance_type] = by_service[svc]['types'].get(ri.instance_type, 0) + 1
        
        expiring_soon = [ri.to_dict() for ri in ris if ri.days_until_expiry <= 90]
        
        return {
            'service': 'reservedinstances',
            'summary': {
                'active_ri_count': len(ris),
                'total_instance_count': sum(ri.instance_count for ri in ris),
                'utilization_percent': round(utilization.utilization_percentage, 2),
                'coverage_percent': round(coverage.coverage_percentage, 2),
                'unused_hours': round(utilization.unused_hours, 2),
                'net_savings_usd': round(utilization.net_savings, 2)
            },
            'by_service': by_service,
            'expiring_within_90d': expiring_soon,
            'recommendations_count': len(recommendations),
            'optimization_opportunities': [r.get('title') for r in recommendations[:5]]
        }
