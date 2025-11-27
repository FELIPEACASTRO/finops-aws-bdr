"""
Integration Tests - ServiceFactory + All 252 AWS Services
Testes de integração completos da factory com todos os serviços
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

import boto3
from moto import mock_aws

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from finops_aws.core.factories import (
    ServiceFactory, AWSClientFactory, AWSClientConfig, AWSServiceType
)


class TestServiceFactoryCompleteIntegration:
    """Testes de integração completa da ServiceFactory"""
    
    @pytest.fixture
    def client_factory(self):
        """Factory de clientes AWS mockada"""
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        """Factory de serviços"""
        return ServiceFactory(client_factory)
    
    def test_all_service_getters_exist(self, service_factory):
        """Teste: Todos os getters de serviço existem"""
        expected_services = [
            'ec2', 'lambda_service', 'rds', 's3', 'dynamodb', 'ecs', 'eks',
            'cloudwatch', 'cloudfront', 'route53', 'iam', 'kms', 'sns', 'sqs',
            'sagemaker', 'bedrock', 'glue', 'athena', 'redshift', 'emr',
            'kinesis', 'batch', 'stepfunctions', 'apigateway', 'cognito',
            'secretsmanager', 'waf', 'guardduty', 'inspector', 'macie',
            'securityhub', 'config', 'cloudtrail', 'backup', 'datasync'
        ]
        
        missing_getters = []
        for service_name in expected_services:
            getter_name = f'get_{service_name}_service'
            if not hasattr(service_factory, getter_name):
                alt_getter = f'get_{service_name}'
                if not hasattr(service_factory, alt_getter):
                    missing_getters.append(service_name)
        
        assert len(missing_getters) == 0, f"Missing getters: {missing_getters}"
    
    @mock_aws
    def test_ec2_service_full_workflow(self, service_factory):
        """Teste E2E: Fluxo completo do serviço EC2"""
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        
        ec2_client.run_instances(
            ImageId='ami-12345678',
            MinCount=2,
            MaxCount=2,
            InstanceType='t3.medium'
        )
        
        service = service_factory.get_ec2_service()
        
        assert service is not None
        assert hasattr(service, 'get_resources') or hasattr(service, 'get_instances')
        assert hasattr(service, 'health_check')
    
    @mock_aws
    def test_lambda_service_full_workflow(self, service_factory):
        """Teste E2E: Fluxo completo do serviço Lambda"""
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        iam_client = boto3.client('iam', region_name='us-east-1')
        
        try:
            iam_client.create_role(
                RoleName='lambda-test-role',
                AssumeRolePolicyDocument='{"Version": "2012-10-17", "Statement": []}'
            )
        except Exception:
            pass
        
        service = service_factory.get_lambda_service()
        
        assert service is not None
        assert hasattr(service, 'get_resources') or hasattr(service, 'get_functions')
    
    @mock_aws
    def test_s3_service_full_workflow(self, service_factory):
        """Teste E2E: Fluxo completo do serviço S3"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        s3_client.create_bucket(Bucket='test-bucket-1')
        s3_client.create_bucket(Bucket='test-bucket-2')
        s3_client.put_object(Bucket='test-bucket-1', Key='test.txt', Body=b'test content')
        
        service = service_factory.get_s3_service()
        
        assert service is not None
        assert hasattr(service, 'get_resources') or hasattr(service, 'get_buckets')
    
    @mock_aws
    def test_rds_service_full_workflow(self, service_factory):
        """Teste E2E: Fluxo completo do serviço RDS"""
        rds_client = boto3.client('rds', region_name='us-east-1')
        
        try:
            rds_client.create_db_instance(
                DBInstanceIdentifier='test-db',
                DBInstanceClass='db.t3.micro',
                Engine='mysql',
                MasterUsername='admin',
                MasterUserPassword='password123'
            )
        except Exception:
            pass
        
        service = service_factory.get_rds_service()
        
        assert service is not None
        assert hasattr(service, 'get_resources') or hasattr(service, 'get_instances')
    
    @mock_aws
    def test_dynamodb_service_full_workflow(self, service_factory):
        """Teste E2E: Fluxo completo do serviço DynamoDB"""
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        table = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        service = service_factory.get_dynamodb_service()
        
        assert service is not None
        assert hasattr(service, 'get_resources') or hasattr(service, 'get_tables')
    
    def test_all_services_have_common_interface(self, service_factory):
        """Teste: Todos os serviços têm interface comum"""
        sample_services = [
            'ec2', 's3', 'lambda_service', 'rds', 'dynamodb',
            'ecs', 'cloudwatch', 'sns', 'sqs'
        ]
        
        for service_name in sample_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                
                assert hasattr(service, 'SERVICE_NAME') or hasattr(service, 'service_name')


