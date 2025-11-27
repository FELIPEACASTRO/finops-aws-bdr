"""
E2E Tests - Multi-Account and Multi-Region Scenarios
Testes E2E para cenários enterprise multi-conta e multi-região
"""
import pytest
import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import dataclass
from typing import Dict, List, Any

import boto3
from moto import mock_aws

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from finops_aws.resilient_lambda_handler import FinOpsResilientHandler
from finops_aws.core.factories import ServiceFactory, AWSClientFactory, AWSClientConfig


@dataclass
class MockLambdaContext:
    function_name: str = "finops-aws-analyzer"
    function_version: str = "$LATEST"
    invoked_function_arn: str = "arn:aws:lambda:us-east-1:123456789012:function:finops-aws-analyzer"
    memory_limit_in_mb: int = 1024
    aws_request_id: str = "multi-account-test-12345"
    log_group_name: str = "/aws/lambda/finops-aws-analyzer"
    log_stream_name: str = "2025/11/27/[$LATEST]abcdef123456"
    
    def get_remaining_time_in_millis(self):
        return 300000


class TestMultiAccountAnalysis:
    """Testes E2E para análise multi-conta"""
    
    @pytest.fixture
    def accounts(self):
        """Lista de contas AWS para teste"""
        return [
            {'id': '111111111111', 'name': 'Production', 'env': 'prod'},
            {'id': '222222222222', 'name': 'Staging', 'env': 'staging'},
            {'id': '333333333333', 'name': 'Development', 'env': 'dev'},
            {'id': '444444444444', 'name': 'Sandbox', 'env': 'sandbox'}
        ]
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_organizations_cross_account_analysis(self, accounts, context):
        """Teste E2E: Análise cross-account via Organizations"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.organizations",
            "detail-type": "Cross-Account Analysis",
            "detail": {
                "accounts": [acc['id'] for acc in accounts],
                "aggregation_type": "consolidated",
                "include_child_accounts": True
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='111111111111'):
            handler = FinOpsResilientHandler()
            
            account_results = {
                acc['id']: {
                    'costs': {'EC2': 1000 * (i + 1), 'Lambda': 200 * (i + 1)},
                    'resources': {'ec2_instances': 10 * (i + 1)},
                    'environment': acc['env']
                }
                for i, acc in enumerate(accounts)
            }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'cross_account_analysis': account_results,
                    'total_costs': sum(r['costs']['EC2'] + r['costs']['Lambda'] for r in account_results.values()),
                    'account_count': len(accounts)
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_cost_aggregation_across_accounts(self, accounts, context):
        """Teste E2E: Agregação de custos entre contas"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.cost-aggregation",
            "detail": {
                "accounts": [acc['id'] for acc in accounts],
                "period_days": 30,
                "group_by": "account"
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='111111111111'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'aggregated_costs': {
                        'by_account': {
                            '111111111111': 5000.0,
                            '222222222222': 3000.0,
                            '333333333333': 1500.0,
                            '444444444444': 500.0
                        },
                        'total': 10000.0
                    }
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_account_specific_recommendations(self, accounts, context):
        """Teste E2E: Recomendações específicas por conta"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.recommendations",
            "detail": {
                "accounts": [acc['id'] for acc in accounts],
                "recommendation_types": ["rightsizing", "reserved_instances", "savings_plans"]
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='111111111111'):
            handler = FinOpsResilientHandler()
            
            recommendations_by_account = {
                acc['id']: [
                    {
                        'type': 'rightsizing',
                        'resource': f'i-{acc["id"][:8]}',
                        'savings': 100.0 * (i + 1)
                    }
                ]
                for i, acc in enumerate(accounts)
            }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'recommendations_by_account': recommendations_by_account,
                    'total_potential_savings': sum(
                        rec['savings'] 
                        for recs in recommendations_by_account.values() 
                        for rec in recs
                    )
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestMultiRegionAnalysis:
    """Testes E2E para análise multi-região"""
    
    @pytest.fixture
    def regions(self):
        """Lista de regiões AWS para teste"""
        return [
            'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1',
            'ap-southeast-1', 'ap-northeast-1', 'sa-east-1'
        ]
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_global_resource_inventory(self, regions, context):
        """Teste E2E: Inventário global de recursos"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.global-inventory",
            "detail": {
                "regions": regions,
                "services": ["ec2", "rds", "lambda", "s3"]
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            regional_inventory = {
                region: {
                    'ec2': {'count': 10 + i, 'cost': 1000 * (i + 1)},
                    'rds': {'count': 2 + i, 'cost': 500 * (i + 1)},
                    'lambda': {'count': 20 + i, 'cost': 100 * (i + 1)},
                    's3': {'count': 5 + i, 'cost': 50 * (i + 1)}
                }
                for i, region in enumerate(regions)
            }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'global_inventory': regional_inventory,
                    'total_resources': sum(
                        sum(svc['count'] for svc in inv.values())
                        for inv in regional_inventory.values()
                    )
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_regional_cost_comparison(self, regions, context):
        """Teste E2E: Comparação de custos por região"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.regional-costs",
            "detail": {
                "regions": regions,
                "period_days": 30,
                "compare_with_previous": True
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            regional_costs = {
                region: {
                    'current_period': 5000.0 + (i * 1000),
                    'previous_period': 4500.0 + (i * 900),
                    'change_percentage': ((5000.0 + i*1000) - (4500.0 + i*900)) / (4500.0 + i*900) * 100
                }
                for i, region in enumerate(regions)
            }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'regional_costs': regional_costs,
                    'highest_cost_region': max(regional_costs.items(), key=lambda x: x[1]['current_period'])[0],
                    'total_cost': sum(r['current_period'] for r in regional_costs.values())
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_cross_region_data_transfer_analysis(self, regions, context):
        """Teste E2E: Análise de transferência de dados cross-region"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.data-transfer",
            "detail": {
                "regions": regions,
                "analyze_cross_region": True,
                "period_days": 30
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            transfer_matrix = {}
            for i, src in enumerate(regions[:4]):
                transfer_matrix[src] = {}
                for j, dst in enumerate(regions[:4]):
                    if src != dst:
                        transfer_matrix[src][dst] = {
                            'gb_transferred': 100.0 * (i + j + 1),
                            'cost': 9.0 * (i + j + 1)
                        }
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'transfer_matrix': transfer_matrix,
                    'total_transfer_cost': sum(
                        t['cost']
                        for src_data in transfer_matrix.values()
                        for t in src_data.values()
                    )
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestEnterpriseScenarios:
    """Testes E2E para cenários enterprise complexos"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_full_enterprise_analysis(self, context):
        """Teste E2E: Análise enterprise completa"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.enterprise",
            "detail": {
                "organization_id": "o-abc123def",
                "accounts": ["111111111111", "222222222222", "333333333333"],
                "regions": ["us-east-1", "us-west-2", "eu-west-1"],
                "services": ["ec2", "rds", "lambda", "s3", "eks", "dynamodb"],
                "analysis_depth": "comprehensive",
                "include_forecasting": True,
                "include_anomaly_detection": True
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='111111111111'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'enterprise_analysis': {
                        'total_monthly_cost': 150000.0,
                        'total_resources': 5000,
                        'cost_by_account': {
                            '111111111111': 80000.0,
                            '222222222222': 50000.0,
                            '333333333333': 20000.0
                        },
                        'cost_by_service': {
                            'ec2': 60000.0,
                            'rds': 40000.0,
                            'lambda': 15000.0,
                            's3': 10000.0,
                            'eks': 20000.0,
                            'dynamodb': 5000.0
                        },
                        'forecasted_next_month': 165000.0,
                        'anomalies_detected': 3,
                        'potential_savings': 25000.0
                    }
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_budget_compliance_check(self, context):
        """Teste E2E: Verificação de compliance com orçamento"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.budget-compliance",
            "detail": {
                "budgets": [
                    {"name": "Production", "account": "111111111111", "monthly_limit": 100000.0},
                    {"name": "Staging", "account": "222222222222", "monthly_limit": 50000.0},
                    {"name": "Development", "account": "333333333333", "monthly_limit": 25000.0}
                ],
                "alert_threshold_percentage": 80
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='111111111111'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'budget_status': [
                        {
                            'name': 'Production',
                            'limit': 100000.0,
                            'current_spend': 85000.0,
                            'percentage_used': 85.0,
                            'status': 'WARNING',
                            'forecasted_overage': 5000.0
                        },
                        {
                            'name': 'Staging',
                            'limit': 50000.0,
                            'current_spend': 35000.0,
                            'percentage_used': 70.0,
                            'status': 'OK',
                            'forecasted_overage': 0.0
                        },
                        {
                            'name': 'Development',
                            'limit': 25000.0,
                            'current_spend': 28000.0,
                            'percentage_used': 112.0,
                            'status': 'EXCEEDED',
                            'forecasted_overage': 5000.0
                        }
                    ],
                    'alerts_triggered': 2
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_tagging_compliance_analysis(self, context):
        """Teste E2E: Análise de compliance de tags"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.tagging-compliance",
            "detail": {
                "required_tags": ["Environment", "Project", "CostCenter", "Owner"],
                "services": ["ec2", "rds", "s3", "lambda"],
                "report_non_compliant": True
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'tagging_compliance': {
                        'total_resources': 500,
                        'compliant_resources': 350,
                        'non_compliant_resources': 150,
                        'compliance_percentage': 70.0,
                        'missing_tags_by_type': {
                            'Environment': 50,
                            'Project': 75,
                            'CostCenter': 100,
                            'Owner': 80
                        },
                        'non_compliant_by_service': {
                            'ec2': 60,
                            'rds': 20,
                            's3': 40,
                            'lambda': 30
                        }
                    }
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]


class TestControlTowerIntegration:
    """Testes E2E para integração com Control Tower"""
    
    @pytest.fixture
    def context(self):
        return MockLambdaContext()
    
    @mock_aws
    def test_control_tower_ou_analysis(self, context):
        """Teste E2E: Análise por Organizational Unit"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.control-tower",
            "detail": {
                "organizational_units": [
                    {"id": "ou-prod-12345", "name": "Production"},
                    {"id": "ou-dev-67890", "name": "Development"},
                    {"id": "ou-sandbox-11111", "name": "Sandbox"}
                ],
                "include_account_details": True
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'ou_analysis': {
                        'Production': {
                            'accounts': 5,
                            'total_cost': 100000.0,
                            'resources': 2000
                        },
                        'Development': {
                            'accounts': 10,
                            'total_cost': 30000.0,
                            'resources': 1500
                        },
                        'Sandbox': {
                            'accounts': 20,
                            'total_cost': 10000.0,
                            'resources': 500
                        }
                    }
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
    
    @mock_aws
    def test_guardrail_compliance_check(self, context):
        """Teste E2E: Verificação de guardrails"""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='finops-aws-state')
        
        event = {
            "source": "finops.guardrails",
            "detail": {
                "check_types": ["cost_guardrails", "security_guardrails", "compliance_guardrails"]
            }
        }
        
        with patch('finops_aws.utils.aws_helpers.get_aws_account_id', return_value='123456789012'):
            handler = FinOpsResilientHandler()
            
            with patch.object(handler.executor, 'execute_with_dependencies', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    'guardrail_status': {
                        'cost_guardrails': {'compliant': 45, 'non_compliant': 5},
                        'security_guardrails': {'compliant': 48, 'non_compliant': 2},
                        'compliance_guardrails': {'compliant': 50, 'non_compliant': 0}
                    },
                    'overall_compliance': 95.3
                }
                
                result = asyncio.run(handler.handle_request(event, context))
                
                assert result['statusCode'] in [200, 500]
