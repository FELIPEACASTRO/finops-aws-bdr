"""
Core business logic module

Este módulo contém a lógica central do FinOps AWS:
- StateManager: Gerenciamento de estado com S3 (legacy)
- DynamoDBStateManager: Gerenciamento de estado com DynamoDB (FASE 1.2)
- ResilientExecutor: Execução resiliente com retry e circuit breaker
- CleanupManager: Limpeza automática de arquivos temporários
- Factories: Criação centralizada de clientes e serviços (FASE 1.3)
"""

from .state_manager import (
    StateManager,
    ExecutionState,
    TaskState,
    TaskType,
    ExecutionStatus
)
from .resilient_executor import (
    ResilientExecutor,
    CircuitBreaker,
    RetryConfig,
    CircuitBreakerConfig
)
from .cleanup_manager import (
    CleanupManager,
    CleanupConfig,
    CleanupResult,
    cleanup_after_execution
)
from .dynamodb_state_manager import (
    DynamoDBStateManager,
    DynamoDBMapper,
    DynamoDBClientProtocol,
    DynamoDBTableProtocol,
    ExecutionRecord,
    CheckpointData,
    TaskStatus,
    ServiceCategory,
    BatchConfig,
    ExecutionStatus as DynamoDBExecutionStatus
)
from .retry_handler import (
    RetryHandler,
    RetryPolicy,
    RetryMetrics,
    RetryDecision,
    ErrorCategory,
    retry_with_exponential_backoff,
    async_retry_with_exponential_backoff,
    create_aws_retry_policy
)
from .factories import (
    AWSClientFactory,
    AWSServiceType,
    AWSClientConfig,
    ServiceFactory,
    ServiceConfig,
    ServiceProtocol
)

__all__ = [
    # Legacy S3 State Manager
    'StateManager',
    'ExecutionState',
    'TaskState',
    'TaskType',
    'ExecutionStatus',
    # DynamoDB State Manager (FASE 1.2)
    'DynamoDBStateManager',
    'DynamoDBMapper',
    'DynamoDBClientProtocol',
    'DynamoDBTableProtocol',
    'ExecutionRecord',
    'CheckpointData',
    'TaskStatus',
    'ServiceCategory',
    'BatchConfig',
    'DynamoDBExecutionStatus',
    # Resilient Executor
    'ResilientExecutor',
    'CircuitBreaker',
    'RetryConfig',
    'CircuitBreakerConfig',
    # Retry Handler (FASE 1.2)
    'RetryHandler',
    'RetryPolicy',
    'RetryMetrics',
    'RetryDecision',
    'ErrorCategory',
    'retry_with_exponential_backoff',
    'async_retry_with_exponential_backoff',
    'create_aws_retry_policy',
    # Cleanup Manager
    'CleanupManager',
    'CleanupConfig',
    'CleanupResult',
    'cleanup_after_execution',
    # Factories (FASE 1.3)
    'AWSClientFactory',
    'AWSServiceType',
    'AWSClientConfig',
    'ServiceFactory',
    'ServiceConfig',
    'ServiceProtocol'
]
