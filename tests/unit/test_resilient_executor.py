"""
Testes para o ResilientExecutor
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.finops_aws.core.resilient_executor import (
    ResilientExecutor, CircuitBreaker, CircuitBreakerState,
    RetryConfig, CircuitBreakerConfig
)
from src.finops_aws.core.state_manager import (
    StateManager, TaskType, ExecutionStatus
)


class TestCircuitBreaker:
    """Testes para CircuitBreaker"""

    def test_circuit_breaker_closed_state(self):
        """Testa estado fechado do circuit breaker"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_execute() is True

    def test_circuit_breaker_opens_after_failures(self):
        """Testa abertura do circuit breaker após falhas"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        cb = CircuitBreaker(config)

        # Primeira falha
        cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_execute() is True

        # Segunda falha - deve abrir
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_execute() is False

    def test_circuit_breaker_half_open_after_timeout(self):
        """Testa estado meio-aberto após timeout"""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0)
        cb = CircuitBreaker(config)

        # Força falha para abrir
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Após timeout, deve permitir tentativa
        assert cb.can_execute() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_breaker_closes_after_success(self):
        """Testa fechamento após sucesso"""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config)

        # Abre circuit breaker
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Sucesso deve fechar
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0


class TestResilientExecutor:
    """Testes para ResilientExecutor"""

    def setup_method(self, method):
        """Setup para cada teste"""
        self.state_manager = Mock(spec=StateManager)
        self.executor = ResilientExecutor(self.state_manager)

        # Mock da execução atual
        self.mock_execution = Mock()
        self.mock_execution.tasks = {}
        self.state_manager.current_execution = self.mock_execution

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Testa execução bem-sucedida de tarefa"""
        task_id = 'test-task'
        task_type = TaskType.COST_ANALYSIS
        expected_result = {'data': 'test'}

        # Mock da tarefa
        mock_task = Mock()
        mock_task.status = ExecutionStatus.PENDING
        self.state_manager.start_task.return_value = mock_task

        # Função de teste
        async def test_func():
            return expected_result

        result = await self.executor.execute_task(task_id, test_func, task_type)

        assert result == expected_result
        self.state_manager.start_task.assert_called_once_with(task_id)
        self.state_manager.complete_task.assert_called_once_with(task_id, expected_result)

    @pytest.mark.asyncio
    async def test_execute_task_with_retry(self):
        """Testa execução com retry"""
        task_id = 'test-task'
        task_type = TaskType.COST_ANALYSIS

        # Mock da tarefa
        mock_task = Mock()
        mock_task.status = ExecutionStatus.PENDING
        self.state_manager.start_task.return_value = mock_task

        # Função que falha na primeira tentativa
        call_count = 0
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt fails")
            return {'success': True}

        result = await self.executor.execute_task(task_id, failing_func, task_type)

        assert result == {'success': True}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_task_max_retries_exceeded(self):
        """Testa falha após esgotar tentativas"""
        task_id = 'test-task'
        task_type = TaskType.COST_ANALYSIS

        # Mock da tarefa
        mock_task = Mock()
        mock_task.status = ExecutionStatus.PENDING
        self.state_manager.start_task.return_value = mock_task

        # Função que sempre falha
        async def always_fails():
            raise Exception("Always fails")

        with pytest.raises(Exception, match="Always fails"):
            await self.executor.execute_task(task_id, always_fails, task_type)

        self.state_manager.fail_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_timeout(self):
        """Testa timeout de tarefa"""
        task_id = 'test-task'
        task_type = TaskType.COST_ANALYSIS
        timeout = 0.1  # 100ms

        # Mock da tarefa
        mock_task = Mock()
        mock_task.status = ExecutionStatus.PENDING
        self.state_manager.start_task.return_value = mock_task

        # Função que demora mais que o timeout
        async def slow_func():
            await asyncio.sleep(0.2)
            return {'data': 'test'}

        with pytest.raises(asyncio.TimeoutError):
            await self.executor.execute_task(task_id, slow_func, task_type, timeout)

    @pytest.mark.asyncio
    async def test_execute_task_already_completed(self):
        """Testa tarefa já concluída"""
        task_id = 'test-task'
        task_type = TaskType.COST_ANALYSIS
        cached_result = {'cached': 'data'}

        # Mock da tarefa já concluída
        mock_task = Mock()
        mock_task.status = ExecutionStatus.COMPLETED
        mock_task.result_data = cached_result

        self.mock_execution.tasks = {task_id: mock_task}

        async def test_func():
            return {'new': 'data'}

        result = await self.executor.execute_task(task_id, test_func, task_type)

        assert result == cached_result
        # Não deve chamar start_task se já está concluída
        self.state_manager.start_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_task_circuit_breaker_open(self):
        """Testa circuit breaker aberto"""
        task_id = 'test-task'
        task_type = TaskType.COST_ANALYSIS

        # Força abertura do circuit breaker
        cb = self.executor._get_circuit_breaker(task_type)
        cb.state = CircuitBreakerState.OPEN
        cb.next_attempt_time = datetime.now().replace(year=2099)  # Futuro distante

        async def test_func():
            return {'data': 'test'}

        with pytest.raises(Exception, match="Circuit breaker open"):
            await self.executor.execute_task(task_id, test_func, task_type)

        self.state_manager.skip_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_all_pending_tasks(self):
        """Testa execução de todas as tarefas pendentes"""
        # Mock de tarefas pendentes
        mock_task1 = Mock()
        mock_task1.task_id = 'task1'
        mock_task1.task_type = TaskType.COST_ANALYSIS

        mock_task2 = Mock()
        mock_task2.task_id = 'task2'
        mock_task2.task_type = TaskType.EC2_METRICS

        self.state_manager.get_pending_tasks.return_value = [mock_task1, mock_task2]

        # Mock das tarefas no state manager
        self.state_manager.start_task.return_value = Mock()

        # Funções de teste
        task_functions = {
            TaskType.COST_ANALYSIS: lambda: {'cost': 'data'},
            TaskType.EC2_METRICS: lambda: {'ec2': 'data'}
        }

        results = await self.executor.execute_all_pending_tasks(task_functions, max_concurrent=2)

        assert len(results) == 2
        assert 'task1' in results
        assert 'task2' in results

    @pytest.mark.asyncio
    async def test_execute_with_dependencies(self):
        """Testa execução com dependências"""
        # Mock de tarefas pendentes
        task1 = Mock()
        task1.task_id = 'task1'
        task1.task_type = TaskType.EC2_METRICS

        task2 = Mock()
        task2.task_id = 'task2'
        task2.task_type = TaskType.EC2_RECOMMENDATIONS

        self.state_manager.get_pending_tasks.return_value = [task1, task2]
        self.state_manager.get_completed_tasks.return_value = []

        # Mock das tarefas no state manager
        self.state_manager.start_task.return_value = Mock()

        # Funções de teste
        task_functions = {
            TaskType.EC2_METRICS: lambda: {'ec2': 'metrics'},
            TaskType.EC2_RECOMMENDATIONS: lambda: {'ec2': 'recommendations'}
        }

        # Dependências: recommendations dependem de metrics
        dependencies = {
            TaskType.EC2_RECOMMENDATIONS: [TaskType.EC2_METRICS]
        }

        results = await self.executor.execute_with_dependencies(
            task_functions, dependencies, max_concurrent=1
        )

        # Deve executar ambas as tarefas
        assert len(results) == 2

    def test_get_execution_progress(self):
        """Testa obtenção do progresso da execução"""
        summary = {'test': 'data'}
        self.state_manager.get_execution_summary.return_value = summary

        progress = self.executor.get_execution_progress()

        assert 'test' in progress
        assert 'circuit_breakers' in progress

    def test_reset_circuit_breaker(self):
        """Testa reset de circuit breaker"""
        task_type = TaskType.COST_ANALYSIS

        # Força falha para abrir circuit breaker
        cb = self.executor._get_circuit_breaker(task_type)
        cb.record_failure()

        # Reset
        self.executor.reset_circuit_breaker(task_type)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_reset_all_circuit_breakers(self):
        """Testa reset de todos os circuit breakers"""
        # Força falhas em múltiplos circuit breakers
        cb1 = self.executor._get_circuit_breaker(TaskType.COST_ANALYSIS)
        cb2 = self.executor._get_circuit_breaker(TaskType.EC2_METRICS)

        cb1.record_failure()
        cb2.record_failure()

        # Reset todos
        self.executor.reset_all_circuit_breakers()

        assert cb1.state == CircuitBreakerState.CLOSED
        assert cb2.state == CircuitBreakerState.CLOSED

    def test_calculate_delay(self):
        """Testa cálculo de delay para retry"""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False)

        delay1 = self.executor._calculate_delay(1, config)
        delay2 = self.executor._calculate_delay(2, config)
        delay3 = self.executor._calculate_delay(3, config)

        assert delay1 == 1.0  # base_delay * 2^0
        assert delay2 == 2.0  # base_delay * 2^1
        assert delay3 == 4.0  # base_delay * 2^2

    def test_calculate_delay_with_max(self):
        """Testa cálculo de delay com máximo"""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=3.0, jitter=False)

        delay = self.executor._calculate_delay(10, config)  # Seria muito alto

        assert delay == 3.0  # Limitado pelo max_delay

    def test_calculate_delay_with_jitter(self):
        """Testa cálculo de delay com jitter"""
        config = RetryConfig(base_delay=2.0, exponential_base=2.0, jitter=True)

        delay = self.executor._calculate_delay(1, config)

        # Com jitter, deve estar entre 50% e 100% do valor base
        assert 1.0 <= delay <= 2.0
