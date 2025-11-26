"""
Testes unitários para OptimizerService
"""
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.finops_aws.services.optimizer_service import OptimizerService
from src.finops_aws.models.finops_models import OptimizationRecommendation


class TestOptimizerService:
    """Testes para o serviço de otimização"""
    
    @pytest.fixture
    def optimizer_service(self):
        """Fixture para OptimizerService"""
        with patch('src.finops_aws.services.optimizer_service.get_compute_optimizer_client'):
            return OptimizerService()
    
    @pytest.fixture
    def mock_ec2_recommendation(self):
        """Mock de recomendação EC2"""
        return {
            'instanceArn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0',
            'currentInstanceType': 't3.xlarge',
            'finding': 'OVER_PROVISIONED',
            'recommendationOptions': [
                {
                    'instanceType': 't3.large',
                    'estimatedMonthlySavings': {
                        'currency': 'USD',
                        'value': 45.67
                    }
                },
                {
                    'instanceType': 't3.medium',
                    'estimatedMonthlySavings': {
                        'currency': 'USD',
                        'value': 67.89
                    }
                }
            ],
            'utilizationMetrics': [
                {
                    'name': 'CPU',
                    'statistic': {
                        'maximum': 25.5
                    }
                },
                {
                    'name': 'MEMORY',
                    'statistic': {
                        'maximum': 40.2
                    }
                }
            ]
        }
    
    @pytest.fixture
    def mock_lambda_recommendation(self):
        """Mock de recomendação Lambda"""
        return {
            'functionArn': 'arn:aws:lambda:us-east-1:123456789012:function:my-function',
            'currentMemorySize': 1024,
            'finding': 'OVER_PROVISIONED',
            'memorySizeRecommendationOptions': [
                {
                    'memorySize': 512,
                    'estimatedMonthlySavings': {
                        'currency': 'USD',
                        'value': 12.34
                    }
                }
            ],
            'utilizationMetrics': [
                {
                    'name': 'MEMORY',
                    'statistic': {
                        'maximum': 45.8
                    }
                }
            ]
        }
    
    def test_is_compute_optimizer_enabled_true(self, optimizer_service):
        """Testa verificação quando Compute Optimizer está habilitado"""
        optimizer_service.client.get_enrollment_status = Mock(return_value={'status': 'Active'})
        
        result = optimizer_service.is_compute_optimizer_enabled()
        
        assert result is True
        assert optimizer_service._optimizer_enabled is True
    
    def test_is_compute_optimizer_enabled_false(self, optimizer_service):
        """Testa verificação quando Compute Optimizer não está habilitado"""
        error = ClientError(
            error_response={'Error': {'Code': 'OptInRequiredException'}},
            operation_name='GetEnrollmentStatus'
        )
        optimizer_service.client.get_enrollment_status = Mock(side_effect=error)
        
        result = optimizer_service.is_compute_optimizer_enabled()
        
        assert result is False
        assert optimizer_service._optimizer_enabled is False
    
    def test_process_ec2_recommendation(self, optimizer_service, mock_ec2_recommendation):
        """Testa processamento de recomendação EC2"""
        result = optimizer_service._process_ec2_recommendation(mock_ec2_recommendation)
        
        assert isinstance(result, OptimizationRecommendation)
        assert result.resource_id == 'i-1234567890abcdef0'
        assert result.resource_type == 'EC2'
        assert result.current_configuration == 't3.xlarge'
        assert result.recommended_configurations == ['t3.large', 't3.medium']
        assert result.estimated_monthly_savings == 45.67  # Primeira opção
        assert result.finding == 'OVER_PROVISIONED'
        assert result.utilization_metrics == {'cpu': 25.5, 'memory': 40.2}
    
    def test_process_lambda_recommendation(self, optimizer_service, mock_lambda_recommendation):
        """Testa processamento de recomendação Lambda"""
        result = optimizer_service._process_lambda_recommendation(mock_lambda_recommendation)
        
        assert isinstance(result, OptimizationRecommendation)
        assert result.resource_id == 'my-function'
        assert result.resource_type == 'Lambda'
        assert result.current_configuration == '1024MB'
        assert result.recommended_configurations == ['512MB']
        assert result.estimated_monthly_savings == 12.34
        assert result.finding == 'OVER_PROVISIONED'
        assert result.utilization_metrics == {'memory': 45.8}
    
    def test_get_ec2_recommendations_enabled(self, optimizer_service, mock_ec2_recommendation):
        """Testa obtenção de recomendações EC2 quando habilitado"""
        optimizer_service.is_compute_optimizer_enabled = Mock(return_value=True)
        
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {'instanceRecommendations': [mock_ec2_recommendation]}
        ]
        optimizer_service.client.get_paginator = Mock(return_value=mock_paginator)
        
        result = optimizer_service.get_ec2_recommendations()
        
        assert len(result) == 1
        assert isinstance(result[0], OptimizationRecommendation)
        assert result[0].resource_id == 'i-1234567890abcdef0'
    
    def test_get_ec2_recommendations_disabled(self, optimizer_service):
        """Testa obtenção de recomendações EC2 quando desabilitado"""
        optimizer_service.is_compute_optimizer_enabled = Mock(return_value=False)
        
        result = optimizer_service.get_ec2_recommendations()
        
        assert result == []
    
    def test_get_lambda_recommendations_enabled(self, optimizer_service, mock_lambda_recommendation):
        """Testa obtenção de recomendações Lambda quando habilitado"""
        optimizer_service.is_compute_optimizer_enabled = Mock(return_value=True)
        
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {'lambdaFunctionRecommendations': [mock_lambda_recommendation]}
        ]
        optimizer_service.client.get_paginator = Mock(return_value=mock_paginator)
        
        result = optimizer_service.get_lambda_recommendations()
        
        assert len(result) == 1
        assert isinstance(result[0], OptimizationRecommendation)
        assert result[0].resource_id == 'my-function'
    
    def test_get_all_recommendations(self, optimizer_service):
        """Testa obtenção de todas as recomendações"""
        mock_ec2_rec = OptimizationRecommendation(
            resource_id='i-123',
            resource_type='EC2',
            current_configuration='t3.large',
            recommended_configurations=['t3.medium'],
            estimated_monthly_savings=25.0
        )
        
        mock_lambda_rec = OptimizationRecommendation(
            resource_id='function1',
            resource_type='Lambda',
            current_configuration='1024MB',
            recommended_configurations=['512MB'],
            estimated_monthly_savings=10.0
        )
        
        optimizer_service.get_ec2_recommendations = Mock(return_value=[mock_ec2_rec])
        optimizer_service.get_lambda_recommendations = Mock(return_value=[mock_lambda_rec])
        
        result = optimizer_service.get_all_recommendations()
        
        assert 'ec2_recommendations' in result
        assert 'lambda_recommendations' in result
        assert len(result['ec2_recommendations']) == 1
        assert len(result['lambda_recommendations']) == 1
    
    def test_calculate_total_savings_potential(self, optimizer_service):
        """Testa cálculo do potencial total de economia"""
        recommendations = {
            'ec2_recommendations': [
                OptimizationRecommendation(
                    resource_id='i-123',
                    resource_type='EC2',
                    current_configuration='t3.large',
                    recommended_configurations=['t3.medium'],
                    estimated_monthly_savings=25.50
                ),
                OptimizationRecommendation(
                    resource_id='i-456',
                    resource_type='EC2',
                    current_configuration='t3.xlarge',
                    recommended_configurations=['t3.large'],
                    estimated_monthly_savings=45.75
                )
            ],
            'lambda_recommendations': [
                OptimizationRecommendation(
                    resource_id='function1',
                    resource_type='Lambda',
                    current_configuration='1024MB',
                    recommended_configurations=['512MB'],
                    estimated_monthly_savings=12.25
                )
            ]
        }
        
        result = optimizer_service.calculate_total_savings_potential(recommendations)
        
        # 25.50 + 45.75 + 12.25 = 83.50
        assert result == 83.50