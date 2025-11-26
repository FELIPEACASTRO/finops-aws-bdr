"""
DynamoDB State Manager - Sistema de Controle de Execução com DynamoDB

FASE 1.2 do Roadmap FinOps AWS
Objetivo: Substituir S3 por DynamoDB para persistência de estado com checkpoint granular

Autor: FinOps AWS Team
Data: Novembro 2025

Vantagens sobre S3:
- Latência menor para leituras/escritas
- Operações atômicas (condicionais)
- TTL automático para limpeza de execuções antigas
- Índices secundários para consultas eficientes
- Checkpoint granular por serviço AWS

Melhorias de Arquitetura:
- Injeção de dependências para cliente DynamoDB (Clean Architecture)
- Integração com RetryHandler para operações resilientes
- ConditionExpression para evitar race conditions
- Mapper dedicado para serialização JSON/Decimal
"""
import os
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable, Protocol
from enum import Enum
import json
import boto3
from botocore.exceptions import ClientError

from ..utils.logger import setup_logger
from .retry_handler import RetryHandler, RetryPolicy, create_aws_retry_policy

logger = setup_logger(__name__)


class DynamoDBClientProtocol(Protocol):
    """Protocol para injeção de dependência do cliente DynamoDB"""
    
    def describe_table(self, **kwargs) -> Dict[str, Any]: ...
    def create_table(self, **kwargs) -> Dict[str, Any]: ...
    def get_waiter(self, waiter_name: str) -> Any: ...


class DynamoDBTableProtocol(Protocol):
    """Protocol para injeção de dependência da tabela DynamoDB"""
    
    def put_item(self, **kwargs) -> Dict[str, Any]: ...
    def get_item(self, **kwargs) -> Dict[str, Any]: ...
    def update_item(self, **kwargs) -> Dict[str, Any]: ...
    def query(self, **kwargs) -> Dict[str, Any]: ...
    def delete_item(self, **kwargs) -> Dict[str, Any]: ...


