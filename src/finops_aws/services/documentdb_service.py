"""
DocumentDB FinOps Service - Análise de Custos do Amazon DocumentDB

FASE 2.5 - Serviços de Alto Custo de Banco de Dados
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters e instâncias DocumentDB
- Análise de configuração e storage
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
class DocumentDBInstance:
    """Representa uma instância DocumentDB"""
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
    ca_certificate_identifier: Optional[str] = None
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
            'instance_size': self.instance_size,
            'instance_family': self.instance_family,
            'tags': self.tags,
            'instance_create_time': self.instance_create_time.isoformat() if self.instance_create_time else None
        }


@dataclass
class DocumentDBCluster:
    """Representa um cluster DocumentDB"""
    db_cluster_identifier: str
    db_cluster_arn: str
    engine: str
    engine_version: str
    status: str
    db_cluster_members: List[Dict[str, Any]] = field(default_factory=list)
    availability_zones: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    reader_endpoint: Optional[str] = None
    port: int = 27017
    master_username: Optional[str] = None
    backup_retention_period: int = 1
    preferred_backup_window: Optional[str] = None
    preferred_maintenance_window: Optional[str] = None
    storage_encrypted: bool = False
    kms_key_id: Optional[str] = None
    deletion_protection: bool = False
    multi_az: bool = False
    cluster_create_time: Optional[datetime] = None
    enabled_cloudwatch_logs_exports: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_available(self) -> bool:
        return self.status == 'available'
    
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
    def has_cloudwatch_logs(self) -> bool:
        return len(self.enabled_cloudwatch_logs_exports) > 0
    
    @property
    def has_multi_az(self) -> bool:
        return self.multi_az or len(self.availability_zones) > 1
    
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
            'multi_az': self.multi_az,
            'instance_count': self.instance_count,
            'writer_count': self.writer_count,
            'reader_count': self.reader_count,
            'has_cloudwatch_logs': self.has_cloudwatch_logs,
            'enabled_cloudwatch_logs_exports': self.enabled_cloudwatch_logs_exports,
            'availability_zones': self.availability_zones,
            'tags': self.tags,
            'cluster_create_time': self.cluster_create_time.isoformat() if self.cluster_create_time else None
        }


@dataclass 
class DocumentDBClusterSnapshot:
    """Representa um snapshot de cluster DocumentDB"""
    db_cluster_snapshot_identifier: str
    db_cluster_snapshot_arn: str
    db_cluster_identifier: str
    status: str
    engine: str
    engine_version: str
    snapshot_type: str
    snapshot_create_time: Optional[datetime] = None
    storage_encrypted: bool = False
    kms_key_id: Optional[str] = None
    percent_progress: int = 0
    
    @property
    def is_automatic(self) -> bool:
        return self.snapshot_type == 'automated'
    
    @property
    def is_manual(self) -> bool:
        return self.snapshot_type == 'manual'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'db_cluster_snapshot_identifier': self.db_cluster_snapshot_identifier,
            'db_cluster_snapshot_arn': self.db_cluster_snapshot_arn,
            'db_cluster_identifier': self.db_cluster_identifier,
            'status': self.status,
            'engine': self.engine,
            'engine_version': self.engine_version,
            'snapshot_type': self.snapshot_type,
            'storage_encrypted': self.storage_encrypted,
            'percent_progress': self.percent_progress,
            'is_automatic': self.is_automatic,
            'is_manual': self.is_manual,
            'snapshot_create_time': self.snapshot_create_time.isoformat() if self.snapshot_create_time else None
        }


class DocumentDBService(BaseAWSService):
    """
    Serviço FinOps para Amazon DocumentDB
    
    Analisa clusters e instâncias DocumentDB (compatível com MongoDB)
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._docdb_client = None
        self._cloudwatch_client = None
    
    @property
    def docdb_client(self):
        if self._docdb_client is None:
            self._docdb_client = self.client_factory.get_client('docdb')
        return self._docdb_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            self._cloudwatch_client = self.client_factory.get_client('cloudwatch')
        return self._cloudwatch_client
    
    @property
    def service_name(self) -> str:
        return "Amazon DocumentDB"
    
    def health_check(self) -> bool:
        """Verifica se o serviço DocumentDB está acessível"""
        try:
            self.docdb_client.describe_db_clusters(MaxRecords=20)
            return True
        except Exception as e:
            logger.error(f"DocumentDB health check failed: {e}")
            return False
    
    def get_clusters(self) -> List[DocumentDBCluster]:
        """Lista todos os clusters DocumentDB"""
        clusters = []
        try:
            paginator = self.docdb_client.get_paginator('describe_db_clusters')
            for page in paginator.paginate():
                for cluster in page.get('DBClusters', []):
                    if cluster.get('Engine') != 'docdb':
                        continue
                    
                    clusters.append(DocumentDBCluster(
                        db_cluster_identifier=cluster['DBClusterIdentifier'],
                        db_cluster_arn=cluster['DBClusterArn'],
                        engine=cluster['Engine'],
                        engine_version=cluster['EngineVersion'],
                        status=cluster['Status'],
                        db_cluster_members=cluster.get('DBClusterMembers', []),
                        availability_zones=cluster.get('AvailabilityZones', []),
                        endpoint=cluster.get('Endpoint'),
                        reader_endpoint=cluster.get('ReaderEndpoint'),
                        port=cluster.get('Port', 27017),
                        master_username=cluster.get('MasterUsername'),
                        backup_retention_period=cluster.get('BackupRetentionPeriod', 1),
                        preferred_backup_window=cluster.get('PreferredBackupWindow'),
                        preferred_maintenance_window=cluster.get('PreferredMaintenanceWindow'),
                        storage_encrypted=cluster.get('StorageEncrypted', False),
                        kms_key_id=cluster.get('KmsKeyId'),
                        deletion_protection=cluster.get('DeletionProtection', False),
                        multi_az=cluster.get('MultiAZ', False),
                        cluster_create_time=cluster.get('ClusterCreateTime'),
                        enabled_cloudwatch_logs_exports=cluster.get('EnabledCloudwatchLogsExports', []),
                        tags={t['Key']: t['Value'] for t in cluster.get('TagList', [])}
                    ))
            
            logger.info(f"Found {len(clusters)} DocumentDB clusters")
        except Exception as e:
            logger.error(f"Error listing DocumentDB clusters: {e}")
        
        return clusters
    
    def get_instances(self) -> List[DocumentDBInstance]:
        """Lista todas as instâncias DocumentDB"""
        instances = []
        try:
            paginator = self.docdb_client.get_paginator('describe_db_instances')
            for page in paginator.paginate():
                for instance in page.get('DBInstances', []):
                    if instance.get('Engine') != 'docdb':
                        continue
                    
                    instances.append(DocumentDBInstance(
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
                        ca_certificate_identifier=instance.get('CACertificateIdentifier'),
                        tags={t['Key']: t['Value'] for t in instance.get('TagList', [])}
                    ))
            
            logger.info(f"Found {len(instances)} DocumentDB instances")
        except Exception as e:
            logger.error(f"Error listing DocumentDB instances: {e}")
        
        return instances
    
    def get_cluster_snapshots(self) -> List[DocumentDBClusterSnapshot]:
        """Lista todos os snapshots de clusters DocumentDB"""
        snapshots = []
        try:
            paginator = self.docdb_client.get_paginator('describe_db_cluster_snapshots')
            for page in paginator.paginate():
                for snapshot in page.get('DBClusterSnapshots', []):
                    if snapshot.get('Engine') != 'docdb':
                        continue
                    
                    snapshots.append(DocumentDBClusterSnapshot(
                        db_cluster_snapshot_identifier=snapshot['DBClusterSnapshotIdentifier'],
                        db_cluster_snapshot_arn=snapshot['DBClusterSnapshotArn'],
                        db_cluster_identifier=snapshot['DBClusterIdentifier'],
                        status=snapshot['Status'],
                        engine=snapshot['Engine'],
                        engine_version=snapshot['EngineVersion'],
                        snapshot_type=snapshot.get('SnapshotType', 'manual'),
                        snapshot_create_time=snapshot.get('SnapshotCreateTime'),
                        storage_encrypted=snapshot.get('StorageEncrypted', False),
                        kms_key_id=snapshot.get('KmsKeyId'),
                        percent_progress=snapshot.get('PercentProgress', 0)
                    ))
            
            logger.info(f"Found {len(snapshots)} DocumentDB cluster snapshots")
        except Exception as e:
            logger.error(f"Error listing DocumentDB cluster snapshots: {e}")
        
        return snapshots
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos DocumentDB"""
        clusters = self.get_clusters()
        instances = self.get_instances()
        snapshots = self.get_cluster_snapshots()
        
        return {
            'clusters': [c.to_dict() for c in clusters],
            'instances': [i.to_dict() for i in instances],
            'snapshots': [s.to_dict() for s in snapshots],
            'summary': {
                'total_clusters': len(clusters),
                'total_instances': len(instances),
                'total_snapshots': len(snapshots),
                'available_clusters': len([c for c in clusters if c.is_available]),
                'encrypted_clusters': len([c for c in clusters if c.has_encryption]),
                'multi_az_clusters': len([c for c in clusters if c.has_multi_az]),
                'writer_instances': len([i for i in instances if i.is_writer]),
                'reader_instances': len([i for i in instances if i.is_reader])
            }
        }
    
    def get_metrics(self, cluster_identifier: Optional[str] = None, period_hours: int = 24) -> Dict[str, Any]:
        """Obtém métricas de utilização do DocumentDB"""
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
                    'DatabaseConnections',
                    'ReadIOPS',
                    'WriteIOPS',
                    'ReadLatency',
                    'WriteLatency',
                    'VolumeBytesUsed'
                ]
                
                for metric_name in metric_names:
                    try:
                        response = self.cloudwatch_client.get_metric_statistics(
                            Namespace='AWS/DocDB',
                            MetricName=metric_name,
                            Dimensions=[
                                {'Name': 'DBClusterIdentifier', 'Value': cluster.db_cluster_identifier}
                            ],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['Average', 'Maximum', 'Minimum']
                        )
                        
                        datapoints = response.get('Datapoints', [])
                        if datapoints:
                            cluster_metrics[metric_name] = {
                                'average': sum(d.get('Average', 0) for d in datapoints) / len(datapoints),
                                'maximum': max(d.get('Maximum', 0) for d in datapoints),
                                'minimum': min(d.get('Minimum', 0) for d in datapoints)
                            }
                    except Exception as e:
                        logger.debug(f"Could not get metric {metric_name} for {cluster.db_cluster_identifier}: {e}")
                
                metrics[cluster.db_cluster_identifier] = cluster_metrics
                
            except Exception as e:
                logger.error(f"Error getting metrics for {cluster.db_cluster_identifier}: {e}")
        
        return metrics
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização de custos para DocumentDB"""
        recommendations = []
        clusters = self.get_clusters()
        instances = self.get_instances()
        
        for cluster in clusters:
            if not cluster.has_encryption:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='security',
                    title='Cluster DocumentDB sem Criptografia',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não está criptografado",
                    action='Crie um novo cluster criptografado e migre os dados',
                    estimated_savings=0.0,
                    priority='high',
                    metadata={'engine_version': cluster.engine_version}
                ))
            
            if not cluster.has_deletion_protection:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='reliability',
                    title='Cluster DocumentDB sem Proteção contra Deleção',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não tem proteção contra deleção",
                    action='Habilite deletion protection para proteção em produção',
                    estimated_savings=0.0,
                    priority='medium',
                    metadata={}
                ))
            
            if cluster.backup_retention_period < 7:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='reliability',
                    title='Período de Retenção de Backup Curto',
                    description=f"Cluster '{cluster.db_cluster_identifier}' tem apenas {cluster.backup_retention_period} dia(s) de retenção",
                    action='Considere aumentar a retenção para pelo menos 7 dias',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={'current_retention': cluster.backup_retention_period}
                ))
            
            if not cluster.has_cloudwatch_logs:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='operational',
                    title='Cluster DocumentDB sem Logs no CloudWatch',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não exporta logs para CloudWatch",
                    action='Habilite exportação de logs (audit, profiler) para melhor observabilidade',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={}
                ))
            
            if cluster.reader_count == 0 and cluster.instance_count > 0:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='reliability',
                    title='Cluster DocumentDB sem Réplicas de Leitura',
                    description=f"Cluster '{cluster.db_cluster_identifier}' não tem instâncias de leitura",
                    action='Adicione réplicas de leitura para alta disponibilidade e distribuição de carga',
                    estimated_savings=0.0,
                    priority='medium',
                    metadata={'current_instance_count': cluster.instance_count}
                ))
            
            if cluster.reader_count > 3:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=cluster.db_cluster_identifier,
                    recommendation_type='cost_optimization',
                    title='Cluster DocumentDB com Muitas Réplicas',
                    description=f"Cluster '{cluster.db_cluster_identifier}' tem {cluster.reader_count} réplicas de leitura",
                    action='Avalie se todas as réplicas são necessárias. Considere consolidar',
                    estimated_savings=150.0 * (cluster.reader_count - 3),
                    priority='medium',
                    metadata={'reader_count': cluster.reader_count}
                ))
        
        instance_classes = {}
        for instance in instances:
            cls = instance.db_instance_class
            if cls not in instance_classes:
                instance_classes[cls] = 0
            instance_classes[cls] += 1
        
        for instance in instances:
            if not instance.is_available:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=instance.db_instance_identifier,
                    recommendation_type='operational',
                    title='Instância DocumentDB Não Disponível',
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
                    title='Instância DocumentDB com Geração Antiga',
                    description=f"Instância '{instance.db_instance_identifier}' usa família r4 (geração antiga)",
                    action='Migre para r5 ou r6g para melhor custo-benefício',
                    estimated_savings=50.0,
                    priority='medium',
                    metadata={'current_class': instance.db_instance_class}
                ))
        
        logger.info(f"Generated {len(recommendations)} DocumentDB recommendations")
        return recommendations
