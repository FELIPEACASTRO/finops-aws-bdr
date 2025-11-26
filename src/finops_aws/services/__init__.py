"""
Serviços FinOps AWS

Este módulo contém os serviços para análise de custos, métricas e otimização.

FASE 2: Expansão de Serviços (21 serviços implementados)
- BaseAWSService: Classe base para todos os serviços
- S3Service: Análise de Object Storage
- EBSService: Análise de Block Storage
- DynamoDBFinOpsService: Análise de NoSQL
- EFSService: Análise de File Storage
- ElastiCacheService: Análise de Cache (Redis/Memcached)
- ECSContainerService: Análise de Containers (ECS/Fargate)

FASE 2.3: Serviços de Alta Prioridade
- EC2FinOpsService: Análise de EC2 instances
- LambdaFinOpsService: Análise de Lambda functions
- RedshiftService: Análise de Redshift clusters
- CloudFrontService: Análise de CloudFront distributions
- ELBService: Análise de Load Balancers (ALB, NLB, CLB)
- EMRService: Análise de EMR clusters
- VPCNetworkService: Análise de NAT Gateways e Elastic IPs
- KinesisService: Análise de Kinesis Data Streams
- GlueService: Análise de Glue ETL jobs
- SageMakerService: Análise de SageMaker notebooks/endpoints
- Route53Service: Análise de Route53 hosted zones
- BackupService: Análise de AWS Backup vaults
- SNSSQSService: Análise de SNS topics e SQS queues
- SecretsManagerService: Análise de Secrets Manager
"""

from .cost_service import CostService
from .metrics_service import MetricsService
from .optimizer_service import OptimizerService
from .rds_service import RDSService, RDSInstance
from .base_service import (
    BaseAWSService,
    ServiceCost,
    ServiceMetrics,
    ServiceRecommendation
)
from .s3_service import S3Service, S3Bucket
from .ebs_service import EBSService, EBSVolume, EBSSnapshot
from .dynamodb_finops_service import DynamoDBFinOpsService, DynamoDBTable
from .efs_service import EFSService, EFSFileSystem
from .elasticache_service import ElastiCacheService, ElastiCacheCluster, ElastiCacheReplicationGroup
from .ecs_service import ECSContainerService, ECSCluster, ECSService, ECSTask
from .ec2_finops_service import EC2FinOpsService, EC2Instance, ReservedInstance, SpotRequest
from .lambda_finops_service import LambdaFinOpsService, LambdaFunction, LambdaMetricsData
from .redshift_service import RedshiftService, RedshiftCluster
from .cloudfront_service import CloudFrontService, CloudFrontDistribution
from .elb_service import ELBService, LoadBalancer, TargetGroup
from .emr_service import EMRService, EMRCluster
from .vpc_network_service import VPCNetworkService, NATGateway, ElasticIP, VPC
from .kinesis_service import KinesisService, KinesisDataStream
from .glue_service import GlueService, GlueJob, GlueCrawler
from .sagemaker_service import SageMakerService, SageMakerNotebook, SageMakerEndpoint
from .route53_service import Route53Service, HostedZone
from .backup_service import BackupService, BackupVault, BackupPlan
from .sns_sqs_service import SNSSQSService, SNSTopic, SQSQueue
from .secrets_manager_service import SecretsManagerService, Secret

__all__ = [
    'CostService',
    'MetricsService',
    'OptimizerService',
    'RDSService',
    'RDSInstance',
    'BaseAWSService',
    'ServiceCost',
    'ServiceMetrics',
    'ServiceRecommendation',
    'S3Service',
    'S3Bucket',
    'EBSService',
    'EBSVolume',
    'EBSSnapshot',
    'DynamoDBFinOpsService',
    'DynamoDBTable',
    'EFSService',
    'EFSFileSystem',
    'ElastiCacheService',
    'ElastiCacheCluster',
    'ElastiCacheReplicationGroup',
    'ECSContainerService',
    'ECSCluster',
    'ECSService',
    'ECSTask',
    'EC2FinOpsService',
    'EC2Instance',
    'ReservedInstance',
    'SpotRequest',
    'LambdaFinOpsService',
    'LambdaFunction',
    'LambdaMetricsData',
    'RedshiftService',
    'RedshiftCluster',
    'CloudFrontService',
    'CloudFrontDistribution',
    'ELBService',
    'LoadBalancer',
    'TargetGroup',
    'EMRService',
    'EMRCluster',
    'VPCNetworkService',
    'NATGateway',
    'ElasticIP',
    'VPC',
    'KinesisService',
    'KinesisDataStream',
    'GlueService',
    'GlueJob',
    'GlueCrawler',
    'SageMakerService',
    'SageMakerNotebook',
    'SageMakerEndpoint',
    'Route53Service',
    'HostedZone',
    'BackupService',
    'BackupVault',
    'BackupPlan',
    'SNSSQSService',
    'SNSTopic',
    'SQSQueue',
    'SecretsManagerService',
    'Secret'
]
