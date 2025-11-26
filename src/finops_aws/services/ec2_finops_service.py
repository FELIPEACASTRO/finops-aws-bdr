"""
EC2 FinOps Service - Análise de Custos e Otimização de Instâncias EC2

FASE 2 - Prioridade 1: Compute (maior impacto em custos)
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de instâncias EC2 com detalhes (tipo, estado, pricing model)
- Análise de Reserved Instances e Savings Plans
- Detecção de instâncias ociosas ou subutilizadas
- Recomendações de rightsizing e modernização
- Análise de Spot vs On-Demand
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class EC2Instance:
    """Representa uma instância EC2"""
    instance_id: str
    instance_type: str
    state: str
    availability_zone: str
    launch_time: Optional[datetime] = None
    platform: str = "Linux/UNIX"
    tenancy: str = "default"
    lifecycle: str = "normal"  # normal, spot, scheduled
    monitoring: str = "disabled"
    ebs_optimized: bool = False
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    vpc_id: Optional[str] = None
    subnet_id: Optional[str] = None
    iam_instance_profile: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    cpu_credits: Optional[str] = None  # standard, unlimited (para T instances)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'instance_id': self.instance_id,
            'instance_type': self.instance_type,
            'state': self.state,
            'availability_zone': self.availability_zone,
            'launch_time': self.launch_time.isoformat() if self.launch_time else None,
            'platform': self.platform,
            'tenancy': self.tenancy,
            'lifecycle': self.lifecycle,
            'monitoring': self.monitoring,
            'ebs_optimized': self.ebs_optimized,
            'tags': self.tags
        }


@dataclass
class ReservedInstance:
    """Representa uma Reserved Instance"""
    reserved_instance_id: str
    instance_type: str
    availability_zone: Optional[str]
    instance_count: int
    state: str
    offering_type: str  # No Upfront, Partial Upfront, All Upfront
    offering_class: str  # standard, convertible
    duration: int  # seconds
    start: datetime
    end: datetime
    fixed_price: float
    usage_price: float
    scope: str  # Availability Zone, Region
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reserved_instance_id': self.reserved_instance_id,
            'instance_type': self.instance_type,
            'availability_zone': self.availability_zone,
            'instance_count': self.instance_count,
            'state': self.state,
            'offering_type': self.offering_type,
            'offering_class': self.offering_class,
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'fixed_price': self.fixed_price
        }


@dataclass
class SpotRequest:
    """Representa uma Spot Instance Request"""
    spot_instance_request_id: str
    instance_id: Optional[str]
    state: str
    status_code: str
    instance_type: str
    spot_price: Optional[str]
    launch_time: Optional[datetime]
    availability_zone: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'spot_instance_request_id': self.spot_instance_request_id,
            'instance_id': self.instance_id,
            'state': self.state,
            'status_code': self.status_code,
            'instance_type': self.instance_type,
            'spot_price': self.spot_price
        }


class EC2FinOpsService(BaseAWSService):
    """
    Serviço FinOps para análise de custos EC2
    
    Analisa instâncias EC2, Reserved Instances, Spot Instances
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(
        self,
        ec2_client=None,
        cloudwatch_client=None,
        cost_client=None,
        pricing_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._ec2_client = ec2_client
        self._pricing_client = pricing_client
    
    @property
    def ec2_client(self):
        if self._ec2_client is None:
            import boto3
            self._ec2_client = boto3.client('ec2')
        return self._ec2_client
    
    @property
    def pricing_client(self):
        if self._pricing_client is None:
            import boto3
            self._pricing_client = boto3.client('pricing', region_name='us-east-1')
        return self._pricing_client
    
    def get_service_name(self) -> str:
        return "Amazon EC2"
    
    def health_check(self) -> bool:
        try:
            self.ec2_client.describe_instances(MaxResults=5)
            return True
        except Exception:
            return False
    
    
    def get_instances(self, states: List[str] = None) -> List[EC2Instance]:
        """
        Lista todas as instâncias EC2
        
        Args:
            states: Filtro por estado (running, stopped, etc.)
        
        Returns:
            Lista de EC2Instance
        """
        instances = []
        filters = []
        
        if states:
            filters.append({'Name': 'instance-state-name', 'Values': states})
        
        paginator = self.ec2_client.get_paginator('describe_instances')
        page_iterator = paginator.paginate(Filters=filters) if filters else paginator.paginate()
        
        for page in page_iterator:
            for reservation in page.get('Reservations', []):
                for inst in reservation.get('Instances', []):
                    tags = {t['Key']: t['Value'] for t in inst.get('Tags', [])}
                    
                    instance = EC2Instance(
                        instance_id=inst['InstanceId'],
                        instance_type=inst['InstanceType'],
                        state=inst['State']['Name'],
                        availability_zone=inst['Placement']['AvailabilityZone'],
                        launch_time=inst.get('LaunchTime'),
                        platform=inst.get('Platform', 'Linux/UNIX'),
                        tenancy=inst['Placement'].get('Tenancy', 'default'),
                        lifecycle=inst.get('InstanceLifecycle', 'normal'),
                        monitoring=inst.get('Monitoring', {}).get('State', 'disabled'),
                        ebs_optimized=inst.get('EbsOptimized', False),
                        private_ip=inst.get('PrivateIpAddress'),
                        public_ip=inst.get('PublicIpAddress'),
                        vpc_id=inst.get('VpcId'),
                        subnet_id=inst.get('SubnetId'),
                        iam_instance_profile=inst.get('IamInstanceProfile', {}).get('Arn'),
                        tags=tags,
                        cpu_credits=inst.get('CpuOptions', {}).get('CreditsSpecification')
                    )
                    instances.append(instance)
        
        return instances
    
    
    def get_reserved_instances(self, state: str = 'active') -> List[ReservedInstance]:
        """
        Lista Reserved Instances
        
        Args:
            state: Filtro por estado (active, payment-pending, retired)
        
        Returns:
            Lista de ReservedInstance
        """
        reserved = []
        
        response = self.ec2_client.describe_reserved_instances(
            Filters=[{'Name': 'state', 'Values': [state]}]
        )
        
        for ri in response.get('ReservedInstances', []):
            reserved_instance = ReservedInstance(
                reserved_instance_id=ri['ReservedInstancesId'],
                instance_type=ri['InstanceType'],
                availability_zone=ri.get('AvailabilityZone'),
                instance_count=ri['InstanceCount'],
                state=ri['State'],
                offering_type=ri['OfferingType'],
                offering_class=ri.get('OfferingClass', 'standard'),
                duration=ri['Duration'],
                start=ri['Start'],
                end=ri['End'],
                fixed_price=ri['FixedPrice'],
                usage_price=ri['UsagePrice'],
                scope=ri.get('Scope', 'Availability Zone')
            )
            reserved.append(reserved_instance)
        
        return reserved
    
    
    def get_spot_requests(self) -> List[SpotRequest]:
        """Lista Spot Instance Requests ativas"""
        spots = []
        
        response = self.ec2_client.describe_spot_instance_requests(
            Filters=[{'Name': 'state', 'Values': ['open', 'active']}]
        )
        
        for spot in response.get('SpotInstanceRequests', []):
            spot_request = SpotRequest(
                spot_instance_request_id=spot['SpotInstanceRequestId'],
                instance_id=spot.get('InstanceId'),
                state=spot['State'],
                status_code=spot['Status']['Code'],
                instance_type=spot['LaunchSpecification']['InstanceType'],
                spot_price=spot.get('SpotPrice'),
                launch_time=spot.get('CreateTime'),
                availability_zone=spot['LaunchSpecification'].get('Placement', {}).get('AvailabilityZone')
            )
            spots.append(spot_request)
        
        return spots
    
    
    def get_instance_utilization(self, instance_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Obtém métricas de utilização de uma instância
        
        Args:
            instance_id: ID da instância
            days: Período de análise
        
        Returns:
            Dicionário com métricas de CPU, Network, Disk
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        
        cpu_stats = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        
        if cpu_stats.get('Datapoints'):
            avg_cpu = sum(d['Average'] for d in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
            max_cpu = max(d['Maximum'] for d in cpu_stats['Datapoints'])
            metrics['cpu'] = {'average': round(avg_cpu, 2), 'maximum': round(max_cpu, 2)}
        
        network_in = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='NetworkIn',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        
        network_out = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='NetworkOut',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        
        if network_in.get('Datapoints'):
            total_in = sum(d['Sum'] for d in network_in['Datapoints'])
            metrics['network_in_gb'] = round(total_in / (1024**3), 2)
        
        if network_out.get('Datapoints'):
            total_out = sum(d['Sum'] for d in network_out['Datapoints'])
            metrics['network_out_gb'] = round(total_out / (1024**3), 2)
        
        return metrics
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        instances = self.get_instances()
        return [inst.to_dict() for inst in instances]
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de EC2"""
        instances = self.get_instances()
        reserved = self.get_reserved_instances()
        
        running = [i for i in instances if i.state == 'running']
        stopped = [i for i in instances if i.state == 'stopped']
        spot_instances = [i for i in instances if i.lifecycle == 'spot']
        
        instance_types = {}
        for inst in running:
            instance_types[inst.instance_type] = instance_types.get(inst.instance_type, 0) + 1
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(instances),
            metrics={
                'running_instances': len(running),
                'stopped_instances': len(stopped),
                'spot_instances': len(spot_instances),
                'reserved_instances': len(reserved),
                'instance_types': instance_types,
                'total_reserved_count': sum(ri.instance_count for ri in reserved)
            },
            period_days=7,
            collected_at=datetime.utcnow()
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para EC2"""
        recommendations = []
        instances = self.get_instances()
        reserved = self.get_reserved_instances()
        
        running = [i for i in instances if i.state == 'running']
        stopped = [i for i in instances if i.state == 'stopped']
        
        for inst in stopped:
            if inst.launch_time:
                stopped_days = (datetime.utcnow() - inst.launch_time.replace(tzinfo=None)).days
                if stopped_days > 7:
                    recommendations.append(ServiceRecommendation(
                        resource_id=inst.instance_id,
                        resource_type='EC2 Instance',
                        recommendation_type='STOPPED_INSTANCE',
                        title=f'Instância parada há {stopped_days} dias',
                        description=f'Instância {inst.instance_id} ({inst.instance_type}) está parada há {stopped_days} dias. '
                                   f'Considere terminá-la ou criar uma AMI e encerrar para economizar custos de EBS.',
                        estimated_savings=10.0,
                        priority='MEDIUM',
                        action='Terminar instância ou criar AMI e encerrar'
                    ))
        
        for inst in running:
            if inst.instance_type.startswith(('m4.', 'm3.', 'c4.', 'c3.', 'r4.', 'r3.')):
                new_type = inst.instance_type.replace('m4.', 'm6i.').replace('m3.', 'm6i.')
                new_type = new_type.replace('c4.', 'c6i.').replace('c3.', 'c6i.')
                new_type = new_type.replace('r4.', 'r6i.').replace('r3.', 'r6i.')
                
                recommendations.append(ServiceRecommendation(
                    resource_id=inst.instance_id,
                    resource_type='EC2 Instance',
                    recommendation_type='MODERNIZE_INSTANCE',
                    title=f'Modernizar instância {inst.instance_type}',
                    description=f'Instância {inst.instance_id} usa tipo antigo {inst.instance_type}. '
                               f'Considere migrar para {new_type} para melhor performance e custo.',
                    estimated_savings=15.0,
                    priority='MEDIUM',
                    action=f'Migrar para {new_type}'
                ))
        
        on_demand_running = [i for i in running if i.lifecycle == 'normal']
        if len(on_demand_running) > 5:
            type_counts = {}
            for inst in on_demand_running:
                type_counts[inst.instance_type] = type_counts.get(inst.instance_type, 0) + 1
            
            for inst_type, count in type_counts.items():
                if count >= 3:
                    ri_coverage = sum(ri.instance_count for ri in reserved 
                                    if ri.instance_type == inst_type)
                    uncovered = count - ri_coverage
                    
                    if uncovered >= 2:
                        estimated_savings = uncovered * 50 * 12
                        recommendations.append(ServiceRecommendation(
                            resource_id=f'{inst_type}-fleet',
                            resource_type='EC2 Fleet',
                            recommendation_type='RESERVED_INSTANCE',
                            title=f'Considere Reserved Instances para {inst_type}',
                            description=f'Você tem {count} instâncias {inst_type} On-Demand com apenas '
                                       f'{ri_coverage} cobertas por RI. Considere comprar RIs para as '
                                       f'{uncovered} instâncias descobertas.',
                            estimated_savings=estimated_savings,
                            priority='HIGH',
                            action=f'Comprar {uncovered} Reserved Instances {inst_type}'
                        ))
        
        for inst in running:
            if inst.lifecycle == 'normal':
                if 'test' in inst.tags.get('Environment', '').lower() or \
                   'dev' in inst.tags.get('Environment', '').lower() or \
                   'test' in inst.tags.get('Name', '').lower():
                    recommendations.append(ServiceRecommendation(
                        resource_id=inst.instance_id,
                        resource_type='EC2 Instance',
                        recommendation_type='SPOT_CANDIDATE',
                        title=f'Candidata a Spot Instance',
                        description=f'Instância {inst.instance_id} parece ser de ambiente não-produção. '
                                   f'Considere usar Spot Instances para economia de até 90%.',
                        estimated_savings=50.0,
                        priority='LOW',
                        action='Migrar para Spot Instance'
                    ))
        
        for inst in running:
            try:
                utilization = self.get_instance_utilization(inst.instance_id, days=7)
                if utilization.get('cpu', {}).get('average', 100) < 10:
                    recommendations.append(ServiceRecommendation(
                        resource_id=inst.instance_id,
                        resource_type='EC2 Instance',
                        recommendation_type='UNDERUTILIZED',
                        title=f'Instância subutilizada',
                        description=f'Instância {inst.instance_id} ({inst.instance_type}) tem CPU média '
                                   f'de {utilization["cpu"]["average"]}% nos últimos 7 dias. '
                                   f'Considere fazer downsize.',
                        estimated_savings=30.0,
                        priority='HIGH',
                        action='Fazer downsize do tipo de instância'
                    ))
            except Exception:
                pass
        
        for ri in reserved:
            days_until_expiry = (ri.end.replace(tzinfo=None) - datetime.utcnow()).days
            if 0 < days_until_expiry <= 30:
                recommendations.append(ServiceRecommendation(
                    resource_id=ri.reserved_instance_id,
                    resource_type='Reserved Instance',
                    recommendation_type='RI_EXPIRING',
                    title=f'Reserved Instance expirando em {days_until_expiry} dias',
                    description=f'RI {ri.reserved_instance_id} ({ri.instance_type} x{ri.instance_count}) '
                               f'expira em {ri.end.strftime("%Y-%m-%d")}. Avalie renovação.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Renovar ou converter para Savings Plans'
                ))
        
        return recommendations
