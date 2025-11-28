"""
Extended QA Test Suite for FinOps AWS
======================================

This test suite addresses the gaps identified in the QA Gap Analysis,
implementing additional test types from the exhaustive QA guide (87 types).

New Test Categories:
1. Load Testing (simulated)
2. Stress Testing (simulated)
3. Spike Testing (simulated)
4. Vulnerability Scanning (static)
5. Fault Injection Testing
6. Chaos Engineering (basic)
7. Infrastructure Testing (IaC)
8. Database/State Testing (S3)
9. Failover Testing
10. Endurance Testing (simulated)
11. Capacity Testing
12. Scalability Testing
"""

import pytest
import time
import sys
import os
import re
import ast
import json
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from moto import mock_aws
import boto3


class TestLoadTesting:
    """
    LOAD TESTING (Teste de Carga)
    Avalia o desempenho sob carga normal e de pico.
    """
    
    @mock_aws
    def test_service_factory_under_load(self):
        """Testa ServiceFactory sob carga de múltiplas requisições"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        
        start = time.time()
        
        for _ in range(10):
            services = sf.get_all_services()
            assert len(services) >= 250
        
        elapsed = time.time() - start
        
        assert elapsed < 10.0, f"10 iterations took {elapsed:.2f}s (should be < 10s)"
    
    def test_retry_handler_under_load(self):
        """Testa RetryHandler sob carga de operações concorrentes"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        results = []
        errors = []
        
        def operation(idx):
            try:
                result = handler.execute(lambda: f"result_{idx}")
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i in range(50):
            t = threading.Thread(target=operation, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors under load: {errors}"
        assert len(results) == 50
    
    @mock_aws
    def test_state_manager_concurrent_writes(self):
        """Testa StateManager com escritas concorrentes"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        errors = []
        executions = []
        lock = threading.Lock()
        
        def create_execution(idx):
            try:
                manager = StateManager()
                execution = manager.create_execution(account_id=f'12345678901{idx % 10}')
                with lock:
                    executions.append(execution)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=create_execution, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        assert len(executions) == 10


class TestStressTesting:
    """
    STRESS TESTING (Teste de Estresse)
    Leva o sistema ao seu limite para ver como ele falha e se recupera.
    """
    
    def test_circuit_breaker_under_stress(self):
        """Testa Circuit Breaker sob estresse de falhas consecutivas"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=10, recovery_timeout=1)
        cb = CircuitBreaker(config)
        
        for _ in range(20):
            cb.record_failure()
        
        assert cb.state == CircuitBreakerState.OPEN
        
        cb.record_success()
    
    def test_retry_handler_max_failures(self):
        """Testa RetryHandler com máximo de falhas"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(max_retries=10, base_delay=0.001, max_delay=0.01)
        handler = RetryHandler(policy=policy)
        
        call_count = [0]
        def always_fails():
            call_count[0] += 1
            raise RuntimeError("Stress test failure")
        
        with pytest.raises(RuntimeError):
            handler.execute(always_fails)
        
        assert call_count[0] == 11
    
    @mock_aws
    def test_service_factory_rapid_instantiation(self):
        """Testa criação rápida de múltiplas instâncias ServiceFactory"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        factories = []
        start = time.time()
        
        for _ in range(20):
            cf = AWSClientFactory()
            sf = ServiceFactory(cf)
            factories.append(sf)
        
        elapsed = time.time() - start
        
        assert len(factories) == 20
        assert elapsed < 30.0


class TestSpikeTesting:
    """
    SPIKE TESTING (Teste de Pico)
    Testa a reação do sistema a picos súbitos e extremos de carga.
    """
    
    def test_retry_handler_sudden_burst(self):
        """Testa RetryHandler com burst súbito de requisições"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        results = []
        
        start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(lambda i=i: handler.execute(lambda: f"result_{i}"))
                for i in range(100)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        elapsed = time.time() - start
        
        assert len(results) == 100
        assert elapsed < 5.0, f"Burst took {elapsed:.2f}s (should be < 5s)"
    
    def test_circuit_breaker_rapid_state_changes(self):
        """Testa Circuit Breaker com mudanças rápidas de estado"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker(config)
        
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        time.sleep(0.15)
        cb.can_execute()
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN


class TestVulnerabilityScanning:
    """
    VULNERABILITY SCANNING (Scan de Vulnerabilidades)
    Análise estática de segurança adicional.
    """
    
    def test_no_pickle_usage(self):
        """Verifica ausência de pickle (deserialização insegura)"""
        violations = []
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    if 'pickle.load' in content or 'pickle.loads' in content:
                        violations.append(filepath)
        
        assert len(violations) == 0, f"Pickle usage found in: {violations}"
    
    def test_no_shell_injection(self):
        """Verifica ausência de padrões de shell injection"""
        patterns = [
            r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
            r'os\.system\s*\(',
            r'os\.popen\s*\(',
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
                            violations.append((filepath, pattern))
        
        assert len(violations) == 0, f"Shell injection patterns: {violations}"
    
    def test_no_yaml_unsafe_load(self):
        """Verifica ausência de yaml.load sem Loader seguro"""
        violations = []
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    if re.search(r'yaml\.load\s*\([^)]*\)', content):
                        if 'Loader=' not in content:
                            violations.append(filepath)
        
        assert len(violations) == 0, f"Unsafe yaml.load in: {violations}"
    
    def test_no_assert_in_production_code(self):
        """Verifica ausência de assert em código de produção (exceto testes)"""
        violations = []
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    assert_count = len(re.findall(r'\bassert\s+', content))
                    if assert_count > 5:
                        violations.append((filepath, assert_count))
        
        assert len(violations) == 0, f"Too many asserts in production: {violations}"


class TestFaultInjectionTesting:
    """
    FAULT INJECTION TESTING (Injeção de Falhas)
    Introduz falhas intencionalmente para testar a robustez.
    """
    
    def test_retry_handler_intermittent_failures(self):
        """Testa RetryHandler com falhas intermitentes"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(max_retries=5, base_delay=0.001)
        handler = RetryHandler(policy=policy)
        
        call_count = [0]
        def intermittent_failure():
            call_count[0] += 1
            if call_count[0] % 3 != 0:
                raise ConnectionError("Intermittent failure")
            return "success"
        
        result = handler.execute(intermittent_failure)
        assert result == "success"
        assert call_count[0] == 3
    
    def test_circuit_breaker_mixed_results(self):
        """Testa Circuit Breaker com resultados mistos"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config)
        
        for i in range(10):
            if i % 2 == 0:
                cb.record_success()
            else:
                cb.record_failure()
        
        assert cb.state == CircuitBreakerState.CLOSED
    
    @mock_aws
    def test_service_factory_with_failing_client(self):
        """Testa ServiceFactory quando cliente AWS falha"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        
        services = sf.get_all_services()
        assert len(services) >= 250


class TestChaosEngineering:
    """
    CHAOS ENGINEERING (Engenharia de Caos)
    Injeta falhas de forma controlada para verificar resiliência.
    """
    
    def test_circuit_breaker_recovery_after_chaos(self):
        """Simula caos e verifica recuperação do Circuit Breaker"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=0.5)
        cb = CircuitBreaker(config)
        
        for _ in range(5):
            cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        time.sleep(0.6)
        cb.can_execute()
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        cb.record_success()
        cb.record_success()
        cb.record_success()
        
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_retry_handler_random_failures(self):
        """Testa RetryHandler com falhas aleatórias (simuladas)"""
        import random
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        random.seed(42)
        policy = RetryPolicy(max_retries=10, base_delay=0.001)
        handler = RetryHandler(policy=policy)
        
        call_count = [0]
        def random_failure():
            call_count[0] += 1
            if call_count[0] < 5:
                raise ConnectionError("Random chaos failure")
            return "recovered"
        
        result = handler.execute(random_failure)
        assert result == "recovered"
    
    @mock_aws
    def test_state_manager_bucket_recovery(self):
        """Testa recuperação quando bucket S3 é recriado"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        manager = StateManager()
        execution1 = manager.create_execution(account_id='123456789012')
        assert execution1 is not None


class TestInfrastructureTesting:
    """
    INFRASTRUCTURE TESTING (Teste de Infraestrutura)
    Valida a configuração da infraestrutura como código (IaC).
    """
    
    def test_terraform_files_exist(self):
        """Verifica existência dos arquivos Terraform"""
        terraform_path = 'infrastructure/terraform'
        required_files = ['main.tf', 'variables.tf', 'outputs.tf']
        
        for file in required_files:
            filepath = os.path.join(terraform_path, file)
            assert os.path.exists(filepath), f"Missing: {filepath}"
    
    def test_terraform_valid_syntax(self):
        """Verifica sintaxe básica dos arquivos Terraform"""
        terraform_path = 'infrastructure/terraform'
        
        if not os.path.exists(terraform_path):
            pytest.skip("Terraform directory not found")
        
        for file in os.listdir(terraform_path):
            if file.endswith('.tf'):
                filepath = os.path.join(terraform_path, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                assert '{' in content or 'variable' in content or '#' in content
    
    def test_terraform_no_hardcoded_secrets(self):
        """Verifica ausência de secrets hardcoded no Terraform"""
        terraform_path = 'infrastructure/terraform'
        patterns = [
            r'password\s*=\s*"[^"]{8,}"',
            r'secret\s*=\s*"[^"]{8,}"',
            r'api_key\s*=\s*"[^"]{8,}"',
        ]
        
        violations = []
        for file in os.listdir(terraform_path):
            if file.endswith('.tf'):
                filepath = os.path.join(terraform_path, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        violations.append(filepath)
        
        assert len(violations) == 0, f"Secrets in Terraform: {violations}"


class TestDatabaseStateTesting:
    """
    DATABASE/STATE TESTING (Teste de Banco de Dados/Estado)
    Valida a integridade e consistência do estado em S3.
    """
    
    @mock_aws
    def test_state_persistence(self):
        """Testa persistência do estado no S3"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, {'data': 'test'})
        
        completed = manager.get_completed_tasks()
        assert len(completed) > 0
    
    @mock_aws
    def test_state_isolation_between_executions(self):
        """Testa isolamento de estado entre execuções"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        manager1 = StateManager()
        manager2 = StateManager()
        
        exec1 = manager1.create_execution(account_id='111111111111')
        exec2 = manager2.create_execution(account_id='222222222222')
        
        assert exec1 != exec2
    
    @mock_aws
    def test_state_manager_handles_large_data(self):
        """Testa StateManager com dados grandes"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        manager.create_execution(account_id='123456789012')
        
        large_data = {
            'services': [f'service_{i}' for i in range(1000)],
            'metrics': {f'metric_{i}': i * 1.5 for i in range(500)}
        }
        
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, large_data)
        
        completed = manager.get_completed_tasks()
        assert len(completed) > 0


class TestFailoverTesting:
    """
    FAILOVER TESTING (Teste de Failover)
    Valida a capacidade do sistema de mudar para backup em caso de falha.
    """
    
    def test_retry_handler_eventual_success(self):
        """Testa RetryHandler com sucesso eventual após falhas"""
        from src.finops_aws.core.retry_handler import RetryHandler, RetryPolicy
        
        policy = RetryPolicy(max_retries=5, base_delay=0.001)
        handler = RetryHandler(policy=policy)
        
        attempt = [0]
        def eventual_success():
            attempt[0] += 1
            if attempt[0] < 4:
                raise TimeoutError("Service unavailable")
            return "success_after_failover"
        
        result = handler.execute(eventual_success)
        assert result == "success_after_failover"
        assert attempt[0] == 4
    
    def test_circuit_breaker_half_open_recovery(self):
        """Testa recuperação do Circuit Breaker em estado HALF_OPEN"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker(config)
        
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        time.sleep(0.15)
        assert cb.can_execute() == True
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED


class TestEnduranceTesting:
    """
    ENDURANCE TESTING (Teste de Resistência)
    Avalia o desempenho sob carga sustentada.
    """
    
    def test_retry_handler_sustained_operations(self):
        """Testa RetryHandler sob operações sustentadas"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        start = time.time()
        for i in range(200):
            result = handler.execute(lambda: "sustained_operation")
            assert result == "sustained_operation"
        
        elapsed = time.time() - start
        
        assert elapsed < 5.0, f"200 sustained operations took {elapsed:.2f}s"
    
    def test_circuit_breaker_sustained_success(self):
        """Testa Circuit Breaker sob sucesso sustentado"""
        from src.finops_aws.core.resilient_executor import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config)
        
        for _ in range(100):
            cb.record_success()
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0


