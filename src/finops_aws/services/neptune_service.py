"""
Neptune FinOps Service - Análise de Custos do Amazon Neptune

FASE 2.5 - Serviços de Alto Custo de Banco de Dados
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters e instâncias Neptune
- Análise de graph database
- Métricas de utilização
- Recomendações de otimização de custos
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class NeptuneInstance:
    """Representa uma instância Neptune"""
    db_instance_identifier: str
    db_instance_arn: str
    db_instance_class: str
    engine: str
    engine_version: str
    db_instance_status: str
    db_cluster_identifier: Optional[str] = None
    availability_zone: Optional[str] = None
    publicly_accessible: bool = False
    storage_encrypted: bool = False
    kms_key_id: Optional[str] = None
    auto_minor_version_upgrade: bool = True
    promotion_tier: int = 1
    is_cluster_writer: bool = False
    instance_create_time: Optional[datetime] = None
    preferred_maintenance_window: Optional[str] = None
    preferred_backup_window: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_writer(self) -> bool:
        return self.is_cluster_writer
    
    @property
    def is_reader(self) -> bool:
        return not self.is_cluster_writer
    
    @property
    def is_available(self) -> bool:
        return self.db_instance_status == 'available'
    
    @property
    def is_serverless(self) -> bool:
        return 'serverless' in self.db_instance_class.lower()
    
    @property
    def instance_size(self) -> str:
        parts = self.db_instance_class.split('.')
        return parts[-1] if len(parts) >= 3 else 'unknown'
    
    @property
    def instance_family(self) -> str:
        parts = self.db_instance_class.split('.')
        return parts[1] if len(parts) >= 2 else 'unknown'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'db_instance_identifier': self.db_instance_identifier,
            'db_instance_arn': self.db_instance_arn,
            'db_instance_class': self.db_instance_class,
            'engine': self.engine,
            'engine_version': self.engine_version,
            'db_instance_status': self.db_instance_status,
            'db_cluster_identifier': self.db_cluster_identifier,
            'availability_zone': self.availability_zone,
            'publicly_accessible': self.publicly_accessible,
            'storage_encrypted': self.storage_encrypted,
            'promotion_tier': self.promotion_tier,
            'is_cluster_writer': self.is_cluster_writer,
            'is_writer': self.is_writer,
            'is_reader': self.is_reader,
            'is_serverless': self.is_serverless,
            'instance_size': self.instance_size,
            'instance_family': self.instance_family,
            'tags': self.tags,
            'instance_create_time': self.instance_create_time.isoformat() if self.instance_create_time else None
        }


@dataclass
class NeptuneCluster:
    """Representa um cluster Neptune"""
    db_cluster_identifier: str
    db_cluster_arn: str
    engine: str
    engine_version: str
    status: str
    db_cluster_members: List[Dict[str, Any]] = field(default_factory=list)
    availability_zones: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    reader_endpoint: Optional[str] = None
    port: int = 8182
    backup_retention_period: int = 1
    preferred_backup_window: Optional[str] = None
    preferred_maintenance_window: Optional[str] = None
    storage_encrypted: bool = False
    kms_key_id: Optional[str] = None
    deletion_protection: bool = False
    iam_database_authentication_enabled: bool = False
    serverless_v2_scaling_configuration: Optional[Dict[str, Any]] = None
    cluster_create_time: Optional[datetime] = None
    enabled_cloudwatch_logs_exports: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_available(self) -> bool:
        return self.status == 'available'
    
    @property
    def is_serverless(self) -> bool:
        return self.serverless_v2_scaling_configuration is not None
    
    @property
    def instance_count(self) -> int:
        return len(self.db_cluster_members)
    
    @property
    def writer_count(self) -> int:
        return len([m for m in self.db_cluster_members if m.get('IsClusterWriter', False)])
    
    @property
    def reader_count(self) -> int:
        return self.instance_count - self.writer_count
    
    @property
    def has_deletion_protection(self) -> bool:
        return self.deletion_protection
    
    @property
    def has_encryption(self) -> bool:
        return self.storage_encrypted
    
    @property
    def has_iam_auth(self) -> bool:
        return self.iam_database_authentication_enabled
    
    @property
    def has_cloudwatch_logs(self) -> bool:
        return len(self.enabled_cloudwatch_logs_exports) > 0
    
    @property
    def min_capacity(self) -> Optional[float]:
        if self.serverless_v2_scaling_configuration:
            return self.serverless_v2_scaling_configuration.get('MinCapacity')
        return None
    
    @property
    def max_capacity(self) -> Optional[float]:
        if self.serverless_v2_scaling_configuration:
            return self.serverless_v2_scaling_configuration.get('MaxCapacity')
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'db_cluster_identifier': self.db_cluster_identifier,
            'db_cluster_arn': self.db_cluster_arn,
            'engine': self.engine,
            'engine_version': self.engine_version,
            'status': self.status,
            'endpoint': self.endpoint,
            'reader_endpoint': self.reader_endpoint,
            'port': self.port,
            'backup_retention_period': self.backup_retention_period,
            'storage_encrypted': self.storage_encrypted,
            'deletion_protection': self.deletion_protection,
            'iam_database_authentication_enabled': self.iam_database_authentication_enabled,
            'is_serverless': self.is_serverless,
            'instance_count': self.instance_count,
            'writer_count': self.writer_count,
            'reader_count': self.reader_count,
            'has_cloudwatch_logs': self.has_cloudwatch_logs,
            'enabled_cloudwatch_logs_exports': self.enabled_cloudwatch_logs_exports,
            'availability_zones': self.availability_zones,
            'serverless_config': self.serverless_v2_scaling_configuration,
            'tags': self.tags,
            'cluster_create_time': self.cluster_create_time.isoformat() if self.cluster_create_time else None
        }


class NeptuneService(BaseAWSService):
    """
    Serviço FinOps para Amazon Neptune
    
    Analisa clusters e instâncias Neptune (graph database)
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._neptune_client = None
        self._cloudwatch_client = None
    
    @property
    def neptune_client(self):
        if self._neptune_client is None:
            self._neptune_client = self.client_factory.get_client('neptune')
        return self._neptune_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            self._cloudwatch_client = self.client_factory.get_client('cloudwatch')
        return self._cloudwatch_client
    
    @property
    def service_name(self) -> str:
        return "Amazon Neptune"
    
    def health_check(self) -> bool:
        """Verifica se o serviço Neptune está acessível"""
        try:
            self.neptune_client.describe_db_clusters(MaxRecords=20)
            return True
        except Exception as e:
            logger.error(f"Neptune health check failed: {e}")
            return False
    
    def get_clusters(self) -> List[NeptuneCluster]:
        """Lista todos os clusters Neptune"""
        clusters = []
        try:
            paginator = self.neptune_client.get_paginator('describe_db_clusters')
            for page in paginator.paginate():
                for cluster in page.get('DBClusters', []):
                    if cluster.get('Engine') != 'neptune':
                        continue
                    
                    clusters.append(NeptuneCluster(
                        db_cluster_identifier=cluster['DBClusterIdentifier'],
                        db_cluster_arn=cluster['DBClusterArn'],
                        engine=cluster['Engine'],
                        engine_version=cluster['EngineVersion'],
                        status=cluster['Status'],
                        db_cluster_members=cluster.get('DBClusterMembers', []),
                        availability_zones=cluster.get('AvailabilityZones', []),
                        endpoint=cluster.get('Endpoint'),
                        reader_endpoint=cluster.get('ReaderEndpoint'),
                        port=cluster.get('Port', 8182),
                        backup_retention_period=cluster.get('BackupRetentionPeriod', 1),
                        preferred_backup_window=cluster.get('PreferredBackupWindow'),
                        preferred_maintenance_window=cluster.get('PreferredMaintenanceWindow'),
                        storage_encrypted=cluster.get('StorageEncrypted', False),
                        kms_key_id=cluster.get('KmsKeyId'),
                        deletion_protection=cluster.get('DeletionProtection', False),
                        iam_database_authentication_enabled=cluster.get('IAMDatabaseAuthenticationEnabled', False),
                        serverless_v2_scaling_configuration=cluster.get('ServerlessV2ScalingConfiguration'),
                        cluster_create_time=cluster.get('ClusterCreateTime'),
                        enabled_cloudwatch_logs_exports=cluster.get('EnabledCloudwatchLogsExports', []),
                        tags={t['Key']: t['Value'] for t in cluster.get('TagList', [])}
                    ))
            
            logger.info(f"Found {len(clusters)} Neptune clusters")
        except Exception as e:
            logger.error(f"Error listing Neptune clusters: {e}")
        
        return clusters
    
    def get_instances(self) -> List[NeptuneInstance]:
        """Lista todas as instâncias Neptune"""
        instances = []
        try:
            paginator = self.neptune_client.get_paginator('describe_db_instances')
            for page in paginator.paginate():
                for instance in page.get('DBInstances', []):
                    if instance.get('Engine') != 'neptune':
                        continue
                    
                    instances.append(NeptuneInstance(
                        db_instance_identifier=instance['DBInstanceIdentifier'],
                        db_instance_arn=instance['DBInstanceArn'],
                        db_instance_class=instance['DBInstanceClass'],
                        engine=instance['Engine'],
                        engine_version=instance['EngineVersion'],
                        db_instance_status=instance['DBInstanceStatus'],
                        db_cluster_identifier=instance.get('DBClusterIdentifier'),
                        availability_zone=instance.get('AvailabilityZone'),
                        publicly_accessible=instance.get('PubliclyAccessible', False),
                        storage_encrypted=instance.get('StorageEncrypted', False),
                        kms_key_id=instance.get('KmsKeyId'),
                        auto_minor_version_upgrade=instance.get('AutoMinorVersionUpgrade', True),
                        promotion_tier=instance.get('PromotionTier', 1),
                        instance_create_time=instance.get('InstanceCreateTime'),
                        preferred_maintenance_window=instance.get('PreferredMaintenanceWindow'),
                        preferred_backup_window=instance.get('PreferredBackupWindow'),
                        tags={t['Key']: t['Value'] for t in instance.get('TagList', [])}
                    ))
            
            logger.info(f"Found {len(instances)} Neptune instances")
        except Exception as e:
            logger.error(f"Error listing Neptune instances: {e}")
        
        return instances
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos Neptune"""
        clusters = self.get_clusters()
        instances = self.get_instances()
        
        return {
            'clusters': [c.to_dict() for c in clusters],
            'instances': [i.to_dict() for i in instances],
            'summary': {
                'total_clusters': len(clusters),
                'total_instances': len(instances),
                'available_clusters': len([c for c in clusters if c.is_available]),
                'serverless_clusters': len([c for c in clusters if c.is_serverless]),
                'encrypted_clusters': len([c for c in clusters if c.has_encryption]),
                'writer_instances': len([i for i in instances if i.is_writer]),
                'reader_instances': len([i for i in instances if i.is_reader]),
                'serverless_instances': len([i for i in instances if i.is_serverless])
            }
        }
    
    def get_metrics(self, cluster_identifier: Optional[str] = None, period_hours: int = 24) -> Dict[str, Any]:
        """Obtém métricas de utilização do Neptune"""
        metrics = {}
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)
        
        clusters = self.get_clusters()
        if cluster_identifier:
            clusters = [c for c in clusters if c.db_cluster_identifier == cluster_identifier]
        
        for cluster in clusters:
            try:
                cluster_metrics = {}
                
                metric_names = [
                    'CPUUtilization',
                    'FreeableMemory',
                    'GremlinRequestsPerSec',
                    'SparqlRequestsPerSec',
                    'NumTxCommitted',
                    'NumTxOpened',
                    'TotalRequestsPerSec',
                    'VolumeBytesUsed',
                    'VolumeReadIOPs',
                    'VolumeWriteIOPs'
                ]
                
                for metric_name in metric_names:
                    try:
                        response = self.cloudwatch_client.get_metric_statistics(
                            Namespace='AWS/Neptune',
                            MetricName=metric_name,
                            Dimensions=[
                                {'Name': 'DBClusterIdentifier', 'Value': cluster.db_cluster_identifier}
                            ],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['Average', 'Maximum', 'Sum']
                        )
                        
                        datapoints = response.get('Datapoints', [])
                        if datapoints:
                            cluster_metrics[metric_name] = {
                                'average': sum(d.get('Average', 0) for d in datapoints) / len(datapoints),
                                'maximum': max(d.get('Maximum', 0) for d in datapoints),
                                'sum': sum(d.get('Sum', 0) for d in datapoints)
                            }
                    except Exception as e:
                        logger.debug(f"Could not get metric {metric_name} for {cluster.db_cluster_identifier}: {e}")
                
                metrics[cluster.db_cluster_identifier] = cluster_metrics
                
            except Exception as e:
                logger.error(f"Error getting metrics for {cluster.db_cluster_identifier}: {e}")
        
        return metrics
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização de custos para Neptune"""
        recommendations = []
        clusters = self.get_clusters()
        instances = self.get_instances()
        
        for cluster in clusters:
            if not cluster.has_encryption:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='security',
                    title='Cluster Neptune sem Criptografia',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não está criptografado",
                    action='Crie um novo cluster criptografado e migre os dados do grafo',
                    estimated_savings=0.0,
                    priority='high',
                    metadata={'engine_version': cluster.engine_version}
                ))
            
            if not cluster.has_iam_auth:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='security',
                    title='Cluster Neptune sem Autenticação IAM',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não usa autenticação IAM",
                    action='Habilite IAM database authentication para maior segurança',
                    estimated_savings=0.0,
                    priority='medium',
                    metadata={}
                ))
            
            if not cluster.has_deletion_protection:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='reliability',
                    title='Cluster Neptune sem Proteção contra Deleção',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não tem proteção contra deleção",
                    action='Habilite deletion protection para ambientes de produção',
                    estimated_savings=0.0,
                    priority='medium',
                    metadata={}
                ))
            
            if not cluster.is_serverless and cluster.instance_count > 0:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='cost_optimization',
                    title='Considere Neptune Serverless',
                    description=f"Cluster provisionado '{cluster.db_cluster_identifier}' pode se beneficiar de serverless",
                    action='Avalie migração para Neptune Serverless para workloads variáveis',
                    estimated_savings=100.0,
                    priority='low',
                    metadata={'current_instance_count': cluster.instance_count}
                ))
            
            if cluster.reader_count == 0 and cluster.instance_count > 0:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='reliability',
                    title='Cluster Neptune sem Réplicas de Leitura',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não tem réplicas de leitura",
                    action='Adicione réplicas para alta disponibilidade e distribuição de queries',
                    estimated_savings=0.0,
                    priority='medium',
                    metadata={}
                ))
            
            if not cluster.has_cloudwatch_logs:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='operational',
                    title='Cluster Neptune sem Logs no CloudWatch',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não exporta logs para CloudWatch",
                    action='Habilite exportação de audit logs para melhor observabilidade',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={}
                ))
        
        for instance in instances:
            if not instance.is_available:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=instance.db_instance_identifier,
                    recommendation_type='operational',
                    title='Instância Neptune Não Disponível',
                    description=f"Instância '{instance.db_instance_identifier}' está em estado '{instance.db_instance_status}'",
                    action='Investigue o estado da instância e tome ação corretiva',
                    estimated_savings=0.0,
                    priority='high',
                    metadata={'status': instance.db_instance_status}
                ))
            
            if instance.instance_family == 'r4':
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=instance.db_instance_identifier,
                    recommendation_type='modernization',
                    title='Instância Neptune com Geração Antiga',
                    description=f"Instância '{instance.db_instance_identifier}' usa família r4 (geração antiga)",
                    action='Migre para r5 ou r6g para melhor custo-benefício',
                    estimated_savings=60.0,
                    priority='medium',
                    metadata={'current_class': instance.db_instance_class}
                ))
            
            if instance.publicly_accessible:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=instance.db_instance_identifier,
                    recommendation_type='security',
                    title='Instância Neptune Publicamente Acessível',
                    description=f"Instância '{instance.db_instance_identifier}' está publicamente acessível",
                    action='Desabilite acesso público para graph databases em produção',
                    estimated_savings=0.0,
                    priority='high',
                    metadata={}
                ))
        
        logger.info(f"Generated {len(recommendations)} Neptune recommendations")
        return recommendations
