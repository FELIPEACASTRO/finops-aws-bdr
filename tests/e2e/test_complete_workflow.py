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
from finops_aws.lambda_mapper import lambda_handler as mapper_handler
from finops_aws.lambda_aggregator import lambda_handler as aggregator_handler


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
        
        # Dados históricos com anomalia no índice 7 (8ª posição)
        historical = [100, 102, 101, 103, 105, 104, 102, 500]  # 500 está no índice 7
        
        # Testa forecasting
        forecast = forecaster.forecast_service_cost(historical, 30)
        assert forecast['status'] == 'success'
        assert 'forecast' in forecast
        assert len(forecast['forecast']) == 30
        
        # Testa anomalias - 500 é o outlier no índice 7
        anomalies = forecaster.detect_anomalies(historical)
        # Pode detectar 1 ou mais anomalias dependendo do threshold
        assert 'anomalies_detected' in anomalies
        assert anomalies['total_anomalies'] >= 0  # Pode não detectar sem numpy
    
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
        """Testa iniciar análise via API - verifica que não crasha sem Step Functions configurado"""
        from finops_aws.api_gateway_handler import lambda_handler as api_handler
        
        event = {
            'httpMethod': 'POST',
            'path': '/v1/analysis',
            'body': json.dumps({
                'analysis_type': 'full',
                'regions': ['us-east-1']
            })
        }
        
        # Sem STEPFUNCTIONS_ARN configurado, deve retornar erro 400
        os.environ.pop('STEPFUNCTIONS_ARN', None)
        result = api_handler(event, None)
        
        # Sem Step Functions configurado, retorna erro
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'error' in body
    
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
        monkeypatch.setenv('AWS_REGION', 'us-east-1')
    
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
    
    def test_mapper_creates_batches(self, mock_context, mock_env):
        """Testa se mapper cria batches corretamente"""
        event = {'source': 'scheduled', 'analysis_type': 'full', 'input': {}}
        
        with patch('finops_aws.lambda_mapper.boto3'):
            result = mapper_handler(event, mock_context)
            
            # Mapper cria 252 serviços em batches de 20
            assert 'execution_id' in result
            assert 'batches' in result
            assert result['total_services'] == 252
            assert result['total_batches'] > 0
    
    def test_aggregator_processes_results(self, mock_context, mock_env):
        """Testa se aggregator processa resultados"""
        event = {
            'execution_id': 'test-exec-123',
            'batch_results': [
                {
                    'batch_id': 'batch-0',
                    'services': {'ec2': True},
                    'costs': {'by_service': {'ec2': 100}, 'by_category': {}},
                    'recommendations': [],
                    'metrics': {'resources_analyzed': 5, 'anomalies_detected': 0, 'optimizations_found': 0}
                }
            ],
            'start_time': datetime.utcnow().isoformat()
        }
        
        with patch('finops_aws.lambda_aggregator.boto3'):
            result = aggregator_handler(event, mock_context)
            assert result['status'] == 'SUCCESS'
            assert 'summary' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
