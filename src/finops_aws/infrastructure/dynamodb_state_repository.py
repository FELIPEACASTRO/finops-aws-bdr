"""
Repositório DynamoDB para persistência de estado das execuções FinOps.

Implementa persistência robusta de estado com checkpoint granular por serviço AWS,
conforme especificado na FASE 1.2 do roadmap.
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
from decimal import Decimal

from ..core.state_manager import ExecutionState, TaskState, ExecutionStatus, TaskType
from ..utils.logger import setup_logger


class DynamoDBStateRepository:
    """
    Repositório DynamoDB para persistência de estado das execuções.
    
    Funcionalidades:
    - Checkpoint granular por serviço AWS
    - Persistência robusta com retry automático
    - Consultas eficientes de estado
    - Limpeza automática de execuções antigas
    - Suporte a execução incremental
    """
    
    def __init__(self, table_name: str = None, region: str = None):
        self.table_name = table_name or 'finops-execution-state'
        self.region = region or 'us-east-1'
        self.logger = setup_logger(__name__)
        
        # Inicializa cliente DynamoDB
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.table = None
        
        # Inicializa tabela
        self._initialize_table()
    
    def _initialize_table(self):
        """Inicializa ou cria tabela DynamoDB se não existir."""
        try:
            self.table = self.dynamodb.Table(self.table_name)
            # Testa se a tabela existe
            self.table.load()
            self.logger.info(f"Connected to DynamoDB table: {self.table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self.logger.info(f"Table {self.table_name} not found, creating...")
                self._create_table()
            else:
                self.logger.error(f"Error connecting to DynamoDB table: {e}")
                raise
    
    def _create_table(self):
        """Cria tabela DynamoDB com schema otimizado."""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'pk',  # partition key: account_id
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'sk',  # sort key: execution_id ou task_id
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'pk',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'sk',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'gsi1pk',  # GSI para consultas por status
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'gsi1sk',  # GSI sort key
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'StatusIndex',
                        'KeySchema': [
                            {
                                'AttributeName': 'gsi1pk',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'gsi1sk',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'FinOps-AWS'
                    },
                    {
                        'Key': 'Component',
                        'Value': 'StateManagement'
                    }
                ]
            )
            
            # Aguarda tabela ficar ativa
            table.wait_until_exists()
            self.table = table
            self.logger.info(f"Created DynamoDB table: {self.table_name}")
            
        except ClientError as e:
            self.logger.error(f"Error creating DynamoDB table: {e}")
            raise
    
    def save_execution_state(self, execution: ExecutionState) -> bool:
        """
        Salva estado completo da execução no DynamoDB.
        
        Args:
            execution: Estado da execução
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Atualiza timestamp
            execution.last_updated = datetime.now()
            
            # Converte para formato DynamoDB
            execution_item = self._execution_to_dynamodb_item(execution)
            
            # Salva execução principal
            self.table.put_item(Item=execution_item)
            
            # Salva cada tarefa individualmente para checkpoint granular
            for task_id, task in execution.tasks.items():
                task_item = self._task_to_dynamodb_item(execution.account_id, task)
                self.table.put_item(Item=task_item)
            
            # Atualiza referência da última execução
            self._update_latest_execution_reference(execution)
            
            self.logger.debug(f"Saved execution state: {execution.execution_id}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Error saving execution state: {e}")
            return False
    
    def get_execution_state(self, account_id: str, execution_id: str) -> Optional[ExecutionState]:
        """
        Recupera estado da execução do DynamoDB.
        
        Args:
            account_id: ID da conta AWS
            execution_id: ID da execução
            
        Returns:
            ExecutionState ou None se não encontrado
        """
        try:
            # Busca execução principal
            response = self.table.get_item(
                Key={
                    'pk': account_id,
                    'sk': f"EXEC#{execution_id}"
                }
            )
            
            if 'Item' not in response:
                return None
            
            execution_data = self._dynamodb_item_to_execution(response['Item'])
            
            # Busca todas as tarefas da execução
            tasks = self._get_execution_tasks(account_id, execution_id)
            execution_data.tasks = {task.task_id: task for task in tasks}
            
            return execution_data
            
        except ClientError as e:
            self.logger.error(f"Error getting execution state: {e}")
            return None
    
    def get_latest_execution(self, account_id: str) -> Optional[ExecutionState]:
        """
        Recupera a última execução para uma conta.
        
        Args:
            account_id: ID da conta AWS
            
        Returns:
            ExecutionState da última execução ou None
        """
        try:
            # Busca referência da última execução
            response = self.table.get_item(
                Key={
                    'pk': account_id,
                    'sk': 'LATEST'
                }
            )
            
            if 'Item' not in response:
                return None
            
            latest_execution_id = response['Item']['execution_id']
            return self.get_execution_state(account_id, latest_execution_id)
            
        except ClientError as e:
            self.logger.error(f"Error getting latest execution: {e}")
            return None
    
    def get_execution_tasks(self, account_id: str, execution_id: str) -> List[TaskState]:
        """
        Recupera todas as tarefas de uma execução.
        
        Args:
            account_id: ID da conta AWS
            execution_id: ID da execução
            
        Returns:
            Lista de TaskState
        """
        return self._get_execution_tasks(account_id, execution_id)
    
    def _get_execution_tasks(self, account_id: str, execution_id: str) -> List[TaskState]:
        """Busca tarefas de uma execução no DynamoDB."""
        try:
            response = self.table.query(
                KeyConditionExpression='pk = :pk AND begins_with(sk, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': account_id,
                    ':sk_prefix': f"TASK#{execution_id}#"
                }
            )
            
            tasks = []
            for item in response['Items']:
                task = self._dynamodb_item_to_task(item)
                tasks.append(task)
            
            return tasks
            
        except ClientError as e:
            self.logger.error(f"Error getting execution tasks: {e}")
            return []
    
    def update_task_state(self, account_id: str, task: TaskState) -> bool:
        """
        Atualiza estado de uma tarefa específica.
        
        Args:
            account_id: ID da conta AWS
            task: Estado da tarefa
            
        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            task_item = self._task_to_dynamodb_item(account_id, task)
            self.table.put_item(Item=task_item)
            
            self.logger.debug(f"Updated task state: {task.task_id}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Error updating task state: {e}")
            return False
    
    def get_task_state(self, account_id: str, task_id: str) -> Optional[TaskState]:
        """
        Recupera estado de uma tarefa específica.
        
        Args:
            account_id: ID da conta AWS
            task_id: ID da tarefa
            
        Returns:
            TaskState ou None se não encontrado
        """
        try:
            response = self.table.get_item(
                Key={
                    'pk': account_id,
                    'sk': f"TASK#{task_id}"
                }
            )
            
            if 'Item' not in response:
                return None
            
            return self._dynamodb_item_to_task(response['Item'])
            
        except ClientError as e:
            self.logger.error(f"Error getting task state: {e}")
            return None
    
    def get_executions_by_status(self, status: ExecutionStatus, limit: int = 50) -> List[ExecutionState]:
        """
        Busca execuções por status usando GSI.
        
        Args:
            status: Status da execução
            limit: Limite de resultados
            
        Returns:
            Lista de ExecutionState
        """
        try:
            response = self.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='gsi1pk = :status',
                ExpressionAttributeValues={
                    ':status': f"STATUS#{status.value}"
                },
                Limit=limit,
                ScanIndexForward=False  # Mais recentes primeiro
            )
            
            executions = []
            for item in response['Items']:
                if item['sk'].startswith('EXEC#'):
                    execution = self._dynamodb_item_to_execution(item)
                    # Carrega tarefas se necessário
                    account_id = item['pk']
                    execution_id = item['sk'].replace('EXEC#', '')
                    tasks = self._get_execution_tasks(account_id, execution_id)
                    execution.tasks = {task.task_id: task for task in tasks}
                    executions.append(execution)
            
            return executions
            
        except ClientError as e:
            self.logger.error(f"Error getting executions by status: {e}")
            return []
    
    def cleanup_old_executions(self, account_id: str, keep_days: int = 7) -> int:
        """
        Remove execuções antigas para economizar espaço.
        
        Args:
            account_id: ID da conta AWS
            keep_days: Número de dias para manter
            
        Returns:
            int: Número de execuções removidas
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            # Busca execuções antigas
            response = self.table.query(
                KeyConditionExpression='pk = :pk AND begins_with(sk, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': account_id,
                    ':sk_prefix': 'EXEC#'
                }
            )
            
            items_to_delete = []
            executions_removed = 0
            
            for item in response['Items']:
                started_at = datetime.fromisoformat(item['started_at'])
                if started_at < cutoff_date:
                    execution_id = item['sk'].replace('EXEC#', '')
                    
                    # Adiciona execução para remoção
                    items_to_delete.append({
                        'pk': account_id,
                        'sk': f"EXEC#{execution_id}"
                    })
                    
                    # Busca e adiciona tarefas para remoção
                    tasks = self._get_execution_tasks(account_id, execution_id)
                    for task in tasks:
                        items_to_delete.append({
                            'pk': account_id,
                            'sk': f"TASK#{task.task_id}"
                        })
                    
                    executions_removed += 1
            
            # Remove em lotes
            if items_to_delete:
                self._batch_delete_items(items_to_delete)
                self.logger.info(f"Cleaned up {executions_removed} old executions")
            
            return executions_removed
            
        except ClientError as e:
            self.logger.error(f"Error cleaning up old executions: {e}")
            return 0
    
    def _batch_delete_items(self, items: List[Dict[str, str]]):
        """Remove itens em lotes usando batch_writer."""
        try:
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key=item)
                    
        except ClientError as e:
            self.logger.error(f"Error in batch delete: {e}")
            raise
    
    def _execution_to_dynamodb_item(self, execution: ExecutionState) -> Dict[str, Any]:
        """Converte ExecutionState para item DynamoDB."""
        return {
            'pk': execution.account_id,
            'sk': f"EXEC#{execution.execution_id}",
            'gsi1pk': f"STATUS#{execution.status.value}",
            'gsi1sk': execution.last_updated.isoformat(),
            'execution_id': execution.execution_id,
            'account_id': execution.account_id,
            'started_at': execution.started_at.isoformat(),
            'last_updated': execution.last_updated.isoformat(),
            'status': execution.status.value,
            'metadata': execution.metadata,
            'record_type': 'EXECUTION',
            'ttl': int((datetime.now() + timedelta(days=30)).timestamp())  # TTL de 30 dias
        }
    
    def _task_to_dynamodb_item(self, account_id: str, task: TaskState) -> Dict[str, Any]:
        """Converte TaskState para item DynamoDB."""
        item = {
            'pk': account_id,
            'sk': f"TASK#{task.task_id}",
            'task_id': task.task_id,
            'task_type': task.task_type.value,
            'status': task.status.value,
            'retry_count': task.retry_count,
            'record_type': 'TASK',
            'ttl': int((datetime.now() + timedelta(days=30)).timestamp())  # TTL de 30 dias
        }
        
        if task.started_at:
            item['started_at'] = task.started_at.isoformat()
        if task.completed_at:
            item['completed_at'] = task.completed_at.isoformat()
        if task.error_message:
            item['error_message'] = task.error_message
        if task.result_data:
            # Converte para formato DynamoDB (substitui float por Decimal)
            item['result_data'] = self._convert_floats_to_decimal(task.result_data)
        if task.checksum:
            item['checksum'] = task.checksum
        
        return item
    
    def _dynamodb_item_to_execution(self, item: Dict[str, Any]) -> ExecutionState:
        """Converte item DynamoDB para ExecutionState."""
        return ExecutionState(
            execution_id=item['execution_id'],
            account_id=item['account_id'],
            started_at=datetime.fromisoformat(item['started_at']),
            last_updated=datetime.fromisoformat(item['last_updated']),
            status=ExecutionStatus(item['status']),
            tasks={},  # Será preenchido separadamente
            metadata=item.get('metadata', {})
        )
    
    def _dynamodb_item_to_task(self, item: Dict[str, Any]) -> TaskState:
        """Converte item DynamoDB para TaskState."""
        task = TaskState(
            task_id=item['task_id'],
            task_type=TaskType(item['task_type']),
            status=ExecutionStatus(item['status']),
            retry_count=item.get('retry_count', 0),
            error_message=item.get('error_message'),
            checksum=item.get('checksum')
        )
        
        if 'started_at' in item:
            task.started_at = datetime.fromisoformat(item['started_at'])
        if 'completed_at' in item:
            task.completed_at = datetime.fromisoformat(item['completed_at'])
        if 'result_data' in item:
            # Converte Decimal de volta para float
            task.result_data = self._convert_decimals_to_float(item['result_data'])
        
        return task
    
    def _update_latest_execution_reference(self, execution: ExecutionState):
        """Atualiza referência da última execução."""
        try:
            self.table.put_item(
                Item={
                    'pk': execution.account_id,
                    'sk': 'LATEST',
                    'execution_id': execution.execution_id,
                    'last_updated': execution.last_updated.isoformat(),
                    'status': execution.status.value,
                    'record_type': 'LATEST_REFERENCE'
                }
            )
        except ClientError as e:
            self.logger.error(f"Error updating latest execution reference: {e}")
    
    def _convert_floats_to_decimal(self, data: Any) -> Any:
        """Converte floats para Decimal para compatibilidade com DynamoDB."""
        if isinstance(data, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_floats_to_decimal(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        else:
            return data
    
    def _convert_decimals_to_float(self, data: Any) -> Any:
        """Converte Decimals de volta para float."""
        if isinstance(data, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals_to_float(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data
    
    def get_execution_progress(self, account_id: str, execution_id: str) -> Dict[str, Any]:
        """
        Retorna progresso detalhado de uma execução.
        
        Args:
            account_id: ID da conta AWS
            execution_id: ID da execução
            
        Returns:
            Dict com informações de progresso
        """
        execution = self.get_execution_state(account_id, execution_id)
        if not execution:
            return {}
        
        tasks = list(execution.tasks.values())
        completed_tasks = [t for t in tasks if t.status == ExecutionStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == ExecutionStatus.FAILED]
        running_tasks = [t for t in tasks if t.status == ExecutionStatus.RUNNING]
        pending_tasks = [t for t in tasks if t.status == ExecutionStatus.PENDING]
        
        total_tasks = len(tasks)
        completion_percentage = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'execution_id': execution.execution_id,
            'account_id': execution.account_id,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat(),
            'last_updated': execution.last_updated.isoformat(),
            'total_tasks': total_tasks,
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'running_tasks': len(running_tasks),
            'pending_tasks': len(pending_tasks),
            'completion_percentage': round(completion_percentage, 2),
            'tasks_by_type': {
                task_type.value: {
                    'total': len([t for t in tasks if t.task_type == task_type]),
                    'completed': len([t for t in completed_tasks if t.task_type == task_type]),
                    'failed': len([t for t in failed_tasks if t.task_type == task_type]),
                    'running': len([t for t in running_tasks if t.task_type == task_type]),
                    'pending': len([t for t in pending_tasks if t.task_type == task_type])
                }
                for task_type in TaskType
            }
        }