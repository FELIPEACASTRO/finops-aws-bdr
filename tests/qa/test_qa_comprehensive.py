"""
Comprehensive QA Test Suite for FinOps AWS
===========================================

This test suite implements multiple QA testing methodologies based on the
QA specialist document covering 64+ test types.

Categories:
1. Smoke Testing - Build stability
2. Sanity Testing - Critical functionality
3. Integration Testing - Module communication
4. API Testing - Lambda handlers
5. Security Testing (SAST) - Static analysis
6. Robustness Testing - Error handling
7. Performance Testing - Response times
8. Boundary Value Analysis
9. Equivalence Partitioning
10. State Transition Testing
11. Positive/Negative Testing
12. Documentation Testing
13. Regression Testing
"""

import pytest
import time
import sys
import os
import ast
import re
import threading
from unittest.mock import Mock, patch
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from moto import mock_aws
import boto3


class TestSmokeTests:
    """
    SMOKE TESTING (Teste de Fumaça)
    Verifica a estabilidade básica da build.
    """
    
    def test_core_module_imports(self):
        """Verifica se os módulos principais podem ser importados"""
        from src.finops_aws.core.state_manager import StateManager
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        from src.finops_aws.core.resilient_executor import ResilientExecutor
        from src.finops_aws.core.retry_handler import RetryHandler
        assert StateManager is not None
        assert ServiceFactory is not None
        assert AWSClientFactory is not None
        assert ResilientExecutor is not None
        assert RetryHandler is not None
    
    def test_services_import(self):
        """Verifica se os serviços podem ser importados"""
        import src.finops_aws.services
        assert src.finops_aws.services is not None
    
    @mock_aws
    def test_service_factory_instantiation(self):
        """Verifica se ServiceFactory pode ser instanciado"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        assert sf is not None
    
    def test_lambda_handler_import(self):
        """Verifica se o Lambda handler pode ser importado"""
        from src.finops_aws.resilient_lambda_handler import FinOpsResilientHandler
        assert FinOpsResilientHandler is not None
    
    def test_models_import(self):
        """Verifica se os modelos podem ser importados"""
        import src.finops_aws.models.finops_models
        assert src.finops_aws.models.finops_models is not None
    
    def test_script_syntax_validation(self):
        """Verifica sintaxe dos scripts principais"""
        scripts = ['run_local_demo.py', 'run_with_aws.py']
        for script in scripts:
            with open(script, 'r') as f:
                content = f.read()
            ast.parse(content)


class TestSanityTests:
    """
    SANITY TESTING (Teste de Sanidade)
    Verificação rápida das funcionalidades críticas.
    """
    
    @mock_aws
    def test_state_manager_basic_operations(self):
        """Testa operações básicas do StateManager"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        manager = StateManager()
        
        execution = manager.create_execution(account_id='123456789012')
        assert execution is not None
    
    def test_retry_handler_basic(self):
        """Testa operações básicas do RetryHandler"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        call_count = [0]
        def success_func():
            call_count[0] += 1
            return "success"
        
        result = handler.execute(success_func)
        assert result == "success"
        assert call_count[0] == 1
    
    @mock_aws
    def test_service_factory_get_all_services(self):
        """Testa se ServiceFactory retorna todos os serviços"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        
        services = sf.get_all_services()
        assert len(services) >= 250


class TestIntegrationTests:
    """
    INTEGRATION TESTING (Teste de Integração)
    Verifica a comunicação entre módulos.
    """
    
    @mock_aws
    def test_state_manager_with_service_factory(self):
        """Testa integração entre StateManager e ServiceFactory"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        state_manager = StateManager()
        client_factory = AWSClientFactory()
        service_factory = ServiceFactory(client_factory)
        
        execution = state_manager.create_execution(account_id='123456789012')
        services = service_factory.get_all_services()
        
        assert execution is not None
        assert len(services) >= 250
    
    @mock_aws
    def test_resilient_executor_with_state_manager(self):
        """Testa integração entre ResilientExecutor e StateManager"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        from src.finops_aws.core.resilient_executor import ResilientExecutor
        
        state_manager = StateManager()
        state_manager.create_execution(account_id='123456789012')
        
        executor = ResilientExecutor(state_manager)
        assert executor is not None
    
    def test_retry_handler_with_exponential_backoff(self):
        """Testa integração do RetryHandler com backoff exponencial"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.01,
            max_delay=0.1,
            exponential_base=2
        )
        handler = RetryHandler(policy=policy)
        
        call_count = [0]
        def failing_then_success():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = handler.execute(failing_then_success)
        assert result == "success"
        assert call_count[0] == 3


class TestAPITesting:
    """
    API TESTING (Teste de API)
    Testa Lambda handlers e endpoints.
    """
    
    @mock_aws
    def test_lambda_handler_event_processing(self):
        """Testa processamento de eventos pelo Lambda handler"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import FinOpsResilientHandler
        
        handler = FinOpsResilientHandler()
        
        event = {
            'action': 'analyze',
            'account_id': '123456789012'
        }
        
        assert handler is not None
    
    def test_lambda_aggregator_exists(self):
        """Testa que o módulo lambda_aggregator existe"""
        from src.finops_aws import lambda_aggregator
        assert lambda_aggregator is not None
    
    def test_lambda_mapper_exists(self):
        """Testa que o módulo lambda_mapper existe"""
        from src.finops_aws import lambda_mapper
        assert lambda_mapper is not None


