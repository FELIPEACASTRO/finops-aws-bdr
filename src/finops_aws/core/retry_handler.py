"""
Retry Handler - Sistema de Retry Inteligente com Backoff Exponencial

FASE 1.2 do Roadmap FinOps AWS
Objetivo: Implementar retry inteligente com backoff exponencial e jitter

Autor: FinOps AWS Team
Data: Novembro 2025

Características:
- Backoff exponencial com jitter para evitar thundering herd
- Classificação de erros (retryable vs non-retryable)
- Métricas de retry para observabilidade
- Integração com DynamoDB State Manager
"""
import asyncio
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import (
    Any, Callable, Dict, List, Optional, 
    Type, TypeVar, Union, Awaitable
)
import traceback

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')


class ErrorCategory(Enum):
    """Categorias de erro para classificação"""
    TRANSIENT = "transient"
    THROTTLING = "throttling"
    TIMEOUT = "timeout"
    CLIENT_ERROR = "client_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE_NOT_FOUND = "resource_not_found"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class RetryDecision(Enum):
    """Decisão de retry"""
    RETRY = "retry"
    STOP = "stop"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RETRY_IMMEDIATELY = "retry_immediately"


@dataclass
class RetryPolicy:
    """
    Política de retry configurável
    
    Attributes:
        max_retries: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        exponential_base: Base para cálculo exponencial
        jitter: Fator de jitter (0.0 a 1.0)
        retryable_exceptions: Exceções que devem ser retried
        non_retryable_exceptions: Exceções que não devem ser retried
        retryable_status_codes: Status codes HTTP que devem ser retried
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.25
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ConnectionError,
        TimeoutError,
        OSError
    ])
    non_retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ValueError,
        TypeError,
        KeyError
    ])
    retryable_status_codes: List[int] = field(default_factory=lambda: [
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504   # Gateway Timeout
    ])

    def should_retry(self, exception: Exception, attempt: int) -> RetryDecision:
        """
        Determina se uma exceção deve ser retried
        
        Args:
            exception: Exceção lançada
            attempt: Número da tentativa atual (1-indexed)
            
        Returns:
            RetryDecision indicando ação a tomar
        """
        if attempt > self.max_retries:
            return RetryDecision.STOP
        
        for non_retryable in self.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                return RetryDecision.STOP
        
        for retryable in self.retryable_exceptions:
            if isinstance(exception, retryable):
                return RetryDecision.RETRY_WITH_BACKOFF
        
        error_category = self._classify_error(exception)
        
        if error_category in [ErrorCategory.TRANSIENT, ErrorCategory.TIMEOUT, ErrorCategory.NETWORK_ERROR]:
            return RetryDecision.RETRY_WITH_BACKOFF
        elif error_category == ErrorCategory.THROTTLING:
            return RetryDecision.RETRY_WITH_BACKOFF
        elif error_category in [ErrorCategory.CLIENT_ERROR, ErrorCategory.VALIDATION]:
            return RetryDecision.STOP
        elif error_category == ErrorCategory.SERVER_ERROR:
            return RetryDecision.RETRY_WITH_BACKOFF
        
        return RetryDecision.RETRY_WITH_BACKOFF

    def _classify_error(self, exception: Exception) -> ErrorCategory:
        """Classifica o tipo de erro"""
        error_msg = str(exception).lower()
        error_type = type(exception).__name__.lower()
        
        if 'timeout' in error_msg or 'timeout' in error_type:
            return ErrorCategory.TIMEOUT
        elif 'throttl' in error_msg or 'rate' in error_msg:
            return ErrorCategory.THROTTLING
        elif 'connect' in error_msg or 'network' in error_msg:
            return ErrorCategory.NETWORK_ERROR
        elif 'auth' in error_msg:
            if 'authori' in error_msg:
                return ErrorCategory.AUTHORIZATION
            return ErrorCategory.AUTHENTICATION
        elif 'not found' in error_msg or '404' in error_msg:
            return ErrorCategory.RESOURCE_NOT_FOUND
        elif 'valid' in error_msg:
            return ErrorCategory.VALIDATION
        elif hasattr(exception, 'response'):
            response = getattr(exception, 'response', None)
            if response is not None:
                status_code = getattr(response, 'status_code', 0)
                if 400 <= status_code < 500:
                    return ErrorCategory.CLIENT_ERROR
                elif status_code >= 500:
                    return ErrorCategory.SERVER_ERROR
        
        return ErrorCategory.UNKNOWN

    def calculate_delay(self, attempt: int) -> float:
        """
        Calcula o delay para a próxima tentativa
        
        Args:
            attempt: Número da tentativa (0-indexed)
            
        Returns:
            Delay em segundos
        """
        exponential_delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(exponential_delay, self.max_delay)
        
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay = delay + random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


@dataclass
class RetryMetrics:
    """Métricas de retry para observabilidade"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    retries_exhausted: int = 0
    total_retry_time: float = 0.0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    last_error: Optional[str] = None
    last_success_at: Optional[datetime] = None

    def record_attempt(self, success: bool, error: Optional[Exception] = None, duration: float = 0.0):
        """Registra uma tentativa"""
        self.total_attempts += 1
        
        if success:
            self.successful_attempts += 1
            self.last_success_at = datetime.now()
        else:
            self.failed_attempts += 1
            if error:
                self.last_error = str(error)
                category = self._get_error_category(error)
                self.errors_by_category[category] = self.errors_by_category.get(category, 0) + 1
        
        self.total_retry_time += duration

    def _get_error_category(self, error: Exception) -> str:
        """Obtém categoria do erro para métricas"""
        return type(error).__name__

    def to_dict(self) -> Dict[str, Any]:
        """Converte métricas para dicionário"""
        return {
            'total_attempts': self.total_attempts,
            'successful_attempts': self.successful_attempts,
            'failed_attempts': self.failed_attempts,
            'retries_exhausted': self.retries_exhausted,
            'total_retry_time_seconds': round(self.total_retry_time, 3),
            'success_rate': round(
                (self.successful_attempts / self.total_attempts * 100)
                if self.total_attempts > 0 else 0, 2
            ),
            'errors_by_category': self.errors_by_category,
            'last_error': self.last_error,
            'last_success_at': self.last_success_at.isoformat() if self.last_success_at else None
        }


