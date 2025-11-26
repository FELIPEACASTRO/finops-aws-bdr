"""
S3 Service - Análise de custos e métricas do Amazon S3

FASE 2 do Roadmap FinOps AWS
Objetivo: Análise completa de Object Storage

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
class S3Bucket:
    """Representa um bucket S3"""
    name: str
    creation_date: Optional[datetime] = None
    region: Optional[str] = None
    size_bytes: int = 0
    object_count: int = 0
    storage_class: str = "STANDARD"
    versioning_enabled: bool = False
    lifecycle_rules: int = 0
    encryption_enabled: bool = False
    public_access_blocked: bool = True


class S3Service(BaseAWSService):
    """
    Serviço para análise completa do Amazon S3
    
    Coleta custos, métricas de uso e recomendações de otimização
    para buckets S3.
    
    Suporta injeção de dependências para Clean Architecture.
    """
    
    SERVICE_NAME = "Amazon S3"
    SERVICE_FILTER = "Amazon Simple Storage Service"
    
    def __init__(
        self,
        s3_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o S3Service
        
        Args:
            s3_client: Cliente S3 injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        super().__init__(cost_client=cost_client, cloudwatch_client=cloudwatch_client)
        self._s3_client = s3_client
    
    @property
    def s3_client(self):
        """Lazy loading do cliente S3"""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3', region_name=self.region)
        return self._s3_client
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.s3_client.list_buckets()
            return True
        except Exception:
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os buckets S3"""
        buckets = self.get_buckets()
        return [
            {
                'name': b.name,
                'region': b.region,
                'size_bytes': b.size_bytes,
                'object_count': b.object_count,
                'storage_class': b.storage_class
            }
            for b in buckets
        ]
    
    def get_buckets(self) -> List[S3Bucket]:
        """
        Obtém lista de todos os buckets S3 com detalhes
        
        Returns:
            Lista de S3Bucket
        """
        try:
            response = self.s3_client.list_buckets()
            buckets = []
            
            for bucket_data in response.get('Buckets', []):
                bucket = S3Bucket(
                    name=bucket_data['Name'],
                    creation_date=bucket_data.get('CreationDate')
                )
                
                try:
                    location = self.s3_client.get_bucket_location(Bucket=bucket.name)
                    bucket.region = location.get('LocationConstraint') or 'us-east-1'
                except Exception:
                    bucket.region = 'unknown'
                
                try:
                    versioning = self.s3_client.get_bucket_versioning(Bucket=bucket.name)
                    bucket.versioning_enabled = versioning.get('Status') == 'Enabled'
                except Exception:
                    pass
                
                try:
                    encryption = self.s3_client.get_bucket_encryption(Bucket=bucket.name)
                    bucket.encryption_enabled = bool(encryption.get('ServerSideEncryptionConfiguration'))
                except Exception:
                    pass
                
                try:
                    lifecycle = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket.name)
                    bucket.lifecycle_rules = len(lifecycle.get('Rules', []))
                except Exception:
                    pass
                
                try:
                    public_access = self.s3_client.get_public_access_block(Bucket=bucket.name)
                    config = public_access.get('PublicAccessBlockConfiguration', {})
                    bucket.public_access_blocked = all([
                        config.get('BlockPublicAcls', False),
                        config.get('IgnorePublicAcls', False),
                        config.get('BlockPublicPolicy', False),
                        config.get('RestrictPublicBuckets', False)
                    ])
                except Exception:
                    bucket.public_access_blocked = False
                
                buckets.append(bucket)
            
            logger.info(f"Found {len(buckets)} S3 buckets")
            return buckets
            
        except ClientError as e:
            handle_aws_error(e, "get_s3_buckets")
            return []
    
    def get_bucket_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """
        Obtém métricas de um bucket específico
        
        Args:
            bucket_name: Nome do bucket
            
        Returns:
            Dicionário com métricas do bucket
        """
        metrics = {}
        
        size_metric = self.get_cloudwatch_metric(
            namespace='AWS/S3',
            metric_name='BucketSizeBytes',
            dimensions=[
                {'Name': 'BucketName', 'Value': bucket_name},
                {'Name': 'StorageType', 'Value': 'StandardStorage'}
            ],
            period_days=7
        )
        metrics['size_bytes'] = size_metric
        
        objects_metric = self.get_cloudwatch_metric(
            namespace='AWS/S3',
            metric_name='NumberOfObjects',
            dimensions=[
                {'Name': 'BucketName', 'Value': bucket_name},
                {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
            ],
            period_days=7
        )
        metrics['object_count'] = objects_metric
        
        return metrics
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do S3"""
        buckets = self.get_buckets()
        
        total_size = 0
        total_objects = 0
        
        for bucket in buckets[:10]:
            bucket_metrics = self.get_bucket_metrics(bucket.name)
            total_size += bucket_metrics.get('size_bytes', {}).get('latest', 0)
            total_objects += bucket_metrics.get('object_count', {}).get('latest', 0)
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(buckets),
            metrics={
                'total_size_bytes': total_size,
                'total_objects': total_objects,
                'buckets_with_versioning': sum(1 for b in buckets if b.versioning_enabled),
                'buckets_with_encryption': sum(1 for b in buckets if b.encryption_enabled),
                'buckets_with_lifecycle': sum(1 for b in buckets if b.lifecycle_rules > 0),
                'public_buckets': sum(1 for b in buckets if not b.public_access_blocked)
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para S3"""
        recommendations = []
        buckets = self.get_buckets()
        
        for bucket in buckets:
            if not bucket.lifecycle_rules:
                recommendations.append(ServiceRecommendation(
                    resource_id=bucket.name,
                    resource_type='S3Bucket',
                    recommendation_type='LIFECYCLE_POLICY',
                    description=f'Bucket {bucket.name} não possui políticas de ciclo de vida. '
                               'Considere implementar para reduzir custos de armazenamento.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    implementation_effort='LOW',
                    details={
                        'bucket_name': bucket.name,
                        'region': bucket.region,
                        'suggestion': 'Implementar Intelligent-Tiering ou transição para Glacier'
                    }
                ))
            
            if bucket.versioning_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=bucket.name,
                    resource_type='S3Bucket',
                    recommendation_type='VERSION_CLEANUP',
                    description=f'Bucket {bucket.name} tem versionamento habilitado. '
                               'Considere criar regras para expirar versões antigas.',
                    estimated_savings=0.0,
                    priority='LOW',
                    implementation_effort='LOW',
                    details={
                        'bucket_name': bucket.name,
                        'versioning_enabled': True,
                        'suggestion': 'Adicionar regra de expiração de noncurrent versions'
                    }
                ))
            
            if not bucket.public_access_blocked:
                recommendations.append(ServiceRecommendation(
                    resource_id=bucket.name,
                    resource_type='S3Bucket',
                    recommendation_type='SECURITY',
                    description=f'Bucket {bucket.name} pode ter acesso público. '
                               'Revise as configurações de segurança.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    implementation_effort='LOW',
                    details={
                        'bucket_name': bucket.name,
                        'public_access_blocked': False,
                        'suggestion': 'Habilitar Block Public Access'
                    }
                ))
            
            if not bucket.encryption_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=bucket.name,
                    resource_type='S3Bucket',
                    recommendation_type='SECURITY',
                    description=f'Bucket {bucket.name} não possui criptografia padrão. '
                               'Considere habilitar criptografia SSE-S3 ou SSE-KMS.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    implementation_effort='LOW',
                    details={
                        'bucket_name': bucket.name,
                        'encryption_enabled': False,
                        'suggestion': 'Habilitar default encryption com SSE-S3'
                    }
                ))
        
        logger.info(f"Generated {len(recommendations)} S3 recommendations")
        return recommendations
    
    def get_storage_class_analysis(self) -> Dict[str, Any]:
        """
        Analisa distribuição de classes de armazenamento
        
        Returns:
            Dicionário com análise de storage classes
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            response = self.cost_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [self.SERVICE_FILTER]
                    }
                }
            )
            
            storage_costs = {}
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    usage_type = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if 'Standard' in usage_type:
                        storage_class = 'Standard'
                    elif 'IntelligentTiering' in usage_type:
                        storage_class = 'Intelligent-Tiering'
                    elif 'Glacier' in usage_type:
                        storage_class = 'Glacier'
                    elif 'OneZone' in usage_type:
                        storage_class = 'One Zone-IA'
                    elif 'StandardIA' in usage_type or 'InfrequentAccess' in usage_type:
                        storage_class = 'Standard-IA'
                    else:
                        storage_class = 'Other'
                    
                    if storage_class not in storage_costs:
                        storage_costs[storage_class] = 0.0
                    storage_costs[storage_class] += cost
            
            return {
                'storage_class_costs': storage_costs,
                'total_cost': sum(storage_costs.values()),
                'optimization_potential': self._calculate_optimization_potential(storage_costs)
            }
            
        except ClientError as e:
            handle_aws_error(e, "get_storage_class_analysis")
            return {}
    
    def _calculate_optimization_potential(self, storage_costs: Dict[str, float]) -> Dict[str, Any]:
        """Calcula potencial de otimização baseado em storage classes"""
        standard_cost = storage_costs.get('Standard', 0.0)
        
        if standard_cost == 0:
            return {'potential_savings': 0.0, 'recommendation': 'Nenhum dado de Standard storage'}
        
        potential_savings = standard_cost * 0.40
        
        return {
            'potential_savings': potential_savings,
            'recommendation': 'Migrar dados acessados com pouca frequência para Intelligent-Tiering',
            'current_standard_cost': standard_cost,
            'estimated_savings_pct': 40
        }
