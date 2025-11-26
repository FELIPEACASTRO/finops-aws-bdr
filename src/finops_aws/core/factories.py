"""
Factory Pattern - Sistema de Criação de Clientes e Serviços AWS

FASE 1.3 do Roadmap FinOps AWS
Objetivo: Centralizar criação de clientes AWS e serviços com Factory Pattern

Autor: FinOps AWS Team
Data: Novembro 2025

Benefícios:
- Centralização da criação de clientes AWS
- Injeção de dependências facilitada
- Melhor testabilidade (mocks simplificados)
- Consistência na inicialização de serviços
- Configuração centralizada (região, retry, timeouts)
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, Type, TypeVar, Protocol, Callable
from enum import Enum
import boto3
from botocore.config import Config

from ..utils.logger import setup_logger
from .retry_handler import RetryHandler, create_aws_retry_policy

logger = setup_logger(__name__)


class AWSServiceType(Enum):
    """Tipos de serviços AWS suportados"""
    EC2 = "ec2"
    LAMBDA = "lambda"
    RDS = "rds"
    S3 = "s3"
    DYNAMODB = "dynamodb"
    CLOUDWATCH = "cloudwatch"
    COST_EXPLORER = "ce"
    COMPUTE_OPTIMIZER = "compute-optimizer"
    EBS = "ebs"
    EFS = "efs"
    CLOUDFRONT = "cloudfront"
    ELB = "elasticloadbalancing"
    ROUTE53 = "route53"
    IAM = "iam"
    KMS = "kms"
    STS = "sts"


@dataclass
class AWSClientConfig:
    """
    Configuração para clientes AWS
    
    Permite personalizar comportamento de clientes boto3
    com retry, timeouts e outras configurações.
    """
    region: Optional[str] = None
    max_retries: int = 3
    connect_timeout: int = 10
    read_timeout: int = 30
    max_pool_connections: int = 10
    signature_version: str = "v4"
    
    def __post_init__(self):
        if self.region is None:
            self.region = os.getenv('AWS_REGION', 'us-east-1')
    
    def to_botocore_config(self) -> Config:
        """Converte para configuração botocore"""
        return Config(
            region_name=self.region,
            retries={'max_attempts': self.max_retries, 'mode': 'adaptive'},
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            max_pool_connections=self.max_pool_connections,
            signature_version=self.signature_version
        )


class AWSClientFactory:
    """
    Factory para criação de clientes AWS
    
    Centraliza a criação de clientes boto3 com:
    - Cache de clientes (singleton por tipo/região)
    - Configuração padronizada
    - Suporte a injeção para testes
    - Logging de criação de clientes
    
    Uso:
        factory = AWSClientFactory()
        ec2 = factory.get_client(AWSServiceType.EC2)
        
    Com configuração personalizada:
        config = AWSClientConfig(region='eu-west-1', max_retries=5)
        factory = AWSClientFactory(config=config)
        
    Para testes (mock injection):
        mock_ec2 = Mock()
        factory = AWSClientFactory()
        factory.register_mock(AWSServiceType.EC2, mock_ec2)
    """
    
    _instance: Optional['AWSClientFactory'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern para factory"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        config: Optional[AWSClientConfig] = None,
        session: Optional[boto3.Session] = None
    ):
        """
        Inicializa a factory de clientes
        
        Args:
            config: Configuração para clientes AWS
            session: Sessão boto3 customizada (opcional)
        """
        if self._initialized:
            return
            
        self.config = config or AWSClientConfig()
        self.session = session or boto3.Session()
        self._clients: Dict[str, Any] = {}
        self._resources: Dict[str, Any] = {}
        self._mocks: Dict[AWSServiceType, Any] = {}
        self._initialized = True
        
        logger.info("AWSClientFactory initialized", extra={
            'extra_data': {
                'region': self.config.region,
                'max_retries': self.config.max_retries
            }
        })
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton (útil para testes)"""
        cls._instance = None
    
    def register_mock(self, service_type: AWSServiceType, mock_client: Any):
        """
        Registra um mock para um tipo de serviço
        
        Args:
            service_type: Tipo de serviço AWS
            mock_client: Cliente mock para testes
        """
        self._mocks[service_type] = mock_client
        logger.debug(f"Registered mock for {service_type.value}")
    
    def clear_mocks(self):
        """Remove todos os mocks registrados"""
        self._mocks.clear()
    
    def get_client(
        self,
        service_type: AWSServiceType,
        region: Optional[str] = None
    ) -> Any:
        """
        Obtém cliente boto3 para um serviço AWS
        
        Args:
            service_type: Tipo de serviço AWS
            region: Região específica (override)
            
        Returns:
            Cliente boto3 para o serviço
        """
        if service_type in self._mocks:
            return self._mocks[service_type]
        
        effective_region = region or self.config.region
        
        if service_type == AWSServiceType.COST_EXPLORER:
            effective_region = 'us-east-1'
        
        cache_key = f"{service_type.value}_{effective_region}"
        
        if cache_key not in self._clients:
            self._clients[cache_key] = self._create_client(
                service_type.value,
                effective_region
            )
            logger.info(f"Created client for {service_type.value}", extra={
                'extra_data': {'region': effective_region}
            })
        
        return self._clients[cache_key]
    
    def get_resource(
        self,
        service_type: AWSServiceType,
        region: Optional[str] = None
    ) -> Any:
        """
        Obtém resource boto3 para um serviço AWS
        
        Args:
            service_type: Tipo de serviço AWS
            region: Região específica (override)
            
        Returns:
            Resource boto3 para o serviço
        """
        if service_type in self._mocks:
            return self._mocks[service_type]
        
        effective_region = region or self.config.region
        cache_key = f"{service_type.value}_{effective_region}_resource"
        
        if cache_key not in self._resources:
            self._resources[cache_key] = self._create_resource(
                service_type.value,
                effective_region
            )
            logger.info(f"Created resource for {service_type.value}", extra={
                'extra_data': {'region': effective_region}
            })
        
        return self._resources[cache_key]
    
    def _create_client(self, service_name: str, region: str) -> Any:
        """Cria cliente boto3 com configuração padrão"""
        return self.session.client(
            service_name,
            region_name=region,
            config=self.config.to_botocore_config()
        )
    
    def _create_resource(self, service_name: str, region: str) -> Any:
        """Cria resource boto3 com configuração padrão"""
        return self.session.resource(
            service_name,
            region_name=region,
            config=self.config.to_botocore_config()
        )
    
    def clear_cache(self):
        """Limpa cache de clientes"""
        self._clients.clear()
        self._resources.clear()
        logger.info("Client cache cleared")


