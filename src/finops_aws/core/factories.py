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
    AMPLIFY = "amplify"
    APPSYNC = "appsync"
    SAM = "sam"
    LAMBDAEDGE = "lambdaedge"
    STACKSETS = "stacksets"
    SERVICEQUOTAS = "servicequotas"
    LICENSEMANAGER = "licensemanager"
    RESOURCEGROUPS = "resourcegroups"
    TAGEDITOR = "tageditor"
    RAM = "ram"
    OUTPOSTS = "outposts"
    LOCALZONES = "localzones"
    WAVELENGTH = "wavelength"
    PRIVATE5G = "private5g"
    CLOUDWATCHLOGS = "cloudwatchlogs"
    CLOUDWATCHINSIGHTS = "cloudwatchinsights"
    SYNTHETICS = "synthetics"
    RUM = "rum"
    EVIDENTLY = "evidently"
    SERVICELENS = "servicelens"
    CONTAINERINSIGHTS = "containerinsights"
    LAMBDAINSIGHTS = "lambdainsights"
    CONTRIBUTORINSIGHTS = "contributorinsights"
    APPLICATIONINSIGHTS = "applicationinsights"
    INTERNETMONITOR = "internetmonitor"
    NETWORKMONITOR = "networkmonitor"
    COSTEXPLORER = "costexplorer"
    BUDGETS = "budgets"
    SAVINGSPLANS = "savingsplans"
    RESERVEDINSTANCES = "reservedinstances"
    COSTANOMALYDETECTION = "costanomalydetection"
    COSTCATEGORIES = "costcategories"
    COSTALLOCATIONTAGS = "costallocationtags"
    BILLINGCONDUCTOR = "billingconductor"
    MARKETPLACEMETERING = "marketplacemetering"
    DATAEXPORTS = "dataexports"
    SECRETSMANAGERADV = "secretsmanageradv"
    PRIVATECA = "privateca"
    CLOUDHSM = "cloudhsm"
    DIRECTORYSERVICE = "directoryservice"
    IDENTITYCENTER = "identitycenter"
    ACCESSANALYZER = "accessanalyzer"
    FIREWALLMANAGER = "firewallmanager"
    SHIELD = "shield"
    NETWORKFIREWALL = "networkfirewall"
    AUDITMANAGER = "auditmanager"
    DETECTIVE = "detective"
    SECURITYLAKE = "securitylake"
    APPMESH = "appmesh"
    CLOUDMAP = "cloudmap"
    PRIVATELINK = "privatelink"
    VPCLATTICE = "vpclattice"
    VERIFIEDACCESS = "verifiedaccess"
    CLIENTVPN = "clientvpn"
    SITETOSITEVPN = "sitetositevpn"
    NETWORKMANAGER = "networkmanager"
    REACHABILITYANALYZER = "reachabilityanalyzer"
    TRAFFICMIRRORING = "trafficmirroring"
    ELASTICACHEGLOBAL = "elasticacheglobal"
    DYNAMODBGLOBAL = "dynamodbglobal"
    AURORASERVERLESS = "auroraserverless"
    RDSPROXY = "rdsproxy"
    DMSMIGRATION = "dmsmigration"
    SCHEMACONVERSION = "schemaconversion"
    REDSHIFTSERVERLESS = "redshiftserverless"
    OPENSEARCHSERVERLESS = "opensearchserverless"
    MSKCONNECT = "mskconnect"
    GLUEDATABREW = "gluedatabrew"
    DATAZONE = "datazone"
    CLEANROOMS = "cleanrooms"
    SAGEMAKERSTUDIO = "sagemakerstudio"
    SAGEMAKERPIPELINES = "sagemakerpipelines"
    SAGEMAKERFEATURESTORE = "sagemakerfeaturestore"
    SAGEMAKERMODELREGISTRY = "sagemakermodelregistry"
    SAGEMAKEREXPERIMENTS = "sagemakerexperiments"
    SAGEMAKERDEBUGGER = "sagemakerdebugger"
    SAGEMAKERCLARIFY = "sagemakerclarify"
    SAGEMAKERGROUNDTRUTH = "sagemakergroundtruth"
    PANORAMA = "panorama"
    DEEPRACER = "deepracer"
    DEEPCOMPOSER = "deepcomposer"
    HEALTHLAKE = "healthlake"
    CODEARTIFACT = "codeartifact"
    CODEGURU = "codeguru"
    FIS = "fis"
    PATCHMANAGER = "patchmanager"
    STATEMANAGER = "statemanager"
    SSMAUTOMATION = "ssmautomation"
    OPSCENTER = "opscenter"
    INCIDENTMANAGER = "incidentmanager"
    AUTOSCALING = "autoscaling"
    LAUNCHWIZARD = "launchwizard"
    WORKSPACESWEB = "workspacesweb"
    APPSTREAMADV = "appstreamadv"
    WORKMAIL = "workmail"
    WICKR = "wickr"
    CHIMESDK = "chimesdk"
    HONEYCODE = "honeycode"
    MANAGEDGRAFANA = "managedgrafana"
    MANAGEDPROMETHEUS = "managedprometheus"
    MANAGEDFLINK = "managedflink"
    MWAA = "mwaa"
    GROUNDSTATION = "groundstation"
    NIMBLESTUDIO = "nimblestudio"
    SIMSPACEWEAVER = "simspaceweaver"
    IOTTWINMAKER = "iottwinmaker"
    IOTFLEETWISE = "iotfleetwise"
    IOTSITEWISE = "iotsitewise"
    LOCATIONSERVICE = "locationservice"
    GEOSPATIAL = "geospatial"
    HEALTHOMICS = "healthomics"
    SUPPLYCHAIN = "supplychain"


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
    
    def _string_to_service_type(self, service_name: str) -> AWSServiceType:
        """
        Converte string para AWSServiceType enum
        
        Args:
            service_name: Nome do serviço como string (ex: 'ec2', 's3')
            
        Returns:
            AWSServiceType correspondente
            
        Raises:
            ValueError: Se o serviço não for suportado
        """
        service_name_lower = service_name.lower().replace('-', '_').replace(' ', '_')
        
        for service_type in AWSServiceType:
            if service_type.value == service_name or service_type.name.lower() == service_name_lower:
                return service_type
        
        raise ValueError(f"Unsupported AWS service: {service_name}. "
                        f"Available services: {[s.value for s in AWSServiceType][:10]}...")
    
    def get_client(
        self,
        service_type: 'AWSServiceType | str',
        region: Optional[str] = None
    ) -> Any:
        """
        Obtém cliente boto3 para um serviço AWS
        
        Args:
            service_type: Tipo de serviço AWS (enum ou string)
            region: Região específica (override)
            
        Returns:
            Cliente boto3 para o serviço
        """
        if isinstance(service_type, str):
            service_type = self._string_to_service_type(service_type)
        
        if service_type in self._mocks:
            return self._mocks[service_type]
        
        effective_region = region or self.config.region or 'us-east-1'
        
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
        service_type: 'AWSServiceType | str',
        region: Optional[str] = None
    ) -> Any:
        """
        Obtém resource boto3 para um serviço AWS
        
        Args:
            service_type: Tipo de serviço AWS (enum ou string)
            region: Região específica (override)
            
        Returns:
            Resource boto3 para o serviço
        """
        if isinstance(service_type, str):
            service_type = self._string_to_service_type(service_type)
        
        if service_type in self._mocks:
            return self._mocks[service_type]
        
        effective_region = region or self.config.region or 'us-east-1'
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
    

    def get_amplify_service(self):
        """Obtém instância do AmplifyService"""
        if 'amplify' in self._mocks:
            return self._mocks['amplify']
        if 'amplify' not in self._services:
            from ..services.amplify_service import AmplifyService
            self._services['amplify'] = AmplifyService(self.client_factory)
        return self._services['amplify']

    def get_appsync_service(self):
        """Obtém instância do AppSyncService"""
        if 'appsync' in self._mocks:
            return self._mocks['appsync']
        if 'appsync' not in self._services:
            from ..services.appsync_service import AppSyncService
            self._services['appsync'] = AppSyncService(self.client_factory)
        return self._services['appsync']

    def get_apigatewayv2_service(self):
        """Obtém instância do ApiGatewayV2Service"""
        if 'apigatewayv2' in self._mocks:
            return self._mocks['apigatewayv2']
        if 'apigatewayv2' not in self._services:
            from ..services.apigatewayv2_service import ApiGatewayV2Service
            self._services['apigatewayv2'] = ApiGatewayV2Service(self.client_factory)
        return self._services['apigatewayv2']

    def get_sam_service(self):
        """Obtém instância do SAMService"""
        if 'sam' in self._mocks:
            return self._mocks['sam']
        if 'sam' not in self._services:
            from ..services.sam_service import SAMService
            self._services['sam'] = SAMService(self.client_factory)
        return self._services['sam']

    def get_lambdaedge_service(self):
        """Obtém instância do LambdaEdgeService"""
        if 'lambdaedge' in self._mocks:
            return self._mocks['lambdaedge']
        if 'lambdaedge' not in self._services:
            from ..services.lambdaedge_service import LambdaEdgeService
            self._services['lambdaedge'] = LambdaEdgeService(self.client_factory)
        return self._services['lambdaedge']

    def get_stacksets_service(self):
        """Obtém instância do StackSetsService"""
        if 'stacksets' in self._mocks:
            return self._mocks['stacksets']
        if 'stacksets' not in self._services:
            from ..services.stacksets_service import StackSetsService
            self._services['stacksets'] = StackSetsService(self.client_factory)
        return self._services['stacksets']

    def get_servicequotas_service(self):
        """Obtém instância do ServiceQuotasService"""
        if 'servicequotas' in self._mocks:
            return self._mocks['servicequotas']
        if 'servicequotas' not in self._services:
            from ..services.servicequotas_service import ServiceQuotasService
            self._services['servicequotas'] = ServiceQuotasService(self.client_factory)
        return self._services['servicequotas']

    def get_licensemanager_service(self):
        """Obtém instância do LicenseManagerService"""
        if 'licensemanager' in self._mocks:
            return self._mocks['licensemanager']
        if 'licensemanager' not in self._services:
            from ..services.licensemanager_service import LicenseManagerService
            self._services['licensemanager'] = LicenseManagerService(self.client_factory)
        return self._services['licensemanager']

    def get_resourcegroups_service(self):
        """Obtém instância do ResourceGroupsService"""
        if 'resourcegroups' in self._mocks:
            return self._mocks['resourcegroups']
        if 'resourcegroups' not in self._services:
            from ..services.resourcegroups_service import ResourceGroupsService
            self._services['resourcegroups'] = ResourceGroupsService(self.client_factory)
        return self._services['resourcegroups']

    def get_tageditor_service(self):
        """Obtém instância do TagEditorService"""
        if 'tageditor' in self._mocks:
            return self._mocks['tageditor']
        if 'tageditor' not in self._services:
            from ..services.tageditor_service import TagEditorService
            self._services['tageditor'] = TagEditorService(self.client_factory)
        return self._services['tageditor']

    def get_ram_service(self):
        """Obtém instância do RAMService"""
        if 'ram' in self._mocks:
            return self._mocks['ram']
        if 'ram' not in self._services:
            from ..services.ram_service import RAMService
            self._services['ram'] = RAMService(self.client_factory)
        return self._services['ram']

    def get_outposts_service(self):
        """Obtém instância do OutpostsService"""
        if 'outposts' in self._mocks:
            return self._mocks['outposts']
        if 'outposts' not in self._services:
            from ..services.outposts_service import OutpostsService
            self._services['outposts'] = OutpostsService(self.client_factory)
        return self._services['outposts']

    def get_localzones_service(self):
        """Obtém instância do LocalZonesService"""
        if 'localzones' in self._mocks:
            return self._mocks['localzones']
        if 'localzones' not in self._services:
            from ..services.localzones_service import LocalZonesService
            self._services['localzones'] = LocalZonesService(self.client_factory)
        return self._services['localzones']

    def get_wavelength_service(self):
        """Obtém instância do WavelengthService"""
        if 'wavelength' in self._mocks:
            return self._mocks['wavelength']
        if 'wavelength' not in self._services:
            from ..services.wavelength_service import WavelengthService
            self._services['wavelength'] = WavelengthService(self.client_factory)
        return self._services['wavelength']

    def get_private5g_service(self):
        """Obtém instância do Private5GService"""
        if 'private5g' in self._mocks:
            return self._mocks['private5g']
        if 'private5g' not in self._services:
            from ..services.private5g_service import Private5GService
            self._services['private5g'] = Private5GService(self.client_factory)
        return self._services['private5g']

    def get_cloudwatchlogs_service(self):
        """Obtém instância do CloudWatchLogsService"""
        if 'cloudwatchlogs' in self._mocks:
            return self._mocks['cloudwatchlogs']
        if 'cloudwatchlogs' not in self._services:
            from ..services.cloudwatchlogs_service import CloudWatchLogsService
            self._services['cloudwatchlogs'] = CloudWatchLogsService(self.client_factory)
        return self._services['cloudwatchlogs']

    def get_cloudwatchinsights_service(self):
        """Obtém instância do CloudWatchInsightsService"""
        if 'cloudwatchinsights' in self._mocks:
            return self._mocks['cloudwatchinsights']
        if 'cloudwatchinsights' not in self._services:
            from ..services.cloudwatchinsights_service import CloudWatchInsightsService
            self._services['cloudwatchinsights'] = CloudWatchInsightsService(self.client_factory)
        return self._services['cloudwatchinsights']

    def get_synthetics_service(self):
        """Obtém instância do SyntheticsService"""
        if 'synthetics' in self._mocks:
            return self._mocks['synthetics']
        if 'synthetics' not in self._services:
            from ..services.synthetics_service import SyntheticsService
            self._services['synthetics'] = SyntheticsService(self.client_factory)
        return self._services['synthetics']

    def get_rum_service(self):
        """Obtém instância do RUMService"""
        if 'rum' in self._mocks:
            return self._mocks['rum']
        if 'rum' not in self._services:
            from ..services.rum_service import RUMService
            self._services['rum'] = RUMService(self.client_factory)
        return self._services['rum']

    def get_evidently_service(self):
        """Obtém instância do EvidentlyService"""
        if 'evidently' in self._mocks:
            return self._mocks['evidently']
        if 'evidently' not in self._services:
            from ..services.evidently_service import EvidentlyService
            self._services['evidently'] = EvidentlyService(self.client_factory)
        return self._services['evidently']

    def get_servicelens_service(self):
        """Obtém instância do ServiceLensService"""
        if 'servicelens' in self._mocks:
            return self._mocks['servicelens']
        if 'servicelens' not in self._services:
            from ..services.servicelens_service import ServiceLensService
            self._services['servicelens'] = ServiceLensService(self.client_factory)
        return self._services['servicelens']

    def get_containerinsights_service(self):
        """Obtém instância do ContainerInsightsService"""
        if 'containerinsights' in self._mocks:
            return self._mocks['containerinsights']
        if 'containerinsights' not in self._services:
            from ..services.containerinsights_service import ContainerInsightsService
            self._services['containerinsights'] = ContainerInsightsService(self.client_factory)
        return self._services['containerinsights']

    def get_lambdainsights_service(self):
        """Obtém instância do LambdaInsightsService"""
        if 'lambdainsights' in self._mocks:
            return self._mocks['lambdainsights']
        if 'lambdainsights' not in self._services:
            from ..services.lambdainsights_service import LambdaInsightsService
            self._services['lambdainsights'] = LambdaInsightsService(self.client_factory)
        return self._services['lambdainsights']

    def get_contributorinsights_service(self):
        """Obtém instância do ContributorInsightsService"""
        if 'contributorinsights' in self._mocks:
            return self._mocks['contributorinsights']
        if 'contributorinsights' not in self._services:
            from ..services.contributorinsights_service import ContributorInsightsService
            self._services['contributorinsights'] = ContributorInsightsService(self.client_factory)
        return self._services['contributorinsights']

    def get_applicationinsights_service(self):
        """Obtém instância do ApplicationInsightsService"""
        if 'applicationinsights' in self._mocks:
            return self._mocks['applicationinsights']
        if 'applicationinsights' not in self._services:
            from ..services.applicationinsights_service import ApplicationInsightsService
            self._services['applicationinsights'] = ApplicationInsightsService(self.client_factory)
        return self._services['applicationinsights']

    def get_internetmonitor_service(self):
        """Obtém instância do InternetMonitorService"""
        if 'internetmonitor' in self._mocks:
            return self._mocks['internetmonitor']
        if 'internetmonitor' not in self._services:
            from ..services.internetmonitor_service import InternetMonitorService
            self._services['internetmonitor'] = InternetMonitorService(self.client_factory)
        return self._services['internetmonitor']

    def get_networkmonitor_service(self):
        """Obtém instância do NetworkMonitorService"""
        if 'networkmonitor' in self._mocks:
            return self._mocks['networkmonitor']
        if 'networkmonitor' not in self._services:
            from ..services.networkmonitor_service import NetworkMonitorService
            self._services['networkmonitor'] = NetworkMonitorService(self.client_factory)
        return self._services['networkmonitor']

    def get_costexplorer_service(self):
        """Obtém instância do CostExplorerService"""
        if 'costexplorer' in self._mocks:
            return self._mocks['costexplorer']
        if 'costexplorer' not in self._services:
            from ..services.costexplorer_service import CostExplorerService
            self._services['costexplorer'] = CostExplorerService(self.client_factory)
        return self._services['costexplorer']

    def get_budgets_service(self):
        """Obtém instância do BudgetsService"""
        if 'budgets' in self._mocks:
            return self._mocks['budgets']
        if 'budgets' not in self._services:
            from ..services.budgets_service import BudgetsService
            self._services['budgets'] = BudgetsService(self.client_factory)
        return self._services['budgets']

    def get_savingsplans_service(self):
        """Obtém instância do SavingsPlansService"""
        if 'savingsplans' in self._mocks:
            return self._mocks['savingsplans']
        if 'savingsplans' not in self._services:
            from ..services.savingsplans_service import SavingsPlansService
            self._services['savingsplans'] = SavingsPlansService(self.client_factory)
        return self._services['savingsplans']

    def get_reservedinstances_service(self):
        """Obtém instância do ReservedInstancesService"""
        if 'reservedinstances' in self._mocks:
            return self._mocks['reservedinstances']
        if 'reservedinstances' not in self._services:
            from ..services.reservedinstances_service import ReservedInstancesService
            self._services['reservedinstances'] = ReservedInstancesService(self.client_factory)
        return self._services['reservedinstances']

    def get_costanomalydetection_service(self):
        """Obtém instância do CostAnomalyDetectionService"""
        if 'costanomalydetection' in self._mocks:
            return self._mocks['costanomalydetection']
        if 'costanomalydetection' not in self._services:
            from ..services.costanomalydetection_service import CostAnomalyDetectionService
            self._services['costanomalydetection'] = CostAnomalyDetectionService(self.client_factory)
        return self._services['costanomalydetection']

    def get_costcategories_service(self):
        """Obtém instância do CostCategoriesService"""
        if 'costcategories' in self._mocks:
            return self._mocks['costcategories']
        if 'costcategories' not in self._services:
            from ..services.costcategories_service import CostCategoriesService
            self._services['costcategories'] = CostCategoriesService(self.client_factory)
        return self._services['costcategories']

    def get_costallocationtags_service(self):
        """Obtém instância do CostAllocationTagsService"""
        if 'costallocationtags' in self._mocks:
            return self._mocks['costallocationtags']
        if 'costallocationtags' not in self._services:
            from ..services.costallocationtags_service import CostAllocationTagsService
            self._services['costallocationtags'] = CostAllocationTagsService(self.client_factory)
        return self._services['costallocationtags']

    def get_billingconductor_service(self):
        """Obtém instância do BillingConductorService"""
        if 'billingconductor' in self._mocks:
            return self._mocks['billingconductor']
        if 'billingconductor' not in self._services:
            from ..services.billingconductor_service import BillingConductorService
            self._services['billingconductor'] = BillingConductorService(self.client_factory)
        return self._services['billingconductor']

    def get_marketplacemetering_service(self):
        """Obtém instância do MarketplaceMeteringService"""
        if 'marketplacemetering' in self._mocks:
            return self._mocks['marketplacemetering']
        if 'marketplacemetering' not in self._services:
            from ..services.marketplacemetering_service import MarketplaceMeteringService
            self._services['marketplacemetering'] = MarketplaceMeteringService(self.client_factory)
        return self._services['marketplacemetering']

    def get_dataexports_service(self):
        """Obtém instância do DataExportsService"""
        if 'dataexports' in self._mocks:
            return self._mocks['dataexports']
        if 'dataexports' not in self._services:
            from ..services.dataexports_service import DataExportsService
            self._services['dataexports'] = DataExportsService(self.client_factory)
        return self._services['dataexports']

    def get_secretsmanageradv_service(self):
        """Obtém instância do SecretsManagerAdvService"""
        if 'secretsmanageradv' in self._mocks:
            return self._mocks['secretsmanageradv']
        if 'secretsmanageradv' not in self._services:
            from ..services.secretsmanageradv_service import SecretsManagerAdvService
            self._services['secretsmanageradv'] = SecretsManagerAdvService(self.client_factory)
        return self._services['secretsmanageradv']

    def get_privateca_service(self):
        """Obtém instância do PrivateCAService"""
        if 'privateca' in self._mocks:
            return self._mocks['privateca']
        if 'privateca' not in self._services:
            from ..services.privateca_service import PrivateCAService
            self._services['privateca'] = PrivateCAService(self.client_factory)
        return self._services['privateca']

    def get_cloudhsm_service(self):
        """Obtém instância do CloudHSMService"""
        if 'cloudhsm' in self._mocks:
            return self._mocks['cloudhsm']
        if 'cloudhsm' not in self._services:
            from ..services.cloudhsm_service import CloudHSMService
            self._services['cloudhsm'] = CloudHSMService(self.client_factory)
        return self._services['cloudhsm']

    def get_directoryservice_service(self):
        """Obtém instância do DirectoryServiceService"""
        if 'directoryservice' in self._mocks:
            return self._mocks['directoryservice']
        if 'directoryservice' not in self._services:
            from ..services.directoryservice_service import DirectoryServiceService
            self._services['directoryservice'] = DirectoryServiceService(self.client_factory)
        return self._services['directoryservice']

    def get_identitycenter_service(self):
        """Obtém instância do IdentityCenterService"""
        if 'identitycenter' in self._mocks:
            return self._mocks['identitycenter']
        if 'identitycenter' not in self._services:
            from ..services.identitycenter_service import IdentityCenterService
            self._services['identitycenter'] = IdentityCenterService(self.client_factory)
        return self._services['identitycenter']

    def get_accessanalyzer_service(self):
        """Obtém instância do AccessAnalyzerService"""
        if 'accessanalyzer' in self._mocks:
            return self._mocks['accessanalyzer']
        if 'accessanalyzer' not in self._services:
            from ..services.accessanalyzer_service import AccessAnalyzerService
            self._services['accessanalyzer'] = AccessAnalyzerService(self.client_factory)
        return self._services['accessanalyzer']

    def get_firewallmanager_service(self):
        """Obtém instância do FirewallManagerService"""
        if 'firewallmanager' in self._mocks:
            return self._mocks['firewallmanager']
        if 'firewallmanager' not in self._services:
            from ..services.firewallmanager_service import FirewallManagerService
            self._services['firewallmanager'] = FirewallManagerService(self.client_factory)
        return self._services['firewallmanager']

    def get_shield_service(self):
        """Obtém instância do ShieldService"""
        if 'shield' in self._mocks:
            return self._mocks['shield']
        if 'shield' not in self._services:
            from ..services.shield_service import ShieldService
            self._services['shield'] = ShieldService(self.client_factory)
        return self._services['shield']

    def get_networkfirewall_service(self):
        """Obtém instância do NetworkFirewallService"""
        if 'networkfirewall' in self._mocks:
            return self._mocks['networkfirewall']
        if 'networkfirewall' not in self._services:
            from ..services.networkfirewall_service import NetworkFirewallService
            self._services['networkfirewall'] = NetworkFirewallService(self.client_factory)
        return self._services['networkfirewall']

    def get_auditmanager_service(self):
        """Obtém instância do AuditManagerService"""
        if 'auditmanager' in self._mocks:
            return self._mocks['auditmanager']
        if 'auditmanager' not in self._services:
            from ..services.auditmanager_service import AuditManagerService
            self._services['auditmanager'] = AuditManagerService(self.client_factory)
        return self._services['auditmanager']

    def get_detective_service(self):
        """Obtém instância do DetectiveService"""
        if 'detective' in self._mocks:
            return self._mocks['detective']
        if 'detective' not in self._services:
            from ..services.detective_service import DetectiveService
            self._services['detective'] = DetectiveService(self.client_factory)
        return self._services['detective']

    def get_securitylake_service(self):
        """Obtém instância do SecurityLakeService"""
        if 'securitylake' in self._mocks:
            return self._mocks['securitylake']
        if 'securitylake' not in self._services:
            from ..services.securitylake_service import SecurityLakeService
            self._services['securitylake'] = SecurityLakeService(self.client_factory)
        return self._services['securitylake']

    def get_appmesh_service(self):
        """Obtém instância do AppMeshService"""
        if 'appmesh' in self._mocks:
            return self._mocks['appmesh']
        if 'appmesh' not in self._services:
            from ..services.appmesh_service import AppMeshService
            self._services['appmesh'] = AppMeshService(self.client_factory)
        return self._services['appmesh']

    def get_cloudmap_service(self):
        """Obtém instância do CloudMapService"""
        if 'cloudmap' in self._mocks:
            return self._mocks['cloudmap']
        if 'cloudmap' not in self._services:
            from ..services.cloudmap_service import CloudMapService
            self._services['cloudmap'] = CloudMapService(self.client_factory)
        return self._services['cloudmap']

    def get_privatelink_service(self):
        """Obtém instância do PrivateLinkService"""
        if 'privatelink' in self._mocks:
            return self._mocks['privatelink']
        if 'privatelink' not in self._services:
            from ..services.privatelink_service import PrivateLinkService
            self._services['privatelink'] = PrivateLinkService(self.client_factory)
        return self._services['privatelink']

    def get_vpclattice_service(self):
        """Obtém instância do VPCLatticeService"""
        if 'vpclattice' in self._mocks:
            return self._mocks['vpclattice']
        if 'vpclattice' not in self._services:
            from ..services.vpclattice_service import VPCLatticeService
            self._services['vpclattice'] = VPCLatticeService(self.client_factory)
        return self._services['vpclattice']

    def get_verifiedaccess_service(self):
        """Obtém instância do VerifiedAccessService"""
        if 'verifiedaccess' in self._mocks:
            return self._mocks['verifiedaccess']
        if 'verifiedaccess' not in self._services:
            from ..services.verifiedaccess_service import VerifiedAccessService
            self._services['verifiedaccess'] = VerifiedAccessService(self.client_factory)
        return self._services['verifiedaccess']

    def get_clientvpn_service(self):
        """Obtém instância do ClientVPNService"""
        if 'clientvpn' in self._mocks:
            return self._mocks['clientvpn']
        if 'clientvpn' not in self._services:
            from ..services.clientvpn_service import ClientVPNService
            self._services['clientvpn'] = ClientVPNService(self.client_factory)
        return self._services['clientvpn']

    def get_sitetositevpn_service(self):
        """Obtém instância do SiteToSiteVPNService"""
        if 'sitetositevpn' in self._mocks:
            return self._mocks['sitetositevpn']
        if 'sitetositevpn' not in self._services:
            from ..services.sitetositevpn_service import SiteToSiteVPNService
            self._services['sitetositevpn'] = SiteToSiteVPNService(self.client_factory)
        return self._services['sitetositevpn']

    def get_networkmanager_service(self):
        """Obtém instância do NetworkManagerService"""
        if 'networkmanager' in self._mocks:
            return self._mocks['networkmanager']
        if 'networkmanager' not in self._services:
            from ..services.networkmanager_service import NetworkManagerService
            self._services['networkmanager'] = NetworkManagerService(self.client_factory)
        return self._services['networkmanager']

    def get_reachabilityanalyzer_service(self):
        """Obtém instância do ReachabilityAnalyzerService"""
        if 'reachabilityanalyzer' in self._mocks:
            return self._mocks['reachabilityanalyzer']
        if 'reachabilityanalyzer' not in self._services:
            from ..services.reachabilityanalyzer_service import ReachabilityAnalyzerService
            self._services['reachabilityanalyzer'] = ReachabilityAnalyzerService(self.client_factory)
        return self._services['reachabilityanalyzer']

    def get_trafficmirroring_service(self):
        """Obtém instância do TrafficMirroringService"""
        if 'trafficmirroring' in self._mocks:
            return self._mocks['trafficmirroring']
        if 'trafficmirroring' not in self._services:
            from ..services.trafficmirroring_service import TrafficMirroringService
            self._services['trafficmirroring'] = TrafficMirroringService(self.client_factory)
        return self._services['trafficmirroring']

    def get_elasticacheglobal_service(self):
        """Obtém instância do ElastiCacheGlobalService"""
        if 'elasticacheglobal' in self._mocks:
            return self._mocks['elasticacheglobal']
        if 'elasticacheglobal' not in self._services:
            from ..services.elasticacheglobal_service import ElastiCacheGlobalService
            self._services['elasticacheglobal'] = ElastiCacheGlobalService(self.client_factory)
        return self._services['elasticacheglobal']

    def get_dynamodbglobal_service(self):
        """Obtém instância do DynamoDBGlobalService"""
        if 'dynamodbglobal' in self._mocks:
            return self._mocks['dynamodbglobal']
        if 'dynamodbglobal' not in self._services:
            from ..services.dynamodbglobal_service import DynamoDBGlobalService
            self._services['dynamodbglobal'] = DynamoDBGlobalService(self.client_factory)
        return self._services['dynamodbglobal']

    def get_auroraserverless_service(self):
        """Obtém instância do AuroraServerlessService"""
        if 'auroraserverless' in self._mocks:
            return self._mocks['auroraserverless']
        if 'auroraserverless' not in self._services:
            from ..services.auroraserverless_service import AuroraServerlessService
            self._services['auroraserverless'] = AuroraServerlessService(self.client_factory)
        return self._services['auroraserverless']

    def get_rdsproxy_service(self):
        """Obtém instância do RDSProxyService"""
        if 'rdsproxy' in self._mocks:
            return self._mocks['rdsproxy']
        if 'rdsproxy' not in self._services:
            from ..services.rdsproxy_service import RDSProxyService
            self._services['rdsproxy'] = RDSProxyService(self.client_factory)
        return self._services['rdsproxy']

    def get_dmsmigration_service(self):
        """Obtém instância do DMSMigrationService"""
        if 'dmsmigration' in self._mocks:
            return self._mocks['dmsmigration']
        if 'dmsmigration' not in self._services:
            from ..services.dmsmigration_service import DMSMigrationService
            self._services['dmsmigration'] = DMSMigrationService(self.client_factory)
        return self._services['dmsmigration']

    def get_schemaconversion_service(self):
        """Obtém instância do SchemaConversionService"""
        if 'schemaconversion' in self._mocks:
            return self._mocks['schemaconversion']
        if 'schemaconversion' not in self._services:
            from ..services.schemaconversion_service import SchemaConversionService
            self._services['schemaconversion'] = SchemaConversionService(self.client_factory)
        return self._services['schemaconversion']

    def get_redshiftserverless_service(self):
        """Obtém instância do RedshiftServerlessService"""
        if 'redshiftserverless' in self._mocks:
            return self._mocks['redshiftserverless']
        if 'redshiftserverless' not in self._services:
            from ..services.redshiftserverless_service import RedshiftServerlessService
            self._services['redshiftserverless'] = RedshiftServerlessService(self.client_factory)
        return self._services['redshiftserverless']

    def get_opensearchserverless_service(self):
        """Obtém instância do OpenSearchServerlessService"""
        if 'opensearchserverless' in self._mocks:
            return self._mocks['opensearchserverless']
        if 'opensearchserverless' not in self._services:
            from ..services.opensearchserverless_service import OpenSearchServerlessService
            self._services['opensearchserverless'] = OpenSearchServerlessService(self.client_factory)
        return self._services['opensearchserverless']

    def get_mskconnect_service(self):
        """Obtém instância do MSKConnectService"""
        if 'mskconnect' in self._mocks:
            return self._mocks['mskconnect']
        if 'mskconnect' not in self._services:
            from ..services.mskconnect_service import MSKConnectService
            self._services['mskconnect'] = MSKConnectService(self.client_factory)
        return self._services['mskconnect']

    def get_gluedatabrew_service(self):
        """Obtém instância do GlueDataBrewService"""
        if 'gluedatabrew' in self._mocks:
            return self._mocks['gluedatabrew']
        if 'gluedatabrew' not in self._services:
            from ..services.gluedatabrew_service import GlueDataBrewService
            self._services['gluedatabrew'] = GlueDataBrewService(self.client_factory)
        return self._services['gluedatabrew']

    def get_datazone_service(self):
        """Obtém instância do DataZoneService"""
        if 'datazone' in self._mocks:
            return self._mocks['datazone']
        if 'datazone' not in self._services:
            from ..services.datazone_service import DataZoneService
            self._services['datazone'] = DataZoneService(self.client_factory)
        return self._services['datazone']

    def get_cleanrooms_service(self):
        """Obtém instância do CleanRoomsService"""
        if 'cleanrooms' in self._mocks:
            return self._mocks['cleanrooms']
        if 'cleanrooms' not in self._services:
            from ..services.cleanrooms_service import CleanRoomsService
            self._services['cleanrooms'] = CleanRoomsService(self.client_factory)
        return self._services['cleanrooms']

    def get_sagemakerstudio_service(self):
        """Obtém instância do SageMakerStudioService"""
        if 'sagemakerstudio' in self._mocks:
            return self._mocks['sagemakerstudio']
        if 'sagemakerstudio' not in self._services:
            from ..services.sagemakerstudio_service import SageMakerStudioService
            self._services['sagemakerstudio'] = SageMakerStudioService(self.client_factory)
        return self._services['sagemakerstudio']

    def get_sagemakerpipelines_service(self):
        """Obtém instância do SageMakerPipelinesService"""
        if 'sagemakerpipelines' in self._mocks:
            return self._mocks['sagemakerpipelines']
        if 'sagemakerpipelines' not in self._services:
            from ..services.sagemakerpipelines_service import SageMakerPipelinesService
            self._services['sagemakerpipelines'] = SageMakerPipelinesService(self.client_factory)
        return self._services['sagemakerpipelines']

    def get_sagemakerfeaturestore_service(self):
        """Obtém instância do SageMakerFeatureStoreService"""
        if 'sagemakerfeaturestore' in self._mocks:
            return self._mocks['sagemakerfeaturestore']
        if 'sagemakerfeaturestore' not in self._services:
            from ..services.sagemakerfeaturestore_service import SageMakerFeatureStoreService
            self._services['sagemakerfeaturestore'] = SageMakerFeatureStoreService(self.client_factory)
        return self._services['sagemakerfeaturestore']

    def get_sagemakermodelregistry_service(self):
        """Obtém instância do SageMakerModelRegistryService"""
        if 'sagemakermodelregistry' in self._mocks:
            return self._mocks['sagemakermodelregistry']
        if 'sagemakermodelregistry' not in self._services:
            from ..services.sagemakermodelregistry_service import SageMakerModelRegistryService
            self._services['sagemakermodelregistry'] = SageMakerModelRegistryService(self.client_factory)
        return self._services['sagemakermodelregistry']

    def get_sagemakerexperiments_service(self):
        """Obtém instância do SageMakerExperimentsService"""
        if 'sagemakerexperiments' in self._mocks:
            return self._mocks['sagemakerexperiments']
        if 'sagemakerexperiments' not in self._services:
            from ..services.sagemakerexperiments_service import SageMakerExperimentsService
            self._services['sagemakerexperiments'] = SageMakerExperimentsService(self.client_factory)
        return self._services['sagemakerexperiments']

    def get_sagemakerdebugger_service(self):
        """Obtém instância do SageMakerDebuggerService"""
        if 'sagemakerdebugger' in self._mocks:
            return self._mocks['sagemakerdebugger']
        if 'sagemakerdebugger' not in self._services:
            from ..services.sagemakerdebugger_service import SageMakerDebuggerService
            self._services['sagemakerdebugger'] = SageMakerDebuggerService(self.client_factory)
        return self._services['sagemakerdebugger']

    def get_sagemakerclarify_service(self):
        """Obtém instância do SageMakerClarifyService"""
        if 'sagemakerclarify' in self._mocks:
            return self._mocks['sagemakerclarify']
        if 'sagemakerclarify' not in self._services:
            from ..services.sagemakerclarify_service import SageMakerClarifyService
            self._services['sagemakerclarify'] = SageMakerClarifyService(self.client_factory)
        return self._services['sagemakerclarify']

    def get_sagemakergroundtruth_service(self):
        """Obtém instância do SageMakerGroundTruthService"""
        if 'sagemakergroundtruth' in self._mocks:
            return self._mocks['sagemakergroundtruth']
        if 'sagemakergroundtruth' not in self._services:
            from ..services.sagemakergroundtruth_service import SageMakerGroundTruthService
            self._services['sagemakergroundtruth'] = SageMakerGroundTruthService(self.client_factory)
        return self._services['sagemakergroundtruth']

    def get_panorama_service(self):
        """Obtém instância do PanoramaService"""
        if 'panorama' in self._mocks:
            return self._mocks['panorama']
        if 'panorama' not in self._services:
            from ..services.panorama_service import PanoramaService
            self._services['panorama'] = PanoramaService(self.client_factory)
        return self._services['panorama']

    def get_deepracer_service(self):
        """Obtém instância do DeepRacerService"""
        if 'deepracer' in self._mocks:
            return self._mocks['deepracer']
        if 'deepracer' not in self._services:
            from ..services.deepracer_service import DeepRacerService
            self._services['deepracer'] = DeepRacerService(self.client_factory)
        return self._services['deepracer']

    def get_deepcomposer_service(self):
        """Obtém instância do DeepComposerService"""
        if 'deepcomposer' in self._mocks:
            return self._mocks['deepcomposer']
        if 'deepcomposer' not in self._services:
            from ..services.deepcomposer_service import DeepComposerService
            self._services['deepcomposer'] = DeepComposerService(self.client_factory)
        return self._services['deepcomposer']

    def get_healthlake_service(self):
        """Obtém instância do HealthLakeService"""
        if 'healthlake' in self._mocks:
            return self._mocks['healthlake']
        if 'healthlake' not in self._services:
            from ..services.healthlake_service import HealthLakeService
            self._services['healthlake'] = HealthLakeService(self.client_factory)
        return self._services['healthlake']

    def get_codeartifact_service(self):
        """Obtém instância do CodeArtifactService"""
        if 'codeartifact' in self._mocks:
            return self._mocks['codeartifact']
        if 'codeartifact' not in self._services:
            from ..services.codeartifact_service import CodeArtifactService
            self._services['codeartifact'] = CodeArtifactService(self.client_factory)
        return self._services['codeartifact']

    def get_codeguru_service(self):
        """Obtém instância do CodeGuruService"""
        if 'codeguru' in self._mocks:
            return self._mocks['codeguru']
        if 'codeguru' not in self._services:
            from ..services.codeguru_service import CodeGuruService
            self._services['codeguru'] = CodeGuruService(self.client_factory)
        return self._services['codeguru']

    def get_fis_service(self):
        """Obtém instância do FISService"""
        if 'fis' in self._mocks:
            return self._mocks['fis']
        if 'fis' not in self._services:
            from ..services.fis_service import FISService
            self._services['fis'] = FISService(self.client_factory)
        return self._services['fis']

    def get_patchmanager_service(self):
        """Obtém instância do PatchManagerService"""
        if 'patchmanager' in self._mocks:
            return self._mocks['patchmanager']
        if 'patchmanager' not in self._services:
            from ..services.patchmanager_service import PatchManagerService
            self._services['patchmanager'] = PatchManagerService(self.client_factory)
        return self._services['patchmanager']

    def get_statemanager_service(self):
        """Obtém instância do StateManagerService"""
        if 'statemanager' in self._mocks:
            return self._mocks['statemanager']
        if 'statemanager' not in self._services:
            from ..services.statemanager_service import StateManagerService
            self._services['statemanager'] = StateManagerService(self.client_factory)
        return self._services['statemanager']

    def get_ssmautomation_service(self):
        """Obtém instância do SSMAutomationService"""
        if 'ssmautomation' in self._mocks:
            return self._mocks['ssmautomation']
        if 'ssmautomation' not in self._services:
            from ..services.ssmautomation_service import SSMAutomationService
            self._services['ssmautomation'] = SSMAutomationService(self.client_factory)
        return self._services['ssmautomation']

    def get_opscenter_service(self):
        """Obtém instância do OpsCenterService"""
        if 'opscenter' in self._mocks:
            return self._mocks['opscenter']
        if 'opscenter' not in self._services:
            from ..services.opscenter_service import OpsCenterService
            self._services['opscenter'] = OpsCenterService(self.client_factory)
        return self._services['opscenter']

    def get_incidentmanager_service(self):
        """Obtém instância do IncidentManagerService"""
        if 'incidentmanager' in self._mocks:
            return self._mocks['incidentmanager']
        if 'incidentmanager' not in self._services:
            from ..services.incidentmanager_service import IncidentManagerService
            self._services['incidentmanager'] = IncidentManagerService(self.client_factory)
        return self._services['incidentmanager']

    def get_autoscaling_service(self):
        """Obtém instância do AutoScalingService"""
        if 'autoscaling' in self._mocks:
            return self._mocks['autoscaling']
        if 'autoscaling' not in self._services:
            from ..services.autoscaling_service import AutoScalingService
            self._services['autoscaling'] = AutoScalingService(self.client_factory)
        return self._services['autoscaling']

    def get_launchwizard_service(self):
        """Obtém instância do LaunchWizardService"""
        if 'launchwizard' in self._mocks:
            return self._mocks['launchwizard']
        if 'launchwizard' not in self._services:
            from ..services.launchwizard_service import LaunchWizardService
            self._services['launchwizard'] = LaunchWizardService(self.client_factory)
        return self._services['launchwizard']

    def get_workspacesweb_service(self):
        """Obtém instância do WorkSpacesWebService"""
        if 'workspacesweb' in self._mocks:
            return self._mocks['workspacesweb']
        if 'workspacesweb' not in self._services:
            from ..services.workspacesweb_service import WorkSpacesWebService
            self._services['workspacesweb'] = WorkSpacesWebService(self.client_factory)
        return self._services['workspacesweb']

    def get_appstreamadv_service(self):
        """Obtém instância do AppStreamAdvService"""
        if 'appstreamadv' in self._mocks:
            return self._mocks['appstreamadv']
        if 'appstreamadv' not in self._services:
            from ..services.appstreamadv_service import AppStreamAdvService
            self._services['appstreamadv'] = AppStreamAdvService(self.client_factory)
        return self._services['appstreamadv']

    def get_workmail_service(self):
        """Obtém instância do WorkMailService"""
        if 'workmail' in self._mocks:
            return self._mocks['workmail']
        if 'workmail' not in self._services:
            from ..services.workmail_service import WorkMailService
            self._services['workmail'] = WorkMailService(self.client_factory)
        return self._services['workmail']

    def get_wickr_service(self):
        """Obtém instância do WickrService"""
        if 'wickr' in self._mocks:
            return self._mocks['wickr']
        if 'wickr' not in self._services:
            from ..services.wickr_service import WickrService
            self._services['wickr'] = WickrService(self.client_factory)
        return self._services['wickr']

    def get_chimesdk_service(self):
        """Obtém instância do ChimeSDKService"""
        if 'chimesdk' in self._mocks:
            return self._mocks['chimesdk']
        if 'chimesdk' not in self._services:
            from ..services.chimesdk_service import ChimeSDKService
            self._services['chimesdk'] = ChimeSDKService(self.client_factory)
        return self._services['chimesdk']

    def get_honeycode_service(self):
        """Obtém instância do HoneycodeService"""
        if 'honeycode' in self._mocks:
            return self._mocks['honeycode']
        if 'honeycode' not in self._services:
            from ..services.honeycode_service import HoneycodeService
            self._services['honeycode'] = HoneycodeService(self.client_factory)
        return self._services['honeycode']

    def get_managedgrafana_service(self):
        """Obtém instância do ManagedGrafanaService"""
        if 'managedgrafana' in self._mocks:
            return self._mocks['managedgrafana']
        if 'managedgrafana' not in self._services:
            from ..services.managedgrafana_service import ManagedGrafanaService
            self._services['managedgrafana'] = ManagedGrafanaService(self.client_factory)
        return self._services['managedgrafana']

    def get_managedprometheus_service(self):
        """Obtém instância do ManagedPrometheusService"""
        if 'managedprometheus' in self._mocks:
            return self._mocks['managedprometheus']
        if 'managedprometheus' not in self._services:
            from ..services.managedprometheus_service import ManagedPrometheusService
            self._services['managedprometheus'] = ManagedPrometheusService(self.client_factory)
        return self._services['managedprometheus']

    def get_managedflink_service(self):
        """Obtém instância do ManagedFlinkService"""
        if 'managedflink' in self._mocks:
            return self._mocks['managedflink']
        if 'managedflink' not in self._services:
            from ..services.managedflink_service import ManagedFlinkService
            self._services['managedflink'] = ManagedFlinkService(self.client_factory)
        return self._services['managedflink']

    def get_mwaa_service(self):
        """Obtém instância do MWAAService"""
        if 'mwaa' in self._mocks:
            return self._mocks['mwaa']
        if 'mwaa' not in self._services:
            from ..services.mwaa_service import MWAAService
            self._services['mwaa'] = MWAAService(self.client_factory)
        return self._services['mwaa']

    def get_groundstation_service(self):
        """Obtém instância do GroundStationService"""
        if 'groundstation' in self._mocks:
            return self._mocks['groundstation']
        if 'groundstation' not in self._services:
            from ..services.groundstation_service import GroundStationService
            self._services['groundstation'] = GroundStationService(self.client_factory)
        return self._services['groundstation']

    def get_nimblestudio_service(self):
        """Obtém instância do NimbleStudioService"""
        if 'nimblestudio' in self._mocks:
            return self._mocks['nimblestudio']
        if 'nimblestudio' not in self._services:
            from ..services.nimblestudio_service import NimbleStudioService
            self._services['nimblestudio'] = NimbleStudioService(self.client_factory)
        return self._services['nimblestudio']

    def get_simspaceweaver_service(self):
        """Obtém instância do SimSpaceWeaverService"""
        if 'simspaceweaver' in self._mocks:
            return self._mocks['simspaceweaver']
        if 'simspaceweaver' not in self._services:
            from ..services.simspaceweaver_service import SimSpaceWeaverService
            self._services['simspaceweaver'] = SimSpaceWeaverService(self.client_factory)
        return self._services['simspaceweaver']

    def get_iottwinmaker_service(self):
        """Obtém instância do IoTTwinMakerService"""
        if 'iottwinmaker' in self._mocks:
            return self._mocks['iottwinmaker']
        if 'iottwinmaker' not in self._services:
            from ..services.iottwinmaker_service import IoTTwinMakerService
            self._services['iottwinmaker'] = IoTTwinMakerService(self.client_factory)
        return self._services['iottwinmaker']

    def get_iotfleetwise_service(self):
        """Obtém instância do IoTFleetWiseService"""
        if 'iotfleetwise' in self._mocks:
            return self._mocks['iotfleetwise']
        if 'iotfleetwise' not in self._services:
            from ..services.iotfleetwise_service import IoTFleetWiseService
            self._services['iotfleetwise'] = IoTFleetWiseService(self.client_factory)
        return self._services['iotfleetwise']

    def get_iotsitewise_service(self):
        """Obtém instância do IoTSiteWiseService"""
        if 'iotsitewise' in self._mocks:
            return self._mocks['iotsitewise']
        if 'iotsitewise' not in self._services:
            from ..services.iotsitewise_service import IoTSiteWiseService
            self._services['iotsitewise'] = IoTSiteWiseService(self.client_factory)
        return self._services['iotsitewise']

    def get_locationservice_service(self):
        """Obtém instância do LocationServiceService"""
        if 'locationservice' in self._mocks:
            return self._mocks['locationservice']
        if 'locationservice' not in self._services:
            from ..services.locationservice_service import LocationServiceService
            self._services['locationservice'] = LocationServiceService(self.client_factory)
        return self._services['locationservice']

    def get_geospatial_service(self):
        """Obtém instância do GeoSpatialService"""
        if 'geospatial' in self._mocks:
            return self._mocks['geospatial']
        if 'geospatial' not in self._services:
            from ..services.geospatial_service import GeoSpatialService
            self._services['geospatial'] = GeoSpatialService(self.client_factory)
        return self._services['geospatial']

    def get_healthomics_service(self):
        """Obtém instância do HealthOmicsService"""
        if 'healthomics' in self._mocks:
            return self._mocks['healthomics']
        if 'healthomics' not in self._services:
            from ..services.healthomics_service import HealthOmicsService
            self._services['healthomics'] = HealthOmicsService(self.client_factory)
        return self._services['healthomics']

    def get_supplychain_service(self):
        """Obtém instância do SupplyChainService"""
        if 'supplychain' in self._mocks:
            return self._mocks['supplychain']
        if 'supplychain' not in self._services:
            from ..services.supplychain_service import SupplyChainService
            self._services['supplychain'] = SupplyChainService(self.client_factory)
        return self._services['supplychain']

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
            'amplify': self.get_amplify_service(),
            'appsync': self.get_appsync_service(),
            'apigatewayv2': self.get_apigatewayv2_service(),
            'sam': self.get_sam_service(),
            'lambdaedge': self.get_lambdaedge_service(),
            'stacksets': self.get_stacksets_service(),
            'servicequotas': self.get_servicequotas_service(),
            'licensemanager': self.get_licensemanager_service(),
            'resourcegroups': self.get_resourcegroups_service(),
            'tageditor': self.get_tageditor_service(),
            'ram': self.get_ram_service(),
            'outposts': self.get_outposts_service(),
            'localzones': self.get_localzones_service(),
            'wavelength': self.get_wavelength_service(),
            'private5g': self.get_private5g_service(),
            'cloudwatchlogs': self.get_cloudwatchlogs_service(),
            'cloudwatchinsights': self.get_cloudwatchinsights_service(),
            'synthetics': self.get_synthetics_service(),
            'rum': self.get_rum_service(),
            'evidently': self.get_evidently_service(),
            'servicelens': self.get_servicelens_service(),
            'containerinsights': self.get_containerinsights_service(),
            'lambdainsights': self.get_lambdainsights_service(),
            'contributorinsights': self.get_contributorinsights_service(),
            'applicationinsights': self.get_applicationinsights_service(),
            'internetmonitor': self.get_internetmonitor_service(),
            'networkmonitor': self.get_networkmonitor_service(),
            'costexplorer': self.get_costexplorer_service(),
            'budgets': self.get_budgets_service(),
            'savingsplans': self.get_savingsplans_service(),
            'reservedinstances': self.get_reservedinstances_service(),
            'costanomalydetection': self.get_costanomalydetection_service(),
            'costcategories': self.get_costcategories_service(),
            'costallocationtags': self.get_costallocationtags_service(),
            'billingconductor': self.get_billingconductor_service(),
            'marketplacemetering': self.get_marketplacemetering_service(),
            'dataexports': self.get_dataexports_service(),
            'secretsmanageradv': self.get_secretsmanageradv_service(),
            'privateca': self.get_privateca_service(),
            'cloudhsm': self.get_cloudhsm_service(),
            'directoryservice': self.get_directoryservice_service(),
            'identitycenter': self.get_identitycenter_service(),
            'accessanalyzer': self.get_accessanalyzer_service(),
            'firewallmanager': self.get_firewallmanager_service(),
            'shield': self.get_shield_service(),
            'networkfirewall': self.get_networkfirewall_service(),
            'auditmanager': self.get_auditmanager_service(),
            'detective': self.get_detective_service(),
            'securitylake': self.get_securitylake_service(),
            'appmesh': self.get_appmesh_service(),
            'cloudmap': self.get_cloudmap_service(),
            'privatelink': self.get_privatelink_service(),
            'vpclattice': self.get_vpclattice_service(),
            'verifiedaccess': self.get_verifiedaccess_service(),
            'clientvpn': self.get_clientvpn_service(),
            'sitetositevpn': self.get_sitetositevpn_service(),
            'networkmanager': self.get_networkmanager_service(),
            'reachabilityanalyzer': self.get_reachabilityanalyzer_service(),
            'trafficmirroring': self.get_trafficmirroring_service(),
            'elasticacheglobal': self.get_elasticacheglobal_service(),
            'dynamodbglobal': self.get_dynamodbglobal_service(),
            'auroraserverless': self.get_auroraserverless_service(),
            'rdsproxy': self.get_rdsproxy_service(),
            'dmsmigration': self.get_dmsmigration_service(),
            'schemaconversion': self.get_schemaconversion_service(),
            'redshiftserverless': self.get_redshiftserverless_service(),
            'opensearchserverless': self.get_opensearchserverless_service(),
            'mskconnect': self.get_mskconnect_service(),
            'gluedatabrew': self.get_gluedatabrew_service(),
            'datazone': self.get_datazone_service(),
            'cleanrooms': self.get_cleanrooms_service(),
            'sagemakerstudio': self.get_sagemakerstudio_service(),
            'sagemakerpipelines': self.get_sagemakerpipelines_service(),
            'sagemakerfeaturestore': self.get_sagemakerfeaturestore_service(),
            'sagemakermodelregistry': self.get_sagemakermodelregistry_service(),
            'sagemakerexperiments': self.get_sagemakerexperiments_service(),
            'sagemakerdebugger': self.get_sagemakerdebugger_service(),
            'sagemakerclarify': self.get_sagemakerclarify_service(),
            'sagemakergroundtruth': self.get_sagemakergroundtruth_service(),
            'panorama': self.get_panorama_service(),
            'deepracer': self.get_deepracer_service(),
            'deepcomposer': self.get_deepcomposer_service(),
            'healthlake': self.get_healthlake_service(),
            'codeartifact': self.get_codeartifact_service(),
            'codeguru': self.get_codeguru_service(),
            'fis': self.get_fis_service(),
            'patchmanager': self.get_patchmanager_service(),
            'statemanager': self.get_statemanager_service(),
            'ssmautomation': self.get_ssmautomation_service(),
            'opscenter': self.get_opscenter_service(),
            'incidentmanager': self.get_incidentmanager_service(),
            'autoscaling': self.get_autoscaling_service(),
            'launchwizard': self.get_launchwizard_service(),
            'workspacesweb': self.get_workspacesweb_service(),
            'appstreamadv': self.get_appstreamadv_service(),
            'workmail': self.get_workmail_service(),
            'wickr': self.get_wickr_service(),
            'chimesdk': self.get_chimesdk_service(),
            'honeycode': self.get_honeycode_service(),
            'managedgrafana': self.get_managedgrafana_service(),
            'managedprometheus': self.get_managedprometheus_service(),
            'managedflink': self.get_managedflink_service(),
            'mwaa': self.get_mwaa_service(),
            'groundstation': self.get_groundstation_service(),
            'nimblestudio': self.get_nimblestudio_service(),
            'simspaceweaver': self.get_simspaceweaver_service(),
            'iottwinmaker': self.get_iottwinmaker_service(),
            'iotfleetwise': self.get_iotfleetwise_service(),
            'iotsitewise': self.get_iotsitewise_service(),
            'locationservice': self.get_locationservice_service(),
            'geospatial': self.get_geospatial_service(),
            'healthomics': self.get_healthomics_service(),
            'supplychain': self.get_supplychain_service()
        }
    
    def clear_cache(self):
        """Limpa cache de serviços"""
        self._services.clear()
        logger.info("Service cache cleared")
