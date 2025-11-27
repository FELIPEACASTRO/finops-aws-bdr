"""
Route 53 FinOps Service - Análise de Custos de DNS

FASE 2 - Prioridade 2: Networking
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Hosted Zones, Records, Health Checks
- Análise de queries e custos
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class HostedZone:
    """Representa uma Hosted Zone"""
    zone_id: str
    name: str
    record_set_count: int
    is_private: bool
    comment: str = ""
    caller_reference: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'zone_id': self.zone_id,
            'name': self.name,
            'record_set_count': self.record_set_count,
            'is_private': self.is_private,
            'comment': self.comment
        }


@dataclass
class HealthCheck:
    """Representa um Health Check"""
    health_check_id: str
    caller_reference: str
    health_check_version: int
    type: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    resource_path: Optional[str] = None
    fqdn: Optional[str] = None
    request_interval: int = 30
    failure_threshold: int = 3
    measure_latency: bool = False
    inverted: bool = False
    disabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'health_check_id': self.health_check_id,
            'type': self.type,
            'target': self.fqdn or self.ip_address,
            'port': self.port,
            'request_interval': self.request_interval,
            'measure_latency': self.measure_latency,
            'disabled': self.disabled
        }


class Route53Service(BaseAWSService):
    """
    Serviço FinOps para análise de custos Route 53
    """
    
    def __init__(
        self,
        route53_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._route53_client = route53_client
    
    @property
    def route53_client(self):
        if self._route53_client is None:
            import boto3
            self._route53_client = boto3.client('route53')
        return self._route53_client
    
    def get_service_name(self) -> str:
        return "Amazon Route 53"
    
    def health_check(self) -> bool:
        try:
            self.route53_client.list_hosted_zones(MaxItems='1')
            return True
        except Exception:
            return False
    
    
    def get_hosted_zones(self) -> List[HostedZone]:
        """Lista todas as Hosted Zones"""
        zones = []
        
        paginator = self.route53_client.get_paginator('list_hosted_zones')
        
        for page in paginator.paginate():
            for zone in page.get('HostedZones', []):
                zone_id = zone['Id'].replace('/hostedzone/', '')
                
                hosted_zone = HostedZone(
                    zone_id=zone_id,
                    name=zone['Name'],
                    record_set_count=zone['ResourceRecordSetCount'],
                    is_private=zone['Config'].get('PrivateZone', False),
                    comment=zone['Config'].get('Comment', ''),
                    caller_reference=zone['CallerReference']
                )
                zones.append(hosted_zone)
        
        return zones
    
    
    def get_health_checks(self) -> List[HealthCheck]:
        """Lista Health Checks"""
        health_checks = []
        
        paginator = self.route53_client.get_paginator('list_health_checks')
        
        for page in paginator.paginate():
            for hc in page.get('HealthChecks', []):
                config = hc['HealthCheckConfig']
                
                health_check = HealthCheck(
                    health_check_id=hc['Id'],
                    caller_reference=hc['CallerReference'],
                    health_check_version=hc['HealthCheckVersion'],
                    type=config['Type'],
                    ip_address=config.get('IPAddress'),
                    port=config.get('Port'),
                    resource_path=config.get('ResourcePath'),
                    fqdn=config.get('FullyQualifiedDomainName'),
                    request_interval=config.get('RequestInterval', 30),
                    failure_threshold=config.get('FailureThreshold', 3),
                    measure_latency=config.get('MeasureLatency', False),
                    inverted=config.get('Inverted', False),
                    disabled=config.get('Disabled', False)
                )
                health_checks.append(health_check)
        
        return health_checks
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for zone in self.get_hosted_zones():
            res = zone.to_dict()
            res['resource_type'] = 'hosted_zone'
            resources.append(res)
        
        for hc in self.get_health_checks():
            res = hc.to_dict()
            res['resource_type'] = 'health_check'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Route 53"""
        zones = self.get_hosted_zones()
        health_checks = self.get_health_checks()
        
        total_records = sum(z.record_set_count for z in zones)
        private_zones = len([z for z in zones if z.is_private])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(zones) + len(health_checks),
            metrics={
                'hosted_zones': len(zones),
                'private_zones': private_zones,
                'public_zones': len(zones) - private_zones,
                'total_records': total_records,
                'health_checks': len(health_checks),
                'active_health_checks': len([h for h in health_checks if not h.disabled])
            },
            period_days=30,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Route 53"""
        recommendations = []
        zones = self.get_hosted_zones()
        health_checks = self.get_health_checks()
        
        for zone in zones:
            if zone.record_set_count <= 4:
                recommendations.append(ServiceRecommendation(
                    resource_id=zone.zone_id,
                    resource_type='Hosted Zone',
                    recommendation_type='MINIMAL_RECORDS',
                    title=f'Hosted Zone com poucos records ({zone.record_set_count})',
                    description=f'Hosted Zone {zone.name} tem apenas {zone.record_set_count} records. '
                               f'Verifique se ainda é necessária. Custo: $0.50/mês.',
                    estimated_savings=0.5,
                    priority='LOW',
                    action='Avaliar necessidade da hosted zone'
                ))
        
        for hc in health_checks:
            if hc.disabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=hc.health_check_id,
                    resource_type='Health Check',
                    recommendation_type='DISABLED_RESOURCE',
                    title='Health Check desabilitado',
                    description=f'Health Check {hc.health_check_id} está desabilitado. '
                               f'Considere remover se não for mais necessário.',
                    estimated_savings=0.5,
                    priority='LOW',
                    action='Remover health check desabilitado'
                ))
            
            if hc.request_interval == 10:
                recommendations.append(ServiceRecommendation(
                    resource_id=hc.health_check_id,
                    resource_type='Health Check',
                    recommendation_type='FAST_INTERVAL',
                    title='Health Check com intervalo rápido (10s)',
                    description=f'Health Check para {hc.fqdn or hc.ip_address} usa intervalo de 10s '
                               f'(custo maior). Avalie se 30s seria suficiente.',
                    estimated_savings=0.25,
                    priority='LOW',
                    action='Avaliar intervalo de 30s'
                ))
        
        return recommendations