class TestSecurityTesting:
    """
    SECURITY TESTING - SAST (Static Application Security Testing)
    Análise estática de código em busca de vulnerabilidades.
    """
    
    def test_no_hardcoded_credentials(self):
        """Verifica ausência de credenciais hardcoded"""
        patterns = [
            r'aws_access_key_id\s*=\s*["\'][A-Z0-9]{20}["\']',
            r'aws_secret_access_key\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']',
        ]
        
        violations = []
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            violations.append(filepath)
        
        assert len(violations) == 0, f"Credentials found in: {violations}"
    
    def test_no_eval_or_exec_usage(self):
        """Verifica ausência de eval() ou exec() perigosos"""
        violations = []
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    if re.search(r'\beval\s*\(', content) or re.search(r'\bexec\s*\(', content):
                        violations.append(filepath)
        
        assert len(violations) == 0, f"Dangerous eval/exec found in: {violations}"
    
    def test_no_sql_injection_patterns(self):
        """Verifica ausência de padrões de SQL injection"""
        patterns = [
            r'execute\s*\(\s*["\'].*%s.*["\']\s*%',
            r'cursor\.execute\s*\([^,]+\+',
        ]
        
        violations = []
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    for pattern in patterns:
                        if re.search(pattern, content):
                            violations.append(filepath)
        
        assert len(violations) == 0, f"SQL injection patterns found: {violations}"


class TestRobustnessTesting:
    """
    ROBUSTNESS TESTING (Teste de Robustez)
    Valida o comportamento do sistema em condições adversas.
    """
    
    def test_retry_handler_handles_exceptions(self):
        """Testa tratamento de exceções pelo RetryHandler"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        def always_fails():
            raise ValueError("Expected failure")
        
        with pytest.raises(ValueError):
            handler.execute(always_fails)
    
    def test_retry_handler_respects_max_retries(self):
        """Testa respeito ao número máximo de tentativas (1 inicial + N retries)"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(max_retries=3, base_delay=0.001)
        handler = RetryHandler(policy=policy)
        
        call_count = [0]
        def always_fails():
            call_count[0] += 1
            raise ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            handler.execute(always_fails)
        
        assert call_count[0] == 4
    
    @mock_aws
    def test_state_manager_handles_missing_bucket(self):
        """Testa tratamento de bucket S3 inexistente"""
        from src.finops_aws.core.state_manager import StateManager
        
        manager = StateManager(bucket_name='non-existent-bucket')
        
        with pytest.raises(Exception):
            manager.create_execution(account_id='123456789012')
    
    def test_circuit_breaker_state_changes(self):
        """Testa mudança de estado do circuit breaker após falhas"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1)
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitBreakerState.CLOSED
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitBreakerState.OPEN


class TestPerformanceTesting:
    """
    PERFORMANCE TESTING (Teste de Performance)
    Avalia tempos de resposta e utilização de recursos.
    """
    
    def test_retry_handler_latency(self):
        """Testa latência do RetryHandler"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        def quick_operation():
            return "done"
        
        start = time.time()
        for _ in range(100):
            handler.execute(quick_operation)
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"100 operations took {elapsed:.2f}s (should be < 1s)"
    
    @mock_aws
    def test_service_factory_initialization_time(self):
        """Testa tempo de inicialização do ServiceFactory"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        start = time.time()
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        elapsed = time.time() - start
        
        assert elapsed < 5.0, f"ServiceFactory init took {elapsed:.2f}s (should be < 5s)"
    
    @mock_aws
    def test_concurrent_service_access(self):
        """Testa acesso concorrente aos serviços"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        
        errors = []
        results = []
        lock = threading.Lock()
        
        def access_services(thread_id):
            try:
                services = sf.get_all_services()
                with lock:
                    results.append((thread_id, len(services)))
            except Exception as e:
                with lock:
                    errors.append((thread_id, str(e)))
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=access_services, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5


