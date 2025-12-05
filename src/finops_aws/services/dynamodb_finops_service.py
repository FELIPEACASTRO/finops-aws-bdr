"""
DynamoDB FinOps Service - Análise de custos e métricas do Amazon DynamoDB

FASE 2 do Roadmap FinOps AWS
Objetivo: Análise completa de NoSQL

Autor: FinOps AWS Team
Data: Novembro 2025

Nota: Arquivo nomeado dynamodb_finops_service.py para evitar conflito
com dynamodb_state_manager.py do core.
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
class DynamoDBTable:
    """Representa uma tabela DynamoDB"""
    table_name: str
    table_status: str
    item_count: int = 0
    table_size_bytes: int = 0
    billing_mode: str = "PROVISIONED"
    read_capacity: int = 0
    write_capacity: int = 0
    gsi_count: int = 0
    lsi_count: int = 0
    stream_enabled: bool = False
    ttl_enabled: bool = False
    point_in_time_recovery: bool = False
    encryption_type: str = "DEFAULT"
    table_class: str = "STANDARD"


class DynamoDBFinOpsService(BaseAWSService):
    """
    Serviço para análise completa do Amazon DynamoDB
    
    Coleta custos, métricas de uso e recomendações de otimização
    para tabelas DynamoDB.
    
    Suporta injeção de dependências para Clean Architecture.
    """
    
    SERVICE_NAME = "Amazon DynamoDB"
    SERVICE_FILTER = "Amazon DynamoDB"
    
    def __init__(
        self,
        dynamodb_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o DynamoDBFinOpsService
        
        Args:
            dynamodb_client: Cliente DynamoDB injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        super().__init__(cost_client=cost_client, cloudwatch_client=cloudwatch_client)
        self._dynamodb_client = dynamodb_client
    
    @property
    def dynamodb_client(self):
        """Lazy loading do cliente DynamoDB"""
        if self._dynamodb_client is None:
            self._dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        return self._dynamodb_client
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.dynamodb_client.list_tables(Limit=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista todas as tabelas DynamoDB"""
        tables = self.get_tables()
        return [
            {
                'table_name': t.table_name,
                'status': t.table_status,
                'item_count': t.item_count,
                'size_bytes': t.table_size_bytes,
                'billing_mode': t.billing_mode
            }
            for t in tables
        ]
    
    def get_tables(self) -> List[DynamoDBTable]:
        """
        Obtém lista de todas as tabelas DynamoDB com detalhes
        
        Returns:
            Lista de DynamoDBTable
        """
        try:
            tables = []
            
            table_names = []
            paginator = self.dynamodb_client.get_paginator('list_tables')
            for page in paginator.paginate():
                table_names.extend(page.get('TableNames', []))
            
            for table_name in table_names:
                try:
                    response = self.dynamodb_client.describe_table(TableName=table_name)
                    table_data = response['Table']
                    
                    provisioned = table_data.get('ProvisionedThroughput', {})
                    billing_mode = table_data.get('BillingModeSummary', {}).get(
                        'BillingMode', 'PROVISIONED'
                    )
                    
                    sse = table_data.get('SSEDescription', {})
                    encryption_type = sse.get('SSEType', 'DEFAULT') if sse.get('Status') == 'ENABLED' else 'DEFAULT'
                    
                    table = DynamoDBTable(
                        table_name=table_name,
                        table_status=table_data['TableStatus'],
                        item_count=table_data.get('ItemCount', 0),
                        table_size_bytes=table_data.get('TableSizeBytes', 0),
                        billing_mode=billing_mode,
                        read_capacity=provisioned.get('ReadCapacityUnits', 0),
                        write_capacity=provisioned.get('WriteCapacityUnits', 0),
                        gsi_count=len(table_data.get('GlobalSecondaryIndexes', [])),
                        lsi_count=len(table_data.get('LocalSecondaryIndexes', [])),
                        stream_enabled=table_data.get('StreamSpecification', {}).get('StreamEnabled', False),
                        encryption_type=encryption_type,
                        table_class=table_data.get('TableClassSummary', {}).get('TableClass', 'STANDARD')
                    )
                    
                    try:
                        ttl_response = self.dynamodb_client.describe_time_to_live(TableName=table_name)
                        table.ttl_enabled = ttl_response.get('TimeToLiveDescription', {}).get(
                            'TimeToLiveStatus') == 'ENABLED'
                    except ClientError:
                        pass
                    
                    try:
                        pitr_response = self.dynamodb_client.describe_continuous_backups(TableName=table_name)
                        table.point_in_time_recovery = pitr_response.get(
                            'ContinuousBackupsDescription', {}
                        ).get('PointInTimeRecoveryDescription', {}).get(
                            'PointInTimeRecoveryStatus') == 'ENABLED'
                    except ClientError:
                        pass
                    
                    tables.append(table)
                    
                except ClientError as e:
                    logger.warning(f"Failed to describe table {table_name}: {e}")
            
            logger.info(f"Found {len(tables)} DynamoDB tables")
            return tables
            
        except ClientError as e:
            handle_aws_error(e, "get_dynamodb_tables")
            return []
    
    def get_table_metrics(self, table_name: str) -> Dict[str, Any]:
        """
        Obtém métricas de uma tabela específica
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dicionário com métricas da tabela
        """
        dimensions = [{'Name': 'TableName', 'Value': table_name}]
        
        metrics = {
            'consumed_read_capacity': self.get_cloudwatch_metric(
                'AWS/DynamoDB', 'ConsumedReadCapacityUnits', dimensions
            ),
            'consumed_write_capacity': self.get_cloudwatch_metric(
                'AWS/DynamoDB', 'ConsumedWriteCapacityUnits', dimensions
            ),
            'read_throttle_events': self.get_cloudwatch_metric(
                'AWS/DynamoDB', 'ReadThrottledRequests', dimensions
            ),
            'write_throttle_events': self.get_cloudwatch_metric(
                'AWS/DynamoDB', 'WriteThrottledRequests', dimensions
            ),
            'successful_requests': self.get_cloudwatch_metric(
                'AWS/DynamoDB', 'SuccessfulRequestLatency', dimensions
            ),
            'system_errors': self.get_cloudwatch_metric(
                'AWS/DynamoDB', 'SystemErrors', dimensions
            )
        }
        
        return metrics
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do DynamoDB"""
        tables = self.get_tables()
        
        total_items = sum(t.item_count for t in tables)
        total_size = sum(t.table_size_bytes for t in tables)
        
        provisioned_count = sum(1 for t in tables if t.billing_mode == 'PROVISIONED')
        on_demand_count = sum(1 for t in tables if t.billing_mode == 'PAY_PER_REQUEST')
        
        total_rcu = sum(t.read_capacity for t in tables)
        total_wcu = sum(t.write_capacity for t in tables)
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(tables),
            metrics={
                'total_items': total_items,
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024 ** 3),
                'provisioned_tables': provisioned_count,
                'on_demand_tables': on_demand_count,
                'total_rcu': total_rcu,
                'total_wcu': total_wcu,
                'tables_with_gsi': sum(1 for t in tables if t.gsi_count > 0),
                'tables_with_streams': sum(1 for t in tables if t.stream_enabled),
                'tables_with_pitr': sum(1 for t in tables if t.point_in_time_recovery),
                'tables_with_ttl': sum(1 for t in tables if t.ttl_enabled)
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para DynamoDB"""
        recommendations = []
        tables = self.get_tables()
        
        for table in tables:
            if table.billing_mode == 'PROVISIONED':
                table_metrics = self.get_table_metrics(table.table_name)
                
                consumed_rcu = table_metrics.get('consumed_read_capacity', {}).get('average', 0)
                consumed_wcu = table_metrics.get('consumed_write_capacity', {}).get('average', 0)
                
                if table.read_capacity > 0:
                    rcu_utilization = (consumed_rcu / table.read_capacity) * 100
                else:
                    rcu_utilization = 0
                
                if table.write_capacity > 0:
                    wcu_utilization = (consumed_wcu / table.write_capacity) * 100
                else:
                    wcu_utilization = 0
                
                if rcu_utilization < 20 and wcu_utilization < 20:
                    recommendations.append(ServiceRecommendation(
                        resource_id=table.table_name,
                        resource_type='DynamoDBTable',
                        recommendation_type='SWITCH_TO_ON_DEMAND',
                        description=f'Tabela {table.table_name} tem baixa utilização de capacidade. '
                                   'Considere migrar para modo On-Demand.',
                        estimated_savings=self._estimate_on_demand_savings(table),
                        priority='MEDIUM',
                        implementation_effort='LOW',
                        details={
                            'current_mode': 'PROVISIONED',
                            'rcu_utilization': rcu_utilization,
                            'wcu_utilization': wcu_utilization,
                            'provisioned_rcu': table.read_capacity,
                            'provisioned_wcu': table.write_capacity
                        }
                    ))
                
                throttle_read = table_metrics.get('read_throttle_events', {}).get('average', 0)
                throttle_write = table_metrics.get('write_throttle_events', {}).get('average', 0)
                
                if throttle_read > 0 or throttle_write > 0:
                    recommendations.append(ServiceRecommendation(
                        resource_id=table.table_name,
                        resource_type='DynamoDBTable',
                        recommendation_type='INCREASE_CAPACITY',
                        description=f'Tabela {table.table_name} está sofrendo throttling. '
                                   'Considere aumentar capacidade ou habilitar auto-scaling.',
                        estimated_savings=0.0,
                        priority='HIGH',
                        implementation_effort='LOW',
                        details={
                            'read_throttle_events': throttle_read,
                            'write_throttle_events': throttle_write,
                            'suggestion': 'Habilitar DynamoDB Auto Scaling'
                        }
                    ))
            
            if not table.ttl_enabled and table.item_count > 100000:
                recommendations.append(ServiceRecommendation(
                    resource_id=table.table_name,
                    resource_type='DynamoDBTable',
                    recommendation_type='ENABLE_TTL',
                    description=f'Tabela {table.table_name} tem {table.item_count:,} itens '
                               'sem TTL habilitado. Considere usar TTL para dados temporários.',
                    estimated_savings=0.0,
                    priority='LOW',
                    implementation_effort='LOW',
                    details={
                        'item_count': table.item_count,
                        'table_size_gb': table.table_size_bytes / (1024 ** 3)
                    }
                ))
            
            if not table.point_in_time_recovery:
                recommendations.append(ServiceRecommendation(
                    resource_id=table.table_name,
                    resource_type='DynamoDBTable',
                    recommendation_type='ENABLE_PITR',
                    description=f'Tabela {table.table_name} não tem Point-in-Time Recovery. '
                               'Considere habilitar para proteção contra perda de dados.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    implementation_effort='LOW',
                    details={
                        'table_name': table.table_name,
                        'current_status': 'DISABLED',
                        'cost_impact': 'Pequeno custo adicional por GB armazenado'
                    }
                ))
            
            if table.table_class == 'STANDARD' and table.item_count > 0:
                access_frequency = self._estimate_access_frequency(table)
                if access_frequency == 'INFREQUENT':
                    size_gb = table.table_size_bytes / (1024 ** 3)
                    estimated_savings = size_gb * 0.25 * 0.60
                    
                    recommendations.append(ServiceRecommendation(
                        resource_id=table.table_name,
                        resource_type='DynamoDBTable',
                        recommendation_type='CHANGE_TABLE_CLASS',
                        description=f'Tabela {table.table_name} pode se beneficiar da classe '
                                   'Standard-IA para dados acessados com pouca frequência.',
                        estimated_savings=estimated_savings,
                        priority='MEDIUM',
                        implementation_effort='LOW',
                        details={
                            'current_class': 'STANDARD',
                            'recommended_class': 'STANDARD_INFREQUENT_ACCESS',
                            'table_size_gb': size_gb
                        }
                    ))
        
        logger.info(f"Generated {len(recommendations)} DynamoDB recommendations")
        return recommendations
    
    def _estimate_on_demand_savings(self, table: DynamoDBTable) -> float:
        """Estima economia ao migrar para On-Demand"""
        rcu_cost_provisioned = table.read_capacity * 0.00013 * 24 * 30
        wcu_cost_provisioned = table.write_capacity * 0.00065 * 24 * 30
        current_cost = rcu_cost_provisioned + wcu_cost_provisioned
        
        estimated_on_demand = current_cost * 0.3
        
        return max(0, current_cost - estimated_on_demand)
    
    def _estimate_access_frequency(self, table: DynamoDBTable) -> str:
        """Estima frequência de acesso baseado em métricas"""
        metrics = self.get_table_metrics(table.table_name)
        
        consumed_rcu = metrics.get('consumed_read_capacity', {}).get('average', 0)
        consumed_wcu = metrics.get('consumed_write_capacity', {}).get('average', 0)
        
        total_ops = consumed_rcu + consumed_wcu
        
        if table.item_count == 0:
            return 'UNKNOWN'
        
        ops_per_item = total_ops / table.item_count
        
        if ops_per_item < 0.01:
            return 'INFREQUENT'
        elif ops_per_item < 0.1:
            return 'MODERATE'
        else:
            return 'FREQUENT'
    
    def get_capacity_analysis(self) -> Dict[str, Any]:
        """
        Analisa capacidade provisionada vs consumida
        
        Returns:
            Análise de capacidade
        """
        tables = self.get_tables()
        analysis = {
            'tables_analyzed': 0,
            'over_provisioned': [],
            'under_provisioned': [],
            'optimal': [],
            'total_wasted_capacity_cost': 0.0
        }
        
        for table in tables:
            if table.billing_mode != 'PROVISIONED':
                continue
            
            analysis['tables_analyzed'] += 1
            metrics = self.get_table_metrics(table.table_name)
            
            consumed_rcu = metrics.get('consumed_read_capacity', {}).get('average', 0)
            consumed_wcu = metrics.get('consumed_write_capacity', {}).get('average', 0)
            
            rcu_util = (consumed_rcu / table.read_capacity * 100) if table.read_capacity > 0 else 0
            wcu_util = (consumed_wcu / table.write_capacity * 100) if table.write_capacity > 0 else 0
            
            avg_util = (rcu_util + wcu_util) / 2
            
            table_info = {
                'table_name': table.table_name,
                'rcu_utilization': rcu_util,
                'wcu_utilization': wcu_util,
                'provisioned_rcu': table.read_capacity,
                'provisioned_wcu': table.write_capacity
            }
            
            if avg_util < 30:
                analysis['over_provisioned'].append(table_info)
                wasted_rcu = (table.read_capacity - consumed_rcu) * 0.00013 * 24 * 30
                wasted_wcu = (table.write_capacity - consumed_wcu) * 0.00065 * 24 * 30
                analysis['total_wasted_capacity_cost'] += wasted_rcu + wasted_wcu
            elif avg_util > 80:
                analysis['under_provisioned'].append(table_info)
            else:
                analysis['optimal'].append(table_info)
        
        return analysis
