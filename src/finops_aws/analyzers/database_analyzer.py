"""
Database Analyzer - Análise de serviços de banco de dados AWS

Serviços cobertos:
- RDS (MySQL, PostgreSQL, Oracle, SQL Server)
- Aurora
- DynamoDB
- ElastiCache
- Redshift
- DocumentDB
- Neptune

Design Pattern: Strategy
"""
from typing import Dict, List, Any
from datetime import datetime
import logging

from .base_analyzer import (
    BaseAnalyzer,
    Recommendation,
    Priority,
    Impact
)

logger = logging.getLogger(__name__)


class DatabaseAnalyzer(BaseAnalyzer):
    """Analyzer para serviços de banco de dados AWS."""
    
    name = "DatabaseAnalyzer"
    
    def _get_client(self, region: str) -> Any:
        """Retorna clientes boto3 para bancos de dados."""
        import boto3
        return {
            'rds': boto3.client('rds', region_name=region),
            'dynamodb': boto3.client('dynamodb', region_name=region),
            'elasticache': boto3.client('elasticache', region_name=region),
        }
    
    def _collect_resources(self, clients: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta recursos de banco de dados."""
        resources = {}
        
        rds = clients.get('rds')
        if rds:
            try:
                resources['rds_instances'] = rds.describe_db_instances()
                resources['rds_clusters'] = rds.describe_db_clusters()
                resources['rds_snapshots'] = rds.describe_db_snapshots(SnapshotType='manual')
            except Exception as e:
                logger.warning(f"Erro coletando RDS: {e}")
        
        dynamodb = clients.get('dynamodb')
        if dynamodb:
            try:
                resources['dynamodb_tables'] = dynamodb.list_tables()
                resources['dynamodb_client'] = dynamodb
            except Exception as e:
                logger.warning(f"Erro coletando DynamoDB: {e}")
        
        elasticache = clients.get('elasticache')
        if elasticache:
            try:
                resources['elasticache_clusters'] = elasticache.describe_cache_clusters()
            except Exception as e:
                logger.warning(f"Erro coletando ElastiCache: {e}")
        
        return resources
    
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """Analisa recursos e gera recomendações."""
        recommendations = []
        metrics = {}
        
        recommendations.extend(self._analyze_rds(resources, metrics))
        recommendations.extend(self._analyze_dynamodb(resources, metrics))
        recommendations.extend(self._analyze_elasticache(resources, metrics))
        
        return recommendations, metrics
    
    def _analyze_rds(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa instâncias RDS."""
        recommendations = []
        
        instances_data = resources.get('rds_instances', {})
        instances = instances_data.get('DBInstances', [])
        metrics['rds_instances'] = len(instances)
        
        for db in instances:
            db_id = db.get('DBInstanceIdentifier', '')
            db_class = db.get('DBInstanceClass', '')
            
            if not db.get('StorageEncrypted', False):
                recommendations.append(self._create_recommendation(
                    rec_type='RDS_ENCRYPTION',
                    resource_id=db_id,
                    description=f'RDS {db_id} sem criptografia habilitada',
                    service='RDS Security',
                    priority=Priority.HIGH
                ))
            
            if db.get('BackupRetentionPeriod', 0) < 7:
                recommendations.append(self._create_recommendation(
                    rec_type='RDS_BACKUP',
                    resource_id=db_id,
                    description=f'RDS {db_id} com retenção de backup < 7 dias',
                    service='RDS Analysis',
                    priority=Priority.MEDIUM
                ))
            
            if db_class.startswith('db.m3.') or db_class.startswith('db.m4.'):
                recommendations.append(self._create_recommendation(
                    rec_type='RDS_OLD_GENERATION',
                    resource_id=db_id,
                    description=f'RDS {db_id} usa instância antiga ({db_class})',
                    service='RDS Optimization',
                    priority=Priority.LOW,
                    savings=20.0
                ))
        
        clusters_data = resources.get('rds_clusters', {})
        metrics['rds_clusters'] = len(clusters_data.get('DBClusters', []))
        
        snapshots_data = resources.get('rds_snapshots', {})
        metrics['rds_snapshots'] = len(snapshots_data.get('DBSnapshots', []))
        
        return recommendations
    
    def _analyze_dynamodb(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa tabelas DynamoDB."""
        recommendations = []
        tables_data = resources.get('dynamodb_tables', {})
        dynamodb = resources.get('dynamodb_client')
        
        tables = tables_data.get('TableNames', [])
        metrics['dynamodb_tables'] = len(tables)
        
        if not dynamodb:
            return recommendations
        
        for table_name in tables[:10]:
            try:
                table_desc = dynamodb.describe_table(TableName=table_name)
                table = table_desc.get('Table', {})
                
                billing_mode = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
                
                if billing_mode == 'PROVISIONED':
                    read_capacity = table.get('ProvisionedThroughput', {}).get('ReadCapacityUnits', 0)
                    write_capacity = table.get('ProvisionedThroughput', {}).get('WriteCapacityUnits', 0)
                    
                    if read_capacity > 100 or write_capacity > 100:
                        recommendations.append(self._create_recommendation(
                            rec_type='DYNAMODB_CAPACITY',
                            resource_id=table_name,
                            description=f'DynamoDB {table_name} com capacidade provisionada alta - considere on-demand',
                            service='DynamoDB Optimization',
                            priority=Priority.MEDIUM
                        ))
            except Exception:
                pass
        
        return recommendations
    
    def _analyze_elasticache(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa clusters ElastiCache."""
        recommendations = []
        clusters_data = resources.get('elasticache_clusters', {})
        
        clusters = clusters_data.get('CacheClusters', [])
        metrics['elasticache_clusters'] = len(clusters)
        
        for cluster in clusters:
            cluster_id = cluster.get('CacheClusterId', '')
            node_type = cluster.get('CacheNodeType', '')
            
            if 'cache.t2.' in node_type or 'cache.m3.' in node_type:
                recommendations.append(self._create_recommendation(
                    rec_type='ELASTICACHE_OLD_GENERATION',
                    resource_id=cluster_id,
                    description=f'ElastiCache {cluster_id} usa tipo antigo ({node_type})',
                    service='ElastiCache Optimization',
                    priority=Priority.LOW,
                    savings=15.0
                ))
        
        return recommendations
    
    def _get_services_list(self) -> List[str]:
        """Retorna serviços analisados."""
        return ['RDS', 'Aurora', 'DynamoDB', 'ElastiCache']
