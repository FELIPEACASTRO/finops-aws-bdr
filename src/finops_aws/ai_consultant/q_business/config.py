"""
Amazon Q Business Configuration

Configurações e constantes para integração com Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class QBusinessRegion(Enum):
    """Regiões suportadas pelo Amazon Q Business"""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_NORTHEAST_1 = "ap-northeast-1"


class QBusinessIndexType(Enum):
    """Tipos de índice Q Business"""
    STARTER = "STARTER"
    ENTERPRISE = "ENTERPRISE"


class QBusinessRetrieverType(Enum):
    """Tipos de retriever Q Business"""
    NATIVE_INDEX = "NATIVE_INDEX"
    KENDRA_INDEX = "KENDRA_INDEX"


@dataclass
class QBusinessConfig:
    """
    Configuração para Amazon Q Business
    
    Attributes:
        application_id: ID da aplicação Q Business
        index_id: ID do índice de conhecimento
        retriever_id: ID do retriever
        data_source_id: ID do data source S3
        region: Região AWS
        identity_center_instance_arn: ARN do IAM Identity Center
        s3_bucket: Bucket S3 para dados e conhecimento
        sync_schedule: Agendamento de sync do data source
    """
    
    application_id: Optional[str] = field(
        default_factory=lambda: os.environ.get('Q_BUSINESS_APP_ID')
    )
    index_id: Optional[str] = field(
        default_factory=lambda: os.environ.get('Q_BUSINESS_INDEX_ID')
    )
    retriever_id: Optional[str] = field(
        default_factory=lambda: os.environ.get('Q_BUSINESS_RETRIEVER_ID')
    )
    data_source_id: Optional[str] = field(
        default_factory=lambda: os.environ.get('Q_BUSINESS_DATA_SOURCE_ID')
    )
    region: str = field(
        default_factory=lambda: os.environ.get('Q_BUSINESS_REGION', 'us-east-1')
    )
    identity_center_instance_arn: Optional[str] = field(
        default_factory=lambda: os.environ.get('IDENTITY_CENTER_INSTANCE_ARN')
    )
    s3_bucket: Optional[str] = field(
        default_factory=lambda: os.environ.get('FINOPS_REPORTS_BUCKET')
    )
    sync_schedule: str = "DAILY"
    
    index_type: QBusinessIndexType = QBusinessIndexType.ENTERPRISE
    retriever_type: QBusinessRetrieverType = QBusinessRetrieverType.NATIVE_INDEX
    
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 120
    
    s3_prefixes: List[str] = field(default_factory=lambda: [
        "processed/",
        "knowledge/"
    ])
    
    def validate(self) -> Dict[str, Any]:
        """
        Valida configuração e retorna status
        
        Returns:
            Dict com status de validação
        """
        errors = []
        warnings = []
        
        if not self.application_id:
            errors.append("Q_BUSINESS_APP_ID não configurado")
        
        if not self.index_id:
            warnings.append("Q_BUSINESS_INDEX_ID não configurado - será criado")
        
        if not self.identity_center_instance_arn:
            errors.append("IDENTITY_CENTER_INSTANCE_ARN é obrigatório (desde Jul/2024)")
        
        if not self.s3_bucket:
            errors.append("FINOPS_REPORTS_BUCKET não configurado")
        
        if self.region not in [r.value for r in QBusinessRegion]:
            warnings.append(f"Região {self.region} pode não suportar Q Business")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "config": self.to_dict()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário"""
        return {
            "application_id": self.application_id,
            "index_id": self.index_id,
            "retriever_id": self.retriever_id,
            "data_source_id": self.data_source_id,
            "region": self.region,
            "s3_bucket": self.s3_bucket,
            "index_type": self.index_type.value,
            "retriever_type": self.retriever_type.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    @classmethod
    def from_env(cls) -> 'QBusinessConfig':
        """Cria configuração a partir de variáveis de ambiente"""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QBusinessConfig':
        """Cria configuração a partir de dicionário"""
        config = cls()
        
        if 'application_id' in data:
            config.application_id = data['application_id']
        if 'index_id' in data:
            config.index_id = data['index_id']
        if 'retriever_id' in data:
            config.retriever_id = data['retriever_id']
        if 'data_source_id' in data:
            config.data_source_id = data['data_source_id']
        if 'region' in data:
            config.region = data['region']
        if 's3_bucket' in data:
            config.s3_bucket = data['s3_bucket']
        if 'identity_center_instance_arn' in data:
            config.identity_center_instance_arn = data['identity_center_instance_arn']
        if 'max_tokens' in data:
            config.max_tokens = data['max_tokens']
        if 'temperature' in data:
            config.temperature = data['temperature']
        
        return config


DEFAULT_CONFIG = QBusinessConfig()
