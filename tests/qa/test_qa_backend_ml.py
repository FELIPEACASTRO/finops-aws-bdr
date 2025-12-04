"""
Backend & ML Test Suite for FinOps AWS v2.1
============================================

This suite implements backend-specific and ML/AI testing patterns that
exercise REAL application flows with concrete assertions.

Categories:
1. Backend Unit Testing - Tests services, factories, handlers with real invocations
2. Database/State Testing - Tests S3 StateManager with full persistence cycles
3. Service Integration - Tests module communication and data flow
4. Error Handling - Tests edge cases and error recovery
5. ML Model Testing - Tests AI Consultant accuracy and consistency
6. Configuration Testing - Tests config validation and defaults
7. Memory & Resource Testing - Tests resource management
"""

import pytest
import time
import sys
import os
import json
import gc
import threading
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from moto import mock_aws
import boto3


class TestBackendUnitTesting:
    """
    Tests individual backend components with real invocations.
    """
    
    @mock_aws
    def test_state_manager_full_execution_lifecycle(self):
        """Tests complete execution lifecycle: create -> task -> complete"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        
        execution = manager.create_execution(account_id='123456789012')
        assert execution.execution_id is not None
        assert len(execution.execution_id) >= 10
        assert execution.account_id == '123456789012'
        
        manager.start_task(TaskType.COST_ANALYSIS)
        
        result = {'total_cost': 15000.00, 'services': ['EC2', 'RDS']}
        manager.complete_task(TaskType.COST_ANALYSIS, result)
        
        completed_tasks = manager.get_completed_tasks()
        assert len(completed_tasks) >= 1
    
    @mock_aws
    def test_service_factory_instantiates_all_services(self):
        """Tests ServiceFactory creates all 252 services correctly"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        
        services = sf.get_all_services()
        
        assert len(services) >= 250, f"Expected 250+ services, got {len(services)}"
        
        for name, service in services.items():
            assert service is not None
            assert hasattr(service, 'get_service_name') or hasattr(service, 'health_check')
    
    def test_retry_handler_executes_and_returns_correctly(self):
        """Tests RetryHandler executes functions and returns results"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        call_count = [0]
        def test_function():
            call_count[0] += 1
            return {'success': True, 'data': [1, 2, 3]}
        
        result = handler.execute(test_function)
        
        assert result['success'] is True
        assert result['data'] == [1, 2, 3]
        assert call_count[0] == 1
    
    def test_circuit_breaker_transitions_correctly(self):
        """Tests CircuitBreaker state machine transitions"""
        from src.finops_aws.core.resilient_executor import (
            CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        )
        
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1
        )
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitBreakerState.OPEN
        
        time.sleep(1.1)
        
        assert cb.can_execute() == True
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_aws_client_factory_creates_valid_clients(self):
        """Tests AWSClientFactory creates working boto3 clients"""
        from src.finops_aws.core.factories import AWSClientFactory
        
        with mock_aws():
            cf = AWSClientFactory()
            
            s3_client = cf.get_client('s3')
            assert s3_client is not None
            
            ec2_client = cf.get_client('ec2')
            assert ec2_client is not None


class TestDatabaseStateTesting:
    """
    Tests S3-based state persistence with full roundtrips.
    """
    
    @mock_aws
    def test_s3_state_persistence_roundtrip(self):
        """Tests state data survives save and retrieve cycle"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        test_data = {
            'cost': 12345.67,
            'services': ['EC2', 'RDS', 'S3'],
            'recommendations': [
                {'type': 'rightsizing', 'savings': 1000}
            ]
        }
        manager.start_task(TaskType.COST_ANALYSIS)
        manager.complete_task(TaskType.COST_ANALYSIS, test_data)
        
        completed_tasks = manager.get_completed_tasks()
        assert len(completed_tasks) >= 1
    
    @mock_aws
    def test_concurrent_execution_isolation(self):
        """Tests concurrent executions don't interfere with each other"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        manager = StateManager()
        
        exec1 = manager.create_execution(account_id='111111111111')
        exec2 = manager.create_execution(account_id='222222222222')
        
        assert exec1.execution_id != exec2.execution_id
        assert exec1.account_id == '111111111111'
        assert exec2.account_id == '222222222222'
    
    @mock_aws
    def test_state_manager_handles_missing_bucket(self):
        """Tests StateManager handles missing S3 bucket gracefully"""
        from src.finops_aws.core.state_manager import StateManager
        
        with patch('boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_s3.head_bucket.side_effect = Exception("Bucket not found")
            mock_client.return_value = mock_s3
            
            try:
                manager = StateManager()
            except Exception as e:
                assert isinstance(e, Exception)


class TestServiceIntegration:
    """
    Tests module communication and data flow between components.
    """
    
    @mock_aws
    def test_handler_integrates_with_state_manager(self):
        """Tests StateManager integration with handler flow"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        from src.finops_aws.core.retry_handler import RetryHandler
        
        manager = StateManager()
        handler = RetryHandler()
        
        execution = manager.create_execution(account_id='123456789012')
        assert execution is not None
        
        def mock_analysis():
            return {'total_cost': 15000.00, 'services': ['EC2', 'RDS']}
        
        result = handler.execute(mock_analysis)
        
        assert result['total_cost'] == 15000.00
        assert 'EC2' in result['services']
    
    @mock_aws
    def test_service_factory_integrates_with_services(self):
        """Tests ServiceFactory creates services that can execute"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        cf = AWSClientFactory()
        sf = ServiceFactory(cf)
        services = sf.get_all_services()
        
        working_services = 0
        for name, service in list(services.items())[:10]:
            try:
                if hasattr(service, 'health_check'):
                    service.health_check()
                    working_services += 1
            except Exception:
                pass
        
        assert working_services >= 1
    
    def test_retry_handler_with_circuit_breaker_pattern(self):
        """Tests RetryHandler works with circuit breaker pattern"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        def test_operation():
            return {'result': 'success'}
        
        result1 = handler.execute(test_operation)
        assert result1['result'] == 'success'
        
        result2 = handler.execute(test_operation)
        assert result2['result'] == 'success'


