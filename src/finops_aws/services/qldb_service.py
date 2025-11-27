"""
AWS QLDB Service para FinOps.

Análise de custos e otimização de ledger de banco de dados quântico.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class QLDBLedger:
    """Ledger QLDB."""
    name: str
    arn: str = ""
    state: str = "ACTIVE"
    creation_date_time: Optional[datetime] = None
    permissions_mode: str = "ALLOW_ALL"
    deletion_protection: bool = True
    encryption_description: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.state == "ACTIVE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.state == "CREATING"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.state == "DELETING"

    @property
    def has_deletion_protection(self) -> bool:
        """Verifica se tem proteção contra deleção."""
        return bool(self.deletion_protection)

    @property
    def uses_allow_all(self) -> bool:
        """Verifica se usa ALLOW_ALL."""
        return self.permissions_mode == "ALLOW_ALL"

    @property
    def uses_standard(self) -> bool:
        """Verifica se usa STANDARD."""
        return self.permissions_mode == "STANDARD"

    @property
    def encryption_status(self) -> str:
        """Status da criptografia."""
        return self.encryption_description.get('EncryptionStatus', '')

    @property
    def is_encrypted(self) -> bool:
        """Verifica se está criptografado."""
        return self.encryption_status == "ENABLED"

    @property
    def kms_key_arn(self) -> str:
        """ARN da chave KMS."""
        return self.encryption_description.get('KmsKeyArn', '')

    @property
    def has_custom_kms(self) -> bool:
        """Verifica se usa chave KMS customizada."""
        return bool(self.kms_key_arn) and 'alias/aws/qldb' not in self.kms_key_arn

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "state": self.state,
            "is_active": self.is_active,
            "permissions_mode": self.permissions_mode,
            "has_deletion_protection": self.has_deletion_protection,
            "is_encrypted": self.is_encrypted,
            "has_custom_kms": self.has_custom_kms,
            "creation_date_time": self.creation_date_time.isoformat() if self.creation_date_time else None
        }


@dataclass
class QLDBJournalExport:
    """Journal Export QLDB."""
    export_id: str
    ledger_name: str = ""
    export_creation_time: Optional[datetime] = None
    status: str = "IN_PROGRESS"
    inclusive_start_time: Optional[datetime] = None
    exclusive_end_time: Optional[datetime] = None
    s3_export_configuration: Dict[str, Any] = field(default_factory=dict)
    role_arn: str = ""
    output_format: str = "ION_BINARY"

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.status == "IN_PROGRESS"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "COMPLETED"

    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "CANCELLED"

    @property
    def s3_bucket(self) -> str:
        """Bucket S3."""
        return self.s3_export_configuration.get('Bucket', '')

    @property
    def s3_prefix(self) -> str:
        """Prefix S3."""
        return self.s3_export_configuration.get('Prefix', '')

    @property
    def uses_ion_binary(self) -> bool:
        """Verifica se usa ION_BINARY."""
        return self.output_format == "ION_BINARY"

    @property
    def uses_ion_text(self) -> bool:
        """Verifica se usa ION_TEXT."""
        return self.output_format == "ION_TEXT"

    @property
    def uses_json(self) -> bool:
        """Verifica se usa JSON."""
        return self.output_format == "JSON"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "export_id": self.export_id,
            "ledger_name": self.ledger_name,
            "status": self.status,
            "is_in_progress": self.is_in_progress,
            "is_completed": self.is_completed,
            "s3_bucket": self.s3_bucket,
            "output_format": self.output_format,
            "export_creation_time": self.export_creation_time.isoformat() if self.export_creation_time else None
        }


@dataclass
class QLDBStream:
    """Stream QLDB."""
    stream_id: str
    ledger_name: str = ""
    stream_name: str = ""
    role_arn: str = ""
    arn: str = ""
    status: str = "ACTIVE"
    kinesis_configuration: Dict[str, Any] = field(default_factory=dict)
    error_cause: str = ""
    creation_time: Optional[datetime] = None
    inclusive_start_time: Optional[datetime] = None
    exclusive_end_time: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "COMPLETED"

    @property
    def is_canceled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "CANCELED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def is_impaired(self) -> bool:
        """Verifica se está prejudicado."""
        return self.status == "IMPAIRED"

    @property
    def kinesis_stream_arn(self) -> str:
        """ARN do stream Kinesis."""
        return self.kinesis_configuration.get('StreamArn', '')

    @property
    def aggregation_enabled(self) -> bool:
        """Verifica se agregação está habilitada."""
        return self.kinesis_configuration.get('AggregationEnabled', True)

    @property
    def has_error(self) -> bool:
        """Verifica se tem erro."""
        return bool(self.error_cause)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "stream_id": self.stream_id,
            "ledger_name": self.ledger_name,
            "stream_name": self.stream_name,
            "status": self.status,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "kinesis_stream_arn": self.kinesis_stream_arn,
            "has_error": self.has_error,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


class QLDBService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS QLDB."""

    def __init__(self, client_factory):
        """Inicializa o serviço QLDB."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._qldb_client = None

    @property
    def qldb_client(self):
        """Cliente QLDB com lazy loading."""
        if self._qldb_client is None:
            self._qldb_client = self._client_factory.get_client('qldb')
        return self._qldb_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço QLDB."""
        try:
            self.qldb_client.list_ledgers(MaxResults=1)
            return {
                "service": "qldb",
                "status": "healthy",
                "message": "QLDB service is accessible"
            }
        except Exception as e:
            return {
                "service": "qldb",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_ledgers(self) -> List[QLDBLedger]:
        """Lista ledgers."""
        ledgers = []
        try:
            paginator = self.qldb_client.get_paginator('list_ledgers')
            for page in paginator.paginate():
                for ledger in page.get('Ledgers', []):
                    try:
                        details = self.qldb_client.describe_ledger(Name=ledger['Name'])
                        ledgers.append(QLDBLedger(
                            name=details.get('Name', ''),
                            arn=details.get('Arn', ''),
                            state=details.get('State', 'ACTIVE'),
                            creation_date_time=details.get('CreationDateTime'),
                            permissions_mode=details.get('PermissionsMode', 'ALLOW_ALL'),
                            deletion_protection=details.get('DeletionProtection', True),
                            encryption_description=details.get('EncryptionDescription', {})
                        ))
                    except Exception as e:
                        self.logger.error(f"Erro ao descrever ledger: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar ledgers: {e}")
        return ledgers

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos QLDB."""
        ledgers = self.get_ledgers()

        return {
            "ledgers": [l.to_dict() for l in ledgers],
            "summary": {
                "total_ledgers": len(ledgers),
                "active_ledgers": len([l for l in ledgers if l.is_active]),
                "protected_ledgers": len([l for l in ledgers if l.has_deletion_protection]),
                "encrypted_ledgers": len([l for l in ledgers if l.is_encrypted]),
                "custom_kms_ledgers": len([l for l in ledgers if l.has_custom_kms]),
                "allow_all_ledgers": len([l for l in ledgers if l.uses_allow_all]),
                "standard_ledgers": len([l for l in ledgers if l.uses_standard])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do QLDB."""
        ledgers = self.get_ledgers()

        return {
            "ledgers_count": len(ledgers),
            "active_ledgers": len([l for l in ledgers if l.is_active]),
            "creating_ledgers": len([l for l in ledgers if l.is_creating]),
            "protected_ledgers": len([l for l in ledgers if l.has_deletion_protection]),
            "encrypted_ledgers": len([l for l in ledgers if l.is_encrypted]),
            "custom_kms_ledgers": len([l for l in ledgers if l.has_custom_kms]),
            "allow_all_ledgers": len([l for l in ledgers if l.uses_allow_all]),
            "standard_ledgers": len([l for l in ledgers if l.uses_standard])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para QLDB."""
        recommendations = []
        ledgers = self.get_ledgers()

        allow_all = [l for l in ledgers if l.uses_allow_all]
        if allow_all:
            recommendations.append({
                "resource_type": "QLDBLedger",
                "resource_id": "multiple",
                "recommendation": "Usar modo STANDARD",
                "description": f"{len(allow_all)} ledger(s) com modo ALLOW_ALL. "
                               "Considerar migrar para STANDARD para controle granular.",
                "priority": "medium"
            })

        return recommendations
