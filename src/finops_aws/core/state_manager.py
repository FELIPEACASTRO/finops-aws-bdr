"""
Sistema de gerenciamento de estado e recuperação de falhas
Permite que o Lambda continue de onde parou em caso de falha
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import boto3
from botocore.exceptions import ClientError

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ExecutionStatus(Enum):
    """Status de execução de uma tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(Enum):
    """Tipos de tarefas do FinOps"""
    COST_ANALYSIS = "cost_analysis"
    EC2_METRICS = "ec2_metrics"
    LAMBDA_METRICS = "lambda_metrics"
    RDS_METRICS = "rds_metrics"
    S3_METRICS = "s3_metrics"
    EC2_RECOMMENDATIONS = "ec2_recommendations"
    LAMBDA_RECOMMENDATIONS = "lambda_recommendations"
    RDS_RECOMMENDATIONS = "rds_recommendations"
    REPORT_GENERATION = "report_generation"


@dataclass
class TaskState:
    """Estado de uma tarefa individual"""
    task_id: str
    task_type: TaskType
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    result_data: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        data = asdict(self)
        data['task_type'] = self.task_type.value
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskState':
        """Cria TaskState a partir de dicionário"""
        return cls(
            task_id=data['task_id'],
            task_type=TaskType(data['task_type']),
            status=ExecutionStatus(data['status']),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            result_data=data.get('result_data'),
            checksum=data.get('checksum')
        )


@dataclass
class ExecutionState:
    """Estado completo de uma execução"""
    execution_id: str
    account_id: str
    started_at: datetime
    last_updated: datetime
    status: ExecutionStatus
    tasks: Dict[str, TaskState]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            'execution_id': self.execution_id,
            'account_id': self.account_id,
            'started_at': self.started_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'status': self.status.value,
            'tasks': {k: v.to_dict() for k, v in self.tasks.items()},
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionState':
        """Cria ExecutionState a partir de dicionário"""
        return cls(
            execution_id=data['execution_id'],
            account_id=data['account_id'],
            started_at=datetime.fromisoformat(data['started_at']),
            last_updated=datetime.fromisoformat(data['last_updated']),
            status=ExecutionStatus(data['status']),
            tasks={k: TaskState.from_dict(v) for k, v in data['tasks'].items()},
            metadata=data.get('metadata', {})
        )


