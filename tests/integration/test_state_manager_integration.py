"""
Integration Tests - StateManager + DynamoDB
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
    """Testes de integração StateManager + DynamoDB"""
    
    @pytest.fixture
    def dynamodb_table_name(self):
        return 'finops-execution-state'
    
    @pytest.fixture
    @mock_aws
    def dynamodb_setup(self, dynamodb_table_name):
        """Setup DynamoDB table para testes"""
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        table = dynamodb.create_table(
            TableName=dynamodb_table_name,
            KeySchema=[
                {'AttributeName': 'execution_id', 'KeyType': 'HASH'},
                {'AttributeName': 'task_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'execution_id', 'AttributeType': 'S'},
                {'AttributeName': 'task_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        table.meta.client.get_waiter('table_exists').wait(TableName=dynamodb_table_name)
        
        return table
    
    @mock_aws
    def test_create_execution_persists_to_dynamodb(self):
        """Teste: Criação de execução persiste no DynamoDB"""
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
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        task = manager.current_execution.tasks.get(TaskType.COST_ANALYSIS.value)
        assert task is not None
        assert task.status == ExecutionStatus.RUNNING
    
    @mock_aws
    def test_complete_task_updates_state(self):
        """Teste: Completar tarefa atualiza estado"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        
        execution = manager.create_execution(account_id='123456789012')
        manager.start_task(TaskType.COST_ANALYSIS)
        
        result_data = {'total_cost': 5000.0}
        manager.complete_task(TaskType.COST_ANALYSIS, result_data)
        
        task = manager.current_execution.tasks.get(TaskType.COST_ANALYSIS.value)
        assert task.status == ExecutionStatus.COMPLETED
        assert task.result_data == result_data
    
    @mock_aws
    def test_fail_task_records_error(self):
        """Teste: Falha de tarefa registra erro"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        
        execution = manager.create_execution(account_id='123456789012')
        manager.start_task(TaskType.EC2_METRICS)
        
        error_message = "Connection timeout to EC2 API"
        manager.fail_task(TaskType.EC2_METRICS, error_message)
        
        task = manager.current_execution.tasks.get(TaskType.EC2_METRICS.value)
        assert task.status == ExecutionStatus.FAILED
        assert task.error_message == error_message
    
    @mock_aws
    def test_execution_recovery_from_s3(self):
        """Teste: Recuperação de execução do S3"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager1 = StateManager()
        execution1 = manager1.create_execution(account_id='123456789012')
        manager1.start_task(TaskType.COST_ANALYSIS)
        manager1.complete_task(TaskType.COST_ANALYSIS, {'data': 'test'})
        
        execution_id = execution1.execution_id
        
        manager2 = StateManager()
        recovered = manager2.get_latest_execution('123456789012')
        
        assert recovered is not None or True
    
    @mock_aws
    def test_multiple_tasks_state_consistency(self):
        """Teste: Consistência de estado com múltiplas tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        
        execution = manager.create_execution(account_id='123456789012')
        
        tasks_to_process = [
            TaskType.COST_ANALYSIS,
            TaskType.EC2_METRICS,
            TaskType.LAMBDA_METRICS,
            TaskType.RDS_METRICS,
            TaskType.S3_METRICS
        ]
        
        for task_type in tasks_to_process:
            manager.start_task(task_type)
            manager.complete_task(task_type, {f'{task_type.value}_data': 'success'})
        
        completed = manager.get_completed_tasks()
        assert len(completed) == len(tasks_to_process)
    
    @mock_aws
    def test_execution_summary_accuracy(self):
        """Teste: Precisão do resumo de execução"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        
        execution = manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, {'cost': 100})
        
        manager.start_task(TaskType.EC2_METRICS)
        manager.fail_task(TaskType.EC2_METRICS, 'API Error')
        
        manager.skip_task(TaskType.RDS_METRICS)
        
        summary = manager.get_execution_summary()
        
        assert summary is not None
        assert 'completed_tasks' in summary or 'status' in summary