class ServiceProtocol(Protocol):
    """
    Protocol para padronizar interface de serviços
    
    Todos os serviços devem implementar esta interface
    para garantir consistência e facilitar testes.
    """
    
    def get_service_name(self) -> str:
        """Retorna nome do serviço"""
        ...
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        ...


T = TypeVar('T', bound=ServiceProtocol)


@dataclass
class ServiceConfig:
    """Configuração para serviços"""
    enable_retry: bool = True
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    custom_config: Dict[str, Any] = field(default_factory=dict)


class ServiceFactory:
    """
    Factory para criação de serviços FinOps
    
    Centraliza a instanciação de serviços com:
    - Injeção de dependências
    - Configuração unificada
    - Suporte a mocks para testes
    - Lazy initialization
    
    Uso:
        factory = ServiceFactory()
        cost_service = factory.get_cost_service()
        metrics_service = factory.get_metrics_service()
        
    Para testes:
        factory = ServiceFactory()
        factory.register_mock('cost', mock_cost_service)
    """
    
    _instance: Optional['ServiceFactory'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern para factory"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        client_factory: Optional[AWSClientFactory] = None,
        retry_handler: Optional[RetryHandler] = None,
        config: Optional[ServiceConfig] = None
    ):
        """
        Inicializa a factory de serviços
        
        Args:
            client_factory: Factory de clientes AWS
            retry_handler: Handler de retry para operações
            config: Configuração para serviços
        """
        if self._initialized:
            return
            
        self.client_factory = client_factory or AWSClientFactory()
        self.retry_handler = retry_handler or RetryHandler(
            policy=create_aws_retry_policy()
        )
        self.config = config or ServiceConfig()
        self._services: Dict[str, Any] = {}
        self._mocks: Dict[str, Any] = {}
        self._initialized = True
        
        logger.info("ServiceFactory initialized")
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton (útil para testes)"""
        cls._instance = None
        AWSClientFactory.reset_instance()
    
    def register_mock(self, service_name: str, mock_service: Any):
        """
        Registra um mock para um serviço
        
        Args:
            service_name: Nome do serviço ('cost', 'metrics', 'optimizer')
            mock_service: Serviço mock para testes
        """
        self._mocks[service_name] = mock_service
        logger.debug(f"Registered mock for service: {service_name}")
    
    def clear_mocks(self):
        """Remove todos os mocks registrados"""
        self._mocks.clear()
    
    def get_cost_service(self):
        """
        Obtém instância do CostService
        
        Returns:
            CostService configurado
        """
        if 'cost' in self._mocks:
            return self._mocks['cost']
        
        if 'cost' not in self._services:
            from ..services.cost_service import CostService
            self._services['cost'] = CostService(
                client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['cost']
    
    def get_metrics_service(self):
        """
        Obtém instância do MetricsService
        
        Returns:
            MetricsService configurado
        """
        if 'metrics' in self._mocks:
            return self._mocks['metrics']
        
        if 'metrics' not in self._services:
            from ..services.metrics_service import MetricsService
            self._services['metrics'] = MetricsService(
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                ec2_client=self.client_factory.get_client(AWSServiceType.EC2),
                lambda_client=self.client_factory.get_client(AWSServiceType.LAMBDA)
            )
        
        return self._services['metrics']
    
    def get_optimizer_service(self):
        """
        Obtém instância do OptimizerService
        
        Returns:
            OptimizerService configurado
        """
        if 'optimizer' in self._mocks:
            return self._mocks['optimizer']
        
        if 'optimizer' not in self._services:
            from ..services.optimizer_service import OptimizerService
            self._services['optimizer'] = OptimizerService(
                client=self.client_factory.get_client(AWSServiceType.COMPUTE_OPTIMIZER)
            )
        
        return self._services['optimizer']
    
    def get_rds_service(self):
        """
        Obtém instância do RDSService
        
        Returns:
            RDSService configurado
        """
        if 'rds' in self._mocks:
            return self._mocks['rds']
        
        if 'rds' not in self._services:
            from ..services.rds_service import RDSService
            self._services['rds'] = RDSService(
                rds_client=self.client_factory.get_client(AWSServiceType.RDS),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['rds']
    
    def get_s3_service(self):
        """
        Obtém instância do S3Service
        
        Returns:
            S3Service configurado
        """
        if 's3' in self._mocks:
            return self._mocks['s3']
        
        if 's3' not in self._services:
            from ..services.s3_service import S3Service
            self._services['s3'] = S3Service(
                s3_client=self.client_factory.get_client(AWSServiceType.S3),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['s3']
    
    def get_ebs_service(self):
        """
        Obtém instância do EBSService
        
        Returns:
            EBSService configurado
        """
        if 'ebs' in self._mocks:
            return self._mocks['ebs']
        
        if 'ebs' not in self._services:
            from ..services.ebs_service import EBSService
            self._services['ebs'] = EBSService(
                ec2_client=self.client_factory.get_client(AWSServiceType.EC2),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['ebs']
    
    def get_dynamodb_service(self):
        """
        Obtém instância do DynamoDBFinOpsService
        
        Returns:
            DynamoDBFinOpsService configurado
        """
        if 'dynamodb' in self._mocks:
            return self._mocks['dynamodb']
        
        if 'dynamodb' not in self._services:
            from ..services.dynamodb_finops_service import DynamoDBFinOpsService
            self._services['dynamodb'] = DynamoDBFinOpsService(
                dynamodb_client=self.client_factory.get_client(AWSServiceType.DYNAMODB),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['dynamodb']
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        Obtém todas as instâncias de serviços
        
        Returns:
            Dicionário com todos os serviços
        """
        return {
            'cost': self.get_cost_service(),
            'metrics': self.get_metrics_service(),
            'optimizer': self.get_optimizer_service(),
            'rds': self.get_rds_service(),
            's3': self.get_s3_service(),
            'ebs': self.get_ebs_service(),
            'dynamodb': self.get_dynamodb_service()
        }
    
    def clear_cache(self):
        """Limpa cache de serviços"""
        self._services.clear()
        logger.info("Service cache cleared")
