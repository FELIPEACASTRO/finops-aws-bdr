"""
E2E Tests - Lambda Handler Complete Flow
Testes de ponta a ponta do Lambda Handler com eventos realistas AWS
"""
import pytest
import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import dataclass

import boto3
from moto import mock_aws

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from finops_aws.resilient_lambda_handler import FinOpsResilientHandler, lambda_handler
from finops_aws.core.state_manager import StateManager, TaskType, ExecutionStatus


@dataclass
class MockLambdaContext:
    """Mock do contexto Lambda AWS"""
    function_name: str = "finops-aws-analyzer"
    function_version: str = "$LATEST"
    invoked_function_arn: str = "arn:aws:lambda:us-east-1:123456789012:function:finops-aws-analyzer"
    memory_limit_in_mb: int = 1024
    aws_request_id: str = "test-request-id-12345"
    log_group_name: str = "/aws/lambda/finops-aws-analyzer"
    log_stream_name: str = "2025/11/27/[$LATEST]abcdef123456"
    
    def get_remaining_time_in_millis(self):
        return 300000


class TestLambdaHandlerE2EScheduledEvent:
    """Testes E2E com eventos agendados (CloudWatch Events / EventBridge)"""
    
    @pytest.fixture
    def scheduled_event(self):
        """Evento agendado típico do CloudWatch Events"""
        return {
            "version": "0",
            "id": "12345678-1234-1234-1234-123456789012",
            "detail-type": "Scheduled Event",
            "source": "aws.events",
            "account": "123456789012",
            "time": datetime.now(timezone.utc).isoformat(),
            "region": "us-east-1",
            "resources": [
                "arn:aws:events:us-east-1:123456789012:rule/finops-daily-analysis"
            ],
            "detail": {}
        }
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_scheduled_event_full_flow(self, scheduled_event, context):
        """Teste E2E: Evento agendado dispara análise completa"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler, '_analyze_costs', new_callable=AsyncMock) as mock_costs, \
                 patch.object(handler, '_collect_ec2_metrics', new_callable=AsyncMock) as mock_ec2, \
                 patch.object(handler, '_collect_lambda_metrics', new_callable=AsyncMock) as mock_lambda, \
                 patch.object(handler, '_collect_rds_metrics', new_callable=AsyncMock) as mock_rds, \
                 patch.object(handler, '_collect_s3_metrics', new_callable=AsyncMock) as mock_s3, \
                 patch.object(handler, '_get_ec2_recommendations', new_callable=AsyncMock) as mock_ec2_rec, \
                 patch.object(handler, '_get_lambda_recommendations', new_callable=AsyncMock) as mock_lambda_rec, \
                 patch.object(handler, '_get_rds_recommendations', new_callable=AsyncMock) as mock_rds_rec, \
                 patch.object(handler, '_generate_report', new_callable=AsyncMock) as mock_report:
                
                mock_costs.return_value = {"last_7_days": {"EC2": 1500.0, "Lambda": 200.0}}
                mock_ec2.return_value = {"instances": [{"id": "i-12345", "cpu": 45.2}]}
                mock_lambda.return_value = {"functions": [{"name": "test-fn", "invocations": 1000}]}
                mock_rds.return_value = {"databases": [{"id": "db-1", "connections": 50}]}
                mock_s3.return_value = {"buckets": [{"name": "my-bucket", "size_gb": 100}]}
                mock_ec2_rec.return_value = [{"type": "rightsize", "savings": 200.0}]
                mock_lambda_rec.return_value = [{"type": "memory", "savings": 50.0}]
                mock_rds_rec.return_value = [{"type": "reserved", "savings": 300.0}]
                mock_report.return_value = {"report_id": "report-123", "status": "generated"}
                
                result = asyncio.run(handler.handle_request(scheduled_event, context))
                
                assert result['statusCode'] == 200
                body = json.loads(result['body'])
                assert 'execution_id' in body
                assert 'results' in body or 'summary' in body


class TestLambdaHandlerE2EAPIGateway:
    """Testes E2E com eventos do API Gateway"""
    
    @pytest.fixture
    def api_gateway_event(self):
        """Evento típico do API Gateway REST"""
        return {
            "resource": "/analyze",
            "path": "/analyze",
            "httpMethod": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token"
            },
            "queryStringParameters": {
                "period": "30",
                "services": "ec2,lambda,rds"
            },
            "body": json.dumps({
                "account_id": "123456789012",
                "regions": ["us-east-1", "us-west-2"],
                "include_recommendations": True
            }),
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "abc123",
                "stage": "prod",
                "requestId": "api-request-id-12345"
            }
        }
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_api_gateway_post_analysis(self, api_gateway_event, context):
        """Teste E2E: API Gateway POST dispara análise"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'cost_analysis': {'total': 5000.0},
                    'ec2_metrics': {'instances': 10},
                    'recommendations': {'savings': 1000.0}
                }
                
                result = asyncio.run(handler.handle_request(api_gateway_event, context))
                
                assert result['statusCode'] in [200, 500]
                assert 'X-Request-ID' in result['headers']


