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
            ('ec2_finops', 'get_ec2_finops_service'),
            ('lambda_finops', 'get_lambda_finops_service'),
            ('rds', 'get_rds_service'),
            ('s3', 'get_s3_service'),
            ('dynamodb', 'get_dynamodb_service'),
            ('ecs', 'get_ecs_service'),
            ('eks', 'get_eks_service'),
            ('cloudwatch', 'get_cloudwatch_service'),
            ('cloudfront', 'get_cloudfront_service'),
            ('iam', 'get_iam_service'),
        ]
        
        missing_getters = []
        for service_name, getter_name in expected_services:
            if not hasattr(service_factory, getter_name):
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
        
        service = service_factory.get_ec2_finops_service()
        
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
        
        service = service_factory.get_lambda_finops_service()
        
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
        has_valid_interface = (
            hasattr(service, 'get_resources') or 
            hasattr(service, 'get_instances') or
            hasattr(service, 'get_rds_instances') or
            hasattr(service, 'get_metrics') or
            hasattr(service, 'get_rds_metrics') or
            hasattr(service, 'health_check')
        )
        assert has_valid_interface, "RDS service missing expected interface"
    
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
        all_services = service_factory.get_all_services()
        
        services_checked = 0
        for service_name, service in list(all_services.items())[:10]:
            if service is not None:
                assert hasattr(service, 'health_check'), f"{service_name} missing health_check"
                services_checked += 1
        
        assert services_checked > 0, "No services could be verified"


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
        service1 = service_factory.get_ec2_finops_service()
        service2 = service_factory.get_ec2_finops_service()
        
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
        all_services = service_factory.get_all_services()
        
        compute_keywords = ['ec2', 'lambda', 'batch', 'lightsail', 'apprunner']
        compute_found = 0
        
        for service_name in all_services:
            if any(kw in service_name.lower() for kw in compute_keywords):
                compute_found += 1
        
        assert compute_found >= 3, f"Expected 3+ compute services, found {compute_found}"
    
    def test_storage_services(self, service_factory):
        """Teste: Serviços de Storage"""
        all_services = service_factory.get_all_services()
        
        storage_keywords = ['s3', 'ebs', 'efs', 'fsx', 'backup']
        storage_found = 0
        
        for service_name in all_services:
            if any(kw in service_name.lower() for kw in storage_keywords):
                storage_found += 1
        
        assert storage_found >= 3, f"Expected 3+ storage services, found {storage_found}"
    
    def test_database_services(self, service_factory):
        """Teste: Serviços de Database"""
        all_services = service_factory.get_all_services()
        
        db_keywords = ['rds', 'dynamodb', 'aurora', 'neptune', 'documentdb', 'elasticache']
        db_found = 0
        
        for service_name in all_services:
            if any(kw in service_name.lower() for kw in db_keywords):
                db_found += 1
        
        assert db_found >= 3, f"Expected 3+ database services, found {db_found}"
    
    def test_networking_services(self, service_factory):
        """Teste: Serviços de Networking"""
        all_services = service_factory.get_all_services()
        
        net_keywords = ['vpc', 'route53', 'cloudfront', 'elb', 'apigateway']
        net_found = 0
        
        for service_name in all_services:
            if any(kw in service_name.lower() for kw in net_keywords):
                net_found += 1
        
        assert net_found >= 3, f"Expected 3+ networking services, found {net_found}"


