"""
Testes unitários para RetryHandler

FASE 1.2 do Roadmap FinOps AWS
Cobertura: Sistema de retry inteligente com backoff exponencial
"""
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.finops_aws.core.retry_handler import (
    RetryHandler,
    RetryPolicy,
    RetryMetrics,
    RetryDecision,
    ErrorCategory,
    retry_with_exponential_backoff,
    async_retry_with_exponential_backoff,
    create_aws_retry_policy
)


class TestRetryPolicy:
    """Testes para RetryPolicy"""

    def test_default_policy(self):
        """Testa política padrão"""
        policy = RetryPolicy()
        
        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 2.0
        assert policy.jitter == 0.25

    def test_custom_policy(self):
        """Testa política personalizada"""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0
        )
        
        assert policy.max_retries == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 120.0

    def test_should_retry_max_attempts(self):
        """Testa que para após max_retries (total attempts = max_retries + 1)"""
        policy = RetryPolicy(max_retries=3)
        
        decision_within = policy.should_retry(ConnectionError("test"), attempt=3)
        assert decision_within == RetryDecision.RETRY_WITH_BACKOFF
        
        decision_exceeded = policy.should_retry(ConnectionError("test"), attempt=4)
        assert decision_exceeded == RetryDecision.STOP

    def test_should_retry_transient_error(self):
        """Testa retry para erro transiente"""
        policy = RetryPolicy()
        
        decision = policy.should_retry(ConnectionError("connection failed"), attempt=1)
        
        assert decision == RetryDecision.RETRY_WITH_BACKOFF

    def test_should_not_retry_value_error(self):
        """Testa que não faz retry para ValueError"""
        policy = RetryPolicy()
        
        decision = policy.should_retry(ValueError("invalid value"), attempt=1)
        
        assert decision == RetryDecision.STOP

    def test_calculate_delay_exponential(self):
        """Testa cálculo exponencial de delay"""
        policy = RetryPolicy(base_delay=1.0, exponential_base=2.0, jitter=0.0)
        
        assert policy.calculate_delay(0) == 1.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 4.0
        assert policy.calculate_delay(3) == 8.0

    def test_calculate_delay_max_cap(self):
        """Testa limite máximo de delay"""
        policy = RetryPolicy(base_delay=1.0, max_delay=5.0, jitter=0.0)
        
        delay = policy.calculate_delay(10)
        
        assert delay == 5.0

    def test_calculate_delay_with_jitter(self):
        """Testa jitter no delay"""
        policy = RetryPolicy(base_delay=10.0, jitter=0.5)
        
        delays = [policy.calculate_delay(0) for _ in range(100)]
        
        assert min(delays) >= 5.0
        assert max(delays) <= 15.0
        assert len(set(delays)) > 1


class TestRetryMetrics:
    """Testes para RetryMetrics"""

    def test_default_metrics(self):
        """Testa métricas padrão"""
        metrics = RetryMetrics()
        
        assert metrics.total_attempts == 0
        assert metrics.successful_attempts == 0
        assert metrics.failed_attempts == 0

    def test_record_success(self):
        """Testa registro de sucesso"""
        metrics = RetryMetrics()
        
        metrics.record_attempt(success=True, duration=1.5)
        
        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 0
        assert metrics.last_success_at is not None

    def test_record_failure(self):
        """Testa registro de falha"""
        metrics = RetryMetrics()
        
        metrics.record_attempt(success=False, error=ValueError("test"), duration=0.5)
        
        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 0
        assert metrics.failed_attempts == 1
        assert metrics.last_error == "test"
        assert 'ValueError' in metrics.errors_by_category

    def test_to_dict(self):
        """Testa conversão para dicionário"""
        metrics = RetryMetrics()
        metrics.record_attempt(success=True, duration=1.0)
        metrics.record_attempt(success=False, error=Exception("err"), duration=0.5)
        
        result = metrics.to_dict()
        
        assert result['total_attempts'] == 2
        assert result['successful_attempts'] == 1
        assert result['failed_attempts'] == 1
        assert result['success_rate'] == 50.0


