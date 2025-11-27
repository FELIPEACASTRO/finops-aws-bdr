"""
AWS Athena Service para FinOps.

Análise de custos e otimização de consultas SQL serverless.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class AthenaWorkgroup:
    """Workgroup do Athena."""
    name: str
    state: str = "ENABLED"
    description: str = ""
    creation_time: Optional[datetime] = None
    bytes_scanned_cutoff_per_query: Optional[int] = None
    enforce_workgroup_configuration: bool = True
    publish_cloudwatch_metrics_enabled: bool = False
    requester_pays_enabled: bool = False
    engine_version: str = "Athena engine version 3"
    output_location: Optional[str] = None
    encryption_configuration: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_enabled(self) -> bool:
        """Verifica se workgroup está habilitado."""
        return self.state == "ENABLED"

    @property
    def has_query_limit(self) -> bool:
        """Verifica se tem limite de bytes por query."""
        return self.bytes_scanned_cutoff_per_query is not None

    @property
    def has_metrics(self) -> bool:
        """Verifica se publica métricas CloudWatch."""
        return self.publish_cloudwatch_metrics_enabled

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia configurada."""
        return bool(self.encryption_configuration)

    @property
    def query_limit_gb(self) -> float:
        """Limite de query em GB."""
        if self.bytes_scanned_cutoff_per_query:
            return self.bytes_scanned_cutoff_per_query / (1024 ** 3)
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "state": self.state,
            "description": self.description,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "bytes_scanned_cutoff_per_query": self.bytes_scanned_cutoff_per_query,
            "enforce_workgroup_configuration": self.enforce_workgroup_configuration,
            "publish_cloudwatch_metrics_enabled": self.publish_cloudwatch_metrics_enabled,
            "engine_version": self.engine_version,
            "output_location": self.output_location,
            "is_enabled": self.is_enabled,
            "has_query_limit": self.has_query_limit,
            "has_metrics": self.has_metrics,
            "has_encryption": self.has_encryption,
            "query_limit_gb": self.query_limit_gb
        }


@dataclass
class AthenaDataCatalog:
    """Catálogo de dados do Athena."""
    name: str
    catalog_type: str = "GLUE"
    description: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)

    @property
    def is_glue(self) -> bool:
        """Verifica se é catálogo Glue."""
        return self.catalog_type == "GLUE"

    @property
    def is_hive(self) -> bool:
        """Verifica se é catálogo Hive."""
        return self.catalog_type == "HIVE"

    @property
    def is_lambda(self) -> bool:
        """Verifica se é catálogo Lambda."""
        return self.catalog_type == "LAMBDA"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "catalog_type": self.catalog_type,
            "description": self.description,
            "parameters": self.parameters,
            "is_glue": self.is_glue,
            "is_hive": self.is_hive,
            "is_lambda": self.is_lambda
        }


@dataclass
class AthenaPreparedStatement:
    """Prepared statement do Athena."""
    statement_name: str
    workgroup_name: str
    query_statement: str = ""
    description: str = ""
    last_modified_time: Optional[datetime] = None

    @property
    def query_length(self) -> int:
        """Tamanho da query."""
        return len(self.query_statement)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "statement_name": self.statement_name,
            "workgroup_name": self.workgroup_name,
            "query_statement": self.query_statement[:100] + "..." if len(self.query_statement) > 100 else self.query_statement,
            "description": self.description,
            "last_modified_time": self.last_modified_time.isoformat() if self.last_modified_time else None,
            "query_length": self.query_length
        }


@dataclass
class AthenaQueryExecution:
    """Execução de query do Athena."""
    query_execution_id: str
    query: str = ""
    state: str = "SUCCEEDED"
    workgroup: str = "primary"
    database: Optional[str] = None
    data_scanned_bytes: int = 0
    execution_time_ms: int = 0
    submission_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None

    @property
    def is_succeeded(self) -> bool:
        """Verifica se foi bem sucedida."""
        return self.state == "SUCCEEDED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.state == "FAILED"

    @property
    def is_running(self) -> bool:
        """Verifica se está em execução."""
        return self.state == "RUNNING"

    @property
    def data_scanned_gb(self) -> float:
        """Dados escaneados em GB."""
        return self.data_scanned_bytes / (1024 ** 3)

    @property
    def execution_time_seconds(self) -> float:
        """Tempo de execução em segundos."""
        return self.execution_time_ms / 1000

    @property
    def estimated_cost(self) -> float:
        """Custo estimado ($5 por TB escaneado)."""
        return (self.data_scanned_bytes / (1024 ** 4)) * 5.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "query_execution_id": self.query_execution_id,
            "query": self.query[:100] + "..." if len(self.query) > 100 else self.query,
            "state": self.state,
            "workgroup": self.workgroup,
            "database": self.database,
            "data_scanned_bytes": self.data_scanned_bytes,
            "data_scanned_gb": self.data_scanned_gb,
            "execution_time_ms": self.execution_time_ms,
            "execution_time_seconds": self.execution_time_seconds,
            "is_succeeded": self.is_succeeded,
            "is_failed": self.is_failed,
            "estimated_cost": self.estimated_cost
        }


