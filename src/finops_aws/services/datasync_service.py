"""
AWS DataSync Service para FinOps.

Análise de custos e otimização de transferência de dados.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class DataSyncTask:
    """Task de transferência DataSync."""
    task_arn: str
    name: str = ""
    status: str = "AVAILABLE"
    source_location_arn: str = ""
    destination_location_arn: str = ""
    cloud_watch_log_group_arn: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    schedule: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_detail: Optional[str] = None
    creation_time: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.status == "AVAILABLE"

    @property
    def is_running(self) -> bool:
        """Verifica se está em execução."""
        return self.status == "RUNNING"

    @property
    def is_queued(self) -> bool:
        """Verifica se está na fila."""
        return self.status == "QUEUED"

    @property
    def has_schedule(self) -> bool:
        """Verifica se tem schedule."""
        return bool(self.schedule)

    @property
    def has_logging(self) -> bool:
        """Verifica se tem logging."""
        return self.cloud_watch_log_group_arn is not None

    @property
    def verify_mode(self) -> str:
        """Modo de verificação."""
        return self.options.get('VerifyMode', 'POINT_IN_TIME_CONSISTENT')

    @property
    def has_error(self) -> bool:
        """Verifica se tem erro."""
        return self.error_code is not None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "task_arn": self.task_arn,
            "name": self.name,
            "status": self.status,
            "source_location_arn": self.source_location_arn,
            "destination_location_arn": self.destination_location_arn,
            "cloud_watch_log_group_arn": self.cloud_watch_log_group_arn,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "is_available": self.is_available,
            "is_running": self.is_running,
            "has_schedule": self.has_schedule,
            "has_logging": self.has_logging,
            "verify_mode": self.verify_mode,
            "has_error": self.has_error
        }


@dataclass
class DataSyncLocation:
    """Localização DataSync."""
    location_arn: str
    location_uri: str = ""
    location_type: str = "S3"
    creation_time: Optional[datetime] = None

    @property
    def is_s3(self) -> bool:
        """Verifica se é S3."""
        return self.location_type == "S3" or "s3://" in self.location_uri

    @property
    def is_efs(self) -> bool:
        """Verifica se é EFS."""
        return self.location_type == "EFS"

    @property
    def is_fsx(self) -> bool:
        """Verifica se é FSx."""
        return "FSX" in self.location_type.upper()

    @property
    def is_nfs(self) -> bool:
        """Verifica se é NFS."""
        return self.location_type == "NFS"

    @property
    def is_smb(self) -> bool:
        """Verifica se é SMB."""
        return self.location_type == "SMB"

    @property
    def is_hdfs(self) -> bool:
        """Verifica se é HDFS."""
        return self.location_type == "HDFS"

    @property
    def is_object_storage(self) -> bool:
        """Verifica se é object storage."""
        return self.location_type == "OBJECT_STORAGE"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "location_arn": self.location_arn,
            "location_uri": self.location_uri,
            "location_type": self.location_type,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "is_s3": self.is_s3,
            "is_efs": self.is_efs,
            "is_fsx": self.is_fsx,
            "is_nfs": self.is_nfs,
            "is_smb": self.is_smb
        }


@dataclass
class DataSyncTaskExecution:
    """Execução de task DataSync."""
    task_execution_arn: str
    status: str = "SUCCESS"
    start_time: Optional[datetime] = None
    bytes_transferred: int = 0
    bytes_written: int = 0
    files_transferred: int = 0
    estimated_bytes_to_transfer: int = 0
    estimated_files_to_transfer: int = 0
    result: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Verifica se foi bem sucedida."""
        return self.status == "SUCCESS"

    @property
    def is_error(self) -> bool:
        """Verifica se teve erro."""
        return self.status == "ERROR"

    @property
    def is_launching(self) -> bool:
        """Verifica se está iniciando."""
        return self.status == "LAUNCHING"

    @property
    def is_transferring(self) -> bool:
        """Verifica se está transferindo."""
        return self.status == "TRANSFERRING"

    @property
    def bytes_transferred_gb(self) -> float:
        """Bytes transferidos em GB."""
        return self.bytes_transferred / (1024 ** 3)

    @property
    def progress_percent(self) -> float:
        """Progresso em porcentagem."""
        if self.estimated_bytes_to_transfer > 0:
            return (self.bytes_transferred / self.estimated_bytes_to_transfer) * 100
        return 100.0 if self.is_success else 0.0

    @property
    def estimated_cost(self) -> float:
        """Custo estimado ($0.0125/GB transferido)."""
        return self.bytes_transferred_gb * 0.0125

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "task_execution_arn": self.task_execution_arn,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "bytes_transferred": self.bytes_transferred,
            "bytes_transferred_gb": self.bytes_transferred_gb,
            "bytes_written": self.bytes_written,
            "files_transferred": self.files_transferred,
            "is_success": self.is_success,
            "is_error": self.is_error,
            "progress_percent": self.progress_percent,
            "estimated_cost": self.estimated_cost
        }


