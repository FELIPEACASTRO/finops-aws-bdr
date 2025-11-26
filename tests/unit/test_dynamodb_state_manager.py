"""
Testes unitários para DynamoDBStateManager

FASE 1.2 do Roadmap FinOps AWS
Cobertura: Sistema de controle de execução com DynamoDB
"""
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest
import boto3
from moto import mock_aws
from decimal import Decimal

from src.finops_aws.core.dynamodb_state_manager import (
    DynamoDBStateManager,
    ExecutionRecord,
    ExecutionStatus,
    CheckpointData,
    TaskStatus,
    ServiceCategory,
    BatchConfig
)


class TestCheckpointData:
    """Testes para CheckpointData"""

    def test_create_checkpoint(self):
        """Testa criação de checkpoint"""
        checkpoint = CheckpointData(
            service_name='ec2',
            category=ServiceCategory.COMPUTE,
            status=TaskStatus.PENDING
        )
        
        assert checkpoint.service_name == 'ec2'
        assert checkpoint.category == ServiceCategory.COMPUTE
        assert checkpoint.status == TaskStatus.PENDING
        assert checkpoint.items_processed == 0

    def test_checkpoint_to_dict(self):
        """Testa conversão para dicionário"""
        now = datetime.now()
        checkpoint = CheckpointData(
            service_name='lambda',
            category=ServiceCategory.COMPUTE,
            status=TaskStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            items_processed=100,
            items_total=100,
            progress_percentage=100.0
        )
        
        result = checkpoint.to_dict()
        
        assert result['service_name'] == 'lambda'
        assert result['category'] == 'compute'
        assert result['status'] == 'completed'
        assert result['items_processed'] == 100
        assert result['progress_percentage'] == 100.0

    def test_checkpoint_from_dict(self):
        """Testa criação a partir de dicionário"""
        data = {
            'service_name': 's3',
            'category': 'storage',
            'status': 'running',
            'started_at': '2025-11-26T10:00:00',
            'completed_at': None,
            'items_processed': 50,
            'items_total': 100,
            'progress_percentage': 50.0,
            'last_processed_id': 'bucket-50',
            'result_summary': None,
            'error_message': None,
            'retry_count': 0
        }
        
        checkpoint = CheckpointData.from_dict(data)
        
        assert checkpoint.service_name == 's3'
        assert checkpoint.category == ServiceCategory.STORAGE
        assert checkpoint.status == TaskStatus.RUNNING
        assert checkpoint.items_processed == 50


class TestExecutionRecord:
    """Testes para ExecutionRecord"""

    def test_create_execution_record(self):
        """Testa criação de registro de execução"""
        now = datetime.now()
        record = ExecutionRecord(
            execution_id='exec_123',
            account_id='123456789012',
            region='us-east-1',
            status=ExecutionStatus.RUNNING,
            started_at=now,
            last_updated=now,
            total_services=5
        )
        
        assert record.execution_id == 'exec_123'
        assert record.account_id == '123456789012'
        assert record.status == ExecutionStatus.RUNNING
        assert record.total_services == 5

    def test_execution_record_to_dynamodb_item(self):
        """Testa conversão para item DynamoDB"""
        now = datetime.now()
        record = ExecutionRecord(
            execution_id='exec_456',
            account_id='123456789012',
            region='us-east-1',
            status=ExecutionStatus.RUNNING,
            started_at=now,
            last_updated=now,
            total_services=3,
            checkpoints={
                'ec2': CheckpointData(
                    service_name='ec2',
                    category=ServiceCategory.COMPUTE,
                    status=TaskStatus.PENDING
                )
            }
        )
        
        item = record.to_dynamodb_item()
        
        assert item['PK'] == 'EXEC#exec_456'
        assert item['SK'] == 'ACCOUNT#123456789012'
        assert item['execution_id'] == 'exec_456'
        assert item['status'] == 'running'
        assert item['GSI1PK'] == 'ACCOUNT#123456789012'

    def test_execution_record_from_dynamodb_item(self):
        """Testa criação a partir de item DynamoDB"""
        now = datetime.now()
        checkpoints = {
            'ec2': {
                'service_name': 'ec2',
                'category': 'compute',
                'status': 'pending',
                'started_at': None,
                'completed_at': None,
                'last_checkpoint_at': None,
                'items_processed': 0,
                'items_total': 0,
                'progress_percentage': 0.0,
                'last_processed_id': None,
                'result_summary': None,
                'error_message': None,
                'retry_count': 0
            }
        }
        
        item = {
            'PK': 'EXEC#exec_789',
            'SK': 'ACCOUNT#123456789012',
            'execution_id': 'exec_789',
            'account_id': '123456789012',
            'region': 'us-east-1',
            'status': 'running',
            'started_at': now.isoformat(),
            'last_updated': now.isoformat(),
            'total_services': 1,
            'completed_services': 0,
            'failed_services': 0,
            'total_items_processed': 0,
            'estimated_cost_analyzed': Decimal('0'),
            'metadata': '{}',
            'checkpoints': json.dumps(checkpoints)
        }
        
        record = ExecutionRecord.from_dynamodb_item(item)
        
        assert record.execution_id == 'exec_789'
        assert record.account_id == '123456789012'
        assert record.status == ExecutionStatus.RUNNING
        assert 'ec2' in record.checkpoints