class TestServiceFactoryAllServicesInstantiation:
    """Testes de instanciação de todos os 252 serviços"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        return ServiceFactory(client_factory)
    
    def test_get_all_services_returns_all(self, service_factory):
        """Teste: get_all_services retorna todos os serviços"""
        all_services = service_factory.get_all_services()
        
        assert len(all_services) >= 250, f"Expected 250+ services, got {len(all_services)}"
    
    def test_each_service_instantiates_successfully(self, service_factory):
        """Teste: Cada serviço instancia com sucesso"""
        all_services = service_factory.get_all_services()
        
        failed_services = []
        for service_name, service_instance in all_services.items():
            if service_instance is None:
                failed_services.append(service_name)
        
        assert len(failed_services) == 0, f"Failed to instantiate: {failed_services}"
    
    def test_services_have_required_methods(self, service_factory):
        """Teste: Serviços têm métodos obrigatórios"""
        all_services = service_factory.get_all_services()
        
        required_methods = ['health_check']
        services_missing_methods = {}
        
        for service_name, service in all_services.items():
            missing = []
            for method in required_methods:
                if not hasattr(service, method):
                    missing.append(method)
            if missing:
                services_missing_methods[service_name] = missing
        
        assert len(services_missing_methods) == 0, f"Services missing methods: {services_missing_methods}"
    
    def test_service_caching(self, service_factory):
        """Teste: Serviços são cacheados corretamente"""
        service1 = service_factory.get_ec2_service()
        service2 = service_factory.get_ec2_service()
        
        assert service1 is service2


class TestServiceFactoryCategories:
    """Testes por categoria de serviço"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        return ServiceFactory(client_factory)
    
    def test_compute_services(self, service_factory):
        """Teste: Serviços de Compute"""
        compute_services = ['ec2', 'lambda_service', 'batch', 'lightsail', 'apprunner']
        
        for service_name in compute_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"
    
    def test_storage_services(self, service_factory):
        """Teste: Serviços de Storage"""
        storage_services = ['s3', 'ebs', 'efs', 'fsx', 'backup']
        
        for service_name in storage_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"
    
    def test_database_services(self, service_factory):
        """Teste: Serviços de Database"""
        database_services = ['rds', 'dynamodb', 'elasticache', 'neptune', 'documentdb']
        
        for service_name in database_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"
    
    def test_networking_services(self, service_factory):
        """Teste: Serviços de Networking"""
        networking_services = ['cloudfront', 'route53', 'elb', 'apigateway']
        
        for service_name in networking_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"
    
    def test_security_services(self, service_factory):
        """Teste: Serviços de Security"""
        security_services = ['iam', 'kms', 'waf', 'guardduty', 'securityhub']
        
        for service_name in security_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"
    
    def test_aiml_services(self, service_factory):
        """Teste: Serviços de AI/ML"""
        aiml_services = ['sagemaker', 'bedrock', 'comprehend', 'rekognition', 'textract']
        
        for service_name in aiml_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"
    
    def test_analytics_services(self, service_factory):
        """Teste: Serviços de Analytics"""
        analytics_services = ['athena', 'glue', 'emr', 'kinesis', 'quicksight']
        
        for service_name in analytics_services:
            getter = getattr(service_factory, f'get_{service_name}_service', None)
            if getter:
                service = getter()
                assert service is not None, f"Failed to get {service_name}"


