"""
AWS IVS (Interactive Video Service) para FinOps.

Análise de custos e otimização de streaming interativo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class IVSChannel:
    """Channel IVS."""
    channel_arn: str
    name: str = ""
    latency_mode: str = "LOW"
    type: str = "STANDARD"
    authorized: bool = False
    ingest_endpoint: str = ""
    playback_url: str = ""
    recording_configuration_arn: str = ""
    insecure_ingest: bool = False
    preset: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_low_latency(self) -> bool:
        """Verifica se é baixa latência."""
        return self.latency_mode == "LOW"

    @property
    def is_normal_latency(self) -> bool:
        """Verifica se é latência normal."""
        return self.latency_mode == "NORMAL"

    @property
    def is_standard_type(self) -> bool:
        """Verifica se é tipo standard."""
        return self.type == "STANDARD"

    @property
    def is_basic_type(self) -> bool:
        """Verifica se é tipo basic."""
        return self.type == "BASIC"

    @property
    def has_recording(self) -> bool:
        """Verifica se tem gravação configurada."""
        return bool(self.recording_configuration_arn)

    @property
    def is_authorized(self) -> bool:
        """Verifica se é autorizado."""
        return self.authorized

    @property
    def is_insecure(self) -> bool:
        """Verifica se permite ingestão insegura."""
        return self.insecure_ingest

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado (quando streaming)."""
        if self.is_standard_type:
            return 2.0
        return 0.20

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "channel_arn": self.channel_arn,
            "name": self.name,
            "latency_mode": self.latency_mode,
            "type": self.type,
            "is_low_latency": self.is_low_latency,
            "is_standard_type": self.is_standard_type,
            "has_recording": self.has_recording,
            "is_authorized": self.is_authorized,
            "is_insecure": self.is_insecure,
            "estimated_hourly_cost": self.estimated_hourly_cost
        }


@dataclass
class IVSStream:
    """Stream IVS."""
    channel_arn: str
    stream_id: str = ""
    playback_url: str = ""
    start_time: Optional[datetime] = None
    state: str = "LIVE"
    health: str = "HEALTHY"
    viewer_count: int = 0

    @property
    def is_live(self) -> bool:
        """Verifica se está ao vivo."""
        return self.state == "LIVE"

    @property
    def is_offline(self) -> bool:
        """Verifica se está offline."""
        return self.state == "OFFLINE"

    @property
    def is_healthy(self) -> bool:
        """Verifica se está saudável."""
        return self.health == "HEALTHY"

    @property
    def is_starving(self) -> bool:
        """Verifica se está com problemas de dados."""
        return self.health == "STARVING"

    @property
    def has_viewers(self) -> bool:
        """Verifica se tem viewers."""
        return self.viewer_count > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "channel_arn": self.channel_arn,
            "stream_id": self.stream_id,
            "state": self.state,
            "health": self.health,
            "is_live": self.is_live,
            "is_healthy": self.is_healthy,
            "viewer_count": self.viewer_count,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }


@dataclass
class IVSRecordingConfiguration:
    """Recording Configuration IVS."""
    recording_configuration_arn: str
    name: str = ""
    destination_configuration: Dict[str, Any] = field(default_factory=dict)
    state: str = "ACTIVE"
    thumbnail_configuration: Dict[str, Any] = field(default_factory=dict)
    recording_reconnect_window_seconds: int = 0
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.state == "ACTIVE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.state == "CREATING"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.state == "CREATE_FAILED"

    @property
    def s3_bucket(self) -> str:
        """Bucket S3 de destino."""
        s3_config = self.destination_configuration.get('s3', {})
        return s3_config.get('bucketName', '')

    @property
    def has_thumbnails(self) -> bool:
        """Verifica se tem thumbnails configurados."""
        return bool(self.thumbnail_configuration)

    @property
    def has_reconnect_window(self) -> bool:
        """Verifica se tem janela de reconexão."""
        return self.recording_reconnect_window_seconds > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "recording_configuration_arn": self.recording_configuration_arn,
            "name": self.name,
            "state": self.state,
            "is_active": self.is_active,
            "s3_bucket": self.s3_bucket,
            "has_thumbnails": self.has_thumbnails,
            "has_reconnect_window": self.has_reconnect_window,
            "recording_reconnect_window_seconds": self.recording_reconnect_window_seconds
        }


@dataclass
class IVSPlaybackKeyPair:
    """Playback Key Pair IVS."""
    key_pair_arn: str
    name: str = ""
    fingerprint: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "key_pair_arn": self.key_pair_arn,
            "name": self.name,
            "fingerprint": self.fingerprint[:20] + "..." if len(self.fingerprint) > 20 else self.fingerprint
        }


