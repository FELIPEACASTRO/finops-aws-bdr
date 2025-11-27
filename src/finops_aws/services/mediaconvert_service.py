"""
AWS MediaConvert Service para FinOps.

Análise de custos e otimização de jobs de transcodificação.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class MediaConvertJob:
    """Job MediaConvert."""
    job_id: str
    arn: str = ""
    status: str = "SUBMITTED"
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    queue: str = ""
    role: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    user_metadata: Dict[str, str] = field(default_factory=dict)
    billing_tags_source: str = "QUEUE"
    error_code: int = 0
    error_message: str = ""

    @property
    def is_complete(self) -> bool:
        """Verifica se está completo."""
        return self.status == "COMPLETE"

    @property
    def is_submitted(self) -> bool:
        """Verifica se foi submetido."""
        return self.status == "SUBMITTED"

    @property
    def is_progressing(self) -> bool:
        """Verifica se está em progresso."""
        return self.status == "PROGRESSING"

    @property
    def is_error(self) -> bool:
        """Verifica se teve erro."""
        return self.status == "ERROR"

    @property
    def is_canceled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "CANCELED"

    @property
    def has_error(self) -> bool:
        """Verifica se tem mensagem de erro."""
        return bool(self.error_message)

    @property
    def output_groups_count(self) -> int:
        """Número de grupos de saída."""
        return len(self.settings.get('OutputGroups', []))

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "arn": self.arn,
            "status": self.status,
            "is_complete": self.is_complete,
            "is_error": self.is_error,
            "queue": self.queue,
            "output_groups_count": self.output_groups_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None
        }


@dataclass
class MediaConvertQueue:
    """Queue MediaConvert."""
    name: str
    arn: str = ""
    status: str = "ACTIVE"
    description: str = ""
    type: str = "ON_DEMAND"
    pricing_plan: str = "ON_DEMAND"
    submitted_jobs_count: int = 0
    progressing_jobs_count: int = 0
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    reservation_plan_settings: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_paused(self) -> bool:
        """Verifica se está pausado."""
        return self.status == "PAUSED"

    @property
    def is_on_demand(self) -> bool:
        """Verifica se é on-demand."""
        return self.pricing_plan == "ON_DEMAND"

    @property
    def is_reserved(self) -> bool:
        """Verifica se é reservado."""
        return self.pricing_plan == "RESERVED"

    @property
    def has_reserved_slots(self) -> bool:
        """Verifica se tem slots reservados."""
        return bool(self.reservation_plan_settings)

    @property
    def reserved_slots(self) -> int:
        """Número de slots reservados."""
        return self.reservation_plan_settings.get('ReservedSlots', 0)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "status": self.status,
            "is_active": self.is_active,
            "is_on_demand": self.is_on_demand,
            "is_reserved": self.is_reserved,
            "submitted_jobs_count": self.submitted_jobs_count,
            "progressing_jobs_count": self.progressing_jobs_count,
            "reserved_slots": self.reserved_slots
        }


@dataclass  
class MediaConvertPreset:
    """Preset MediaConvert."""
    name: str
    arn: str = ""
    description: str = ""
    category: str = ""
    type: str = "CUSTOM"
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    settings: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_custom(self) -> bool:
        """Verifica se é customizado."""
        return self.type == "CUSTOM"

    @property
    def is_system(self) -> bool:
        """Verifica se é do sistema."""
        return self.type == "SYSTEM"

    @property
    def has_video_settings(self) -> bool:
        """Verifica se tem configurações de vídeo."""
        return 'VideoDescription' in self.settings

    @property
    def has_audio_settings(self) -> bool:
        """Verifica se tem configurações de áudio."""
        return 'AudioDescriptions' in self.settings

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "description": self.description,
            "category": self.category,
            "is_custom": self.is_custom,
            "is_system": self.is_system,
            "has_video_settings": self.has_video_settings,
            "has_audio_settings": self.has_audio_settings
        }


class MediaConvertService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS MediaConvert."""

    def __init__(self, client_factory):
        """Inicializa o serviço MediaConvert."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._mediaconvert_client = None

    @property
    def mediaconvert_client(self):
        """Cliente MediaConvert com lazy loading."""
        if self._mediaconvert_client is None:
            self._mediaconvert_client = self._client_factory.get_client('mediaconvert')
        return self._mediaconvert_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço MediaConvert."""
        try:
            self.mediaconvert_client.list_queues(MaxResults=1)
            return {
                "service": "mediaconvert",
                "status": "healthy",
                "message": "MediaConvert service is accessible"
            }
        except Exception as e:
            return {
                "service": "mediaconvert",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_queues(self) -> List[MediaConvertQueue]:
        """Lista queues."""
        queues = []
        try:
            paginator = self.mediaconvert_client.get_paginator('list_queues')
            for page in paginator.paginate():
                for queue in page.get('Queues', []):
                    queues.append(MediaConvertQueue(
                        name=queue.get('Name', ''),
                        arn=queue.get('Arn', ''),
                        status=queue.get('Status', 'ACTIVE'),
                        description=queue.get('Description', ''),
                        type=queue.get('Type', 'ON_DEMAND'),
                        pricing_plan=queue.get('PricingPlan', 'ON_DEMAND'),
                        submitted_jobs_count=queue.get('SubmittedJobsCount', 0),
                        progressing_jobs_count=queue.get('ProgressingJobsCount', 0),
                        created_at=queue.get('CreatedAt'),
                        last_updated=queue.get('LastUpdated'),
                        reservation_plan_settings=queue.get('ReservationPlanSettings', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar queues: {e}")
        return queues

    def get_jobs(self, max_results: int = 50) -> List[MediaConvertJob]:
        """Lista jobs recentes."""
        jobs = []
        try:
            response = self.mediaconvert_client.list_jobs(MaxResults=min(max_results, 20))
            for job in response.get('Jobs', []):
                jobs.append(MediaConvertJob(
                    job_id=job.get('Id', ''),
                    arn=job.get('Arn', ''),
                    status=job.get('Status', 'SUBMITTED'),
                    created_at=job.get('CreatedAt'),
                    finished_at=job.get('FinishedAt'),
                    queue=job.get('Queue', ''),
                    role=job.get('Role', ''),
                    settings=job.get('Settings', {}),
                    user_metadata=job.get('UserMetadata', {}),
                    error_code=job.get('ErrorCode', 0),
                    error_message=job.get('ErrorMessage', '')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs: {e}")
        return jobs

    def get_presets(self) -> List[MediaConvertPreset]:
        """Lista presets customizados."""
        presets = []
        try:
            paginator = self.mediaconvert_client.get_paginator('list_presets')
            for page in paginator.paginate():
                for preset in page.get('Presets', []):
                    presets.append(MediaConvertPreset(
                        name=preset.get('Name', ''),
                        arn=preset.get('Arn', ''),
                        description=preset.get('Description', ''),
                        category=preset.get('Category', ''),
                        type=preset.get('Type', 'CUSTOM'),
                        created_at=preset.get('CreatedAt'),
                        last_updated=preset.get('LastUpdated'),
                        settings=preset.get('Settings', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar presets: {e}")
        return presets

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos MediaConvert."""
        queues = self.get_queues()
        jobs = self.get_jobs()
        presets = self.get_presets()

        return {
            "queues": [q.to_dict() for q in queues],
            "jobs": [j.to_dict() for j in jobs],
            "presets": [p.to_dict() for p in presets],
            "summary": {
                "total_queues": len(queues),
                "active_queues": len([q for q in queues if q.is_active]),
                "on_demand_queues": len([q for q in queues if q.is_on_demand]),
                "reserved_queues": len([q for q in queues if q.is_reserved]),
                "total_jobs_sampled": len(jobs),
                "complete_jobs": len([j for j in jobs if j.is_complete]),
                "error_jobs": len([j for j in jobs if j.is_error]),
                "total_presets": len(presets),
                "custom_presets": len([p for p in presets if p.is_custom])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do MediaConvert."""
        queues = self.get_queues()
        jobs = self.get_jobs()
        presets = self.get_presets()

        return {
            "queues_count": len(queues),
            "active_queues": len([q for q in queues if q.is_active]),
            "paused_queues": len([q for q in queues if q.is_paused]),
            "on_demand_queues": len([q for q in queues if q.is_on_demand]),
            "reserved_queues": len([q for q in queues if q.is_reserved]),
            "total_reserved_slots": sum(q.reserved_slots for q in queues),
            "jobs_sampled": len(jobs),
            "jobs_complete": len([j for j in jobs if j.is_complete]),
            "jobs_error": len([j for j in jobs if j.is_error]),
            "jobs_progressing": len([j for j in jobs if j.is_progressing]),
            "presets_count": len(presets),
            "custom_presets": len([p for p in presets if p.is_custom])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para MediaConvert."""
        recommendations = []
        queues = self.get_queues()
        jobs = self.get_jobs()

        error_jobs = [j for j in jobs if j.is_error]
        if len(error_jobs) > len(jobs) * 0.1 and len(jobs) > 5:
            recommendations.append({
                "resource_type": "MediaConvertJob",
                "resource_id": "multiple",
                "recommendation": "Investigar jobs com erro",
                "description": f"{len(error_jobs)} job(s) com erro de {len(jobs)} amostrados. "
                               "Verificar configurações e inputs.",
                "priority": "high"
            })

        paused_queues = [q for q in queues if q.is_paused]
        if paused_queues:
            recommendations.append({
                "resource_type": "MediaConvertQueue",
                "resource_id": "multiple",
                "recommendation": "Remover queues pausadas",
                "description": f"{len(paused_queues)} queue(s) pausada(s). "
                               "Considerar remover se não forem mais necessárias.",
                "priority": "low"
            })

        return recommendations
