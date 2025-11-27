"""
Aurora FinOps Service - Análise de Custos do Amazon Aurora

FASE 2.4 - Serviços Não-Serverless de Alto Custo
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters Aurora (MySQL, PostgreSQL)
- Análise de instâncias e storage
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
class AuroraInstance:
    """Representa uma instância Aurora"""
    db_instance_identifier: str
    db_instance_arn: str
    db_instance_class: str
    engine: str
    engine_version: str
    status: str
    db_cluster_identifier: Optional[str] = None
    availability_zone: Optional[str] = None
    multi_az: bool = False
    publicly_accessible: bool = False
    storage_encrypted: bool = False
    kms_key_id: Optional[str] = None
    performance_insights_enabled: bool = False
    enhanced_monitoring_interval: int = 0
    auto_minor_version_upgrade: bool = True
    promotion_tier: int = 1
    is_cluster_writer: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    @property
    def is_serverless(self) -> bool:
        return 'serverless' in self.db_instance_class.lower()
    
    @property
    def is_writer(self) -> bool:
        return self.is_cluster_writer
    
    @property
    def is_reader(self) -> bool:
        return not self.is_cluster_writer
    
    @property
    def is_mysql(self) -> bool:
        return 'mysql' in self.engine.lower()
    
    @property
    def is_postgresql(self) -> bool:
        return 'postgres' in self.engine.lower()
    
    @property
    def has_performance_insights(self) -> bool:
        return self.performance_insights_enabled
    
    @property
    def has_enhanced_monitoring(self) -> bool:
        return self.enhanced_monitoring_interval > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'db_instance_identifier': self.db_instance_identifier,
            'db_instance_arn': self.db_instance_arn,
            'db_instance_class': self.db_instance_class,
            'engine': self.engine,
            'engine_version': self.engine_version,
            'status': self.status,
            'db_cluster_identifier': self.db_cluster_identifier,
            'availability_zone': self.availability_zone,
            'multi_az': self.multi_az,
            'publicly_accessible': self.publicly_accessible,
            'storage_encrypted': self.storage_encrypted,
            'performance_insights_enabled': self.performance_insights_enabled,
            'enhanced_monitoring_interval': self.enhanced_monitoring_interval,
            'promotion_tier': self.promotion_tier,
            'is_cluster_writer': self.is_cluster_writer,
            'is_serverless': self.is_serverless,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class AuroraCluster:
    """Representa um cluster Aurora"""
    db_cluster_identifier: str
    db_cluster_arn: str
    engine: str
    engine_version: str
    engine_mode: str
    status: str
    database_name: Optional[str] = None
    master_username: Optional[str] = None
    endpoint: Optional[str] = None
    reader_endpoint: Optional[str] = None
    port: int = 3306
    multi_az: bool = False
    storage_encrypted: bool = False
    kms_key_id: Optional[str] = None
    deletion_protection: bool = False
    backup_retention_period: int = 7
    preferred_backup_window: Optional[str] = None
    preferred_maintenance_window: Optional[str] = None
    allocated_storage: int = 0
    copy_tags_to_snapshot: bool = False
    cross_account_clone: bool = False
    http_endpoint_enabled: bool = False
    iam_database_authentication_enabled: bool = False
    global_write_forwarding_status: Optional[str] = None
    serverless_v2_scaling_configuration: Optional[Dict[str, Any]] = None
    performance_insights_enabled: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    db_cluster_members: List[Dict[str, Any]] = field(default_factory=list)
    instances: List[AuroraInstance] = field(default_factory=list)
    
    @property
    def is_serverless_v1(self) -> bool:
        return self.engine_mode == 'serverless'
    
    @property
    def is_serverless_v2(self) -> bool:
        return self.serverless_v2_scaling_configuration is not None
    
    @property
    def is_serverless(self) -> bool:
        return self.is_serverless_v1 or self.is_serverless_v2
    
    @property
    def is_provisioned(self) -> bool:
        return self.engine_mode == 'provisioned'
    
    @property
    def is_mysql(self) -> bool:
        return 'mysql' in self.engine.lower()
    
    @property
    def is_postgresql(self) -> bool:
        return 'postgres' in self.engine.lower()
    
    @property
    def instance_count(self) -> int:
        return len(self.instances)
    
    @property
    def writer_count(self) -> int:
        return len([i for i in self.instances if i.is_writer])
    
    @property
    def reader_count(self) -> int:
        return len([i for i in self.instances if i.is_reader])
    
    @property
    def has_readers(self) -> bool:
        return self.reader_count > 0
    
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
            'engine_mode': self.engine_mode,
            'status': self.status,
            'database_name': self.database_name,
            'endpoint': self.endpoint,
            'reader_endpoint': self.reader_endpoint,
            'port': self.port,
            'multi_az': self.multi_az,
            'storage_encrypted': self.storage_encrypted,
            'deletion_protection': self.deletion_protection,
            'backup_retention_period': self.backup_retention_period,
            'allocated_storage': self.allocated_storage,
            'is_serverless': self.is_serverless,
            'is_serverless_v2': self.is_serverless_v2,
            'is_provisioned': self.is_provisioned,
            'instance_count': self.instance_count,
            'writer_count': self.writer_count,
            'reader_count': self.reader_count,
            'min_capacity': self.min_capacity,
            'max_capacity': self.max_capacity,
            'performance_insights_enabled': self.performance_insights_enabled,
            'iam_database_authentication_enabled': self.iam_database_authentication_enabled,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'instances': [i.to_dict() for i in self.instances]
        }


class AuroraService(BaseAWSService):
    """
    Serviço FinOps para Amazon Aurora
    
    Analisa clusters Aurora MySQL e PostgreSQL, incluindo
    configurações serverless, e fornece recomendações de otimização.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._rds_client = None
        self._cloudwatch_client = None
    
    @property
    def rds_client(self):
        if self._rds_client is None:
            from ..core.factories import AWSServiceType
            self._rds_client = self.client_factory.get_client(AWSServiceType.RDS)
        return self._rds_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            from ..core.factories import AWSServiceType
            self._cloudwatch_client = self.client_factory.get_client(AWSServiceType.CLOUDWATCH)
        return self._cloudwatch_client
    
    def get_service_name(self) -> str:
        return "Aurora"
    
    def health_check(self) -> bool:
        try:
            self.rds_client.describe_db_clusters(MaxRecords=20)
            return True
        except Exception as e:
            logger.error(f"Aurora health check failed: {e}")
            return False
    
    def get_clusters(self) -> List[AuroraCluster]:
        """Lista todos os clusters Aurora"""
        clusters = []
        
        try:
            paginator = self.rds_client.get_paginator('describe_db_clusters')
            
            for page in paginator.paginate():
                for cluster_data in page.get('DBClusters', []):
                    engine = cluster_data.get('Engine', '')
                    if 'aurora' not in engine.lower():
                        continue
                    
                    cluster = self._parse_cluster(cluster_data)
                    if cluster:
                        cluster.instances = self._get_cluster_instances(cluster.db_cluster_identifier)
                        clusters.append(cluster)
            
            logger.info(f"Found {len(clusters)} Aurora clusters")
            
        except Exception as e:
            logger.error(f"Error listing Aurora clusters: {e}")
        
        return clusters
    
    def _parse_cluster(self, data: Dict[str, Any]) -> Optional[AuroraCluster]:
        """Parse dados do cluster"""
        try:
            return AuroraCluster(
                db_cluster_identifier=data.get('DBClusterIdentifier', ''),
                db_cluster_arn=data.get('DBClusterArn', ''),
                engine=data.get('Engine', ''),
                engine_version=data.get('EngineVersion', ''),
                engine_mode=data.get('EngineMode', 'provisioned'),
                status=data.get('Status', ''),
                database_name=data.get('DatabaseName'),
                master_username=data.get('MasterUsername'),
                endpoint=data.get('Endpoint'),
                reader_endpoint=data.get('ReaderEndpoint'),
                port=data.get('Port', 3306),
                multi_az=data.get('MultiAZ', False),
                storage_encrypted=data.get('StorageEncrypted', False),
                kms_key_id=data.get('KmsKeyId'),
                deletion_protection=data.get('DeletionProtection', False),
                backup_retention_period=data.get('BackupRetentionPeriod', 7),
                preferred_backup_window=data.get('PreferredBackupWindow'),
                preferred_maintenance_window=data.get('PreferredMaintenanceWindow'),
                allocated_storage=data.get('AllocatedStorage', 0),
                copy_tags_to_snapshot=data.get('CopyTagsToSnapshot', False),
                http_endpoint_enabled=data.get('HttpEndpointEnabled', False),
                iam_database_authentication_enabled=data.get('IAMDatabaseAuthenticationEnabled', False),
                global_write_forwarding_status=data.get('GlobalWriteForwardingStatus'),
                serverless_v2_scaling_configuration=data.get('ServerlessV2ScalingConfiguration'),
                performance_insights_enabled=data.get('PerformanceInsightsEnabled', False),
                tags={t['Key']: t['Value'] for t in data.get('TagList', [])},
                created_at=data.get('ClusterCreateTime'),
                db_cluster_members=data.get('DBClusterMembers', [])
            )
        except Exception as e:
            logger.error(f"Error parsing cluster: {e}")
            return None
    
    def _get_cluster_instances(self, cluster_identifier: str) -> List[AuroraInstance]:
        """Obtém instâncias de um cluster"""
        instances = []
        
        try:
            paginator = self.rds_client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate(
                Filters=[
                    {'Name': 'db-cluster-id', 'Values': [cluster_identifier]}
                ]
            ):
                for instance_data in page.get('DBInstances', []):
                    instance = self._parse_instance(instance_data)
                    if instance:
                        instances.append(instance)
            
        except Exception as e:
            logger.warning(f"Error getting instances for cluster {cluster_identifier}: {e}")
        
        return instances
    
    def _parse_instance(self, data: Dict[str, Any]) -> Optional[AuroraInstance]:
        """Parse dados da instância"""
        try:
            return AuroraInstance(
                db_instance_identifier=data.get('DBInstanceIdentifier', ''),
                db_instance_arn=data.get('DBInstanceArn', ''),
                db_instance_class=data.get('DBInstanceClass', ''),
                engine=data.get('Engine', ''),
                engine_version=data.get('EngineVersion', ''),
                status=data.get('DBInstanceStatus', ''),
                db_cluster_identifier=data.get('DBClusterIdentifier'),
                availability_zone=data.get('AvailabilityZone'),
                multi_az=data.get('MultiAZ', False),
                publicly_accessible=data.get('PubliclyAccessible', False),
                storage_encrypted=data.get('StorageEncrypted', False),
                kms_key_id=data.get('KmsKeyId'),
                performance_insights_enabled=data.get('PerformanceInsightsEnabled', False),
                enhanced_monitoring_interval=data.get('MonitoringInterval', 0),
                auto_minor_version_upgrade=data.get('AutoMinorVersionUpgrade', True),
                promotion_tier=data.get('PromotionTier', 1),
                is_cluster_writer=data.get('IsClusterWriter', False),
                tags={t['Key']: t['Value'] for t in data.get('TagList', [])},
                created_at=data.get('InstanceCreateTime')
            )
        except Exception as e:
            logger.error(f"Error parsing instance: {e}")
            return None
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos Aurora"""
        clusters = self.get_clusters()
        
        total_instances = sum(c.instance_count for c in clusters)
        mysql_clusters = [c for c in clusters if c.is_mysql]
        postgres_clusters = [c for c in clusters if c.is_postgresql]
        serverless_clusters = [c for c in clusters if c.is_serverless]
        
        return {
            'clusters': [c.to_dict() for c in clusters],
            'summary': {
                'total_clusters': len(clusters),
                'total_instances': total_instances,
                'mysql_clusters': len(mysql_clusters),
                'postgresql_clusters': len(postgres_clusters),
                'serverless_clusters': len(serverless_clusters),
                'provisioned_clusters': len([c for c in clusters if c.is_provisioned]),
                'encrypted_clusters': len([c for c in clusters if c.storage_encrypted]),
                'multi_az_clusters': len([c for c in clusters if c.multi_az])
            }
        }
    
    def get_costs(self) -> List[ServiceCost]:
        """Retorna estimativas de custo para clusters Aurora"""
        costs = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            cluster_cost = 0.0
            
            if cluster.is_serverless_v2:
                min_cap = cluster.min_capacity or 0.5
                avg_capacity = (min_cap + (cluster.max_capacity or 16)) / 2
                acu_rate = 0.12
                cluster_cost = avg_capacity * acu_rate * 24 * 30
            else:
                for instance in cluster.instances:
                    hourly_rate = self._get_instance_hourly_rate(instance.db_instance_class)
                    cluster_cost += hourly_rate * 24 * 30
            
            storage_cost = cluster.allocated_storage * 0.10
            cluster_cost += storage_cost
            
            costs.append(ServiceCost(
                service_name='Aurora',
                resource_id=cluster.db_cluster_arn,
                cost=cluster_cost,
                period='monthly_estimate',
                currency='USD',
                metadata={
                    'cluster_name': cluster.db_cluster_identifier,
                    'engine': cluster.engine,
                    'is_serverless': cluster.is_serverless,
                    'instance_count': cluster.instance_count,
                    'storage_gb': cluster.allocated_storage
                }
            ))
        
        return costs
    
    def _get_instance_hourly_rate(self, instance_class: str) -> float:
        """Retorna taxa horária estimada para classe de instância"""
        rates = {
            'db.t3.micro': 0.018,
            'db.t3.small': 0.036,
            'db.t3.medium': 0.072,
            'db.t3.large': 0.145,
            'db.t4g.micro': 0.016,
            'db.t4g.small': 0.032,
            'db.t4g.medium': 0.065,
            'db.t4g.large': 0.129,
            'db.r5.large': 0.29,
            'db.r5.xlarge': 0.58,
            'db.r5.2xlarge': 1.16,
            'db.r5.4xlarge': 2.32,
            'db.r6g.large': 0.26,
            'db.r6g.xlarge': 0.52,
            'db.r6g.2xlarge': 1.04,
            'db.r6i.large': 0.29,
            'db.r6i.xlarge': 0.58,
            'db.serverless': 0.12,
        }
        return rates.get(instance_class, 0.20)
    
    def get_metrics(self) -> List[ServiceMetrics]:
        """Retorna métricas dos clusters Aurora"""
        metrics = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            try:
                cpu = self._get_cluster_metric(cluster.db_cluster_identifier, 'CPUUtilization')
                connections = self._get_cluster_metric(cluster.db_cluster_identifier, 'DatabaseConnections')
                
                if cpu is not None:
                    metrics.append(ServiceMetrics(
                        service_name='Aurora',
                        resource_id=cluster.db_cluster_arn,
                        metric_name='CPUUtilization',
                        value=cpu,
                        unit='Percent',
                        period='last_hour',
                        metadata={
                            'cluster_name': cluster.db_cluster_identifier,
                            'engine': cluster.engine
                        }
                    ))
                
                if connections is not None:
                    metrics.append(ServiceMetrics(
                        service_name='Aurora',
                        resource_id=cluster.db_cluster_arn,
                        metric_name='DatabaseConnections',
                        value=connections,
                        unit='Count',
                        period='last_hour',
                        metadata={
                            'cluster_name': cluster.db_cluster_identifier
                        }
                    ))
                
            except Exception as e:
                logger.warning(f"Error getting metrics for cluster {cluster.db_cluster_identifier}: {e}")
        
        return metrics
    
    def _get_cluster_metric(self, cluster_id: str, metric_name: str) -> Optional[float]:
        """Obtém métrica do CloudWatch"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'DBClusterIdentifier', 'Value': cluster_id}
                ],
                StartTime=datetime.now(timezone.utc) - timedelta(hours=1),
                EndTime=datetime.now(timezone.utc),
                Period=3600,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                return datapoints[-1].get('Average')
            return None
            
        except Exception as e:
            logger.debug(f"Could not get metric {metric_name} for {cluster_id}: {e}")
            return None
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Aurora"""
        recommendations = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            if not cluster.storage_encrypted:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.db_cluster_arn,
                    resource_type='Aurora Cluster',
                    recommendation_type='SECURITY',
                    title='Habilitar criptografia de storage',
                    description=f'Cluster {cluster.db_cluster_identifier} não possui criptografia habilitada. '
                               f'Considere criar novo cluster com encryption at rest.',
                    action='Criar novo cluster com encryption habilitado e migrar dados',
                    estimated_savings=0.0,
                    priority='HIGH',
                    metadata={'cluster_name': cluster.db_cluster_identifier}
                ))
            
            if not cluster.deletion_protection:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.db_cluster_arn,
                    resource_type='Aurora Cluster',
                    recommendation_type='SECURITY',
                    title='Habilitar proteção contra deleção',
                    description=f'Cluster {cluster.db_cluster_identifier} não possui deletion protection. '
                               f'Habilite para evitar deleção acidental.',
                    action='Habilitar deletion protection no cluster',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    metadata={'cluster_name': cluster.db_cluster_identifier}
                ))
            
            if cluster.backup_retention_period < 7:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.db_cluster_arn,
                    resource_type='Aurora Cluster',
                    recommendation_type='OPERATIONAL',
                    title='Aumentar período de retenção de backups',
                    description=f'Cluster {cluster.db_cluster_identifier} tem retenção de apenas '
                               f'{cluster.backup_retention_period} dias. Considere aumentar para 7+.',
                    action='Aumentar backup retention period para pelo menos 7 dias',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    metadata={'cluster_name': cluster.db_cluster_identifier}
                ))
            
            if cluster.is_provisioned and not cluster.has_readers and cluster.instance_count == 1:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.db_cluster_arn,
                    resource_type='Aurora Cluster',
                    recommendation_type='OPERATIONAL',
                    title='Adicionar instância de leitura para HA',
                    description=f'Cluster {cluster.db_cluster_identifier} tem apenas uma instância. '
                               f'Adicione uma read replica para alta disponibilidade.',
                    action='Criar Aurora Replica em outra AZ',
                    estimated_savings=0.0,
                    priority='HIGH',
                    metadata={'cluster_name': cluster.db_cluster_identifier}
                ))
            
            if cluster.is_provisioned and cluster.instance_count >= 2:
                estimated_savings = self._estimate_serverless_savings(cluster)
                if estimated_savings > 0:
                    recommendations.append(ServiceRecommendation(
                        resource_id=cluster.db_cluster_arn,
                        resource_type='Aurora Cluster',
                        recommendation_type='COST_OPTIMIZATION',
                        title='Considerar migração para Serverless v2',
                        description=f'Cluster {cluster.db_cluster_identifier} pode se beneficiar do '
                                   f'Aurora Serverless v2 para workloads variáveis.',
                        action='Avaliar padrão de uso e migrar para Serverless v2',
                        estimated_savings=estimated_savings,
                        priority='MEDIUM',
                        metadata={
                            'cluster_name': cluster.db_cluster_identifier,
                            'current_instances': cluster.instance_count
                        }
                    ))
            
            for instance in cluster.instances:
                if instance.publicly_accessible:
                    recommendations.append(ServiceRecommendation(
                        resource_id=instance.db_instance_arn,
                        resource_type='Aurora Instance',
                        recommendation_type='SECURITY',
                        title='Remover acesso público',
                        description=f'Instância {instance.db_instance_identifier} está publicamente acessível. '
                                   f'Configure acesso apenas via VPC.',
                        action='Desabilitar publicly accessible',
                        estimated_savings=0.0,
                        priority='HIGH',
                        metadata={
                            'cluster_name': cluster.db_cluster_identifier,
                            'instance_name': instance.db_instance_identifier
                        }
                    ))
                
                if not instance.has_performance_insights and 't3' not in instance.db_instance_class:
                    recommendations.append(ServiceRecommendation(
                        resource_id=instance.db_instance_arn,
                        resource_type='Aurora Instance',
                        recommendation_type='OPERATIONAL',
                        title='Habilitar Performance Insights',
                        description=f'Instância {instance.db_instance_identifier} não tem Performance Insights. '
                                   f'Habilite para melhor observabilidade.',
                        action='Habilitar Performance Insights',
                        estimated_savings=0.0,
                        priority='LOW',
                        metadata={
                            'cluster_name': cluster.db_cluster_identifier,
                            'instance_name': instance.db_instance_identifier
                        }
                    ))
        
        logger.info(f"Generated {len(recommendations)} Aurora recommendations")
        return recommendations
    
    def _estimate_serverless_savings(self, cluster: AuroraCluster) -> float:
        """Estima economia ao migrar para Serverless v2"""
        current_cost = 0.0
        for instance in cluster.instances:
            hourly_rate = self._get_instance_hourly_rate(instance.db_instance_class)
            current_cost += hourly_rate * 24 * 30
        
        avg_acu = 4.0
        serverless_cost = avg_acu * 0.12 * 24 * 30
        
        savings = current_cost - serverless_cost
        return max(0, savings)
