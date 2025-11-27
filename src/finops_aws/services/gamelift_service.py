"""
AWS GameLift Service para FinOps.

Análise de custos e otimização de servidores de jogos.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class GameLiftFleet:
    """Fleet GameLift."""
    fleet_id: str
    fleet_arn: str = ""
    fleet_type: str = "ON_DEMAND"
    instance_type: str = "c5.large"
    description: str = ""
    name: str = ""
    creation_time: Optional[datetime] = None
    termination_time: Optional[datetime] = None
    status: str = "NEW"
    build_id: str = ""
    build_arn: str = ""
    script_id: str = ""
    script_arn: str = ""
    server_launch_path: str = ""
    server_launch_parameters: str = ""
    log_paths: List[str] = field(default_factory=list)
    new_game_session_protection_policy: str = "NoProtection"
    operating_system: str = "AMAZON_LINUX_2"
    compute_type: str = "EC2"
    anywhere_configuration: Dict[str, Any] = field(default_factory=dict)
    instance_role_arn: str = ""
    certificate_configuration: Dict[str, str] = field(default_factory=dict)
    locations: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_new(self) -> bool:
        """Verifica se é novo."""
        return self.status == "NEW"

    @property
    def is_building(self) -> bool:
        """Verifica se está construindo."""
        return self.status == "BUILDING"

    @property
    def is_downloading(self) -> bool:
        """Verifica se está baixando."""
        return self.status == "DOWNLOADING"

    @property
    def is_validating(self) -> bool:
        """Verifica se está validando."""
        return self.status == "VALIDATING"

    @property
    def is_activating(self) -> bool:
        """Verifica se está ativando."""
        return self.status == "ACTIVATING"

    @property
    def is_terminated(self) -> bool:
        """Verifica se está terminado."""
        return self.status == "TERMINATED"

    @property
    def is_error(self) -> bool:
        """Verifica se está em erro."""
        return self.status == "ERROR"

    @property
    def is_on_demand(self) -> bool:
        """Verifica se é on-demand."""
        return self.fleet_type == "ON_DEMAND"

    @property
    def is_spot(self) -> bool:
        """Verifica se é spot."""
        return self.fleet_type == "SPOT"

    @property
    def uses_build(self) -> bool:
        """Verifica se usa build."""
        return bool(self.build_id)

    @property
    def uses_script(self) -> bool:
        """Verifica se usa script."""
        return bool(self.script_id)

    @property
    def is_ec2(self) -> bool:
        """Verifica se usa EC2."""
        return self.compute_type == "EC2"

    @property
    def is_anywhere(self) -> bool:
        """Verifica se é Anywhere."""
        return self.compute_type == "ANYWHERE"

    @property
    def has_protection(self) -> bool:
        """Verifica se tem proteção."""
        return self.new_game_session_protection_policy == "FullProtection"

    @property
    def is_windows(self) -> bool:
        """Verifica se é Windows."""
        return "WINDOWS" in self.operating_system

    @property
    def is_linux(self) -> bool:
        """Verifica se é Linux."""
        return "LINUX" in self.operating_system

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado."""
        size_costs = {
            'small': 0.10, 'medium': 0.20, 'large': 0.40,
            'xlarge': 0.80, '2xlarge': 1.60, '4xlarge': 3.20
        }
        base = 0.40
        for size, cost in size_costs.items():
            if size in self.instance_type:
                base = cost
                break
        if self.is_spot:
            base *= 0.3
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "fleet_id": self.fleet_id,
            "fleet_arn": self.fleet_arn,
            "name": self.name,
            "fleet_type": self.fleet_type,
            "instance_type": self.instance_type,
            "status": self.status,
            "is_active": self.is_active,
            "is_on_demand": self.is_on_demand,
            "is_spot": self.is_spot,
            "operating_system": self.operating_system,
            "compute_type": self.compute_type,
            "has_protection": self.has_protection,
            "estimated_hourly_cost": self.estimated_hourly_cost,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class GameLiftBuild:
    """Build GameLift."""
    build_id: str
    build_arn: str = ""
    name: str = ""
    version: str = ""
    status: str = "INITIALIZED"
    size_on_disk: int = 0
    operating_system: str = "AMAZON_LINUX_2"
    creation_time: Optional[datetime] = None
    server_sdk_version: str = ""

    @property
    def is_ready(self) -> bool:
        """Verifica se está pronto."""
        return self.status == "READY"

    @property
    def is_initialized(self) -> bool:
        """Verifica se está inicializado."""
        return self.status == "INITIALIZED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def size_gb(self) -> float:
        """Tamanho em GB."""
        return self.size_on_disk / (1024 ** 3)

    @property
    def is_windows(self) -> bool:
        """Verifica se é Windows."""
        return "WINDOWS" in self.operating_system

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "build_id": self.build_id,
            "build_arn": self.build_arn,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "is_ready": self.is_ready,
            "size_gb": self.size_gb,
            "operating_system": self.operating_system,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class GameLiftGameSession:
    """Game Session GameLift."""
    game_session_id: str
    fleet_id: str = ""
    fleet_arn: str = ""
    name: str = ""
    ip_address: str = ""
    dns_name: str = ""
    port: int = 0
    player_session_creation_policy: str = "ACCEPT_ALL"
    creator_id: str = ""
    game_properties: List[Dict[str, str]] = field(default_factory=list)
    status: str = "ACTIVE"
    status_reason: str = ""
    current_player_session_count: int = 0
    maximum_player_session_count: int = 0
    creation_time: Optional[datetime] = None
    termination_time: Optional[datetime] = None
    matched_player_sessions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativa."""
        return self.status == "ACTIVE"

    @property
    def is_activating(self) -> bool:
        """Verifica se está ativando."""
        return self.status == "ACTIVATING"

    @property
    def is_terminated(self) -> bool:
        """Verifica se está terminada."""
        return self.status == "TERMINATED"

    @property
    def is_terminating(self) -> bool:
        """Verifica se está terminando."""
        return self.status == "TERMINATING"

    @property
    def is_error(self) -> bool:
        """Verifica se está em erro."""
        return self.status == "ERROR"

    @property
    def player_count(self) -> int:
        """Número de jogadores."""
        return self.current_player_session_count

    @property
    def max_players(self) -> int:
        """Máximo de jogadores."""
        return self.maximum_player_session_count

    @property
    def is_full(self) -> bool:
        """Verifica se está cheio."""
        return self.player_count >= self.max_players and self.max_players > 0

    @property
    def availability_percentage(self) -> float:
        """Percentual de disponibilidade."""
        if self.max_players == 0:
            return 100.0
        available = self.max_players - self.player_count
        return (available / self.max_players) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "game_session_id": self.game_session_id,
            "fleet_id": self.fleet_id,
            "name": self.name,
            "status": self.status,
            "is_active": self.is_active,
            "player_count": self.player_count,
            "max_players": self.max_players,
            "is_full": self.is_full,
            "availability_percentage": self.availability_percentage,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


class GameLiftService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS GameLift."""

    def __init__(self, client_factory):
        """Inicializa o serviço GameLift."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._gamelift_client = None

    @property
    def gamelift_client(self):
        """Cliente GameLift com lazy loading."""
        if self._gamelift_client is None:
            self._gamelift_client = self._client_factory.get_client('gamelift')
        return self._gamelift_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço GameLift."""
        try:
            self.gamelift_client.list_fleets(Limit=1)
            return {
                "service": "gamelift",
                "status": "healthy",
                "message": "GameLift service is accessible"
            }
        except Exception as e:
            return {
                "service": "gamelift",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_fleets(self) -> List[GameLiftFleet]:
        """Lista fleets."""
        fleets = []
        try:
            paginator = self.gamelift_client.get_paginator('list_fleets')
            fleet_ids = []
            for page in paginator.paginate():
                fleet_ids.extend(page.get('FleetIds', []))
            
            if fleet_ids:
                for i in range(0, len(fleet_ids), 25):
                    batch = fleet_ids[i:i+25]
                    response = self.gamelift_client.describe_fleet_attributes(FleetIds=batch)
                    for fleet in response.get('FleetAttributes', []):
                        fleets.append(GameLiftFleet(
                            fleet_id=fleet.get('FleetId', ''),
                            fleet_arn=fleet.get('FleetArn', ''),
                            fleet_type=fleet.get('FleetType', 'ON_DEMAND'),
                            instance_type=fleet.get('InstanceType', 'c5.large'),
                            description=fleet.get('Description', ''),
                            name=fleet.get('Name', ''),
                            creation_time=fleet.get('CreationTime'),
                            termination_time=fleet.get('TerminationTime'),
                            status=fleet.get('Status', 'NEW'),
                            build_id=fleet.get('BuildId', ''),
                            build_arn=fleet.get('BuildArn', ''),
                            script_id=fleet.get('ScriptId', ''),
                            script_arn=fleet.get('ScriptArn', ''),
                            server_launch_path=fleet.get('ServerLaunchPath', ''),
                            server_launch_parameters=fleet.get('ServerLaunchParameters', ''),
                            log_paths=fleet.get('LogPaths', []),
                            new_game_session_protection_policy=fleet.get('NewGameSessionProtectionPolicy', 'NoProtection'),
                            operating_system=fleet.get('OperatingSystem', 'AMAZON_LINUX_2'),
                            compute_type=fleet.get('ComputeType', 'EC2'),
                            anywhere_configuration=fleet.get('AnywhereConfiguration', {}),
                            instance_role_arn=fleet.get('InstanceRoleArn', ''),
                            certificate_configuration=fleet.get('CertificateConfiguration', {}),
                            locations=fleet.get('Locations', [])
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar fleets: {e}")
        return fleets

    def get_builds(self) -> List[GameLiftBuild]:
        """Lista builds."""
        builds = []
        try:
            paginator = self.gamelift_client.get_paginator('list_builds')
            for page in paginator.paginate():
                for build in page.get('Builds', []):
                    builds.append(GameLiftBuild(
                        build_id=build.get('BuildId', ''),
                        build_arn=build.get('BuildArn', ''),
                        name=build.get('Name', ''),
                        version=build.get('Version', ''),
                        status=build.get('Status', 'INITIALIZED'),
                        size_on_disk=build.get('SizeOnDisk', 0),
                        operating_system=build.get('OperatingSystem', 'AMAZON_LINUX_2'),
                        creation_time=build.get('CreationTime'),
                        server_sdk_version=build.get('ServerSdkVersion', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar builds: {e}")
        return builds

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos GameLift."""
        fleets = self.get_fleets()
        builds = self.get_builds()

        active_fleets = [f for f in fleets if f.is_active]

        return {
            "fleets": [f.to_dict() for f in fleets],
            "builds": [b.to_dict() for b in builds],
            "summary": {
                "total_fleets": len(fleets),
                "active_fleets": len(active_fleets),
                "on_demand_fleets": len([f for f in fleets if f.is_on_demand]),
                "spot_fleets": len([f for f in fleets if f.is_spot]),
                "ec2_fleets": len([f for f in fleets if f.is_ec2]),
                "anywhere_fleets": len([f for f in fleets if f.is_anywhere]),
                "total_builds": len(builds),
                "ready_builds": len([b for b in builds if b.is_ready]),
                "estimated_hourly_cost": sum(f.estimated_hourly_cost for f in active_fleets)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do GameLift."""
        fleets = self.get_fleets()
        builds = self.get_builds()

        return {
            "fleets_count": len(fleets),
            "active_fleets": len([f for f in fleets if f.is_active]),
            "on_demand_fleets": len([f for f in fleets if f.is_on_demand]),
            "spot_fleets": len([f for f in fleets if f.is_spot]),
            "ec2_fleets": len([f for f in fleets if f.is_ec2]),
            "anywhere_fleets": len([f for f in fleets if f.is_anywhere]),
            "builds_count": len(builds),
            "ready_builds": len([b for b in builds if b.is_ready]),
            "failed_builds": len([b for b in builds if b.is_failed])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para GameLift."""
        recommendations = []
        fleets = self.get_fleets()

        on_demand = [f for f in fleets if f.is_on_demand and f.is_active]
        if on_demand:
            recommendations.append({
                "resource_type": "GameLiftFleet",
                "resource_id": "multiple",
                "recommendation": "Considerar fleets Spot",
                "description": f"{len(on_demand)} fleet(s) on-demand ativa(s). "
                               "Considerar usar Spot para economizar até 70%.",
                "priority": "high"
            })

        return recommendations
