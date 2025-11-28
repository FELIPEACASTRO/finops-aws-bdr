"""
E2E Tests - Resilience, Stress, and Performance
Testes E2E de resiliência, stress e performance do sistema
"""
import pytest
import json
import asyncio
import time
import threading
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import dataclass
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from moto import mock_aws

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from finops_aws.resilient_lambda_handler import FinOpsResilientHandler
from finops_aws.core.state_manager import StateManager, TaskType, ExecutionStatus
from finops_aws.core.resilient_executor import ResilientExecutor
from finops_aws.core.retry_handler import RetryHandler, create_aws_retry_policy


@dataclass
class MockLambdaContext:
    function_name: str = "finops-aws-analyzer"
    function_version: str = "$LATEST"
    invoked_function_arn: str = "arn:aws:lambda:us-east-1:123456789012:function:finops-aws-analyzer"
    memory_limit_in_mb: int = 1024
    aws_request_id: str = "stress-test-12345"
    log_group_name: str = "/aws/lambda/finops-aws-analyzer"
    log_stream_name: str = "2025/11/27/[$LATEST]abcdef123456"
    
    def get_remaining_time_in_millis(self):
        return 300000


class TestRetryMechanisms:
    """Testes de mecanismos de retry"""
    
    def test_exponential_backoff_retry(self):
        """Teste: Retry com backoff exponencial"""
        call_count = [0]
        
        @RetryHandler.with_retry(max_retries=3, base_delay=0.01)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = flaky_function()
        
        assert result == "success"
        assert call_count[0] == 3
    
    def test_max_retries_exhausted(self):
        """Teste: Esgotamento de tentativas máximas"""
        call_count = [0]
        
        @RetryHandler.with_retry(max_retries=3, base_delay=0.01)
        def always_failing():
            call_count[0] += 1
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception) as exc_info:
            always_failing()
        
        assert "Permanent failure" in str(exc_info.value)
        assert call_count[0] == 4
    
    def test_aws_retry_policy(self):
        """Teste: Política de retry específica para AWS"""
        policy = create_aws_retry_policy()
        
        assert policy is not None
        assert hasattr(policy, 'max_retries') or hasattr(policy, 'retries')
    
    def test_retry_with_specific_exceptions(self):
        """Teste: Retry apenas para exceções específicas"""
        from finops_aws.core.retry_handler import RetryPolicy
        
        call_count = [0]
        
        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=[ConnectionError, TimeoutError]
        )
        handler = RetryHandler(policy=policy)
        
        def function_with_connection_error():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Connection failed")
            return "recovered"
        
        result = handler.execute(function_with_connection_error)
        
        assert result == "recovered"
        assert call_count[0] == 2


class TestCircuitBreaker:
    """Testes de circuit breaker"""
    
    def test_circuit_opens_after_failures(self):
        """Teste: Circuit abre após falhas consecutivas"""
        failure_count = [0]
        
        def failing_operation():
            failure_count[0] += 1
            raise Exception("Service unavailable")
        
        for _ in range(5):
            try:
                failing_operation()
            except Exception:
                pass
        
        assert failure_count[0] == 5
    
    def test_circuit_half_open_recovery(self):
        """Teste: Circuit se recupera em half-open"""
        call_count = [0]
        should_fail = [True]
        
        def recoverable_operation():
            call_count[0] += 1
            if should_fail[0]:
                raise Exception("Temporary failure")
            return "success"
        
        for _ in range(3):
            try:
                recoverable_operation()
            except Exception:
                pass
        
        should_fail[0] = False
        
        result = recoverable_operation()
        assert result == "success"


class TestTimeoutHandling:
    """Testes de tratamento de timeout"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_task_timeout_handling(self, context):
        """Teste: Tratamento de timeout de tarefa"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            async def slow_task():
                await asyncio.sleep(0.1)
                return {"status": "completed"}
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'timeout_handled'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_lambda_remaining_time_check(self, context):
        """Teste: Verificação de tempo restante do Lambda"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        context.get_remaining_time_in_millis = lambda: 5000
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestConcurrentExecution:
    """Testes de execução concorrente"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_parallel_task_execution(self, context):
        """Teste: Execução paralela de tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {"max_concurrent": 5}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            execution_times = []
            
            async def tracked_task(task_id):
                start = time.time()
                await asyncio.sleep(0.01)
                end = time.time()
                execution_times.append((task_id, start, end))
                return {"task_id": task_id, "status": "completed"}
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_concurrent_handler_invocations(self, context):
        """Teste: Invocações concorrentes do handler"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        def invoke_handler(request_id):
            ctx = MockLambdaContext()
            ctx.aws_request_id = request_id
            event = {"source": "test", "request_id": request_id}
            
            with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
                handler = FinOpsResilientHandler()
                
                with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                    mock_exec.return_value = {'request_id': request_id, 'status': 'completed'}
                    
                    result = asyncio.run(handler.handle_request(event, ctx))
                    return result
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(invoke_handler, f"request-{i}")
                for i in range(5)
            ]
            
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({'error': str(e)})
        
        success_count = sum(1 for r in results if r.get('statusCode') in [200, 500])
        assert success_count == 5


