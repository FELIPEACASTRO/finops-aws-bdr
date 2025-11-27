"""
AWS Macie FinOps Service.

Análise de custos e métricas do Amazon Macie para descoberta de dados sensíveis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class MacieClassificationJob:
    """Representa um job de classificação Macie."""
    
    job_id: str = ""
    name: str = ""
    job_status: str = ""
    job_type: str = ""
    created_at: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    managed_data_identifier_selector: str = ""
    s3_job_definition: Dict[str, Any] = field(default_factory=dict)
    sampling_percentage: int = 100
    schedule_frequency: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_running(self) -> bool:
        """Verifica se job está rodando."""
        return self.job_status.upper() == "RUNNING"
    
    @property
    def is_paused(self) -> bool:
        """Verifica se job está pausado."""
        return self.job_status.upper() == "PAUSED"
    
    @property
    def is_cancelled(self) -> bool:
        """Verifica se job foi cancelado."""
        return self.job_status.upper() == "CANCELLED"
    
    @property
    def is_complete(self) -> bool:
        """Verifica se job está completo."""
        return self.job_status.upper() == "COMPLETE"
    
    @property
    def is_idle(self) -> bool:
        """Verifica se job está idle."""
        return self.job_status.upper() == "IDLE"
    
    @property
    def is_user_paused(self) -> bool:
        """Verifica se job foi pausado pelo usuário."""
        return self.job_status.upper() == "USER_PAUSED"
    
    @property
    def is_one_time(self) -> bool:
        """Verifica se é job único."""
        return self.job_type.upper() == "ONE_TIME"
    
    @property
    def is_scheduled(self) -> bool:
        """Verifica se é job agendado."""
        return self.job_type.upper() == "SCHEDULED"
    
    @property
    def has_schedule(self) -> bool:
        """Verifica se tem schedule."""
        return bool(self.schedule_frequency)
    
    @property
    def uses_sampling(self) -> bool:
        """Verifica se usa sampling."""
        return self.sampling_percentage < 100
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    @property
    def objects_processed(self) -> int:
        """Retorna quantidade de objetos processados."""
        return self.statistics.get("approximateNumberOfObjectsToProcess", 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "job_status": self.job_status,
            "job_type": self.job_type,
            "is_running": self.is_running,
            "is_scheduled": self.is_scheduled,
            "uses_sampling": self.uses_sampling,
            "sampling_percentage": self.sampling_percentage
        }


@dataclass
class MacieBucket:
    """Representa um bucket S3 monitorado pelo Macie."""
    
    bucket_name: str = ""
    account_id: str = ""
    region: str = ""
    classifiable_object_count: int = 0
    classifiable_size_in_bytes: int = 0
    unclassifiable_object_count: int = 0
    error_code: str = ""
    error_message: str = ""
    job_details: Dict[str, Any] = field(default_factory=dict)
    last_automated_discovery_time: Optional[datetime] = None
    object_count: int = 0
    object_count_by_encryption_type: Dict[str, int] = field(default_factory=dict)
    sensitivity_score: int = 0
    shared_access: str = ""
    size_in_bytes: int = 0
    tags: List[Dict[str, str]] = field(default_factory=list)
    versioning: bool = False
    allows_unencrypted_object_uploads: str = ""
    public_access: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_public(self) -> bool:
        """Verifica se bucket é público."""
        return self.public_access.get("effectivePermission", "").upper() == "PUBLIC"
    
    @property
    def is_not_public(self) -> bool:
        """Verifica se bucket não é público."""
        return self.public_access.get("effectivePermission", "").upper() == "NOT_PUBLIC"
    
    @property
    def has_error(self) -> bool:
        """Verifica se tem erro."""
        return bool(self.error_code)
    
    @property
    def is_shared(self) -> bool:
        """Verifica se bucket é compartilhado."""
        return self.shared_access.upper() in ["EXTERNAL", "INTERNAL"]
    
    @property
    def is_external_shared(self) -> bool:
        """Verifica se bucket é compartilhado externamente."""
        return self.shared_access.upper() == "EXTERNAL"
    
    @property
    def is_internal_shared(self) -> bool:
        """Verifica se bucket é compartilhado internamente."""
        return self.shared_access.upper() == "INTERNAL"
    
    @property
    def is_not_shared(self) -> bool:
        """Verifica se bucket não é compartilhado."""
        return self.shared_access.upper() == "NOT_SHARED"
    
    @property
    def has_unclassifiable_objects(self) -> bool:
        """Verifica se tem objetos não classificáveis."""
        return self.unclassifiable_object_count > 0
    
    @property
    def has_sensitivity(self) -> bool:
        """Verifica se tem sensibilidade."""
        return self.sensitivity_score > 0
    
    @property
    def is_high_sensitivity(self) -> bool:
        """Verifica se tem alta sensibilidade."""
        return self.sensitivity_score >= 50
    
    @property
    def size_in_gb(self) -> float:
        """Retorna tamanho em GB."""
        return self.size_in_bytes / (1024 ** 3)
    
    @property
    def allows_unencrypted(self) -> bool:
        """Verifica se permite uploads não criptografados."""
        return self.allows_unencrypted_object_uploads.upper() == "TRUE"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "bucket_name": self.bucket_name,
            "account_id": self.account_id,
            "region": self.region,
            "is_public": self.is_public,
            "is_shared": self.is_shared,
            "has_sensitivity": self.has_sensitivity,
            "sensitivity_score": self.sensitivity_score,
            "object_count": self.object_count,
            "size_in_gb": round(self.size_in_gb, 2)
        }


@dataclass
class MacieFinding:
    """Representa um finding Macie."""
    
    id: str = ""
    type: str = ""
    category: str = ""
    severity: Dict[str, Any] = field(default_factory=dict)
    title: str = ""
    description: str = ""
    archived: bool = False
    count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resources_affected: Dict[str, Any] = field(default_factory=dict)
    classification_details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def severity_score(self) -> float:
        """Retorna score de severidade."""
        return self.severity.get("score", 0.0)
    
    @property
    def severity_description(self) -> str:
        """Retorna descrição de severidade."""
        return self.severity.get("description", "Low")
    
    @property
    def is_high_severity(self) -> bool:
        """Verifica se é alta severidade."""
        return self.severity_score >= 7.0
    
    @property
    def is_medium_severity(self) -> bool:
        """Verifica se é média severidade."""
        return 4.0 <= self.severity_score < 7.0
    
    @property
    def is_low_severity(self) -> bool:
        """Verifica se é baixa severidade."""
        return self.severity_score < 4.0
    
    @property
    def is_archived(self) -> bool:
        """Verifica se está arquivado."""
        return bool(self.archived)
    
    @property
    def is_policy_finding(self) -> bool:
        """Verifica se é finding de policy."""
        return self.category.upper() == "POLICY"
    
    @property
    def is_sensitive_data_finding(self) -> bool:
        """Verifica se é finding de dados sensíveis."""
        return self.category.upper() == "CLASSIFICATION"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "type": self.type,
            "category": self.category,
            "title": self.title,
            "severity_score": self.severity_score,
            "is_high_severity": self.is_high_severity,
            "is_archived": self.is_archived
        }


class MacieService(BaseAWSService):
    """Serviço FinOps para Amazon Macie."""

    def __init__(self, client_factory):
        """Inicializa o serviço Macie."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente Macie."""
        return self._client_factory.get_client("macie2")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.get_macie_session()
            return {"status": "healthy", "service": "macie"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "macie", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos Macie."""
        client = self._get_client()
        
        jobs = self._list_jobs(client)
        buckets = self._list_buckets(client)
        
        running_jobs = [j for j in jobs if j.is_running]
        scheduled_jobs = [j for j in jobs if j.is_scheduled]
        public_buckets = [b for b in buckets if b.is_public]
        sensitive_buckets = [b for b in buckets if b.has_sensitivity]
        
        return {
            "classification_jobs": [j.to_dict() for j in jobs],
            "buckets": [b.to_dict() for b in buckets],
            "summary": {
                "total_jobs": len(jobs),
                "running_jobs": len(running_jobs),
                "scheduled_jobs": len(scheduled_jobs),
                "total_buckets": len(buckets),
                "public_buckets": len(public_buckets),
                "sensitive_buckets": len(sensitive_buckets)
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos Macie."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        buckets_cost = summary["total_buckets"] * 0.10
        
        return {
            "estimated_monthly": buckets_cost,
            "cost_factors": {
                "bucket_evaluation": "$0.10 per bucket per month",
                "sensitive_data_discovery": "$1.00 per GB first 50k GB",
                "automated_discovery": "Varies by data volume"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas Macie."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "jobs_count": summary["total_jobs"],
            "running_jobs": summary["running_jobs"],
            "scheduled_jobs": summary["scheduled_jobs"],
            "buckets_count": summary["total_buckets"],
            "public_buckets": summary["public_buckets"],
            "sensitive_buckets": summary["sensitive_buckets"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de segurança."""
        recommendations = []
        resources = self.get_resources()
        
        for bucket in resources["buckets"]:
            if bucket.get("is_public"):
                recommendations.append({
                    "type": "FIX_PUBLIC_BUCKET",
                    "resource": bucket["bucket_name"],
                    "description": f"Bucket '{bucket['bucket_name']}' é público",
                    "impact": "critical",
                    "action": "Revisar e restringir acesso público"
                })
            
            if bucket.get("is_high_sensitivity", bucket.get("sensitivity_score", 0) >= 50):
                recommendations.append({
                    "type": "PROTECT_SENSITIVE_DATA",
                    "resource": bucket["bucket_name"],
                    "description": f"Bucket '{bucket['bucket_name']}' contém dados sensíveis",
                    "impact": "high",
                    "action": "Revisar classificação e proteger dados"
                })
        
        return recommendations

    def _list_jobs(self, client) -> List[MacieClassificationJob]:
        """Lista jobs de classificação."""
        jobs = []
        try:
            paginator = client.get_paginator("list_classification_jobs")
            for page in paginator.paginate():
                for job in page.get("items", []):
                    jobs.append(MacieClassificationJob(
                        job_id=job.get("jobId", ""),
                        name=job.get("name", ""),
                        job_status=job.get("jobStatus", ""),
                        job_type=job.get("jobType", ""),
                        created_at=job.get("createdAt")
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing classification jobs: {e}")
        return jobs

    def _list_buckets(self, client) -> List[MacieBucket]:
        """Lista buckets monitorados."""
        buckets = []
        try:
            paginator = client.get_paginator("describe_buckets")
            for page in paginator.paginate():
                for bucket in page.get("buckets", []):
                    buckets.append(MacieBucket(
                        bucket_name=bucket.get("bucketName", ""),
                        account_id=bucket.get("accountId", ""),
                        region=bucket.get("region", ""),
                        classifiable_object_count=bucket.get("classifiableObjectCount", 0),
                        classifiable_size_in_bytes=bucket.get("classifiableSizeInBytes", 0),
                        object_count=bucket.get("objectCount", 0),
                        sensitivity_score=bucket.get("sensitivityScore", 0),
                        shared_access=bucket.get("sharedAccess", ""),
                        size_in_bytes=bucket.get("sizeInBytes", 0),
                        public_access=bucket.get("publicAccess", {})
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing buckets: {e}")
        return buckets
