"""
AWS RoboMaker Service para FinOps.

Análise de custos e otimização de robótica.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class RoboMakerRobotApplication:
    """Robot Application RoboMaker."""
    name: str
    arn: str = ""
    version: str = ""
    robot_software_suite: Dict[str, str] = field(default_factory=dict)
    last_updated_at: Optional[datetime] = None
    revision_id: str = ""
    environment: Dict[str, str] = field(default_factory=dict)

    @property
    def uses_ros(self) -> bool:
        """Verifica se usa ROS."""
        return self.robot_software_suite.get('name', '') == "ROS"

    @property
    def uses_ros2(self) -> bool:
        """Verifica se usa ROS2."""
        return self.robot_software_suite.get('name', '') == "ROS2"

    @property
    def ros_version(self) -> str:
        """Versão ROS."""
        return self.robot_software_suite.get('version', '')

    @property
    def has_version(self) -> bool:
        """Verifica se tem versão."""
        return bool(self.version)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "version": self.version,
            "uses_ros": self.uses_ros,
            "uses_ros2": self.uses_ros2,
            "ros_version": self.ros_version,
            "has_version": self.has_version,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None
        }


@dataclass
class RoboMakerSimulationApplication:
    """Simulation Application RoboMaker."""
    name: str
    arn: str = ""
    version: str = ""
    robot_software_suite: Dict[str, str] = field(default_factory=dict)
    simulation_software_suite: Dict[str, str] = field(default_factory=dict)
    rendering_engine: Dict[str, str] = field(default_factory=dict)
    last_updated_at: Optional[datetime] = None
    revision_id: str = ""
    environment: Dict[str, str] = field(default_factory=dict)

    @property
    def uses_ros(self) -> bool:
        """Verifica se usa ROS."""
        return self.robot_software_suite.get('name', '') == "ROS"

    @property
    def uses_ros2(self) -> bool:
        """Verifica se usa ROS2."""
        return self.robot_software_suite.get('name', '') == "ROS2"

    @property
    def simulation_engine(self) -> str:
        """Engine de simulação."""
        return self.simulation_software_suite.get('name', '')

    @property
    def uses_gazebo(self) -> bool:
        """Verifica se usa Gazebo."""
        return self.simulation_engine == "Gazebo"

    @property
    def uses_worldforge(self) -> bool:
        """Verifica se usa WorldForge."""
        return self.simulation_engine == "WorldForge"

    @property
    def renderer(self) -> str:
        """Renderer."""
        return self.rendering_engine.get('name', '')

    @property
    def uses_ogre(self) -> bool:
        """Verifica se usa OGRE."""
        return self.renderer == "OGRE"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "version": self.version,
            "uses_ros": self.uses_ros,
            "uses_ros2": self.uses_ros2,
            "simulation_engine": self.simulation_engine,
            "uses_gazebo": self.uses_gazebo,
            "renderer": self.renderer,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None
        }


@dataclass
class RoboMakerSimulationJob:
    """Simulation Job RoboMaker."""
    arn: str
    name: str = ""
    status: str = "Pending"
    last_started_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    failure_behavior: str = "Fail"
    failure_code: str = ""
    failure_reason: str = ""
    client_request_token: str = ""
    output_location: Dict[str, str] = field(default_factory=dict)
    logging_config: Dict[str, bool] = field(default_factory=dict)
    max_job_duration_in_seconds: int = 0
    simulation_time_millis: int = 0
    iam_role: str = ""
    robot_applications: List[Dict[str, Any]] = field(default_factory=list)
    simulation_applications: List[Dict[str, Any]] = field(default_factory=list)
    data_sources: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    vpc_config: Dict[str, Any] = field(default_factory=dict)
    compute: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.status == "Pending"

    @property
    def is_preparing(self) -> bool:
        """Verifica se está preparando."""
        return self.status == "Preparing"

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.status == "Running"

    @property
    def is_restarting(self) -> bool:
        """Verifica se está reiniciando."""
        return self.status == "Restarting"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "Completed"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "Failed"

    @property
    def is_terminated(self) -> bool:
        """Verifica se está terminado."""
        return self.status == "Terminated"

    @property
    def is_terminating(self) -> bool:
        """Verifica se está terminando."""
        return self.status == "Terminating"

    @property
    def is_canceled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "Canceled"

    @property
    def simulation_time_seconds(self) -> float:
        """Tempo de simulação em segundos."""
        return self.simulation_time_millis / 1000

    @property
    def simulation_time_hours(self) -> float:
        """Tempo de simulação em horas."""
        return self.simulation_time_seconds / 3600

    @property
    def has_failure(self) -> bool:
        """Verifica se tem falha."""
        return bool(self.failure_code or self.failure_reason)

    @property
    def fails_on_error(self) -> bool:
        """Verifica se falha em erro."""
        return self.failure_behavior == "Fail"

    @property
    def continues_on_error(self) -> bool:
        """Verifica se continua em erro."""
        return self.failure_behavior == "Continue"

    @property
    def estimated_cost(self) -> float:
        """Custo estimado baseado no tempo."""
        return self.simulation_time_hours * 0.40

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "arn": self.arn,
            "name": self.name,
            "status": self.status,
            "is_running": self.is_running,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "simulation_time_seconds": self.simulation_time_seconds,
            "simulation_time_hours": self.simulation_time_hours,
            "has_failure": self.has_failure,
            "estimated_cost": self.estimated_cost,
            "last_started_at": self.last_started_at.isoformat() if self.last_started_at else None
        }


@dataclass
class RoboMakerWorldGenerationJob:
    """World Generation Job RoboMaker."""
    arn: str
    status: str = "Pending"
    created_at: Optional[datetime] = None
    failure_code: str = ""
    failure_reason: str = ""
    client_request_token: str = ""
    template: str = ""
    world_count: int = 0
    finished_worlds_summary: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.status == "Pending"

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.status == "Running"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "Completed"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "Failed"

    @property
    def is_partial_failed(self) -> bool:
        """Verifica se falhou parcialmente."""
        return self.status == "PartialFailed"

    @property
    def is_canceled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.status == "Canceled"

    @property
    def is_canceling(self) -> bool:
        """Verifica se está cancelando."""
        return self.status == "Canceling"

    @property
    def succeeded_worlds(self) -> int:
        """Mundos com sucesso."""
        return self.finished_worlds_summary.get('succeededWorldCount', 0)

    @property
    def failed_worlds(self) -> int:
        """Mundos com falha."""
        return self.finished_worlds_summary.get('failedWorldCount', 0)

    @property
    def has_failure(self) -> bool:
        """Verifica se tem falha."""
        return bool(self.failure_code or self.failure_reason)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "arn": self.arn,
            "status": self.status,
            "is_running": self.is_running,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "world_count": self.world_count,
            "succeeded_worlds": self.succeeded_worlds,
            "failed_worlds": self.failed_worlds,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RoboMakerService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS RoboMaker."""

    def __init__(self, client_factory):
        """Inicializa o serviço RoboMaker."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._robomaker_client = None

    @property
    def robomaker_client(self):
        """Cliente RoboMaker com lazy loading."""
        if self._robomaker_client is None:
            self._robomaker_client = self._client_factory.get_client('robomaker')
        return self._robomaker_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço RoboMaker."""
        try:
            self.robomaker_client.list_robots(maxResults=1)
            return {
                "service": "robomaker",
                "status": "healthy",
                "message": "RoboMaker service is accessible"
            }
        except Exception as e:
            return {
                "service": "robomaker",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_robot_applications(self) -> List[RoboMakerRobotApplication]:
        """Lista robot applications."""
        apps = []
        try:
            paginator = self.robomaker_client.get_paginator('list_robot_applications')
            for page in paginator.paginate():
                for app in page.get('robotApplicationSummaries', []):
                    apps.append(RoboMakerRobotApplication(
                        name=app.get('name', ''),
                        arn=app.get('arn', ''),
                        version=app.get('version', ''),
                        robot_software_suite=app.get('robotSoftwareSuite', {}),
                        last_updated_at=app.get('lastUpdatedAt')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar robot applications: {e}")
        return apps

    def get_simulation_applications(self) -> List[RoboMakerSimulationApplication]:
        """Lista simulation applications."""
        apps = []
        try:
            paginator = self.robomaker_client.get_paginator('list_simulation_applications')
            for page in paginator.paginate():
                for app in page.get('simulationApplicationSummaries', []):
                    apps.append(RoboMakerSimulationApplication(
                        name=app.get('name', ''),
                        arn=app.get('arn', ''),
                        version=app.get('version', ''),
                        robot_software_suite=app.get('robotSoftwareSuite', {}),
                        simulation_software_suite=app.get('simulationSoftwareSuite', {}),
                        last_updated_at=app.get('lastUpdatedAt')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar simulation applications: {e}")
        return apps

    def get_simulation_jobs(self) -> List[RoboMakerSimulationJob]:
        """Lista simulation jobs."""
        jobs = []
        try:
            paginator = self.robomaker_client.get_paginator('list_simulation_jobs')
            for page in paginator.paginate():
                for job in page.get('simulationJobSummaries', []):
                    jobs.append(RoboMakerSimulationJob(
                        arn=job.get('arn', ''),
                        name=job.get('name', ''),
                        status=job.get('status', 'Pending'),
                        last_updated_at=job.get('lastUpdatedAt'),
                        robot_applications=job.get('robotApplicationNames', []),
                        simulation_applications=job.get('simulationApplicationNames', []),
                        data_sources=job.get('dataSourceNames', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar simulation jobs: {e}")
        return jobs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos RoboMaker."""
        robot_apps = self.get_robot_applications()
        sim_apps = self.get_simulation_applications()
        jobs = self.get_simulation_jobs()

        running_jobs = [j for j in jobs if j.is_running]

        return {
            "robot_applications": [a.to_dict() for a in robot_apps],
            "simulation_applications": [a.to_dict() for a in sim_apps],
            "simulation_jobs": [j.to_dict() for j in jobs[:50]],
            "summary": {
                "total_robot_applications": len(robot_apps),
                "total_simulation_applications": len(sim_apps),
                "ros_apps": len([a for a in robot_apps if a.uses_ros]),
                "ros2_apps": len([a for a in robot_apps if a.uses_ros2]),
                "total_simulation_jobs": len(jobs),
                "running_jobs": len(running_jobs),
                "completed_jobs": len([j for j in jobs if j.is_completed]),
                "failed_jobs": len([j for j in jobs if j.is_failed]),
                "total_simulation_hours": sum(j.simulation_time_hours for j in jobs)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do RoboMaker."""
        robot_apps = self.get_robot_applications()
        sim_apps = self.get_simulation_applications()
        jobs = self.get_simulation_jobs()

        return {
            "robot_applications_count": len(robot_apps),
            "simulation_applications_count": len(sim_apps),
            "ros_apps": len([a for a in robot_apps if a.uses_ros]),
            "ros2_apps": len([a for a in robot_apps if a.uses_ros2]),
            "gazebo_apps": len([a for a in sim_apps if a.uses_gazebo]),
            "simulation_jobs_count": len(jobs),
            "running_jobs": len([j for j in jobs if j.is_running]),
            "pending_jobs": len([j for j in jobs if j.is_pending]),
            "completed_jobs": len([j for j in jobs if j.is_completed]),
            "failed_jobs": len([j for j in jobs if j.is_failed]),
            "total_simulation_hours": sum(j.simulation_time_hours for j in jobs)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para RoboMaker."""
        recommendations = []
        jobs = self.get_simulation_jobs()

        failed_jobs = [j for j in jobs if j.is_failed]
        if len(failed_jobs) > 5:
            recommendations.append({
                "resource_type": "RoboMakerSimulationJob",
                "resource_id": "multiple",
                "recommendation": "Investigar jobs com falha",
                "description": f"{len(failed_jobs)} job(s) de simulação com falha. "
                               "Revisar configurações para evitar custos desnecessários.",
                "priority": "medium"
            })

        return recommendations