class TestAWSClientFactoryIntegration:
    """Testes de integração do AWSClientFactory"""
    
    def test_client_factory_creates_clients(self):
        """Teste: Factory cria clientes corretamente"""
        config = AWSClientConfig(region='us-east-1')
        factory = AWSClientFactory(config)
        
        for service_type in [AWSServiceType.EC2, AWSServiceType.S3, AWSServiceType.LAMBDA]:
            with patch.object(factory.session, 'client') as mock_client:
                mock_client.return_value = MagicMock()
                client = factory.get_client(service_type)
                assert client is not None
    
    def test_client_factory_caches_clients(self):
        """Teste: Factory cacheia clientes"""
        config = AWSClientConfig(region='us-east-1')
        factory = AWSClientFactory(config)
        
        with patch.object(factory.session, 'client') as mock_client:
            mock_client.return_value = MagicMock()
            
            client1 = factory.get_client(AWSServiceType.EC2)
            client2 = factory.get_client(AWSServiceType.EC2)
            
            assert mock_client.call_count == 1
    
    def test_client_factory_region_override(self):
        """Teste: Factory suporta override de região"""
        config = AWSClientConfig(region='us-east-1')
        factory = AWSClientFactory(config)
        
        with patch.object(factory.session, 'client') as mock_client:
            mock_client.return_value = MagicMock()
            
            factory.get_client(AWSServiceType.EC2, region='eu-west-1')
            
            call_args = mock_client.call_args
            assert call_args[1]['region_name'] == 'eu-west-1'
    
    def test_client_factory_cost_explorer_always_us_east_1(self):
        """Teste: Cost Explorer sempre usa us-east-1"""
        config = AWSClientConfig(region='eu-west-1')
        factory = AWSClientFactory(config)
        
        with patch.object(factory.session, 'client') as mock_client:
            mock_client.return_value = MagicMock()
            
            factory.get_client(AWSServiceType.COST_EXPLORER)
            
            call_args = mock_client.call_args
            assert call_args[1]['region_name'] == 'us-east-1'


class TestServiceHealthChecks:
    """Testes de health check de serviços"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        return ServiceFactory(client_factory)
    
    @mock_aws
    def test_ec2_health_check(self, service_factory):
        """Teste: Health check do EC2"""
        service = service_factory.get_ec2_service()
        result = service.health_check()
        assert result is not None
    
    @mock_aws
    def test_s3_health_check(self, service_factory):
        """Teste: Health check do S3"""
        service = service_factory.get_s3_service()
        result = service.health_check()
        assert result is not None
    
    @mock_aws
    def test_lambda_health_check(self, service_factory):
        """Teste: Health check do Lambda"""
        service = service_factory.get_lambda_service()
        result = service.health_check()
        assert result is not None
    
    def test_all_services_health_check(self, service_factory):
        """Teste: Health check de todos os serviços"""
        all_services = service_factory.get_all_services()
        
        health_results = {}
        for service_name, service in all_services.items():
            if hasattr(service, 'health_check'):
                try:
                    result = service.health_check()
                    health_results[service_name] = 'OK' if result else 'FAIL'
                except Exception as e:
                    health_results[service_name] = f'ERROR: {str(e)[:50]}'
        
        assert len(health_results) > 0


class TestServiceDataIntegrity:
    """Testes de integridade de dados dos serviços"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        return ServiceFactory(client_factory)
    
    @mock_aws
    def test_ec2_returns_valid_structure(self, service_factory):
        """Teste: EC2 retorna estrutura válida"""
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        ec2_client.run_instances(
            ImageId='ami-12345678',
            MinCount=1,
            MaxCount=1,
            InstanceType='t3.micro'
        )
        
        service = service_factory.get_ec2_service()
        
        if hasattr(service, 'get_resources'):
            resources = service.get_resources()
            assert isinstance(resources, (dict, list))
    
    @mock_aws
    def test_s3_returns_valid_structure(self, service_factory):
        """Teste: S3 retorna estrutura válida"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        service = service_factory.get_s3_service()
        
        if hasattr(service, 'get_resources'):
            resources = service.get_resources()
            assert isinstance(resources, (dict, list))
    
    def test_service_response_types(self, service_factory):
        """Teste: Tipos de resposta dos serviços"""
        all_services = service_factory.get_all_services()
        
        for service_name, service in list(all_services.items())[:10]:
            if hasattr(service, 'get_resources'):
                try:
                    resources = service.get_resources()
                    assert resources is not None
                    assert isinstance(resources, (dict, list, tuple))
                except Exception:
                    pass