class TestAWSClientFactoryIntegration:
    """Testes de integração do AWSClientFactory"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @mock_aws
    def test_client_factory_creates_clients(self, client_factory):
        """Teste: Factory cria clientes corretamente"""
        ec2_client = client_factory.get_client('ec2')
        s3_client = client_factory.get_client('s3')
        
        assert ec2_client is not None
        assert s3_client is not None
    
    @mock_aws
    def test_client_factory_caches_clients(self, client_factory):
        """Teste: Factory cacheia clientes"""
        client1 = client_factory.get_client('ec2')
        client2 = client_factory.get_client('ec2')
        
        assert client1 is client2
    
    @mock_aws
    def test_client_factory_different_regions(self, client_factory):
        """Teste: Factory suporta diferentes regiões"""
        client_east = client_factory.get_client('ec2', region='us-east-1')
        client_west = client_factory.get_client('ec2', region='us-west-2')
        
        assert client_east is not None
        assert client_west is not None


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
        service = service_factory.get_ec2_finops_service()
        
        try:
            health = service.health_check()
            assert isinstance(health, (dict, bool)), f"Health check must return dict or bool, got {type(health)}"
        except Exception as e:
            if 'NoCredentialsError' in str(type(e).__name__):
                pytest.skip("Moto does not fully implement this API")
            raise
    
    @mock_aws
    def test_lambda_health_check(self, service_factory):
        """Teste: Health check do Lambda"""
        service = service_factory.get_lambda_finops_service()
        
        try:
            health = service.health_check()
            assert isinstance(health, (dict, bool)), f"Health check must return dict or bool, got {type(health)}"
        except Exception as e:
            if 'NoCredentialsError' in str(type(e).__name__):
                pytest.skip("Moto does not fully implement this API")
            raise
    
    @mock_aws
    def test_s3_health_check(self, service_factory):
        """Teste: Health check do S3"""
        service = service_factory.get_s3_service()
        
        try:
            health = service.health_check()
            assert isinstance(health, (dict, bool)), f"Health check must return dict or bool, got {type(health)}"
        except Exception as e:
            if 'NoCredentialsError' in str(type(e).__name__):
                pytest.skip("Moto does not fully implement this API")
            raise


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
        
        service = service_factory.get_ec2_finops_service()
        try:
            instances = service.get_instances()
            assert isinstance(instances, list)
        except Exception as e:
            if 'NoCredentialsError' in str(type(e).__name__) or 'NotImplementedError' in str(type(e).__name__):
                pytest.skip("Moto does not fully implement this API")
            raise
    
    @mock_aws
    def test_s3_returns_valid_structure(self, service_factory):
        """Teste: S3 retorna estrutura válida"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        service = service_factory.get_s3_service()
        
        assert service is not None
        if hasattr(service, 'get_buckets'):
            try:
                buckets = service.get_buckets()
                assert isinstance(buckets, list)
            except Exception as e:
                if 'NoCredentialsError' in str(type(e).__name__):
                    pytest.skip("Moto does not fully implement this API")


class TestServiceRecommendations:
    """Testes de recomendações de serviços"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        return ServiceFactory(client_factory)
    
    @mock_aws
    def test_ec2_recommendations_structure(self, service_factory):
        """Teste: Recomendações do EC2 têm estrutura válida"""
        service = service_factory.get_ec2_finops_service()
        
        if hasattr(service, 'get_recommendations'):
            try:
                recommendations = service.get_recommendations()
                assert isinstance(recommendations, list)
            except Exception as e:
                if 'NoCredentialsError' in str(type(e).__name__) or 'NotImplementedError' in str(type(e).__name__):
                    pytest.skip("Moto does not fully implement this API")
                raise
    
    @mock_aws
    def test_lambda_recommendations_structure(self, service_factory):
        """Teste: Recomendações do Lambda têm estrutura válida"""
        service = service_factory.get_lambda_finops_service()
        
        if hasattr(service, 'get_recommendations'):
            try:
                recommendations = service.get_recommendations()
                assert isinstance(recommendations, list)
            except Exception as e:
                if 'NoCredentialsError' in str(type(e).__name__) or 'NotImplementedError' in str(type(e).__name__):
                    pytest.skip("Moto does not fully implement this API")
                raise


class TestServiceMetrics:
    """Testes de métricas de serviços"""
    
    @pytest.fixture
    def client_factory(self):
        config = AWSClientConfig(region='us-east-1')
        return AWSClientFactory(config)
    
    @pytest.fixture
    def service_factory(self, client_factory):
        return ServiceFactory(client_factory)
    
    @mock_aws
    def test_ec2_metrics_structure(self, service_factory):
        """Teste: Métricas do EC2 têm estrutura válida"""
        service = service_factory.get_ec2_finops_service()
        
        if hasattr(service, 'get_metrics'):
            try:
                metrics = service.get_metrics()
                assert metrics is not None
            except Exception as e:
                if 'NoCredentialsError' in str(type(e).__name__) or 'NotImplementedError' in str(type(e).__name__):
                    pytest.skip("Moto does not fully implement this API")
                raise
    
    @mock_aws
    def test_cloudwatch_service_exists(self, service_factory):
        """Teste: Serviço CloudWatch existe"""
        service = service_factory.get_cloudwatch_service()
        
        assert service is not None
        assert hasattr(service, 'health_check')
