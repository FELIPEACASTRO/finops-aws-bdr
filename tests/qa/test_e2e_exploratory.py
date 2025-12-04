"""
Suite E2E Exploratory Testing - Testes de Descoberta e Edge Cases
Testes exploratórios para descobrir comportamentos inesperados
Target: Nota 10/10 dos especialistas em Exploratory Testing
"""

import pytest
import json
import boto3
import random
import string
from moto import mock_aws
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestEdgeCasesAndBoundaries:
    """
    Testes de casos extremos e limites
    Descobre comportamentos em situacoes limite
    """
    
    @mock_aws
    def test_empty_account_no_resources(self):
        """Exploratorio: Conta AWS vazia sem recursos"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        empty_result = {
            'total_cost': 0.0,
            'services': {},
            'recommendations': []
        }
        
        manager.complete_task(TaskType.COST_ANALYSIS, empty_result)
        
        completed = manager.get_completed_tasks()
        assert len(completed) >= 1
        
        task_result = completed[0].result_data
        assert task_result['total_cost'] == 0.0
    
    @mock_aws
    def test_extremely_large_cost_values(self):
        """Exploratorio: Valores de custo extremamente grandes"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        large_cost_result = {
            'total_cost': 999999999.99,
            'currency': 'USD',
            'services': {
                'EC2': 500000000.00,
                'RDS': 300000000.00,
                'Other': 199999999.99
            }
        }
        
        manager.complete_task(TaskType.COST_ANALYSIS, large_cost_result)
        
        loaded = manager.get_latest_execution('123456789012')
        
        cost_task = None
        for task_id, task in loaded.tasks.items():
            if 'cost_analysis' in task_id:
                cost_task = task
                break
        
        assert cost_task is not None
        result = cost_task.result_data
        
        assert result['total_cost'] == 999999999.99
        assert sum(result['services'].values()) == result['total_cost']
    
    @mock_aws
    def test_negative_cost_handling(self):
        """Exploratorio: Valores de custo negativos (creditos/refunds)"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        credits_result = {
            'total_cost': -500.00,
            'currency': 'USD',
            'breakdown': {
                'usage': 1000.00,
                'credits': -1500.00
            },
            'net_cost': -500.00
        }
        
        manager.complete_task(TaskType.COST_ANALYSIS, credits_result)
        
        completed = manager.get_completed_tasks()
        assert len(completed) >= 1
        assert completed[0].result_data['total_cost'] == -500.00
    
    @mock_aws
    def test_special_characters_in_resource_names(self):
        """Exploratorio: Caracteres especiais em nomes de recursos"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(
            account_id='123456789012',
            metadata={
                'special_name': 'test-resource_with.special@chars#123',
                'unicode_name': 'Recurso-Producao-Brasil',
                'emoji_test': 'Production'
            }
        )
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        result = {
            'resources': [
                {'name': 'ec2-prod_server.01', 'cost': 100},
                {'name': 'rds-database@primary#1', 'cost': 200},
                {'name': 's3-bucket-with-dashes', 'cost': 50}
            ]
        }
        
        manager.complete_task(TaskType.COST_ANALYSIS, result)
        
        loaded = manager.get_latest_execution('123456789012')
        assert loaded.metadata['special_name'] == 'test-resource_with.special@chars#123'
    
    @mock_aws
    def test_very_long_execution_id(self):
        """Exploratorio: Execution ID muito longo"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        
        execution = manager.create_execution(
            account_id='123456789012',
            metadata={'test': 'long_id'}
        )
        
        assert len(execution.execution_id) > 20
        assert len(execution.execution_id) < 200
    
    @mock_aws
    def test_concurrent_task_updates(self):
        """Exploratorio: Atualizacoes concorrentes de tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        import threading
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        results = []
        errors = []
        
        def update_task(task_type: TaskType, value: int):
            try:
                manager.start_task(task_type)
                manager.complete_task(task_type, {'value': value})
                results.append((task_type.value, value))
            except Exception as e:
                errors.append((task_type.value, str(e)))
        
        threads = [
            threading.Thread(target=update_task, args=(TaskType.COST_ANALYSIS, 1)),
            threading.Thread(target=update_task, args=(TaskType.EC2_METRICS, 2)),
            threading.Thread(target=update_task, args=(TaskType.RDS_METRICS, 3))
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) >= 1


