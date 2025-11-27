"""
AWS Braket Service para FinOps.

Análise de custos e otimização de computação quântica.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class BraketQuantumTask:
    """Quantum Task Braket."""
    quantum_task_arn: str
    device_arn: str = ""
    device_parameters: Dict[str, Any] = field(default_factory=dict)
    shots: int = 0
    status: str = "CREATED"
    failure_reason: str = ""
    output_s3_bucket: str = ""
    output_s3_directory: str = ""
    created_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    queue_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_created(self) -> bool:
        """Verifica se foi criado."""
        return self.status == "CREATED"

    @property
    def is_queued(self) -> bool:
        """Verifica se está na fila."""
        return self.status == "QUEUED"

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.status == "RUNNING"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "COMPLETED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def is_cancelling(self) -> bool:
        """Verifica se está cancelando."""
        return self.status == "CANCELLING"

    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "CANCELLED"

    @property
    def has_failure(self) -> bool:
        """Verifica se tem falha."""
        return bool(self.failure_reason)

    @property
    def queue_position(self) -> str:
        """Posição na fila."""
        return self.queue_info.get('position', '')

    @property
    def queue_priority(self) -> str:
        """Prioridade na fila."""
        return self.queue_info.get('queuePriority', '')

    @property
    def uses_ionq(self) -> bool:
        """Verifica se usa IonQ."""
        return "ionq" in self.device_arn.lower()

    @property
    def uses_rigetti(self) -> bool:
        """Verifica se usa Rigetti."""
        return "rigetti" in self.device_arn.lower()

    @property
    def uses_simulator(self) -> bool:
        """Verifica se usa simulador."""
        return "simulator" in self.device_arn.lower()

    @property
    def uses_dwave(self) -> bool:
        """Verifica se usa D-Wave."""
        return "d-wave" in self.device_arn.lower() or "dwave" in self.device_arn.lower()

    @property
    def estimated_cost(self) -> float:
        """Custo estimado por shot."""
        if self.uses_simulator:
            return 0.0 + self.shots * 0.0001
        elif self.uses_ionq:
            return 0.30 + self.shots * 0.01
        elif self.uses_rigetti:
            return 0.30 + self.shots * 0.00035
        elif self.uses_dwave:
            return 0.30 + self.shots * 0.00019
        return 0.30

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "quantum_task_arn": self.quantum_task_arn,
            "device_arn": self.device_arn,
            "shots": self.shots,
            "status": self.status,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "uses_simulator": self.uses_simulator,
            "uses_ionq": self.uses_ionq,
            "uses_rigetti": self.uses_rigetti,
            "estimated_cost": self.estimated_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class BraketJob:
    """Job Braket."""
    job_arn: str
    job_name: str = ""
    status: str = "CREATED"
    device_config: Dict[str, Any] = field(default_factory=dict)
    algorithm_specification: Dict[str, Any] = field(default_factory=dict)
    output_data_config: Dict[str, Any] = field(default_factory=dict)
    instance_config: Dict[str, Any] = field(default_factory=dict)
    role_arn: str = ""
    stopping_condition: Dict[str, int] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    failure_reason: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    billable_duration: int = 0

    @property
    def is_created(self) -> bool:
        """Verifica se foi criado."""
        return self.status == "CREATED"

    @property
    def is_queued(self) -> bool:
        """Verifica se está na fila."""
        return self.status == "QUEUED"

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.status == "RUNNING"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "COMPLETED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def is_cancelling(self) -> bool:
        """Verifica se está cancelando."""
        return self.status == "CANCELLING"

    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "CANCELLED"

    @property
    def has_failure(self) -> bool:
        """Verifica se tem falha."""
        return bool(self.failure_reason)

    @property
    def instance_type(self) -> str:
        """Tipo de instância."""
        return self.instance_config.get('instanceType', '')

    @property
    def instance_count(self) -> int:
        """Número de instâncias."""
        return self.instance_config.get('instanceCount', 1)

    @property
    def volume_size_gb(self) -> int:
        """Tamanho do volume em GB."""
        return self.instance_config.get('volumeSizeInGb', 0)

    @property
    def max_runtime_seconds(self) -> int:
        """Tempo máximo de execução em segundos."""
        return self.stopping_condition.get('maxRuntimeInSeconds', 0)

    @property
    def billable_hours(self) -> float:
        """Horas faturáveis."""
        return self.billable_duration / 3600

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_arn": self.job_arn,
            "job_name": self.job_name,
            "status": self.status,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "instance_type": self.instance_type,
            "instance_count": self.instance_count,
            "billable_hours": self.billable_hours,
            "has_failure": self.has_failure,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class BraketService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Braket."""

    def __init__(self, client_factory):
        """Inicializa o serviço Braket."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._braket_client = None

    @property
    def braket_client(self):
        """Cliente Braket com lazy loading."""
        if self._braket_client is None:
            self._braket_client = self._client_factory.get_client('braket')
        return self._braket_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Braket."""
        try:
            self.braket_client.search_quantum_tasks(filters=[])
            return {
                "service": "braket",
                "status": "healthy",
                "message": "Braket service is accessible"
            }
        except Exception as e:
            return {
                "service": "braket",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_quantum_tasks(self) -> List[BraketQuantumTask]:
        """Lista quantum tasks."""
        tasks = []
        try:
            paginator = self.braket_client.get_paginator('search_quantum_tasks')
            for page in paginator.paginate(filters=[]):
                for task in page.get('quantumTasks', []):
                    tasks.append(BraketQuantumTask(
                        quantum_task_arn=task.get('quantumTaskArn', ''),
                        device_arn=task.get('deviceArn', ''),
                        shots=task.get('shots', 0),
                        status=task.get('status', 'CREATED'),
                        output_s3_bucket=task.get('outputS3Bucket', ''),
                        output_s3_directory=task.get('outputS3Directory', ''),
                        created_at=task.get('createdAt'),
                        ended_at=task.get('endedAt'),
                        tags=task.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar quantum tasks: {e}")
        return tasks

    def get_jobs(self) -> List[BraketJob]:
        """Lista jobs."""
        jobs = []
        try:
            paginator = self.braket_client.get_paginator('search_jobs')
            for page in paginator.paginate(filters=[]):
                for job in page.get('jobs', []):
                    jobs.append(BraketJob(
                        job_arn=job.get('jobArn', ''),
                        job_name=job.get('jobName', ''),
                        status=job.get('status', 'CREATED'),
                        created_at=job.get('createdAt'),
                        started_at=job.get('startedAt'),
                        ended_at=job.get('endedAt'),
                        tags=job.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs: {e}")
        return jobs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Braket."""
        tasks = self.get_quantum_tasks()
        jobs = self.get_jobs()

        return {
            "quantum_tasks": [t.to_dict() for t in tasks[:100]],
            "jobs": [j.to_dict() for j in jobs],
            "summary": {
                "total_quantum_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if t.is_completed]),
                "failed_tasks": len([t for t in tasks if t.is_failed]),
                "running_tasks": len([t for t in tasks if t.is_running]),
                "simulator_tasks": len([t for t in tasks if t.uses_simulator]),
                "ionq_tasks": len([t for t in tasks if t.uses_ionq]),
                "rigetti_tasks": len([t for t in tasks if t.uses_rigetti]),
                "total_jobs": len(jobs),
                "completed_jobs": len([j for j in jobs if j.is_completed]),
                "failed_jobs": len([j for j in jobs if j.is_failed]),
                "estimated_task_cost": sum(t.estimated_cost for t in tasks)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Braket."""
        tasks = self.get_quantum_tasks()
        jobs = self.get_jobs()

        return {
            "quantum_tasks_count": len(tasks),
            "completed_tasks": len([t for t in tasks if t.is_completed]),
            "failed_tasks": len([t for t in tasks if t.is_failed]),
            "running_tasks": len([t for t in tasks if t.is_running]),
            "queued_tasks": len([t for t in tasks if t.is_queued]),
            "simulator_tasks": len([t for t in tasks if t.uses_simulator]),
            "ionq_tasks": len([t for t in tasks if t.uses_ionq]),
            "rigetti_tasks": len([t for t in tasks if t.uses_rigetti]),
            "dwave_tasks": len([t for t in tasks if t.uses_dwave]),
            "jobs_count": len(jobs),
            "completed_jobs": len([j for j in jobs if j.is_completed]),
            "failed_jobs": len([j for j in jobs if j.is_failed]),
            "running_jobs": len([j for j in jobs if j.is_running])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Braket."""
        recommendations = []
        tasks = self.get_quantum_tasks()

        failed_tasks = [t for t in tasks if t.is_failed]
        if len(failed_tasks) > 5:
            recommendations.append({
                "resource_type": "BraketQuantumTask",
                "resource_id": "multiple",
                "recommendation": "Investigar tasks com falha",
                "description": f"{len(failed_tasks)} quantum task(s) com falha. "
                               "Revisar configurações para evitar custos desnecessários.",
                "priority": "medium"
            })

        return recommendations
