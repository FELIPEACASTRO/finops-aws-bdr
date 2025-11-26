"""
Testes para o StateManager
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3
import json

from src.finops_aws.core.state_manager import (
    StateManager, ExecutionState, TaskState, ExecutionStatus, TaskType
)


@mock_aws
class TestStateManager:
    """Testes para StateManager"""

    def setup_method(self, method):
        """Setup para cada teste"""
        # Criar bucket S3 mock
        self.bucket_name = 'test-finops-state'
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket=self.bucket_name)

        self.state_manager = StateManager(self.bucket_name)
        self.account_id = '123456789012'

    def test_create_new_execution(self):
        """Testa criação de nova execução"""
        metadata = {'test': 'data'}

        execution = self.state_manager.create_execution(self.account_id, metadata)

        assert execution.account_id == self.account_id
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.metadata == metadata
        assert len(execution.tasks) > 0
        assert self.state_manager.current_execution == execution

    def test_save_and_load_execution_state(self):
        """Testa salvamento e carregamento de estado"""
        execution = self.state_manager.create_execution(self.account_id)
        execution_id = execution.execution_id

        # Modifica estado
        execution.metadata['modified'] = True
        self.state_manager.save_execution_state(execution)

        # Carrega estado
        loaded_execution = self.state_manager.get_execution_state(execution_id)

        assert loaded_execution is not None
        assert loaded_execution.execution_id == execution_id
        assert loaded_execution.metadata['modified'] is True

    def test_get_latest_execution(self):
        """Testa obtenção da última execução"""
        execution = self.state_manager.create_execution(self.account_id)

        latest = self.state_manager.get_latest_execution(self.account_id)

        assert latest is not None
        assert latest.execution_id == execution.execution_id

    def test_start_task(self):
        """Testa início de tarefa"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        task = self.state_manager.start_task(task_id)

        assert task.status == ExecutionStatus.RUNNING
        assert task.started_at is not None
        assert task.retry_count == 1

    def test_complete_task(self):
        """Testa conclusão de tarefa"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        self.state_manager.start_task(task_id)
        result_data = {'result': 'success'}

        task = self.state_manager.complete_task(task_id, result_data)

        assert task.status == ExecutionStatus.COMPLETED
        assert task.completed_at is not None
        assert task.result_data == result_data
        assert task.checksum is not None

    def test_fail_task(self):
        """Testa falha de tarefa"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        self.state_manager.start_task(task_id)
        error_message = 'Test error'

        task = self.state_manager.fail_task(task_id, error_message)

        assert task.status == ExecutionStatus.FAILED
        assert task.error_message == error_message

    def test_skip_task(self):
        """Testa pular tarefa"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        reason = 'Test skip'
        task = self.state_manager.skip_task(task_id, reason)

        assert task.status == ExecutionStatus.SKIPPED
        assert task.error_message == reason

    def test_get_pending_tasks(self):
        """Testa obtenção de tarefas pendentes"""
        execution = self.state_manager.create_execution(self.account_id)

        pending_tasks = self.state_manager.get_pending_tasks()

        assert len(pending_tasks) > 0
        assert all(task.status == ExecutionStatus.PENDING for task in pending_tasks)

    def test_get_failed_tasks(self):
        """Testa obtenção de tarefas falhadas"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        self.state_manager.start_task(task_id)
        self.state_manager.fail_task(task_id, 'Test error')

        failed_tasks = self.state_manager.get_failed_tasks()

        assert len(failed_tasks) == 1
        assert failed_tasks[0].status == ExecutionStatus.FAILED

    def test_get_completed_tasks(self):
        """Testa obtenção de tarefas concluídas"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        self.state_manager.start_task(task_id)
        self.state_manager.complete_task(task_id, {'result': 'success'})

        completed_tasks = self.state_manager.get_completed_tasks()

        assert len(completed_tasks) == 1
        assert completed_tasks[0].status == ExecutionStatus.COMPLETED

    def test_is_execution_complete(self):
        """Testa verificação de execução completa"""
        execution = self.state_manager.create_execution(self.account_id)

        # Inicialmente não está completa
        assert not self.state_manager.is_execution_complete()

        # Completa todas as tarefas
        for task_id in execution.tasks.keys():
            self.state_manager.start_task(task_id)
            self.state_manager.complete_task(task_id, {'result': 'success'})

        # Agora está completa
        assert self.state_manager.is_execution_complete()

    def test_complete_execution(self):
        """Testa conclusão de execução"""
        execution = self.state_manager.create_execution(self.account_id)

        completed_execution = self.state_manager.complete_execution()

        assert completed_execution.status == ExecutionStatus.COMPLETED

    def test_get_execution_summary(self):
        """Testa obtenção de resumo da execução"""
        execution = self.state_manager.create_execution(self.account_id)
        task_id = list(execution.tasks.keys())[0]

        # Completa uma tarefa
        self.state_manager.start_task(task_id)
        self.state_manager.complete_task(task_id, {'result': 'success'})

        summary = self.state_manager.get_execution_summary()

        assert 'execution_id' in summary
        assert 'account_id' in summary
        assert 'total_tasks' in summary
        assert 'completed_tasks' in summary
        assert 'completion_percentage' in summary
        assert summary['completed_tasks'] == 1

    def test_resume_existing_execution(self):
        """Testa retomada de execução existente"""
        # Cria execução inicial
        execution1 = self.state_manager.create_execution(self.account_id)
        execution1_id = execution1.execution_id

        # Cria novo state manager (simula nova instância)
        new_state_manager = StateManager(self.bucket_name)

        # Tenta criar nova execução (deve retomar a existente)
        execution2 = new_state_manager.create_execution(self.account_id)

        assert execution2.execution_id == execution1_id

    def test_resume_old_execution_creates_new(self):
        """Testa que execução muito antiga cria nova"""
        execution = self.state_manager.create_execution(self.account_id)

        # Simula execução muito antiga (>2 horas)
        old_time = datetime.now() - timedelta(hours=3)
        execution.last_updated = old_time
        self.state_manager.save_execution_state(execution)

        # Cria novo state manager
        new_state_manager = StateManager(self.bucket_name)

        # Deve criar nova execução
        new_execution = new_state_manager.create_execution(self.account_id)

        assert new_execution.execution_id != execution.execution_id

    def test_task_state_serialization(self):
        """Testa serialização de TaskState"""
        task = TaskState(
            task_id='test-task',
            task_type=TaskType.COST_ANALYSIS,
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result_data={'test': 'data'}
        )

        # Serializa
        task_dict = task.to_dict()

        # Deserializa
        restored_task = TaskState.from_dict(task_dict)

        assert restored_task.task_id == task.task_id
        assert restored_task.task_type == task.task_type
        assert restored_task.status == task.status
        assert restored_task.result_data == task.result_data

    def test_execution_state_serialization(self):
        """Testa serialização de ExecutionState"""
        execution = self.state_manager.create_execution(self.account_id)

        # Serializa
        execution_dict = execution.to_dict()

        # Deserializa
        restored_execution = ExecutionState.from_dict(execution_dict)

        assert restored_execution.execution_id == execution.execution_id
        assert restored_execution.account_id == execution.account_id
        assert restored_execution.status == execution.status
        assert len(restored_execution.tasks) == len(execution.tasks)