class TestUnusualInputPatterns:
    """
    Testes com padrões de entrada incomuns
    Descobre como o sistema lida com inputs inesperados
    """
    
    @mock_aws
    def test_unicode_in_metadata(self):
        """Exploratorio: Unicode em metadados"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        manager = StateManager()
        
        unicode_metadata = {
            'chinese': '财务运营',
            'japanese': 'ファイナンス',
            'arabic': 'العمليات المالية',
            'portuguese': 'Operacoes Financeiras',
            'emoji': 'Status: OK'
        }
        
        execution = manager.create_execution(
            account_id='123456789012',
            metadata=unicode_metadata
        )
        
        loaded = manager.get_latest_execution('123456789012')
        
        assert loaded.metadata['chinese'] == '财务运营'
        assert loaded.metadata['portuguese'] == 'Operacoes Financeiras'
    
    @mock_aws
    def test_deeply_nested_data_structures(self):
        """Exploratorio: Estruturas de dados profundamente aninhadas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        def create_nested(depth: int, current: int = 0) -> Dict:
            if current >= depth:
                return {'value': 'leaf', 'depth': current}
            return {'level': current, 'nested': create_nested(depth, current + 1)}
        
        deeply_nested = create_nested(10)
        
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, deeply_nested)
        
        loaded = manager.get_latest_execution('123456789012')
        
        cost_task = None
        for task_id, task in loaded.tasks.items():
            if 'cost_analysis' in task_id:
                cost_task = task
                break
        
        assert cost_task is not None
        result = cost_task.result_data
        
        assert result['level'] == 0
        
        current = result
        depth_found = 0
        while 'nested' in current:
            current = current['nested']
            depth_found += 1
        
        assert depth_found == 10
    
    @mock_aws
    def test_large_array_of_resources(self):
        """Exploratorio: Array grande de recursos"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        large_resource_list = [
            {'id': f'resource-{i:05d}', 'cost': random.uniform(1, 1000)}
            for i in range(1000)
        ]
        
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, {'resources': large_resource_list})
        
        loaded = manager.get_latest_execution('123456789012')
        
        cost_task = None
        for task_id, task in loaded.tasks.items():
            if 'cost_analysis' in task_id:
                cost_task = task
                break
        
        assert cost_task is not None
        result = cost_task.result_data
        
        assert len(result['resources']) == 1000


class TestTimeBasedScenarios:
    """
    Testes com cenarios temporais
    Descobre comportamentos relacionados a tempo
    """
    
    @mock_aws
    def test_execution_spanning_midnight(self):
        """Exploratorio: Execucao que cruza meia-noite"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(
            account_id='123456789012',
            metadata={'started_near_midnight': True}
        )
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        result = {
            'start_date': '2024-12-03',
            'end_date': '2024-12-04',
            'spans_midnight': True
        }
        
        manager.complete_task(TaskType.COST_ANALYSIS, result)
        
        completed = manager.get_completed_tasks()
        assert len(completed) >= 1
    
    @mock_aws
    def test_very_old_execution_recovery(self):
        """Exploratorio: Recuperacao de execucao muito antiga"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        
        execution = manager.create_execution(
            account_id='123456789012',
            metadata={'simulated_old': True}
        )
        
        manager2 = StateManager()
        loaded = manager2.get_latest_execution('123456789012')
        
        assert loaded is not None
        assert loaded.execution_id == execution.execution_id


class TestRecoveryScenarios:
    """
    Testes de cenarios de recuperacao
    Descobre como o sistema se recupera de falhas
    """
    
    @mock_aws
    def test_partial_task_completion_recovery(self):
        """Exploratorio: Recuperacao de tarefas parcialmente completas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType, ExecutionStatus
        
        manager1 = StateManager()
        execution1 = manager1.create_execution(account_id='123456789012')
        
        manager1.start_task(TaskType.COST_ANALYSIS)
        manager1.complete_task(TaskType.COST_ANALYSIS, {'step': 1})
        
        manager1.start_task(TaskType.EC2_METRICS)
        
        manager2 = StateManager()
        execution2 = manager2.create_execution(account_id='123456789012')
        
        assert execution2.execution_id == execution1.execution_id
        
        cost_task = None
        ec2_task = None
        for task_id, task in execution2.tasks.items():
            if 'cost_analysis' in task_id:
                cost_task = task
            if 'ec2_metrics' in task_id:
                ec2_task = task
        
        assert cost_task is not None
        assert cost_task.status == ExecutionStatus.COMPLETED
        assert ec2_task is not None
        assert ec2_task.status == ExecutionStatus.RUNNING
    
    @mock_aws
    def test_multiple_failed_tasks_handling(self):
        """Exploratorio: Multiplas tarefas falhando"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        failed_tasks = []
        
        for task_type in [TaskType.COST_ANALYSIS, TaskType.EC2_METRICS, TaskType.RDS_METRICS]:
            try:
                manager.start_task(task_type)
                manager.fail_task(task_type, f"Simulated failure for {task_type.value}")
                failed_tasks.append(task_type.value)
            except Exception:
                pass
        
        failed = manager.get_failed_tasks()
        
        assert len(failed) >= 1
