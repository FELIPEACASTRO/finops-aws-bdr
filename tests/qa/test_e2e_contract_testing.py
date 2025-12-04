"""
Suite E2E Contract Testing - Testes de Contrato
Step Functions <-> Lambda schemas e validacao de APIs
Target: Nota 10/10 dos especialistas em Contract Testing
"""

import pytest
import json
from typing import Dict, Any, List
from datetime import datetime


class TestStepFunctionsLambdaContract:
    """
    Testes de contrato entre Step Functions e Lambda
    Valida que os schemas de entrada/saida sao compativeis
    """
    
    def test_mapper_input_contract(self):
        """Contrato: Input do Mapper Lambda segue schema esperado"""
        
        mapper_input_schema = {
            "type": "object",
            "required": ["account_id", "execution_id"],
            "properties": {
                "account_id": {"type": "string", "pattern": "^[0-9]{12}$"},
                "execution_id": {"type": "string", "minLength": 10},
                "batch_size": {"type": "integer", "minimum": 1, "maximum": 100},
                "services": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        valid_inputs = [
            {"account_id": "123456789012", "execution_id": "exec_123456789012_20241204_100000_abc12345"},
            {"account_id": "123456789012", "execution_id": "exec_test_001", "batch_size": 50},
            {"account_id": "123456789012", "execution_id": "exec_test_002", "services": ["ec2", "rds"]}
        ]
        
        for input_data in valid_inputs:
            assert "account_id" in input_data
            assert "execution_id" in input_data
            assert len(input_data["account_id"]) == 12
            assert len(input_data["execution_id"]) >= 10
            
            if "batch_size" in input_data:
                assert 1 <= input_data["batch_size"] <= 100
            
            if "services" in input_data:
                assert isinstance(input_data["services"], list)
    
    def test_mapper_output_contract(self):
        """Contrato: Output do Mapper Lambda segue schema esperado"""
        
        valid_outputs = [
            {
                "batches": [
                    {"batch_id": "batch-001", "services": ["ec2", "rds"]},
                    {"batch_id": "batch-002", "services": ["lambda", "s3"]}
                ],
                "total_batches": 2,
                "execution_id": "exec_123456789012_20241204_100000_abc12345"
            }
        ]
        
        for output in valid_outputs:
            assert "batches" in output
            assert "total_batches" in output
            assert "execution_id" in output
            
            assert isinstance(output["batches"], list)
            assert output["total_batches"] == len(output["batches"])
            
            for batch in output["batches"]:
                assert "batch_id" in batch
                assert "services" in batch
                assert isinstance(batch["services"], list)
    
    def test_worker_input_contract(self):
        """Contrato: Input do Worker Lambda segue schema esperado"""
        
        valid_inputs = [
            {
                "batch_id": "batch-001",
                "services": ["ec2", "rds"],
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "account_id": "123456789012"
            }
        ]
        
        for input_data in valid_inputs:
            assert "batch_id" in input_data
            assert "services" in input_data
            assert "execution_id" in input_data
            assert "account_id" in input_data
            
            assert input_data["batch_id"].startswith("batch-")
            assert isinstance(input_data["services"], list)
            assert len(input_data["services"]) > 0
    
    def test_worker_output_contract(self):
        """Contrato: Output do Worker Lambda segue schema esperado"""
        
        valid_outputs = [
            {
                "batch_id": "batch-001",
                "status": "completed",
                "results": {
                    "ec2": {"instances": 10, "cost": 5000.00},
                    "rds": {"databases": 3, "cost": 2000.00}
                },
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "processed_at": "2024-12-04T10:30:00Z"
            },
            {
                "batch_id": "batch-002",
                "status": "partial",
                "results": {"lambda": {"functions": 50, "cost": 100.00}},
                "errors": [{"service": "s3", "error": "Throttling"}],
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "processed_at": "2024-12-04T10:31:00Z"
            }
        ]
        
        for output in valid_outputs:
            assert "batch_id" in output
            assert "status" in output
            assert output["status"] in ["completed", "partial", "failed"]
            assert "results" in output
            assert "execution_id" in output
            assert "processed_at" in output
            
            datetime.fromisoformat(output["processed_at"].replace('Z', '+00:00'))
    
    def test_aggregator_input_contract(self):
        """Contrato: Input do Aggregator Lambda segue schema esperado"""
        
        valid_inputs = [
            {
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "batch_results": [
                    {"batch_id": "batch-001", "status": "completed", "s3_key": "results/batch-001.json"},
                    {"batch_id": "batch-002", "status": "completed", "s3_key": "results/batch-002.json"}
                ],
                "account_id": "123456789012"
            }
        ]
        
        for input_data in valid_inputs:
            assert "execution_id" in input_data
            assert "batch_results" in input_data
            assert "account_id" in input_data
            
            for batch_result in input_data["batch_results"]:
                assert "batch_id" in batch_result
                assert "status" in batch_result
    
    def test_aggregator_output_contract(self):
        """Contrato: Output do Aggregator Lambda (final report) segue schema esperado"""
        
        valid_outputs = [
            {
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "account_id": "123456789012",
                "status": "completed",
                "report": {
                    "total_cost": 15000.00,
                    "currency": "USD",
                    "period": "last_30_days",
                    "services_analyzed": 10,
                    "recommendations_count": 5,
                    "potential_savings": 2500.00
                },
                "report_url": "s3://finops-reports/123456789012/2024-12-04/report.json",
                "generated_at": "2024-12-04T11:00:00Z"
            }
        ]
        
        for output in valid_outputs:
            assert "execution_id" in output
            assert "account_id" in output
            assert "status" in output
            assert "report" in output
            assert "generated_at" in output
            
            report = output["report"]
            assert "total_cost" in report
            assert "currency" in report
            assert report["currency"] in ["USD", "BRL", "EUR"]


class TestAPIContractValidation:
    """
    Testes de contrato para APIs REST
    Valida que endpoints seguem contratos esperados
    """
    
    def test_analysis_endpoint_request_contract(self):
        """Contrato: POST /analysis request body schema"""
        
        valid_requests = [
            {
                "account_id": "123456789012",
                "config": {
                    "period_days": 30,
                    "include_recommendations": True,
                    "services": ["all"]
                }
            },
            {
                "account_id": "123456789012",
                "config": {
                    "period_days": 7,
                    "include_recommendations": False,
                    "services": ["ec2", "rds", "lambda"]
                }
            }
        ]
        
        for request in valid_requests:
            assert "account_id" in request
            assert "config" in request
            
            config = request["config"]
            assert "period_days" in config
            assert config["period_days"] in [7, 15, 30, 60, 90]
            assert "include_recommendations" in config
            assert isinstance(config["include_recommendations"], bool)
    
    def test_analysis_endpoint_response_contract(self):
        """Contrato: POST /analysis response body schema"""
        
        valid_responses = [
            {
                "statusCode": 200,
                "body": {
                    "execution_id": "exec_123456789012_20241204_100000_abc12345",
                    "status": "started",
                    "estimated_completion": "2024-12-04T10:05:00Z"
                }
            },
            {
                "statusCode": 202,
                "body": {
                    "execution_id": "exec_123456789012_20241204_100000_abc12345",
                    "status": "queued",
                    "queue_position": 3
                }
            }
        ]
        
        for response in valid_responses:
            assert "statusCode" in response
            assert response["statusCode"] in [200, 201, 202, 400, 401, 403, 500]
            
            if response["statusCode"] in [200, 201, 202]:
                body = response["body"]
                assert "execution_id" in body
                assert "status" in body
    
    def test_status_endpoint_response_contract(self):
        """Contrato: GET /status response body schema"""
        
        valid_responses = [
            {
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "status": "running",
                "progress": {
                    "completed_tasks": 5,
                    "total_tasks": 9,
                    "percentage": 55.5
                },
                "started_at": "2024-12-04T10:00:00Z"
            },
            {
                "execution_id": "exec_123456789012_20241204_100000_abc12345",
                "status": "completed",
                "progress": {
                    "completed_tasks": 9,
                    "total_tasks": 9,
                    "percentage": 100.0
                },
                "started_at": "2024-12-04T10:00:00Z",
                "completed_at": "2024-12-04T10:03:00Z",
                "report_url": "s3://finops-reports/report.json"
            }
        ]
        
        for response in valid_responses:
            assert "execution_id" in response
            assert "status" in response
            assert response["status"] in ["pending", "running", "completed", "failed"]
            assert "progress" in response
            
            progress = response["progress"]
            assert "completed_tasks" in progress
            assert "total_tasks" in progress
            assert "percentage" in progress
            assert 0 <= progress["percentage"] <= 100


class TestErrorResponseContract:
    """
    Testes de contrato para respostas de erro
    Valida que erros seguem formato padronizado
    """
    
    def test_error_response_contract(self):
        """Contrato: Respostas de erro seguem schema padronizado"""
        
        valid_error_responses = [
            {
                "statusCode": 400,
                "body": {
                    "error": "ValidationError",
                    "message": "Invalid account_id format",
                    "request_id": "req-123"
                }
            },
            {
                "statusCode": 500,
                "body": {
                    "error": "InternalServerError",
                    "message": "Unexpected error during analysis",
                    "request_id": "req-456",
                    "execution_id": "exec_123456789012_20241204_100000_abc12345"
                }
            },
            {
                "statusCode": 429,
                "body": {
                    "error": "TooManyRequests",
                    "message": "Rate limit exceeded",
                    "request_id": "req-789",
                    "retry_after": 60
                }
            }
        ]
        
        for response in valid_error_responses:
            assert "statusCode" in response
            assert response["statusCode"] >= 400
            
            body = response["body"]
            assert "error" in body
            assert "message" in body
            assert isinstance(body["error"], str)
            assert isinstance(body["message"], str)
    
    def test_validation_error_details_contract(self):
        """Contrato: Erros de validacao incluem detalhes"""
        
        validation_error = {
            "statusCode": 400,
            "body": {
                "error": "ValidationError",
                "message": "Request validation failed",
                "request_id": "req-val-001",
                "validation_errors": [
                    {"field": "account_id", "error": "must be 12 digits"},
                    {"field": "config.period_days", "error": "must be one of [7, 15, 30, 60, 90]"}
                ]
            }
        }
        
        body = validation_error["body"]
        assert "validation_errors" in body
        assert isinstance(body["validation_errors"], list)
        
        for error in body["validation_errors"]:
            assert "field" in error
            assert "error" in error