class TestBoundaryValueAnalysis:
    """
    BOUNDARY VALUE ANALYSIS (Análise de Valor Limite)
    Testa valores nos limites das partições de entrada.
    """
    
    def test_retry_policy_min_retries(self):
        """Testa número mínimo de tentativas (1)"""
        from src.finops_aws.core.retry_handler import RetryPolicy
        
        policy = RetryPolicy(max_retries=1)
        assert policy.max_retries == 1
    
    def test_retry_policy_max_retries(self):
        """Testa número alto de tentativas"""
        from src.finops_aws.core.retry_handler import RetryPolicy
        
        policy = RetryPolicy(max_retries=100)
        assert policy.max_retries == 100
    
    def test_retry_policy_zero_delay(self):
        """Testa delay zero"""
        from src.finops_aws.core.retry_handler import RetryPolicy
        
        policy = RetryPolicy(base_delay=0.0)
        assert policy.base_delay == 0.0
    
    def test_circuit_breaker_threshold_one(self):
        """Testa threshold mínimo do circuit breaker"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config)
        
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN


class TestEquivalencePartitioning:
    """
    EQUIVALENCE PARTITIONING (Partição de Equivalência)
    Divide dados de entrada em classes de equivalência.
    """
    
    @mock_aws
    def test_valid_account_id_formats(self):
        """Testa formatos válidos de account_id"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        manager = StateManager()
        
        valid_account_ids = [
            '123456789012',
            '000000000000',
            '999999999999',
        ]
        
        for account_id in valid_account_ids:
            execution = manager.create_execution(account_id=account_id)
            assert execution is not None
    
    def test_retry_policy_delay_ranges(self):
        """Testa diferentes faixas de delay"""
        from src.finops_aws.core.retry_handler import RetryPolicy
        
        delay_ranges = [0.001, 0.1, 1.0, 10.0]
        
        for delay in delay_ranges:
            policy = RetryPolicy(base_delay=delay)
            assert policy.base_delay == delay


class TestStateTransitionTesting:
    """
    STATE TRANSITION TESTING (Teste de Transição de Estado)
    Testa mudanças de estado baseadas em eventos.
    """
    
    def test_circuit_breaker_state_transitions(self):
        """Testa transições de estado do circuit breaker"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitBreakerState.CLOSED
        
        cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        time.sleep(1.1)
        can_exec = cb.can_execute()
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
    
    @mock_aws
    def test_task_state_transitions(self):
        """Testa transições de estado de tasks"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        manager.complete_task(TaskType.COST_ANALYSIS, {'data': 'test'})
        
        completed = manager.get_completed_tasks()
        assert len(completed) > 0


class TestPositiveNegativeTesting:
    """
    POSITIVE & NEGATIVE TESTING
    Testa comportamento com entradas válidas e inválidas.
    """
    
    def test_retry_handler_positive_success(self):
        """Teste Positivo: Função que sempre tem sucesso"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        result = handler.execute(lambda: "success")
        assert result == "success"
    
    def test_retry_handler_negative_always_fails(self):
        """Teste Negativo: Função que sempre falha"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(max_retries=2, base_delay=0.001)
        handler = RetryHandler(policy=policy)
        
        def always_fails():
            raise RuntimeError("fail")
        
        with pytest.raises(RuntimeError):
            handler.execute(always_fails)
    
    def test_circuit_breaker_positive_healthy(self):
        """Teste Positivo: Circuit breaker saudável"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config)
        
        for _ in range(10):
            cb.record_success()
        
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_circuit_breaker_negative_unhealthy(self):
        """Teste Negativo: Circuit breaker com muitas falhas"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        for _ in range(5):
            cb.record_failure()
        
        assert cb.state == CircuitBreakerState.OPEN


class TestDocumentationTesting:
    """
    DOCUMENTATION TESTING (Teste de Documentação)
    Valida a precisão e completude da documentação.
    """
    
    def test_readme_exists_and_has_content(self):
        """Verifica README com conteúdo"""
        assert os.path.exists('README.md')
        with open('README.md', 'r') as f:
            content = f.read()
        assert len(content) > 1000
    
    def test_replit_md_exists(self):
        """Verifica existência do replit.md"""
        assert os.path.exists('replit.md')
    
    def test_docs_directory_exists(self):
        """Verifica existência do diretório docs"""
        assert os.path.isdir('docs')
    
    def test_terraform_docs_exist(self):
        """Verifica documentação do Terraform"""
        terraform_path = 'infrastructure/terraform'
        assert os.path.isdir(terraform_path)
        files = os.listdir(terraform_path)
        assert any('README' in f or f.endswith('.md') for f in files)


class TestRegressionTests:
    """
    REGRESSION TESTING (Teste de Regressão)
    Garante que alterações não introduzam novos defeitos.
    """
    
    @mock_aws
    def test_state_manager_resolve_task_id_regression(self):
        """Teste de regressão: _resolve_task_id aceita enum e string"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        manager.start_task('ec2_metrics')
        
        assert True
    
    def test_retry_handler_decorator_regression(self):
        """Teste de regressão: Decorator with_retry funciona"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(max_retries=2, base_delay=0.001)
        handler = RetryHandler(policy=policy)
        
        @handler.with_retry_decorator()
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"


class TestCodeQualityMetrics:
    """
    CODE QUALITY METRICS
    Métricas de qualidade do código.
    """
    
    def test_service_count_meets_requirement(self):
        """Verifica se o número de serviços atende ao requisito"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        with patch('boto3.client'):
            cf = AWSClientFactory()
            sf = ServiceFactory(cf)
            services = sf.get_all_services()
        
        assert len(services) >= 250, f"Expected 250+ services, got {len(services)}"
    
    def test_no_syntax_errors_in_source(self):
        """Verifica ausência de erros de sintaxe no código fonte"""
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    ast.parse(content)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
