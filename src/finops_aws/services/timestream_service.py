"""
Timestream FinOps Service - Análise de Custos do Amazon Timestream

FASE 2.5 - Serviços de Alto Custo de Banco de Dados
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de databases e tables Timestream
- Análise de time series database
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
class TimestreamDatabase:
    """Representa um database Timestream"""
    database_name: str
    arn: str
    table_count: int = 0
    kms_key_id: Optional[str] = None
    creation_time: Optional[datetime] = None
    last_updated_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_encrypted(self) -> bool:
        return self.kms_key_id is not None
    
    @property
    def has_tables(self) -> bool:
        return self.table_count > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'database_name': self.database_name,
            'arn': self.arn,
            'table_count': self.table_count,
            'kms_key_id': self.kms_key_id,
            'is_encrypted': self.is_encrypted,
            'has_tables': self.has_tables,
            'tags': self.tags,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'last_updated_time': self.last_updated_time.isoformat() if self.last_updated_time else None
        }


@dataclass
class TimestreamTable:
    """Representa uma table Timestream"""
    table_name: str
    database_name: str
    arn: str
    table_status: str
    memory_store_retention_period_in_hours: int = 24
    magnetic_store_retention_period_in_days: int = 365
    magnetic_store_write_properties: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None
    creation_time: Optional[datetime] = None
    last_updated_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        return self.table_status == 'ACTIVE'
    
    @property
    def memory_retention_hours(self) -> int:
        return self.memory_store_retention_period_in_hours
    
    @property
    def magnetic_retention_days(self) -> int:
        return self.magnetic_store_retention_period_in_days
    
    @property
    def has_magnetic_writes(self) -> bool:
        if self.magnetic_store_write_properties:
            return self.magnetic_store_write_properties.get('EnableMagneticStoreWrites', False)
        return False
    
    @property
    def total_retention_days(self) -> int:
        memory_days = self.memory_store_retention_period_in_hours / 24
        return int(memory_days + self.magnetic_store_retention_period_in_days)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'table_name': self.table_name,
            'database_name': self.database_name,
            'arn': self.arn,
            'table_status': self.table_status,
            'is_active': self.is_active,
            'memory_store_retention_period_in_hours': self.memory_store_retention_period_in_hours,
            'magnetic_store_retention_period_in_days': self.magnetic_store_retention_period_in_days,
            'has_magnetic_writes': self.has_magnetic_writes,
            'total_retention_days': self.total_retention_days,
            'schema': self.schema,
            'tags': self.tags,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'last_updated_time': self.last_updated_time.isoformat() if self.last_updated_time else None
        }


@dataclass
class TimestreamScheduledQuery:
    """Representa uma scheduled query Timestream"""
    name: str
    arn: str
    state: str
    query_string: str
    schedule_expression: str
    target_database: str
    target_table: str
    error_report_s3_bucket: Optional[str] = None
    creation_time: Optional[datetime] = None
    last_run_status: Optional[str] = None
    next_invocation_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_enabled(self) -> bool:
        return self.state == 'ENABLED'
    
    @property
    def is_disabled(self) -> bool:
        return self.state == 'DISABLED'
    
    @property
    def has_error_reporting(self) -> bool:
        return self.error_report_s3_bucket is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'state': self.state,
            'is_enabled': self.is_enabled,
            'query_string': self.query_string[:200] + '...' if len(self.query_string) > 200 else self.query_string,
            'schedule_expression': self.schedule_expression,
            'target_database': self.target_database,
            'target_table': self.target_table,
            'has_error_reporting': self.has_error_reporting,
            'last_run_status': self.last_run_status,
            'tags': self.tags,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'next_invocation_time': self.next_invocation_time.isoformat() if self.next_invocation_time else None
        }


class TimestreamService(BaseAWSService):
    """
    Serviço FinOps para Amazon Timestream
    
    Analisa databases e tables Timestream (time series database)
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._timestream_write_client = None
        self._timestream_query_client = None
        self._cloudwatch_client = None
    
    @property
    def timestream_write_client(self):
        if self._timestream_write_client is None:
            self._timestream_write_client = self.client_factory.get_client('timestream-write')
        return self._timestream_write_client
    
    @property
    def timestream_query_client(self):
        if self._timestream_query_client is None:
            self._timestream_query_client = self.client_factory.get_client('timestream-query')
        return self._timestream_query_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            self._cloudwatch_client = self.client_factory.get_client('cloudwatch')
        return self._cloudwatch_client
    
    @property
    def service_name(self) -> str:
        return "Amazon Timestream"
    
    def health_check(self) -> bool:
        """Verifica se o serviço Timestream está acessível"""
        try:
            self.timestream_write_client.list_databases(MaxResults=1)
            return True
        except Exception as e:
            logger.error(f"Timestream health check failed: {e}")
            return False
    
    def get_databases(self) -> List[TimestreamDatabase]:
        """Lista todos os databases Timestream"""
        databases = []
        try:
            paginator = self.timestream_write_client.get_paginator('list_databases')
            for page in paginator.paginate():
                for db in page.get('Databases', []):
                    database = TimestreamDatabase(
                        database_name=db['DatabaseName'],
                        arn=db['Arn'],
                        table_count=db.get('TableCount', 0),
                        kms_key_id=db.get('KmsKeyId'),
                        creation_time=db.get('CreationTime'),
                        last_updated_time=db.get('LastUpdatedTime')
                    )
                    
                    try:
                        tags_response = self.timestream_write_client.list_tags_for_resource(
                            ResourceARN=db['Arn']
                        )
                        database.tags = {t['Key']: t['Value'] for t in tags_response.get('Tags', [])}
                    except Exception as e:  # noqa: E722
                        pass
                    
                    databases.append(database)
            
            logger.info(f"Found {len(databases)} Timestream databases")
        except Exception as e:
            logger.error(f"Error listing Timestream databases: {e}")
        
        return databases
    
    def get_tables(self, database_name: Optional[str] = None) -> List[TimestreamTable]:
        """Lista todas as tables Timestream"""
        tables = []
        
        databases = self.get_databases() if not database_name else [
            TimestreamDatabase(database_name=database_name, arn='', table_count=0)
        ]
        
        for db in databases:
            try:
                paginator = self.timestream_write_client.get_paginator('list_tables')
                for page in paginator.paginate(DatabaseName=db.database_name):
                    for table in page.get('Tables', []):
                        retention = table.get('RetentionProperties', {})
                        magnetic_props = table.get('MagneticStoreWriteProperties')
                        
                        t = TimestreamTable(
                            table_name=table['TableName'],
                            database_name=table['DatabaseName'],
                            arn=table['Arn'],
                            table_status=table['TableStatus'],
                            memory_store_retention_period_in_hours=retention.get('MemoryStoreRetentionPeriodInHours', 24),
                            magnetic_store_retention_period_in_days=retention.get('MagneticStoreRetentionPeriodInDays', 365),
                            magnetic_store_write_properties=magnetic_props,
                            schema=table.get('Schema'),
                            creation_time=table.get('CreationTime'),
                            last_updated_time=table.get('LastUpdatedTime')
                        )
                        
                        try:
                            tags_response = self.timestream_write_client.list_tags_for_resource(
                                ResourceARN=table['Arn']
                            )
                            t.tags = {tag['Key']: tag['Value'] for tag in tags_response.get('Tags', [])}
                        except Exception as e:  # noqa: E722
                            pass
                        
                        tables.append(t)
                        
            except Exception as e:
                logger.error(f"Error listing tables for database {db.database_name}: {e}")
        
        logger.info(f"Found {len(tables)} Timestream tables")
        return tables
    
    def get_scheduled_queries(self) -> List[TimestreamScheduledQuery]:
        """Lista todas as scheduled queries Timestream"""
        queries = []
        try:
            paginator = self.timestream_query_client.get_paginator('list_scheduled_queries')
            for page in paginator.paginate():
                for sq in page.get('ScheduledQueries', []):
                    try:
                        details = self.timestream_query_client.describe_scheduled_query(
                            ScheduledQueryArn=sq['Arn']
                        )
                        sq_detail = details['ScheduledQuery']
                        
                        target_config = sq_detail.get('TargetConfiguration', {}).get('TimestreamConfiguration', {})
                        error_config = sq_detail.get('ErrorReportConfiguration', {}).get('S3Configuration', {})
                        
                        query = TimestreamScheduledQuery(
                            name=sq_detail['Name'],
                            arn=sq_detail['Arn'],
                            state=sq_detail['State'],
                            query_string=sq_detail.get('QueryString', ''),
                            schedule_expression=sq_detail.get('ScheduleConfiguration', {}).get('ScheduleExpression', ''),
                            target_database=target_config.get('DatabaseName', ''),
                            target_table=target_config.get('TableName', ''),
                            error_report_s3_bucket=error_config.get('BucketName'),
                            creation_time=sq_detail.get('CreationTime'),
                            last_run_status=sq_detail.get('LastRunSummary', {}).get('RunStatus'),
                            next_invocation_time=sq_detail.get('NextInvocationTime')
                        )
                        queries.append(query)
                    except Exception as e:
                        logger.debug(f"Could not describe scheduled query {sq['Arn']}: {e}")
            
            logger.info(f"Found {len(queries)} Timestream scheduled queries")
        except Exception as e:
            logger.error(f"Error listing Timestream scheduled queries: {e}")
        
        return queries
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos Timestream"""
        databases = self.get_databases()
        tables = self.get_tables()
        scheduled_queries = self.get_scheduled_queries()
        
        tables_by_database = {}
        for table in tables:
            if table.database_name not in tables_by_database:
                tables_by_database[table.database_name] = []
            tables_by_database[table.database_name].append(table.to_dict())
        
        return {
            'databases': [db.to_dict() for db in databases],
            'tables': [t.to_dict() for t in tables],
            'scheduled_queries': [sq.to_dict() for sq in scheduled_queries],
            'tables_by_database': tables_by_database,
            'summary': {
                'total_databases': len(databases),
                'total_tables': len(tables),
                'total_scheduled_queries': len(scheduled_queries),
                'active_tables': len([t for t in tables if t.is_active]),
                'encrypted_databases': len([db for db in databases if db.is_encrypted]),
                'enabled_scheduled_queries': len([sq for sq in scheduled_queries if sq.is_enabled])
            }
        }
    
    def get_metrics(self, database_name: Optional[str] = None, period_hours: int = 24) -> Dict[str, Any]:
        """Obtém métricas de utilização do Timestream"""
        metrics = {}
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)
        
        tables = self.get_tables(database_name)
        
        for table in tables:
            try:
                table_metrics = {}
                
                metric_names = [
                    'SuccessfulRequestLatency',
                    'SystemErrors',
                    'UserErrors',
                    'MagneticStoreRejectedRecordCount',
                    'MemoryStoreDataBytes'
                ]
                
                for metric_name in metric_names:
                    try:
                        response = self.cloudwatch_client.get_metric_statistics(
                            Namespace='AWS/Timestream',
                            MetricName=metric_name,
                            Dimensions=[
                                {'Name': 'DatabaseName', 'Value': table.database_name},
                                {'Name': 'TableName', 'Value': table.table_name}
                            ],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['Average', 'Maximum', 'Sum']
                        )
                        
                        datapoints = response.get('Datapoints', [])
                        if datapoints:
                            table_metrics[metric_name] = {
                                'average': sum(d.get('Average', 0) for d in datapoints) / len(datapoints),
                                'maximum': max(d.get('Maximum', 0) for d in datapoints),
                                'sum': sum(d.get('Sum', 0) for d in datapoints)
                            }
                    except Exception as e:
                        logger.debug(f"Could not get metric {metric_name}: {e}")
                
                table_key = f"{table.database_name}/{table.table_name}"
                metrics[table_key] = table_metrics
                
            except Exception as e:
                logger.error(f"Error getting metrics for {table.database_name}/{table.table_name}: {e}")
        
        return metrics
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização de custos para Timestream"""
        recommendations = []
        databases = self.get_databases()
        tables = self.get_tables()
        scheduled_queries = self.get_scheduled_queries()
        
        for db in databases:
            if not db.is_encrypted:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=db.database_name,
                    recommendation_type='security',
                    title='Database Timestream sem Criptografia CMK',
                    description=f"Database '{db.database_name}' usa criptografia padrão AWS",
                    action='Considere usar CMK (Customer Managed Key) para maior controle de segurança',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={'table_count': db.table_count}
                ))
            
            if not db.has_tables:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=db.database_name,
                    recommendation_type='cost_optimization',
                    title='Database Timestream sem Tables',
                    description=f"Database '{db.database_name}' não tem tables",
                    action='Delete o database se não for mais necessário',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={}
                ))
        
        for table in tables:
            if not table.is_active:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=f"{table.database_name}/{table.table_name}",
                    recommendation_type='operational',
                    title='Table Timestream Não Ativa',
                    description=f"Table '{table.table_name}' está em estado '{table.table_status}'",
                    action='Investigue o estado da table e tome ação corretiva',
                    estimated_savings=0.0,
                    priority='high',
                    metadata={'status': table.table_status}
                ))
            
            if table.memory_retention_hours > 168:
                estimated_savings = (table.memory_retention_hours - 168) * 0.05
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=f"{table.database_name}/{table.table_name}",
                    recommendation_type='cost_optimization',
                    title='Retenção de Memory Store Alta',
                    description=f"Table '{table.table_name}' tem {table.memory_retention_hours}h de retenção em memory store",
                    action='Reduza a retenção do memory store para mover dados mais rápido para magnetic store',
                    estimated_savings=estimated_savings,
                    priority='medium',
                    metadata={'current_hours': table.memory_retention_hours}
                ))
            
            if table.magnetic_retention_days > 3650:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=f"{table.database_name}/{table.table_name}",
                    recommendation_type='cost_optimization',
                    title='Retenção de Magnetic Store Muito Longa',
                    description=f"Table '{table.table_name}' retém dados por {table.magnetic_retention_days} dias (>10 anos)",
                    action='Avalie se é necessário reter dados por tanto tempo. Considere exportar para S3',
                    estimated_savings=50.0,
                    priority='low',
                    metadata={'current_days': table.magnetic_retention_days}
                ))
            
            if table.has_magnetic_writes:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=f"{table.database_name}/{table.table_name}",
                    recommendation_type='performance',
                    title='Escrita Direta no Magnetic Store Habilitada',
                    description=f"Table '{table.table_name}' permite escrita direta no magnetic store",
                    action='Monitore latência de queries. Escrita magnética pode impactar performance',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={}
                ))
        
        for sq in scheduled_queries:
            if sq.is_disabled:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=sq.name,
                    recommendation_type='operational',
                    title='Scheduled Query Desabilitada',
                    description=f"Scheduled query '{sq.name}' está desabilitada",
                    action='Delete a scheduled query se não for mais necessária',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={'last_status': sq.last_run_status}
                ))
            
            if not sq.has_error_reporting:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=sq.name,
                    recommendation_type='operational',
                    title='Scheduled Query sem Error Reporting',
                    description=f"Scheduled query '{sq.name}' não tem error reporting configurado",
                    action='Configure error reporting para S3 para diagnóstico de falhas',
                    estimated_savings=0.0,
                    priority='low',
                    metadata={}
                ))
        
        logger.info(f"Generated {len(recommendations)} Timestream recommendations")
        return recommendations