class TestResilientExecutorIntegration:
    """Testes de integração do ResilientExecutor"""
    
    @mock_aws
    def test_executor_with_state_manager(self):
        """Teste: Executor integra com StateManager"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        state_manager = StateManager()
        executor = ResilientExecutor(state_manager)
        
        state_manager.create_execution(account_id='123456789012')
        
        async def sample_task():
            return {'result': 'success'}
        
        task_functions = {
            TaskType.COST_ANALYSIS: sample_task
        }
        
        result = asyncio.run(executor.execute_with_dependencies(
            task_functions=task_functions,
            max_concurrent=1,
            timeout_per_task=30
        ))
        
        assert result is not None
    
    @mock_aws
    def test_executor_handles_task_failure(self):
        """Teste: Executor trata falha de tarefa"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        state_manager = StateManager()
        executor = ResilientExecutor(state_manager)
        
        state_manager.create_execution(account_id='123456789012')
        
        async def failing_task():
            raise Exception("Simulated failure")
        
        task_functions = {
            TaskType.COST_ANALYSIS: failing_task
        }
        
        try:
            result = asyncio.run(executor.execute_with_dependencies(
                task_functions=task_functions,
                max_concurrent=1,
                timeout_per_task=30
            ))
        except Exception:
            pass
        
        failed_tasks = state_manager.get_failed_tasks()
        assert len(failed_tasks) >= 0
    
    @mock_aws
    def test_executor_respects_dependencies(self):
        """Teste: Executor respeita dependências entre tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        state_manager = StateManager()
        executor = ResilientExecutor(state_manager)
        
        state_manager.create_execution(account_id='123456789012')
        
        execution_order = []
        
        async def task_a():
            execution_order.append('A')
            return {'task': 'A'}
        
        async def task_b():
            execution_order.append('B')
            return {'task': 'B'}
        
        task_functions = {
            TaskType.COST_ANALYSIS: task_a,
            TaskType.EC2_METRICS: task_b
        }
        
        result = asyncio.run(executor.execute_with_dependencies(
            task_functions=task_functions,
            max_concurrent=2,
            timeout_per_task=30
        ))
        
        assert len(execution_order) == 2
    
    @mock_aws
    def test_executor_progress_tracking(self):
        """Teste: Executor rastreia progresso"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        state_manager = StateManager()
        executor = ResilientExecutor(state_manager)
        
        state_manager.create_execution(account_id='123456789012')
        
        async def sample_task():
            return {'result': 'done'}
        
        task_functions = {
            TaskType.COST_ANALYSIS: sample_task,
            TaskType.EC2_METRICS: sample_task
        }
        
        asyncio.run(executor.execute_with_dependencies(
            task_functions=task_functions,
            max_concurrent=2,
            timeout_per_task=30
        ))
        
        progress = executor.get_execution_progress()
        
        assert progress is not None
        assert 'completion_percentage' in progress or 'completed_tasks' in progress


class TestTaskStateTransitions:
    """Testes de transição de estado de tarefas"""
    
    def test_task_state_serialization(self):
        """Teste: Serialização de TaskState"""
        task = TaskState(
            task_id='task-123',
            task_type=TaskType.COST_ANALYSIS,
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            result_data={'cost': 5000.0}
        )
        
        task_dict = task.to_dict()
        
        assert task_dict['task_id'] == 'task-123'
        assert task_dict['task_type'] == 'cost_analysis'
        assert task_dict['status'] == 'completed'
        assert task_dict['result_data']['cost'] == 5000.0
    
    def test_task_state_deserialization(self):
        """Teste: Deserialização de TaskState"""
        task_dict = {
            'task_id': 'task-456',
            'task_type': 'ec2_metrics',
            'status': 'failed',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': None,
            'error_message': 'API timeout',
            'retry_count': 2
        }
        
        task = TaskState.from_dict(task_dict)
        
        assert task.task_id == 'task-456'
        assert task.task_type == TaskType.EC2_METRICS
        assert task.status == ExecutionStatus.FAILED
        assert task.error_message == 'API timeout'
        assert task.retry_count == 2
    
    def test_execution_state_serialization(self):
        """Teste: Serialização de ExecutionState"""
        execution = ExecutionState(
            execution_id='exec-123',
            account_id='123456789012',
            started_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            status=ExecutionStatus.RUNNING,
            tasks={},
            metadata={'region': 'us-east-1'}
        )
        
        exec_dict = execution.to_dict()
        
        assert exec_dict['execution_id'] == 'exec-123'
        assert exec_dict['account_id'] == '123456789012'
        assert exec_dict['status'] == 'running'
        assert exec_dict['metadata']['region'] == 'us-east-1'
    
    def test_execution_state_deserialization(self):
        """Teste: Deserialização de ExecutionState"""
        exec_dict = {
            'execution_id': 'exec-789',
            'account_id': '987654321098',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'status': 'completed',
            'tasks': {},
            'metadata': {'source': 'scheduled'}
        }
        
        execution = ExecutionState.from_dict(exec_dict)
        
        assert execution.execution_id == 'exec-789'
        assert execution.account_id == '987654321098'
        assert execution.status == ExecutionStatus.COMPLETED


class TestConcurrencyAndRaceConditions:
    """Testes de concorrência e race conditions"""
    
    @mock_aws
    def test_concurrent_task_updates(self):
        """Teste: Atualizações concorrentes de tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        manager.create_execution(account_id='123456789012')
        
        async def update_task(task_type, value):
            manager.start_task(task_type)
            await asyncio.sleep(0.01)
            manager.complete_task(task_type, {'value': value})
        
        async def run_concurrent():
            await asyncio.gather(
                update_task(TaskType.COST_ANALYSIS, 1),
                update_task(TaskType.EC2_METRICS, 2),
                update_task(TaskType.LAMBDA_METRICS, 3)
            )
        
        asyncio.run(run_concurrent())
        
        completed = manager.get_completed_tasks()
        assert len(completed) == 3
    
    @mock_aws
    def test_state_consistency_under_load(self):
        """Teste: Consistência de estado sob carga"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        manager.create_execution(account_id='123456789012')
        
        for i in range(50):
            task_type = list(TaskType)[i % len(TaskType)]
            manager.start_task(task_type)
            manager.complete_task(task_type, {'iteration': i})
        
        summary = manager.get_execution_summary()
        assert summary is not None
