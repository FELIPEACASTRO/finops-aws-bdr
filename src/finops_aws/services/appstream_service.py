"""
AWS AppStream 2.0 Service para FinOps.

Análise de custos e otimização de streaming de aplicações.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class AppStreamFleet:
    """Fleet AppStream."""
    name: str
    arn: str = ""
    display_name: str = ""
    description: str = ""
    image_name: str = ""
    image_arn: str = ""
    instance_type: str = "stream.standard.medium"
    fleet_type: str = "ALWAYS_ON"
    state: str = "STOPPED"
    max_user_duration_in_seconds: int = 57600
    disconnect_timeout_in_seconds: int = 900
    idle_disconnect_timeout_in_seconds: int = 0
    enable_default_internet_access: bool = False
    vpc_config: Dict[str, Any] = field(default_factory=dict)
    compute_capacity_status: Dict[str, Any] = field(default_factory=dict)
    stream_view: str = "APP"
    platform: str = "WINDOWS"
    created_time: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.state == "RUNNING"

    @property
    def is_stopped(self) -> bool:
        """Verifica se está parado."""
        return self.state == "STOPPED"

    @property
    def is_starting(self) -> bool:
        """Verifica se está iniciando."""
        return self.state == "STARTING"

    @property
    def is_stopping(self) -> bool:
        """Verifica se está parando."""
        return self.state == "STOPPING"

    @property
    def is_always_on(self) -> bool:
        """Verifica se é always-on."""
        return self.fleet_type == "ALWAYS_ON"

    @property
    def is_on_demand(self) -> bool:
        """Verifica se é on-demand."""
        return self.fleet_type == "ON_DEMAND"

    @property
    def is_elastic(self) -> bool:
        """Verifica se é elastic."""
        return self.fleet_type == "ELASTIC"

    @property
    def desired_capacity(self) -> int:
        """Capacidade desejada."""
        return self.compute_capacity_status.get('Desired', 0)

    @property
    def running_capacity(self) -> int:
        """Capacidade rodando."""
        return self.compute_capacity_status.get('Running', 0)

    @property
    def in_use_capacity(self) -> int:
        """Capacidade em uso."""
        return self.compute_capacity_status.get('InUse', 0)

    @property
    def available_capacity(self) -> int:
        """Capacidade disponível."""
        return self.compute_capacity_status.get('Available', 0)

    @property
    def utilization_percentage(self) -> float:
        """Percentual de utilização."""
        if self.running_capacity == 0:
            return 0.0
        return (self.in_use_capacity / self.running_capacity) * 100

    @property
    def is_windows(self) -> bool:
        """Verifica se é Windows."""
        return self.platform == "WINDOWS"

    @property
    def is_amazon_linux(self) -> bool:
        """Verifica se é Amazon Linux."""
        return self.platform.startswith("AMAZON_LINUX")

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado por instância."""
        size_costs = {
            'small': 0.10, 'medium': 0.20, 'large': 0.40,
            'xlarge': 0.80, '2xlarge': 1.60, '4xlarge': 3.20
        }
        for size, cost in size_costs.items():
            if size in self.instance_type:
                return cost * self.running_capacity
        return 0.20 * self.running_capacity

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "display_name": self.display_name,
            "instance_type": self.instance_type,
            "fleet_type": self.fleet_type,
            "state": self.state,
            "is_running": self.is_running,
            "is_always_on": self.is_always_on,
            "desired_capacity": self.desired_capacity,
            "running_capacity": self.running_capacity,
            "in_use_capacity": self.in_use_capacity,
            "utilization_percentage": self.utilization_percentage,
            "platform": self.platform,
            "estimated_hourly_cost": self.estimated_hourly_cost
        }


@dataclass
class AppStreamStack:
    """Stack AppStream."""
    name: str
    arn: str = ""
    description: str = ""
    display_name: str = ""
    created_time: Optional[datetime] = None
    storage_connectors: List[Dict[str, Any]] = field(default_factory=list)
    redirect_url: str = ""
    feedback_url: str = ""
    user_settings: List[Dict[str, str]] = field(default_factory=list)
    application_settings: Dict[str, Any] = field(default_factory=dict)
    access_endpoints: List[Dict[str, Any]] = field(default_factory=list)
    embed_host_domains: List[str] = field(default_factory=list)
    streaming_experience_settings: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_storage_connectors(self) -> bool:
        """Verifica se tem conectores de storage."""
        return len(self.storage_connectors) > 0

    @property
    def has_redirect_url(self) -> bool:
        """Verifica se tem URL de redirecionamento."""
        return bool(self.redirect_url)

    @property
    def has_feedback_url(self) -> bool:
        """Verifica se tem URL de feedback."""
        return bool(self.feedback_url)

    @property
    def has_embed_domains(self) -> bool:
        """Verifica se tem domínios de embedding."""
        return len(self.embed_host_domains) > 0

    @property
    def storage_types(self) -> List[str]:
        """Tipos de storage conectados."""
        return [sc.get('ConnectorType', '') for sc in self.storage_connectors]

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "display_name": self.display_name,
            "has_storage_connectors": self.has_storage_connectors,
            "storage_types": self.storage_types,
            "has_redirect_url": self.has_redirect_url,
            "has_feedback_url": self.has_feedback_url,
            "has_embed_domains": self.has_embed_domains,
            "created_time": self.created_time.isoformat() if self.created_time else None
        }


