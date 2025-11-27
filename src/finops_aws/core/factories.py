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
    MSK = "kafka"
    EKS = "eks"
    OPENSEARCH = "opensearch"
    WORKSPACES = "workspaces"
    FSX = "fsx"
    DOCUMENTDB = "docdb"
    NEPTUNE = "neptune"
    TIMESTREAM_WRITE = "timestream-write"
    TIMESTREAM_QUERY = "timestream-query"
    BATCH = "batch"
    STEPFUNCTIONS = "stepfunctions"
    APIGATEWAY = "apigateway"
    APIGATEWAYV2 = "apigatewayv2"
    TRANSFER = "transfer"
    LOGS = "logs"
    WAFV2 = "wafv2"
    COGNITO_IDP = "cognito-idp"
    COGNITO_IDENTITY = "cognito-identity"
    EVENTS = "events"
    PIPES = "pipes"
    SCHEMAS = "schemas"
    CODEBUILD = "codebuild"
    CODEPIPELINE = "codepipeline"
    CODEDEPLOY = "codedeploy"
    CODECOMMIT = "codecommit"
    GUARDDUTY = "guardduty"
    INSPECTOR2 = "inspector2"
    CONFIG = "config"
    CLOUDTRAIL = "cloudtrail"
    ACM = "acm"
    BEDROCK = "bedrock"
    BEDROCK_RUNTIME = "bedrock-runtime"
    COMPREHEND = "comprehend"
    REKOGNITION = "rekognition"
    TEXTRACT = "textract"
    ATHENA = "athena"
    QUICKSIGHT = "quicksight"
    DATASYNC = "datasync"
    LAKEFORMATION = "lakeformation"
    GLOBALACCELERATOR = "globalaccelerator"
    DIRECTCONNECT = "directconnect"
    TRANSITGATEWAY = "transitgateway"
    ECR = "ecr"
    APPRUNNER = "apprunner"
    ELASTICBEANSTALK = "elasticbeanstalk"
    LIGHTSAIL = "lightsail"
    IOT = "iot"
    IOTANALYTICS = "iotanalytics"
    GREENGRASSV2 = "greengrassv2"
    IOTEVENTS = "iotevents"
    MEDIACONVERT = "mediaconvert"
    MEDIALIVE = "medialive"
    MEDIAPACKAGE = "mediapackage"
    IVS = "ivs"
    DMS = "dms"
    MGN = "mgn"
    SNOWBALL = "snowball"
    DATAPIPELINE = "datapipeline"
    APPSTREAM = "appstream"
    WORKDOCS = "workdocs"
    CHIME = "chime"
    GAMELIFT = "gamelift"
    ROBOMAKER = "robomaker"
    QLDB = "qldb"
    MANAGEDBLOCKCHAIN = "managedblockchain"
    BRAKET = "braket"
    XRAY = "xray"
    CLOUDFORMATION = "cloudformation"
    SSM = "ssm"
    APPCONFIG = "appconfig"
    SECURITYHUB = "securityhub"
    MACIE = "macie2"
    TRUSTEDADVISOR = "support"
    ORGANIZATIONS = "organizations"
    CONTROLTOWER = "controltower"
    PINPOINT = "pinpoint"
    SES = "ses"
    CONNECT = "connect"
    SERVICECATALOG = "servicecatalog"
    APPFLOW = "appflow"
    MQ = "mq"
    KINESISVIDEO = "kinesisvideo"
    MEDIASTORE = "mediastore"
    ELASTICINFERENCE = "elastic-inference"
    FORECAST = "forecast"
    LOOKOUTMETRICS = "lookoutmetrics"
    LOOKOUTVISION = "lookoutvision"
    MEMORYDB = "memorydb"
    KEYSPACES = "keyspaces"
    STORAGEGATEWAY = "storagegateway"
    DATAEXCHANGE = "dataexchange"
    CODESTAR = "codestar"
    CLOUD9 = "cloud9"
    SERVERLESSREPO = "serverlessrepo"
    PROTON = "proton"
    LEX = "lex"
    POLLY = "polly"
    TRANSCRIBE = "transcribe"
    PERSONALIZE = "personalize"
    FINSPACE = "finspace"
    MARKETPLACECATALOG = "marketplace-catalog"
    AUTOGLUON = "autogluon"
    BACKUPRESTORE = "backuprestore"
    CASSANDRA = "cassandra"
    CODECOMMIT_ENHANCED = "codecommit"
    DATAPORTAL = "dataportal"
    DATASYNC_ENHANCED = "datasync"
    DISTRO = "distro"
    DYNAMODB_STREAMS = "dynamodb-streams"
    GLUESTREAMING = "glue-streaming"
    LOOKOUTEQUIPMENT = "lookoutequipment"
    S3OUTPOSTS = "s3outposts"
    SNOW = "snow"


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
    
    def get_msk_service(self):
        """Obtém instância do MSKService"""
        if 'msk' in self._mocks:
            return self._mocks['msk']
        
        if 'msk' not in self._services:
            from ..services.msk_service import MSKService
            self._services['msk'] = MSKService(
                msk_client=self.client_factory.get_client(AWSServiceType.MSK),
                cloudwatch_client=self.client_factory.get_client(AWSServiceType.CLOUDWATCH),
                cost_client=self.client_factory.get_client(AWSServiceType.COST_EXPLORER)
            )
        
        return self._services['msk']
    
    def get_eks_service(self):
        """Obtém instância do EKSService"""
        if 'eks' in self._mocks:
            return self._mocks['eks']
        
        if 'eks' not in self._services:
            from ..services.eks_service import EKSService
            self._services['eks'] = EKSService(self.client_factory)
        
        return self._services['eks']
    
    def get_aurora_service(self):
        """Obtém instância do AuroraService"""
        if 'aurora' in self._mocks:
            return self._mocks['aurora']
        
        if 'aurora' not in self._services:
            from ..services.aurora_service import AuroraService
            self._services['aurora'] = AuroraService(self.client_factory)
        
        return self._services['aurora']
    
    def get_opensearch_service(self):
        """Obtém instância do OpenSearchService"""
        if 'opensearch' in self._mocks:
            return self._mocks['opensearch']
        
        if 'opensearch' not in self._services:
            from ..services.opensearch_service import OpenSearchService
            self._services['opensearch'] = OpenSearchService(self.client_factory)
        
        return self._services['opensearch']
    
    def get_workspaces_service(self):
        """Obtém instância do WorkSpacesService"""
        if 'workspaces' in self._mocks:
            return self._mocks['workspaces']
        
        if 'workspaces' not in self._services:
            from ..services.workspaces_service import WorkSpacesService
            self._services['workspaces'] = WorkSpacesService(self.client_factory)
        
        return self._services['workspaces']
    
    def get_fsx_service(self):
        """Obtém instância do FSxService"""
        if 'fsx' in self._mocks:
            return self._mocks['fsx']
        
        if 'fsx' not in self._services:
            from ..services.fsx_service import FSxService
            self._services['fsx'] = FSxService(self.client_factory)
        
        return self._services['fsx']
    
    def get_documentdb_service(self):
        """Obtém instância do DocumentDBService"""
        if 'documentdb' in self._mocks:
            return self._mocks['documentdb']
        
        if 'documentdb' not in self._services:
            from ..services.documentdb_service import DocumentDBService
            self._services['documentdb'] = DocumentDBService(self.client_factory)
        
        return self._services['documentdb']
    
    def get_neptune_service(self):
        """Obtém instância do NeptuneService"""
        if 'neptune' in self._mocks:
            return self._mocks['neptune']
        
        if 'neptune' not in self._services:
            from ..services.neptune_service import NeptuneService
            self._services['neptune'] = NeptuneService(self.client_factory)
        
        return self._services['neptune']
    
    def get_timestream_service(self):
        """Obtém instância do TimestreamService"""
        if 'timestream' in self._mocks:
            return self._mocks['timestream']
        
        if 'timestream' not in self._services:
            from ..services.timestream_service import TimestreamService
            self._services['timestream'] = TimestreamService(self.client_factory)
        
        return self._services['timestream']
    
    def get_batch_service(self):
        """Obtém instância do BatchService"""
        if 'batch' in self._mocks:
            return self._mocks['batch']
        
        if 'batch' not in self._services:
            from ..services.batch_service import BatchService
            self._services['batch'] = BatchService(self.client_factory)
        
        return self._services['batch']
    
    def get_stepfunctions_service(self):
        """Obtém instância do StepFunctionsService"""
        if 'stepfunctions' in self._mocks:
            return self._mocks['stepfunctions']
        
        if 'stepfunctions' not in self._services:
            from ..services.stepfunctions_service import StepFunctionsService
            self._services['stepfunctions'] = StepFunctionsService(self.client_factory)
        
        return self._services['stepfunctions']
    
    def get_apigateway_service(self):
        """Obtém instância do APIGatewayService"""
        if 'apigateway' in self._mocks:
            return self._mocks['apigateway']
        
        if 'apigateway' not in self._services:
            from ..services.apigateway_service import APIGatewayService
            self._services['apigateway'] = APIGatewayService(self.client_factory)
        
        return self._services['apigateway']
    
    def get_transfer_service(self):
        """Obtém instância do TransferFamilyService"""
        if 'transfer' in self._mocks:
            return self._mocks['transfer']
        
        if 'transfer' not in self._services:
            from ..services.transfer_service import TransferFamilyService
            self._services['transfer'] = TransferFamilyService(self.client_factory)
        
        return self._services['transfer']
    
    def get_cloudwatch_logs_service(self):
        """Obtém instância do CloudWatchService"""
        if 'cloudwatch_logs' in self._mocks:
            return self._mocks['cloudwatch_logs']
        
        if 'cloudwatch_logs' not in self._services:
            from ..services.cloudwatch_service import CloudWatchService
            self._services['cloudwatch_logs'] = CloudWatchService(self.client_factory)
        
        return self._services['cloudwatch_logs']
    
    def get_waf_service(self):
        """Obtém instância do WAFService"""
        if 'waf' in self._mocks:
            return self._mocks['waf']
        
        if 'waf' not in self._services:
            from ..services.waf_service import WAFService
            self._services['waf'] = WAFService(self.client_factory)
        
        return self._services['waf']
    
    def get_cognito_service(self):
        """Obtém instância do CognitoService"""
        if 'cognito' in self._mocks:
            return self._mocks['cognito']
        
        if 'cognito' not in self._services:
            from ..services.cognito_service import CognitoService
            self._services['cognito'] = CognitoService(self.client_factory)
        
        return self._services['cognito']
    
    def get_eventbridge_service(self):
        """Obtém instância do EventBridgeService"""
        if 'eventbridge' in self._mocks:
            return self._mocks['eventbridge']
        
        if 'eventbridge' not in self._services:
            from ..services.eventbridge_service import EventBridgeService
            self._services['eventbridge'] = EventBridgeService(self.client_factory)
        
        return self._services['eventbridge']
    
    def get_codebuild_service(self):
        """Obtém instância do CodeBuildService"""
        if 'codebuild' in self._mocks:
            return self._mocks['codebuild']
        
        if 'codebuild' not in self._services:
            from ..services.codebuild_service import CodeBuildService
            self._services['codebuild'] = CodeBuildService(self.client_factory)
        
        return self._services['codebuild']
    
    def get_codepipeline_service(self):
        """Obtém instância do CodePipelineService"""
        if 'codepipeline' in self._mocks:
            return self._mocks['codepipeline']
        
        if 'codepipeline' not in self._services:
            from ..services.codepipeline_service import CodePipelineService
            self._services['codepipeline'] = CodePipelineService(self.client_factory)
        
        return self._services['codepipeline']
    
    def get_codedeploy_service(self):
        """Obtém instância do CodeDeployService"""
        if 'codedeploy' in self._mocks:
            return self._mocks['codedeploy']
        
        if 'codedeploy' not in self._services:
            from ..services.codedeploy_service import CodeDeployService
            self._services['codedeploy'] = CodeDeployService(self.client_factory)
        
        return self._services['codedeploy']
    
    def get_codecommit_service(self):
        """Obtém instância do CodeCommitService"""
        if 'codecommit' in self._mocks:
            return self._mocks['codecommit']
        
        if 'codecommit' not in self._services:
            from ..services.codecommit_service import CodeCommitService
            self._services['codecommit'] = CodeCommitService(self.client_factory)
        
        return self._services['codecommit']
    
    def get_guardduty_service(self):
        """Obtém instância do GuardDutyService"""
        if 'guardduty' in self._mocks:
            return self._mocks['guardduty']
        
        if 'guardduty' not in self._services:
            from ..services.guardduty_service import GuardDutyService
            self._services['guardduty'] = GuardDutyService(self.client_factory)
        
        return self._services['guardduty']
    
    def get_inspector_service(self):
        """Obtém instância do InspectorService"""
        if 'inspector' in self._mocks:
            return self._mocks['inspector']
        
        if 'inspector' not in self._services:
            from ..services.inspector_service import InspectorService
            self._services['inspector'] = InspectorService(self.client_factory)
        
        return self._services['inspector']
    
    def get_config_service(self):
        """Obtém instância do ConfigService"""
        if 'config' in self._mocks:
            return self._mocks['config']
        
        if 'config' not in self._services:
            from ..services.config_service import ConfigService
            self._services['config'] = ConfigService(self.client_factory)
        
        return self._services['config']
    
    def get_cloudtrail_service(self):
        """Obtém instância do CloudTrailService"""
        if 'cloudtrail' in self._mocks:
            return self._mocks['cloudtrail']
        
        if 'cloudtrail' not in self._services:
            from ..services.cloudtrail_service import CloudTrailService
            self._services['cloudtrail'] = CloudTrailService(self.client_factory)
        
        return self._services['cloudtrail']
    
    def get_kms_service(self):
        """Obtém instância do KMSService"""
        if 'kms' in self._mocks:
            return self._mocks['kms']
        
        if 'kms' not in self._services:
            from ..services.kms_service import KMSService
            self._services['kms'] = KMSService(self.client_factory)
        
        return self._services['kms']
    
    def get_acm_service(self):
        """Obtém instância do ACMService"""
        if 'acm' in self._mocks:
            return self._mocks['acm']
        
        if 'acm' not in self._services:
            from ..services.acm_service import ACMService
            self._services['acm'] = ACMService(self.client_factory)
        
        return self._services['acm']
    
    def get_bedrock_service(self):
        """Obtém instância do BedrockService"""
        if 'bedrock' in self._mocks:
            return self._mocks['bedrock']
        
        if 'bedrock' not in self._services:
            from ..services.bedrock_service import BedrockService
            self._services['bedrock'] = BedrockService(self.client_factory)
        
        return self._services['bedrock']
    
    def get_comprehend_service(self):
        """Obtém instância do ComprehendService"""
        if 'comprehend' in self._mocks:
            return self._mocks['comprehend']
        
        if 'comprehend' not in self._services:
            from ..services.comprehend_service import ComprehendService
            self._services['comprehend'] = ComprehendService(self.client_factory)
        
        return self._services['comprehend']
    
    def get_rekognition_service(self):
        """Obtém instância do RekognitionService"""
        if 'rekognition' in self._mocks:
            return self._mocks['rekognition']
        
        if 'rekognition' not in self._services:
            from ..services.rekognition_service import RekognitionService
            self._services['rekognition'] = RekognitionService(self.client_factory)
        
        return self._services['rekognition']
    
    def get_textract_service(self):
        """Obtém instância do TextractService"""
        if 'textract' in self._mocks:
            return self._mocks['textract']
        
        if 'textract' not in self._services:
            from ..services.textract_service import TextractService
            self._services['textract'] = TextractService(self.client_factory)
        
        return self._services['textract']
    
    def get_athena_service(self):
        """Obtém instância do AthenaService"""
        if 'athena' in self._mocks:
            return self._mocks['athena']
        
        if 'athena' not in self._services:
            from ..services.athena_service import AthenaService
            self._services['athena'] = AthenaService(self.client_factory)
        
        return self._services['athena']
    
    def get_quicksight_service(self):
        """Obtém instância do QuickSightService"""
        if 'quicksight' in self._mocks:
            return self._mocks['quicksight']
        
        if 'quicksight' not in self._services:
            from ..services.quicksight_service import QuickSightService
            self._services['quicksight'] = QuickSightService(self.client_factory)
        
        return self._services['quicksight']
    
    def get_datasync_service(self):
        """Obtém instância do DataSyncService"""
        if 'datasync' in self._mocks:
            return self._mocks['datasync']
        
        if 'datasync' not in self._services:
            from ..services.datasync_service import DataSyncService
            self._services['datasync'] = DataSyncService(self.client_factory)
        
        return self._services['datasync']
    
    def get_lakeformation_service(self):
        """Obtém instância do LakeFormationService"""
        if 'lakeformation' in self._mocks:
            return self._mocks['lakeformation']
        
        if 'lakeformation' not in self._services:
            from ..services.lakeformation_service import LakeFormationService
            self._services['lakeformation'] = LakeFormationService(self.client_factory)
        
        return self._services['lakeformation']
    
    def get_globalaccelerator_service(self):
        """Obtém instância do GlobalAcceleratorService"""
        if 'globalaccelerator' in self._mocks:
            return self._mocks['globalaccelerator']
        
        if 'globalaccelerator' not in self._services:
            from ..services.globalaccelerator_service import GlobalAcceleratorService
            self._services['globalaccelerator'] = GlobalAcceleratorService(self.client_factory)
        
        return self._services['globalaccelerator']
    
    def get_directconnect_service(self):
        """Obtém instância do DirectConnectService"""
        if 'directconnect' in self._mocks:
            return self._mocks['directconnect']
        
        if 'directconnect' not in self._services:
            from ..services.directconnect_service import DirectConnectService
            self._services['directconnect'] = DirectConnectService(self.client_factory)
        
        return self._services['directconnect']
    
    def get_transitgateway_service(self):
        """Obtém instância do TransitGatewayService"""
        if 'transitgateway' in self._mocks:
            return self._mocks['transitgateway']
        
        if 'transitgateway' not in self._services:
            from ..services.transitgateway_service import TransitGatewayService
            self._services['transitgateway'] = TransitGatewayService(self.client_factory)
        
        return self._services['transitgateway']
    
    def get_ecr_service(self):
        """Obtém instância do ECRService"""
        if 'ecr' in self._mocks:
            return self._mocks['ecr']
        
        if 'ecr' not in self._services:
            from ..services.ecr_service import ECRService
            self._services['ecr'] = ECRService(self.client_factory)
        
        return self._services['ecr']
    
    def get_apprunner_service(self):
        """Obtém instância do AppRunnerServiceManager"""
        if 'apprunner' in self._mocks:
            return self._mocks['apprunner']
        
        if 'apprunner' not in self._services:
            from ..services.apprunner_service import AppRunnerServiceManager
            self._services['apprunner'] = AppRunnerServiceManager(self.client_factory)
        
        return self._services['apprunner']
    
    def get_elasticbeanstalk_service(self):
        """Obtém instância do ElasticBeanstalkService"""
        if 'elasticbeanstalk' in self._mocks:
            return self._mocks['elasticbeanstalk']
        
        if 'elasticbeanstalk' not in self._services:
            from ..services.elasticbeanstalk_service import ElasticBeanstalkService
            self._services['elasticbeanstalk'] = ElasticBeanstalkService(self.client_factory)
        
        return self._services['elasticbeanstalk']
    
    def get_lightsail_service(self):
        """Obtém instância do LightsailService"""
        if 'lightsail' in self._mocks:
            return self._mocks['lightsail']
        
        if 'lightsail' not in self._services:
            from ..services.lightsail_service import LightsailService
            self._services['lightsail'] = LightsailService(self.client_factory)
        
        return self._services['lightsail']
    
    def get_iot_service(self):
        """Obtém instância do IoTCoreService"""
        if 'iot' in self._mocks:
            return self._mocks['iot']
        
        if 'iot' not in self._services:
            from ..services.iot_service import IoTCoreService
            self._services['iot'] = IoTCoreService(self.client_factory)
        
        return self._services['iot']
    
    def get_iotanalytics_service(self):
        """Obtém instância do IoTAnalyticsService"""
        if 'iotanalytics' in self._mocks:
            return self._mocks['iotanalytics']
        
        if 'iotanalytics' not in self._services:
            from ..services.iotanalytics_service import IoTAnalyticsService
            self._services['iotanalytics'] = IoTAnalyticsService(self.client_factory)
        
        return self._services['iotanalytics']
    
    def get_greengrass_service(self):
        """Obtém instância do GreengrassService"""
        if 'greengrass' in self._mocks:
            return self._mocks['greengrass']
        
        if 'greengrass' not in self._services:
            from ..services.greengrass_service import GreengrassService
            self._services['greengrass'] = GreengrassService(self.client_factory)
        
        return self._services['greengrass']
    
    def get_iotevents_service(self):
        """Obtém instância do IoTEventsService"""
        if 'iotevents' in self._mocks:
            return self._mocks['iotevents']
        
        if 'iotevents' not in self._services:
            from ..services.iotevents_service import IoTEventsService
            self._services['iotevents'] = IoTEventsService(self.client_factory)
        
        return self._services['iotevents']
    
    def get_mediaconvert_service(self):
        """Obtém instância do MediaConvertService"""
        if 'mediaconvert' in self._mocks:
            return self._mocks['mediaconvert']
        
        if 'mediaconvert' not in self._services:
            from ..services.mediaconvert_service import MediaConvertService
            self._services['mediaconvert'] = MediaConvertService(self.client_factory)
        
        return self._services['mediaconvert']
    
    def get_medialive_service(self):
        """Obtém instância do MediaLiveService"""
        if 'medialive' in self._mocks:
            return self._mocks['medialive']
        
        if 'medialive' not in self._services:
            from ..services.medialive_service import MediaLiveService
            self._services['medialive'] = MediaLiveService(self.client_factory)
        
        return self._services['medialive']
    
    def get_mediapackage_service(self):
        """Obtém instância do MediaPackageService"""
        if 'mediapackage' in self._mocks:
            return self._mocks['mediapackage']
        
        if 'mediapackage' not in self._services:
            from ..services.mediapackage_service import MediaPackageService
            self._services['mediapackage'] = MediaPackageService(self.client_factory)
        
        return self._services['mediapackage']
    
    def get_ivs_service(self):
        """Obtém instância do IVSService"""
        if 'ivs' in self._mocks:
            return self._mocks['ivs']
        
        if 'ivs' not in self._services:
            from ..services.ivs_service import IVSService
            self._services['ivs'] = IVSService(self.client_factory)
        
        return self._services['ivs']
    
    def get_dms_service(self):
        """Obtém instância do DMSService"""
        if 'dms' in self._mocks:
            return self._mocks['dms']
        
        if 'dms' not in self._services:
            from ..services.dms_service import DMSService
            self._services['dms'] = DMSService(self.client_factory)
        
        return self._services['dms']
    
    def get_mgn_service(self):
        """Obtém instância do MGNService"""
        if 'mgn' in self._mocks:
            return self._mocks['mgn']
        
        if 'mgn' not in self._services:
            from ..services.mgn_service import MGNService
            self._services['mgn'] = MGNService(self.client_factory)
        
        return self._services['mgn']
    
    def get_snowfamily_service(self):
        """Obtém instância do SnowFamilyService"""
        if 'snowfamily' in self._mocks:
            return self._mocks['snowfamily']
        
        if 'snowfamily' not in self._services:
            from ..services.snowfamily_service import SnowFamilyService
            self._services['snowfamily'] = SnowFamilyService(self.client_factory)
        
        return self._services['snowfamily']
    
    def get_datapipeline_service(self):
        """Obtém instância do DataPipelineService"""
        if 'datapipeline' in self._mocks:
            return self._mocks['datapipeline']
        
        if 'datapipeline' not in self._services:
            from ..services.datapipeline_service import DataPipelineService
            self._services['datapipeline'] = DataPipelineService(self.client_factory)
        
        return self._services['datapipeline']
    
    def get_appstream_service(self):
        """Obtém instância do AppStreamService"""
        if 'appstream' in self._mocks:
            return self._mocks['appstream']
        
        if 'appstream' not in self._services:
            from ..services.appstream_service import AppStreamService
            self._services['appstream'] = AppStreamService(self.client_factory)
        
        return self._services['appstream']
    
    def get_workdocs_service(self):
        """Obtém instância do WorkDocsService"""
        if 'workdocs' in self._mocks:
            return self._mocks['workdocs']
        
        if 'workdocs' not in self._services:
            from ..services.workdocs_service import WorkDocsService
            self._services['workdocs'] = WorkDocsService(self.client_factory)
        
        return self._services['workdocs']
    
    def get_chime_service(self):
        """Obtém instância do ChimeService"""
        if 'chime' in self._mocks:
            return self._mocks['chime']
        
        if 'chime' not in self._services:
            from ..services.chime_service import ChimeService
            self._services['chime'] = ChimeService(self.client_factory)
        
        return self._services['chime']
    
    def get_gamelift_service(self):
        """Obtém instância do GameLiftService"""
        if 'gamelift' in self._mocks:
            return self._mocks['gamelift']
        
        if 'gamelift' not in self._services:
            from ..services.gamelift_service import GameLiftService
            self._services['gamelift'] = GameLiftService(self.client_factory)
        
        return self._services['gamelift']
    
    def get_robomaker_service(self):
        """Obtém instância do RoboMakerService"""
        if 'robomaker' in self._mocks:
            return self._mocks['robomaker']
        
        if 'robomaker' not in self._services:
            from ..services.robomaker_service import RoboMakerService
            self._services['robomaker'] = RoboMakerService(self.client_factory)
        
        return self._services['robomaker']
    
    def get_qldb_service(self):
        """Obtém instância do QLDBService"""
        if 'qldb' in self._mocks:
            return self._mocks['qldb']
        
        if 'qldb' not in self._services:
            from ..services.qldb_service import QLDBService
            self._services['qldb'] = QLDBService(self.client_factory)
        
        return self._services['qldb']
    
    def get_managedblockchain_service(self):
        """Obtém instância do ManagedBlockchainService"""
        if 'managedblockchain' in self._mocks:
            return self._mocks['managedblockchain']
        
        if 'managedblockchain' not in self._services:
            from ..services.managedblockchain_service import ManagedBlockchainService
            self._services['managedblockchain'] = ManagedBlockchainService(self.client_factory)
        
        return self._services['managedblockchain']
    
    def get_braket_service(self):
        """Obtém instância do BraketService"""
        if 'braket' in self._mocks:
            return self._mocks['braket']
        
        if 'braket' not in self._services:
            from ..services.braket_service import BraketService
            self._services['braket'] = BraketService(self.client_factory)
        
        return self._services['braket']
    
    def get_xray_service(self):
        """Obtém instância do XRayService"""
        if 'xray' in self._mocks:
            return self._mocks['xray']
        
        if 'xray' not in self._services:
            from ..services.xray_service import XRayService
            self._services['xray'] = XRayService(self.client_factory)
        
        return self._services['xray']
    
    def get_cloudformation_service(self):
        """Obtém instância do CloudFormationService"""
        if 'cloudformation' in self._mocks:
            return self._mocks['cloudformation']
        
        if 'cloudformation' not in self._services:
            from ..services.cloudformation_service import CloudFormationService
            self._services['cloudformation'] = CloudFormationService(self.client_factory)
        
        return self._services['cloudformation']
    
    def get_ssm_service(self):
        """Obtém instância do SSMService"""
        if 'ssm' in self._mocks:
            return self._mocks['ssm']
        
        if 'ssm' not in self._services:
            from ..services.ssm_service import SSMService
            self._services['ssm'] = SSMService(self.client_factory)
        
        return self._services['ssm']
    
    def get_appconfig_service(self):
        """Obtém instância do AppConfigService"""
        if 'appconfig' in self._mocks:
            return self._mocks['appconfig']
        
        if 'appconfig' not in self._services:
            from ..services.appconfig_service import AppConfigService
            self._services['appconfig'] = AppConfigService(self.client_factory)
        
        return self._services['appconfig']
    
    def get_sqs_service(self):
        """Obtém instância do SQSService"""
        if 'sqs' in self._mocks:
            return self._mocks['sqs']
        
        if 'sqs' not in self._services:
            from ..services.sqs_service import SQSService
            self._services['sqs'] = SQSService(self.client_factory)
        
        return self._services['sqs']
    
    def get_iam_service(self):
        """Obtém instância do IAMService"""
        if 'iam' in self._mocks:
            return self._mocks['iam']
        
        if 'iam' not in self._services:
            from ..services.iam_service import IAMService
            self._services['iam'] = IAMService(self.client_factory)
        
        return self._services['iam']
    
    def get_securityhub_service(self):
        """Obtém instância do SecurityHubService"""
        if 'securityhub' in self._mocks:
            return self._mocks['securityhub']
        
        if 'securityhub' not in self._services:
            from ..services.securityhub_service import SecurityHubService
            self._services['securityhub'] = SecurityHubService(self.client_factory)
        
        return self._services['securityhub']
    
    def get_macie_service(self):
        """Obtém instância do MacieService"""
        if 'macie' in self._mocks:
            return self._mocks['macie']
        
        if 'macie' not in self._services:
            from ..services.macie_service import MacieService
            self._services['macie'] = MacieService(self.client_factory)
        
        return self._services['macie']
    
    def get_trustedadvisor_service(self):
        """Obtém instância do TrustedAdvisorService"""
        if 'trustedadvisor' in self._mocks:
            return self._mocks['trustedadvisor']
        
        if 'trustedadvisor' not in self._services:
            from ..services.trustedadvisor_service import TrustedAdvisorService
            self._services['trustedadvisor'] = TrustedAdvisorService(self.client_factory)
        
        return self._services['trustedadvisor']
    
    def get_organizations_service(self):
        """Obtém instância do OrganizationsService"""
        if 'organizations' in self._mocks:
            return self._mocks['organizations']
        
        if 'organizations' not in self._services:
            from ..services.organizations_service import OrganizationsService
            self._services['organizations'] = OrganizationsService(self.client_factory)
        
        return self._services['organizations']
    
    def get_controltower_service(self):
        """Obtém instância do ControlTowerService"""
        if 'controltower' in self._mocks:
            return self._mocks['controltower']
        
        if 'controltower' not in self._services:
            from ..services.controltower_service import ControlTowerService
            self._services['controltower'] = ControlTowerService(self.client_factory)
        
        return self._services['controltower']
    
    def get_pinpoint_service(self):
        """Obtém instância do PinpointService"""
        if 'pinpoint' in self._mocks:
            return self._mocks['pinpoint']
        if 'pinpoint' not in self._services:
            from ..services.pinpoint_service import PinpointService
            self._services['pinpoint'] = PinpointService(self.client_factory)
        return self._services['pinpoint']
    
    def get_ses_service(self):
        """Obtém instância do SESService"""
        if 'ses' in self._mocks:
            return self._mocks['ses']
        if 'ses' not in self._services:
            from ..services.ses_service import SesService
            self._services['ses'] = SesService(self.client_factory)
        return self._services['ses']
    
    def get_connect_service(self):
        """Obtém instância do ConnectService"""
        if 'connect' in self._mocks:
            return self._mocks['connect']
        if 'connect' not in self._services:
            from ..services.connect_service import ConnectService
            self._services['connect'] = ConnectService(self.client_factory)
        return self._services['connect']
    
    def get_servicecatalog_service(self):
        """Obtém instância do ServiceCatalogService"""
        if 'servicecatalog' in self._mocks:
            return self._mocks['servicecatalog']
        if 'servicecatalog' not in self._services:
            from ..services.servicecatalog_service import ServicecatalogService
            self._services['servicecatalog'] = ServicecatalogService(self.client_factory)
        return self._services['servicecatalog']
    
    def get_appflow_service(self):
        """Obtém instância do AppFlowService"""
        if 'appflow' in self._mocks:
            return self._mocks['appflow']
        if 'appflow' not in self._services:
            from ..services.appflow_service import AppflowService
            self._services['appflow'] = AppflowService(self.client_factory)
        return self._services['appflow']
    
    def get_mq_service(self):
        """Obtém instância do MQService"""
        if 'mq' in self._mocks:
            return self._mocks['mq']
        if 'mq' not in self._services:
            from ..services.mq_service import MqService
            self._services['mq'] = MqService(self.client_factory)
        return self._services['mq']
    
    def get_kinesisvideo_service(self):
        """Obtém instância do KinesisVideoService"""
        if 'kinesisvideo' in self._mocks:
            return self._mocks['kinesisvideo']
        if 'kinesisvideo' not in self._services:
            from ..services.kinesisvideo_service import KinesisvideoService
            self._services['kinesisvideo'] = KinesisvideoService(self.client_factory)
        return self._services['kinesisvideo']
    
    def get_mediastore_service(self):
        """Obtém instância do MediaStoreService"""
        if 'mediastore' in self._mocks:
            return self._mocks['mediastore']
        if 'mediastore' not in self._services:
            from ..services.mediastore_service import MediastoreService
            self._services['mediastore'] = MediastoreService(self.client_factory)
        return self._services['mediastore']
    
    def get_forecast_service(self):
        """Obtém instância do ForecastService"""
        if 'forecast' in self._mocks:
            return self._mocks['forecast']
        if 'forecast' not in self._services:
            from ..services.forecast_service import ForecastService
            self._services['forecast'] = ForecastService(self.client_factory)
        return self._services['forecast']
    
    def get_memorydb_service(self):
        """Obtém instância do MemoryDBService"""
        if 'memorydb' in self._mocks:
            return self._mocks['memorydb']
        if 'memorydb' not in self._services:
            from ..services.memorydb_service import MemorydbService
            self._services['memorydb'] = MemorydbService(self.client_factory)
        return self._services['memorydb']
    
    def get_keyspaces_service(self):
        """Obtém instância do KeyspacesService"""
        if 'keyspaces' in self._mocks:
            return self._mocks['keyspaces']
        if 'keyspaces' not in self._services:
            from ..services.keyspaces_service import KeyspacesService
            self._services['keyspaces'] = KeyspacesService(self.client_factory)
        return self._services['keyspaces']
    
    def get_storagegateway_service(self):
        """Obtém instância do StorageGatewayService"""
        if 'storagegateway' in self._mocks:
            return self._mocks['storagegateway']
        if 'storagegateway' not in self._services:
            from ..services.storagegateway_service import StoragegatewayService
            self._services['storagegateway'] = StoragegatewayService(self.client_factory)
        return self._services['storagegateway']
    
    def get_dataexchange_service(self):
        """Obtém instância do DataExchangeService"""
        if 'dataexchange' in self._mocks:
            return self._mocks['dataexchange']
        if 'dataexchange' not in self._services:
            from ..services.dataexchange_service import DataexchangeService
            self._services['dataexchange'] = DataexchangeService(self.client_factory)
        return self._services['dataexchange']
    
    def get_codestar_service(self):
        """Obtém instância do CodeStarService"""
        if 'codestar' in self._mocks:
            return self._mocks['codestar']
        if 'codestar' not in self._services:
            from ..services.codestar_service import CodestarService
            self._services['codestar'] = CodestarService(self.client_factory)
        return self._services['codestar']
    
    def get_cloud9_service(self):
        """Obtém instância do Cloud9Service"""
        if 'cloud9' in self._mocks:
            return self._mocks['cloud9']
        if 'cloud9' not in self._services:
            from ..services.cloud9_service import Cloud9Service
            self._services['cloud9'] = Cloud9Service(self.client_factory)
        return self._services['cloud9']
    
    def get_serverlessrepo_service(self):
        """Obtém instância do ServerlessRepoService"""
        if 'serverlessrepo' in self._mocks:
            return self._mocks['serverlessrepo']
        if 'serverlessrepo' not in self._services:
            from ..services.serverlessrepo_service import ServerlessrepoService
            self._services['serverlessrepo'] = ServerlessrepoService(self.client_factory)
        return self._services['serverlessrepo']
    
    def get_proton_service(self):
        """Obtém instância do ProtonService"""
        if 'proton' in self._mocks:
            return self._mocks['proton']
        if 'proton' not in self._services:
            from ..services.proton_service import ProtonService
            self._services['proton'] = ProtonService(self.client_factory)
        return self._services['proton']
    
    def get_lex_service(self):
        """Obtém instância do LexService"""
        if 'lex' in self._mocks:
            return self._mocks['lex']
        if 'lex' not in self._services:
            from ..services.lex_service import LexService
            self._services['lex'] = LexService(self.client_factory)
        return self._services['lex']
    
    def get_polly_service(self):
        """Obtém instância do PollyService"""
        if 'polly' in self._mocks:
            return self._mocks['polly']
        if 'polly' not in self._services:
            from ..services.polly_service import PollyService
            self._services['polly'] = PollyService(self.client_factory)
        return self._services['polly']
    
    def get_transcribe_service(self):
        """Obtém instância do TranscribeService"""
        if 'transcribe' in self._mocks:
            return self._mocks['transcribe']
        if 'transcribe' not in self._services:
            from ..services.transcribe_service import TranscribeService
            self._services['transcribe'] = TranscribeService(self.client_factory)
        return self._services['transcribe']
    
    def get_personalize_service(self):
        """Obtém instância do PersonalizeService"""
        if 'personalize' in self._mocks:
            return self._mocks['personalize']
        if 'personalize' not in self._services:
            from ..services.personalize_service import PersonalizeService
            self._services['personalize'] = PersonalizeService(self.client_factory)
        return self._services['personalize']
    
    def get_finspace_service(self):
        """Obtém instância do FinSpaceService"""
        if 'finspace' in self._mocks:
            return self._mocks['finspace']
        if 'finspace' not in self._services:
            from ..services.finspace_service import FinspaceService
            self._services['finspace'] = FinspaceService(self.client_factory)
        return self._services['finspace']
    
    def get_autogluon_service(self):
        """Obtém instância do AutoGluonService"""
        if 'autogluon' in self._mocks:
            return self._mocks['autogluon']
        if 'autogluon' not in self._services:
            from ..services.autogluon_service import AutogluonService
            self._services['autogluon'] = AutogluonService(self.client_factory)
        return self._services['autogluon']
    
    def get_backuprestore_service(self):
        """Obtém instância do BackupRestoreService"""
        if 'backuprestore' in self._mocks:
            return self._mocks['backuprestore']
        if 'backuprestore' not in self._services:
            from ..services.backuprestore_service import BackuprestoreService
            self._services['backuprestore'] = BackuprestoreService(self.client_factory)
        return self._services['backuprestore']
    
    def get_cassandra_service(self):
        """Obtém instância do CassandraService"""
        if 'cassandra' in self._mocks:
            return self._mocks['cassandra']
        if 'cassandra' not in self._services:
            from ..services.cassandra_service import CassandraService
            self._services['cassandra'] = CassandraService(self.client_factory)
        return self._services['cassandra']
    
    def get_cloudwatch_service(self):
        """Obtém instância do CloudWatchService"""
        if 'cloudwatch' in self._mocks:
            return self._mocks['cloudwatch']
        if 'cloudwatch' not in self._services:
            from ..services.cloudwatch_service import CloudWatchService
            self._services['cloudwatch'] = CloudWatchService(self.client_factory)
        return self._services['cloudwatch']
    
    def get_codecommit_enhanced_service(self):
        """Obtém instância do CodeCommitEnhancedService"""
        if 'codecommit_enhanced' in self._mocks:
            return self._mocks['codecommit_enhanced']
        if 'codecommit_enhanced' not in self._services:
            from ..services.codecommit_enhanced_service import CodecommitenhancedService
            self._services['codecommit_enhanced'] = CodecommitenhancedService(self.client_factory)
        return self._services['codecommit_enhanced']
    
    def get_dataportal_service(self):
        """Obtém instância do DataPortalService"""
        if 'dataportal' in self._mocks:
            return self._mocks['dataportal']
        if 'dataportal' not in self._services:
            from ..services.dataportal_service import DataportalService
            self._services['dataportal'] = DataportalService(self.client_factory)
        return self._services['dataportal']
    
    def get_datasync_enhanced_service(self):
        """Obtém instância do DataSyncEnhancedService"""
        if 'datasync_enhanced' in self._mocks:
            return self._mocks['datasync_enhanced']
        if 'datasync_enhanced' not in self._services:
            from ..services.datasync_enhanced_service import DatasyncenhancedService
            self._services['datasync_enhanced'] = DatasyncenhancedService(self.client_factory)
        return self._services['datasync_enhanced']
    
    def get_distro_service(self):
        """Obtém instância do DistroService"""
        if 'distro' in self._mocks:
            return self._mocks['distro']
        if 'distro' not in self._services:
            from ..services.distro_service import DistroService
            self._services['distro'] = DistroService(self.client_factory)
        return self._services['distro']
    
    def get_dynamodb_finops_service(self):
        """Obtém instância do DynamoDBFinOpsService"""
        if 'dynamodb_finops' in self._mocks:
            return self._mocks['dynamodb_finops']
        if 'dynamodb_finops' not in self._services:
            from ..services.dynamodb_finops_service import DynamoDBFinOpsService
            self._services['dynamodb_finops'] = DynamoDBFinOpsService(self.client_factory)
        return self._services['dynamodb_finops']
    
    def get_dynamodb_streams_service(self):
        """Obtém instância do DynamoDBStreamsService"""
        if 'dynamodb_streams' in self._mocks:
            return self._mocks['dynamodb_streams']
        if 'dynamodb_streams' not in self._services:
            from ..services.dynamodb_streams_service import DynamodbstreamsService
            self._services['dynamodb_streams'] = DynamodbstreamsService(self.client_factory)
        return self._services['dynamodb_streams']
    
    def get_elasticache_serverless_service(self):
        """Obtém instância do ElastiCacheServerlessService"""
        if 'elasticache_serverless' in self._mocks:
            return self._mocks['elasticache_serverless']
        if 'elasticache_serverless' not in self._services:
            from ..services.elasticache_serverless_service import ElasticacheserverlessService
            self._services['elasticache_serverless'] = ElasticacheserverlessService(self.client_factory)
        return self._services['elasticache_serverless']
    
    def get_elasticinference_service(self):
        """Obtém instância do ElasticInferenceService"""
        if 'elasticinference' in self._mocks:
            return self._mocks['elasticinference']
        if 'elasticinference' not in self._services:
            from ..services.elasticinference_service import ElasticinferenceService
            self._services['elasticinference'] = ElasticinferenceService(self.client_factory)
        return self._services['elasticinference']
    
    def get_emr_serverless_service(self):
        """Obtém instância do EMRServerlessService"""
        if 'emr_serverless' in self._mocks:
            return self._mocks['emr_serverless']
        if 'emr_serverless' not in self._services:
            from ..services.emr_serverless_service import EmrserverlessService
            self._services['emr_serverless'] = EmrserverlessService(self.client_factory)
        return self._services['emr_serverless']
    
    def get_gluestreaming_service(self):
        """Obtém instância do GlueStreamingService"""
        if 'gluestreaming' in self._mocks:
            return self._mocks['gluestreaming']
        if 'gluestreaming' not in self._services:
            from ..services.gluestreaming_service import GluestreamingService
            self._services['gluestreaming'] = GluestreamingService(self.client_factory)
        return self._services['gluestreaming']
    
    def get_lookoutequipment_service(self):
        """Obtém instância do LookoutEquipmentService"""
        if 'lookoutequipment' in self._mocks:
            return self._mocks['lookoutequipment']
        if 'lookoutequipment' not in self._services:
            from ..services.lookoutequipment_service import LookoutequipmentService
            self._services['lookoutequipment'] = LookoutequipmentService(self.client_factory)
        return self._services['lookoutequipment']
    
    def get_lookoutmetrics_service(self):
        """Obtém instância do LookoutMetricsService"""
        if 'lookoutmetrics' in self._mocks:
            return self._mocks['lookoutmetrics']
        if 'lookoutmetrics' not in self._services:
            from ..services.lookoutmetrics_service import LookoutmetricsService
            self._services['lookoutmetrics'] = LookoutmetricsService(self.client_factory)
        return self._services['lookoutmetrics']
    
    def get_lookoutvision_service(self):
        """Obtém instância do LookoutVisionService"""
        if 'lookoutvision' in self._mocks:
            return self._mocks['lookoutvision']
        if 'lookoutvision' not in self._services:
            from ..services.lookoutvision_service import LookoutvisionService
            self._services['lookoutvision'] = LookoutvisionService(self.client_factory)
        return self._services['lookoutvision']
    
    def get_marketplacecatalog_service(self):
        """Obtém instância do MarketplaceCatalogService"""
        if 'marketplacecatalog' in self._mocks:
            return self._mocks['marketplacecatalog']
        if 'marketplacecatalog' not in self._services:
            from ..services.marketplacecatalog_service import MarketplacecatalogService
            self._services['marketplacecatalog'] = MarketplacecatalogService(self.client_factory)
        return self._services['marketplacecatalog']
    
    def get_msk_serverless_service(self):
        """Obtém instância do MSKServerlessService"""
        if 'msk_serverless' in self._mocks:
            return self._mocks['msk_serverless']
        if 'msk_serverless' not in self._services:
            from ..services.msk_serverless_service import MskserverlessService
            self._services['msk_serverless'] = MskserverlessService(self.client_factory)
        return self._services['msk_serverless']
    
    def get_rds_custom_service(self):
        """Obtém instância do RDSCustomService"""
        if 'rds_custom' in self._mocks:
            return self._mocks['rds_custom']
        if 'rds_custom' not in self._services:
            from ..services.rds_custom_service import RdscustomService
            self._services['rds_custom'] = RdscustomService(self.client_factory)
        return self._services['rds_custom']
    
    def get_s3outposts_service(self):
        """Obtém instância do S3OutpostsService"""
        if 's3outposts' in self._mocks:
            return self._mocks['s3outposts']
        if 's3outposts' not in self._services:
            from ..services.s3outposts_service import S3outpostsService
            self._services['s3outposts'] = S3outpostsService(self.client_factory)
        return self._services['s3outposts']
    
    def get_snow_service(self):
        """Obtém instância do SnowService"""
        if 'snow' in self._mocks:
            return self._mocks['snow']
        if 'snow' not in self._services:
            from ..services.snow_service import SnowService
            self._services['snow'] = SnowService(self.client_factory)
        return self._services['snow']
    
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
            'secrets_manager': self.get_secrets_manager_service(),
            'msk': self.get_msk_service(),
            'eks': self.get_eks_service(),
            'aurora': self.get_aurora_service(),
            'opensearch': self.get_opensearch_service(),
            'workspaces': self.get_workspaces_service(),
            'fsx': self.get_fsx_service(),
            'documentdb': self.get_documentdb_service(),
            'neptune': self.get_neptune_service(),
            'timestream': self.get_timestream_service(),
            'batch': self.get_batch_service(),
            'stepfunctions': self.get_stepfunctions_service(),
            'apigateway': self.get_apigateway_service(),
            'transfer': self.get_transfer_service(),
            'cloudwatch_logs': self.get_cloudwatch_logs_service(),
            'waf': self.get_waf_service(),
            'cognito': self.get_cognito_service(),
            'eventbridge': self.get_eventbridge_service(),
            'codebuild': self.get_codebuild_service(),
            'codepipeline': self.get_codepipeline_service(),
            'codedeploy': self.get_codedeploy_service(),
            'codecommit': self.get_codecommit_service(),
            'guardduty': self.get_guardduty_service(),
            'inspector': self.get_inspector_service(),
            'config': self.get_config_service(),
            'cloudtrail': self.get_cloudtrail_service(),
            'kms': self.get_kms_service(),
            'acm': self.get_acm_service(),
            'bedrock': self.get_bedrock_service(),
            'comprehend': self.get_comprehend_service(),
            'rekognition': self.get_rekognition_service(),
            'textract': self.get_textract_service(),
            'athena': self.get_athena_service(),
            'quicksight': self.get_quicksight_service(),
            'datasync': self.get_datasync_service(),
            'lakeformation': self.get_lakeformation_service(),
            'globalaccelerator': self.get_globalaccelerator_service(),
            'directconnect': self.get_directconnect_service(),
            'transitgateway': self.get_transitgateway_service(),
            'ecr': self.get_ecr_service(),
            'apprunner': self.get_apprunner_service(),
            'elasticbeanstalk': self.get_elasticbeanstalk_service(),
            'lightsail': self.get_lightsail_service(),
            'iot': self.get_iot_service(),
            'iotanalytics': self.get_iotanalytics_service(),
            'greengrass': self.get_greengrass_service(),
            'iotevents': self.get_iotevents_service(),
            'mediaconvert': self.get_mediaconvert_service(),
            'medialive': self.get_medialive_service(),
            'mediapackage': self.get_mediapackage_service(),
            'ivs': self.get_ivs_service(),
            'dms': self.get_dms_service(),
            'mgn': self.get_mgn_service(),
            'snowfamily': self.get_snowfamily_service(),
            'datapipeline': self.get_datapipeline_service(),
            'appstream': self.get_appstream_service(),
            'workdocs': self.get_workdocs_service(),
            'chime': self.get_chime_service(),
            'gamelift': self.get_gamelift_service(),
            'robomaker': self.get_robomaker_service(),
            'qldb': self.get_qldb_service(),
            'managedblockchain': self.get_managedblockchain_service(),
            'braket': self.get_braket_service(),
            'xray': self.get_xray_service(),
            'cloudformation': self.get_cloudformation_service(),
            'ssm': self.get_ssm_service(),
            'appconfig': self.get_appconfig_service(),
            'sqs': self.get_sqs_service(),
            'iam': self.get_iam_service(),
            'securityhub': self.get_securityhub_service(),
            'macie': self.get_macie_service(),
            'trustedadvisor': self.get_trustedadvisor_service(),
            'organizations': self.get_organizations_service(),
            'controltower': self.get_controltower_service(),
            'pinpoint': self.get_pinpoint_service(),
            'ses': self.get_ses_service(),
            'connect': self.get_connect_service(),
            'servicecatalog': self.get_servicecatalog_service(),
            'appflow': self.get_appflow_service(),
            'mq': self.get_mq_service(),
            'kinesisvideo': self.get_kinesisvideo_service(),
            'mediastore': self.get_mediastore_service(),
            'forecast': self.get_forecast_service(),
            'memorydb': self.get_memorydb_service(),
            'keyspaces': self.get_keyspaces_service(),
            'storagegateway': self.get_storagegateway_service(),
            'dataexchange': self.get_dataexchange_service(),
            'codestar': self.get_codestar_service(),
            'cloud9': self.get_cloud9_service(),
            'serverlessrepo': self.get_serverlessrepo_service(),
            'proton': self.get_proton_service(),
            'lex': self.get_lex_service(),
            'polly': self.get_polly_service(),
            'transcribe': self.get_transcribe_service(),
            'personalize': self.get_personalize_service(),
            'finspace': self.get_finspace_service(),
            'autogluon': self.get_autogluon_service(),
            'backuprestore': self.get_backuprestore_service(),
            'cassandra': self.get_cassandra_service(),
            'cloudwatch': self.get_cloudwatch_service(),
            'codecommit_enhanced': self.get_codecommit_enhanced_service(),
            'dataportal': self.get_dataportal_service(),
            'datasync_enhanced': self.get_datasync_enhanced_service(),
            'distro': self.get_distro_service(),
            'dynamodb_finops': self.get_dynamodb_finops_service(),
            'dynamodb_streams': self.get_dynamodb_streams_service(),
            'elasticache_serverless': self.get_elasticache_serverless_service(),
            'elasticinference': self.get_elasticinference_service(),
            'emr_serverless': self.get_emr_serverless_service(),
            'gluestreaming': self.get_gluestreaming_service(),
            'lookoutequipment': self.get_lookoutequipment_service(),
            'lookoutmetrics': self.get_lookoutmetrics_service(),
            'lookoutvision': self.get_lookoutvision_service(),
            'marketplacecatalog': self.get_marketplacecatalog_service(),
            'msk_serverless': self.get_msk_serverless_service(),
            'rds_custom': self.get_rds_custom_service(),
            's3outposts': self.get_s3outposts_service(),
            'snow': self.get_snow_service(),
        }
    
    def clear_cache(self):
        """Limpa cache de serviços"""
        self._services.clear()
        logger.info("Service cache cleared")
