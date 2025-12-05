"""
EFS Service - Análise de custos e métricas do Amazon EFS

FASE 2 do Roadmap FinOps AWS
Objetivo: Análise completa de File Storage

Autor: FinOps AWS Team
Data: Novembro 2025
"""
import boto3
from datetime import datetime, timedelta
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
class EFSFileSystem:
    """Representa um sistema de arquivos EFS"""
    file_system_id: str
    name: str
    lifecycle_state: str
    size_bytes: int = 0
    performance_mode: str = "generalPurpose"
    throughput_mode: str = "bursting"
    provisioned_throughput: float = 0.0
    encrypted: bool = False
    number_of_mount_targets: int = 0
    creation_time: Optional[datetime] = None
    availability_zone: Optional[str] = None
    lifecycle_policies: int = 0


class EFSService(BaseAWSService):
    """
    Serviço para análise completa do Amazon EFS
    
    Coleta custos, métricas de uso e recomendações de otimização
    para sistemas de arquivos EFS.
    
    Suporta injeção de dependências para Clean Architecture.
    """
    
    SERVICE_NAME = "Amazon EFS"
    SERVICE_FILTER = "Amazon Elastic File System"
    
    def __init__(
        self,
        efs_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o EFSService
        
        Args:
            efs_client: Cliente EFS injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        super().__init__(cost_client=cost_client, cloudwatch_client=cloudwatch_client)
        self._efs_client = efs_client
    
    @property
    def efs_client(self):
        """Lazy loading do cliente EFS"""
        if self._efs_client is None:
            self._efs_client = boto3.client('efs', region_name=self.region)
        return self._efs_client
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.efs_client.describe_file_systems(MaxItems=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os sistemas de arquivos EFS"""
        file_systems = self.get_file_systems()
        return [
            {
                'file_system_id': fs.file_system_id,
                'name': fs.name,
                'size_bytes': fs.size_bytes,
                'performance_mode': fs.performance_mode,
                'throughput_mode': fs.throughput_mode
            }
            for fs in file_systems
        ]
    
    def get_file_systems(self) -> List[EFSFileSystem]:
        """
        Obtém lista de todos os sistemas de arquivos EFS
        
        Returns:
            Lista de EFSFileSystem
        """
        try:
            file_systems = []
            marker = None
            
            while True:
                params = {'MaxItems': 100}
                if marker:
                    params['Marker'] = marker
                
                response = self.efs_client.describe_file_systems(**params)
                
                for fs_data in response.get('FileSystems', []):
                    name = fs_data.get('Name', fs_data['FileSystemId'])
                    
                    for tag in fs_data.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    fs = EFSFileSystem(
                        file_system_id=fs_data['FileSystemId'],
                        name=name,
                        lifecycle_state=fs_data['LifeCycleState'],
                        size_bytes=fs_data.get('SizeInBytes', {}).get('Value', 0),
                        performance_mode=fs_data.get('PerformanceMode', 'generalPurpose'),
                        throughput_mode=fs_data.get('ThroughputMode', 'bursting'),
                        provisioned_throughput=fs_data.get('ProvisionedThroughputInMibps', 0.0),
                        encrypted=fs_data.get('Encrypted', False),
                        number_of_mount_targets=fs_data.get('NumberOfMountTargets', 0),
                        creation_time=fs_data.get('CreationTime'),
                        availability_zone=fs_data.get('AvailabilityZoneName')
                    )
                    
                    try:
                        lifecycle = self.efs_client.describe_lifecycle_configuration(
                            FileSystemId=fs.file_system_id
                        )
                        fs.lifecycle_policies = len(lifecycle.get('LifecyclePolicies', []))
                    except Exception as e:  # noqa: E722
                        pass
                    
                    file_systems.append(fs)
                
                marker = response.get('NextMarker')
                if not marker:
                    break
            
            logger.info(f"Found {len(file_systems)} EFS file systems")
            return file_systems
            
        except ClientError as e:
            handle_aws_error(e, "get_efs_file_systems")
            return []
    
    def get_file_system_metrics(self, file_system_id: str) -> Dict[str, Any]:
        """
        Obtém métricas de um sistema de arquivos específico
        
        Args:
            file_system_id: ID do sistema de arquivos
            
        Returns:
            Dicionário com métricas
        """
        dimensions = [{'Name': 'FileSystemId', 'Value': file_system_id}]
        
        metrics = {
            'client_connections': self.get_cloudwatch_metric(
                'AWS/EFS', 'ClientConnections', dimensions
            ),
            'data_read_bytes': self.get_cloudwatch_metric(
                'AWS/EFS', 'DataReadIOBytes', dimensions
            ),
            'data_write_bytes': self.get_cloudwatch_metric(
                'AWS/EFS', 'DataWriteIOBytes', dimensions
            ),
            'metadata_io_bytes': self.get_cloudwatch_metric(
                'AWS/EFS', 'MetadataIOBytes', dimensions
            ),
            'total_io_bytes': self.get_cloudwatch_metric(
                'AWS/EFS', 'TotalIOBytes', dimensions
            ),
            'burst_credit_balance': self.get_cloudwatch_metric(
                'AWS/EFS', 'BurstCreditBalance', dimensions
            ),
            'percent_io_limit': self.get_cloudwatch_metric(
                'AWS/EFS', 'PercentIOLimit', dimensions
            )
        }
        
        return metrics
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do EFS"""
        file_systems = self.get_file_systems()
        
        total_size = sum(fs.size_bytes for fs in file_systems)
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(file_systems),
            metrics={
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024 ** 3),
                'general_purpose_count': sum(1 for fs in file_systems if fs.performance_mode == 'generalPurpose'),
                'max_io_count': sum(1 for fs in file_systems if fs.performance_mode == 'maxIO'),
                'bursting_throughput_count': sum(1 for fs in file_systems if fs.throughput_mode == 'bursting'),
                'provisioned_throughput_count': sum(1 for fs in file_systems if fs.throughput_mode == 'provisioned'),
                'elastic_throughput_count': sum(1 for fs in file_systems if fs.throughput_mode == 'elastic'),
                'encrypted_count': sum(1 for fs in file_systems if fs.encrypted),
                'with_lifecycle_policies': sum(1 for fs in file_systems if fs.lifecycle_policies > 0)
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para EFS"""
        recommendations = []
        file_systems = self.get_file_systems()
        
        for fs in file_systems:
            if fs.lifecycle_policies == 0:
                size_gb = fs.size_bytes / (1024 ** 3)
                estimated_savings = size_gb * 0.30 * 0.85
                
                recommendations.append(ServiceRecommendation(
                    resource_id=fs.file_system_id,
                    resource_type='EFSFileSystem',
                    recommendation_type='ENABLE_LIFECYCLE',
                    description=f'File system {fs.name} não possui políticas de lifecycle. '
                               'Habilite Intelligent-Tiering para economizar em dados não acessados.',
                    estimated_savings=estimated_savings,
                    priority='MEDIUM',
                    implementation_effort='LOW',
                    details={
                        'file_system_id': fs.file_system_id,
                        'name': fs.name,
                        'size_gb': size_gb,
                        'suggestion': 'Habilitar transição para Infrequent Access após 30 dias'
                    }
                ))
            
            if fs.throughput_mode == 'provisioned':
                metrics = self.get_file_system_metrics(fs.file_system_id)
                io_limit = metrics.get('percent_io_limit', {}).get('average', 0)
                
                if io_limit < 30:
                    monthly_cost = fs.provisioned_throughput * 6.0
                    estimated_savings = monthly_cost * 0.5
                    
                    recommendations.append(ServiceRecommendation(
                        resource_id=fs.file_system_id,
                        resource_type='EFSFileSystem',
                        recommendation_type='OPTIMIZE_THROUGHPUT',
                        description=f'File system {fs.name} tem throughput provisionado mas baixa utilização. '
                                   'Considere mudar para Elastic ou Bursting.',
                        estimated_savings=estimated_savings,
                        priority='MEDIUM',
                        implementation_effort='LOW',
                        details={
                            'current_mode': 'provisioned',
                            'provisioned_mibps': fs.provisioned_throughput,
                            'io_limit_pct': io_limit,
                            'recommended_mode': 'elastic'
                        }
                    ))
            
            if fs.throughput_mode == 'bursting':
                metrics = self.get_file_system_metrics(fs.file_system_id)
                burst_credits = metrics.get('burst_credit_balance', {}).get('latest', 0)
                
                if burst_credits < 1000000000:
                    recommendations.append(ServiceRecommendation(
                        resource_id=fs.file_system_id,
                        resource_type='EFSFileSystem',
                        recommendation_type='BURST_CREDITS_LOW',
                        description=f'File system {fs.name} está com burst credits baixos. '
                                   'Considere aumentar o tamanho ou mudar para Elastic throughput.',
                        estimated_savings=0.0,
                        priority='HIGH',
                        implementation_effort='MEDIUM',
                        details={
                            'burst_credits': burst_credits,
                            'suggestion': 'Migrar para Elastic throughput mode'
                        }
                    ))
            
            if not fs.encrypted:
                recommendations.append(ServiceRecommendation(
                    resource_id=fs.file_system_id,
                    resource_type='EFSFileSystem',
                    recommendation_type='SECURITY',
                    description=f'File system {fs.name} não está criptografado. '
                               'Considere criar novo FS criptografado para compliance.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    implementation_effort='HIGH',
                    details={
                        'encrypted': False,
                        'note': 'EFS não permite habilitar criptografia após criação'
                    }
                ))
            
            if fs.number_of_mount_targets == 0:
                size_gb = fs.size_bytes / (1024 ** 3)
                monthly_cost = size_gb * 0.30
                
                recommendations.append(ServiceRecommendation(
                    resource_id=fs.file_system_id,
                    resource_type='EFSFileSystem',
                    recommendation_type='UNUSED_RESOURCE',
                    description=f'File system {fs.name} não possui mount targets. '
                               'Pode estar sem uso - considere deletar se não necessário.',
                    estimated_savings=monthly_cost,
                    priority='HIGH',
                    implementation_effort='LOW',
                    details={
                        'mount_targets': 0,
                        'size_gb': size_gb,
                        'monthly_cost': monthly_cost
                    }
                ))
        
        logger.info(f"Generated {len(recommendations)} EFS recommendations")
        return recommendations
