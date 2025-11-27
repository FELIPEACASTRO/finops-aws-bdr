"""
Executor resiliente para tarefas FinOps
Implementa retry automático, circuit breaker e recuperação de falhas
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum
import traceback

from .state_manager import StateManager, TaskType, ExecutionStatus, TaskState
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CircuitBreakerState(Enum):
    """Estados do Circuit Breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Falhas detectadas, rejeitando chamadas
    HALF_OPEN = "half_open"  # Testando se o serviço se recuperou


@dataclass
class RetryConfig:
    """Configuração de retry para tarefas"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception


class CircuitBreaker:
    """
    Circuit Breaker para proteger contra falhas em cascata
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None

    def can_execute(self) -> bool:
        """Verifica se pode executar a operação"""
        now = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.next_attempt_time is not None and now >= self.next_attempt_time:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Registra sucesso na operação"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None
        self.next_attempt_time = None

    def record_failure(self):
        """Registra falha na operação"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.next_attempt_time = self.last_failure_time + timedelta(
                seconds=self.config.recovery_timeout
            )


class ResilientExecutor:
    """
    Executor resiliente para tarefas FinOps
    Implementa retry, circuit breaker e recuperação de estado
    """
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[TaskType, RetryConfig] = self._get_default_retry_configs()
        self.circuit_configs: Dict[TaskType, CircuitBreakerConfig] = self._get_default_circuit_configs()

    def _get_default_retry_configs(self) -> Dict[TaskType, RetryConfig]:
        """Configurações de retry padrão por tipo de tarefa"""
        return {
            TaskType.COST_ANALYSIS: RetryConfig(max_retries=3, base_delay=2.0),
            TaskType.EC2_METRICS: RetryConfig(max_retries=5, base_delay=1.0),
            TaskType.LAMBDA_METRICS: RetryConfig(max_retries=5, base_delay=1.0),
            TaskType.RDS_METRICS: RetryConfig(max_retries=3, base_delay=3.0),
            TaskType.S3_METRICS: RetryConfig(max_retries=2, base_delay=5.0),
            TaskType.EC2_RECOMMENDATIONS: RetryConfig(max_retries=3, base_delay=2.0),
            TaskType.LAMBDA_RECOMMENDATIONS: RetryConfig(max_retries=3, base_delay=2.0),
            TaskType.RDS_RECOMMENDATIONS: RetryConfig(max_retries=2, base_delay=3.0),
            TaskType.REPORT_GENERATION: RetryConfig(max_retries=2, base_delay=1.0)
        }

    def _get_default_circuit_configs(self) -> Dict[TaskType, CircuitBreakerConfig]:
        """Configurações de circuit breaker padrão por tipo de tarefa"""
        return {
            TaskType.COST_ANALYSIS: CircuitBreakerConfig(failure_threshold=3, recovery_timeout=120),
            TaskType.EC2_METRICS: CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60),
            TaskType.LAMBDA_METRICS: CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60),
            TaskType.RDS_METRICS: CircuitBreakerConfig(failure_threshold=3, recovery_timeout=180),
            TaskType.S3_METRICS: CircuitBreakerConfig(failure_threshold=2, recovery_timeout=300),
            TaskType.EC2_RECOMMENDATIONS: CircuitBreakerConfig(failure_threshold=3, recovery_timeout=120),
            TaskType.LAMBDA_RECOMMENDATIONS: CircuitBreakerConfig(failure_threshold=3, recovery_timeout=120),
            TaskType.RDS_RECOMMENDATIONS: CircuitBreakerConfig(failure_threshold=2, recovery_timeout=180),
            TaskType.REPORT_GENERATION: CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        }

    def _get_circuit_breaker(self, task_type: TaskType) -> CircuitBreaker:
        """Obtém circuit breaker para tipo de tarefa"""
        key = task_type.value
        if key not in self.circuit_breakers:
            config = self.circuit_configs.get(task_type, CircuitBreakerConfig())
            self.circuit_breakers[key] = CircuitBreaker(config)
        return self.circuit_breakers[key]

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calcula delay para retry com backoff exponencial"""
        delay = min(
            config.base_delay * (config.exponential_base ** (attempt - 1)),
            config.max_delay
        )
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Jitter de 50-100%
        
        return delay

    async def execute_task(
        self,
        task_id: str,
        task_func: Callable[[], Any],
        task_type: TaskType,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Executa tarefa com retry e circuit breaker
        
        Args:
            task_id: ID da tarefa
            task_func: Função a ser executada
            task_type: Tipo da tarefa
            timeout: Timeout em segundos
            
        Returns:
            Resultado da execução
        """
        circuit_breaker = self._get_circuit_breaker(task_type)
        retry_config = self.retry_configs.get(task_type, RetryConfig())
        
        # Verifica se a tarefa já foi concluída
        if self.state_manager.current_execution:
            existing_task = self.state_manager.current_execution.tasks.get(task_id)
            if existing_task and existing_task.status == ExecutionStatus.COMPLETED:
                logger.info(f"Task {task_id} already completed, returning cached result")
                return existing_task.result_data

        # Verifica circuit breaker
        if not circuit_breaker.can_execute():
            error_msg = f"Circuit breaker open for task type {task_type.value}"
            self.state_manager.skip_task(task_id, error_msg)
            raise Exception(error_msg)

        # Inicia tarefa
        task_state = self.state_manager.start_task(task_id)
        last_exception = None
        
        for attempt in range(1, retry_config.max_retries + 1):
            try:
                logger.info(f"Executing task {task_id}, attempt {attempt}/{retry_config.max_retries}")
                
                # Executa com timeout se especificado
                if timeout:
                    result = await asyncio.wait_for(
                        self._run_task_function(task_func),
                        timeout=timeout
                    )
                else:
                    result = await self._run_task_function(task_func)
                
                # Sucesso - registra no circuit breaker e state manager
                circuit_breaker.record_success()
                self.state_manager.complete_task(task_id, result)
                
                logger.info(f"Task {task_id} completed successfully on attempt {attempt}")
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = e
                error_msg = f"Task {task_id} timed out after {timeout} seconds"
                logger.warning(f"{error_msg} (attempt {attempt})")
                
            except Exception as e:
                last_exception = e
                error_msg = f"Task {task_id} failed: {str(e)}"
                logger.warning(f"{error_msg} (attempt {attempt})")
                logger.debug(f"Task {task_id} traceback: {traceback.format_exc()}")
            
            # Se não é a última tentativa, aguarda antes de tentar novamente
            if attempt < retry_config.max_retries:
                delay = self._calculate_delay(attempt, retry_config)
                logger.info(f"Retrying task {task_id} in {delay:.2f} seconds")
                await asyncio.sleep(delay)
        
        # Todas as tentativas falharam
        circuit_breaker.record_failure()
        error_msg = f"Task {task_id} failed after {retry_config.max_retries} attempts: {str(last_exception)}"
        self.state_manager.fail_task(task_id, error_msg)
        
        logger.error(error_msg)
        if last_exception is not None:
            raise last_exception
        raise RuntimeError(error_msg)

    async def _run_task_function(self, task_func: Callable) -> Any:
        """Executa função da tarefa (sync ou async)"""
        if asyncio.iscoroutinefunction(task_func):
            return await task_func()
        else:
            # Executa função síncrona em thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, task_func)

    async def execute_all_pending_tasks(
        self,
        task_functions: Dict[TaskType, Callable],
        max_concurrent: int = 5,
        timeout_per_task: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executa todas as tarefas pendentes com controle de concorrência
        
        Args:
            task_functions: Mapeamento de tipo de tarefa para função
            max_concurrent: Máximo de tarefas concorrentes
            timeout_per_task: Timeout por tarefa em segundos
            
        Returns:
            Resultados das execuções
        """
        pending_tasks = self.state_manager.get_pending_tasks()
        if not pending_tasks:
            logger.info("No pending tasks to execute")
            return {}

        logger.info(f"Executing {len(pending_tasks)} pending tasks with max concurrency {max_concurrent}")
        
        # Cria semáforo para controlar concorrência
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def execute_with_semaphore(task: TaskState):
            async with semaphore:
                task_func = task_functions.get(task.task_type)
                if not task_func:
                    error_msg = f"No function defined for task type {task.task_type.value}"
                    self.state_manager.skip_task(task.task_id, error_msg)
                    return None
                
                try:
                    result = await self.execute_task(
                        task.task_id,
                        task_func,
                        task.task_type,
                        timeout_per_task
                    )
                    results[task.task_id] = result
                    return result
                except Exception as e:
                    logger.error(f"Failed to execute task {task.task_id}: {e}")
                    results[task.task_id] = None
                    return None

        # Executa todas as tarefas pendentes
        await asyncio.gather(
            *[execute_with_semaphore(task) for task in pending_tasks],
            return_exceptions=True
        )
        
        logger.info(f"Completed execution of {len(pending_tasks)} tasks")
        return results

    def get_execution_progress(self) -> Dict[str, Any]:
        """
        Retorna progresso da execução atual
        
        Returns:
            Informações de progresso
        """
        if not self.state_manager.current_execution:
            return {}

        summary = self.state_manager.get_execution_summary()
        
        # Adiciona informações dos circuit breakers
        circuit_status = {}
        for task_type, cb in self.circuit_breakers.items():
            circuit_status[task_type] = {
                'state': cb.state.value,
                'failure_count': cb.failure_count,
                'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None,
                'next_attempt': cb.next_attempt_time.isoformat() if cb.next_attempt_time else None
            }
        
        summary['circuit_breakers'] = circuit_status
        return summary

    def reset_circuit_breaker(self, task_type: TaskType):
        """
        Reseta circuit breaker para um tipo de tarefa
        
        Args:
            task_type: Tipo da tarefa
        """
        key = task_type.value
        if key in self.circuit_breakers:
            self.circuit_breakers[key].record_success()
            logger.info(f"Reset circuit breaker for {task_type.value}")

    def reset_all_circuit_breakers(self):
        """Reseta todos os circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.record_success()
        logger.info("Reset all circuit breakers")

    async def execute_with_dependencies(
        self,
        task_functions: Dict[TaskType, Callable],
        dependencies: Optional[Dict[TaskType, List[TaskType]]] = None,
        max_concurrent: int = 5,
        timeout_per_task: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executa tarefas respeitando dependências
        
        Args:
            task_functions: Mapeamento de tipo de tarefa para função
            dependencies: Dependências entre tarefas
            max_concurrent: Máximo de tarefas concorrentes
            timeout_per_task: Timeout por tarefa
            
        Returns:
            Resultados das execuções
        """
        if not dependencies:
            dependencies = self._get_default_dependencies()

        pending_tasks = {task.task_type: task for task in self.state_manager.get_pending_tasks()}
        completed_types = {task.task_type for task in self.state_manager.get_completed_tasks()}
        results = {}
        
        # Executa em ondas respeitando dependências
        while pending_tasks:
            # Encontra tarefas que podem ser executadas (dependências satisfeitas)
            ready_tasks = []
            for task_type, task in pending_tasks.items():
                deps = dependencies.get(task_type, [])
                if all(dep in completed_types for dep in deps):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Deadlock ou dependências circulares
                remaining_types = list(pending_tasks.keys())
                logger.error(f"No tasks ready to execute. Remaining: {remaining_types}")
                break
            
            logger.info(f"Executing wave of {len(ready_tasks)} tasks")
            
            # Executa tarefas prontas
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def execute_ready_task(task: TaskState):
                async with semaphore:
                    task_func = task_functions.get(task.task_type)
                    if not task_func:
                        error_msg = f"No function defined for task type {task.task_type.value}"
                        self.state_manager.skip_task(task.task_id, error_msg)
                        return None
                    
                    try:
                        result = await self.execute_task(
                            task.task_id,
                            task_func,
                            task.task_type,
                            timeout_per_task
                        )
                        results[task.task_id] = result
                        completed_types.add(task.task_type)
                        return result
                    except Exception as e:
                        logger.error(f"Failed to execute task {task.task_id}: {e}")
                        # Remove das pendentes mesmo se falhou para evitar loop infinito
                        completed_types.add(task.task_type)
                        return None
            
            await asyncio.gather(
                *[execute_ready_task(task) for task in ready_tasks],
                return_exceptions=True
            )
            
            # Remove tarefas executadas das pendentes
            for task in ready_tasks:
                pending_tasks.pop(task.task_type, None)
        
        return results

    def _get_default_dependencies(self) -> Dict[TaskType, List[TaskType]]:
        """Dependências padrão entre tarefas"""
        return {
            TaskType.EC2_RECOMMENDATIONS: [TaskType.EC2_METRICS],
            TaskType.LAMBDA_RECOMMENDATIONS: [TaskType.LAMBDA_METRICS],
            TaskType.RDS_RECOMMENDATIONS: [TaskType.RDS_METRICS],
            TaskType.REPORT_GENERATION: [
                TaskType.COST_ANALYSIS,
                TaskType.EC2_METRICS,
                TaskType.LAMBDA_METRICS,
                TaskType.EC2_RECOMMENDATIONS,
                TaskType.LAMBDA_RECOMMENDATIONS
            ]
        }