"""
AWS WorkDocs Service para FinOps.

Análise de custos e otimização de armazenamento de documentos.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class WorkDocsUser:
    """User WorkDocs."""
    user_id: str
    username: str = ""
    email_address: str = ""
    given_name: str = ""
    surname: str = ""
    organization_id: str = ""
    root_folder_id: str = ""
    recycle_bin_folder_id: str = ""
    status: str = "ACTIVE"
    type: str = "USER"
    created_timestamp: Optional[datetime] = None
    modified_timestamp: Optional[datetime] = None
    time_zone_id: str = ""
    locale: str = ""
    storage: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_inactive(self) -> bool:
        """Verifica se está inativo."""
        return self.status == "INACTIVE"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.status == "PENDING"

    @property
    def is_user(self) -> bool:
        """Verifica se é usuário."""
        return self.type == "USER"

    @property
    def is_admin(self) -> bool:
        """Verifica se é admin."""
        return self.type == "ADMIN"

    @property
    def is_poweruser(self) -> bool:
        """Verifica se é power user."""
        return self.type == "POWERUSER"

    @property
    def storage_used_bytes(self) -> int:
        """Storage usado em bytes."""
        rule = self.storage.get('StorageRule', {})
        return rule.get('StorageAllocatedInBytes', 0)

    @property
    def storage_used_gb(self) -> float:
        """Storage usado em GB."""
        return self.storage_used_bytes / (1024 ** 3)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email_address": self.email_address,
            "status": self.status,
            "type": self.type,
            "is_active": self.is_active,
            "storage_used_gb": self.storage_used_gb,
            "created_timestamp": self.created_timestamp.isoformat() if self.created_timestamp else None
        }


@dataclass
class WorkDocsFolder:
    """Folder WorkDocs."""
    folder_id: str
    name: str = ""
    creator_id: str = ""
    parent_folder_id: str = ""
    created_timestamp: Optional[datetime] = None
    modified_timestamp: Optional[datetime] = None
    resource_state: str = "ACTIVE"
    signature: str = ""
    labels: List[str] = field(default_factory=list)
    size: int = 0
    latest_version_size: int = 0

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.resource_state == "ACTIVE"

    @property
    def is_recycling(self) -> bool:
        """Verifica se está na lixeira."""
        return self.resource_state == "RECYCLING"

    @property
    def is_recycled(self) -> bool:
        """Verifica se foi reciclado."""
        return self.resource_state == "RECYCLED"

    @property
    def is_restoring(self) -> bool:
        """Verifica se está restaurando."""
        return self.resource_state == "RESTORING"

    @property
    def has_labels(self) -> bool:
        """Verifica se tem labels."""
        return len(self.labels) > 0

    @property
    def size_mb(self) -> float:
        """Tamanho em MB."""
        return self.size / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "folder_id": self.folder_id,
            "name": self.name,
            "resource_state": self.resource_state,
            "is_active": self.is_active,
            "has_labels": self.has_labels,
            "size_mb": self.size_mb,
            "created_timestamp": self.created_timestamp.isoformat() if self.created_timestamp else None
        }


@dataclass
class WorkDocsDocument:
    """Document WorkDocs."""
    document_id: str
    name: str = ""
    creator_id: str = ""
    parent_folder_id: str = ""
    created_timestamp: Optional[datetime] = None
    modified_timestamp: Optional[datetime] = None
    resource_state: str = "ACTIVE"
    labels: List[str] = field(default_factory=list)
    latest_version_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.resource_state == "ACTIVE"

    @property
    def is_recycling(self) -> bool:
        """Verifica se está na lixeira."""
        return self.resource_state == "RECYCLING"

    @property
    def has_labels(self) -> bool:
        """Verifica se tem labels."""
        return len(self.labels) > 0

    @property
    def content_type(self) -> str:
        """Tipo de conteúdo."""
        return self.latest_version_metadata.get('ContentType', '')

    @property
    def size_bytes(self) -> int:
        """Tamanho em bytes."""
        return self.latest_version_metadata.get('Size', 0)

    @property
    def size_mb(self) -> float:
        """Tamanho em MB."""
        return self.size_bytes / (1024 * 1024)

    @property
    def version_id(self) -> str:
        """ID da versão."""
        return self.latest_version_metadata.get('Id', '')

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "document_id": self.document_id,
            "name": self.name,
            "resource_state": self.resource_state,
            "is_active": self.is_active,
            "has_labels": self.has_labels,
            "content_type": self.content_type,
            "size_mb": self.size_mb,
            "created_timestamp": self.created_timestamp.isoformat() if self.created_timestamp else None
        }


class WorkDocsService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS WorkDocs."""

    def __init__(self, client_factory):
        """Inicializa o serviço WorkDocs."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._workdocs_client = None

    @property
    def workdocs_client(self):
        """Cliente WorkDocs com lazy loading."""
        if self._workdocs_client is None:
            self._workdocs_client = self._client_factory.get_client('workdocs')
        return self._workdocs_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço WorkDocs."""
        try:
            self.workdocs_client.describe_users(MaxResults=1)
            return {
                "service": "workdocs",
                "status": "healthy",
                "message": "WorkDocs service is accessible"
            }
        except Exception as e:
            return {
                "service": "workdocs",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_users(self, organization_id: str = None) -> List[WorkDocsUser]:
        """Lista users."""
        users = []
        try:
            params = {}
            if organization_id:
                params['OrganizationId'] = organization_id
            
            paginator = self.workdocs_client.get_paginator('describe_users')
            for page in paginator.paginate(**params):
                for user in page.get('Users', []):
                    users.append(WorkDocsUser(
                        user_id=user.get('Id', ''),
                        username=user.get('Username', ''),
                        email_address=user.get('EmailAddress', ''),
                        given_name=user.get('GivenName', ''),
                        surname=user.get('Surname', ''),
                        organization_id=user.get('OrganizationId', ''),
                        root_folder_id=user.get('RootFolderId', ''),
                        recycle_bin_folder_id=user.get('RecycleBinFolderId', ''),
                        status=user.get('Status', 'ACTIVE'),
                        type=user.get('Type', 'USER'),
                        created_timestamp=user.get('CreatedTimestamp'),
                        modified_timestamp=user.get('ModifiedTimestamp'),
                        time_zone_id=user.get('TimeZoneId', ''),
                        locale=user.get('Locale', ''),
                        storage=user.get('Storage', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar users: {e}")
        return users

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos WorkDocs."""
        users = self.get_users()

        active_users = [u for u in users if u.is_active]

        return {
            "users": [u.to_dict() for u in users],
            "summary": {
                "total_users": len(users),
                "active_users": len(active_users),
                "inactive_users": len([u for u in users if u.is_inactive]),
                "pending_users": len([u for u in users if u.is_pending]),
                "admin_users": len([u for u in users if u.is_admin]),
                "power_users": len([u for u in users if u.is_poweruser]),
                "regular_users": len([u for u in users if u.is_user]),
                "total_storage_gb": sum(u.storage_used_gb for u in users)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do WorkDocs."""
        users = self.get_users()

        return {
            "users_count": len(users),
            "active_users": len([u for u in users if u.is_active]),
            "inactive_users": len([u for u in users if u.is_inactive]),
            "pending_users": len([u for u in users if u.is_pending]),
            "admin_users": len([u for u in users if u.is_admin]),
            "power_users": len([u for u in users if u.is_poweruser]),
            "regular_users": len([u for u in users if u.is_user]),
            "total_storage_gb": sum(u.storage_used_gb for u in users)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para WorkDocs."""
        recommendations = []
        users = self.get_users()

        inactive_users = [u for u in users if u.is_inactive]
        if inactive_users:
            recommendations.append({
                "resource_type": "WorkDocsUser",
                "resource_id": "multiple",
                "recommendation": "Remover usuários inativos",
                "description": f"{len(inactive_users)} usuário(s) inativo(s). "
                               "Considerar remover para economizar em licenças.",
                "priority": "medium"
            })

        return recommendations