class AthenaService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Athena."""

    def __init__(self, client_factory):
        """Inicializa o serviço Athena."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._athena_client = None

    @property
    def athena_client(self):
        """Cliente Athena com lazy loading."""
        if self._athena_client is None:
            self._athena_client = self._client_factory.get_client('athena')
        return self._athena_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Athena."""
        try:
            self.athena_client.list_work_groups(MaxResults=1)
            return {
                "service": "athena",
                "status": "healthy",
                "message": "Athena service is accessible"
            }
        except Exception as e:
            return {
                "service": "athena",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_workgroups(self) -> List[AthenaWorkgroup]:
        """Lista workgroups do Athena."""
        workgroups = []
        try:
            paginator = self.athena_client.get_paginator('list_work_groups')
            for page in paginator.paginate():
                for wg in page.get('WorkGroups', []):
                    try:
                        details = self.athena_client.get_work_group(WorkGroup=wg.get('Name', ''))
                        wg_config = details.get('WorkGroup', {})
                        config = wg_config.get('Configuration', {})
                        result_config = config.get('ResultConfiguration', {})
                        workgroups.append(AthenaWorkgroup(
                            name=wg_config.get('Name', ''),
                            state=wg_config.get('State', 'ENABLED'),
                            description=wg_config.get('Description', ''),
                            creation_time=wg_config.get('CreationTime'),
                            bytes_scanned_cutoff_per_query=config.get('BytesScannedCutoffPerQuery'),
                            enforce_workgroup_configuration=config.get('EnforceWorkGroupConfiguration', True),
                            publish_cloudwatch_metrics_enabled=config.get('PublishCloudWatchMetricsEnabled', False),
                            requester_pays_enabled=config.get('RequesterPaysEnabled', False),
                            engine_version=config.get('EngineVersion', {}).get('SelectedEngineVersion', ''),
                            output_location=result_config.get('OutputLocation'),
                            encryption_configuration=result_config.get('EncryptionConfiguration', {})
                        ))
                    except Exception:
                        workgroups.append(AthenaWorkgroup(
                            name=wg.get('Name', ''),
                            state=wg.get('State', 'ENABLED'),
                            description=wg.get('Description', ''),
                            creation_time=wg.get('CreationTime')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar workgroups: {e}")
        return workgroups

    def get_data_catalogs(self) -> List[AthenaDataCatalog]:
        """Lista catálogos de dados."""
        catalogs = []
        try:
            paginator = self.athena_client.get_paginator('list_data_catalogs')
            for page in paginator.paginate():
                for cat in page.get('DataCatalogsSummary', []):
                    catalogs.append(AthenaDataCatalog(
                        name=cat.get('CatalogName', ''),
                        catalog_type=cat.get('Type', 'GLUE'),
                        description=cat.get('Description', ''),
                        parameters=cat.get('Parameters', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar catálogos: {e}")
        return catalogs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Athena."""
        workgroups = self.get_workgroups()
        data_catalogs = self.get_data_catalogs()

        return {
            "workgroups": [wg.to_dict() for wg in workgroups],
            "data_catalogs": [dc.to_dict() for dc in data_catalogs],
            "summary": {
                "total_workgroups": len(workgroups),
                "enabled_workgroups": len([wg for wg in workgroups if wg.is_enabled]),
                "workgroups_with_limits": len([wg for wg in workgroups if wg.has_query_limit]),
                "workgroups_with_metrics": len([wg for wg in workgroups if wg.has_metrics]),
                "workgroups_with_encryption": len([wg for wg in workgroups if wg.has_encryption]),
                "total_catalogs": len(data_catalogs),
                "glue_catalogs": len([dc for dc in data_catalogs if dc.is_glue])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Athena."""
        workgroups = self.get_workgroups()
        data_catalogs = self.get_data_catalogs()

        return {
            "workgroups_count": len(workgroups),
            "enabled_workgroups": len([wg for wg in workgroups if wg.is_enabled]),
            "workgroups_with_query_limits": len([wg for wg in workgroups if wg.has_query_limit]),
            "workgroups_with_cloudwatch_metrics": len([wg for wg in workgroups if wg.has_metrics]),
            "workgroups_with_encryption": len([wg for wg in workgroups if wg.has_encryption]),
            "data_catalogs_count": len(data_catalogs),
            "catalog_types": {
                "glue": len([dc for dc in data_catalogs if dc.is_glue]),
                "hive": len([dc for dc in data_catalogs if dc.is_hive]),
                "lambda": len([dc for dc in data_catalogs if dc.is_lambda])
            }
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Athena."""
        recommendations = []
        workgroups = self.get_workgroups()

        for wg in workgroups:
            if wg.is_enabled and not wg.has_query_limit:
                recommendations.append({
                    "resource_type": "AthenaWorkgroup",
                    "resource_id": wg.name,
                    "recommendation": "Configurar limite de bytes por query",
                    "description": f"Workgroup '{wg.name}' não tem limite de dados escaneados. "
                                   "Configurar BytesScannedCutoffPerQuery para evitar custos inesperados.",
                    "priority": "high"
                })

            if wg.is_enabled and not wg.has_metrics:
                recommendations.append({
                    "resource_type": "AthenaWorkgroup",
                    "resource_id": wg.name,
                    "recommendation": "Habilitar métricas CloudWatch",
                    "description": f"Workgroup '{wg.name}' não publica métricas no CloudWatch. "
                                   "Habilitar para monitorar custos e performance.",
                    "priority": "medium"
                })

            if wg.is_enabled and not wg.has_encryption:
                recommendations.append({
                    "resource_type": "AthenaWorkgroup",
                    "resource_id": wg.name,
                    "recommendation": "Habilitar criptografia de resultados",
                    "description": f"Workgroup '{wg.name}' não tem criptografia de resultados. "
                                   "Recomendado para segurança de dados.",
                    "priority": "medium"
                })

        return recommendations
