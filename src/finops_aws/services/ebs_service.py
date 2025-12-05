"""
EBS Service - Análise de custos e métricas do Amazon EBS

FASE 2 do Roadmap FinOps AWS
Objetivo: Análise completa de Block Storage

Autor: FinOps AWS Team
Data: Novembro 2025
"""
import boto3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from botocore.exceptions import ClientError

from .base_service import (
    BaseAWSService,
    ServiceCost,
    ServiceMetrics,
    ServiceRecommendation
)
from ..utils.logger import setup_logger
from ..utils.aws_helpers import handle_aws_error, get_aws_region

logger = setup_logger(__name__)


@dataclass
class EBSVolume:
    """Representa um volume EBS"""
    volume_id: str
    volume_type: str
    size_gb: int
    state: str
    availability_zone: str
    iops: int = 0
    throughput: int = 0
    encrypted: bool = False
    attached: bool = False
    instance_id: Optional[str] = None
    create_time: Optional[datetime] = None
    snapshot_id: Optional[str] = None


@dataclass
class EBSSnapshot:
    """Representa um snapshot EBS"""
    snapshot_id: str
    volume_id: str
    volume_size: int
    state: str
    start_time: Optional[datetime] = None
    description: str = ""
    encrypted: bool = False


class EBSService(BaseAWSService):
    """
    Serviço para análise completa do Amazon EBS
    
    Coleta custos, métricas de uso e recomendações de otimização
    para volumes e snapshots EBS.
    
    Suporta injeção de dependências para Clean Architecture.
    """
    
    SERVICE_NAME = "Amazon EBS"
    SERVICE_FILTER = "Amazon Elastic Compute Cloud - EBS"
    
    def __init__(
        self,
        ec2_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o EBSService
        
        Args:
            ec2_client: Cliente EC2 injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        super().__init__(cost_client=cost_client, cloudwatch_client=cloudwatch_client)
        self._ec2_client = ec2_client
    
    @property
    def ec2_client(self):
        """Lazy loading do cliente EC2"""
        if self._ec2_client is None:
            self._ec2_client = boto3.client('ec2', region_name=self.region)
        return self._ec2_client
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.ec2_client.describe_volumes(MaxResults=5)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os volumes EBS"""
        volumes = self.get_volumes()
        return [
            {
                'volume_id': v.volume_id,
                'volume_type': v.volume_type,
                'size_gb': v.size_gb,
                'state': v.state,
                'attached': v.attached
            }
            for v in volumes
        ]
    
    def get_volumes(self) -> List[EBSVolume]:
        """
        Obtém lista de todos os volumes EBS
        
        Returns:
            Lista de EBSVolume
        """
        try:
            volumes = []
            paginator = self.ec2_client.get_paginator('describe_volumes')
            
            for page in paginator.paginate():
                for vol in page.get('Volumes', []):
                    attachments = vol.get('Attachments', [])
                    is_attached = len(attachments) > 0
                    instance_id = attachments[0].get('InstanceId') if is_attached else None
                    
                    volume = EBSVolume(
                        volume_id=vol['VolumeId'],
                        volume_type=vol['VolumeType'],
                        size_gb=vol['Size'],
                        state=vol['State'],
                        availability_zone=vol['AvailabilityZone'],
                        iops=vol.get('Iops', 0),
                        throughput=vol.get('Throughput', 0),
                        encrypted=vol.get('Encrypted', False),
                        attached=is_attached,
                        instance_id=instance_id,
                        create_time=vol.get('CreateTime'),
                        snapshot_id=vol.get('SnapshotId')
                    )
                    volumes.append(volume)
            
            logger.info(f"Found {len(volumes)} EBS volumes")
            return volumes
            
        except ClientError as e:
            handle_aws_error(e, "get_ebs_volumes")
            return []
    
    def get_snapshots(self, owner_id: str = 'self') -> List[EBSSnapshot]:
        """
        Obtém lista de snapshots EBS
        
        Args:
            owner_id: ID do proprietário ('self' para conta atual)
            
        Returns:
            Lista de EBSSnapshot
        """
        try:
            snapshots = []
            paginator = self.ec2_client.get_paginator('describe_snapshots')
            
            for page in paginator.paginate(OwnerIds=[owner_id]):
                for snap in page.get('Snapshots', []):
                    snapshot = EBSSnapshot(
                        snapshot_id=snap['SnapshotId'],
                        volume_id=snap.get('VolumeId', ''),
                        volume_size=snap.get('VolumeSize', 0),
                        state=snap['State'],
                        start_time=snap.get('StartTime'),
                        description=snap.get('Description', ''),
                        encrypted=snap.get('Encrypted', False)
                    )
                    snapshots.append(snapshot)
            
            logger.info(f"Found {len(snapshots)} EBS snapshots")
            return snapshots
            
        except ClientError as e:
            handle_aws_error(e, "get_ebs_snapshots")
            return []
    
    def get_volume_metrics(self, volume_id: str) -> Dict[str, Any]:
        """
        Obtém métricas de um volume específico
        
        Args:
            volume_id: ID do volume
            
        Returns:
            Dicionário com métricas do volume
        """
        dimensions = [{'Name': 'VolumeId', 'Value': volume_id}]
        
        metrics = {
            'read_ops': self.get_cloudwatch_metric(
                'AWS/EBS', 'VolumeReadOps', dimensions
            ),
            'write_ops': self.get_cloudwatch_metric(
                'AWS/EBS', 'VolumeWriteOps', dimensions
            ),
            'read_bytes': self.get_cloudwatch_metric(
                'AWS/EBS', 'VolumeReadBytes', dimensions
            ),
            'write_bytes': self.get_cloudwatch_metric(
                'AWS/EBS', 'VolumeWriteBytes', dimensions
            ),
            'idle_time': self.get_cloudwatch_metric(
                'AWS/EBS', 'VolumeIdleTime', dimensions
            ),
            'queue_length': self.get_cloudwatch_metric(
                'AWS/EBS', 'VolumeQueueLength', dimensions
            )
        }
        
        return metrics
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do EBS"""
        volumes = self.get_volumes()
        snapshots = self.get_snapshots()
        
        total_size = sum(v.size_gb for v in volumes)
        attached_count = sum(1 for v in volumes if v.attached)
        unattached_count = len(volumes) - attached_count
        
        volume_types = {}
        for v in volumes:
            if v.volume_type not in volume_types:
                volume_types[v.volume_type] = {'count': 0, 'size_gb': 0}
            volume_types[v.volume_type]['count'] += 1
            volume_types[v.volume_type]['size_gb'] += v.size_gb
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(volumes),
            metrics={
                'total_size_gb': total_size,
                'attached_volumes': attached_count,
                'unattached_volumes': unattached_count,
                'snapshot_count': len(snapshots),
                'snapshot_size_gb': sum(s.volume_size for s in snapshots),
                'encrypted_volumes': sum(1 for v in volumes if v.encrypted),
                'volume_types': volume_types
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para EBS"""
        recommendations = []
        volumes = self.get_volumes()
        snapshots = self.get_snapshots()
        
        gp2_volumes = [v for v in volumes if v.volume_type == 'gp2']
        for vol in gp2_volumes:
            estimated_savings = vol.size_gb * 0.02
            recommendations.append(ServiceRecommendation(
                resource_id=vol.volume_id,
                resource_type='EBSVolume',
                recommendation_type='UPGRADE_VOLUME_TYPE',
                description=f'Volume {vol.volume_id} usa gp2. Migrar para gp3 pode '
                           'reduzir custos e melhorar performance.',
                estimated_savings=estimated_savings,
                priority='MEDIUM',
                implementation_effort='MEDIUM',
                details={
                    'current_type': 'gp2',
                    'recommended_type': 'gp3',
                    'size_gb': vol.size_gb,
                    'savings_per_month': estimated_savings
                }
            ))
        
        unattached = [v for v in volumes if not v.attached]
        for vol in unattached:
            type_costs = {
                'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125,
                'io2': 0.125, 'st1': 0.045, 'sc1': 0.015
            }
            monthly_cost = vol.size_gb * type_costs.get(vol.volume_type, 0.10)
            
            recommendations.append(ServiceRecommendation(
                resource_id=vol.volume_id,
                resource_type='EBSVolume',
                recommendation_type='DELETE_UNATTACHED',
                description=f'Volume {vol.volume_id} não está anexado a nenhuma instância. '
                           'Considere criar snapshot e deletar o volume.',
                estimated_savings=monthly_cost,
                priority='HIGH',
                implementation_effort='LOW',
                details={
                    'volume_type': vol.volume_type,
                    'size_gb': vol.size_gb,
                    'state': vol.state,
                    'monthly_cost': monthly_cost
                }
            ))
        
        now = datetime.now(timezone.utc)
        old_snapshots = [
            s for s in snapshots
            if s.start_time and (now - s.start_time.replace(tzinfo=None)).days > 90
        ]
        
        if old_snapshots:
            total_old_size = sum(s.volume_size for s in old_snapshots)
            estimated_savings = total_old_size * 0.05
            
            recommendations.append(ServiceRecommendation(
                resource_id='multiple',
                resource_type='EBSSnapshot',
                recommendation_type='CLEANUP_SNAPSHOTS',
                description=f'{len(old_snapshots)} snapshots têm mais de 90 dias. '
                           'Revise e delete os desnecessários.',
                estimated_savings=estimated_savings,
                priority='MEDIUM',
                implementation_effort='MEDIUM',
                details={
                    'old_snapshot_count': len(old_snapshots),
                    'total_size_gb': total_old_size,
                    'estimated_monthly_savings': estimated_savings
                }
            ))
        
        unencrypted = [v for v in volumes if not v.encrypted]
        if unencrypted:
            recommendations.append(ServiceRecommendation(
                resource_id='multiple',
                resource_type='EBSVolume',
                recommendation_type='SECURITY',
                description=f'{len(unencrypted)} volumes não estão criptografados. '
                           'Considere habilitar criptografia para compliance.',
                estimated_savings=0.0,
                priority='HIGH',
                implementation_effort='HIGH',
                details={
                    'unencrypted_count': len(unencrypted),
                    'volume_ids': [v.volume_id for v in unencrypted[:10]]
                }
            ))
        
        logger.info(f"Generated {len(recommendations)} EBS recommendations")
        return recommendations
    
    def get_volume_utilization(self, volume_id: str) -> Dict[str, Any]:
        """
        Analisa utilização de um volume
        
        Args:
            volume_id: ID do volume
            
        Returns:
            Análise de utilização
        """
        metrics = self.get_volume_metrics(volume_id)
        
        idle_pct = metrics.get('idle_time', {}).get('average', 0) * 100
        read_ops = metrics.get('read_ops', {}).get('average', 0)
        write_ops = metrics.get('write_ops', {}).get('average', 0)
        
        total_ops = read_ops + write_ops
        
        if idle_pct > 90:
            utilization = 'LOW'
        elif idle_pct > 70:
            utilization = 'MEDIUM'
        else:
            utilization = 'HIGH'
        
        return {
            'volume_id': volume_id,
            'utilization_level': utilization,
            'idle_percentage': idle_pct,
            'avg_read_ops': read_ops,
            'avg_write_ops': write_ops,
            'total_ops_per_second': total_ops,
            'recommendation': self._get_utilization_recommendation(utilization, idle_pct)
        }
    
    def _get_utilization_recommendation(self, utilization: str, idle_pct: float) -> str:
        """Gera recomendação baseada na utilização"""
        if utilization == 'LOW':
            return 'Volume com baixa utilização. Considere redimensionar ou migrar para tipo mais econômico.'
        elif utilization == 'MEDIUM':
            return 'Volume com utilização moderada. Monitore para identificar padrões de uso.'
        else:
            return 'Volume com alta utilização. Considere aumentar IOPS ou migrar para io2.'
