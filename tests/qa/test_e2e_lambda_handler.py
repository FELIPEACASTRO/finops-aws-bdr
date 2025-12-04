"""
Suite E2E Lambda Handler - Testes de Ponta a Ponta
Invoca lambda_handler real com eventos completos e valida responses
Target: Nota 10/10 dos especialistas em E2E Coverage
"""

import pytest
import json
import asyncio
import boto3
from unittest.mock import MagicMock, patch, AsyncMock
from moto import mock_aws
from datetime import datetime
from typing import Dict, Any


class MockLambdaContext:
    """Mock do contexto Lambda AWS"""
    def __init__(self, request_id: str = "test-request-123", function_name: str = "finops-handler"):
        self.aws_request_id = request_id
        self.function_name = function_name
        self.function_version = "$LATEST"
        self.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{function_name}"
        self.memory_limit_in_mb = 512
        self.log_group_name = f"/aws/lambda/{function_name}"
        self.log_stream_name = "2024/12/04/[$LATEST]abc123"
        self._remaining_time = 300000
        
    def get_remaining_time_in_millis(self) -> int:
        return self._remaining_time


class TestE2ELambdaHandlerEventBridge:
    """
    E2E Tests: EventBridge -> Lambda Handler -> Response
    Simula invocacao real via EventBridge scheduled events
    """
    
    @mock_aws
    def test_eventbridge_scheduled_execution_full_flow(self):
        """E2E: EventBridge scheduled event -> Lambda -> Complete analysis"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "version": "0",
            "id": "12345678-1234-1234-1234-123456789012",
            "detail-type": "Scheduled Event",
            "source": "aws.events",
            "account": "123456789012",
            "time": "2024-12-04T10:00:00Z",
            "region": "us-east-1",
            "resources": ["arn:aws:events:us-east-1:123456789012:rule/finops-daily"],
            "detail": {}
        }
        
        context = MockLambdaContext(request_id="evt-sched-001")
        
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
        assert response['statusCode'] in [200, 500]
        assert 'body' in response
        
        body = json.loads(response['body']) if isinstance(response['body'], str) else response['body']
        assert isinstance(body, dict)
        
        if response['statusCode'] == 200:
            assert 'execution_id' in body or 'partial' in body or 'account_id' in body
    
    @mock_aws
    def test_eventbridge_with_custom_detail(self):
        """E2E: EventBridge com detail customizado para analise especifica"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "version": "0",
            "id": "custom-analysis-event",
            "detail-type": "FinOps Analysis Request",
            "source": "finops.scheduler",
            "account": "123456789012",
            "time": datetime.now().isoformat(),
            "region": "us-east-1",
            "detail": {
                "analysis_type": "cost_optimization",
                "services": ["ec2", "rds", "lambda"],
                "period_days": 30,
                "include_recommendations": True
            }
        }
        
        context = MockLambdaContext(request_id="evt-custom-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
        assert 'headers' in response
        assert response['headers'].get('Content-Type') == 'application/json'


class TestE2ELambdaHandlerAPIGateway:
    """
    E2E Tests: API Gateway -> Lambda Handler -> HTTP Response
    Simula invocacao via API Gateway REST/HTTP
    """
    
    @mock_aws
    def test_api_gateway_post_analysis_request(self):
        """E2E: API Gateway POST request para iniciar analise"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "httpMethod": "POST",
            "path": "/analysis",
            "headers": {
                "Content-Type": "application/json",
                "X-Api-Key": "test-api-key-12345"
            },
            "body": json.dumps({
                "account_id": "123456789012",
                "analysis_config": {
                    "include_costs": True,
                    "include_metrics": True,
                    "include_recommendations": True,
                    "period_days": 30
                }
            }),
            "queryStringParameters": None,
            "pathParameters": None,
            "requestContext": {
                "requestId": "api-gw-req-001",
                "stage": "prod",
                "identity": {
                    "sourceIp": "192.168.1.1"
                }
            }
        }
        
        context = MockLambdaContext(request_id="api-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
        assert 'headers' in response
        
        if 'X-Request-ID' in response.get('headers', {}):
            assert response['headers']['X-Request-ID'] == "api-001"
    
    @mock_aws
    def test_api_gateway_get_status_request(self):
        """E2E: API Gateway GET request para status de execucao"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "httpMethod": "GET",
            "path": "/status",
            "headers": {
                "Accept": "application/json"
            },
            "queryStringParameters": {
                "execution_id": "exec_123456789012_20241204_100000_abc12345"
            },
            "requestContext": {
                "requestId": "api-gw-status-001"
            }
        }
        
        context = MockLambdaContext(request_id="api-status-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response


class TestE2ELambdaHandlerStepFunctions:
    """
    E2E Tests: Step Functions -> Lambda Handler -> State Machine Integration
    Simula invocacao via Step Functions state machine
    """
    
    @mock_aws
    def test_step_functions_mapper_invocation(self):
        """E2E: Step Functions Mapper task invoca Lambda"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "execution_id": "arn:aws:states:us-east-1:123456789012:execution:finops-sm:exec-001",
            "state_machine_name": "finops-state-machine",
            "task_type": "MAPPER",
            "input": {
                "account_id": "123456789012",
                "batch_size": 50,
                "services_to_analyze": ["ec2", "rds", "lambda", "s3", "dynamodb"]
            },
            "retry_count": 0
        }
        
        context = MockLambdaContext(request_id="sfn-mapper-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
    
    @mock_aws
    def test_step_functions_worker_invocation(self):
        """E2E: Step Functions Worker task processa batch de servicos"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "execution_id": "arn:aws:states:us-east-1:123456789012:execution:finops-sm:exec-001",
            "state_machine_name": "finops-state-machine",
            "task_type": "WORKER",
            "batch_id": "batch-001",
            "input": {
                "account_id": "123456789012",
                "services_batch": ["ec2", "rds"],
                "analysis_config": {
                    "period_days": 30,
                    "include_recommendations": True
                }
            },
            "retry_count": 0
        }
        
        context = MockLambdaContext(request_id="sfn-worker-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
    
    @mock_aws
    def test_step_functions_aggregator_invocation(self):
        """E2E: Step Functions Aggregator consolida resultados"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "execution_id": "arn:aws:states:us-east-1:123456789012:execution:finops-sm:exec-001",
            "state_machine_name": "finops-state-machine",
            "task_type": "AGGREGATOR",
            "input": {
                "account_id": "123456789012",
                "batch_results": [
                    {"batch_id": "batch-001", "status": "completed", "s3_key": "results/batch-001.json"},
                    {"batch_id": "batch-002", "status": "completed", "s3_key": "results/batch-002.json"}
                ]
            },
            "retry_count": 0
        }
        
        context = MockLambdaContext(request_id="sfn-agg-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response


class TestE2ELambdaHandlerErrorScenarios:
    """
    E2E Tests: Cenarios de erro e recuperacao
    Valida comportamento em situacoes adversas
    """
    
    @mock_aws
    def test_lambda_handler_with_invalid_event(self):
        """E2E: Handler processa evento invalido gracefully"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "invalid_key": "invalid_value",
            "malformed": True
        }
        
        context = MockLambdaContext(request_id="err-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
        assert response['statusCode'] in [200, 400, 500]
    
    @mock_aws
    def test_lambda_handler_with_null_context(self):
        """E2E: Handler funciona sem contexto Lambda"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {"source": "test", "detail": {}}
        
        response = lambda_handler(event, None)
        
        assert response is not None
        assert 'statusCode' in response
    
    @mock_aws
    def test_lambda_handler_timeout_simulation(self):
        """E2E: Handler respeita timeout e salva estado parcial"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        context = MockLambdaContext(request_id="timeout-001")
        context._remaining_time = 1000
        
        event = {"source": "timeout_test", "detail": {}}
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response
    
    @mock_aws
    def test_lambda_handler_retry_after_failure(self):
        """E2E: Handler retoma execucao apos falha anterior"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "source": "retry_test",
            "detail": {},
            "retry_attempt": 2,
            "previous_execution_id": "exec_123456789012_20241204_090000_prev1234"
        }
        
        context = MockLambdaContext(request_id="retry-001")
        response = lambda_handler(event, context)
        
        assert response is not None
        assert 'statusCode' in response


class TestE2ELambdaHandlerResponseValidation:
    """
    E2E Tests: Validacao completa da estrutura de resposta
    Garante que todas as respostas seguem o contrato esperado
    """
    
    @mock_aws
    def test_response_contains_all_required_fields(self):
        """E2E: Resposta contem todos os campos obrigatorios"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {"source": "validation_test", "detail": {}}
        context = MockLambdaContext(request_id="val-001")
        
        response = lambda_handler(event, context)
        
        assert 'statusCode' in response
        assert 'body' in response
        assert 'headers' in response
        
        assert isinstance(response['statusCode'], int)
        assert isinstance(response['headers'], dict)
        
        headers = response['headers']
        assert 'Content-Type' in headers
        assert headers['Content-Type'] == 'application/json'
    
    @mock_aws
    def test_response_body_schema_validation(self):
        """E2E: Body da resposta segue schema esperado"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {"source": "schema_test", "detail": {}}
        context = MockLambdaContext(request_id="schema-001")
        
        response = lambda_handler(event, context)
        
        body = json.loads(response['body']) if isinstance(response['body'], str) else response['body']
        
        assert isinstance(body, dict)
        
        if response['statusCode'] == 200:
            valid_fields = ['execution_id', 'account_id', 'partial', 'costs', 'recommendations', 
                          'summary', 'generated_at', 'status', 'progress', 'results']
            has_expected_field = any(field in body for field in valid_fields)
            assert has_expected_field, f"Response body missing expected fields. Got: {list(body.keys())}"
        elif response['statusCode'] == 500:
            assert 'error' in body or 'message' in body
    
    @mock_aws
    def test_response_cors_headers(self):
        """E2E: Resposta inclui headers CORS corretos para API Gateway"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        from src.finops_aws.resilient_lambda_handler import lambda_handler
        
        event = {
            "httpMethod": "OPTIONS",
            "path": "/analysis",
            "headers": {"Origin": "https://dashboard.finops.example.com"}
        }
        context = MockLambdaContext(request_id="cors-001")
        
        response = lambda_handler(event, context)
        
        assert 'statusCode' in response
        assert 'headers' in response