@dataclass
class DataSyncAgent:
    """Agente DataSync."""
    agent_arn: str
    name: str = ""
    status: str = "ONLINE"
    last_connection_time: Optional[datetime] = None
    creation_time: Optional[datetime] = None
    endpoint_type: str = "PUBLIC"
    private_link_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_online(self) -> bool:
        """Verifica se está online."""
        return self.status == "ONLINE"

    @property
    def is_offline(self) -> bool:
        """Verifica se está offline."""
        return self.status == "OFFLINE"

    @property
    def uses_private_link(self) -> bool:
        """Verifica se usa PrivateLink."""
        return self.endpoint_type == "PRIVATE_LINK" or bool(self.private_link_config)

    @property
    def is_public(self) -> bool:
        """Verifica se usa endpoint público."""
        return self.endpoint_type == "PUBLIC"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "agent_arn": self.agent_arn,
            "name": self.name,
            "status": self.status,
            "last_connection_time": self.last_connection_time.isoformat() if self.last_connection_time else None,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "endpoint_type": self.endpoint_type,
            "is_online": self.is_online,
            "is_offline": self.is_offline,
            "uses_private_link": self.uses_private_link,
            "is_public": self.is_public
        }


class DataSyncService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS DataSync."""

    def __init__(self, client_factory):
        """Inicializa o serviço DataSync."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._datasync_client = None

    @property
    def datasync_client(self):
        """Cliente DataSync com lazy loading."""
        if self._datasync_client is None:
            self._datasync_client = self._client_factory.get_client('datasync')
        return self._datasync_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço DataSync."""
        try:
            self.datasync_client.list_tasks(MaxResults=1)
            return {
                "service": "datasync",
                "status": "healthy",
                "message": "DataSync service is accessible"
            }
        except Exception as e:
            return {
                "service": "datasync",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_tasks(self) -> List[DataSyncTask]:
        """Lista tasks de transferência."""
        tasks = []
        try:
            paginator = self.datasync_client.get_paginator('list_tasks')
            for page in paginator.paginate():
                for task in page.get('Tasks', []):
                    try:
                        details = self.datasync_client.describe_task(TaskArn=task.get('TaskArn', ''))
                        tasks.append(DataSyncTask(
                            task_arn=details.get('TaskArn', ''),
                            name=details.get('Name', ''),
                            status=details.get('Status', 'AVAILABLE'),
                            source_location_arn=details.get('SourceLocationArn', ''),
                            destination_location_arn=details.get('DestinationLocationArn', ''),
                            cloud_watch_log_group_arn=details.get('CloudWatchLogGroupArn'),
                            options=details.get('Options', {}),
                            schedule=details.get('Schedule', {}),
                            error_code=details.get('ErrorCode'),
                            error_detail=details.get('ErrorDetail'),
                            creation_time=details.get('CreationTime')
                        ))
                    except Exception:
                        tasks.append(DataSyncTask(
                            task_arn=task.get('TaskArn', ''),
                            name=task.get('Name', ''),
                            status=task.get('Status', 'AVAILABLE')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar tasks: {e}")
        return tasks

    def get_locations(self) -> List[DataSyncLocation]:
        """Lista localizações."""
        locations = []
        try:
            paginator = self.datasync_client.get_paginator('list_locations')
            for page in paginator.paginate():
                for loc in page.get('Locations', []):
                    location_type = "UNKNOWN"
                    uri = loc.get('LocationUri', '')
                    if 's3://' in uri:
                        location_type = "S3"
                    elif 'efs' in uri.lower():
                        location_type = "EFS"
                    elif 'fsx' in uri.lower():
                        location_type = "FSX"
                    elif 'nfs://' in uri:
                        location_type = "NFS"
                    elif 'smb://' in uri:
                        location_type = "SMB"
                    
                    locations.append(DataSyncLocation(
                        location_arn=loc.get('LocationArn', ''),
                        location_uri=uri,
                        location_type=location_type
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar localizações: {e}")
        return locations

    def get_agents(self) -> List[DataSyncAgent]:
        """Lista agentes."""
        agents = []
        try:
            paginator = self.datasync_client.get_paginator('list_agents')
            for page in paginator.paginate():
                for agent in page.get('Agents', []):
                    try:
                        details = self.datasync_client.describe_agent(AgentArn=agent.get('AgentArn', ''))
                        agents.append(DataSyncAgent(
                            agent_arn=details.get('AgentArn', ''),
                            name=details.get('Name', ''),
                            status=details.get('Status', 'ONLINE'),
                            last_connection_time=details.get('LastConnectionTime'),
                            creation_time=details.get('CreationTime'),
                            endpoint_type=details.get('EndpointType', 'PUBLIC'),
                            private_link_config=details.get('PrivateLinkConfig', {})
                        ))
                    except Exception:
                        agents.append(DataSyncAgent(
                            agent_arn=agent.get('AgentArn', ''),
                            name=agent.get('Name', ''),
                            status=agent.get('Status', 'ONLINE')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar agentes: {e}")
        return agents

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos DataSync."""
        tasks = self.get_tasks()
        locations = self.get_locations()
        agents = self.get_agents()

        return {
            "tasks": [t.to_dict() for t in tasks],
            "locations": [l.to_dict() for l in locations],
            "agents": [a.to_dict() for a in agents],
            "summary": {
                "total_tasks": len(tasks),
                "available_tasks": len([t for t in tasks if t.is_available]),
                "running_tasks": len([t for t in tasks if t.is_running]),
                "tasks_with_schedule": len([t for t in tasks if t.has_schedule]),
                "tasks_with_logging": len([t for t in tasks if t.has_logging]),
                "total_locations": len(locations),
                "s3_locations": len([l for l in locations if l.is_s3]),
                "efs_locations": len([l for l in locations if l.is_efs]),
                "total_agents": len(agents),
                "online_agents": len([a for a in agents if a.is_online]),
                "offline_agents": len([a for a in agents if a.is_offline])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do DataSync."""
        tasks = self.get_tasks()
        locations = self.get_locations()
        agents = self.get_agents()

        return {
            "tasks_count": len(tasks),
            "available_tasks": len([t for t in tasks if t.is_available]),
            "running_tasks": len([t for t in tasks if t.is_running]),
            "scheduled_tasks": len([t for t in tasks if t.has_schedule]),
            "tasks_with_errors": len([t for t in tasks if t.has_error]),
            "locations_count": len(locations),
            "location_types": {
                "s3": len([l for l in locations if l.is_s3]),
                "efs": len([l for l in locations if l.is_efs]),
                "fsx": len([l for l in locations if l.is_fsx]),
                "nfs": len([l for l in locations if l.is_nfs]),
                "smb": len([l for l in locations if l.is_smb])
            },
            "agents_count": len(agents),
            "online_agents": len([a for a in agents if a.is_online]),
            "private_link_agents": len([a for a in agents if a.uses_private_link])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para DataSync."""
        recommendations = []
        tasks = self.get_tasks()
        agents = self.get_agents()

        # Verificar tasks sem logging
        for task in tasks:
            if task.is_available and not task.has_logging:
                recommendations.append({
                    "resource_type": "DataSyncTask",
                    "resource_id": task.name or task.task_arn,
                    "recommendation": "Habilitar logging CloudWatch",
                    "description": f"Task '{task.name}' não tem logging configurado. "
                                   "Recomendado para monitoramento e troubleshooting.",
                    "priority": "medium"
                })

        # Verificar tasks com erros
        for task in tasks:
            if task.has_error:
                recommendations.append({
                    "resource_type": "DataSyncTask",
                    "resource_id": task.name or task.task_arn,
                    "recommendation": "Investigar erro na task",
                    "description": f"Task '{task.name}' tem erro: {task.error_code}. "
                                   f"Detalhe: {task.error_detail}",
                    "priority": "high"
                })

        # Verificar agentes offline
        for agent in agents:
            if agent.is_offline:
                recommendations.append({
                    "resource_type": "DataSyncAgent",
                    "resource_id": agent.name or agent.agent_arn,
                    "recommendation": "Verificar agente offline",
                    "description": f"Agente '{agent.name}' está offline. "
                                   "Verificar conectividade e status do agente.",
                    "priority": "high"
                })

        # Verificar agentes públicos
        public_agents = [a for a in agents if a.is_public and a.is_online]
        if public_agents:
            recommendations.append({
                "resource_type": "DataSyncAgent",
                "resource_id": "multiple",
                "recommendation": "Considerar PrivateLink para agentes",
                "description": f"{len(public_agents)} agente(s) usando endpoint público. "
                               "Considerar PrivateLink para maior segurança.",
                "priority": "medium"
            })

        return recommendations
