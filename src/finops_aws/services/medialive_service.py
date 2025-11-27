"""
AWS MediaLive Service para FinOps.

Análise de custos e otimização de canais de transmissão ao vivo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class MediaLiveChannel:
    """Channel MediaLive."""
    channel_id: str
    name: str = ""
    arn: str = ""
    state: str = "IDLE"
    channel_class: str = "STANDARD"
    input_attachments: List[Dict[str, Any]] = field(default_factory=list)
    destinations: List[Dict[str, Any]] = field(default_factory=list)
    encoder_settings: Dict[str, Any] = field(default_factory=dict)
    pipeline_details: List[Dict[str, Any]] = field(default_factory=list)
    role_arn: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.state == "RUNNING"

    @property
    def is_idle(self) -> bool:
        """Verifica se está ocioso."""
        return self.state == "IDLE"

    @property
    def is_starting(self) -> bool:
        """Verifica se está iniciando."""
        return self.state == "STARTING"

    @property
    def is_stopping(self) -> bool:
        """Verifica se está parando."""
        return self.state == "STOPPING"

    @property
    def is_standard_class(self) -> bool:
        """Verifica se é classe standard."""
        return self.channel_class == "STANDARD"

    @property
    def is_single_pipeline(self) -> bool:
        """Verifica se é single pipeline."""
        return self.channel_class == "SINGLE_PIPELINE"

    @property
    def inputs_count(self) -> int:
        """Número de inputs."""
        return len(self.input_attachments)

    @property
    def outputs_count(self) -> int:
        """Número de outputs."""
        return len(self.destinations)

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado."""
        if self.is_standard_class:
            return 3.0
        return 1.5

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "arn": self.arn,
            "state": self.state,
            "is_running": self.is_running,
            "is_idle": self.is_idle,
            "channel_class": self.channel_class,
            "is_standard_class": self.is_standard_class,
            "inputs_count": self.inputs_count,
            "outputs_count": self.outputs_count,
            "estimated_hourly_cost": self.estimated_hourly_cost
        }


@dataclass
class MediaLiveInput:
    """Input MediaLive."""
    input_id: str
    name: str = ""
    arn: str = ""
    type: str = "URL_PULL"
    state: str = "DETACHED"
    attached_channels: List[str] = field(default_factory=list)
    input_class: str = "STANDARD"
    destinations: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_attached(self) -> bool:
        """Verifica se está anexado."""
        return self.state == "ATTACHED"

    @property
    def is_detached(self) -> bool:
        """Verifica se está desanexado."""
        return self.state == "DETACHED"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.state == "CREATING"

    @property
    def is_deleted(self) -> bool:
        """Verifica se foi deletado."""
        return self.state == "DELETED"

    @property
    def is_url_pull(self) -> bool:
        """Verifica se é URL pull."""
        return self.type == "URL_PULL"

    @property
    def is_rtmp_push(self) -> bool:
        """Verifica se é RTMP push."""
        return self.type == "RTMP_PUSH"

    @property
    def is_rtp_push(self) -> bool:
        """Verifica se é RTP push."""
        return self.type == "RTP_PUSH"

    @property
    def channels_count(self) -> int:
        """Número de canais anexados."""
        return len(self.attached_channels)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "input_id": self.input_id,
            "name": self.name,
            "arn": self.arn,
            "type": self.type,
            "state": self.state,
            "is_attached": self.is_attached,
            "is_detached": self.is_detached,
            "input_class": self.input_class,
            "channels_count": self.channels_count
        }


@dataclass
class MediaLiveInputSecurityGroup:
    """Input Security Group MediaLive."""
    security_group_id: str
    arn: str = ""
    state: str = "IDLE"
    whitelist_rules: List[Dict[str, str]] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_idle(self) -> bool:
        """Verifica se está ocioso."""
        return self.state == "IDLE"

    @property
    def is_in_use(self) -> bool:
        """Verifica se está em uso."""
        return self.state == "IN_USE"

    @property
    def rules_count(self) -> int:
        """Número de regras."""
        return len(self.whitelist_rules)

    @property
    def inputs_count(self) -> int:
        """Número de inputs."""
        return len(self.inputs)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "security_group_id": self.security_group_id,
            "arn": self.arn,
            "state": self.state,
            "is_idle": self.is_idle,
            "is_in_use": self.is_in_use,
            "rules_count": self.rules_count,
            "inputs_count": self.inputs_count
        }


