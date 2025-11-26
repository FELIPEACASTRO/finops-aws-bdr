"""
Core business logic module

Este módulo contém a lógica central do FinOps AWS:
- StateManager: Gerenciamento de estado e recuperação de falhas
- ResilientExecutor: Execução resiliente com retry e circuit breaker
- CleanupManager: Limpeza automática de arquivos temporários
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

__all__ = [
    'StateManager',
    'ExecutionState',
    'TaskState',
    'TaskType',
    'ExecutionStatus',
    'ResilientExecutor',
    'CircuitBreaker',
    'RetryConfig',
    'CircuitBreakerConfig',
    'CleanupManager',
    'CleanupConfig',
    'CleanupResult',
    'cleanup_after_execution'
]