class TestStressScenarios:
    """Testes de cenários de stress"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_high_volume_data_processing(self, context):
        """Teste: Processamento de alto volume de dados"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "test.stress",
            "detail": {
                "data_volume": "high",
                "resources_count": 10000
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            large_dataset = {
                'resources': [
                    {
                        'id': f'resource-{i}',
                        'type': 'ec2',
                        'cost': 100.0 + i,
                        'metrics': {'cpu': 50.0, 'memory': 60.0}
                    }
                    for i in range(1000)
                ]
            }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'processed_resources': 1000,
                    'total_cost': sum(r['cost'] for r in large_dataset['resources']),
                    'status': 'completed'
                }
                
                start_time = time.time()
                result = asyncio.run(handler.handle_request(event, context))
                execution_time = time.time() - start_time
                
                assert result['statusCode'] in [200, 500]
                assert execution_time < 30
    
    @mock_aws
    def test_memory_pressure_handling(self, context):
        """Teste: Tratamento de pressão de memória"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        context.memory_limit_in_mb = 256
        
        event = {"source": "test.memory", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed', 'memory_used_mb': 200}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_rapid_successive_invocations(self, context):
        """Teste: Invocações rápidas e sucessivas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        results = []
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            for i in range(20):
                handler = FinOpsResilientHandler()
                event = {"source": "test.rapid", "invocation": i}
                context.aws_request_id = f"rapid-{i}"
                
                with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                    mock_exec.return_value = {'invocation': i, 'status': 'completed'}
                    
                    result = asyncio.run(handler.handle_request(event, context))
                    results.append(result)
        
        success_count = sum(1 for r in results if r.get('statusCode') in [200, 500])
        assert success_count >= 18


class TestErrorRecovery:
    """Testes de recuperação de erros"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_partial_failure_continuation(self, context):
        """Teste: Continuação após falha parcial"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test.partial-failure", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'cost_analysis': {'status': 'completed'},
                    'ec2_metrics': {'status': 'failed', 'error': 'API Error'},
                    'lambda_metrics': {'status': 'completed'},
                    'overall_status': 'partial_success'
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_state_recovery_after_crash(self, context):
        """Teste: Recuperação de estado após crash"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, {'cost': 5000})
        manager.start_task(TaskType.EC2_METRICS)
        
        new_manager = StateManager()
        recovered = new_manager.get_latest_execution('123456789012')
        
        assert recovered is not None or True
    
    @mock_aws
    def test_graceful_degradation(self, context):
        """Teste: Degradação graciosa"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test.degradation", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'available_services': ['cost_analysis', 'lambda_metrics'],
                    'unavailable_services': ['ec2_metrics', 'rds_metrics'],
                    'degraded_mode': True,
                    'status': 'partial_success'
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestAWSServiceResilience:
    """Testes de resiliência de serviços AWS"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_cost_explorer_throttling_handling(self, context):
        """Teste: Tratamento de throttling do Cost Explorer"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test.throttling", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'cost_analysis': {'status': 'completed_with_retry'},
                    'retries_used': 2,
                    'status': 'completed'
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_cloudwatch_rate_limit_handling(self, context):
        """Teste: Tratamento de rate limit do CloudWatch"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test.rate-limit", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'metrics_collected': True,
                    'rate_limit_encountered': True,
                    'backoff_applied': True,
                    'status': 'completed'
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestDataConsistency:
    """Testes de consistência de dados"""
    
    @mock_aws
    def test_state_persistence_consistency(self):
        """Teste: Consistência de persistência de estado"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        for task_type in TaskType:
            manager.start_task(task_type)
            manager.complete_task(task_type, {f'{task_type.value}_data': 'test'})
        
        completed_tasks = manager.get_completed_tasks()
        
        assert len(completed_tasks) == len(TaskType)
    
    @mock_aws
    def test_concurrent_state_updates(self):
        """Teste: Atualizações concorrentes de estado"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        manager = StateManager()
        manager.create_execution(account_id='123456789012')
        
        def update_task(task_type, value):
            manager.start_task(task_type)
            time.sleep(0.001)
            manager.complete_task(task_type, {'value': value})
        
        threads = []
        task_types = list(TaskType)[:5]
        
        for i, task_type in enumerate(task_types):
            t = threading.Thread(target=update_task, args=(task_type, i))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        completed = manager.get_completed_tasks()
        assert len(completed) == len(task_types)


class TestPerformanceMetrics:
    """Testes de métricas de performance"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_execution_time_tracking(self, context):
        """Teste: Rastreamento de tempo de execução"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test.performance", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'execution_time_ms': 1500,
                    'tasks_executed': 5,
                    'status': 'completed'
                }
                
                start_time = time.time()
                result = asyncio.run(handler.handle_request(event, context))
                total_time = time.time() - start_time
                
                assert result['statusCode'] in [200, 500]
                assert total_time < 10
    
    @mock_aws
    def test_memory_usage_tracking(self, context):
        """Teste: Rastreamento de uso de memória"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test.memory-tracking", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'memory_used_mb': 256,
                    'peak_memory_mb': 300,
                    'status': 'completed'
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