@dataclass
class AppStreamImage:
    """Image AppStream."""
    name: str
    arn: str = ""
    base_image_arn: str = ""
    display_name: str = ""
    state: str = "AVAILABLE"
    visibility: str = "PRIVATE"
    image_builder_supported: bool = True
    image_builder_name: str = ""
    platform: str = "WINDOWS"
    description: str = ""
    state_change_reason: Dict[str, str] = field(default_factory=dict)
    applications: List[Dict[str, Any]] = field(default_factory=list)
    created_time: Optional[datetime] = None
    public_base_image_released_date: Optional[datetime] = None
    appstream_agent_version: str = ""

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.state == "AVAILABLE"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.state == "PENDING"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.state == "FAILED"

    @property
    def is_private(self) -> bool:
        """Verifica se é privada."""
        return self.visibility == "PRIVATE"

    @property
    def is_public(self) -> bool:
        """Verifica se é pública."""
        return self.visibility == "PUBLIC"

    @property
    def is_shared(self) -> bool:
        """Verifica se é compartilhada."""
        return self.visibility == "SHARED"

    @property
    def applications_count(self) -> int:
        """Número de aplicações."""
        return len(self.applications)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "state": self.state,
            "visibility": self.visibility,
            "is_available": self.is_available,
            "is_private": self.is_private,
            "platform": self.platform,
            "applications_count": self.applications_count,
            "image_builder_supported": self.image_builder_supported,
            "created_time": self.created_time.isoformat() if self.created_time else None
        }