class IVSService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS IVS."""

    def __init__(self, client_factory):
        """Inicializa o serviço IVS."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._ivs_client = None

    @property
    def ivs_client(self):
        """Cliente IVS com lazy loading."""
        if self._ivs_client is None:
            self._ivs_client = self._client_factory.get_client('ivs')
        return self._ivs_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço IVS."""
        try:
            self.ivs_client.list_channels(maxResults=1)
            return {
                "service": "ivs",
                "status": "healthy",
                "message": "IVS service is accessible"
            }
        except Exception as e:
            return {
                "service": "ivs",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_channels(self) -> List[IVSChannel]:
        """Lista channels."""
        channels = []
        try:
            paginator = self.ivs_client.get_paginator('list_channels')
            for page in paginator.paginate():
                for ch in page.get('channels', []):
                    channels.append(IVSChannel(
                        channel_arn=ch.get('arn', ''),
                        name=ch.get('name', ''),
                        latency_mode=ch.get('latencyMode', 'LOW'),
                        type=ch.get('type', 'STANDARD'),
                        authorized=ch.get('authorized', False),
                        ingest_endpoint=ch.get('ingestEndpoint', ''),
                        playback_url=ch.get('playbackUrl', ''),
                        recording_configuration_arn=ch.get('recordingConfigurationArn', ''),
                        insecure_ingest=ch.get('insecureIngest', False),
                        preset=ch.get('preset', ''),
                        tags=ch.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar channels: {e}")
        return channels

    def get_streams(self) -> List[IVSStream]:
        """Lista streams ativos."""
        streams = []
        try:
            paginator = self.ivs_client.get_paginator('list_streams')
            for page in paginator.paginate():
                for stream in page.get('streams', []):
                    streams.append(IVSStream(
                        channel_arn=stream.get('channelArn', ''),
                        stream_id=stream.get('streamId', ''),
                        start_time=stream.get('startTime'),
                        state=stream.get('state', 'LIVE'),
                        health=stream.get('health', 'HEALTHY'),
                        viewer_count=stream.get('viewerCount', 0)
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar streams: {e}")
        return streams

    def get_recording_configurations(self) -> List[IVSRecordingConfiguration]:
        """Lista recording configurations."""
        configs = []
        try:
            paginator = self.ivs_client.get_paginator('list_recording_configurations')
            for page in paginator.paginate():
                for config in page.get('recordingConfigurations', []):
                    configs.append(IVSRecordingConfiguration(
                        recording_configuration_arn=config.get('arn', ''),
                        name=config.get('name', ''),
                        destination_configuration=config.get('destinationConfiguration', {}),
                        state=config.get('state', 'ACTIVE'),
                        tags=config.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar recording configurations: {e}")
        return configs

    def get_playback_key_pairs(self) -> List[IVSPlaybackKeyPair]:
        """Lista playback key pairs."""
        key_pairs = []
        try:
            paginator = self.ivs_client.get_paginator('list_playback_key_pairs')
            for page in paginator.paginate():
                for kp in page.get('keyPairs', []):
                    key_pairs.append(IVSPlaybackKeyPair(
                        key_pair_arn=kp.get('arn', ''),
                        name=kp.get('name', ''),
                        fingerprint=kp.get('fingerprint', ''),
                        tags=kp.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar key pairs: {e}")
        return key_pairs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos IVS."""
        channels = self.get_channels()
        streams = self.get_streams()
        recording_configs = self.get_recording_configurations()
        key_pairs = self.get_playback_key_pairs()

        return {
            "channels": [ch.to_dict() for ch in channels],
            "streams": [s.to_dict() for s in streams],
            "recording_configurations": [rc.to_dict() for rc in recording_configs],
            "playback_key_pairs": [kp.to_dict() for kp in key_pairs],
            "summary": {
                "total_channels": len(channels),
                "standard_channels": len([ch for ch in channels if ch.is_standard_type]),
                "basic_channels": len([ch for ch in channels if ch.is_basic_type]),
                "channels_with_recording": len([ch for ch in channels if ch.has_recording]),
                "authorized_channels": len([ch for ch in channels if ch.is_authorized]),
                "live_streams": len([s for s in streams if s.is_live]),
                "healthy_streams": len([s for s in streams if s.is_healthy]),
                "total_viewers": sum(s.viewer_count for s in streams),
                "total_recording_configs": len(recording_configs),
                "total_key_pairs": len(key_pairs)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do IVS."""
        channels = self.get_channels()
        streams = self.get_streams()
        recording_configs = self.get_recording_configurations()

        return {
            "channels_count": len(channels),
            "standard_channels": len([ch for ch in channels if ch.is_standard_type]),
            "basic_channels": len([ch for ch in channels if ch.is_basic_type]),
            "low_latency_channels": len([ch for ch in channels if ch.is_low_latency]),
            "channels_with_recording": len([ch for ch in channels if ch.has_recording]),
            "authorized_channels": len([ch for ch in channels if ch.is_authorized]),
            "insecure_channels": len([ch for ch in channels if ch.is_insecure]),
            "streams_count": len(streams),
            "live_streams": len([s for s in streams if s.is_live]),
            "healthy_streams": len([s for s in streams if s.is_healthy]),
            "starving_streams": len([s for s in streams if s.is_starving]),
            "total_viewers": sum(s.viewer_count for s in streams),
            "recording_configs_count": len(recording_configs),
            "active_recording_configs": len([rc for rc in recording_configs if rc.is_active])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para IVS."""
        recommendations = []
        channels = self.get_channels()
        streams = self.get_streams()

        insecure = [ch for ch in channels if ch.is_insecure]
        if insecure:
            recommendations.append({
                "resource_type": "IVSChannel",
                "resource_id": "multiple",
                "recommendation": "Desabilitar ingestão insegura",
                "description": f"{len(insecure)} canal(is) com ingestão insegura. "
                               "Considerar usar RTMPS para maior segurança.",
                "priority": "high"
            })

        no_auth = [ch for ch in channels if not ch.is_authorized]
        if len(no_auth) > 0 and len(no_auth) == len(channels):
            recommendations.append({
                "resource_type": "IVSChannel",
                "resource_id": "multiple",
                "recommendation": "Considerar autorização de canais",
                "description": "Nenhum canal usa autorização. "
                               "Considerar habilitar para controle de acesso.",
                "priority": "medium"
            })

        starving = [s for s in streams if s.is_starving]
        if starving:
            recommendations.append({
                "resource_type": "IVSStream",
                "resource_id": "multiple",
                "recommendation": "Investigar streams com problemas",
                "description": f"{len(starving)} stream(s) com status STARVING. "
                               "Verificar conectividade e bitrate.",
                "priority": "high"
            })

        return recommendations
