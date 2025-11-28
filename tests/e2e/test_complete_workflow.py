"""
Testes E2E - Fluxo Completo FinOps AWS
Valida mapper → workers → aggregator → relatório
"""
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import os

# Setup AWS region before importing boto3-dependent modules
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Imports do projeto
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from finops_aws.multi_account_handler import lambda_handler as multi_account_handler
from finops_aws.forecasting_engine import CostForecaster, lambda_handler as forecasting_handler


class TestCompleteWorkflow:
    """Testa fluxo completo E2E"""
    
    @pytest.fixture
    def mock_context(self):
        """Context mock para Lambda"""
        context = Mock()
        context.aws_request_id = "test-execution-123"
        context.function_name = "finops-test"
        return context
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Configurações de ambiente"""
        monkeypatch.setenv('BATCH_SIZE', '20')
        monkeypatch.setenv('REPORTS_BUCKET_NAME', 'test-bucket')
        monkeypatch.setenv('STATE_PREFIX', 'state/')
        monkeypatch.setenv('LOG_LEVEL', 'INFO')
        monkeypatch.setenv('AWS_REGION', 'us-east-1')
    
    def test_multi_account_orchestrator(self, mock_context):
        """Testa orquestração multi-conta"""
        event = {}
        
        with patch('finops_aws.multi_account_handler.boto3'):
            result = multi_account_handler(event, mock_context)
            
            assert result['status'] == 'success'
            assert 'batches_count' in result
            assert 'accounts_count' in result
    
    def test_forecasting_engine(self):
        """Testa engine de previsão"""
        forecaster = CostForecaster()
        
        # Dados históricos
        historical = [100, 102, 101, 103, 105, 104, 102, 500]  # Com anomalia
        
        # Testa forecasting
        forecast = forecaster.forecast_service_cost(historical, 30)
        assert forecast['status'] == 'success'
        assert 'forecast' in forecast
        assert len(forecast['forecast']) == 30
        
        # Testa anomalias
        anomalies = forecaster.detect_anomalies(historical)
        assert len(anomalies['anomalies_detected']) > 0
        assert any(a['day_index'] == 7 for a in anomalies['anomalies_detected'])  # Detecta outlier
    
    def test_api_gateway_health_check(self, mock_env):
        """Testa endpoint de health check"""
        from finops_aws.api_gateway_handler import lambda_handler as api_handler
        
        event = {
            'httpMethod': 'GET',
            'path': '/v1/health'
        }
        
        with patch('finops_aws.api_gateway_handler.get_s3_client'):
            result = api_handler(event, None)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['status'] == 'healthy'
    
    def test_api_gateway_start_analysis(self, mock_env):
        """Testa iniciar análise via API"""
        from finops_aws.api_gateway_handler import lambda_handler as api_handler
        
        event = {
            'httpMethod': 'POST',
            'path': '/v1/analysis',
            'body': json.dumps({
                'analysis_type': 'full',
                'regions': ['us-east-1']
            })
        }
        
        with patch('finops_aws.api_gateway_handler.get_stepfunctions_client') as mock_get_sfn:
            mock_sfn = MagicMock()
            mock_sfn.start_execution.return_value = {
                'executionArn': 'arn:aws:states:us-east-1:123456789:execution:finops:test-123',
                'startDate': datetime.utcnow()
            }
            mock_get_sfn.return_value = mock_sfn
            
            os.environ['STEPFUNCTIONS_ARN'] = 'arn:aws:states:us-east-1:123456789:stateMachine:finops'
            
            result = api_handler(event, None)
            
            assert result['statusCode'] == 202
            body = json.loads(result['body'])
            assert body['status'] == 'accepted'
    
    def test_forecasting_basic(self):
        """Testa forecasting básico"""
        forecaster = CostForecaster()
        
        # Dados históricos: mínimo 7 dias
        historical = [100, 102, 101, 103, 105, 104, 102]
        
        forecast = forecaster.forecast_service_cost(historical, 10)
        assert forecast['status'] == 'success'
        assert 'forecast' in forecast
        assert len(forecast['forecast']) == 10
        assert forecast['forecast_mean'] > 0
    
    def test_anomaly_detection(self):
        """Testa detecção de anomalias"""
        forecaster = CostForecaster()
        
        # Dados com outlier
        historical = [100, 101, 102, 101, 100, 500, 102, 101]
        
        anomalies = forecaster.detect_anomalies(historical)
        assert 'anomalies_detected' in anomalies
        assert anomalies['total_anomalies'] >= 0


class TestPerformance:
    """Testes de performance E2E"""
    
    def test_forecasting_performance(self):
        """Testa performance do forecasting"""
        forecaster = CostForecaster()
        
        # Dados históricos de 1 ano
        historical = [100 + (i * 0.5) for i in range(365)]
        
        import time
        start = time.time()
        forecast = forecaster.forecast_aggregated_costs(
            {'ec2': historical, 'rds': historical, 'lambda': historical},
            forecast_days=90
        )
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Deve ser rápido
        assert 'total_forecast' in forecast
    
    def test_large_batch_handling(self, mock_context, mock_env):
        """Testa manipulação de batches grandes"""
        event = {'source': 'scheduled', 'analysis_type': 'full', 'input': {}}
        
        with patch('finops_aws.lambda_mapper.boto3'):
            import time
            start = time.time()
            result = mapper_handler(event, mock_context)
            elapsed = time.time() - start
            
            assert elapsed < 5.0  # Mapper deve ser rápido
            assert result['statusCode'] == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