class TestBatchConfig:
    """Testes para BatchConfig"""

    def test_default_batch_config(self):
        """Testa configuração padrão de batch"""
        config = BatchConfig()
        
        assert config.batch_size == 100
        assert config.max_concurrent_batches == 5
        assert config.checkpoint_interval == 50
        assert config.retry_failed_items is True

    def test_custom_batch_config(self):
        """Testa configuração personalizada de batch"""
        config = BatchConfig(
            batch_size=50,
            max_concurrent_batches=10,
            checkpoint_interval=25
        )
        
        assert config.batch_size == 50
        assert config.max_concurrent_batches == 10


@mock_aws
class TestDynamoDBStateManager:
    """Testes para DynamoDBStateManager"""

    def setup_method(self, method):
        """Setup para cada teste"""
        self.table_name = 'test-finops-executions'
        self.region = 'us-east-1'
        
        self.dynamodb = boto3.client('dynamodb', region_name=self.region)
        
        self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        self.manager = DynamoDBStateManager(
            table_name=self.table_name,
            region=self.region
        )

    def test_manager_initialization(self):
        """Testa inicialização do manager"""
        assert self.manager.table_name == self.table_name
        assert self.manager.region == self.region
        assert self.manager.current_execution is None

    def test_create_execution(self):
        """Testa criação de execução"""
        account_id = '123456789012'
        
        execution = self.manager.create_execution(account_id)
        
        assert execution is not None
        assert execution.account_id == account_id
        assert execution.status == ExecutionStatus.RUNNING
        assert self.manager.current_execution == execution

    def test_create_execution_with_services(self):
        """Testa criação de execução com serviços específicos"""
        account_id = '123456789012'
        services = ['ec2', 'lambda', 's3']
        
        execution = self.manager.create_execution(account_id, services=services)
        
        assert len(execution.checkpoints) == 3
        assert 'ec2' in execution.checkpoints
        assert 'lambda' in execution.checkpoints
        assert 's3' in execution.checkpoints

    def test_update_checkpoint(self):
        """Testa atualização de checkpoint"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2'])
        
        result = self.manager.update_checkpoint(
            'ec2',
            status=TaskStatus.RUNNING,
            items_total=100
        )
        
        assert result is True
        checkpoint = self.manager.current_execution.checkpoints['ec2']
        assert checkpoint.status == TaskStatus.RUNNING
        assert checkpoint.items_total == 100

    def test_start_service(self):
        """Testa início de processamento de serviço"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['lambda'])
        
        result = self.manager.start_service('lambda', items_total=50)
        
        assert result is True
        checkpoint = self.manager.current_execution.checkpoints['lambda']
        assert checkpoint.status == TaskStatus.RUNNING
        assert checkpoint.items_total == 50
        assert checkpoint.started_at is not None

    def test_complete_service(self):
        """Testa conclusão de serviço"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['s3'])
        self.manager.start_service('s3', items_total=100)
        
        result = self.manager.complete_service('s3', result_summary={'buckets': 10})
        
        assert result is True
        checkpoint = self.manager.current_execution.checkpoints['s3']
        assert checkpoint.status == TaskStatus.COMPLETED
        assert checkpoint.completed_at is not None

    def test_fail_service(self):
        """Testa falha de serviço"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['rds'])
        self.manager.start_service('rds')
        
        result = self.manager.fail_service('rds', 'Connection timeout')
        
        assert result is True
        checkpoint = self.manager.current_execution.checkpoints['rds']
        assert checkpoint.status == TaskStatus.FAILED
        assert checkpoint.error_message == 'Connection timeout'
        assert checkpoint.retry_count == 1

    def test_skip_service(self):
        """Testa pular serviço"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ecs'])
        
        result = self.manager.skip_service('ecs', 'No resources found')
        
        assert result is True
        checkpoint = self.manager.current_execution.checkpoints['ecs']
        assert checkpoint.status == TaskStatus.SKIPPED

    def test_get_pending_services(self):
        """Testa obtenção de serviços pendentes"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2', 'lambda', 's3'])
        self.manager.complete_service('ec2')
        
        pending = self.manager.get_pending_services()
        
        assert len(pending) == 2
        assert 'lambda' in pending
        assert 's3' in pending
        assert 'ec2' not in pending

    def test_get_failed_services(self):
        """Testa obtenção de serviços falhos"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2', 'lambda'])
        self.manager.fail_service('lambda', 'API Error')
        
        failed = self.manager.get_failed_services()
        
        assert len(failed) == 1
        assert 'lambda' in failed

    def test_complete_execution(self):
        """Testa conclusão de execução"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2'])
        self.manager.complete_service('ec2')
        
        result = self.manager.complete_execution()
        
        assert result is True
        assert self.manager.current_execution.status == ExecutionStatus.COMPLETED
        assert self.manager.current_execution.completed_at is not None

    def test_complete_execution_with_failures(self):
        """Testa conclusão de execução com falhas"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2', 'lambda'])
        self.manager.complete_service('ec2')
        self.manager.fail_service('lambda', 'Error')
        
        result = self.manager.complete_execution()
        
        assert result is True
        assert self.manager.current_execution.status == ExecutionStatus.PARTIALLY_COMPLETED

    def test_get_execution_progress(self):
        """Testa obtenção de progresso"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2', 'lambda', 's3'])
        self.manager.complete_service('ec2')
        self.manager.start_service('lambda')
        
        progress = self.manager.get_execution_progress()
        
        assert progress['total_services'] == 3
        assert progress['completed_services'] == 1
        assert 'ec2' in progress['services_by_status']['completed']
        assert 'lambda' in progress['services_by_status']['running']
        assert 's3' in progress['services_by_status']['pending']

    def test_get_service_checkpoint(self):
        """Testa obtenção de checkpoint de serviço"""
        account_id = '123456789012'
        self.manager.create_execution(account_id, services=['ec2'])
        self.manager.update_checkpoint('ec2', items_processed=50, items_total=100)
        
        checkpoint = self.manager.get_service_checkpoint('ec2')
        
        assert checkpoint is not None
        assert checkpoint.items_processed == 50
        assert checkpoint.items_total == 100

    def test_get_execution(self):
        """Testa obtenção de execução específica"""
        account_id = '123456789012'
        execution = self.manager.create_execution(account_id)
        
        retrieved = self.manager.get_execution(execution.execution_id, account_id)
        
        assert retrieved is not None
        assert retrieved.execution_id == execution.execution_id

    def test_get_running_execution(self):
        """Testa obtenção de execução em andamento"""
        account_id = '123456789012'
        self.manager.create_execution(account_id)
        
        running = self.manager.get_running_execution(account_id)
        
        assert running is not None
        assert running.status == ExecutionStatus.RUNNING

    def test_no_current_execution_errors(self):
        """Testa erros quando não há execução atual"""
        result = self.manager.update_checkpoint('ec2', status=TaskStatus.RUNNING)
        assert result is False
        
        result = self.manager.complete_execution()
        assert result is False
        
        pending = self.manager.get_pending_services()
        assert pending == []

    def test_service_category_detection(self):
        """Testa detecção de categoria de serviço"""
        account_id = '123456789012'
        self.manager.create_execution(
            account_id, 
            services=['ec2', 's3', 'rds', 'vpc', 'sagemaker']
        )
        
        checkpoints = self.manager.current_execution.checkpoints
        
        assert checkpoints['ec2'].category == ServiceCategory.COMPUTE
        assert checkpoints['s3'].category == ServiceCategory.STORAGE
        assert checkpoints['rds'].category == ServiceCategory.DATABASE
        assert checkpoints['vpc'].category == ServiceCategory.NETWORKING
        assert checkpoints['sagemaker'].category == ServiceCategory.MACHINE_LEARNING