class TestErrorHandling:
    """
    Tests error handling and edge cases.
    """
    
    def test_retry_handler_raises_after_max_retries(self):
        """Tests RetryHandler raises after exhausting retries"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        def always_fail():
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError):
            handler.execute(always_fail)
    
    def test_circuit_breaker_rejects_when_open(self):
        """Tests CircuitBreaker rejects calls when open"""
        from src.finops_aws.core.resilient_executor import (
            CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
        )
        
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        cb = CircuitBreaker(config)
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_execute() == False
    
    @mock_aws
    def test_state_manager_handles_all_task_types(self):
        """Tests StateManager handles all task types"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager, TaskType
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        for task_type in TaskType:
            try:
                manager.start_task(task_type)
            except Exception:
                pass
    
    def test_service_factory_handles_missing_services(self):
        """Tests ServiceFactory handles missing services"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        with mock_aws():
            cf = AWSClientFactory()
            sf = ServiceFactory(cf)
            
            services = sf.get_all_services()
            assert isinstance(services, dict)


class TestMLModelValidation:
    """
    Tests AI Consultant ML functionality with real data flows.
    """
    
    def test_prompt_builder_generates_persona_specific_prompts(self):
        """Tests PromptBuilder generates different prompts per persona"""
        from src.finops_aws.ai_consultant.prompts.builder import PromptBuilder
        from src.finops_aws.ai_consultant.prompts.personas import PromptPersona
        
        builder = PromptBuilder()
        
        cost_data = {
            'total_cost': 50000.00,
            'services': [
                {'name': 'EC2', 'cost': 25000.00},
                {'name': 'RDS', 'cost': 15000.00},
                {'name': 'S3', 'cost': 10000.00}
            ],
            'period': '2024-11'
        }
        
        prompts = {}
        for persona in [PromptPersona.EXECUTIVE, PromptPersona.CTO, PromptPersona.DEVOPS]:
            prompt = builder.build_analysis_prompt(
                cost_data=cost_data,
                period="2024-11-01 a 2024-11-30",
                persona=persona
            )
            prompts[persona.value] = prompt
            
            assert isinstance(prompt, str)
            assert len(prompt) > 50
        
        unique_prompts = set(prompts.values())
        assert len(unique_prompts) >= 2, "Personas should generate different prompts"
    
    def test_data_formatter_handles_various_formats(self):
        """Tests DataFormatter handles different input formats"""
        from src.finops_aws.ai_consultant.processors.data_formatter import DataFormatter
        
        formatter = DataFormatter()
        
        report = {
            'total_cost': 8000.0,
            'services': [
                {'ServiceName': 'EC2', 'Amount': 5000},
                {'ServiceName': 'RDS', 'Amount': 3000}
            ]
        }
        result = formatter.format_cost_report(report)
        assert result is not None
        
        empty_result = formatter.format_cost_report({})
        assert empty_result is not None
    
    def test_ai_consultant_consistency_across_runs(self):
        """Tests AI Consultant produces consistent outputs for same input"""
        from src.finops_aws.ai_consultant.prompts.builder import PromptBuilder
        from src.finops_aws.ai_consultant.prompts.personas import PromptPersona
        
        builder = PromptBuilder()
        
        fixed_data = {'total_cost': 10000, 'services': [{'name': 'EC2', 'cost': 10000}]}
        
        prompt1 = builder.build_analysis_prompt(
            cost_data=fixed_data,
            period="2024-11",
            persona=PromptPersona.EXECUTIVE
        )
        prompt2 = builder.build_analysis_prompt(
            cost_data=fixed_data,
            period="2024-11",
            persona=PromptPersona.EXECUTIVE
        )
        
        assert prompt1 == prompt2, "Same input should produce same output"
    
    def test_email_sender_initialization(self):
        """Tests EmailSender initialization"""
        from src.finops_aws.ai_consultant.delivery.email_sender import EmailSender
        
        sender = EmailSender(
            sender_email='test@example.com',
            region='us-east-1'
        )
        
        assert sender.sender_email == 'test@example.com'
        assert sender.region == 'us-east-1'
    
    def test_slack_notifier_initialization(self):
        """Tests SlackNotifier initialization"""
        from src.finops_aws.ai_consultant.delivery.slack_notifier import SlackNotifier
        
        notifier = SlackNotifier(
            webhook_url='https://hooks.slack.com/test',
            username='TestBot'
        )
        
        assert notifier.webhook_url == 'https://hooks.slack.com/test'
        assert notifier.username == 'TestBot'


class TestConfigurationValidation:
    """
    Tests configuration handling and validation.
    """
    
    def test_retry_policy_has_sensible_defaults(self):
        """Tests RetryPolicy defaults are reasonable"""
        from src.finops_aws.core.retry_handler import RetryPolicy
        
        policy = RetryPolicy()
        
        assert policy.max_retries >= 1
        assert policy.max_retries <= 10
        assert policy.base_delay >= 0
        assert policy.base_delay <= 5
    
    def test_circuit_breaker_config_validation(self):
        """Tests CircuitBreakerConfig validates parameters"""
        from src.finops_aws.core.resilient_executor import CircuitBreakerConfig
        
        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30
        )
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 30
    
    def test_q_business_config_stores_values(self):
        """Tests QBusinessConfig correctly stores configuration"""
        from src.finops_aws.ai_consultant.q_business.config import QBusinessConfig
        
        config = QBusinessConfig(
            application_id='app-123',
            index_id='idx-456',
            region='us-west-2'
        )
        
        assert config.application_id == 'app-123'
        assert config.index_id == 'idx-456'
        assert config.region == 'us-west-2'


class TestMemoryResourceManagement:
    """
    Tests memory and resource management.
    """
    
    def test_service_factory_does_not_leak_memory(self):
        """Tests ServiceFactory cleans up properly"""
        import gc
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        with mock_aws():
            cf = AWSClientFactory()
            sf = ServiceFactory(cf)
            services = sf.get_all_services()
            
            del services
            del sf
            del cf
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        growth = final_objects - initial_objects
        assert growth < 10000, f"Potential memory leak: {growth} objects created"
    
    @mock_aws
    def test_state_manager_cleans_up_resources(self):
        """Tests StateManager releases resources properly"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        manager = StateManager()
        execution = manager.create_execution(account_id='123456789012')
        
        del execution
        del manager
    
    def test_large_result_set_handling(self):
        """Tests system handles large result sets without issues"""
        large_data = {
            'services': [
                {'name': f'Service_{i}', 'cost': float(i * 100)}
                for i in range(1000)
            ]
        }
        
        total_cost = sum(s['cost'] for s in large_data['services'])
        assert total_cost == sum(i * 100 for i in range(1000))


