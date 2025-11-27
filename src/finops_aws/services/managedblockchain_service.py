"""
AWS Managed Blockchain Service para FinOps.

Análise de custos e otimização de blockchain.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class ManagedBlockchainNetwork:
    """Network Managed Blockchain."""
    network_id: str
    name: str = ""
    description: str = ""
    framework: str = "HYPERLEDGER_FABRIC"
    framework_version: str = ""
    status: str = "AVAILABLE"
    voting_policy: Dict[str, Any] = field(default_factory=dict)
    creation_date: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    arn: str = ""

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.status == "AVAILABLE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "CREATING"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.status == "DELETING"

    @property
    def is_deleted(self) -> bool:
        """Verifica se foi deletado."""
        return self.status == "DELETED"

    @property
    def uses_fabric(self) -> bool:
        """Verifica se usa Hyperledger Fabric."""
        return self.framework == "HYPERLEDGER_FABRIC"

    @property
    def uses_ethereum(self) -> bool:
        """Verifica se usa Ethereum."""
        return self.framework == "ETHEREUM"

    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return len(self.tags) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "network_id": self.network_id,
            "name": self.name,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "status": self.status,
            "is_available": self.is_available,
            "uses_fabric": self.uses_fabric,
            "uses_ethereum": self.uses_ethereum,
            "has_tags": self.has_tags,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass
class ManagedBlockchainMember:
    """Member Managed Blockchain."""
    member_id: str
    network_id: str = ""
    name: str = ""
    description: str = ""
    status: str = "AVAILABLE"
    creation_date: Optional[datetime] = None
    is_owned: bool = False
    kms_key_arn: str = ""
    log_publishing_configuration: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    arn: str = ""

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.status == "AVAILABLE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "CREATING"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.status == "DELETING"

    @property
    def is_deleted(self) -> bool:
        """Verifica se foi deletado."""
        return self.status == "DELETED"

    @property
    def is_updating(self) -> bool:
        """Verifica se está atualizando."""
        return self.status == "UPDATING"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_key_arn)

    @property
    def has_logging(self) -> bool:
        """Verifica se tem logging."""
        return len(self.log_publishing_configuration) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "member_id": self.member_id,
            "network_id": self.network_id,
            "name": self.name,
            "status": self.status,
            "is_available": self.is_available,
            "is_owned": self.is_owned,
            "has_encryption": self.has_encryption,
            "has_logging": self.has_logging,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass
class ManagedBlockchainNode:
    """Node Managed Blockchain."""
    node_id: str
    network_id: str = ""
    member_id: str = ""
    instance_type: str = "bc.t3.small"
    availability_zone: str = ""
    framework_attributes: Dict[str, Any] = field(default_factory=dict)
    log_publishing_configuration: Dict[str, Any] = field(default_factory=dict)
    state_db: str = "LevelDB"
    status: str = "AVAILABLE"
    creation_date: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    kms_key_arn: str = ""
    arn: str = ""

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.status == "AVAILABLE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "CREATING"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.status == "DELETING"

    @property
    def is_deleted(self) -> bool:
        """Verifica se foi deletado."""
        return self.status == "DELETED"

    @property
    def is_updating(self) -> bool:
        """Verifica se está atualizando."""
        return self.status == "UPDATING"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def uses_level_db(self) -> bool:
        """Verifica se usa LevelDB."""
        return self.state_db == "LevelDB"

    @property
    def uses_couch_db(self) -> bool:
        """Verifica se usa CouchDB."""
        return self.state_db == "CouchDB"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_key_arn)

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado."""
        size_costs = {
            'small': 0.10, 'medium': 0.20, 'large': 0.40,
            'xlarge': 0.80, '2xlarge': 1.60
        }
        for size, cost in size_costs.items():
            if size in self.instance_type:
                return cost
        return 0.10

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "node_id": self.node_id,
            "network_id": self.network_id,
            "member_id": self.member_id,
            "instance_type": self.instance_type,
            "status": self.status,
            "is_available": self.is_available,
            "state_db": self.state_db,
            "has_encryption": self.has_encryption,
            "estimated_hourly_cost": self.estimated_hourly_cost,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


class ManagedBlockchainService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Managed Blockchain."""

    def __init__(self, client_factory):
        """Inicializa o serviço Managed Blockchain."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._blockchain_client = None

    @property
    def blockchain_client(self):
        """Cliente Managed Blockchain com lazy loading."""
        if self._blockchain_client is None:
            self._blockchain_client = self._client_factory.get_client('managedblockchain')
        return self._blockchain_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Managed Blockchain."""
        try:
            self.blockchain_client.list_networks(MaxResults=1)
            return {
                "service": "managedblockchain",
                "status": "healthy",
                "message": "Managed Blockchain service is accessible"
            }
        except Exception as e:
            return {
                "service": "managedblockchain",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_networks(self) -> List[ManagedBlockchainNetwork]:
        """Lista networks."""
        networks = []
        try:
            paginator = self.blockchain_client.get_paginator('list_networks')
            for page in paginator.paginate():
                for net in page.get('Networks', []):
                    networks.append(ManagedBlockchainNetwork(
                        network_id=net.get('Id', ''),
                        name=net.get('Name', ''),
                        description=net.get('Description', ''),
                        framework=net.get('Framework', 'HYPERLEDGER_FABRIC'),
                        framework_version=net.get('FrameworkVersion', ''),
                        status=net.get('Status', 'AVAILABLE'),
                        creation_date=net.get('CreationDate'),
                        arn=net.get('Arn', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar networks: {e}")
        return networks

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Managed Blockchain."""
        networks = self.get_networks()

        return {
            "networks": [n.to_dict() for n in networks],
            "summary": {
                "total_networks": len(networks),
                "available_networks": len([n for n in networks if n.is_available]),
                "fabric_networks": len([n for n in networks if n.uses_fabric]),
                "ethereum_networks": len([n for n in networks if n.uses_ethereum])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Managed Blockchain."""
        networks = self.get_networks()

        return {
            "networks_count": len(networks),
            "available_networks": len([n for n in networks if n.is_available]),
            "creating_networks": len([n for n in networks if n.is_creating]),
            "fabric_networks": len([n for n in networks if n.uses_fabric]),
            "ethereum_networks": len([n for n in networks if n.uses_ethereum])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Managed Blockchain."""
        return []
