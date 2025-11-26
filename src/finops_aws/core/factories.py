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
    ELASTICACHE = "elasticache"
    ECS = "ecs"
    CLOUDFRONT = "cloudfront"
    ELB = "elb"
    ELB_V2 = "elbv2"
    ROUTE53 = "route53"
    IAM = "iam"
    KMS = "kms"
    STS = "sts"
    REDSHIFT = "redshift"
    REDSHIFT_SERVERLESS = "redshift-serverless"
    EMR = "emr"
    EMR_SERVERLESS = "emr-serverless"
    KINESIS = "kinesis"
    FIREHOSE = "firehose"
    GLUE = "glue"
    SAGEMAKER = "sagemaker"
    BACKUP = "backup"
    SNS = "sns"
    SQS = "sqs"
    SECRETS_MANAGER = "secretsmanager"
    PRICING = "pricing"


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
    
    def get_efs_service(self):
        """
        Obtém instância do EFSService
        
        Returns:
            EFSService configurado
        """
        if 'efs' in self._mocks:
            return self._mocks['efs']
        
        if 'efs' not in self._services:
            from ..services.efs_service import EFSService
            self._services['efs'] = EFSService(
                efs_client=self.client_factory.get_client(AWSServiceType.EFS),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['efs']
    
    def get_elasticache_service(self):
        """
        Obtém instância do ElastiCacheService
        
        Returns:
            ElastiCacheService configurado
        """
        if 'elasticache' in self._mocks:
            return self._mocks['elasticache']
        
        if 'elasticache' not in self._services:
            from ..services.elasticache_service import ElastiCacheService
            self._services['elasticache'] = ElastiCacheService(
                elasticache_client=self.client_factory.get_client(AWSServiceType.ELASTICACHE),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['elasticache']
    
    def get_ecs_service(self):
        """
        Obtém instância do ECSContainerService
        
        Returns:
            ECSContainerService configurado
        """
        if 'ecs' in self._mocks:
            return self._mocks['ecs']
        
        if 'ecs' not in self._services:
            from ..services.ecs_service import ECSContainerService
            self._services['ecs'] = ECSContainerService(
                ecs_client=self.client_factory.get_client(AWSServiceType.ECS),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['ecs']
    
    def get_ec2_finops_service(self):
        """Obtém instância do EC2FinOpsService"""
        if 'ec2_finops' in self._mocks:
            return self._mocks['ec2_finops']
        
        if 'ec2_finops' not in self._services:
            from ..services.ec2_finops_service import EC2FinOpsService
            self._services['ec2_finops'] = EC2FinOpsService(
                ec2_client=self.client_factory.get_client(AWSServiceType.EC2),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['ec2_finops']
    
    def get_lambda_finops_service(self):
        """Obtém instância do LambdaFinOpsService"""
        if 'lambda_finops' in self._mocks:
            return self._mocks['lambda_finops']
        
        if 'lambda_finops' not in self._services:
            from ..services.lambda_finops_service import LambdaFinOpsService
            self._services['lambda_finops'] = LambdaFinOpsService(
                lambda_client=self.client_factory.get_client(AWSServiceType.LAMBDA),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['lambda_finops']
    
    def get_redshift_service(self):
        """Obtém instância do RedshiftService"""
        if 'redshift' in self._mocks:
            return self._mocks['redshift']
        
        if 'redshift' not in self._services:
            from ..services.redshift_service import RedshiftService
            self._services['redshift'] = RedshiftService(
                redshift_client=self.client_factory.get_client(AWSServiceType.REDSHIFT),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['redshift']
    
    def get_cloudfront_service(self):
        """Obtém instância do CloudFrontService"""
        if 'cloudfront' in self._mocks:
            return self._mocks['cloudfront']
        
        if 'cloudfront' not in self._services:
            from ..services.cloudfront_service import CloudFrontService
            self._services['cloudfront'] = CloudFrontService(
                cloudfront_client=self.client_factory.get_client(AWSServiceType.CLOUDFRONT),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['cloudfront']
    
    def get_elb_service(self):
        """Obtém instância do ELBService"""
        if 'elb' in self._mocks:
            return self._mocks['elb']
        
        if 'elb' not in self._services:
            from ..services.elb_service import ELBService
            self._services['elb'] = ELBService(
                elbv2_client=self.client_factory.get_client(AWSServiceType.ELB_V2),
                elb_client=self.client_factory.get_client(AWSServiceType.ELB),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['elb']
    
    def get_emr_service(self):
        """Obtém instância do EMRService"""
        if 'emr' in self._mocks:
            return self._mocks['emr']
        
        if 'emr' not in self._services:
            from ..services.emr_service import EMRService
            self._services['emr'] = EMRService(
                emr_client=self.client_factory.get_client(AWSServiceType.EMR),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['emr']
    
    def get_vpc_network_service(self):
        """Obtém instância do VPCNetworkService"""
        if 'vpc_network' in self._mocks:
            return self._mocks['vpc_network']
        
        if 'vpc_network' not in self._services:
            from ..services.vpc_network_service import VPCNetworkService
            self._services['vpc_network'] = VPCNetworkService(
                ec2_client=self.client_factory.get_client(AWSServiceType.EC2),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['vpc_network']
    
    def get_kinesis_service(self):
        """Obtém instância do KinesisService"""
        if 'kinesis' in self._mocks:
            return self._mocks['kinesis']
        
        if 'kinesis' not in self._services:
            from ..services.kinesis_service import KinesisService
            self._services['kinesis'] = KinesisService(
                kinesis_client=self.client_factory.get_client(AWSServiceType.KINESIS),
                firehose_client=self.client_factory.get_client(AWSServiceType.FIREHOSE),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['kinesis']
    
    def get_glue_service(self):
        """Obtém instância do GlueService"""
        if 'glue' in self._mocks:
            return self._mocks['glue']
        
        if 'glue' not in self._services:
            from ..services.glue_service import GlueService
            self._services['glue'] = GlueService(
                glue_client=self.client_factory.get_client(AWSServiceType.GLUE),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['glue']
    
    def get_sagemaker_service(self):
        """Obtém instância do SageMakerService"""
        if 'sagemaker' in self._mocks:
            return self._mocks['sagemaker']
        
        if 'sagemaker' not in self._services:
            from ..services.sagemaker_service import SageMakerService
            self._services['sagemaker'] = SageMakerService(
                sagemaker_client=self.client_factory.get_client(AWSServiceType.SAGEMAKER),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['sagemaker']
    
    def get_route53_service(self):
        """Obtém instância do Route53Service"""
        if 'route53' in self._mocks:
            return self._mocks['route53']
        
        if 'route53' not in self._services:
            from ..services.route53_service import Route53Service
            self._services['route53'] = Route53Service(
                route53_client=self.client_factory.get_client(AWSServiceType.ROUTE53),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['route53']
    
    def get_backup_service(self):
        """Obtém instância do BackupService"""
        if 'backup' in self._mocks:
            return self._mocks['backup']
        
        if 'backup' not in self._services:
            from ..services.backup_service import BackupService
            self._services['backup'] = BackupService(
                backup_client=self.client_factory.get_client(AWSServiceType.BACKUP),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['backup']
    
    def get_sns_sqs_service(self):
        """Obtém instância do SNSSQSService"""
        if 'sns_sqs' in self._mocks:
            return self._mocks['sns_sqs']
        
        if 'sns_sqs' not in self._services:
            from ..services.sns_sqs_service import SNSSQSService
            self._services['sns_sqs'] = SNSSQSService(
                sns_client=self.client_factory.get_client(AWSServiceType.SNS),
                sqs_client=self.client_factory.get_client(AWSServiceType.SQS),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['sns_sqs']
    
    def get_secrets_manager_service(self):
        """Obtém instância do SecretsManagerService"""
        if 'secrets_manager' in self._mocks:
            return self._mocks['secrets_manager']
        
        if 'secrets_manager' not in self._services:
            from ..services.secrets_manager_service import SecretsManagerService
            self._services['secrets_manager'] = SecretsManagerService(
                secretsmanager_client=self.client_factory.get_client(AWSServiceType.SECRETS_MANAGER),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['secrets_manager']
    
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
            'dynamodb': self.get_dynamodb_service(),
            'efs': self.get_efs_service(),
            'elasticache': self.get_elasticache_service(),
            'ecs': self.get_ecs_service(),
            'ec2_finops': self.get_ec2_finops_service(),
            'lambda_finops': self.get_lambda_finops_service(),
            'redshift': self.get_redshift_service(),
            'cloudfront': self.get_cloudfront_service(),
            'elb': self.get_elb_service(),
            'emr': self.get_emr_service(),
            'vpc_network': self.get_vpc_network_service(),
            'kinesis': self.get_kinesis_service(),
            'glue': self.get_glue_service(),
            'sagemaker': self.get_sagemaker_service(),
            'route53': self.get_route53_service(),
            'backup': self.get_backup_service(),
            'sns_sqs': self.get_sns_sqs_service(),
            'secrets_manager': self.get_secrets_manager_service()
        }
    
    def clear_cache(self):
        """Limpa cache de serviços"""
        self._services.clear()
        logger.info("Service cache cleared")
