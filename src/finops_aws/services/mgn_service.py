"""
AWS MGN (Application Migration Service) para FinOps.

Análise de custos e otimização de migrações de aplicações.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class MGNSourceServer:
    """Source Server MGN."""
    source_server_id: str
    arn: str = ""
    is_archived: bool = False
    launched_instance: Dict[str, Any] = field(default_factory=dict)
    life_cycle: Dict[str, Any] = field(default_factory=dict)
    replication_type: str = "AGENT_BASED"
    source_properties: Dict[str, Any] = field(default_factory=dict)
    data_replication_info: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def lifecycle_state(self) -> str:
        """Estado do ciclo de vida."""
        return self.life_cycle.get('state', 'NOT_READY')

    @property
    def is_ready_for_test(self) -> bool:
        """Verifica se está pronto para teste."""
        return self.lifecycle_state == "READY_FOR_TEST"

    @property
    def is_ready_for_cutover(self) -> bool:
        """Verifica se está pronto para cutover."""
        return self.lifecycle_state == "READY_FOR_CUTOVER"

    @property
    def is_cutover(self) -> bool:
        """Verifica se passou por cutover."""
        return self.lifecycle_state == "CUTOVER"

    @property
    def is_disconnected(self) -> bool:
        """Verifica se está desconectado."""
        return self.lifecycle_state == "DISCONNECTED"

    @property
    def is_not_ready(self) -> bool:
        """Verifica se não está pronto."""
        return self.lifecycle_state == "NOT_READY"

    @property
    def has_launched_instance(self) -> bool:
        """Verifica se tem instância lançada."""
        return bool(self.launched_instance)

    @property
    def launched_instance_id(self) -> str:
        """ID da instância lançada."""
        ec2 = self.launched_instance.get('ec2InstanceID', '')
        return ec2

    @property
    def is_agent_based(self) -> bool:
        """Verifica se é baseado em agente."""
        return self.replication_type == "AGENT_BASED"

    @property
    def is_snapshot_shipping(self) -> bool:
        """Verifica se usa snapshot shipping."""
        return self.replication_type == "SNAPSHOT_SHIPPING"

    @property
    def hostname(self) -> str:
        """Hostname do servidor fonte."""
        return self.source_properties.get('identificationHints', {}).get('hostname', '')

    @property
    def replication_state(self) -> str:
        """Estado da replicação."""
        return self.data_replication_info.get('dataReplicationState', 'NOT_STARTED')

    @property
    def is_replicating(self) -> bool:
        """Verifica se está replicando."""
        return self.replication_state == "CONTINUOUS"

    @property
    def is_initial_sync(self) -> bool:
        """Verifica se está em sync inicial."""
        return self.replication_state == "INITIAL_SYNC"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "source_server_id": self.source_server_id,
            "arn": self.arn,
            "is_archived": self.is_archived,
            "lifecycle_state": self.lifecycle_state,
            "is_ready_for_test": self.is_ready_for_test,
            "is_ready_for_cutover": self.is_ready_for_cutover,
            "is_cutover": self.is_cutover,
            "has_launched_instance": self.has_launched_instance,
            "replication_type": self.replication_type,
            "replication_state": self.replication_state,
            "hostname": self.hostname
        }


@dataclass
class MGNJob:
    """Job MGN."""
    job_id: str
    arn: str = ""
    job_type: str = "LAUNCH"
    status: str = "PENDING"
    initiated_by: str = "START_TEST"
    creation_date_time: Optional[datetime] = None
    end_date_time: Optional[datetime] = None
    participating_servers: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.status == "PENDING"

    @property
    def is_started(self) -> bool:
        """Verifica se foi iniciado."""
        return self.status == "STARTED"

    @property
    def is_completed(self) -> bool:
        """Verifica se foi completado."""
        return self.status == "COMPLETED"

    @property
    def is_launch_job(self) -> bool:
        """Verifica se é job de lançamento."""
        return self.job_type == "LAUNCH"

    @property
    def is_terminate_job(self) -> bool:
        """Verifica se é job de terminação."""
        return self.job_type == "TERMINATE"

    @property
    def is_test(self) -> bool:
        """Verifica se é teste."""
        return self.initiated_by == "START_TEST"

    @property
    def is_cutover(self) -> bool:
        """Verifica se é cutover."""
        return self.initiated_by == "START_CUTOVER"

    @property
    def servers_count(self) -> int:
        """Número de servidores participando."""
        return len(self.participating_servers)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "arn": self.arn,
            "job_type": self.job_type,
            "status": self.status,
            "is_pending": self.is_pending,
            "is_completed": self.is_completed,
            "is_test": self.is_test,
            "is_cutover": self.is_cutover,
            "servers_count": self.servers_count,
            "creation_date_time": self.creation_date_time.isoformat() if self.creation_date_time else None
        }


@dataclass
class MGNLaunchConfiguration:
    """Launch Configuration MGN."""
    source_server_id: str
    boot_mode: str = "LEGACY_BIOS"
    copy_private_ip: bool = False
    copy_tags: bool = False
    ec2_launch_template_id: str = ""
    launch_disposition: str = "STOPPED"
    licensing: Dict[str, Any] = field(default_factory=dict)
    name: str = ""
    target_instance_type_right_sizing_method: str = "NONE"

    @property
    def uses_legacy_bios(self) -> bool:
        """Verifica se usa BIOS legacy."""
        return self.boot_mode == "LEGACY_BIOS"

    @property
    def uses_uefi(self) -> bool:
        """Verifica se usa UEFI."""
        return self.boot_mode == "UEFI"

    @property
    def launches_stopped(self) -> bool:
        """Verifica se lança parado."""
        return self.launch_disposition == "STOPPED"

    @property
    def launches_started(self) -> bool:
        """Verifica se lança iniciado."""
        return self.launch_disposition == "STARTED"

    @property
    def has_template(self) -> bool:
        """Verifica se tem template."""
        return bool(self.ec2_launch_template_id)

    @property
    def uses_right_sizing(self) -> bool:
        """Verifica se usa right-sizing."""
        return self.target_instance_type_right_sizing_method != "NONE"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "source_server_id": self.source_server_id,
            "boot_mode": self.boot_mode,
            "copy_private_ip": self.copy_private_ip,
            "copy_tags": self.copy_tags,
            "launch_disposition": self.launch_disposition,
            "has_template": self.has_template,
            "uses_right_sizing": self.uses_right_sizing
        }


class MGNService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS MGN."""

    def __init__(self, client_factory):
        """Inicializa o serviço MGN."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._mgn_client = None

    @property
    def mgn_client(self):
        """Cliente MGN com lazy loading."""
        if self._mgn_client is None:
            self._mgn_client = self._client_factory.get_client('mgn')
        return self._mgn_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço MGN."""
        try:
            self.mgn_client.describe_source_servers(maxResults=1)
            return {
                "service": "mgn",
                "status": "healthy",
                "message": "MGN service is accessible"
            }
        except Exception as e:
            return {
                "service": "mgn",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_source_servers(self) -> List[MGNSourceServer]:
        """Lista source servers."""
        servers = []
        try:
            paginator = self.mgn_client.get_paginator('describe_source_servers')
            for page in paginator.paginate():
                for server in page.get('items', []):
                    servers.append(MGNSourceServer(
                        source_server_id=server.get('sourceServerID', ''),
                        arn=server.get('arn', ''),
                        is_archived=server.get('isArchived', False),
                        launched_instance=server.get('launchedInstance', {}),
                        life_cycle=server.get('lifeCycle', {}),
                        replication_type=server.get('replicationType', 'AGENT_BASED'),
                        source_properties=server.get('sourceProperties', {}),
                        data_replication_info=server.get('dataReplicationInfo', {}),
                        tags=server.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar source servers: {e}")
        return servers

    def get_jobs(self) -> List[MGNJob]:
        """Lista jobs."""
        jobs = []
        try:
            paginator = self.mgn_client.get_paginator('describe_jobs')
            for page in paginator.paginate():
                for job in page.get('items', []):
                    jobs.append(MGNJob(
                        job_id=job.get('jobID', ''),
                        arn=job.get('arn', ''),
                        job_type=job.get('type', 'LAUNCH'),
                        status=job.get('status', 'PENDING'),
                        initiated_by=job.get('initiatedBy', 'START_TEST'),
                        creation_date_time=job.get('creationDateTime'),
                        end_date_time=job.get('endDateTime'),
                        participating_servers=job.get('participatingServers', []),
                        tags=job.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs: {e}")
        return jobs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos MGN."""
        servers = self.get_source_servers()
        jobs = self.get_jobs()

        active_servers = [s for s in servers if not s.is_archived]

        return {
            "source_servers": [s.to_dict() for s in servers],
            "jobs": [j.to_dict() for j in jobs[:50]],
            "summary": {
                "total_source_servers": len(servers),
                "active_servers": len(active_servers),
                "archived_servers": len([s for s in servers if s.is_archived]),
                "ready_for_test": len([s for s in active_servers if s.is_ready_for_test]),
                "ready_for_cutover": len([s for s in active_servers if s.is_ready_for_cutover]),
                "cutover_complete": len([s for s in active_servers if s.is_cutover]),
                "replicating": len([s for s in active_servers if s.is_replicating]),
                "total_jobs": len(jobs),
                "pending_jobs": len([j for j in jobs if j.is_pending]),
                "completed_jobs": len([j for j in jobs if j.is_completed])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do MGN."""
        servers = self.get_source_servers()
        jobs = self.get_jobs()

        active_servers = [s for s in servers if not s.is_archived]

        return {
            "source_servers_count": len(servers),
            "active_servers": len(active_servers),
            "archived_servers": len([s for s in servers if s.is_archived]),
            "not_ready": len([s for s in active_servers if s.is_not_ready]),
            "ready_for_test": len([s for s in active_servers if s.is_ready_for_test]),
            "ready_for_cutover": len([s for s in active_servers if s.is_ready_for_cutover]),
            "cutover_complete": len([s for s in active_servers if s.is_cutover]),
            "disconnected": len([s for s in active_servers if s.is_disconnected]),
            "replicating": len([s for s in active_servers if s.is_replicating]),
            "initial_sync": len([s for s in active_servers if s.is_initial_sync]),
            "agent_based": len([s for s in active_servers if s.is_agent_based]),
            "jobs_count": len(jobs),
            "test_jobs": len([j for j in jobs if j.is_test]),
            "cutover_jobs": len([j for j in jobs if j.is_cutover])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para MGN."""
        recommendations = []
        servers = self.get_source_servers()

        active_servers = [s for s in servers if not s.is_archived]
        
        ready_but_not_launched = [s for s in active_servers if s.is_ready_for_cutover and not s.has_launched_instance]
        if ready_but_not_launched:
            recommendations.append({
                "resource_type": "MGNSourceServer",
                "resource_id": "multiple",
                "recommendation": "Servidores prontos para cutover",
                "description": f"{len(ready_but_not_launched)} servidor(es) pronto(s) para cutover. "
                               "Considerar executar cutover para finalizar migração.",
                "priority": "medium"
            })

        disconnected = [s for s in active_servers if s.is_disconnected]
        if disconnected:
            recommendations.append({
                "resource_type": "MGNSourceServer",
                "resource_id": "multiple",
                "recommendation": "Servidores desconectados",
                "description": f"{len(disconnected)} servidor(es) desconectado(s). "
                               "Verificar agente ou arquivar se migração completada.",
                "priority": "high"
            })

        return recommendations