class MediaLiveService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS MediaLive."""

    def __init__(self, client_factory):
        """Inicializa o serviço MediaLive."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._medialive_client = None

    @property
    def medialive_client(self):
        """Cliente MediaLive com lazy loading."""
        if self._medialive_client is None:
            self._medialive_client = self._client_factory.get_client('medialive')
        return self._medialive_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço MediaLive."""
        try:
            self.medialive_client.list_channels(MaxResults=1)
            return {
                "service": "medialive",
                "status": "healthy",
                "message": "MediaLive service is accessible"
            }
        except Exception as e:
            return {
                "service": "medialive",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_channels(self) -> List[MediaLiveChannel]:
        """Lista channels."""
        channels = []
        try:
            paginator = self.medialive_client.get_paginator('list_channels')
            for page in paginator.paginate():
                for ch in page.get('Channels', []):
                    channels.append(MediaLiveChannel(
                        channel_id=ch.get('Id', ''),
                        name=ch.get('Name', ''),
                        arn=ch.get('Arn', ''),
                        state=ch.get('State', 'IDLE'),
                        channel_class=ch.get('ChannelClass', 'STANDARD'),
                        input_attachments=ch.get('InputAttachments', []),
                        destinations=ch.get('Destinations', []),
                        pipeline_details=ch.get('PipelineDetails', []),
                        role_arn=ch.get('RoleArn', ''),
                        tags=ch.get('Tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar channels: {e}")
        return channels

    def get_inputs(self) -> List[MediaLiveInput]:
        """Lista inputs."""
        inputs = []
        try:
            paginator = self.medialive_client.get_paginator('list_inputs')
            for page in paginator.paginate():
                for inp in page.get('Inputs', []):
                    inputs.append(MediaLiveInput(
                        input_id=inp.get('Id', ''),
                        name=inp.get('Name', ''),
                        arn=inp.get('Arn', ''),
                        type=inp.get('Type', 'URL_PULL'),
                        state=inp.get('State', 'DETACHED'),
                        attached_channels=inp.get('AttachedChannels', []),
                        input_class=inp.get('InputClass', 'STANDARD'),
                        destinations=inp.get('Destinations', []),
                        sources=inp.get('Sources', []),
                        security_groups=inp.get('SecurityGroups', []),
                        tags=inp.get('Tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar inputs: {e}")
        return inputs

    def get_input_security_groups(self) -> List[MediaLiveInputSecurityGroup]:
        """Lista input security groups."""
        groups = []
        try:
            paginator = self.medialive_client.get_paginator('list_input_security_groups')
            for page in paginator.paginate():
                for sg in page.get('InputSecurityGroups', []):
                    groups.append(MediaLiveInputSecurityGroup(
                        security_group_id=sg.get('Id', ''),
                        arn=sg.get('Arn', ''),
                        state=sg.get('State', 'IDLE'),
                        whitelist_rules=sg.get('WhitelistRules', []),
                        inputs=sg.get('Inputs', []),
                        tags=sg.get('Tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar security groups: {e}")
        return groups

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos MediaLive."""
        channels = self.get_channels()
        inputs = self.get_inputs()
        security_groups = self.get_input_security_groups()

        running_cost = sum(ch.estimated_hourly_cost for ch in channels if ch.is_running)

        return {
            "channels": [ch.to_dict() for ch in channels],
            "inputs": [i.to_dict() for i in inputs],
            "input_security_groups": [sg.to_dict() for sg in security_groups],
            "summary": {
                "total_channels": len(channels),
                "running_channels": len([ch for ch in channels if ch.is_running]),
                "idle_channels": len([ch for ch in channels if ch.is_idle]),
                "standard_class_channels": len([ch for ch in channels if ch.is_standard_class]),
                "total_inputs": len(inputs),
                "attached_inputs": len([i for i in inputs if i.is_attached]),
                "detached_inputs": len([i for i in inputs if i.is_detached]),
                "total_security_groups": len(security_groups),
                "estimated_hourly_cost": running_cost
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do MediaLive."""
        channels = self.get_channels()
        inputs = self.get_inputs()
        security_groups = self.get_input_security_groups()

        return {
            "channels_count": len(channels),
            "running_channels": len([ch for ch in channels if ch.is_running]),
            "idle_channels": len([ch for ch in channels if ch.is_idle]),
            "standard_class_channels": len([ch for ch in channels if ch.is_standard_class]),
            "single_pipeline_channels": len([ch for ch in channels if ch.is_single_pipeline]),
            "inputs_count": len(inputs),
            "attached_inputs": len([i for i in inputs if i.is_attached]),
            "detached_inputs": len([i for i in inputs if i.is_detached]),
            "security_groups_count": len(security_groups),
            "estimated_hourly_cost": sum(ch.estimated_hourly_cost for ch in channels if ch.is_running)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para MediaLive."""
        recommendations = []
        channels = self.get_channels()
        inputs = self.get_inputs()

        idle_channels = [ch for ch in channels if ch.is_idle]
        if idle_channels:
            recommendations.append({
                "resource_type": "MediaLiveChannel",
                "resource_id": "multiple",
                "recommendation": "Remover canais ociosos",
                "description": f"{len(idle_channels)} canal(is) ocioso(s). "
                               "Considerar remover se não forem mais necessários.",
                "priority": "medium"
            })

        detached_inputs = [i for i in inputs if i.is_detached]
        if detached_inputs:
            recommendations.append({
                "resource_type": "MediaLiveInput",
                "resource_id": "multiple",
                "recommendation": "Remover inputs desanexados",
                "description": f"{len(detached_inputs)} input(s) desanexado(s). "
                               "Considerar remover se não forem mais necessários.",
                "priority": "low"
            })

        return recommendations