class StateManager:
    """
    Gerenciador de estado para execuções do FinOps
    Persiste estado no S3 para recuperação em caso de falha
    """

    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv('FINOPS_STATE_BUCKET', 'finops-aws-state')
        self.s3_client = boto3.client('s3')
        self.current_execution: Optional[ExecutionState] = None

    def _generate_execution_id(self, account_id: str) -> str:
        """Gera ID único para execução usando UUID para evitar colisões"""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_suffix = uuid.uuid4().hex[:8]
        return f"exec_{account_id}_{timestamp}_{unique_suffix}"

    def _get_state_key(self, execution_id: str) -> str:
        """Gera chave S3 para o estado"""
        return f"executions/{execution_id}/state.json"

    def _get_latest_execution_key(self, account_id: str) -> str:
        """Gera chave S3 para a última execução"""
        return f"accounts/{account_id}/latest_execution.json"

    def create_execution(self, account_id: str, metadata: Optional[Dict[str, Any]] = None) -> ExecutionState:
        """
        Cria nova execução ou recupera execução em andamento
        
        Args:
            account_id: ID da conta AWS
            metadata: Metadados adicionais
            
        Returns:
            Estado da execução
        """
        # Verifica se existe execução em andamento
        existing_execution = self.get_latest_execution(account_id)
        
        if existing_execution and existing_execution.status == ExecutionStatus.RUNNING:
            # Verifica se a execução não está muito antiga (> 2 horas)
            time_diff = datetime.now() - existing_execution.last_updated
            if time_diff < timedelta(hours=2):
                logger.info(f"Resuming existing execution: {existing_execution.execution_id}")
                self.current_execution = existing_execution
                return existing_execution
            else:
                logger.warning(f"Existing execution {existing_execution.execution_id} is too old, creating new one")

        # Cria nova execução
        execution_id = self._generate_execution_id(account_id)
        now = datetime.now()
        
        execution = ExecutionState(
            execution_id=execution_id,
            account_id=account_id,
            started_at=now,
            last_updated=now,
            status=ExecutionStatus.RUNNING,
            tasks={},
            metadata=metadata or {}
        )

        # Define tarefas padrão
        self._initialize_default_tasks(execution)
        
        # Salva estado inicial
        self.save_execution_state(execution)
        self.current_execution = execution
        
        logger.info(f"Created new execution: {execution_id}")
        return execution

    def _initialize_default_tasks(self, execution: ExecutionState):
        """Inicializa tarefas padrão para uma execução"""
        for task_type in TaskType:
            task_id = f"{task_type.value}_{execution.execution_id}"
            execution.tasks[task_id] = TaskState(
                task_id=task_id,
                task_type=task_type,
                status=ExecutionStatus.PENDING
            )

    def save_execution_state(self, execution: ExecutionState):
        """
        Salva estado da execução no S3
        
        Args:
            execution: Estado da execução
        """
        try:
            # Atualiza timestamp
            execution.last_updated = datetime.now()
            
            # Salva estado completo
            state_key = self._get_state_key(execution.execution_id)
            state_data = json.dumps(execution.to_dict(), indent=2)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=state_key,
                Body=state_data,
                ContentType='application/json'
            )

            # Atualiza referência da última execução
            latest_key = self._get_latest_execution_key(execution.account_id)
            latest_data = json.dumps({
                'execution_id': execution.execution_id,
                'last_updated': execution.last_updated.isoformat(),
                'status': execution.status.value
            })
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=latest_key,
                Body=latest_data,
                ContentType='application/json'
            )

            logger.debug(f"Saved execution state: {execution.execution_id}")

        except ClientError as e:
            logger.error(f"Failed to save execution state: {e}")
            raise

    def get_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        """
        Recupera estado da execução do S3
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Estado da execução ou None se não encontrado
        """
        try:
            state_key = self._get_state_key(execution_id)
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=state_key
            )
            
            state_data = json.loads(response['Body'].read())
            return ExecutionState.from_dict(state_data)

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"Failed to get execution state: {e}")
            raise

    def get_latest_execution(self, account_id: str) -> Optional[ExecutionState]:
        """
        Recupera a última execução para uma conta
        
        Args:
            account_id: ID da conta AWS
            
        Returns:
            Estado da última execução ou None se não encontrado
        """
        try:
            latest_key = self._get_latest_execution_key(account_id)
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=latest_key
            )
            
            latest_data = json.loads(response['Body'].read())
            execution_id = latest_data['execution_id']
            
            return self.get_execution_state(execution_id)

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"Failed to get latest execution: {e}")
            raise

    def _resolve_task_id(self, task_id_or_type) -> str:
        """
        Resolve task_id a partir de string ou TaskType
        
        Args:
            task_id_or_type: ID da tarefa (string) ou TaskType (enum)
            
        Returns:
            task_id resolvido
        """
        if not self.current_execution:
            raise ValueError("No current execution")
        
        if isinstance(task_id_or_type, TaskType):
            for tid, task in self.current_execution.tasks.items():
                if task.task_type == task_id_or_type:
                    return tid
            raise ValueError(f"Task type {task_id_or_type.value} not found")
        
        if task_id_or_type in self.current_execution.tasks:
            return task_id_or_type
        
        for tid, task in self.current_execution.tasks.items():
            if task.task_type.value == task_id_or_type:
                return tid
        
        raise ValueError(f"Task {task_id_or_type} not found")

    def start_task(self, task_id_or_type) -> TaskState:
        """
        Marca tarefa como iniciada
        
        Args:
            task_id_or_type: ID da tarefa (string) ou TaskType (enum)
            
        Returns:
            Estado da tarefa
        """
        if not self.current_execution:
            raise ValueError("No current execution")

        task_id = self._resolve_task_id(task_id_or_type)
        task = self.current_execution.tasks[task_id]
        task.status = ExecutionStatus.RUNNING
        task.started_at = datetime.now()
        task.retry_count += 1

        self.save_execution_state(self.current_execution)
        logger.info(f"Started task: {task_id}")
        
        return task

    def complete_task(self, task_id_or_type, result_data: Optional[Dict[str, Any]] = None) -> TaskState:
        """
        Marca tarefa como concluída
        
        Args:
            task_id_or_type: ID da tarefa (string) ou TaskType (enum)
            result_data: Dados do resultado
            
        Returns:
            Estado da tarefa
        """
        if not self.current_execution:
            raise ValueError("No current execution")

        task_id = self._resolve_task_id(task_id_or_type)
        task = self.current_execution.tasks[task_id]
        task.status = ExecutionStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result_data = result_data
        
        if result_data:
            data_str = json.dumps(result_data, sort_keys=True)
            task.checksum = hashlib.md5(data_str.encode()).hexdigest()

        self.save_execution_state(self.current_execution)
        logger.info(f"Completed task: {task_id}")
        
        return task

    def fail_task(self, task_id_or_type, error_message: str) -> TaskState:
        """
        Marca tarefa como falhada
        
        Args:
            task_id_or_type: ID da tarefa (string) ou TaskType (enum)
            error_message: Mensagem de erro
            
        Returns:
            Estado da tarefa
        """
        if not self.current_execution:
            raise ValueError("No current execution")

        task_id = self._resolve_task_id(task_id_or_type)
        task = self.current_execution.tasks[task_id]
        task.status = ExecutionStatus.FAILED
        task.error_message = error_message

        self.save_execution_state(self.current_execution)
        logger.error(f"Failed task: {task_id} - {error_message}")
        
        return task

    def skip_task(self, task_id_or_type, reason: Optional[str] = None) -> TaskState:
        """
        Marca tarefa como pulada
        
        Args:
            task_id_or_type: ID da tarefa (string) ou TaskType (enum)
            reason: Motivo para pular
            
        Returns:
            Estado da tarefa
        """
        if not self.current_execution:
            raise ValueError("No current execution")

        task_id = self._resolve_task_id(task_id_or_type)
        task = self.current_execution.tasks[task_id]
        task.status = ExecutionStatus.SKIPPED
        task.error_message = reason

        self.save_execution_state(self.current_execution)
        logger.info(f"Skipped task: {task_id} - {reason}")
        
        return task

    def get_pending_tasks(self) -> List[TaskState]:
        """
        Retorna tarefas pendentes
        
        Returns:
            Lista de tarefas pendentes
        """
        if not self.current_execution:
            return []

        return [
            task for task in self.current_execution.tasks.values()
            if task.status == ExecutionStatus.PENDING
        ]

    def get_failed_tasks(self) -> List[TaskState]:
        """
        Retorna tarefas que falharam
        
        Returns:
            Lista de tarefas que falharam
        """
        if not self.current_execution:
            return []

        return [
            task for task in self.current_execution.tasks.values()
            if task.status == ExecutionStatus.FAILED
        ]

    def get_completed_tasks(self) -> List[TaskState]:
        """
        Retorna tarefas concluídas
        
        Returns:
            Lista de tarefas concluídas
        """
        if not self.current_execution:
            return []

        return [
            task for task in self.current_execution.tasks.values()
            if task.status == ExecutionStatus.COMPLETED
        ]

    def is_execution_complete(self) -> bool:
        """
        Verifica se a execução está completa
        
        Returns:
            True se todas as tarefas foram concluídas ou puladas
        """
        if not self.current_execution:
            return False

        for task in self.current_execution.tasks.values():
            if task.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
                return False

        return True

    def complete_execution(self) -> ExecutionState:
        """
        Marca execução como concluída
        
        Returns:
            Estado da execução
        """
        if not self.current_execution:
            raise ValueError("No current execution")

        self.current_execution.status = ExecutionStatus.COMPLETED
        self.save_execution_state(self.current_execution)
        
        logger.info(f"Completed execution: {self.current_execution.execution_id}")
        return self.current_execution

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da execução atual
        
        Returns:
            Resumo da execução
        """
        if not self.current_execution:
            return {}

        completed_tasks = self.get_completed_tasks()
        failed_tasks = self.get_failed_tasks()
        pending_tasks = self.get_pending_tasks()

        return {
            'execution_id': self.current_execution.execution_id,
            'account_id': self.current_execution.account_id,
            'status': self.current_execution.status.value,
            'started_at': self.current_execution.started_at.isoformat(),
            'last_updated': self.current_execution.last_updated.isoformat(),
            'total_tasks': len(self.current_execution.tasks),
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'pending_tasks': len(pending_tasks),
            'completion_percentage': (len(completed_tasks) / len(self.current_execution.tasks)) * 100 if self.current_execution.tasks else 0
        }

    def cleanup_old_executions(self, account_id: str, keep_days: int = 7):
        """
        Remove execuções antigas para economizar espaço
        
        Args:
            account_id: ID da conta AWS
            keep_days: Número de dias para manter
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            prefix = f"executions/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            objects_to_delete = []
            
            for obj in response.get('Contents', []):
                # Parse execution ID from key
                key_parts = obj['Key'].split('/')
                if len(key_parts) >= 2:
                    execution_id = key_parts[1]
                    
                    # Extract date from execution ID
                    try:
                        date_part = execution_id.split('_')[2]  # exec_account_YYYYMMDD_HHMMSS_hash
                        exec_date = datetime.strptime(date_part, '%Y%m%d')
                        
                        if exec_date < cutoff_date:
                            objects_to_delete.append({'Key': obj['Key']})
                    except (IndexError, ValueError):
                        continue

            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                logger.info(f"Cleaned up {len(objects_to_delete)} old execution files")

        except ClientError as e:
            logger.error(f"Failed to cleanup old executions: {e}")