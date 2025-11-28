"""
Testes E2E - Fluxo Completo FinOps AWS
Valida mapper → workers → aggregator → relatório
"""
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Imports do projeto
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from finops_aws.lambda_mapper import lambda_handler as mapper_handler
from finops_aws.lambda_aggregator import lambda_handler as aggregator_handler
from finops_aws.multi_account_handler import lambda_handler as multi_account_handler
from finops_aws.forecasting_engine import CostForecaster, lambda_handler as forecasting_handler
from finops_aws.api_gateway_handler import lambda_handler as api_handler


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
    
    def test_mapper_creates_batches(self, mock_context, mock_env):
        """Testa se mapper cria batches corretamente"""
        event = {
            'source': 'scheduled',
            'analysis_type': 'full',
            'input': {}
        }
        
        with patch('finops_aws.lambda_mapper.boto3'):
            result = mapper_handler(event, mock_context)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['status'] == 'success'
            assert body['total_batches'] > 0
            assert body['total_services'] > 0
            assert len(body['batches']) == body['total_batches']
    
    def test_aggregator_consolidates_results(self, mock_context, mock_env):
        """Testa se aggregator consolida resultados"""
        event = {
            'execution_id': 'test-exec-123',
            'batch_results': [
                {
                    'batch_id': 'batch-0',
                    'services': {'ec2': True, 'lambda': True},
                    'costs': {
                        'by_service': {'ec2': 100.0, 'lambda': 50.0},
                        'by_category': {'compute': 150.0}
                    },
                    'recommendations': [
                        {'type': 'unused-instance', 'savings': 50.0}
                    ],
                    'metrics': {
                        'resources_analyzed': 5,
                        'anomalies_detected': 0,
                        'optimizations_found': 1
                    }
                }
            ],
            'start_time': datetime.utcnow().isoformat()
        }
        
        with patch('finops_aws.lambda_aggregator.boto3'):
            result = aggregator_handler(event, mock_context)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['status'] == 'SUCCESS'
            assert body['summary']['total_services_analyzed'] > 0
    
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
    
    def test_api_gateway_health_check(self):
        """Testa endpoint de health check"""
        event = {
            'httpMethod': 'GET',
            'path': '/v1/health'
        }
        
        with patch('finops_aws.api_gateway_handler.boto3'):
            result = api_handler(event, None)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['status'] == 'healthy'
    
    def test_api_gateway_start_analysis(self):
        """Testa iniciar análise via API"""
        event = {
            'httpMethod': 'POST',
            'path': '/v1/analysis',
            'body': json.dumps({
                'analysis_type': 'full',
                'regions': ['us-east-1']
            })
        }
        
        with patch('finops_aws.api_gateway_handler.boto3') as mock_boto3:
            # Mock Step Functions
            mock_sfn = MagicMock()
            mock_sfn.start_execution.return_value = {
                'executionArn': 'arn:aws:states:us-east-1:123456789:execution:finops:test-123',
                'startDate': datetime.utcnow()
            }
            mock_boto3.client.return_value = mock_sfn
            
            # Set environment
            os.environ['STEPFUNCTIONS_ARN'] = 'arn:aws:states:us-east-1:123456789:stateMachine:finops'
            
            result = api_handler(event, None)
            
            assert result['statusCode'] == 202
            body = json.loads(result['body'])
            assert body['status'] == 'accepted'
    
    def test_complete_batch_processing(self, mock_context, mock_env):
        """Testa processamento completo de um batch"""
        # Simula: mapper → batch → aggregator
        
        with patch('finops_aws.lambda_mapper.boto3'):
            # 1. Mapper cria batches
            mapper_event = {'source': 'scheduled', 'analysis_type': 'full', 'input': {}}
            mapper_result = mapper_handler(mapper_event, mock_context)
            mapper_body = json.loads(mapper_result['body'])
            
            assert mapper_body['status'] == 'success'
            assert mapper_body['total_batches'] > 0
            
            # 2. Aggregator processa resultados
            with patch('finops_aws.lambda_aggregator.boto3'):
                agg_event = {
                    'execution_id': 'test-exec',
                    'batch_results': [
                        {
                            'batch_id': 'batch-0',
                            'costs': {'by_service': {}, 'by_category': {}},
                            'recommendations': [],
                            'metrics': {
                                'resources_analyzed': 0,
                                'anomalies_detected': 0,
                                'optimizations_found': 0
                            }
                        }
                    ],
                    'start_time': datetime.utcnow().isoformat()
                }
                
                agg_result = aggregator_handler(agg_event, mock_context)
                agg_body = json.loads(agg_result['body'])
                
                assert agg_body['status'] == 'SUCCESS'
    
    def test_error_handling_in_pipeline(self, mock_context, mock_env):
        """Testa tratamento de erros no pipeline"""
        event = {
            'execution_id': 'test-exec-error',
            'batch_results': None,  # Erro simulado
            'start_time': datetime.utcnow().isoformat()
        }
        
        with patch('finops_aws.lambda_aggregator.boto3'):
            # Deve retornar erro sem crashear
            try:
                result = aggregator_handler(event, mock_context)
                # Verifica se recuperou do erro gracefully
                assert result['statusCode'] in [200, 500]
            except Exception as e:
                pytest.fail(f"Handler crashed: {str(e)}")


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
