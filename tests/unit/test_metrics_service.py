"""
Testes unitários para MetricsService
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.finops_aws.services.metrics_service import MetricsService
from src.finops_aws.models.finops_models import EC2InstanceUsage, LambdaFunctionUsage


class TestMetricsService:
    """Testes para o serviço de métricas"""
    
    @pytest.fixture
    def metrics_service(self):
        """Fixture para MetricsService"""
        with patch('src.finops_aws.services.metrics_service.get_cloudwatch_client'), \
             patch('src.finops_aws.services.metrics_service.get_ec2_client'), \
             patch('src.finops_aws.services.metrics_service.get_lambda_client'):
            return MetricsService()
    
    @pytest.fixture
    def mock_ec2_instances(self):
        """Mock de instâncias EC2"""
        return [
            {
                'InstanceId': 'i-1234567890abcdef0',
                'InstanceType': 't3.medium',
                'State': 'running',
                'AvailabilityZone': 'us-east-1a'
            },
            {
                'InstanceId': 'i-0987654321fedcba0',
                'InstanceType': 't3.large',
                'State': 'stopped',
                'AvailabilityZone': 'us-east-1b'
            }
        ]
    
    @pytest.fixture
    def mock_ec2_response(self):
        """Mock de resposta do describe_instances"""
        return {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running'},
                            'Placement': {'AvailabilityZone': 'us-east-1a'}
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def mock_cloudwatch_response(self):
        """Mock de resposta do CloudWatch"""
        return {
            'Datapoints': [
                {'Average': 25.5, 'Timestamp': datetime.now()},
                {'Average': 30.2, 'Timestamp': datetime.now()},
                {'Average': 28.1, 'Timestamp': datetime.now()}
            ]
        }
    
    def test_get_ec2_instances(self, metrics_service, mock_ec2_response):
        """Testa obtenção de instâncias EC2"""
        metrics_service.ec2.describe_instances = Mock(return_value=mock_ec2_response)
        
        result = metrics_service.get_ec2_instances()
        
        assert len(result) == 1
        assert result[0]['InstanceId'] == 'i-1234567890abcdef0'
        assert result[0]['InstanceType'] == 't3.medium'
        assert result[0]['State'] == 'running'
        assert result[0]['AvailabilityZone'] == 'us-east-1a'
    
    def test_get_ec2_cpu_utilization(self, metrics_service, mock_cloudwatch_response):
        """Testa obtenção de utilização de CPU do EC2"""
        metrics_service.cloudwatch.get_metric_statistics = Mock(return_value=mock_cloudwatch_response)
        
        result = metrics_service.get_ec2_cpu_utilization('i-1234567890abcdef0', 7)
        
        # Média dos datapoints: (25.5 + 30.2 + 28.1) / 3 = 27.93
        expected_avg = round((25.5 + 30.2 + 28.1) / 3, 2)
        assert result == expected_avg
        
        # Verifica parâmetros da chamada
        call_args = metrics_service.cloudwatch.get_metric_statistics.call_args[1]
        assert call_args['Namespace'] == 'AWS/EC2'
        assert call_args['MetricName'] == 'CPUUtilization'
        assert call_args['Period'] == 3600
        assert call_args['Statistics'] == ['Average']
    
    def test_get_ec2_cpu_utilization_no_data(self, metrics_service):
        """Testa obtenção de CPU sem dados disponíveis"""
        metrics_service.cloudwatch.get_metric_statistics = Mock(return_value={'Datapoints': []})
        
        result = metrics_service.get_ec2_cpu_utilization('i-1234567890abcdef0', 7)
        
        assert result is None
    
    def test_get_lambda_functions(self, metrics_service):
        """Testa obtenção de funções Lambda"""
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {
                'Functions': [
                    {'FunctionName': 'function1'},
                    {'FunctionName': 'function2'}
                ]
            }
        ]
        
        metrics_service.lambda_client.get_paginator = Mock(return_value=mock_paginator)
        
        result = metrics_service.get_lambda_functions()
        
        assert result == ['function1', 'function2']
    
    def test_get_lambda_metrics(self, metrics_service):
        """Testa obtenção de métricas do Lambda"""
        mock_responses = {
            'Invocations': {'Datapoints': [{'Sum': 100}, {'Sum': 150}]},
            'Duration': {'Datapoints': [{'Average': 250.5}, {'Average': 300.2}]},
            'Errors': {'Datapoints': [{'Sum': 2}]},
            'Throttles': {'Datapoints': []}
        }
        
        def mock_get_metric_statistics(**kwargs):
            metric_name = kwargs['MetricName']
            return mock_responses.get(metric_name, {'Datapoints': []})
        
        metrics_service.cloudwatch.get_metric_statistics = Mock(side_effect=mock_get_metric_statistics)
        
        result = metrics_service.get_lambda_metrics('test-function', 7)
        
        assert result['invocations'] == 250  # 100 + 150
        assert result['duration'] == (250.5 + 300.2) / 2  # Média
        assert result['errors'] == 2
        assert result['throttles'] is None  # Sem dados
    
    def test_get_ec2_usage_data(self, metrics_service, mock_ec2_response):
        """Testa obtenção completa de dados de uso do EC2"""
        metrics_service.ec2.describe_instances = Mock(return_value=mock_ec2_response)
        metrics_service.get_ec2_cpu_utilization = Mock(side_effect=[25.5, 27.3, 30.1])
        
        result = metrics_service.get_ec2_usage_data()
        
        assert len(result) == 1
        assert isinstance(result[0], EC2InstanceUsage)
        assert result[0].instance_id == 'i-1234567890abcdef0'
        assert result[0].instance_type == 't3.medium'
        assert result[0].avg_cpu_7d == 25.5
        assert result[0].avg_cpu_15d == 27.3
        assert result[0].avg_cpu_30d == 30.1
    
    def test_get_lambda_usage_data(self, metrics_service):
        """Testa obtenção completa de dados de uso do Lambda"""
        metrics_service.get_lambda_functions = Mock(return_value=['function1', 'function2'])
        metrics_service.get_lambda_metrics = Mock(return_value={
            'invocations': 100,
            'duration': 250.5,
            'errors': 2,
            'throttles': 0
        })
        
        result = metrics_service.get_lambda_usage_data()
        
        assert len(result) == 2
        assert all(isinstance(usage, LambdaFunctionUsage) for usage in result)
        assert result[0].function_name == 'function1'
        assert result[0].invocations_7d == 100
        assert result[0].avg_duration_7d == 250.5
        assert result[0].errors_7d == 2
        assert result[0].throttles_7d == 0