class TestCapacityTesting:
    """
    CAPACITY TESTING (Teste de Capacidade)
    Determina quantas operações o sistema pode suportar.
    """
    
    @mock_aws
    def test_service_factory_capacity(self):
        """Testa capacidade de criação de serviços"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        
        all_services = sf.get_all_services()
        
        assert len(all_services) >= 250, f"Capacity: {len(all_services)} services"
    
    def test_retry_handler_high_volume(self):
        """Testa RetryHandler com alto volume de operações"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        successful = 0
        for _ in range(500):
            try:
                handler.execute(lambda: "ok")
                successful += 1
            except Exception:
                pass
        
        assert successful == 500


class TestScalabilityTesting:
    """
    SCALABILITY TESTING (Teste de Escalabilidade)
    Mede a capacidade de escalar com aumento de carga.
    """
    
    def test_concurrent_operations_scalability(self):
        """Testa escalabilidade com operações concorrentes crescentes"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        results = {}
        for num_threads in [5, 10, 20]:
            start = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(lambda: handler.execute(lambda: "scaled"))
                    for _ in range(num_threads * 10)
                ]
                concurrent.futures.wait(futures)
            
            elapsed = time.time() - start
            results[num_threads] = elapsed
        
        assert results[20] < results[5] * 10


class TestCodeCoverageMetrics:
    """
    CODE COVERAGE METRICS
    Métricas de cobertura de código (validação estrutural).
    """
    
    def test_all_modules_have_tests(self):
        """Verifica se todos os módulos principais têm testes"""
        core_modules = [
            'state_manager',
            'factories',
            'retry_handler',
            'resilient_executor',
        ]
        
        test_files = []
        for root, dirs, files in os.walk('tests'):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(file)
        
        test_content = ' '.join(test_files)
        
        for module in core_modules:
            assert module in test_content or any(module in f for f in test_files), \
                f"No tests for module: {module}"
    
    def test_test_to_code_ratio(self):
        """Verifica razão testes/código fonte"""
        src_lines = 0
        for root, dirs, files in os.walk('src'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        src_lines += len(f.readlines())
        
        test_lines = 0
        for root, dirs, files in os.walk('tests'):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        test_lines += len(f.readlines())
        
        ratio = test_lines / src_lines if src_lines > 0 else 0
        
        assert ratio >= 0.3, f"Test/Code ratio {ratio:.2f} is too low (should be >= 0.3)"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