class AppStreamService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS AppStream 2.0."""

    def __init__(self, client_factory):
        """Inicializa o serviço AppStream."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._appstream_client = None

    @property
    def appstream_client(self):
        """Cliente AppStream com lazy loading."""
        if self._appstream_client is None:
            self._appstream_client = self._client_factory.get_client('appstream')
        return self._appstream_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço AppStream."""
        try:
            self.appstream_client.describe_fleets(Names=[])
            return {
                "service": "appstream",
                "status": "healthy",
                "message": "AppStream service is accessible"
            }
        except Exception as e:
            return {
                "service": "appstream",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_fleets(self) -> List[AppStreamFleet]:
        """Lista fleets."""
        fleets = []
        try:
            paginator = self.appstream_client.get_paginator('describe_fleets')
            for page in paginator.paginate():
                for fleet in page.get('Fleets', []):
                    fleets.append(AppStreamFleet(
                        name=fleet.get('Name', ''),
                        arn=fleet.get('Arn', ''),
                        display_name=fleet.get('DisplayName', ''),
                        description=fleet.get('Description', ''),
                        image_name=fleet.get('ImageName', ''),
                        image_arn=fleet.get('ImageArn', ''),
                        instance_type=fleet.get('InstanceType', 'stream.standard.medium'),
                        fleet_type=fleet.get('FleetType', 'ALWAYS_ON'),
                        state=fleet.get('State', 'STOPPED'),
                        max_user_duration_in_seconds=fleet.get('MaxUserDurationInSeconds', 57600),
                        disconnect_timeout_in_seconds=fleet.get('DisconnectTimeoutInSeconds', 900),
                        idle_disconnect_timeout_in_seconds=fleet.get('IdleDisconnectTimeoutInSeconds', 0),
                        enable_default_internet_access=fleet.get('EnableDefaultInternetAccess', False),
                        vpc_config=fleet.get('VpcConfig', {}),
                        compute_capacity_status=fleet.get('ComputeCapacityStatus', {}),
                        stream_view=fleet.get('StreamView', 'APP'),
                        platform=fleet.get('Platform', 'WINDOWS'),
                        created_time=fleet.get('CreatedTime')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar fleets: {e}")
        return fleets

    def get_stacks(self) -> List[AppStreamStack]:
        """Lista stacks."""
        stacks = []
        try:
            paginator = self.appstream_client.get_paginator('describe_stacks')
            for page in paginator.paginate():
                for stack in page.get('Stacks', []):
                    stacks.append(AppStreamStack(
                        name=stack.get('Name', ''),
                        arn=stack.get('Arn', ''),
                        description=stack.get('Description', ''),
                        display_name=stack.get('DisplayName', ''),
                        created_time=stack.get('CreatedTime'),
                        storage_connectors=stack.get('StorageConnectors', []),
                        redirect_url=stack.get('RedirectURL', ''),
                        feedback_url=stack.get('FeedbackURL', ''),
                        user_settings=stack.get('UserSettings', []),
                        application_settings=stack.get('ApplicationSettings', {}),
                        access_endpoints=stack.get('AccessEndpoints', []),
                        embed_host_domains=stack.get('EmbedHostDomains', []),
                        streaming_experience_settings=stack.get('StreamingExperienceSettings', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar stacks: {e}")
        return stacks

    def get_images(self) -> List[AppStreamImage]:
        """Lista images."""
        images = []
        try:
            paginator = self.appstream_client.get_paginator('describe_images')
            for page in paginator.paginate():
                for img in page.get('Images', []):
                    images.append(AppStreamImage(
                        name=img.get('Name', ''),
                        arn=img.get('Arn', ''),
                        base_image_arn=img.get('BaseImageArn', ''),
                        display_name=img.get('DisplayName', ''),
                        state=img.get('State', 'AVAILABLE'),
                        visibility=img.get('Visibility', 'PRIVATE'),
                        image_builder_supported=img.get('ImageBuilderSupported', True),
                        image_builder_name=img.get('ImageBuilderName', ''),
                        platform=img.get('Platform', 'WINDOWS'),
                        description=img.get('Description', ''),
                        state_change_reason=img.get('StateChangeReason', {}),
                        applications=img.get('Applications', []),
                        created_time=img.get('CreatedTime'),
                        public_base_image_released_date=img.get('PublicBaseImageReleasedDate'),
                        appstream_agent_version=img.get('AppstreamAgentVersion', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar images: {e}")
        return images

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos AppStream."""
        fleets = self.get_fleets()
        stacks = self.get_stacks()
        images = self.get_images()

        running_fleets = [f for f in fleets if f.is_running]

        return {
            "fleets": [f.to_dict() for f in fleets],
            "stacks": [s.to_dict() for s in stacks],
            "images": [i.to_dict() for i in images[:50]],
            "summary": {
                "total_fleets": len(fleets),
                "running_fleets": len(running_fleets),
                "stopped_fleets": len([f for f in fleets if f.is_stopped]),
                "always_on_fleets": len([f for f in fleets if f.is_always_on]),
                "on_demand_fleets": len([f for f in fleets if f.is_on_demand]),
                "total_running_capacity": sum(f.running_capacity for f in running_fleets),
                "total_in_use_capacity": sum(f.in_use_capacity for f in running_fleets),
                "total_stacks": len(stacks),
                "total_images": len(images),
                "private_images": len([i for i in images if i.is_private]),
                "estimated_hourly_cost": sum(f.estimated_hourly_cost for f in running_fleets)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do AppStream."""
        fleets = self.get_fleets()
        stacks = self.get_stacks()
        images = self.get_images()

        running_fleets = [f for f in fleets if f.is_running]

        return {
            "fleets_count": len(fleets),
            "running_fleets": len(running_fleets),
            "stopped_fleets": len([f for f in fleets if f.is_stopped]),
            "always_on_fleets": len([f for f in fleets if f.is_always_on]),
            "on_demand_fleets": len([f for f in fleets if f.is_on_demand]),
            "elastic_fleets": len([f for f in fleets if f.is_elastic]),
            "total_running_capacity": sum(f.running_capacity for f in running_fleets),
            "total_in_use_capacity": sum(f.in_use_capacity for f in running_fleets),
            "stacks_count": len(stacks),
            "stacks_with_storage": len([s for s in stacks if s.has_storage_connectors]),
            "images_count": len(images),
            "private_images": len([i for i in images if i.is_private]),
            "available_images": len([i for i in images if i.is_available])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para AppStream."""
        recommendations = []
        fleets = self.get_fleets()

        low_utilization = [f for f in fleets if f.is_running and f.utilization_percentage < 20 and f.running_capacity > 0]
        if low_utilization:
            recommendations.append({
                "resource_type": "AppStreamFleet",
                "resource_id": "multiple",
                "recommendation": "Reduzir capacidade de fleets subutilizados",
                "description": f"{len(low_utilization)} fleet(s) com utilização abaixo de 20%. "
                               "Considerar reduzir capacidade ou usar on-demand.",
                "priority": "high"
            })

        always_on_idle = [f for f in fleets if f.is_always_on and f.is_running and f.in_use_capacity == 0]
        if always_on_idle:
            recommendations.append({
                "resource_type": "AppStreamFleet",
                "resource_id": "multiple",
                "recommendation": "Considerar fleets on-demand",
                "description": f"{len(always_on_idle)} fleet(s) always-on sem uso. "
                               "Considerar mudar para on-demand para economizar.",
                "priority": "medium"
            })

        return recommendations