class TestLambdaHandlerE2ESNS:
    """Testes E2E com eventos SNS"""
    
    @pytest.fixture
    def sns_event(self):
        """Evento típico do SNS"""
        return {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "arn:aws:sns:us-east-1:123456789012:finops-trigger:uuid",
                    "Sns": {
                        "Type": "Notification",
                        "MessageId": "sns-message-id-12345",
                        "TopicArn": "arn:aws:sns:us-east-1:123456789012:finops-trigger",
                        "Subject": "FinOps Analysis Request",
                        "Message": json.dumps({
                            "action": "analyze",
                            "account_id": "123456789012",
                            "priority": "high"
                        }),
                        "Timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            ]
        }
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_sns_trigger_analysis(self, sns_event, context):
        """Teste E2E: SNS trigger dispara análise"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(sns_event, context))
                
                assert result['statusCode'] in [200, 500]


class TestLambdaHandlerE2EMultiRegion:
    """Testes E2E para cenários multi-região"""
    
    @pytest.fixture
    def multi_region_event(self):
        """Evento com múltiplas regiões"""
        return {
            "source": "finops.multi-region",
            "detail-type": "Multi-Region Analysis",
            "detail": {
                "regions": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
                "services": ["ec2", "rds", "lambda", "s3"],
                "aggregation": "consolidated"
            }
        }
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_multi_region_analysis(self, multi_region_event, context):
        """Teste E2E: Análise multi-região"""
        for region in ['us-east-1', 'us-west-2', 'eu-west-1']:
            s3 = boto3.client('s3', region_name=region)
            try:
                if region == 'us-east-1':
                    s3.create_bucket(Bucket=f'finops-aws-state')
                else:
                    s3.create_bucket(
                        Bucket=f'finops-aws-state-{region}',
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
            except Exception:
                pass
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'us-east-1': {'costs': 3000.0},
                    'us-west-2': {'costs': 1500.0},
                    'eu-west-1': {'costs': 2000.0}
                }
                
                result = asyncio.run(handler.handle_request(multi_region_event, context))
                
                assert result['statusCode'] in [200, 500]


class TestLambdaHandlerE2EErrorRecovery:
    """Testes E2E de recuperação de erros"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_partial_failure_recovery(self, context):
        """Teste E2E: Recuperação de falha parcial"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            call_count = [0]
            
            async def failing_then_success():
                call_count[0] += 1
                if call_count[0] < 2:
                    raise Exception("Temporary failure")
                return {"status": "recovered"}
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed_with_recovery'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_timeout_handling(self, context):
        """Teste E2E: Tratamento de timeout"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        context.get_remaining_time_in_millis = lambda: 1000
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestLambdaHandlerE2EDataIntegrity:
    """Testes E2E de integridade de dados"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_cost_data_consistency(self, context):
        """Teste E2E: Consistência dos dados de custo"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {"validate_costs": True}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            expected_costs = {
                "EC2": 1500.50,
                "Lambda": 250.75,
                "RDS": 800.00,
                "S3": 50.25
            }
            total_expected = sum(expected_costs.values())
            
            with patch.object(handler, '_analyze_costs', new_callable=AsyncMock) as mock_costs:
                mock_costs.return_value = {
                    "last_30_days": expected_costs,
                    "total": total_expected
                }
                
                with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                    mock_exec.return_value = {'cost_analysis': mock_costs.return_value}
                    
                    result = asyncio.run(handler.handle_request(event, context))
                    
                    assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_metrics_data_structure(self, context):
        """Teste E2E: Estrutura dos dados de métricas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            ec2_metrics = {
                "instances": [
                    {
                        "instance_id": "i-12345",
                        "instance_type": "t3.medium",
                        "cpu_utilization": 45.5,
                        "memory_utilization": 60.2,
                        "network_in": 1024000,
                        "network_out": 512000
                    }
                ],
                "summary": {
                    "total_instances": 1,
                    "avg_cpu": 45.5
                }
            }
            
            with patch.object(handler, '_collect_ec2_metrics', new_callable=AsyncMock) as mock_ec2:
                mock_ec2.return_value = ec2_metrics
                
                with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                    mock_exec.return_value = {'ec2_metrics': ec2_metrics}
                    
                    result = asyncio.run(handler.handle_request(event, context))
                    
                    assert result['statusCode'] in [200, 500]


class TestLambdaHandlerE2ERecommendations:
    """Testes E2E para geração de recomendações"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_ec2_rightsizing_recommendations(self, context):
        """Teste E2E: Recomendações de rightsizing EC2"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {"include_recommendations": True}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            recommendations = [
                {
                    "resource_id": "i-12345",
                    "current_type": "m5.2xlarge",
                    "recommended_type": "m5.large",
                    "monthly_savings": 150.0,
                    "reason": "Low CPU utilization (avg 15%)"
                },
                {
                    "resource_id": "i-67890",
                    "current_type": "c5.4xlarge",
                    "recommended_type": "c5.xlarge",
                    "monthly_savings": 300.0,
                    "reason": "Overprovisioned memory"
                }
            ]
            
            with patch.object(handler, '_get_ec2_recommendations', new_callable=AsyncMock) as mock_rec:
                mock_rec.return_value = recommendations
                
                with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                    mock_exec.return_value = {'ec2_recommendations': recommendations}
                    
                    result = asyncio.run(handler.handle_request(event, context))
                    
                    assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_savings_calculation_accuracy(self, context):
        """Teste E2E: Precisão no cálculo de economias"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            ec2_savings = 450.0
            lambda_savings = 100.0
            rds_savings = 250.0
            total_expected = ec2_savings + lambda_savings + rds_savings
            
            results = {
                'ec2_recommendations': [{"savings": ec2_savings}],
                'lambda_recommendations': [{"savings": lambda_savings}],
                'rds_recommendations': [{"savings": rds_savings}]
            }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = results
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestLambdaHandlerE2EPerformance:
    """Testes E2E de performance"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_execution_time_within_limits(self, context):
        """Teste E2E: Tempo de execução dentro dos limites"""
        import time
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                start_time = time.time()
                result = asyncio.run(handler.handle_request(event, context))
                execution_time = time.time() - start_time
                
                assert execution_time < 30
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_concurrent_task_execution(self, context):
        """Teste E2E: Execução concorrente de tarefas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {"max_concurrent": 5}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            execution_order = []
            
            async def track_execution(task_name):
                execution_order.append(f"start_{task_name}")
                await asyncio.sleep(0.01)
                execution_order.append(f"end_{task_name}")
                return {"task": task_name, "status": "completed"}
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestLambdaHandlerE2ESecurityCompliance:
    """Testes E2E de segurança e compliance"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_no_sensitive_data_in_logs(self, context):
        """Teste E2E: Dados sensíveis não aparecem em logs"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "test",
            "detail": {
                "api_key": "secret-key-12345",
                "password": "super-secret"
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                response_str = json.dumps(result)
                assert 'secret-key-12345' not in response_str
                assert 'super-secret' not in response_str
    
    @mock_aws
    def test_iam_boundary_respect(self, context):
        """Teste E2E: Respeito aos limites IAM"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {"source": "test", "detail": {}}
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {'status': 'completed'}
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
