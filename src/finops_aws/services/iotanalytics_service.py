"""
AWS IoT Analytics Service para FinOps.

Análise de custos e otimização de recursos IoT Analytics.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class IoTAnalyticsChannel:
    """Channel IoT Analytics."""
    channel_name: str
    channel_arn: str = ""
    status: str = "ACTIVE"
    retention_period: Dict[str, Any] = field(default_factory=dict)
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    last_message_arrival_time: Optional[datetime] = None
    storage: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def retention_days(self) -> int:
        """Dias de retenção."""
        if self.retention_period.get('unlimited'):
            return -1
        return self.retention_period.get('numberOfDays', 0)

    @property
    def has_unlimited_retention(self) -> bool:
        """Verifica se tem retenção ilimitada."""
        return self.retention_period.get('unlimited', False)

    @property
    def uses_customer_managed_s3(self) -> bool:
        """Verifica se usa S3 gerenciado pelo cliente."""
        return 'customerManagedS3' in self.storage

    @property
    def uses_service_managed_s3(self) -> bool:
        """Verifica se usa S3 gerenciado pelo serviço."""
        return 'serviceManagedS3' in self.storage

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "channel_name": self.channel_name,
            "channel_arn": self.channel_arn,
            "status": self.status,
            "is_active": self.is_active,
            "retention_days": self.retention_days,
            "has_unlimited_retention": self.has_unlimited_retention,
            "uses_customer_managed_s3": self.uses_customer_managed_s3,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class IoTAnalyticsDatastore:
    """Datastore IoT Analytics."""
    datastore_name: str
    datastore_arn: str = ""
    status: str = "ACTIVE"
    retention_period: Dict[str, Any] = field(default_factory=dict)
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    last_message_arrival_time: Optional[datetime] = None
    storage: Dict[str, Any] = field(default_factory=dict)
    file_format_configuration: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def retention_days(self) -> int:
        """Dias de retenção."""
        if self.retention_period.get('unlimited'):
            return -1
        return self.retention_period.get('numberOfDays', 0)

    @property
    def has_unlimited_retention(self) -> bool:
        """Verifica se tem retenção ilimitada."""
        return self.retention_period.get('unlimited', False)

    @property
    def uses_parquet(self) -> bool:
        """Verifica se usa formato Parquet."""
        return 'parquetConfiguration' in self.file_format_configuration

    @property
    def uses_json(self) -> bool:
        """Verifica se usa formato JSON."""
        return 'jsonConfiguration' in self.file_format_configuration or not self.file_format_configuration

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "datastore_name": self.datastore_name,
            "datastore_arn": self.datastore_arn,
            "status": self.status,
            "is_active": self.is_active,
            "retention_days": self.retention_days,
            "has_unlimited_retention": self.has_unlimited_retention,
            "uses_parquet": self.uses_parquet,
            "uses_json": self.uses_json,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class IoTAnalyticsPipeline:
    """Pipeline IoT Analytics."""
    pipeline_name: str
    pipeline_arn: str = ""
    activities: List[Dict[str, Any]] = field(default_factory=list)
    reprocessing_summaries: List[Dict[str, Any]] = field(default_factory=list)
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None

    @property
    def activities_count(self) -> int:
        """Número de atividades."""
        return len(self.activities)

    @property
    def has_lambda_activity(self) -> bool:
        """Verifica se tem atividade Lambda."""
        return any('lambda' in str(a).lower() for a in self.activities)

    @property
    def has_filter_activity(self) -> bool:
        """Verifica se tem atividade de filtro."""
        return any('filter' in str(a).lower() for a in self.activities)

    @property
    def is_reprocessing(self) -> bool:
        """Verifica se está em reprocessamento."""
        for summary in self.reprocessing_summaries:
            if summary.get('status') == 'RUNNING':
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "pipeline_name": self.pipeline_name,
            "pipeline_arn": self.pipeline_arn,
            "activities_count": self.activities_count,
            "has_lambda_activity": self.has_lambda_activity,
            "has_filter_activity": self.has_filter_activity,
            "is_reprocessing": self.is_reprocessing,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class IoTAnalyticsDataset:
    """Dataset IoT Analytics."""
    dataset_name: str
    dataset_arn: str = ""
    status: str = "ACTIVE"
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    retention_period: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    content_delivery_rules: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def actions_count(self) -> int:
        """Número de ações."""
        return len(self.actions)

    @property
    def triggers_count(self) -> int:
        """Número de triggers."""
        return len(self.triggers)

    @property
    def has_schedule_trigger(self) -> bool:
        """Verifica se tem trigger agendado."""
        return any('schedule' in str(t).lower() for t in self.triggers)

    @property
    def has_content_delivery(self) -> bool:
        """Verifica se tem entrega de conteúdo."""
        return len(self.content_delivery_rules) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "dataset_name": self.dataset_name,
            "dataset_arn": self.dataset_arn,
            "status": self.status,
            "is_active": self.is_active,
            "actions_count": self.actions_count,
            "triggers_count": self.triggers_count,
            "has_schedule_trigger": self.has_schedule_trigger,
            "has_content_delivery": self.has_content_delivery,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


class IoTAnalyticsService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS IoT Analytics."""

    def __init__(self, client_factory):
        """Inicializa o serviço IoT Analytics."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._iotanalytics_client = None

    @property
    def iotanalytics_client(self):
        """Cliente IoT Analytics com lazy loading."""
        if self._iotanalytics_client is None:
            self._iotanalytics_client = self._client_factory.get_client('iotanalytics')
        return self._iotanalytics_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço IoT Analytics."""
        try:
            self.iotanalytics_client.list_channels(maxResults=1)
            return {
                "service": "iotanalytics",
                "status": "healthy",
                "message": "IoT Analytics service is accessible"
            }
        except Exception as e:
            return {
                "service": "iotanalytics",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_channels(self) -> List[IoTAnalyticsChannel]:
        """Lista channels."""
        channels = []
        try:
            paginator = self.iotanalytics_client.get_paginator('list_channels')
            for page in paginator.paginate():
                for ch in page.get('channelSummaries', []):
                    channels.append(IoTAnalyticsChannel(
                        channel_name=ch.get('channelName', ''),
                        status=ch.get('status', 'ACTIVE'),
                        creation_time=ch.get('creationTime'),
                        last_update_time=ch.get('lastUpdateTime'),
                        last_message_arrival_time=ch.get('lastMessageArrivalTime'),
                        storage=ch.get('channelStorage', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar channels: {e}")
        return channels

    def get_datastores(self) -> List[IoTAnalyticsDatastore]:
        """Lista datastores."""
        datastores = []
        try:
            paginator = self.iotanalytics_client.get_paginator('list_datastores')
            for page in paginator.paginate():
                for ds in page.get('datastoreSummaries', []):
                    datastores.append(IoTAnalyticsDatastore(
                        datastore_name=ds.get('datastoreName', ''),
                        status=ds.get('status', 'ACTIVE'),
                        creation_time=ds.get('creationTime'),
                        last_update_time=ds.get('lastUpdateTime'),
                        last_message_arrival_time=ds.get('lastMessageArrivalTime'),
                        storage=ds.get('datastoreStorage', {}),
                        file_format_configuration=ds.get('fileFormatConfiguration', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar datastores: {e}")
        return datastores

    def get_pipelines(self) -> List[IoTAnalyticsPipeline]:
        """Lista pipelines."""
        pipelines = []
        try:
            paginator = self.iotanalytics_client.get_paginator('list_pipelines')
            for page in paginator.paginate():
                for pl in page.get('pipelineSummaries', []):
                    pipelines.append(IoTAnalyticsPipeline(
                        pipeline_name=pl.get('pipelineName', ''),
                        creation_time=pl.get('creationTime'),
                        last_update_time=pl.get('lastUpdateTime'),
                        reprocessing_summaries=pl.get('reprocessingSummaries', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar pipelines: {e}")
        return pipelines

    def get_datasets(self) -> List[IoTAnalyticsDataset]:
        """Lista datasets."""
        datasets = []
        try:
            paginator = self.iotanalytics_client.get_paginator('list_datasets')
            for page in paginator.paginate():
                for ds in page.get('datasetSummaries', []):
                    datasets.append(IoTAnalyticsDataset(
                        dataset_name=ds.get('datasetName', ''),
                        status=ds.get('status', 'ACTIVE'),
                        creation_time=ds.get('creationTime'),
                        last_update_time=ds.get('lastUpdateTime'),
                        actions=ds.get('actions', []),
                        triggers=ds.get('triggers', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar datasets: {e}")
        return datasets

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos IoT Analytics."""
        channels = self.get_channels()
        datastores = self.get_datastores()
        pipelines = self.get_pipelines()
        datasets = self.get_datasets()

        return {
            "channels": [c.to_dict() for c in channels],
            "datastores": [d.to_dict() for d in datastores],
            "pipelines": [p.to_dict() for p in pipelines],
            "datasets": [d.to_dict() for d in datasets],
            "summary": {
                "total_channels": len(channels),
                "active_channels": len([c for c in channels if c.is_active]),
                "channels_with_unlimited_retention": len([c for c in channels if c.has_unlimited_retention]),
                "total_datastores": len(datastores),
                "active_datastores": len([d for d in datastores if d.is_active]),
                "datastores_using_parquet": len([d for d in datastores if d.uses_parquet]),
                "total_pipelines": len(pipelines),
                "pipelines_with_lambda": len([p for p in pipelines if p.has_lambda_activity]),
                "total_datasets": len(datasets),
                "active_datasets": len([d for d in datasets if d.is_active])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do IoT Analytics."""
        channels = self.get_channels()
        datastores = self.get_datastores()
        pipelines = self.get_pipelines()
        datasets = self.get_datasets()

        return {
            "channels_count": len(channels),
            "active_channels": len([c for c in channels if c.is_active]),
            "channels_unlimited_retention": len([c for c in channels if c.has_unlimited_retention]),
            "datastores_count": len(datastores),
            "active_datastores": len([d for d in datastores if d.is_active]),
            "datastores_parquet": len([d for d in datastores if d.uses_parquet]),
            "datastores_json": len([d for d in datastores if d.uses_json]),
            "pipelines_count": len(pipelines),
            "pipelines_with_lambda": len([p for p in pipelines if p.has_lambda_activity]),
            "pipelines_reprocessing": len([p for p in pipelines if p.is_reprocessing]),
            "datasets_count": len(datasets),
            "active_datasets": len([d for d in datasets if d.is_active]),
            "datasets_with_triggers": len([d for d in datasets if d.triggers_count > 0])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para IoT Analytics."""
        recommendations = []
        channels = self.get_channels()
        datastores = self.get_datastores()

        unlimited_channels = [c for c in channels if c.has_unlimited_retention]
        if unlimited_channels:
            recommendations.append({
                "resource_type": "IoTAnalyticsChannel",
                "resource_id": "multiple",
                "recommendation": "Configurar retenção em channels",
                "description": f"{len(unlimited_channels)} channel(s) com retenção ilimitada. "
                               "Configurar período de retenção para otimizar custos.",
                "priority": "medium"
            })

        json_datastores = [d for d in datastores if d.uses_json and not d.uses_parquet]
        if json_datastores:
            recommendations.append({
                "resource_type": "IoTAnalyticsDatastore",
                "resource_id": "multiple",
                "recommendation": "Usar formato Parquet",
                "description": f"{len(json_datastores)} datastore(s) usando JSON. "
                               "Considerar Parquet para melhor performance e menor custo.",
                "priority": "medium"
            })

        return recommendations
