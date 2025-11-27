"""
AWS Snow Family Service para FinOps.

Análise de custos e otimização de jobs Snowball/Snowcone.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class SnowballJob:
    """Snowball Job."""
    job_id: str
    job_state: str = "New"
    job_type: str = "IMPORT"
    snowball_type: str = "STANDARD"
    creation_date: Optional[datetime] = None
    description: str = ""
    kms_key_arn: str = ""
    role_arn: str = ""
    shipping_details: Dict[str, Any] = field(default_factory=dict)
    snowball_capacity_preference: str = "T80"
    resources: Dict[str, Any] = field(default_factory=dict)
    cluster_id: str = ""
    forwarding_address_id: str = ""
    tax_documents: Dict[str, Any] = field(default_factory=dict)
    device_configuration: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_new(self) -> bool:
        """Verifica se é novo."""
        return self.job_state == "New"

    @property
    def is_preparing_appliance(self) -> bool:
        """Verifica se está preparando appliance."""
        return self.job_state == "PreparingAppliance"

    @property
    def is_preparing_shipment(self) -> bool:
        """Verifica se está preparando envio."""
        return self.job_state == "PreparingShipment"

    @property
    def is_in_transit_to_customer(self) -> bool:
        """Verifica se está em trânsito para cliente."""
        return self.job_state == "InTransitToCustomer"

    @property
    def is_with_customer(self) -> bool:
        """Verifica se está com cliente."""
        return self.job_state == "WithCustomer"

    @property
    def is_in_transit_to_aws(self) -> bool:
        """Verifica se está em trânsito para AWS."""
        return self.job_state == "InTransitToAWS"

    @property
    def is_with_aws(self) -> bool:
        """Verifica se está com AWS."""
        return self.job_state == "WithAWS" or self.job_state == "WithAWSSortingFacility"

    @property
    def is_complete(self) -> bool:
        """Verifica se está completo."""
        return self.job_state == "Complete"

    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.job_state == "Cancelled"

    @property
    def is_listing(self) -> bool:
        """Verifica se está listando."""
        return self.job_state == "Listing"

    @property
    def is_import_job(self) -> bool:
        """Verifica se é job de importação."""
        return self.job_type == "IMPORT"

    @property
    def is_export_job(self) -> bool:
        """Verifica se é job de exportação."""
        return self.job_type == "EXPORT"

    @property
    def is_local_use(self) -> bool:
        """Verifica se é uso local."""
        return self.job_type == "LOCAL_USE"

    @property
    def is_snowball_edge(self) -> bool:
        """Verifica se é Snowball Edge."""
        return self.snowball_type.startswith("EDGE")

    @property
    def is_snowcone(self) -> bool:
        """Verifica se é Snowcone."""
        return self.snowball_type.startswith("SNC")

    @property
    def is_standard_snowball(self) -> bool:
        """Verifica se é Snowball padrão."""
        return self.snowball_type == "STANDARD"

    @property
    def capacity_tb(self) -> int:
        """Capacidade em TB."""
        capacity_map = {
            'T50': 50, 'T80': 80, 'T100': 100,
            'T42': 42, 'T98': 98,
            'SNC1_HDD': 8, 'SNC1_SSD': 14
        }
        return capacity_map.get(self.snowball_capacity_preference, 80)

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_key_arn)

    @property
    def is_cluster_job(self) -> bool:
        """Verifica se é job de cluster."""
        return bool(self.cluster_id)

    @property
    def estimated_cost(self) -> float:
        """Custo estimado do job."""
        if self.is_snowcone:
            return 100.0
        elif self.is_snowball_edge:
            return 300.0 if "STORAGE" in self.snowball_type else 400.0
        return 250.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "job_state": self.job_state,
            "job_type": self.job_type,
            "snowball_type": self.snowball_type,
            "is_complete": self.is_complete,
            "is_cancelled": self.is_cancelled,
            "is_with_customer": self.is_with_customer,
            "is_import_job": self.is_import_job,
            "is_export_job": self.is_export_job,
            "capacity_tb": self.capacity_tb,
            "has_encryption": self.has_encryption,
            "is_cluster_job": self.is_cluster_job,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass
class SnowballCluster:
    """Snowball Cluster."""
    cluster_id: str
    cluster_state: str = "AwaitingQuorum"
    job_type: str = "LOCAL_USE"
    snowball_type: str = "EDGE"
    creation_date: Optional[datetime] = None
    description: str = ""
    kms_key_arn: str = ""
    role_arn: str = ""
    address_id: str = ""
    resources: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_awaiting_quorum(self) -> bool:
        """Verifica se aguarda quórum."""
        return self.cluster_state == "AwaitingQuorum"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.cluster_state == "Pending"

    @property
    def is_in_use(self) -> bool:
        """Verifica se está em uso."""
        return self.cluster_state == "InUse"

    @property
    def is_complete(self) -> bool:
        """Verifica se está completo."""
        return self.cluster_state == "Complete"

    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.cluster_state == "Cancelled"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_key_arn)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "cluster_id": self.cluster_id,
            "cluster_state": self.cluster_state,
            "job_type": self.job_type,
            "snowball_type": self.snowball_type,
            "is_in_use": self.is_in_use,
            "is_complete": self.is_complete,
            "has_encryption": self.has_encryption,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


class SnowFamilyService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Snow Family."""

    def __init__(self, client_factory):
        """Inicializa o serviço Snow Family."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._snowball_client = None

    @property
    def snowball_client(self):
        """Cliente Snowball com lazy loading."""
        if self._snowball_client is None:
            self._snowball_client = self._client_factory.get_client('snowball')
        return self._snowball_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Snow Family."""
        try:
            self.snowball_client.list_jobs(MaxResults=1)
            return {
                "service": "snowfamily",
                "status": "healthy",
                "message": "Snow Family service is accessible"
            }
        except Exception as e:
            return {
                "service": "snowfamily",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_jobs(self) -> List[SnowballJob]:
        """Lista jobs."""
        jobs = []
        try:
            paginator = self.snowball_client.get_paginator('list_jobs')
            for page in paginator.paginate():
                for entry in page.get('JobListEntries', []):
                    jobs.append(SnowballJob(
                        job_id=entry.get('JobId', ''),
                        job_state=entry.get('JobState', 'New'),
                        job_type=entry.get('JobType', 'IMPORT'),
                        snowball_type=entry.get('SnowballType', 'STANDARD'),
                        creation_date=entry.get('CreationDate'),
                        description=entry.get('Description', ''),
                        is_master=entry.get('IsMaster', False)
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs: {e}")
        return jobs

    def get_clusters(self) -> List[SnowballCluster]:
        """Lista clusters."""
        clusters = []
        try:
            paginator = self.snowball_client.get_paginator('list_clusters')
            for page in paginator.paginate():
                for entry in page.get('ClusterListEntries', []):
                    clusters.append(SnowballCluster(
                        cluster_id=entry.get('ClusterId', ''),
                        cluster_state=entry.get('ClusterState', 'AwaitingQuorum'),
                        creation_date=entry.get('CreationDate'),
                        description=entry.get('Description', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar clusters: {e}")
        return clusters

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Snow Family."""
        jobs = self.get_jobs()
        clusters = self.get_clusters()

        active_jobs = [j for j in jobs if not j.is_complete and not j.is_cancelled]

        return {
            "jobs": [j.to_dict() for j in jobs],
            "clusters": [c.to_dict() for c in clusters],
            "summary": {
                "total_jobs": len(jobs),
                "active_jobs": len(active_jobs),
                "complete_jobs": len([j for j in jobs if j.is_complete]),
                "cancelled_jobs": len([j for j in jobs if j.is_cancelled]),
                "import_jobs": len([j for j in jobs if j.is_import_job]),
                "export_jobs": len([j for j in jobs if j.is_export_job]),
                "local_use_jobs": len([j for j in jobs if j.is_local_use]),
                "with_customer": len([j for j in active_jobs if j.is_with_customer]),
                "in_transit": len([j for j in active_jobs if j.is_in_transit_to_customer or j.is_in_transit_to_aws]),
                "total_clusters": len(clusters),
                "active_clusters": len([c for c in clusters if c.is_in_use]),
                "estimated_active_cost": sum(j.estimated_cost for j in active_jobs)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Snow Family."""
        jobs = self.get_jobs()
        clusters = self.get_clusters()

        return {
            "total_jobs": len(jobs),
            "new_jobs": len([j for j in jobs if j.is_new]),
            "preparing_jobs": len([j for j in jobs if j.is_preparing_appliance or j.is_preparing_shipment]),
            "with_customer": len([j for j in jobs if j.is_with_customer]),
            "in_transit": len([j for j in jobs if j.is_in_transit_to_customer or j.is_in_transit_to_aws]),
            "complete_jobs": len([j for j in jobs if j.is_complete]),
            "cancelled_jobs": len([j for j in jobs if j.is_cancelled]),
            "import_jobs": len([j for j in jobs if j.is_import_job]),
            "export_jobs": len([j for j in jobs if j.is_export_job]),
            "snowball_edge_jobs": len([j for j in jobs if j.is_snowball_edge]),
            "snowcone_jobs": len([j for j in jobs if j.is_snowcone]),
            "encrypted_jobs": len([j for j in jobs if j.has_encryption]),
            "cluster_jobs": len([j for j in jobs if j.is_cluster_job]),
            "total_clusters": len(clusters),
            "active_clusters": len([c for c in clusters if c.is_in_use])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Snow Family."""
        recommendations = []
        jobs = self.get_jobs()

        no_encryption = [j for j in jobs if not j.has_encryption and not j.is_complete and not j.is_cancelled]
        if no_encryption:
            recommendations.append({
                "resource_type": "SnowballJob",
                "resource_id": "multiple",
                "recommendation": "Usar criptografia KMS",
                "description": f"{len(no_encryption)} job(s) ativo(s) sem criptografia KMS. "
                               "Usar criptografia para dados sensíveis.",
                "priority": "high"
            })

        long_with_customer = [j for j in jobs if j.is_with_customer]
        if len(long_with_customer) > 3:
            recommendations.append({
                "resource_type": "SnowballJob",
                "resource_id": "multiple",
                "recommendation": "Retornar dispositivos",
                "description": f"{len(long_with_customer)} dispositivo(s) com cliente. "
                               "Verificar se transferência foi concluída para evitar cobranças extras.",
                "priority": "medium"
            })

        return recommendations