class TestDynamoDBStateManagerResume:
    """Testes para retomada de execução"""

    @mock_aws
    def test_resume_recent_execution(self):
        """Testa retomada de execução recente"""
        table_name = 'test-finops-resume'
        region = 'us-east-1'
        
        dynamodb = boto3.client('dynamodb', region_name=region)
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        manager = DynamoDBStateManager(table_name=table_name, region=region)
        
        account_id = '123456789012'
        first_execution = manager.create_execution(account_id, services=['ec2'])
        first_id = first_execution.execution_id
        manager.complete_service('ec2')
        
        manager.current_execution = None
        
        second_execution = manager.create_execution(account_id)
        
        assert second_execution.execution_id == first_id


class TestDynamoDBStateManagerEdgeCases:
    """Testes para casos extremos"""

    def test_update_nonexistent_service(self):
        """Testa atualização de serviço inexistente"""
        with patch.object(DynamoDBStateManager, '__init__', lambda x, **kwargs: None):
            manager = DynamoDBStateManager()
            manager.table_name = 'test'
            manager.region = 'us-east-1'
            manager.ttl_days = 30
            manager._dynamodb_client = None
            manager._dynamodb_resource = None
            manager._table = None
            manager.current_execution = ExecutionRecord(
                execution_id='test',
                account_id='123',
                region='us-east-1',
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
                last_updated=datetime.now(),
                checkpoints={}
            )
            
            result = manager.update_checkpoint('nonexistent', status=TaskStatus.RUNNING)
            
            assert result is False

    def test_progress_with_empty_checkpoints(self):
        """Testa progresso com checkpoints vazios"""
        with patch.object(DynamoDBStateManager, '__init__', lambda x, **kwargs: None):
            manager = DynamoDBStateManager()
            manager.table_name = 'test'
            manager.region = 'us-east-1'
            manager.ttl_days = 30
            manager._dynamodb_client = None
            manager._dynamodb_resource = None
            manager._table = None
            manager.current_execution = ExecutionRecord(
                execution_id='test',
                account_id='123',
                region='us-east-1',
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
                last_updated=datetime.now(),
                checkpoints={},
                total_services=0
            )
            
            progress = manager.get_execution_progress()
            
            assert progress['total_services'] == 0
            assert progress['progress_percentage'] == 0