class RetryHandler:
    """
    Handler de retry com backoff exponencial e métricas
    
    Uso:
        handler = RetryHandler()
        result = handler.execute(my_function, arg1, arg2, kwarg1=value)
        
        # Ou como decorator
        @handler.with_retry()
        def my_function():
            ...
    """

    def __init__(self, policy: Optional[RetryPolicy] = None):
        """
        Inicializa o RetryHandler
        
        Args:
            policy: Política de retry (usa padrão se não fornecida)
        """
        self.policy = policy or RetryPolicy()
        self.metrics = RetryMetrics()

    def execute(
        self,
        func: Callable[..., T],
        *args,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        **kwargs
    ) -> T:
        """
        Executa uma função com retry
        
        Args:
            func: Função a executar
            *args: Argumentos posicionais
            on_retry: Callback chamado antes de cada retry
            **kwargs: Argumentos nomeados
            
        Returns:
            Resultado da função
            
        Raises:
            Exception: Se todos os retries falharem
        """
        last_exception = None
        
        for attempt in range(self.policy.max_retries + 1):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                self.metrics.record_attempt(success=True, duration=duration)
                
                if attempt > 0:
                    logger.info(f"Operation succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                last_exception = e
                self.metrics.record_attempt(success=False, error=e, duration=duration)
                
                decision = self.policy.should_retry(e, attempt + 1)
                
                logger.warning(f"Attempt {attempt + 1} failed: {e}", extra={
                    'extra_data': {
                        'attempt': attempt + 1,
                        'max_retries': self.policy.max_retries,
                        'decision': decision.value,
                        'error_type': type(e).__name__
                    }
                })
                
                if decision == RetryDecision.STOP:
                    is_max_retries_exceeded = (attempt + 1) > self.policy.max_retries
                    if is_max_retries_exceeded:
                        self.metrics.retries_exhausted += 1
                        logger.error(f"Max retries exhausted: {e}")
                    else:
                        logger.error(f"Not retrying due to non-retryable error: {e}")
                    raise
                
                if attempt < self.policy.max_retries:
                    delay = self.policy.calculate_delay(attempt)
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    logger.info(f"Retrying in {delay:.2f}s...")
                    time.sleep(delay)
        
        self.metrics.retries_exhausted += 1
        logger.error(f"All {self.policy.max_retries + 1} attempts failed")
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("All retry attempts failed")

    async def execute_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        **kwargs
    ) -> T:
        """
        Executa uma função async com retry
        
        Args:
            func: Função async a executar
            *args: Argumentos posicionais
            on_retry: Callback chamado antes de cada retry
            **kwargs: Argumentos nomeados
            
        Returns:
            Resultado da função
            
        Raises:
            Exception: Se todos os retries falharem
        """
        last_exception = None
        
        for attempt in range(self.policy.max_retries + 1):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                self.metrics.record_attempt(success=True, duration=duration)
                
                if attempt > 0:
                    logger.info(f"Async operation succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                last_exception = e
                self.metrics.record_attempt(success=False, error=e, duration=duration)
                
                decision = self.policy.should_retry(e, attempt + 1)
                
                logger.warning(f"Async attempt {attempt + 1} failed: {e}")
                
                if decision == RetryDecision.STOP:
                    is_max_retries_exceeded = (attempt + 1) > self.policy.max_retries
                    if is_max_retries_exceeded:
                        self.metrics.retries_exhausted += 1
                        logger.error(f"Async max retries exhausted: {e}")
                    else:
                        logger.error(f"Async not retrying due to non-retryable error: {e}")
                    raise
                
                if attempt < self.policy.max_retries:
                    delay = self.policy.calculate_delay(attempt)
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(delay)
        
        self.metrics.retries_exhausted += 1
        logger.error(f"All {self.policy.max_retries + 1} async attempts failed")
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("All async retry attempts failed")

    def with_retry(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None
    ):
        """
        Decorator para adicionar retry a uma função
        
        Args:
            max_retries: Override do número máximo de retries
            base_delay: Override do delay base
            
        Returns:
            Decorator
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                original_max_retries = self.policy.max_retries
                original_base_delay = self.policy.base_delay
                
                try:
                    if max_retries is not None:
                        self.policy.max_retries = max_retries
                    if base_delay is not None:
                        self.policy.base_delay = base_delay
                    
                    return self.execute(func, *args, **kwargs)
                finally:
                    self.policy.max_retries = original_max_retries
                    self.policy.base_delay = original_base_delay
            
            return wrapper
        return decorator

    def with_retry_async(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None
    ):
        """
        Decorator para adicionar retry a uma função async
        
        Args:
            max_retries: Override do número máximo de retries
            base_delay: Override do delay base
            
        Returns:
            Decorator
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                original_max_retries = self.policy.max_retries
                original_base_delay = self.policy.base_delay
                
                try:
                    if max_retries is not None:
                        self.policy.max_retries = max_retries
                    if base_delay is not None:
                        self.policy.base_delay = base_delay
                    
                    return await self.execute_async(func, *args, **kwargs)
                finally:
                    self.policy.max_retries = original_max_retries
                    self.policy.base_delay = original_base_delay
            
            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de retry"""
        return self.metrics.to_dict()

    def reset_metrics(self):
        """Reseta métricas"""
        self.metrics = RetryMetrics()


def create_aws_retry_policy() -> RetryPolicy:
    """
    Cria política de retry otimizada para serviços AWS
    
    Returns:
        RetryPolicy configurada para AWS
    """
    from botocore.exceptions import (
        ClientError, 
        ConnectionError as BotoConnectionError,
        ReadTimeoutError,
        ConnectTimeoutError
    )
    
    return RetryPolicy(
        max_retries=5,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=0.25,
        retryable_exceptions=[
            BotoConnectionError,
            ReadTimeoutError,
            ConnectTimeoutError,
            ConnectionError,
            TimeoutError
        ],
        non_retryable_exceptions=[
            ValueError,
            TypeError,
            KeyError
        ],
        retryable_status_codes=[
            400,  # Throttling (DynamoDB)
            408,
            429,
            500,
            502,
            503,
            504
        ]
    )


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.25
):
    """
    Decorator simples para retry com backoff exponencial
    
    Args:
        max_retries: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        jitter: Fator de jitter
        
    Returns:
        Decorator
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter
    )
    handler = RetryHandler(policy)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return handler.execute(func, *args, **kwargs)
        return wrapper
    
    return decorator


def async_retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.25
):
    """
    Decorator para retry async com backoff exponencial
    
    Args:
        max_retries: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        jitter: Fator de jitter
        
    Returns:
        Decorator
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter
    )
    handler = RetryHandler(policy)
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await handler.execute_async(func, *args, **kwargs)
        return wrapper
    
    return decorator
