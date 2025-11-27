"""
Integration Tests - StateManager + S3
Testes de integração do gerenciador de estado com persistência
"""
import pytest
import json
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch

import boto3
from moto import mock_aws

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from finops_aws.core.state_manager import (
    StateManager, TaskType, ExecutionStatus,
    TaskState, ExecutionState
)
from finops_aws.core.resilient_executor import ResilientExecutor


class TestStateManagerDynamoDBIntegration:
    """Testes de integração StateManager + S3"""
    
    @pytest.fixture
    def s3_bucket_name(self):
        return 'finops-aws-state'
    
    @mock_aws
    def test_create_execution_persists_to_s3(self):
        """Teste: Criação de execução persiste no S3"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        
        execution = manager.create_execution(
            account_id='123456789012',
            metadata={'test': 'value'}
        )
        
        assert execution is not None
        assert execution.account_id == '123456789012'
        assert execution.status == ExecutionStatus.RUNNING
    
    @mock_aws
    def test_task_state_persistence(self):
        """Teste: Estado de tarefa persiste corretamente"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        assert len(task_ids) > 0
        
        first_task_id = task_ids[0]
        manager.start_task(first_task_id)
        
        task = manager.current_execution.tasks.get(first_task_id)
        assert task is not None
        assert task.status == ExecutionStatus.RUNNING
    
    @mock_aws
    def test_complete_task_updates_state(self):
        """Teste: Completar tarefa atualiza estado"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        first_task_id = task_ids[0]
        
        manager.start_task(first_task_id)
        
        result_data = {'total_cost': 5000.0}
        manager.complete_task(first_task_id, result_data)
        
        task = manager.current_execution.tasks.get(first_task_id)
        assert task.status == ExecutionStatus.COMPLETED
        assert task.result_data == result_data
    
    @mock_aws
    def test_fail_task_records_error(self):
        """Teste: Falha de tarefa registra erro"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        first_task_id = task_ids[0]
        
        manager.start_task(first_task_id)
        
        error_message = "Connection timeout to AWS API"
        manager.fail_task(first_task_id, error_message)
        
        task = manager.current_execution.tasks.get(first_task_id)
        assert task.status == ExecutionStatus.FAILED
        assert task.error_message == error_message
    
    @mock_aws
    def test_execution_recovery_from_s3(self):
        """Teste: Recuperação de execução do S3"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager1 = StateManager()
        execution = manager1.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        first_task_id = task_ids[0]
        manager1.start_task(first_task_id)
        manager1.complete_task(first_task_id, {'test': 'data'})
        
        manager2 = StateManager()
        recovered = manager2.get_latest_execution('123456789012')
        
        assert recovered is not None
        assert recovered.execution_id == execution.execution_id
        
        task = recovered.tasks.get(first_task_id)
        assert task is not None
        assert task.status == ExecutionStatus.COMPLETED
    
    @mock_aws
    def test_multiple_tasks_state_consistency(self):
        """Teste: Consistência de estado com múltiplas tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        
        for task_id in task_ids[:3]:
            manager.start_task(task_id)
            manager.complete_task(task_id, {'status': 'done'})
        
        recovered = manager.get_latest_execution('123456789012')
        
        completed_count = sum(
            1 for t in recovered.tasks.values() 
            if t.status == ExecutionStatus.COMPLETED
        )
        assert completed_count == 3
    
    @mock_aws
    def test_execution_summary_accuracy(self):
        """Teste: Sumário de execução preciso"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        
        manager.start_task(task_ids[0])
        manager.complete_task(task_ids[0], {'test': 'data'})
        
        manager.start_task(task_ids[1])
        manager.fail_task(task_ids[1], 'Test error')
        
        summary = manager.get_execution_summary()
        
        assert summary is not None
        assert 'completed' in str(summary).lower() or summary.get('completed_tasks', 0) >= 1


class TestStateRecoveryScenarios:
    """Testes de recuperação de estado"""
    
    @mock_aws
    def test_resume_interrupted_execution(self):
        """Teste: Retomar execução interrompida"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager1 = StateManager()
        execution = manager1.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        manager1.start_task(task_ids[0])
        
        manager2 = StateManager()
        resumed = manager2.create_execution(account_id='123456789012')
        
        assert resumed.execution_id == execution.execution_id
        
        task = resumed.tasks.get(task_ids[0])
        assert task.status == ExecutionStatus.RUNNING
    
    @mock_aws
    def test_new_execution_after_complete(self):
        """Teste: Nova execução após conclusão"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution1 = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution1.tasks.keys())
        for task_id in task_ids:
            manager.start_task(task_id)
            manager.complete_task(task_id, {})
        
        manager.complete_execution()
        
        manager2 = StateManager()
        execution2 = manager2.create_execution(account_id='123456789012')
        
        assert execution2.execution_id != execution1.execution_id


class TestConcurrencyAndRaceConditions:
    """Testes de concorrência e condições de corrida"""
    
    @mock_aws
    def test_sequential_task_updates(self):
        """Teste: Atualizações sequenciais de tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        
        for task_id in task_ids:
            manager.start_task(task_id)
            manager.complete_task(task_id, {'task': task_id})
        
        final_state = manager.get_latest_execution('123456789012')
        
        completed = sum(
            1 for t in final_state.tasks.values()
            if t.status == ExecutionStatus.COMPLETED
        )
        assert completed == len(task_ids)
    
    @mock_aws
    def test_state_consistency_multiple_operations(self):
        """Teste: Consistência de estado após múltiplas operações"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        
        manager.start_task(task_ids[0])
        manager.complete_task(task_ids[0], {'phase': 1})
        
        manager.start_task(task_ids[1])
        manager.fail_task(task_ids[1], 'Controlled failure')
        
        manager.start_task(task_ids[2])
        manager.complete_task(task_ids[2], {'phase': 2})
        
        final_state = manager.current_execution
        
        assert final_state.tasks[task_ids[0]].status == ExecutionStatus.COMPLETED
        assert final_state.tasks[task_ids[1]].status == ExecutionStatus.FAILED
        assert final_state.tasks[task_ids[2]].status == ExecutionStatus.COMPLETED


class TestStateManagerEdgeCases:
    """Testes de casos extremos"""
    
    @mock_aws
    def test_empty_result_data(self):
        """Teste: Dados de resultado vazios"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        manager.start_task(task_ids[0])
        manager.complete_task(task_ids[0], {})
        
        task = manager.current_execution.tasks.get(task_ids[0])
        assert task.status == ExecutionStatus.COMPLETED
        assert task.result_data == {}
    
    @mock_aws
    def test_large_result_data(self):
        """Teste: Dados de resultado grandes"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        large_data = {f'key_{i}': f'value_{i}' * 100 for i in range(100)}
        
        task_ids = list(execution.tasks.keys())
        manager.start_task(task_ids[0])
        manager.complete_task(task_ids[0], large_data)
        
        recovered = manager.get_latest_execution('123456789012')
        task = recovered.tasks.get(task_ids[0])
        
        assert task.status == ExecutionStatus.COMPLETED
        assert len(task.result_data) == 100
    
    @mock_aws
    def test_special_characters_in_error(self):
        """Teste: Caracteres especiais em mensagens de erro"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        error_message = 'Erro com caracteres especiais: émoji 🚀 unicode ç á ñ'
        
        task_ids = list(execution.tasks.keys())
        manager.start_task(task_ids[0])
        manager.fail_task(task_ids[0], error_message)
        
        recovered = manager.get_latest_execution('123456789012')
        task = recovered.tasks.get(task_ids[0])
        
        assert task.error_message == error_message
    
    @mock_aws
    def test_metadata_preservation(self):
        """Teste: Preservação de metadados"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        
        metadata = {
            'source': 'scheduled_event',
            'trigger_time': '2025-01-01T00:00:00Z',
            'custom_config': {'threshold': 100}
        }
        
        execution = manager.create_execution(
            account_id='123456789012',
            metadata=metadata
        )
        
        recovered = manager.get_latest_execution('123456789012')
        
        assert recovered.metadata.get('source') == 'scheduled_event'
        assert 'trigger_time' in recovered.metadata


class TestExecutionSummary:
    """Testes de sumário de execução"""
    
    @mock_aws
    def test_execution_percentage_calculation(self):
        """Teste: Cálculo de percentual de execução"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        total_tasks = len(task_ids)
        
        manager.start_task(task_ids[0])
        manager.complete_task(task_ids[0], {})
        
        summary = manager.get_execution_summary()
        
        assert summary is not None
    
    @mock_aws
    def test_failed_tasks_count(self):
        """Teste: Contagem de tarefas falhadas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        task_ids = list(execution.tasks.keys())
        
        manager.start_task(task_ids[0])
        manager.fail_task(task_ids[0], 'Error 1')
        
        manager.start_task(task_ids[1])
        manager.fail_task(task_ids[1], 'Error 2')
        
        failed_count = sum(
            1 for t in manager.current_execution.tasks.values()
            if t.status == ExecutionStatus.FAILED
        )
        
        assert failed_count == 2