class DynamoDBMapper:
    """
    Mapper para serialização/deserialização entre domínio e DynamoDB
    
    Responsável por converter tipos Python para formato DynamoDB e vice-versa,
    isolando a lógica de serialização em uma camada dedicada.
    """
    
    @staticmethod
    def serialize_decimal(value: Any) -> Any:
        """Converte floats para Decimal (exigido pelo DynamoDB)"""
        if isinstance(value, float):
            return Decimal(str(value))
        elif isinstance(value, dict):
            return {k: DynamoDBMapper.serialize_decimal(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [DynamoDBMapper.serialize_decimal(item) for item in value]
        return value
    
    @staticmethod
    def deserialize_decimal(value: Any) -> Any:
        """Converte Decimal de volta para float"""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: DynamoDBMapper.deserialize_decimal(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [DynamoDBMapper.deserialize_decimal(item) for item in value]
        return value
    
    @staticmethod
    def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
        """Serializa datetime para ISO format string"""
        return dt.isoformat() if dt else None
    
    @staticmethod
    def deserialize_datetime(value: Optional[str]) -> Optional[datetime]:
        """Deserializa ISO format string para datetime"""
        return datetime.fromisoformat(value) if value else None
    
    @staticmethod
    def serialize_json(data: Any) -> str:
        """Serializa dados para JSON com suporte a Decimal"""
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        return json.dumps(data, default=decimal_default)
    
    @staticmethod
    def deserialize_json(json_str: str) -> Any:
        """Deserializa JSON string"""
        return json.loads(json_str) if json_str else {}


class ExecutionStatus(Enum):
    """Status de execução"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Status de uma tarefa individual"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ServiceCategory(Enum):
    """Categorias de serviços AWS para checkpoint granular"""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    ANALYTICS = "analytics"
    MACHINE_LEARNING = "machine_learning"
    MANAGEMENT = "management"
    SECURITY = "security"
    COST = "cost"


@dataclass
class CheckpointData:
    """
    Dados de checkpoint para um serviço específico
    
    Permite retomar a análise de um serviço específico
    sem precisar reprocessar todos os serviços
    """
    service_name: str
    category: ServiceCategory
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_checkpoint_at: Optional[datetime] = None
    items_processed: int = 0
    items_total: int = 0
    progress_percentage: float = 0.0
    last_processed_id: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            'service_name': self.service_name,
            'category': self.category.value,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_checkpoint_at': self.last_checkpoint_at.isoformat() if self.last_checkpoint_at else None,
            'items_processed': self.items_processed,
            'items_total': self.items_total,
            'progress_percentage': self.progress_percentage,
            'last_processed_id': self.last_processed_id,
            'result_summary': self.result_summary,
            'error_message': self.error_message,
            'retry_count': self.retry_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointData':
        """Cria CheckpointData a partir de dicionário"""
        return cls(
            service_name=data['service_name'],
            category=ServiceCategory(data['category']),
            status=TaskStatus(data['status']),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            last_checkpoint_at=datetime.fromisoformat(data['last_checkpoint_at']) if data.get('last_checkpoint_at') else None,
            items_processed=data.get('items_processed', 0),
            items_total=data.get('items_total', 0),
            progress_percentage=data.get('progress_percentage', 0.0),
            last_processed_id=data.get('last_processed_id'),
            result_summary=data.get('result_summary'),
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0)
        )


@dataclass
class BatchConfig:
    """Configuração para processamento em lotes"""
    batch_size: int = 100
    max_concurrent_batches: int = 5
    checkpoint_interval: int = 50
    retry_failed_items: bool = True


@dataclass
class ExecutionRecord:
    """
    Registro completo de uma execução no DynamoDB
    
    Estrutura otimizada para consultas e checkpoints granulares
    """
    execution_id: str
    account_id: str
    region: str
    status: ExecutionStatus
    started_at: datetime
    last_updated: datetime
    completed_at: Optional[datetime] = None
    ttl: Optional[int] = None
    checkpoints: Dict[str, CheckpointData] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_summary: Optional[Dict[str, Any]] = None
    total_services: int = 0
    completed_services: int = 0
    failed_services: int = 0
    total_items_processed: int = 0
    estimated_cost_analyzed: float = 0.0

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Converte para formato DynamoDB"""
        item = {
            'PK': f"EXEC#{self.execution_id}",
            'SK': f"ACCOUNT#{self.account_id}",
            'execution_id': self.execution_id,
            'account_id': self.account_id,
            'region': self.region,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'total_services': self.total_services,
            'completed_services': self.completed_services,
            'failed_services': self.failed_services,
            'total_items_processed': self.total_items_processed,
            'estimated_cost_analyzed': Decimal(str(self.estimated_cost_analyzed)),
            'metadata': json.dumps(self.metadata),
            'checkpoints': json.dumps({k: v.to_dict() for k, v in self.checkpoints.items()}),
            'GSI1PK': f"ACCOUNT#{self.account_id}",
            'GSI1SK': f"EXEC#{self.started_at.isoformat()}"
        }
        
        if self.completed_at:
            item['completed_at'] = self.completed_at.isoformat()
        if self.ttl:
            item['ttl'] = self.ttl
        if self.error_summary:
            item['error_summary'] = json.dumps(self.error_summary)
            
        return item

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'ExecutionRecord':
        """Cria ExecutionRecord a partir de item DynamoDB"""
        checkpoints_data = json.loads(item.get('checkpoints', '{}'))
        checkpoints = {k: CheckpointData.from_dict(v) for k, v in checkpoints_data.items()}
        
        return cls(
            execution_id=item['execution_id'],
            account_id=item['account_id'],
            region=item.get('region', 'us-east-1'),
            status=ExecutionStatus(item['status']),
            started_at=datetime.fromisoformat(item['started_at']),
            last_updated=datetime.fromisoformat(item['last_updated']),
            completed_at=datetime.fromisoformat(item['completed_at']) if item.get('completed_at') else None,
            ttl=item.get('ttl'),
            checkpoints=checkpoints,
            metadata=json.loads(item.get('metadata', '{}')),
            error_summary=json.loads(item['error_summary']) if item.get('error_summary') else None,
            total_services=item.get('total_services', 0),
            completed_services=item.get('completed_services', 0),
            failed_services=item.get('failed_services', 0),
            total_items_processed=item.get('total_items_processed', 0),
            estimated_cost_analyzed=float(item.get('estimated_cost_analyzed', 0))
        )


class DynamoDBStateManager:
    """
    Gerenciador de Estado com DynamoDB
    
    Implementa:
    - Persistência de estado em DynamoDB
    - Checkpoint granular por serviço AWS
    - TTL automático para limpeza
    - Operações atômicas com condições (ConditionExpression)
    - Índices secundários para consultas eficientes
    - Injeção de dependências para Clean Architecture
    - Integração com RetryHandler para resiliência
    
    Estrutura da Tabela:
    - PK: EXEC#<execution_id>
    - SK: ACCOUNT#<account_id>
    - GSI1: Account executions by date
      - GSI1PK: ACCOUNT#<account_id>
      - GSI1SK: EXEC#<timestamp>
    
    Uso:
        manager = DynamoDBStateManager()
        execution = manager.create_execution("123456789012")
        manager.update_checkpoint("ec2", ServiceCategory.COMPUTE, items_processed=50)
        manager.complete_execution()
        
    Com Injeção de Dependências:
        custom_table = mock_dynamodb.Table('test-table')
        manager = DynamoDBStateManager(table=custom_table)
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        region: Optional[str] = None,
        ttl_days: int = 30,
        dynamodb_client: Optional[Any] = None,
        dynamodb_resource: Optional[Any] = None,
        table: Optional[Any] = None,
        retry_handler: Optional[RetryHandler] = None
    ):
        """
        Inicializa o DynamoDB State Manager
        
        Args:
            table_name: Nome da tabela DynamoDB
            region: Região AWS
            ttl_days: Dias para manter execuções antes de expirar
            dynamodb_client: Cliente DynamoDB injetado (para testes/Clean Architecture)
            dynamodb_resource: Resource DynamoDB injetado (para testes/Clean Architecture)
            table: Tabela DynamoDB injetada (para testes/Clean Architecture)
            retry_handler: RetryHandler personalizado (opcional)
        """
        self.table_name = table_name or os.getenv('FINOPS_DYNAMODB_TABLE', 'finops-aws-executions')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        self.ttl_days = ttl_days
        self._dynamodb_client = dynamodb_client
        self._dynamodb_resource = dynamodb_resource
        self._table = table
        self.current_execution: Optional[ExecutionRecord] = None
        self.mapper = DynamoDBMapper()
        
        self._retry_handler = retry_handler or RetryHandler(
            policy=create_aws_retry_policy()
        )
        
        logger.info("DynamoDBStateManager initialized", extra={
            'extra_data': {
                'table_name': self.table_name,
                'region': self.region,
                'ttl_days': self.ttl_days,
                'injected_client': dynamodb_client is not None,
                'injected_table': table is not None
            }
        })

    @property
    def dynamodb_client(self):
        """Lazy initialization do cliente DynamoDB (suporta injeção)"""
        if self._dynamodb_client is None:
            self._dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        return self._dynamodb_client

    @property
    def dynamodb_resource(self):
        """Lazy initialization do resource DynamoDB (suporta injeção)"""
        if self._dynamodb_resource is None:
            self._dynamodb_resource = boto3.resource('dynamodb', region_name=self.region)
        return self._dynamodb_resource

    @property
    def table(self):
        """Lazy initialization da tabela (suporta injeção)"""
        if self._table is None:
            self._table = self.dynamodb_resource.Table(self.table_name)
        return self._table
    
    @property
    def retry_handler(self) -> RetryHandler:
        """Acesso ao retry handler para operações resilientes"""
        return self._retry_handler

    def _generate_execution_id(self, account_id: str) -> str:
        """Gera ID único para execução"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        hash_suffix = hashlib.sha256(f"{account_id}_{timestamp}".encode()).hexdigest()[:12]
        return f"exec_{timestamp}_{hash_suffix}"

    def _calculate_ttl(self) -> int:
        """Calcula timestamp TTL para expiração"""
        expiry_date = datetime.now() + timedelta(days=self.ttl_days)
        return int(expiry_date.timestamp())

    def ensure_table_exists(self) -> bool:
        """
        Verifica se a tabela existe e a cria se necessário
        
        Returns:
            True se a tabela existe ou foi criada com sucesso
        """
        try:
            self.dynamodb_client.describe_table(TableName=self.table_name)
            logger.info(f"Table {self.table_name} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return self._create_table()
            raise

    def _create_table(self) -> bool:
        """Cria a tabela DynamoDB com índices"""
        try:
            self.dynamodb_client.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'GSI1',
                        'KeySchema': [
                            {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                },
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
            
            logger.info(f"Created table {self.table_name}")
            
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name)
            
            return True
        except ClientError as e:
            logger.error(f"Failed to create table: {e}")
            raise

    def create_execution(
        self,
        account_id: str,
        services: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionRecord:
        """
        Cria uma nova execução ou retoma uma existente
        
        Args:
            account_id: ID da conta AWS
            services: Lista de serviços a processar
            metadata: Metadados adicionais
            
        Returns:
            ExecutionRecord com o estado da execução
        """
        existing = self.get_running_execution(account_id)
        if existing:
            if self._should_resume_execution(existing):
                logger.info(f"Resuming existing execution: {existing.execution_id}")
                self.current_execution = existing
                return existing
            else:
                logger.warning(f"Marking old execution as failed: {existing.execution_id}")
                self._mark_execution_failed(existing, "Execution timeout - replaced by new execution")

        now = datetime.now()
        execution_id = self._generate_execution_id(account_id)
        
        default_services = services or [
            'ec2', 'lambda', 'rds', 's3', 'ebs',
            'cloudwatch', 'cost_explorer', 'compute_optimizer'
        ]
        
        checkpoints = {}
        for service in default_services:
            category = self._get_service_category(service)
            checkpoints[service] = CheckpointData(
                service_name=service,
                category=category,
                status=TaskStatus.PENDING
            )
        
        execution = ExecutionRecord(
            execution_id=execution_id,
            account_id=account_id,
            region=self.region,
            status=ExecutionStatus.RUNNING,
            started_at=now,
            last_updated=now,
            ttl=self._calculate_ttl(),
            checkpoints=checkpoints,
            metadata=metadata or {},
            total_services=len(default_services)
        )
        
        self._save_execution(execution)
        self.current_execution = execution
        
        logger.info(f"Created new execution: {execution_id}", extra={
            'extra_data': {
                'account_id': account_id,
                'services': default_services
            }
        })
        
        return execution

    def _get_service_category(self, service: str) -> ServiceCategory:
        """Determina a categoria de um serviço AWS"""
        categories = {
            'ec2': ServiceCategory.COMPUTE,
            'lambda': ServiceCategory.COMPUTE,
            'ecs': ServiceCategory.COMPUTE,
            'eks': ServiceCategory.COMPUTE,
            's3': ServiceCategory.STORAGE,
            'ebs': ServiceCategory.STORAGE,
            'efs': ServiceCategory.STORAGE,
            'glacier': ServiceCategory.STORAGE,
            'rds': ServiceCategory.DATABASE,
            'dynamodb': ServiceCategory.DATABASE,
            'redshift': ServiceCategory.DATABASE,
            'elasticache': ServiceCategory.DATABASE,
            'vpc': ServiceCategory.NETWORKING,
            'elb': ServiceCategory.NETWORKING,
            'cloudfront': ServiceCategory.NETWORKING,
            'route53': ServiceCategory.NETWORKING,
            'athena': ServiceCategory.ANALYTICS,
            'emr': ServiceCategory.ANALYTICS,
            'kinesis': ServiceCategory.ANALYTICS,
            'sagemaker': ServiceCategory.MACHINE_LEARNING,
            'rekognition': ServiceCategory.MACHINE_LEARNING,
            'cloudwatch': ServiceCategory.MANAGEMENT,
            'cloudtrail': ServiceCategory.MANAGEMENT,
            'config': ServiceCategory.MANAGEMENT,
            'iam': ServiceCategory.SECURITY,
            'kms': ServiceCategory.SECURITY,
            'waf': ServiceCategory.SECURITY,
            'cost_explorer': ServiceCategory.COST,
            'compute_optimizer': ServiceCategory.COST,
            'budgets': ServiceCategory.COST
        }
        return categories.get(service.lower(), ServiceCategory.MANAGEMENT)

    def _should_resume_execution(self, execution: ExecutionRecord, max_age_hours: int = 2) -> bool:
        """Verifica se uma execução deve ser retomada"""
        age = datetime.now() - execution.last_updated
        return age < timedelta(hours=max_age_hours)

    def _save_execution(self, execution: ExecutionRecord, is_new: bool = True, use_condition: bool = False):
        """
        Salva execução no DynamoDB com retry e condição atômica opcional
        
        Args:
            execution: ExecutionRecord a salvar
            is_new: Se True e use_condition=True, usa ConditionExpression para evitar sobrescrita
            use_condition: Se True, aplica ConditionExpression para operações atômicas
        """
        def do_save():
            item = execution.to_dynamodb_item()
            
            if is_new and use_condition:
                self.table.put_item(
                    Item=item,
                    ConditionExpression='attribute_not_exists(PK)'
                )
            else:
                self.table.put_item(Item=item)
        
        try:
            self._retry_handler.execute(do_save)
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'ConditionalCheckFailedException':
                logger.warning(f"Execution already exists: {execution.execution_id}")
                raise
            logger.error(f"Failed to save execution: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
            raise
    
    def _update_execution_atomic(
        self,
        execution_id: str,
        account_id: str,
        update_expression: str,
        expression_attribute_names: Dict[str, str],
        expression_attribute_values: Dict[str, Any],
        condition_expression: Optional[str] = None
    ) -> bool:
        """
        Atualiza execução com operação atômica
        
        Args:
            execution_id: ID da execução
            account_id: ID da conta AWS
            update_expression: Expressão de atualização DynamoDB
            expression_attribute_names: Nomes de atributos
            expression_attribute_values: Valores de atributos
            condition_expression: Condição para update atômico
            
        Returns:
            True se atualização foi bem sucedida
        """
        def do_update():
            update_params = {
                'Key': {
                    'PK': f"EXEC#{execution_id}",
                    'SK': f"ACCOUNT#{account_id}"
                },
                'UpdateExpression': update_expression,
                'ExpressionAttributeNames': expression_attribute_names,
                'ExpressionAttributeValues': expression_attribute_values
            }
            
            if condition_expression:
                update_params['ConditionExpression'] = condition_expression
            
            self.table.update_item(**update_params)
            return True
        
        try:
            return self._retry_handler.execute(do_update)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Concurrent update detected for execution: {execution_id}")
                return False
            logger.error(f"Failed to update execution: {e}")
            raise

    def get_running_execution(self, account_id: str) -> Optional[ExecutionRecord]:
        """
        Obtém execução em andamento para uma conta (com retry)
        
        Args:
            account_id: ID da conta AWS
            
        Returns:
            ExecutionRecord se houver execução em andamento
        """
        def do_query():
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':pk': f"ACCOUNT#{account_id}",
                    ':status': ExecutionStatus.RUNNING.value
                },
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                return ExecutionRecord.from_dynamodb_item(items[0])
            return None
        
        try:
            return self._retry_handler.execute(do_query)
        except (ClientError, Exception) as e:
            logger.error(f"Failed to get running execution: {e}")
            return None

    def get_execution(self, execution_id: str, account_id: str) -> Optional[ExecutionRecord]:
        """
        Obtém uma execução específica (com retry)
        
        Args:
            execution_id: ID da execução
            account_id: ID da conta AWS
            
        Returns:
            ExecutionRecord ou None se não encontrada
        """
        def do_get():
            response = self.table.get_item(
                Key={
                    'PK': f"EXEC#{execution_id}",
                    'SK': f"ACCOUNT#{account_id}"
                }
            )
            
            item = response.get('Item')
            if item:
                return ExecutionRecord.from_dynamodb_item(item)
            return None
        
        try:
            return self._retry_handler.execute(do_get)
        except (ClientError, Exception) as e:
            logger.error(f"Failed to get execution: {e}")
            return None

    def update_checkpoint(
        self,
        service_name: str,
        status: Optional[TaskStatus] = None,
        items_processed: Optional[int] = None,
        items_total: Optional[int] = None,
        last_processed_id: Optional[str] = None,
        result_summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Atualiza checkpoint de um serviço específico
        
        Args:
            service_name: Nome do serviço
            status: Novo status
            items_processed: Itens processados
            items_total: Total de itens
            last_processed_id: ID do último item processado
            result_summary: Resumo do resultado
            error_message: Mensagem de erro se houver
            
        Returns:
            True se atualizado com sucesso
        """
        if not self.current_execution:
            logger.error("No current execution to update")
            return False
        
        checkpoint = self.current_execution.checkpoints.get(service_name)
        if not checkpoint:
            logger.warning(f"Service {service_name} not found in checkpoints")
            return False
        
        now = datetime.now()
        
        if status:
            checkpoint.status = status
            if status == TaskStatus.RUNNING and not checkpoint.started_at:
                checkpoint.started_at = now
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]:
                checkpoint.completed_at = now
        
        if items_processed is not None:
            checkpoint.items_processed = items_processed
        if items_total is not None:
            checkpoint.items_total = items_total
        if last_processed_id:
            checkpoint.last_processed_id = last_processed_id
        if result_summary:
            checkpoint.result_summary = result_summary
        if error_message:
            checkpoint.error_message = error_message
            checkpoint.retry_count += 1
        
        if checkpoint.items_total > 0:
            checkpoint.progress_percentage = (checkpoint.items_processed / checkpoint.items_total) * 100
        
        checkpoint.last_checkpoint_at = now
        self.current_execution.last_updated = now
        
        self._update_execution_stats()
        self._save_execution(self.current_execution)
        
        logger.debug(f"Updated checkpoint for {service_name}", extra={
            'extra_data': checkpoint.to_dict()
        })
        
        return True

    def start_service(self, service_name: str, items_total: int = 0) -> bool:
        """
        Marca o início do processamento de um serviço
        
        Args:
            service_name: Nome do serviço
            items_total: Total de itens a processar
            
        Returns:
            True se iniciado com sucesso
        """
        return self.update_checkpoint(
            service_name,
            status=TaskStatus.RUNNING,
            items_total=items_total
        )

    def complete_service(
        self,
        service_name: str,
        result_summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Marca o serviço como concluído
        
        Args:
            service_name: Nome do serviço
            result_summary: Resumo do resultado
            
        Returns:
            True se completado com sucesso
        """
        checkpoint = self.current_execution.checkpoints.get(service_name) if self.current_execution else None
        items_total = checkpoint.items_total if checkpoint else 0
        
        return self.update_checkpoint(
            service_name,
            status=TaskStatus.COMPLETED,
            items_processed=items_total,
            result_summary=result_summary
        )

    def fail_service(self, service_name: str, error_message: str) -> bool:
        """
        Marca o serviço como falho
        
        Args:
            service_name: Nome do serviço
            error_message: Mensagem de erro
            
        Returns:
            True se marcado com sucesso
        """
        return self.update_checkpoint(
            service_name,
            status=TaskStatus.FAILED,
            error_message=error_message
        )

    def skip_service(self, service_name: str, reason: str = "Skipped") -> bool:
        """
        Marca o serviço como pulado
        
        Args:
            service_name: Nome do serviço
            reason: Razão para pular
            
        Returns:
            True se marcado com sucesso
        """
        return self.update_checkpoint(
            service_name,
            status=TaskStatus.SKIPPED,
            error_message=reason
        )

    def _update_execution_stats(self):
        """Atualiza estatísticas da execução baseado nos checkpoints"""
        if not self.current_execution:
            return
        
        completed = 0
        failed = 0
        total_items = 0
        
        for checkpoint in self.current_execution.checkpoints.values():
            if checkpoint.status == TaskStatus.COMPLETED:
                completed += 1
            elif checkpoint.status == TaskStatus.FAILED:
                failed += 1
            total_items += checkpoint.items_processed
        
        self.current_execution.completed_services = completed
        self.current_execution.failed_services = failed
        self.current_execution.total_items_processed = total_items

    def complete_execution(self, final_summary: Optional[Dict[str, Any]] = None) -> bool:
        """
        Marca a execução como concluída
        
        Args:
            final_summary: Resumo final da execução
            
        Returns:
            True se completada com sucesso
        """
        if not self.current_execution:
            logger.error("No current execution to complete")
            return False
        
        now = datetime.now()
        self.current_execution.completed_at = now
        self.current_execution.last_updated = now
        
        if self.current_execution.failed_services > 0:
            self.current_execution.status = ExecutionStatus.PARTIALLY_COMPLETED
        else:
            self.current_execution.status = ExecutionStatus.COMPLETED
        
        if final_summary:
            self.current_execution.metadata['final_summary'] = final_summary
        
        self._save_execution(self.current_execution)
        
        logger.info(f"Execution completed: {self.current_execution.execution_id}", extra={
            'extra_data': {
                'status': self.current_execution.status.value,
                'completed_services': self.current_execution.completed_services,
                'failed_services': self.current_execution.failed_services
            }
        })
        
        return True

    def _mark_execution_failed(self, execution: ExecutionRecord, error_message: str):
        """Marca uma execução como falha"""
        execution.status = ExecutionStatus.FAILED
        execution.last_updated = datetime.now()
        execution.error_summary = {'message': error_message}
        self._save_execution(execution)

    def get_pending_services(self) -> List[str]:
        """
        Obtém lista de serviços pendentes
        
        Returns:
            Lista de nomes de serviços pendentes
        """
        if not self.current_execution:
            return []
        
        return [
            name for name, checkpoint in self.current_execution.checkpoints.items()
            if checkpoint.status == TaskStatus.PENDING
        ]

    def get_failed_services(self) -> List[str]:
        """
        Obtém lista de serviços que falharam
        
        Returns:
            Lista de nomes de serviços falhos
        """
        if not self.current_execution:
            return []
        
        return [
            name for name, checkpoint in self.current_execution.checkpoints.items()
            if checkpoint.status == TaskStatus.FAILED
        ]

    def get_execution_progress(self) -> Dict[str, Any]:
        """
        Obtém progresso da execução atual
        
        Returns:
            Dicionário com estatísticas de progresso
        """
        if not self.current_execution:
            return {'error': 'No current execution'}
        
        exec_state = self.current_execution
        
        services_by_status = {
            'pending': [],
            'running': [],
            'completed': [],
            'failed': [],
            'skipped': []
        }
        
        for name, checkpoint in exec_state.checkpoints.items():
            services_by_status[checkpoint.status.value].append(name)
        
        total = exec_state.total_services
        completed = exec_state.completed_services
        
        return {
            'execution_id': exec_state.execution_id,
            'status': exec_state.status.value,
            'progress_percentage': round((completed / total) * 100, 2) if total > 0 else 0,
            'total_services': total,
            'completed_services': completed,
            'failed_services': exec_state.failed_services,
            'services_by_status': services_by_status,
            'total_items_processed': exec_state.total_items_processed,
            'started_at': exec_state.started_at.isoformat(),
            'last_updated': exec_state.last_updated.isoformat(),
            'elapsed_seconds': (datetime.now() - exec_state.started_at).total_seconds()
        }

    def get_service_checkpoint(self, service_name: str) -> Optional[CheckpointData]:
        """
        Obtém checkpoint de um serviço específico
        
        Args:
            service_name: Nome do serviço
            
        Returns:
            CheckpointData ou None se não encontrado
        """
        if not self.current_execution:
            return None
        return self.current_execution.checkpoints.get(service_name)

    def get_recent_executions(
        self,
        account_id: str,
        limit: int = 10
    ) -> List[ExecutionRecord]:
        """
        Obtém execuções recentes de uma conta
        
        Args:
            account_id: ID da conta AWS
            limit: Número máximo de execuções
            
        Returns:
            Lista de ExecutionRecord
        """
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f"ACCOUNT#{account_id}"
                },
                ScanIndexForward=False,
                Limit=limit
            )
            
            return [ExecutionRecord.from_dynamodb_item(item) for item in response.get('Items', [])]
        except ClientError as e:
            logger.error(f"Failed to get recent executions: {e}")
            return []

    def cleanup_old_executions(self, account_id: str, keep_count: int = 100) -> int:
        """
        Remove execuções antigas (além do TTL)
        
        Args:
            account_id: ID da conta AWS
            keep_count: Número de execuções a manter
            
        Returns:
            Número de execuções removidas
        """
        deleted_count = 0
        
        try:
            executions = self.get_recent_executions(account_id, limit=1000)
            
            if len(executions) <= keep_count:
                return 0
            
            executions_to_delete = executions[keep_count:]
            
            with self.table.batch_writer() as batch:
                for execution in executions_to_delete:
                    batch.delete_item(Key={
                        'PK': f"EXEC#{execution.execution_id}",
                        'SK': f"ACCOUNT#{execution.account_id}"
                    })
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old executions for account {account_id}")
            
        except ClientError as e:
            logger.error(f"Failed to cleanup old executions: {e}")
        
        return deleted_count
