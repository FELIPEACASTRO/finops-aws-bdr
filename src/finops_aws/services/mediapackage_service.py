"""
AWS MediaPackage Service para FinOps.

Análise de custos e otimização de empacotamento de vídeo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class MediaPackageChannel:
    """Channel MediaPackage."""
    channel_id: str
    arn: str = ""
    description: str = ""
    ingress_access_logs: Dict[str, Any] = field(default_factory=dict)
    egress_access_logs: Dict[str, Any] = field(default_factory=dict)
    hls_ingest: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def has_ingress_logs(self) -> bool:
        """Verifica se tem logs de ingress."""
        return bool(self.ingress_access_logs)

    @property
    def has_egress_logs(self) -> bool:
        """Verifica se tem logs de egress."""
        return bool(self.egress_access_logs)

    @property
    def ingest_endpoints_count(self) -> int:
        """Número de endpoints de ingestão."""
        return len(self.hls_ingest.get('ingestEndpoints', []))

    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return len(self.tags) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "channel_id": self.channel_id,
            "arn": self.arn,
            "description": self.description,
            "has_ingress_logs": self.has_ingress_logs,
            "has_egress_logs": self.has_egress_logs,
            "ingest_endpoints_count": self.ingest_endpoints_count,
            "has_tags": self.has_tags
        }


@dataclass
class MediaPackageOriginEndpoint:
    """Origin Endpoint MediaPackage."""
    endpoint_id: str
    channel_id: str = ""
    arn: str = ""
    description: str = ""
    url: str = ""
    manifest_name: str = "index"
    time_delay_seconds: int = 0
    whitelist: List[str] = field(default_factory=list)
    origination: str = "ALLOW"
    startover_window_seconds: int = 0
    hls_package: Dict[str, Any] = field(default_factory=dict)
    dash_package: Dict[str, Any] = field(default_factory=dict)
    cmaf_package: Dict[str, Any] = field(default_factory=dict)
    mss_package: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_allow(self) -> bool:
        """Verifica se origination é ALLOW."""
        return self.origination == "ALLOW"

    @property
    def is_deny(self) -> bool:
        """Verifica se origination é DENY."""
        return self.origination == "DENY"

    @property
    def has_hls(self) -> bool:
        """Verifica se tem HLS."""
        return bool(self.hls_package)

    @property
    def has_dash(self) -> bool:
        """Verifica se tem DASH."""
        return bool(self.dash_package)

    @property
    def has_cmaf(self) -> bool:
        """Verifica se tem CMAF."""
        return bool(self.cmaf_package)

    @property
    def has_mss(self) -> bool:
        """Verifica se tem MSS."""
        return bool(self.mss_package)

    @property
    def has_time_delay(self) -> bool:
        """Verifica se tem atraso de tempo."""
        return self.time_delay_seconds > 0

    @property
    def has_startover(self) -> bool:
        """Verifica se tem startover."""
        return self.startover_window_seconds > 0

    @property
    def has_whitelist(self) -> bool:
        """Verifica se tem whitelist."""
        return len(self.whitelist) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "endpoint_id": self.endpoint_id,
            "channel_id": self.channel_id,
            "arn": self.arn,
            "url": self.url,
            "origination": self.origination,
            "is_allow": self.is_allow,
            "has_hls": self.has_hls,
            "has_dash": self.has_dash,
            "has_cmaf": self.has_cmaf,
            "has_mss": self.has_mss,
            "has_time_delay": self.has_time_delay,
            "has_startover": self.has_startover,
            "has_whitelist": self.has_whitelist
        }


@dataclass
class MediaPackageHarvestJob:
    """Harvest Job MediaPackage."""
    harvest_job_id: str
    arn: str = ""
    channel_id: str = ""
    origin_endpoint_id: str = ""
    s3_destination: Dict[str, Any] = field(default_factory=dict)
    start_time: str = ""
    end_time: str = ""
    status: str = "IN_PROGRESS"
    created_at: Optional[datetime] = None

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.status == "IN_PROGRESS"

    @property
    def is_succeeded(self) -> bool:
        """Verifica se teve sucesso."""
        return self.status == "SUCCEEDED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def s3_bucket(self) -> str:
        """Bucket S3 de destino."""
        return self.s3_destination.get('BucketName', '')

    @property
    def s3_manifest_key(self) -> str:
        """Key do manifesto S3."""
        return self.s3_destination.get('ManifestKey', '')

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "harvest_job_id": self.harvest_job_id,
            "arn": self.arn,
            "channel_id": self.channel_id,
            "origin_endpoint_id": self.origin_endpoint_id,
            "status": self.status,
            "is_in_progress": self.is_in_progress,
            "is_succeeded": self.is_succeeded,
            "is_failed": self.is_failed,
            "s3_bucket": self.s3_bucket,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MediaPackageService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS MediaPackage."""

    def __init__(self, client_factory):
        """Inicializa o serviço MediaPackage."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._mediapackage_client = None

    @property
    def mediapackage_client(self):
        """Cliente MediaPackage com lazy loading."""
        if self._mediapackage_client is None:
            self._mediapackage_client = self._client_factory.get_client('mediapackage')
        return self._mediapackage_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço MediaPackage."""
        try:
            self.mediapackage_client.list_channels(MaxResults=1)
            return {
                "service": "mediapackage",
                "status": "healthy",
                "message": "MediaPackage service is accessible"
            }
        except Exception as e:
            return {
                "service": "mediapackage",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_channels(self) -> List[MediaPackageChannel]:
        """Lista channels."""
        channels = []
        try:
            paginator = self.mediapackage_client.get_paginator('list_channels')
            for page in paginator.paginate():
                for ch in page.get('Channels', []):
                    channels.append(MediaPackageChannel(
                        channel_id=ch.get('Id', ''),
                        arn=ch.get('Arn', ''),
                        description=ch.get('Description', ''),
                        ingress_access_logs=ch.get('IngressAccessLogs', {}),
                        egress_access_logs=ch.get('EgressAccessLogs', {}),
                        hls_ingest=ch.get('HlsIngest', {}),
                        tags=ch.get('Tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar channels: {e}")
        return channels

    def get_origin_endpoints(self) -> List[MediaPackageOriginEndpoint]:
        """Lista origin endpoints."""
        endpoints = []
        try:
            paginator = self.mediapackage_client.get_paginator('list_origin_endpoints')
            for page in paginator.paginate():
                for ep in page.get('OriginEndpoints', []):
                    endpoints.append(MediaPackageOriginEndpoint(
                        endpoint_id=ep.get('Id', ''),
                        channel_id=ep.get('ChannelId', ''),
                        arn=ep.get('Arn', ''),
                        description=ep.get('Description', ''),
                        url=ep.get('Url', ''),
                        manifest_name=ep.get('ManifestName', 'index'),
                        time_delay_seconds=ep.get('TimeDelaySeconds', 0),
                        whitelist=ep.get('Whitelist', []),
                        origination=ep.get('Origination', 'ALLOW'),
                        startover_window_seconds=ep.get('StartoverWindowSeconds', 0),
                        hls_package=ep.get('HlsPackage', {}),
                        dash_package=ep.get('DashPackage', {}),
                        cmaf_package=ep.get('CmafPackage', {}),
                        mss_package=ep.get('MssPackage', {}),
                        tags=ep.get('Tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar origin endpoints: {e}")
        return endpoints

    def get_harvest_jobs(self) -> List[MediaPackageHarvestJob]:
        """Lista harvest jobs."""
        jobs = []
        try:
            paginator = self.mediapackage_client.get_paginator('list_harvest_jobs')
            for page in paginator.paginate():
                for job in page.get('HarvestJobs', []):
                    jobs.append(MediaPackageHarvestJob(
                        harvest_job_id=job.get('Id', ''),
                        arn=job.get('Arn', ''),
                        channel_id=job.get('ChannelId', ''),
                        origin_endpoint_id=job.get('OriginEndpointId', ''),
                        s3_destination=job.get('S3Destination', {}),
                        start_time=job.get('StartTime', ''),
                        end_time=job.get('EndTime', ''),
                        status=job.get('Status', 'IN_PROGRESS'),
                        created_at=job.get('CreatedAt')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar harvest jobs: {e}")
        return jobs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos MediaPackage."""
        channels = self.get_channels()
        endpoints = self.get_origin_endpoints()
        jobs = self.get_harvest_jobs()

        return {
            "channels": [ch.to_dict() for ch in channels],
            "origin_endpoints": [ep.to_dict() for ep in endpoints],
            "harvest_jobs": [j.to_dict() for j in jobs[:50]],
            "summary": {
                "total_channels": len(channels),
                "channels_with_logs": len([ch for ch in channels if ch.has_ingress_logs or ch.has_egress_logs]),
                "total_origin_endpoints": len(endpoints),
                "endpoints_with_hls": len([ep for ep in endpoints if ep.has_hls]),
                "endpoints_with_dash": len([ep for ep in endpoints if ep.has_dash]),
                "endpoints_with_cmaf": len([ep for ep in endpoints if ep.has_cmaf]),
                "total_harvest_jobs": len(jobs),
                "succeeded_jobs": len([j for j in jobs if j.is_succeeded]),
                "failed_jobs": len([j for j in jobs if j.is_failed])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do MediaPackage."""
        channels = self.get_channels()
        endpoints = self.get_origin_endpoints()
        jobs = self.get_harvest_jobs()

        return {
            "channels_count": len(channels),
            "channels_with_ingress_logs": len([ch for ch in channels if ch.has_ingress_logs]),
            "channels_with_egress_logs": len([ch for ch in channels if ch.has_egress_logs]),
            "origin_endpoints_count": len(endpoints),
            "endpoints_hls": len([ep for ep in endpoints if ep.has_hls]),
            "endpoints_dash": len([ep for ep in endpoints if ep.has_dash]),
            "endpoints_cmaf": len([ep for ep in endpoints if ep.has_cmaf]),
            "endpoints_mss": len([ep for ep in endpoints if ep.has_mss]),
            "endpoints_with_whitelist": len([ep for ep in endpoints if ep.has_whitelist]),
            "harvest_jobs_count": len(jobs),
            "harvest_jobs_succeeded": len([j for j in jobs if j.is_succeeded]),
            "harvest_jobs_failed": len([j for j in jobs if j.is_failed])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para MediaPackage."""
        recommendations = []
        channels = self.get_channels()
        endpoints = self.get_origin_endpoints()

        no_logs = [ch for ch in channels if not ch.has_ingress_logs and not ch.has_egress_logs]
        if no_logs:
            recommendations.append({
                "resource_type": "MediaPackageChannel",
                "resource_id": "multiple",
                "recommendation": "Habilitar logs de acesso",
                "description": f"{len(no_logs)} canal(is) sem logs de acesso. "
                               "Habilitar para monitoramento e debugging.",
                "priority": "low"
            })

        no_whitelist = [ep for ep in endpoints if not ep.has_whitelist and ep.is_allow]
        if no_whitelist:
            recommendations.append({
                "resource_type": "MediaPackageOriginEndpoint",
                "resource_id": "multiple",
                "recommendation": "Considerar whitelist de IPs",
                "description": f"{len(no_whitelist)} endpoint(s) sem whitelist. "
                               "Considerar restringir acesso para maior segurança.",
                "priority": "medium"
            })

        return recommendations
