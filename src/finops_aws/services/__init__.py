"""
Serviços FinOps AWS

Este módulo contém os serviços para análise de custos, métricas e otimização.

FASE 2: Expansão de Serviços
- BaseAWSService: Classe base para todos os serviços
- S3Service: Análise de Object Storage
- EBSService: Análise de Block Storage
- DynamoDBFinOpsService: Análise de NoSQL
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
    'DynamoDBTable'
]
