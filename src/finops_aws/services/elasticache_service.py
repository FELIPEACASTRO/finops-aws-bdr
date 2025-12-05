"""
ElastiCache Service - Análise de custos e métricas do Amazon ElastiCache

FASE 2 do Roadmap FinOps AWS
Objetivo: Análise completa de Cache (Redis/Memcached)

Autor: FinOps AWS Team
Data: Novembro 2025
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
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
class ElastiCacheCluster:
    """Representa um cluster ElastiCache"""
    cluster_id: str
    engine: str
    engine_version: str
    cache_node_type: str
    num_cache_nodes: int
    status: str
    availability_zone: Optional[str] = None
    preferred_availability_zone: Optional[str] = None
    cache_subnet_group: Optional[str] = None
    security_groups: List[str] = field(default_factory=list)
    snapshot_retention_limit: int = 0
    snapshot_window: Optional[str] = None
    auth_token_enabled: bool = False
    transit_encryption_enabled: bool = False
    at_rest_encryption_enabled: bool = False
    auto_minor_version_upgrade: bool = True


@dataclass
class ElastiCacheReplicationGroup:
    """Representa um grupo de replicação ElastiCache (Redis)"""
    replication_group_id: str
    description: str
    status: str
    engine: str = "redis"
    cache_node_type: Optional[str] = None
    num_node_groups: int = 1
    replicas_per_node_group: int = 0
    automatic_failover: str = "disabled"
    multi_az: str = "disabled"
    cluster_mode: str = "disabled"
    snapshot_retention_limit: int = 0
    auth_token_enabled: bool = False
    transit_encryption_enabled: bool = False
    at_rest_encryption_enabled: bool = False


class ElastiCacheService(BaseAWSService):
    """
    Serviço para análise completa do Amazon ElastiCache
    
    Coleta custos, métricas de uso e recomendações de otimização
    para clusters Redis e Memcached.
    
    Suporta injeção de dependências para Clean Architecture.
    """
    
    SERVICE_NAME = "Amazon ElastiCache"
    SERVICE_FILTER = "Amazon ElastiCache"
    
    def __init__(
        self,
        elasticache_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o ElastiCacheService
        
        Args:
            elasticache_client: Cliente ElastiCache injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        super().__init__(cost_client=cost_client, cloudwatch_client=cloudwatch_client)
        self._elasticache_client = elasticache_client
    
    @property
    def elasticache_client(self):
        """Lazy loading do cliente ElastiCache"""
        if self._elasticache_client is None:
            self._elasticache_client = boto3.client('elasticache', region_name=self.region)
        return self._elasticache_client
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.elasticache_client.describe_cache_clusters(MaxRecords=20)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os clusters ElastiCache"""
        clusters = self.get_clusters()
        replication_groups = self.get_replication_groups()
        
        resources = []
        for c in clusters:
            resources.append({
                'cluster_id': c.cluster_id,
                'type': 'cluster',
                'engine': c.engine,
                'node_type': c.cache_node_type,
                'num_nodes': c.num_cache_nodes
            })
        
        for rg in replication_groups:
            resources.append({
                'cluster_id': rg.replication_group_id,
                'type': 'replication_group',
                'engine': rg.engine,
                'node_type': rg.cache_node_type,
                'num_node_groups': rg.num_node_groups
            })
        
        return resources
    
    def get_clusters(self) -> List[ElastiCacheCluster]:
        """
        Obtém lista de clusters ElastiCache (Memcached e Redis standalone)
        
        Returns:
            Lista de ElastiCacheCluster
        """
        try:
            clusters = []
            marker = None
            
            while True:
                params = {'MaxRecords': 100, 'ShowCacheNodeInfo': True}
                if marker:
                    params['Marker'] = marker
                
                response = self.elasticache_client.describe_cache_clusters(**params)
                
                for cluster_data in response.get('CacheClusters', []):
                    security_groups = [
                        sg['SecurityGroupId'] 
                        for sg in cluster_data.get('SecurityGroups', [])
                    ]
                    
                    cluster = ElastiCacheCluster(
                        cluster_id=cluster_data['CacheClusterId'],
                        engine=cluster_data['Engine'],
                        engine_version=cluster_data.get('EngineVersion', ''),
                        cache_node_type=cluster_data['CacheNodeType'],
                        num_cache_nodes=cluster_data.get('NumCacheNodes', 1),
                        status=cluster_data['CacheClusterStatus'],
                        availability_zone=cluster_data.get('PreferredAvailabilityZone'),
                        cache_subnet_group=cluster_data.get('CacheSubnetGroupName'),
                        security_groups=security_groups,
                        snapshot_retention_limit=cluster_data.get('SnapshotRetentionLimit', 0),
                        snapshot_window=cluster_data.get('SnapshotWindow'),
                        auth_token_enabled=cluster_data.get('AuthTokenEnabled', False),
                        transit_encryption_enabled=cluster_data.get('TransitEncryptionEnabled', False),
                        at_rest_encryption_enabled=cluster_data.get('AtRestEncryptionEnabled', False),
                        auto_minor_version_upgrade=cluster_data.get('AutoMinorVersionUpgrade', True)
                    )
                    clusters.append(cluster)
                
                marker = response.get('Marker')
                if not marker:
                    break
            
            logger.info(f"Found {len(clusters)} ElastiCache clusters")
            return clusters
            
        except ClientError as e:
            handle_aws_error(e, "get_elasticache_clusters")
            return []
    
    def get_replication_groups(self) -> List[ElastiCacheReplicationGroup]:
        """
        Obtém lista de grupos de replicação Redis
        
        Returns:
            Lista de ElastiCacheReplicationGroup
        """
        try:
            groups = []
            marker = None
            
            while True:
                params = {'MaxRecords': 100}
                if marker:
                    params['Marker'] = marker
                
                response = self.elasticache_client.describe_replication_groups(**params)
                
                for rg_data in response.get('ReplicationGroups', []):
                    node_groups = rg_data.get('NodeGroups', [])
                    cache_node_type = None
                    if node_groups:
                        members = node_groups[0].get('NodeGroupMembers', [])
                        if members:
                            cache_node_type = members[0].get('CacheNodeId', '').split('-')[0] if members else None
                    
                    if not cache_node_type:
                        cache_node_type = rg_data.get('CacheNodeType')
                    
                    group = ElastiCacheReplicationGroup(
                        replication_group_id=rg_data['ReplicationGroupId'],
                        description=rg_data.get('Description', ''),
                        status=rg_data['Status'],
                        cache_node_type=cache_node_type,
                        num_node_groups=len(node_groups),
                        replicas_per_node_group=len(node_groups[0].get('NodeGroupMembers', [])) - 1 if node_groups else 0,
                        automatic_failover=rg_data.get('AutomaticFailover', 'disabled'),
                        multi_az=rg_data.get('MultiAZ', 'disabled'),
                        cluster_mode='enabled' if rg_data.get('ClusterEnabled', False) else 'disabled',
                        snapshot_retention_limit=rg_data.get('SnapshotRetentionLimit', 0),
                        auth_token_enabled=rg_data.get('AuthTokenEnabled', False),
                        transit_encryption_enabled=rg_data.get('TransitEncryptionEnabled', False),
                        at_rest_encryption_enabled=rg_data.get('AtRestEncryptionEnabled', False)
                    )
                    groups.append(group)
                
                marker = response.get('Marker')
                if not marker:
                    break
            
            logger.info(f"Found {len(groups)} ElastiCache replication groups")
            return groups
            
        except ClientError as e:
            handle_aws_error(e, "get_elasticache_replication_groups")
            return []
    
    def get_cluster_metrics(self, cluster_id: str, cache_node_id: str = '0001') -> Dict[str, Any]:
        """
        Obtém métricas de um cluster específico
        
        Args:
            cluster_id: ID do cluster
            cache_node_id: ID do nó (default: 0001)
            
        Returns:
            Dicionário com métricas
        """
        dimensions = [
            {'Name': 'CacheClusterId', 'Value': cluster_id},
            {'Name': 'CacheNodeId', 'Value': cache_node_id}
        ]
        
        metrics = {
            'cpu_utilization': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'CPUUtilization', dimensions
            ),
            'engine_cpu_utilization': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'EngineCPUUtilization', dimensions
            ),
            'database_memory_usage': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'DatabaseMemoryUsagePercentage', dimensions
            ),
            'swap_usage': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'SwapUsage', dimensions
            ),
            'network_bytes_in': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'NetworkBytesIn', dimensions
            ),
            'network_bytes_out': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'NetworkBytesOut', dimensions
            ),
            'cache_hits': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'CacheHits', dimensions
            ),
            'cache_misses': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'CacheMisses', dimensions
            ),
            'curr_connections': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'CurrConnections', dimensions
            ),
            'evictions': self.get_cloudwatch_metric(
                'AWS/ElastiCache', 'Evictions', dimensions
            )
        }
        
        return metrics
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do ElastiCache"""
        clusters = self.get_clusters()
        replication_groups = self.get_replication_groups()
        
        redis_clusters = [c for c in clusters if c.engine == 'redis']
        memcached_clusters = [c for c in clusters if c.engine == 'memcached']
        
        total_nodes = sum(c.num_cache_nodes for c in clusters)
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(clusters) + len(replication_groups),
            metrics={
                'cluster_count': len(clusters),
                'replication_group_count': len(replication_groups),
                'redis_clusters': len(redis_clusters),
                'memcached_clusters': len(memcached_clusters),
                'total_nodes': total_nodes,
                'with_encryption_at_rest': sum(1 for c in clusters if c.at_rest_encryption_enabled),
                'with_encryption_in_transit': sum(1 for c in clusters if c.transit_encryption_enabled),
                'with_auth_token': sum(1 for c in clusters if c.auth_token_enabled),
                'with_automatic_failover': sum(1 for rg in replication_groups if rg.automatic_failover == 'enabled'),
                'with_multi_az': sum(1 for rg in replication_groups if rg.multi_az == 'enabled')
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para ElastiCache"""
        recommendations = []
        clusters = self.get_clusters()
        replication_groups = self.get_replication_groups()
        
        for cluster in clusters:
            metrics = self.get_cluster_metrics(cluster.cluster_id)
            cpu_util = metrics.get('cpu_utilization', {}).get('average', 0)
            memory_usage = metrics.get('database_memory_usage', {}).get('average', 0)
            
            if cpu_util < 10 and memory_usage < 20:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_id,
                    resource_type='ElastiCacheCluster',
                    recommendation_type='RIGHTSIZE_DOWN',
                    description=f'Cluster {cluster.cluster_id} tem baixa utilização de CPU ({cpu_util:.1f}%) '
                               f'e memória ({memory_usage:.1f}%). Considere reduzir o node type.',
                    estimated_savings=self._estimate_node_savings(cluster.cache_node_type),
                    priority='MEDIUM',
                    implementation_effort='MEDIUM',
                    details={
                        'current_node_type': cluster.cache_node_type,
                        'cpu_utilization': cpu_util,
                        'memory_usage': memory_usage,
                        'suggestion': 'Reduzir para node type menor'
                    }
                ))
            
            if not cluster.at_rest_encryption_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_id,
                    resource_type='ElastiCacheCluster',
                    recommendation_type='SECURITY',
                    description=f'Cluster {cluster.cluster_id} não tem criptografia em repouso. '
                               'Considere recriar com criptografia para compliance.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    implementation_effort='HIGH',
                    details={
                        'at_rest_encryption': False,
                        'note': 'Criptografia não pode ser habilitada após criação'
                    }
                ))
            
            evictions = metrics.get('evictions', {}).get('average', 0)
            if evictions > 100:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_id,
                    resource_type='ElastiCacheCluster',
                    recommendation_type='INCREASE_CAPACITY',
                    description=f'Cluster {cluster.cluster_id} está tendo evictions frequentes ({evictions:.0f}/período). '
                               'Considere aumentar a capacidade.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    implementation_effort='MEDIUM',
                    details={
                        'evictions': evictions,
                        'suggestion': 'Aumentar node type ou adicionar nós'
                    }
                ))
            
            cache_hits = metrics.get('cache_hits', {}).get('average', 0)
            cache_misses = metrics.get('cache_misses', {}).get('average', 0)
            total_requests = cache_hits + cache_misses
            
            if total_requests > 0:
                hit_rate = cache_hits / total_requests * 100
                if hit_rate < 80:
                    recommendations.append(ServiceRecommendation(
                        resource_id=cluster.cluster_id,
                        resource_type='ElastiCacheCluster',
                        recommendation_type='OPTIMIZE_CACHE',
                        description=f'Cluster {cluster.cluster_id} tem hit rate baixo ({hit_rate:.1f}%). '
                                   'Revise a estratégia de caching.',
                        estimated_savings=0.0,
                        priority='MEDIUM',
                        implementation_effort='MEDIUM',
                        details={
                            'hit_rate': hit_rate,
                            'cache_hits': cache_hits,
                            'cache_misses': cache_misses
                        }
                    ))
        
        for rg in replication_groups:
            if rg.automatic_failover == 'disabled' and rg.num_node_groups > 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=rg.replication_group_id,
                    resource_type='ElastiCacheReplicationGroup',
                    recommendation_type='ENABLE_FAILOVER',
                    description=f'Replication group {rg.replication_group_id} não tem failover automático. '
                               'Considere habilitar para alta disponibilidade.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    implementation_effort='LOW',
                    details={
                        'automatic_failover': 'disabled',
                        'multi_az': rg.multi_az
                    }
                ))
            
            if rg.snapshot_retention_limit == 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=rg.replication_group_id,
                    resource_type='ElastiCacheReplicationGroup',
                    recommendation_type='ENABLE_BACKUPS',
                    description=f'Replication group {rg.replication_group_id} não tem backups automáticos. '
                               'Considere habilitar para recuperação de desastres.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    implementation_effort='LOW',
                    details={
                        'snapshot_retention_limit': 0
                    }
                ))
        
        logger.info(f"Generated {len(recommendations)} ElastiCache recommendations")
        return recommendations
    
    def _estimate_node_savings(self, node_type: str) -> float:
        """Estima economia ao reduzir node type"""
        node_costs = {
            'cache.t3.micro': 12.0,
            'cache.t3.small': 24.0,
            'cache.t3.medium': 48.0,
            'cache.m5.large': 120.0,
            'cache.m5.xlarge': 240.0,
            'cache.m5.2xlarge': 480.0,
            'cache.r5.large': 150.0,
            'cache.r5.xlarge': 300.0,
            'cache.r5.2xlarge': 600.0
        }
        
        current_cost = node_costs.get(node_type, 100.0)
        return current_cost * 0.5
