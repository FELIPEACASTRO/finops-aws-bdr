"""
ELB FinOps Service - Análise de Custos de Load Balancing

FASE 2 - Prioridade 1: Networking
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de ALB, NLB e CLB
- Análise de utilização e LCU
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class LoadBalancer:
    """Representa um Load Balancer (ALB/NLB)"""
    load_balancer_arn: str
    load_balancer_name: str
    dns_name: str
    scheme: str  # internet-facing, internal
    type: str  # application, network, gateway
    state: str
    vpc_id: str
    availability_zones: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    ip_address_type: str = "ipv4"
    created_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'load_balancer_arn': self.load_balancer_arn,
            'load_balancer_name': self.load_balancer_name,
            'dns_name': self.dns_name,
            'scheme': self.scheme,
            'type': self.type,
            'state': self.state,
            'vpc_id': self.vpc_id,
            'availability_zones': self.availability_zones,
            'ip_address_type': self.ip_address_type,
            'created_time': self.created_time.isoformat() if self.created_time else None
        }


@dataclass
class ClassicLoadBalancer:
    """Representa um Classic Load Balancer"""
    load_balancer_name: str
    dns_name: str
    scheme: str
    vpc_id: Optional[str]
    availability_zones: List[str] = field(default_factory=list)
    subnets: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    instances: List[str] = field(default_factory=list)
    health_check: Dict[str, Any] = field(default_factory=dict)
    created_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'load_balancer_name': self.load_balancer_name,
            'dns_name': self.dns_name,
            'scheme': self.scheme,
            'vpc_id': self.vpc_id,
            'availability_zones': self.availability_zones,
            'instances_count': len(self.instances),
            'type': 'classic',
            'created_time': self.created_time.isoformat() if self.created_time else None
        }


@dataclass
class TargetGroup:
    """Representa um Target Group"""
    target_group_arn: str
    target_group_name: str
    protocol: str
    port: int
    vpc_id: str
    target_type: str  # instance, ip, lambda
    health_check_protocol: str
    health_check_path: Optional[str]
    healthy_threshold: int
    unhealthy_threshold: int
    load_balancer_arns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target_group_arn': self.target_group_arn,
            'target_group_name': self.target_group_name,
            'protocol': self.protocol,
            'port': self.port,
            'target_type': self.target_type,
            'load_balancers_count': len(self.load_balancer_arns)
        }


class ELBService(BaseAWSService):
    """
    Serviço FinOps para análise de custos de Load Balancers
    
    Analisa ALB, NLB e CLB, métricas de utilização
    e fornece recomendações de otimização.
    """
    
    def __init__(
        self,
        elbv2_client=None,
        elb_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._elbv2_client = elbv2_client
        self._elb_client = elb_client
    
    @property
    def elbv2_client(self):
        if self._elbv2_client is None:
            import boto3
            self._elbv2_client = boto3.client('elbv2')
        return self._elbv2_client
    
    @property
    def elb_client(self):
        if self._elb_client is None:
            import boto3
            self._elb_client = boto3.client('elb')
        return self._elb_client
    
    def get_service_name(self) -> str:
        return "Elastic Load Balancing"
    
    def health_check(self) -> bool:
        try:
            self.elbv2_client.describe_load_balancers(PageSize=1)
            return True
        except Exception:
            return False
    
    
    def get_load_balancers(self) -> List[LoadBalancer]:
        """Lista todos os ALB e NLB"""
        load_balancers = []
        
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        
        for page in paginator.paginate():
            for lb in page.get('LoadBalancers', []):
                azs = [az['ZoneName'] for az in lb.get('AvailabilityZones', [])]
                
                load_balancer = LoadBalancer(
                    load_balancer_arn=lb['LoadBalancerArn'],
                    load_balancer_name=lb['LoadBalancerName'],
                    dns_name=lb['DNSName'],
                    scheme=lb['Scheme'],
                    type=lb['Type'],
                    state=lb['State']['Code'],
                    vpc_id=lb.get('VpcId', ''),
                    availability_zones=azs,
                    security_groups=lb.get('SecurityGroups', []),
                    ip_address_type=lb.get('IpAddressType', 'ipv4'),
                    created_time=lb.get('CreatedTime')
                )
                load_balancers.append(load_balancer)
        
        return load_balancers
    
    
    def get_classic_load_balancers(self) -> List[ClassicLoadBalancer]:
        """Lista todos os Classic Load Balancers"""
        classic_lbs = []
        
        paginator = self.elb_client.get_paginator('describe_load_balancers')
        
        for page in paginator.paginate():
            for lb in page.get('LoadBalancerDescriptions', []):
                instances = [i['InstanceId'] for i in lb.get('Instances', [])]
                
                classic_lb = ClassicLoadBalancer(
                    load_balancer_name=lb['LoadBalancerName'],
                    dns_name=lb['DNSName'],
                    scheme=lb.get('Scheme', 'internet-facing'),
                    vpc_id=lb.get('VPCId'),
                    availability_zones=lb.get('AvailabilityZones', []),
                    subnets=lb.get('Subnets', []),
                    security_groups=lb.get('SecurityGroups', []),
                    instances=instances,
                    health_check=lb.get('HealthCheck', {}),
                    created_time=lb.get('CreatedTime')
                )
                classic_lbs.append(classic_lb)
        
        return classic_lbs
    
    
    def get_target_groups(self) -> List[TargetGroup]:
        """Lista todos os Target Groups"""
        target_groups = []
        
        paginator = self.elbv2_client.get_paginator('describe_target_groups')
        
        for page in paginator.paginate():
            for tg in page.get('TargetGroups', []):
                target_group = TargetGroup(
                    target_group_arn=tg['TargetGroupArn'],
                    target_group_name=tg['TargetGroupName'],
                    protocol=tg.get('Protocol', ''),
                    port=tg.get('Port', 0),
                    vpc_id=tg.get('VpcId', ''),
                    target_type=tg['TargetType'],
                    health_check_protocol=tg.get('HealthCheckProtocol', ''),
                    health_check_path=tg.get('HealthCheckPath'),
                    healthy_threshold=tg.get('HealthyThresholdCount', 0),
                    unhealthy_threshold=tg.get('UnhealthyThresholdCount', 0),
                    load_balancer_arns=tg.get('LoadBalancerArns', [])
                )
                target_groups.append(target_group)
        
        return target_groups
    
    
    def get_lb_metrics(self, lb_arn: str, lb_type: str, days: int = 7) -> Dict[str, Any]:
        """Obtém métricas de um Load Balancer"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        lb_name = lb_arn.split('/')[-2] + '/' + lb_arn.split('/')[-1]
        
        if lb_type == 'application':
            namespace = 'AWS/ApplicationELB'
            dimension_name = 'LoadBalancer'
            dimension_value = 'app/' + lb_name
        else:
            namespace = 'AWS/NetworkELB'
            dimension_name = 'LoadBalancer'
            dimension_value = 'net/' + lb_name
        
        requests = self.cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName='RequestCount' if lb_type == 'application' else 'ProcessedBytes',
            Dimensions=[{'Name': dimension_name, 'Value': dimension_value}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if requests.get('Datapoints'):
            if lb_type == 'application':
                metrics['total_requests'] = int(sum(d['Sum'] for d in requests['Datapoints']))
            else:
                metrics['processed_bytes_gb'] = round(
                    sum(d['Sum'] for d in requests['Datapoints']) / (1024**3), 2
                )
        
        if lb_type == 'application':
            lcu = self.cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName='ConsumedLCUs',
                Dimensions=[{'Name': dimension_name, 'Value': dimension_value}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            if lcu.get('Datapoints'):
                metrics['lcu_avg'] = round(
                    sum(d['Average'] for d in lcu['Datapoints']) / len(lcu['Datapoints']), 2
                )
                metrics['lcu_max'] = round(max(d['Maximum'] for d in lcu['Datapoints']), 2)
        
        return metrics
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for lb in self.get_load_balancers():
            resources.append(lb.to_dict())
        
        for clb in self.get_classic_load_balancers():
            resources.append(clb.to_dict())
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de ELB"""
        load_balancers = self.get_load_balancers()
        classic_lbs = self.get_classic_load_balancers()
        target_groups = self.get_target_groups()
        
        alb_count = len([lb for lb in load_balancers if lb.type == 'application'])
        nlb_count = len([lb for lb in load_balancers if lb.type == 'network'])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(load_balancers) + len(classic_lbs),
            metrics={
                'alb_count': alb_count,
                'nlb_count': nlb_count,
                'clb_count': len(classic_lbs),
                'target_groups': len(target_groups),
                'orphan_target_groups': len([tg for tg in target_groups if not tg.load_balancer_arns])
            },
            period_days=7,
            collected_at=datetime.utcnow()
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para ELB"""
        recommendations = []
        load_balancers = self.get_load_balancers()
        classic_lbs = self.get_classic_load_balancers()
        target_groups = self.get_target_groups()
        
        for clb in classic_lbs:
            recommendations.append(ServiceRecommendation(
                resource_id=clb.load_balancer_name,
                resource_type='Classic Load Balancer',
                recommendation_type='MODERNIZE',
                title='Migrar CLB para ALB/NLB',
                description=f'Classic Load Balancer {clb.load_balancer_name} deve ser migrado para ALB ou NLB. '
                           f'CLB não recebe mais atualizações e tem menos features.',
                estimated_savings=20.0,
                priority='MEDIUM',
                action='Migrar para Application ou Network Load Balancer'
            ))
            
            if len(clb.instances) == 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=clb.load_balancer_name,
                    resource_type='Classic Load Balancer',
                    recommendation_type='UNUSED_RESOURCE',
                    title='CLB sem instâncias registradas',
                    description=f'Classic Load Balancer {clb.load_balancer_name} não tem instâncias. '
                               f'Considere remover se não for mais necessário.',
                    estimated_savings=18.0,
                    priority='HIGH',
                    action='Remover CLB não utilizado'
                ))
        
        for lb in load_balancers:
            if lb.state != 'active':
                continue
            
            try:
                metrics = self.get_lb_metrics(lb.load_balancer_arn, lb.type, days=30)
                
                if lb.type == 'application':
                    if metrics.get('total_requests', 0) == 0:
                        recommendations.append(ServiceRecommendation(
                            resource_id=lb.load_balancer_name,
                            resource_type='Application Load Balancer',
                            recommendation_type='UNUSED_RESOURCE',
                            title='ALB sem tráfego',
                            description=f'ALB {lb.load_balancer_name} não teve requests nos últimos 30 dias. '
                                       f'Considere remover se não for mais necessário.',
                            estimated_savings=22.0,
                            priority='HIGH',
                            action='Remover ALB não utilizado'
                        ))
                    
                    lcu_avg = metrics.get('lcu_avg', 0)
                    if lcu_avg < 0.5 and metrics.get('total_requests', 0) > 0:
                        recommendations.append(ServiceRecommendation(
                            resource_id=lb.load_balancer_name,
                            resource_type='Application Load Balancer',
                            recommendation_type='LOW_UTILIZATION',
                            title=f'ALB com baixa utilização (LCU média: {lcu_avg})',
                            description=f'ALB {lb.load_balancer_name} tem utilização muito baixa. '
                                       f'Considere consolidar com outros ALBs.',
                            estimated_savings=10.0,
                            priority='MEDIUM',
                            action='Consolidar ALBs'
                        ))
                
            except Exception:
                pass
        
        orphan_tgs = [tg for tg in target_groups if not tg.load_balancer_arns]
        for tg in orphan_tgs:
            recommendations.append(ServiceRecommendation(
                resource_id=tg.target_group_name,
                resource_type='Target Group',
                recommendation_type='ORPHAN_RESOURCE',
                title='Target Group órfão',
                description=f'Target Group {tg.target_group_name} não está associado a nenhum Load Balancer. '
                           f'Considere remover se não for mais necessário.',
                estimated_savings=0.0,
                priority='LOW',
                action='Remover Target Group órfão'
            ))
        
        return recommendations
