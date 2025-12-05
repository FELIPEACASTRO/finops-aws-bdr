"""
Compute Analyzer - Análise de serviços de computação AWS

Serviços cobertos:
- EC2 (Instances, EBS, EIP, NAT Gateway, etc.)
- Lambda
- ECS/EKS
- Elastic Beanstalk
- Batch
- Lightsail
- App Runner

Design Pattern: Strategy (implementação específica de análise)
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .base_analyzer import (
    BaseAnalyzer,
    Recommendation,
    Priority,
    Impact
)

logger = logging.getLogger(__name__)


class ComputeAnalyzer(BaseAnalyzer):
    """
    Analyzer para serviços de computação AWS.
    
    Implementa Strategy Pattern para análise de:
    - EC2 Instances (stopped, old generation)
    - EBS Volumes (orphan, unoptimized)
    - Elastic IPs (unused)
    - NAT Gateways (cost alerts)
    - Lambda (high memory, deprecated runtimes)
    - Containers (ECS/EKS)
    """
    
    name = "ComputeAnalyzer"
    
    def _get_client(self, region: str) -> Any:
        """Retorna clientes boto3 para computação."""
        import boto3
        return {
            'ec2': boto3.client('ec2', region_name=region),
            'lambda': boto3.client('lambda', region_name=region),
            'ecs': boto3.client('ecs', region_name=region),
        }
    
    def _collect_resources(self, clients: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta recursos de computação."""
        resources = {}
        
        ec2 = clients.get('ec2')
        if ec2:
            try:
                resources['instances'] = ec2.describe_instances()
                resources['volumes'] = ec2.describe_volumes()
                resources['addresses'] = ec2.describe_addresses()
                resources['nat_gateways'] = ec2.describe_nat_gateways(
                    Filter=[{'Name': 'state', 'Values': ['available']}]
                )
                resources['snapshots'] = ec2.describe_snapshots(OwnerIds=['self'])
            except Exception as e:
                logger.warning(f"Erro coletando EC2: {e}")
        
        lambda_client = clients.get('lambda')
        if lambda_client:
            try:
                resources['functions'] = lambda_client.list_functions()
            except Exception as e:
                logger.warning(f"Erro coletando Lambda: {e}")
        
        ecs = clients.get('ecs')
        if ecs:
            try:
                resources['ecs_clusters'] = ecs.list_clusters()
            except Exception as e:
                logger.warning(f"Erro coletando ECS: {e}")
        
        return resources
    
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """Analisa recursos e gera recomendações."""
        recommendations = []
        metrics = {}
        
        recommendations.extend(self._analyze_ec2_instances(resources, metrics))
        recommendations.extend(self._analyze_ebs_volumes(resources, metrics))
        recommendations.extend(self._analyze_elastic_ips(resources, metrics))
        recommendations.extend(self._analyze_nat_gateways(resources, metrics))
        recommendations.extend(self._analyze_lambda_functions(resources, metrics))
        recommendations.extend(self._analyze_ecs(resources, metrics))
        
        return recommendations, metrics
    
    def _analyze_ec2_instances(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa instâncias EC2."""
        recommendations = []
        instances_data = resources.get('instances', {})
        
        all_instances = []
        for res in instances_data.get('Reservations', []):
            all_instances.extend(res.get('Instances', []))
        
        metrics['ec2_instances'] = len(all_instances)
        
        for inst in all_instances:
            state = inst.get('State', {}).get('Name', '')
            inst_id = inst.get('InstanceId', '')
            inst_type = inst.get('InstanceType', '')
            
            if state == 'stopped':
                recommendations.append(self._create_recommendation(
                    rec_type='EC2_STOPPED',
                    resource_id=inst_id,
                    description=f'Instância EC2 {inst_id} ({inst_type}) está parada - considere terminar',
                    service='EC2 Analysis',
                    priority=Priority.MEDIUM
                ))
            
            if inst_type.startswith(('t1.', 't2.', 'm1.', 'm2.', 'm3.')):
                recommendations.append(self._create_recommendation(
                    rec_type='EC2_OLD_GENERATION',
                    resource_id=inst_id,
                    description=f'Instância {inst_id} usa tipo antigo ({inst_type}) - migrar para nova geração',
                    service='EC2 Optimization',
                    priority=Priority.LOW,
                    savings=10.0
                ))
        
        return recommendations
    
    def _analyze_ebs_volumes(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa volumes EBS."""
        recommendations = []
        volumes_data = resources.get('volumes', {})
        
        volumes = volumes_data.get('Volumes', [])
        metrics['ebs_volumes'] = len(volumes)
        
        for vol in volumes:
            vol_id = vol.get('VolumeId', '')
            state = vol.get('State', '')
            attachments = vol.get('Attachments', [])
            size = vol.get('Size', 0)
            vol_type = vol.get('VolumeType', '')
            
            if state == 'available' and not attachments:
                monthly_cost = size * 0.10
                recommendations.append(self._create_recommendation(
                    rec_type='EBS_ORPHAN',
                    resource_id=vol_id,
                    description=f'Volume EBS órfão {vol_id} ({size}GB {vol_type}) - não está anexado',
                    service='EBS Analysis',
                    priority=Priority.HIGH,
                    savings=round(monthly_cost, 2)
                ))
            
            if vol_type == 'gp2' and size > 100:
                recommendations.append(self._create_recommendation(
                    rec_type='EBS_GP2_TO_GP3',
                    resource_id=vol_id,
                    description=f'Volume {vol_id} ({size}GB) pode migrar de gp2 para gp3 com economia',
                    service='EBS Optimization',
                    priority=Priority.MEDIUM,
                    savings=round(size * 0.02, 2)
                ))
        
        return recommendations
    
    def _analyze_elastic_ips(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa Elastic IPs."""
        recommendations = []
        addresses_data = resources.get('addresses', {})
        
        addresses = addresses_data.get('Addresses', [])
        metrics['elastic_ips'] = len(addresses)
        
        for eip in addresses:
            allocation_id = eip.get('AllocationId', eip.get('PublicIp', ''))
            instance_id = eip.get('InstanceId')
            
            if not instance_id:
                recommendations.append(self._create_recommendation(
                    rec_type='EIP_UNUSED',
                    resource_id=allocation_id,
                    description=f'Elastic IP {eip.get("PublicIp", allocation_id)} não está associado',
                    service='EIP Analysis',
                    priority=Priority.MEDIUM,
                    savings=3.60
                ))
        
        return recommendations
    
    def _analyze_nat_gateways(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa NAT Gateways."""
        recommendations = []
        nat_data = resources.get('nat_gateways', {})
        
        nat_gws = nat_data.get('NatGateways', [])
        metrics['nat_gateways'] = len(nat_gws)
        
        for nat in nat_gws:
            nat_id = nat.get('NatGatewayId', '')
            recommendations.append(self._create_recommendation(
                rec_type='NAT_GATEWAY_COST',
                resource_id=nat_id,
                description=f'NAT Gateway {nat_id} ativo - custo ~$32/mês + transferência',
                service='NAT Analysis',
                priority=Priority.INFO
            ))
        
        return recommendations
    
    def _analyze_lambda_functions(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa funções Lambda."""
        recommendations = []
        functions_data = resources.get('functions', {})
        
        functions = functions_data.get('Functions', [])
        metrics['lambda_functions'] = len(functions)
        
        for func in functions:
            func_name = func.get('FunctionName', '')
            memory = func.get('MemorySize', 128)
            runtime = func.get('Runtime', '')
            
            if memory >= 1024:
                recommendations.append(self._create_recommendation(
                    rec_type='LAMBDA_HIGH_MEMORY',
                    resource_id=func_name,
                    description=f'Lambda {func_name} com {memory}MB - verificar se necessário',
                    service='Lambda Analysis',
                    priority=Priority.LOW
                ))
            
            if runtime and 'python2' in runtime.lower():
                recommendations.append(self._create_recommendation(
                    rec_type='LAMBDA_DEPRECATED_RUNTIME',
                    resource_id=func_name,
                    description=f'Lambda {func_name} usa runtime descontinuado ({runtime})',
                    service='Lambda Analysis',
                    priority=Priority.HIGH
                ))
        
        return recommendations
    
    def _analyze_ecs(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa clusters ECS."""
        recommendations = []
        clusters_data = resources.get('ecs_clusters', {})
        
        clusters = clusters_data.get('clusterArns', [])
        metrics['ecs_clusters'] = len(clusters)
        
        return recommendations
    
    def _get_services_list(self) -> List[str]:
        """Retorna serviços analisados."""
        return ['EC2', 'EBS', 'EIP', 'NAT Gateway', 'Lambda', 'ECS']
