"""
Testes unitários para novos serviços AWS (FASE 2)

Testa BaseAWSService, S3Service, EBSService e DynamoDBFinOpsService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.finops_aws.services.base_service import (
    BaseAWSService,
    ServiceCost,
    ServiceMetrics,
    ServiceRecommendation
)
from src.finops_aws.services.s3_service import S3Service, S3Bucket
from src.finops_aws.services.ebs_service import EBSService, EBSVolume, EBSSnapshot
from src.finops_aws.services.dynamodb_finops_service import DynamoDBFinOpsService, DynamoDBTable


class TestServiceCost:
    """Testes para ServiceCost dataclass"""
    
    def test_create_service_cost(self):
        """Testa criação de ServiceCost"""
        cost = ServiceCost(
            service_name="Test Service",
            total_cost=100.50,
            period_days=30
        )
        
        assert cost.service_name == "Test Service"
        assert cost.total_cost == 100.50
        assert cost.period_days == 30
        assert cost.trend == "STABLE"
        assert cost.currency == "USD"
    
    def test_service_cost_to_dict(self):
        """Testa conversão para dicionário"""
        cost = ServiceCost(
            service_name="S3",
            total_cost=50.0,
            period_days=7
        )
        
        result = cost.to_dict()
        
        assert result['service_name'] == "S3"
        assert result['total_cost'] == 50.0
        assert result['period_days'] == 7


class TestServiceMetrics:
    """Testes para ServiceMetrics dataclass"""
    
    def test_create_service_metrics(self):
        """Testa criação de ServiceMetrics"""
        metrics = ServiceMetrics(
            service_name="EBS",
            resource_count=10,
            metrics={'total_size': 500}
        )
        
        assert metrics.service_name == "EBS"
        assert metrics.resource_count == 10
        assert metrics.metrics['total_size'] == 500
    
    def test_service_metrics_to_dict(self):
        """Testa conversão para dicionário"""
        metrics = ServiceMetrics(
            service_name="DynamoDB",
            resource_count=5
        )
        
        result = metrics.to_dict()
        
        assert result['service_name'] == "DynamoDB"
        assert result['resource_count'] == 5


class TestServiceRecommendation:
    """Testes para ServiceRecommendation dataclass"""
    
    def test_create_recommendation(self):
        """Testa criação de ServiceRecommendation"""
        rec = ServiceRecommendation(
            resource_id="vol-123",
            resource_type="EBSVolume",
            recommendation_type="UPGRADE",
            description="Upgrade to gp3",
            estimated_savings=10.0
        )
        
        assert rec.resource_id == "vol-123"
        assert rec.resource_type == "EBSVolume"
        assert rec.estimated_savings == 10.0
        assert rec.priority == "MEDIUM"
    
    def test_recommendation_to_dict(self):
        """Testa conversão para dicionário"""
        rec = ServiceRecommendation(
            resource_id="bucket-123",
            resource_type="S3Bucket",
            recommendation_type="LIFECYCLE",
            description="Add lifecycle policy"
        )
        
        result = rec.to_dict()
        
        assert result['resource_id'] == "bucket-123"
        assert result['recommendation_type'] == "LIFECYCLE"


class TestS3Service:
    """Testes para S3Service"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_s3 = Mock()
        self.mock_cloudwatch = Mock()
        self.mock_cost = Mock()
        
        self.service = S3Service(
            s3_client=self.mock_s3,
            cloudwatch_client=self.mock_cloudwatch,
            cost_client=self.mock_cost
        )
    
    def test_service_name(self):
        """Testa nome do serviço"""
        assert self.service.get_service_name() == "Amazon S3"
    
    def test_health_check_success(self):
        """Testa health check com sucesso"""
        self.mock_s3.list_buckets.return_value = {'Buckets': []}
        
        result = self.service.health_check()
        
        assert result is True
    
    def test_health_check_failure(self):
        """Testa health check com falha"""
        self.mock_s3.list_buckets.side_effect = Exception("Access denied")
        
        result = self.service.health_check()
        
        assert result is False
    
    def test_get_buckets(self):
        """Testa obtenção de buckets"""
        self.mock_s3.list_buckets.return_value = {
            'Buckets': [
                {'Name': 'bucket-1', 'CreationDate': datetime.now()},
                {'Name': 'bucket-2', 'CreationDate': datetime.now()}
            ]
        }
        self.mock_s3.get_bucket_location.return_value = {'LocationConstraint': 'us-west-2'}
        self.mock_s3.get_bucket_versioning.return_value = {'Status': 'Enabled'}
        self.mock_s3.get_bucket_encryption.return_value = {
            'ServerSideEncryptionConfiguration': {}
        }
        self.mock_s3.get_bucket_lifecycle_configuration.return_value = {'Rules': []}
        self.mock_s3.get_public_access_block.return_value = {
            'PublicAccessBlockConfiguration': {
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        }
        
        buckets = self.service.get_buckets()
        
        assert len(buckets) == 2
        assert buckets[0].name == 'bucket-1'
        assert buckets[0].region == 'us-west-2'
    
    def test_get_resources(self):
        """Testa get_resources retorna lista de dicionários"""
        self.mock_s3.list_buckets.return_value = {
            'Buckets': [{'Name': 'test-bucket', 'CreationDate': datetime.now()}]
        }
        self.mock_s3.get_bucket_location.return_value = {'LocationConstraint': None}
        self.mock_s3.get_bucket_versioning.return_value = {}
        self.mock_s3.get_bucket_encryption.side_effect = Exception()
        self.mock_s3.get_bucket_lifecycle_configuration.side_effect = Exception()
        self.mock_s3.get_public_access_block.side_effect = Exception()
        
        resources = self.service.get_resources()
        
        assert len(resources) == 1
        assert 'name' in resources[0]
    
    def test_get_metrics(self):
        """Testa obtenção de métricas agregadas"""
        self.mock_s3.list_buckets.return_value = {
            'Buckets': [{'Name': 'bucket-1', 'CreationDate': datetime.now()}]
        }
        self.mock_s3.get_bucket_location.return_value = {}
        self.mock_s3.get_bucket_versioning.return_value = {}
        self.mock_s3.get_bucket_encryption.side_effect = Exception()
        self.mock_s3.get_bucket_lifecycle_configuration.side_effect = Exception()
        self.mock_s3.get_public_access_block.side_effect = Exception()
        self.mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
        
        metrics = self.service.get_metrics()
        
        assert metrics.service_name == "Amazon S3"
        assert metrics.resource_count == 1
    
    def test_get_recommendations_no_lifecycle(self):
        """Testa recomendação para bucket sem lifecycle"""
        self.mock_s3.list_buckets.return_value = {
            'Buckets': [{'Name': 'no-lifecycle-bucket', 'CreationDate': datetime.now()}]
        }
        self.mock_s3.get_bucket_location.return_value = {}
        self.mock_s3.get_bucket_versioning.return_value = {}
        self.mock_s3.get_bucket_encryption.side_effect = Exception()
        self.mock_s3.get_bucket_lifecycle_configuration.side_effect = Exception()
        self.mock_s3.get_public_access_block.return_value = {
            'PublicAccessBlockConfiguration': {
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        }
        
        recommendations = self.service.get_recommendations()
        
        lifecycle_recs = [r for r in recommendations if r.recommendation_type == 'LIFECYCLE_POLICY']
        assert len(lifecycle_recs) >= 1


class TestEBSService:
    """Testes para EBSService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_ec2 = Mock()
        self.mock_cloudwatch = Mock()
        self.mock_cost = Mock()
        
        self.service = EBSService(
            ec2_client=self.mock_ec2,
            cloudwatch_client=self.mock_cloudwatch,
            cost_client=self.mock_cost
        )
    
    def test_service_name(self):
        """Testa nome do serviço"""
        assert self.service.get_service_name() == "Amazon EBS"
    
    def test_health_check_success(self):
        """Testa health check com sucesso"""
        self.mock_ec2.describe_volumes.return_value = {'Volumes': []}
        
        result = self.service.health_check()
        
        assert result is True
    
    def test_health_check_failure(self):
        """Testa health check com falha"""
        self.mock_ec2.describe_volumes.side_effect = Exception("Access denied")
        
        result = self.service.health_check()
        
        assert result is False
    
    def test_get_volumes(self):
        """Testa obtenção de volumes"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {
                'Volumes': [
                    {
                        'VolumeId': 'vol-123',
                        'VolumeType': 'gp2',
                        'Size': 100,
                        'State': 'in-use',
                        'AvailabilityZone': 'us-east-1a',
                        'Attachments': [{'InstanceId': 'i-123'}],
                        'Encrypted': True
                    }
                ]
            }
        ]
        self.mock_ec2.get_paginator.return_value = paginator
        
        volumes = self.service.get_volumes()
        
        assert len(volumes) == 1
        assert volumes[0].volume_id == 'vol-123'
        assert volumes[0].attached is True
    
    def test_get_snapshots(self):
        """Testa obtenção de snapshots"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {
                'Snapshots': [
                    {
                        'SnapshotId': 'snap-123',
                        'VolumeId': 'vol-123',
                        'VolumeSize': 100,
                        'State': 'completed',
                        'StartTime': datetime.now()
                    }
                ]
            }
        ]
        self.mock_ec2.get_paginator.return_value = paginator
        
        snapshots = self.service.get_snapshots()
        
        assert len(snapshots) == 1
        assert snapshots[0].snapshot_id == 'snap-123'
    
    def test_get_metrics(self):
        """Testa obtenção de métricas agregadas"""
        vol_paginator = Mock()
        vol_paginator.paginate.return_value = [
            {
                'Volumes': [
                    {
                        'VolumeId': 'vol-1',
                        'VolumeType': 'gp3',
                        'Size': 100,
                        'State': 'in-use',
                        'AvailabilityZone': 'us-east-1a',
                        'Attachments': [],
                        'Encrypted': False
                    }
                ]
            }
        ]
        
        snap_paginator = Mock()
        snap_paginator.paginate.return_value = [{'Snapshots': []}]
        
        self.mock_ec2.get_paginator.side_effect = [vol_paginator, snap_paginator]
        
        metrics = self.service.get_metrics()
        
        assert metrics.service_name == "Amazon EBS"
        assert metrics.resource_count == 1
    
    def test_get_recommendations_gp2_upgrade(self):
        """Testa recomendação de upgrade gp2 para gp3"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {
                'Volumes': [
                    {
                        'VolumeId': 'vol-gp2',
                        'VolumeType': 'gp2',
                        'Size': 100,
                        'State': 'in-use',
                        'AvailabilityZone': 'us-east-1a',
                        'Attachments': [{'InstanceId': 'i-123'}],
                        'Encrypted': True
                    }
                ]
            }
        ]
        self.mock_ec2.get_paginator.return_value = paginator
        
        recommendations = self.service.get_recommendations()
        
        upgrade_recs = [r for r in recommendations if r.recommendation_type == 'UPGRADE_VOLUME_TYPE']
        assert len(upgrade_recs) >= 1
    
    def test_get_recommendations_unattached(self):
        """Testa recomendação para volumes não anexados"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {
                'Volumes': [
                    {
                        'VolumeId': 'vol-unattached',
                        'VolumeType': 'gp3',
                        'Size': 50,
                        'State': 'available',
                        'AvailabilityZone': 'us-east-1a',
                        'Attachments': [],
                        'Encrypted': True
                    }
                ]
            }
        ]
        self.mock_ec2.get_paginator.return_value = paginator
        
        recommendations = self.service.get_recommendations()
        
        delete_recs = [r for r in recommendations if r.recommendation_type == 'DELETE_UNATTACHED']
        assert len(delete_recs) >= 1


class TestDynamoDBFinOpsService:
    """Testes para DynamoDBFinOpsService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_dynamodb = Mock()
        self.mock_cloudwatch = Mock()
        self.mock_cost = Mock()
        
        self.service = DynamoDBFinOpsService(
            dynamodb_client=self.mock_dynamodb,
            cloudwatch_client=self.mock_cloudwatch,
            cost_client=self.mock_cost
        )
    
    def test_service_name(self):
        """Testa nome do serviço"""
        assert self.service.get_service_name() == "Amazon DynamoDB"
    
    def test_health_check_success(self):
        """Testa health check com sucesso"""
        self.mock_dynamodb.list_tables.return_value = {'TableNames': []}
        
        result = self.service.health_check()
        
        assert result is True
    
    def test_health_check_failure(self):
        """Testa health check com falha"""
        self.mock_dynamodb.list_tables.side_effect = Exception("Access denied")
        
        result = self.service.health_check()
        
        assert result is False
    
    def test_get_tables(self):
        """Testa obtenção de tabelas"""
        paginator = Mock()
        paginator.paginate.return_value = [{'TableNames': ['table-1', 'table-2']}]
        self.mock_dynamodb.get_paginator.return_value = paginator
        
        self.mock_dynamodb.describe_table.return_value = {
            'Table': {
                'TableName': 'table-1',
                'TableStatus': 'ACTIVE',
                'ItemCount': 1000,
                'TableSizeBytes': 1024000,
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        }
        self.mock_dynamodb.describe_time_to_live.return_value = {
            'TimeToLiveDescription': {'TimeToLiveStatus': 'DISABLED'}
        }
        self.mock_dynamodb.describe_continuous_backups.return_value = {
            'ContinuousBackupsDescription': {
                'PointInTimeRecoveryDescription': {'PointInTimeRecoveryStatus': 'DISABLED'}
            }
        }
        
        tables = self.service.get_tables()
        
        assert len(tables) == 2
    
    def test_get_metrics(self):
        """Testa obtenção de métricas agregadas"""
        paginator = Mock()
        paginator.paginate.return_value = [{'TableNames': ['test-table']}]
        self.mock_dynamodb.get_paginator.return_value = paginator
        
        self.mock_dynamodb.describe_table.return_value = {
            'Table': {
                'TableName': 'test-table',
                'TableStatus': 'ACTIVE',
                'ItemCount': 500,
                'TableSizeBytes': 512000,
                'BillingModeSummary': {'BillingMode': 'PAY_PER_REQUEST'}
            }
        }
        self.mock_dynamodb.describe_time_to_live.return_value = {
            'TimeToLiveDescription': {'TimeToLiveStatus': 'ENABLED'}
        }
        self.mock_dynamodb.describe_continuous_backups.return_value = {
            'ContinuousBackupsDescription': {
                'PointInTimeRecoveryDescription': {'PointInTimeRecoveryStatus': 'ENABLED'}
            }
        }
        
        metrics = self.service.get_metrics()
        
        assert metrics.service_name == "Amazon DynamoDB"
        assert metrics.resource_count == 1
    
    def test_get_recommendations_no_pitr(self):
        """Testa recomendação para tabela sem PITR"""
        paginator = Mock()
        paginator.paginate.return_value = [{'TableNames': ['no-pitr-table']}]
        self.mock_dynamodb.get_paginator.return_value = paginator
        
        self.mock_dynamodb.describe_table.return_value = {
            'Table': {
                'TableName': 'no-pitr-table',
                'TableStatus': 'ACTIVE',
                'ItemCount': 100,
                'TableSizeBytes': 10240,
                'BillingModeSummary': {'BillingMode': 'PAY_PER_REQUEST'}
            }
        }
        self.mock_dynamodb.describe_time_to_live.return_value = {
            'TimeToLiveDescription': {'TimeToLiveStatus': 'DISABLED'}
        }
        self.mock_dynamodb.describe_continuous_backups.return_value = {
            'ContinuousBackupsDescription': {
                'PointInTimeRecoveryDescription': {'PointInTimeRecoveryStatus': 'DISABLED'}
            }
        }
        self.mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
        
        recommendations = self.service.get_recommendations()
        
        pitr_recs = [r for r in recommendations if r.recommendation_type == 'ENABLE_PITR']
        assert len(pitr_recs) >= 1


class TestS3Bucket:
    """Testes para S3Bucket dataclass"""
    
    def test_create_bucket(self):
        """Testa criação de S3Bucket"""
        bucket = S3Bucket(
            name="my-bucket",
            region="us-east-1"
        )
        
        assert bucket.name == "my-bucket"
        assert bucket.region == "us-east-1"
        assert bucket.storage_class == "STANDARD"


class TestEBSVolume:
    """Testes para EBSVolume dataclass"""
    
    def test_create_volume(self):
        """Testa criação de EBSVolume"""
        volume = EBSVolume(
            volume_id="vol-123",
            volume_type="gp3",
            size_gb=100,
            state="in-use",
            availability_zone="us-east-1a"
        )
        
        assert volume.volume_id == "vol-123"
        assert volume.volume_type == "gp3"
        assert volume.size_gb == 100


class TestDynamoDBTable:
    """Testes para DynamoDBTable dataclass"""
    
    def test_create_table(self):
        """Testa criação de DynamoDBTable"""
        table = DynamoDBTable(
            table_name="my-table",
            table_status="ACTIVE"
        )
        
        assert table.table_name == "my-table"
        assert table.table_status == "ACTIVE"
        assert table.billing_mode == "PROVISIONED"