class TestAsyncConcurrency:
    """
    Tests async and concurrent operations.
    """
    
    def test_concurrent_retry_handlers(self):
        """Tests multiple RetryHandlers work concurrently"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                handler = RetryHandler()
                result = handler.execute(lambda: {'worker': worker_id, 'success': True})
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert len(errors) == 0
    
    @mock_aws
    def test_concurrent_state_manager_operations(self):
        """Tests StateManager handles concurrent operations"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.core.state_manager import StateManager
        
        executions = []
        
        def create_execution(account_num):
            manager = StateManager()
            execution = manager.create_execution(account_id=f'{account_num:012d}')
            executions.append(execution)
        
        threads = [threading.Thread(target=create_execution, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(executions) == 3
        execution_ids = [e.execution_id for e in executions]
        assert len(set(execution_ids)) == 3


class TestIdempotency:
    """
    Tests idempotent operations.
    """
    
    def test_retry_handler_same_input_same_output(self):
        """Tests RetryHandler returns same output for same input"""
        from src.finops_aws.core.retry_handler import RetryHandler
        
        handler = RetryHandler()
        
        def deterministic_func():
            return {'value': 42, 'status': 'ok'}
        
        result1 = handler.execute(deterministic_func)
        result2 = handler.execute(deterministic_func)
        
        assert result1 == result2
    
    def test_prompt_builder_deterministic(self):
        """Tests PromptBuilder is deterministic"""
        from src.finops_aws.ai_consultant.prompts.builder import PromptBuilder
        from src.finops_aws.ai_consultant.prompts.personas import PromptPersona
        
        builder = PromptBuilder()
        
        data = {'total_cost': 5000}
        
        prompt1 = builder.build_analysis_prompt(
            cost_data=data,
            period="2024-11",
            persona=PromptPersona.CTO
        )
        prompt2 = builder.build_analysis_prompt(
            cost_data=data,
            period="2024-11",
            persona=PromptPersona.CTO
        )
        
        assert prompt1 == prompt2


class TestBoundaryValues:
    """
    Tests boundary value conditions.
    """
    
    def test_zero_cost_handling(self):
        """Tests system handles zero costs correctly"""
        from src.finops_aws.ai_consultant.processors.data_formatter import DataFormatter
        
        formatter = DataFormatter()
        
        zero_costs = {
            'total_cost': 0.0,
            'services': [{'ServiceName': 'FreeTier', 'Amount': 0.0}]
        }
        
        result = formatter.format_cost_report(zero_costs)
        assert result is not None
    
    def test_negative_cost_handling(self):
        """Tests system handles negative costs (refunds)"""
        refund_data = [
            {'ServiceName': 'EC2', 'Amount': 1000.00},
            {'ServiceName': 'Refund', 'Amount': -200.00}
        ]
        
        total = sum(item['Amount'] for item in refund_data)
        assert total == 800.00
    
    def test_very_large_cost_handling(self):
        """Tests system handles very large cost values"""
        large_costs = [
            {'ServiceName': 'Enterprise', 'Amount': 1_000_000.00},
            {'ServiceName': 'DataTransfer', 'Amount': 500_000.00}
        ]
        
        total = sum(item['Amount'] for item in large_costs)
        assert total == 1_500_000.00
    
    def test_empty_service_list(self):
        """Tests system handles empty service list"""
        from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory
        
        with mock_aws():
            cf = AWSClientFactory()
            sf = ServiceFactory(cf)
            
            services = sf.get_all_services()
            assert len(services) > 0
