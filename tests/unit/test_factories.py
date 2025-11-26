"""
Testes unitários para Factory Pattern (FASE 1.3)

Testa AWSClientFactory e ServiceFactory para garantir:
- Criação correta de clientes AWS
- Cache de clientes (singleton)
- Injeção de mocks para testes
- Configurações customizadas
- Criação de serviços com dependências injetadas
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.config import Config

from src.finops_aws.core.factories import (
    AWSClientFactory,
    AWSServiceType,
    AWSClientConfig,
    ServiceFactory,
    ServiceConfig
)


class TestAWSClientConfig:
    """Testes para AWSClientConfig"""
    
    def test_default_config(self):
        """Testa configuração padrão"""
        config = AWSClientConfig()
        
        assert config.max_retries == 3
        assert config.connect_timeout == 10
        assert config.read_timeout == 30
        assert config.max_pool_connections == 10
        assert config.signature_version == "v4"
    
    def test_custom_config(self):
        """Testa configuração personalizada"""
        config = AWSClientConfig(
            region='eu-west-1',
            max_retries=5,
            connect_timeout=15,
            read_timeout=60
        )
        
        assert config.region == 'eu-west-1'
        assert config.max_retries == 5
        assert config.connect_timeout == 15
        assert config.read_timeout == 60
    
    def test_to_botocore_config(self):
        """Testa conversão para botocore Config"""
        config = AWSClientConfig(
            region='us-west-2',
            max_retries=4
        )
        
        botocore_config = config.to_botocore_config()
        
        assert isinstance(botocore_config, Config)


class TestAWSClientFactory:
    """Testes para AWSClientFactory"""
    
    def setup_method(self):
        """Reset singleton antes de cada teste"""
        AWSClientFactory.reset_instance()
    
    def teardown_method(self):
        """Limpa singleton após cada teste"""
        AWSClientFactory.reset_instance()
    
    def test_singleton_pattern(self):
        """Testa que factory é singleton"""
        factory1 = AWSClientFactory()
        factory2 = AWSClientFactory()
        
        assert factory1 is factory2
    
    def test_reset_instance(self):
        """Testa reset do singleton"""
        factory1 = AWSClientFactory()
        AWSClientFactory.reset_instance()
        factory2 = AWSClientFactory()
        
        assert factory1 is not factory2
    
    def test_register_mock(self):
        """Testa registro de mock"""
        factory = AWSClientFactory()
        mock_client = Mock()
        
        factory.register_mock(AWSServiceType.EC2, mock_client)
        client = factory.get_client(AWSServiceType.EC2)
        
        assert client is mock_client
    
    def test_clear_mocks(self):
        """Testa limpeza de mocks"""
        factory = AWSClientFactory()
        mock_client = Mock()
        
        factory.register_mock(AWSServiceType.EC2, mock_client)
        factory.clear_mocks()
        
        assert AWSServiceType.EC2 not in factory._mocks
    
    @patch('boto3.Session')
    def test_get_client_creates_client(self, mock_session):
        """Testa criação de cliente boto3"""
        mock_boto_client = Mock()
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        factory = AWSClientFactory()
        client = factory.get_client(AWSServiceType.EC2)
        
        mock_session_instance.client.assert_called()
        assert client is mock_boto_client
    
    @patch('boto3.Session')
    def test_get_client_caches_client(self, mock_session):
        """Testa que cliente é cacheado"""
        mock_boto_client = Mock()
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        factory = AWSClientFactory()
        client1 = factory.get_client(AWSServiceType.EC2)
        client2 = factory.get_client(AWSServiceType.EC2)
        
        assert client1 is client2
        assert mock_session_instance.client.call_count == 1
    
    @patch('boto3.Session')
    def test_cost_explorer_uses_us_east_1(self, mock_session):
        """Testa que Cost Explorer sempre usa us-east-1"""
        mock_boto_client = Mock()
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = AWSClientConfig(region='eu-west-1')
        factory = AWSClientFactory(config=config)
        factory.get_client(AWSServiceType.COST_EXPLORER)
        
        call_args = mock_session_instance.client.call_args
        assert call_args[1]['region_name'] == 'us-east-1'
    
    @patch('boto3.Session')
    def test_clear_cache(self, mock_session):
        """Testa limpeza de cache de clientes"""
        mock_boto_client = Mock()
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        factory = AWSClientFactory()
        factory.get_client(AWSServiceType.EC2)
        
        assert len(factory._clients) == 1
        
        factory.clear_cache()
        
        assert len(factory._clients) == 0
    
    @patch('boto3.Session')
    def test_different_regions_create_different_clients(self, mock_session):
        """Testa que regiões diferentes criam clientes diferentes"""
        mock_session_instance = MagicMock()
        mock_session_instance.client.side_effect = [Mock(), Mock()]
        mock_session.return_value = mock_session_instance
        
        factory = AWSClientFactory()
        client1 = factory.get_client(AWSServiceType.EC2, region='us-east-1')
        client2 = factory.get_client(AWSServiceType.EC2, region='eu-west-1')
        
        assert client1 is not client2
        assert mock_session_instance.client.call_count == 2


class TestServiceFactory:
    """Testes para ServiceFactory"""
    
    def setup_method(self):
        """Reset singletons antes de cada teste"""
        ServiceFactory.reset_instance()
    
    def teardown_method(self):
        """Limpa singletons após cada teste"""
        ServiceFactory.reset_instance()
    
    def test_singleton_pattern(self):
        """Testa que factory é singleton"""
        factory1 = ServiceFactory()
        factory2 = ServiceFactory()
        
        assert factory1 is factory2
    
    def test_reset_instance(self):
        """Testa reset do singleton"""
        factory1 = ServiceFactory()
        ServiceFactory.reset_instance()
        factory2 = ServiceFactory()
        
        assert factory1 is not factory2
    
    def test_register_mock(self):
        """Testa registro de mock de serviço"""
        factory = ServiceFactory()
        mock_service = Mock()
        
        factory.register_mock('cost', mock_service)
        service = factory.get_cost_service()
        
        assert service is mock_service
    
    def test_clear_mocks(self):
        """Testa limpeza de mocks de serviços"""
        factory = ServiceFactory()
        mock_service = Mock()
        
        factory.register_mock('cost', mock_service)
        factory.clear_mocks()
        
        assert 'cost' not in factory._mocks
    
    def test_get_cost_service(self):
        """Testa obtenção do CostService com mock"""
        factory = ServiceFactory()
        mock_service = Mock()
        factory.register_mock('cost', mock_service)
        
        service = factory.get_cost_service()
        
        assert service is mock_service
    
    def test_get_cost_service_creates_real_service(self):
        """Testa que CostService real é criado com cliente injetado"""
        factory = ServiceFactory()
        mock_client = Mock()
        factory.client_factory.register_mock(AWSServiceType.COST_EXPLORER, mock_client)
        
        service = factory.get_cost_service()
        
        assert service is not None
        assert service.client is mock_client
    
    def test_get_metrics_service(self):
        """Testa obtenção do MetricsService com mock"""
        factory = ServiceFactory()
        mock_service = Mock()
        factory.register_mock('metrics', mock_service)
        
        service = factory.get_metrics_service()
        
        assert service is mock_service
    
    def test_get_metrics_service_creates_real_service(self):
        """Testa que MetricsService real é criado com clientes injetados"""
        factory = ServiceFactory()
        mock_cloudwatch = Mock()
        mock_ec2 = Mock()
        mock_lambda = Mock()
        
        factory.client_factory.register_mock(AWSServiceType.CLOUDWATCH, mock_cloudwatch)
        factory.client_factory.register_mock(AWSServiceType.EC2, mock_ec2)
        factory.client_factory.register_mock(AWSServiceType.LAMBDA, mock_lambda)
        
        service = factory.get_metrics_service()
        
        assert service is not None
        assert service.cloudwatch is mock_cloudwatch
        assert service.ec2 is mock_ec2
        assert service.lambda_client is mock_lambda
    
    def test_get_optimizer_service(self):
        """Testa obtenção do OptimizerService com mock"""
        factory = ServiceFactory()
        mock_service = Mock()
        factory.register_mock('optimizer', mock_service)
        
        service = factory.get_optimizer_service()
        
        assert service is mock_service
    
    def test_get_optimizer_service_creates_real_service(self):
        """Testa que OptimizerService real é criado com cliente injetado"""
        factory = ServiceFactory()
        mock_client = Mock()
        factory.client_factory.register_mock(AWSServiceType.COMPUTE_OPTIMIZER, mock_client)
        
        service = factory.get_optimizer_service()
        
        assert service is not None
        assert service.client is mock_client
    
    def test_get_rds_service(self):
        """Testa obtenção do RDSService com mock"""
        factory = ServiceFactory()
        mock_service = Mock()
        factory.register_mock('rds', mock_service)
        
        service = factory.get_rds_service()
        
        assert service is mock_service
    
    def test_get_rds_service_creates_real_service(self):
        """Testa que RDSService real é criado com clientes injetados"""
        factory = ServiceFactory()
        mock_rds = Mock()
        mock_cloudwatch = Mock()
        mock_cost = Mock()
        
        factory.client_factory.register_mock(AWSServiceType.RDS, mock_rds)
        factory.client_factory.register_mock(AWSServiceType.CLOUDWATCH, mock_cloudwatch)
        factory.client_factory.register_mock(AWSServiceType.COST_EXPLORER, mock_cost)
        
        service = factory.get_rds_service()
        
        assert service is not None
        assert service.rds_client is mock_rds
        assert service.cloudwatch_client is mock_cloudwatch
        assert service.cost_client is mock_cost
    
    def test_services_are_cached(self):
        """Testa que serviços são cacheados"""
        factory = ServiceFactory()
        mock_service = Mock()
        factory.register_mock('cost', mock_service)
        
        service1 = factory.get_cost_service()
        service2 = factory.get_cost_service()
        
        assert service1 is service2
    
    def test_clear_cache(self):
        """Testa limpeza de cache de serviços"""
        factory = ServiceFactory()
        mock_service = Mock()
        
        factory._services['cost'] = mock_service
        assert len(factory._services) == 1
        
        factory.clear_cache()
        assert len(factory._services) == 0
    
    def test_get_all_services(self):
        """Testa obtenção de todos os serviços"""
        factory = ServiceFactory()
        factory.register_mock('cost', Mock())
        factory.register_mock('metrics', Mock())
        factory.register_mock('optimizer', Mock())
        factory.register_mock('rds', Mock())
        
        services = factory.get_all_services()
        
        assert 'cost' in services
        assert 'metrics' in services
        assert 'optimizer' in services
        assert 'rds' in services


class TestAWSServiceType:
    """Testes para enum AWSServiceType"""
    
    def test_service_types_exist(self):
        """Testa que tipos de serviço existem"""
        assert AWSServiceType.EC2.value == 'ec2'
        assert AWSServiceType.LAMBDA.value == 'lambda'
        assert AWSServiceType.RDS.value == 'rds'
        assert AWSServiceType.S3.value == 's3'
        assert AWSServiceType.DYNAMODB.value == 'dynamodb'
        assert AWSServiceType.CLOUDWATCH.value == 'cloudwatch'
        assert AWSServiceType.COST_EXPLORER.value == 'ce'
        assert AWSServiceType.COMPUTE_OPTIMIZER.value == 'compute-optimizer'
    
    def test_all_supported_services(self):
        """Testa que todos os serviços suportados estão definidos"""
        expected_services = [
            'ec2', 'lambda', 'rds', 's3', 'dynamodb', 'cloudwatch',
            'ce', 'compute-optimizer', 'ebs', 'efs', 'cloudfront',
            'elb', 'route53', 'iam', 'kms', 'sts'
        ]
        
        actual_values = [s.value for s in AWSServiceType]
        
        for service in expected_services:
            assert service in actual_values


class TestServiceConfig:
    """Testes para ServiceConfig"""
    
    def test_default_config(self):
        """Testa configuração padrão"""
        config = ServiceConfig()
        
        assert config.enable_retry is True
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 300
        assert config.custom_config == {}
    
    def test_custom_config(self):
        """Testa configuração personalizada"""
        config = ServiceConfig(
            enable_retry=False,
            enable_caching=False,
            cache_ttl_seconds=600,
            custom_config={'key': 'value'}
        )
        
        assert config.enable_retry is False
        assert config.enable_caching is False
        assert config.cache_ttl_seconds == 600
        assert config.custom_config == {'key': 'value'}


class TestFactoryIntegration:
    """Testes de integração entre factories"""
    
    def setup_method(self):
        """Reset singletons antes de cada teste"""
        ServiceFactory.reset_instance()
    
    def teardown_method(self):
        """Limpa singletons após cada teste"""
        ServiceFactory.reset_instance()
    
    def test_service_factory_uses_client_factory(self):
        """Testa que ServiceFactory usa AWSClientFactory"""
        factory = ServiceFactory()
        
        assert factory.client_factory is not None
        assert isinstance(factory.client_factory, AWSClientFactory)
    
    def test_custom_client_factory_injection(self):
        """Testa injeção de AWSClientFactory customizada"""
        AWSClientFactory.reset_instance()
        custom_client_factory = AWSClientFactory(
            config=AWSClientConfig(region='eu-west-1')
        )
        
        ServiceFactory.reset_instance()
        service_factory = ServiceFactory(client_factory=custom_client_factory)
        
        assert service_factory.client_factory.config.region == 'eu-west-1'
    
    def test_mocks_propagate_correctly(self):
        """Testa que mocks são propagados corretamente"""
        factory = ServiceFactory()
        
        mock_ec2 = Mock()
        factory.client_factory.register_mock(AWSServiceType.EC2, mock_ec2)
        
        client = factory.client_factory.get_client(AWSServiceType.EC2)
        
        assert client is mock_ec2
