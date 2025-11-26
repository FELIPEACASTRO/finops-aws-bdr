"""
Testes unitários para CostService
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.finops_aws.services.cost_service import CostService


class TestCostService:
    """Testes para o serviço de custos"""
    
    @pytest.fixture
    def cost_service(self):
        """Fixture para CostService"""
        with patch('src.finops_aws.services.cost_service.get_cost_explorer_client'):
            return CostService()
    
    @pytest.fixture
    def mock_cost_response(self):
        """Mock de resposta do Cost Explorer"""
        return {
            'ResultsByTime': [
                {
                    'Groups': [
                        {
                            'Keys': ['Amazon Elastic Compute Cloud - Compute'],
                            'Metrics': {
                                'UnblendedCost': {
                                    'Amount': '123.45',
                                    'Unit': 'USD'
                                }
                            }
                        },
                        {
                            'Keys': ['Amazon Simple Storage Service'],
                            'Metrics': {
                                'UnblendedCost': {
                                    'Amount': '12.34',
                                    'Unit': 'USD'
                                }
                            }
                        }
                    ]
                },
                {
                    'Groups': [
                        {
                            'Keys': ['Amazon Elastic Compute Cloud - Compute'],
                            'Metrics': {
                                'UnblendedCost': {
                                    'Amount': '100.00',
                                    'Unit': 'USD'
                                }
                            }
                        }
                    ]
                }
            ]
        }
    
    def test_process_cost_response(self, cost_service, mock_cost_response):
        """Testa processamento de resposta do Cost Explorer"""
        result = cost_service._process_cost_response(mock_cost_response)
        
        expected = {
            'Amazon Elastic Compute Cloud - Compute': 223.45,
            'Amazon Simple Storage Service': 12.34
        }
        
        assert result == expected
    
    def test_process_cost_response_empty(self, cost_service):
        """Testa processamento com resposta vazia"""
        empty_response = {'ResultsByTime': []}
        result = cost_service._process_cost_response(empty_response)
        
        assert result == {}
    
    def test_get_costs_by_service(self, cost_service, mock_cost_response):
        """Testa obtenção de custos por serviço"""
        cost_service.client.get_cost_and_usage = Mock(return_value=mock_cost_response)
        
        result = cost_service.get_costs_by_service(7)
        
        expected = {
            'Amazon Elastic Compute Cloud - Compute': 223.45,
            'Amazon Simple Storage Service': 12.34
        }
        
        assert result == expected
        
        # Verifica se a chamada foi feita com parâmetros corretos
        call_args = cost_service.client.get_cost_and_usage.call_args[1]
        assert call_args['Granularity'] == 'DAILY'
        assert call_args['Metrics'] == ['UnblendedCost']
        assert len(call_args['GroupBy']) == 1
        assert call_args['GroupBy'][0]['Key'] == 'SERVICE'
    
    def test_get_all_period_costs(self, cost_service, mock_cost_response):
        """Testa obtenção de custos para todos os períodos"""
        cost_service.client.get_cost_and_usage = Mock(return_value=mock_cost_response)
        
        result = cost_service.get_all_period_costs()
        
        assert 'last_7_days' in result
        assert 'last_15_days' in result
        assert 'last_30_days' in result
        
        # Verifica se todas as chamadas foram feitas
        assert cost_service.client.get_cost_and_usage.call_count == 3
    
    def test_get_top_services_by_cost(self, cost_service):
        """Testa obtenção dos serviços com maior custo"""
        costs = {
            'Service A': 100.0,
            'Service B': 50.0,
            'Service C': 200.0,
            'Service D': 25.0
        }
        
        result = cost_service.get_top_services_by_cost(costs, limit=2)
        
        assert len(result) == 2
        assert result[0]['service'] == 'Service C'
        assert result[0]['cost'] == 200.0
        assert result[1]['service'] == 'Service A'
        assert result[1]['cost'] == 100.0
        
        # Verifica percentuais
        total_cost = sum(costs.values())
        assert result[0]['percentage'] == (200.0 / total_cost) * 100
    
    def test_get_top_services_empty_costs(self, cost_service):
        """Testa obtenção de top serviços com custos vazios"""
        result = cost_service.get_top_services_by_cost({}, limit=5)
        
        assert result == []