class TestRetryHandler:
    """Testes para RetryHandler"""

    def test_successful_execution(self):
        """Testa execução bem-sucedida"""
        handler = RetryHandler()
        func = Mock(return_value="success")
        
        result = handler.execute(func)
        
        assert result == "success"
        assert func.call_count == 1

    def test_retry_on_failure(self):
        """Testa retry após falha"""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        handler = RetryHandler(policy)
        func = Mock(side_effect=[ConnectionError(), ConnectionError(), "success"])
        
        result = handler.execute(func)
        
        assert result == "success"
        assert func.call_count == 3

    def test_max_retries_exhausted(self):
        """Testa exaustão de retries"""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        handler = RetryHandler(policy)
        func = Mock(side_effect=ConnectionError("always fails"))
        
        with pytest.raises(ConnectionError):
            handler.execute(func)
        
        assert func.call_count == 3
        assert handler.metrics.retries_exhausted == 1

    def test_no_retry_on_value_error(self):
        """Testa que não faz retry para ValueError"""
        handler = RetryHandler()
        func = Mock(side_effect=ValueError("invalid"))
        
        with pytest.raises(ValueError):
            handler.execute(func)
        
        assert func.call_count == 1

    def test_on_retry_callback(self):
        """Testa callback de retry"""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        handler = RetryHandler(policy)
        callback = Mock()
        func = Mock(side_effect=[ConnectionError(), "success"])
        
        handler.execute(func, on_retry=callback)
        
        callback.assert_called_once()

    def test_metrics_tracking(self):
        """Testa rastreamento de métricas"""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        handler = RetryHandler(policy)
        func = Mock(side_effect=[ConnectionError(), "success"])
        
        handler.execute(func)
        
        metrics = handler.get_metrics()
        assert metrics['total_attempts'] == 2
        assert metrics['successful_attempts'] == 1
        assert metrics['failed_attempts'] == 1

    def test_reset_metrics(self):
        """Testa reset de métricas"""
        handler = RetryHandler()
        handler.metrics.total_attempts = 10
        
        handler.reset_metrics()
        
        assert handler.metrics.total_attempts == 0


class TestRetryHandlerDecorator:
    """Testes para decorators do RetryHandler"""

    def test_with_retry_decorator(self):
        """Testa decorator with_retry"""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        handler = RetryHandler(policy)
        
        call_count = 0
        
        @handler.with_retry()
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError()
            return "success"
        
        result = failing_then_success()
        
        assert result == "success"
        assert call_count == 2

    def test_with_retry_override_params(self):
        """Testa override de parâmetros no decorator"""
        handler = RetryHandler()
        
        @handler.with_retry(max_retries=1)
        def always_fails():
            raise ConnectionError()
        
        with pytest.raises(ConnectionError):
            always_fails()


class TestRetryHandlerAsync:
    """Testes para execução async"""

    @pytest.mark.asyncio
    async def test_async_successful_execution(self):
        """Testa execução async bem-sucedida"""
        handler = RetryHandler()
        
        async def async_func():
            return "async success"
        
        result = await handler.execute_async(async_func)
        
        assert result == "async success"

    @pytest.mark.asyncio
    async def test_async_retry_on_failure(self):
        """Testa retry async após falha"""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        handler = RetryHandler(policy)
        call_count = 0
        
        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError()
            return "success"
        
        result = await handler.execute_async(async_func)
        
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_max_retries_exhausted(self):
        """Testa exaustão de retries async"""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        handler = RetryHandler(policy)
        
        async def always_fails():
            raise ConnectionError("always fails")
        
        with pytest.raises(ConnectionError):
            await handler.execute_async(always_fails)


class TestRetryDecorators:
    """Testes para decorators de retry"""

    def test_retry_with_exponential_backoff(self):
        """Testa decorator retry_with_exponential_backoff"""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError()
            return "success"
        
        result = failing_then_success()
        
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_retry_decorator(self):
        """Testa decorator async_retry_with_exponential_backoff"""
        call_count = 0
        
        @async_retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        async def async_failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError()
            return "async success"
        
        result = await async_failing_then_success()
        
        assert result == "async success"
        assert call_count == 2


class TestAWSRetryPolicy:
    """Testes para política AWS"""

    def test_create_aws_retry_policy(self):
        """Testa criação de política AWS"""
        policy = create_aws_retry_policy()
        
        assert policy.max_retries == 5
        assert policy.max_delay == 30.0
        assert 429 in policy.retryable_status_codes
        assert 503 in policy.retryable_status_codes


class TestErrorClassification:
    """Testes para classificação de erros"""

    def test_classify_timeout_error(self):
        """Testa classificação de erro de timeout"""
        policy = RetryPolicy()
        
        decision = policy.should_retry(TimeoutError("request timed out"), attempt=1)
        
        assert decision == RetryDecision.RETRY_WITH_BACKOFF

    def test_classify_connection_error(self):
        """Testa classificação de erro de conexão"""
        policy = RetryPolicy()
        
        decision = policy.should_retry(ConnectionError("connection refused"), attempt=1)
        
        assert decision == RetryDecision.RETRY_WITH_BACKOFF

    def test_classify_type_error(self):
        """Testa classificação de TypeError (não retryable)"""
        policy = RetryPolicy()
        
        decision = policy.should_retry(TypeError("wrong type"), attempt=1)
        
        assert decision == RetryDecision.STOP
