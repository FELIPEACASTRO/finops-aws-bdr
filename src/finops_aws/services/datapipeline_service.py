"""
AWS Data Pipeline Service para FinOps.

Análise de custos e otimização de pipelines de dados.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class DataPipeline:
    """Data Pipeline."""
    pipeline_id: str
    name: str = ""
    description: str = ""
    state: str = "PENDING"
    health_status: str = "HEALTHY"
    creation_time: Optional[datetime] = None
    tags: List[Dict[str, str]] = field(default_factory=list)
    fields: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_pending(self) -> bool:
        """Verifica se está pendente."""
        return self.state == "PENDING"

    @property
    def is_scheduled(self) -> bool:
        """Verifica se está agendado."""
        return self.state == "SCHEDULED"

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.state == "RUNNING"

    @property
    def is_finished(self) -> bool:
        """Verifica se terminou."""
        return self.state == "FINISHED"

    @property
    def is_paused(self) -> bool:
        """Verifica se está pausado."""
        return self.state == "PAUSED"

    @property
    def is_deactivating(self) -> bool:
        """Verifica se está desativando."""
        return self.state == "DEACTIVATING"

    @property
    def is_healthy(self) -> bool:
        """Verifica se está saudável."""
        return self.health_status == "HEALTHY"

    @property
    def is_error(self) -> bool:
        """Verifica se tem erro."""
        return self.health_status == "ERROR"

    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return len(self.tags) > 0

    @property
    def unique_id(self) -> str:
        """ID único do pipeline."""
        for field_item in self.fields:
            if field_item.get('key') == 'uniqueId':
                return field_item.get('stringValue', '')
        return ''

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "state": self.state,
            "health_status": self.health_status,
            "is_running": self.is_running,
            "is_scheduled": self.is_scheduled,
            "is_healthy": self.is_healthy,
            "is_error": self.is_error,
            "has_tags": self.has_tags,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class DataPipelineObject:
    """Data Pipeline Object."""
    object_id: str
    name: str = ""
    fields: List[Dict[str, str]] = field(default_factory=list)

    @property
    def object_type(self) -> str:
        """Tipo do objeto."""
        for field_item in self.fields:
            if field_item.get('key') == 'type':
                return field_item.get('stringValue', '')
        return ''

    @property
    def is_activity(self) -> bool:
        """Verifica se é atividade."""
        return 'Activity' in self.object_type

    @property
    def is_data_node(self) -> bool:
        """Verifica se é data node."""
        return 'DataNode' in self.object_type or self.object_type in ['S3DataNode', 'SqlDataNode', 'DynamoDBDataNode']

    @property
    def is_schedule(self) -> bool:
        """Verifica se é schedule."""
        return self.object_type == 'Schedule'

    @property
    def is_resource(self) -> bool:
        """Verifica se é resource."""
        return self.object_type in ['Ec2Resource', 'EmrCluster']

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "object_id": self.object_id,
            "name": self.name,
            "object_type": self.object_type,
            "is_activity": self.is_activity,
            "is_data_node": self.is_data_node,
            "is_schedule": self.is_schedule,
            "is_resource": self.is_resource
        }


@dataclass
class DataPipelineTaskRun:
    """Data Pipeline Task Run."""
    task_id: str
    pipeline_id: str = ""
    attempt_id: str = ""
    task_status: str = "WAITING_ON_DEPENDENCIES"
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None

    @property
    def is_waiting(self) -> bool:
        """Verifica se está aguardando."""
        return self.task_status == "WAITING_ON_DEPENDENCIES"

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.task_status == "RUNNING"

    @property
    def is_finished(self) -> bool:
        """Verifica se terminou."""
        return self.task_status == "FINISHED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.task_status == "FAILED"

    @property
    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.task_status == "CANCELLED"

    @property
    def is_cascade_failed(self) -> bool:
        """Verifica se falhou em cascata."""
        return self.task_status == "CASCADE_FAILED"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "task_id": self.task_id,
            "pipeline_id": self.pipeline_id,
            "task_status": self.task_status,
            "is_running": self.is_running,
            "is_finished": self.is_finished,
            "is_failed": self.is_failed,
            "actual_start_time": self.actual_start_time.isoformat() if self.actual_start_time else None,
            "actual_end_time": self.actual_end_time.isoformat() if self.actual_end_time else None
        }


class DataPipelineService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Data Pipeline."""

    def __init__(self, client_factory):
        """Inicializa o serviço Data Pipeline."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._datapipeline_client = None

    @property
    def datapipeline_client(self):
        """Cliente Data Pipeline com lazy loading."""
        if self._datapipeline_client is None:
            self._datapipeline_client = self._client_factory.get_client('datapipeline')
        return self._datapipeline_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Data Pipeline."""
        try:
            self.datapipeline_client.list_pipelines()
            return {
                "service": "datapipeline",
                "status": "healthy",
                "message": "Data Pipeline service is accessible"
            }
        except Exception as e:
            return {
                "service": "datapipeline",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_pipelines(self) -> List[DataPipeline]:
        """Lista pipelines."""
        pipelines = []
        try:
            paginator = self.datapipeline_client.get_paginator('list_pipelines')
            pipeline_ids = []
            for page in paginator.paginate():
                for entry in page.get('pipelineIdList', []):
                    pipeline_ids.append(entry.get('id'))

            if pipeline_ids:
                for i in range(0, len(pipeline_ids), 25):
                    batch = pipeline_ids[i:i+25]
                    response = self.datapipeline_client.describe_pipelines(pipelineIds=batch)
                    for desc in response.get('pipelineDescriptionList', []):
                        pipelines.append(DataPipeline(
                            pipeline_id=desc.get('pipelineId', ''),
                            name=desc.get('name', ''),
                            description=desc.get('description', ''),
                            fields=desc.get('fields', []),
                            tags=desc.get('tags', [])
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar pipelines: {e}")
        return pipelines

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Data Pipeline."""
        pipelines = self.get_pipelines()

        return {
            "pipelines": [p.to_dict() for p in pipelines],
            "summary": {
                "total_pipelines": len(pipelines),
                "pending_pipelines": len([p for p in pipelines if p.is_pending]),
                "scheduled_pipelines": len([p for p in pipelines if p.is_scheduled]),
                "running_pipelines": len([p for p in pipelines if p.is_running]),
                "finished_pipelines": len([p for p in pipelines if p.is_finished]),
                "paused_pipelines": len([p for p in pipelines if p.is_paused]),
                "healthy_pipelines": len([p for p in pipelines if p.is_healthy]),
                "error_pipelines": len([p for p in pipelines if p.is_error]),
                "pipelines_with_tags": len([p for p in pipelines if p.has_tags])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Data Pipeline."""
        pipelines = self.get_pipelines()

        return {
            "pipelines_count": len(pipelines),
            "pending_pipelines": len([p for p in pipelines if p.is_pending]),
            "scheduled_pipelines": len([p for p in pipelines if p.is_scheduled]),
            "running_pipelines": len([p for p in pipelines if p.is_running]),
            "finished_pipelines": len([p for p in pipelines if p.is_finished]),
            "paused_pipelines": len([p for p in pipelines if p.is_paused]),
            "deactivating_pipelines": len([p for p in pipelines if p.is_deactivating]),
            "healthy_pipelines": len([p for p in pipelines if p.is_healthy]),
            "error_pipelines": len([p for p in pipelines if p.is_error]),
            "pipelines_with_tags": len([p for p in pipelines if p.has_tags])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Data Pipeline."""
        recommendations = []
        pipelines = self.get_pipelines()

        error_pipelines = [p for p in pipelines if p.is_error]
        if error_pipelines:
            recommendations.append({
                "resource_type": "DataPipeline",
                "resource_id": "multiple",
                "recommendation": "Corrigir pipelines com erro",
                "description": f"{len(error_pipelines)} pipeline(s) com status de erro. "
                               "Verificar logs e corrigir problemas.",
                "priority": "high"
            })

        paused_pipelines = [p for p in pipelines if p.is_paused]
        if paused_pipelines:
            recommendations.append({
                "resource_type": "DataPipeline",
                "resource_id": "multiple",
                "recommendation": "Revisar pipelines pausados",
                "description": f"{len(paused_pipelines)} pipeline(s) pausado(s). "
                               "Verificar se ainda são necessários ou podem ser removidos.",
                "priority": "low"
            })

        no_tags = [p for p in pipelines if not p.has_tags]
        if no_tags and len(pipelines) > 0:
            recommendations.append({
                "resource_type": "DataPipeline",
                "resource_id": "multiple",
                "recommendation": "Adicionar tags aos pipelines",
                "description": f"{len(no_tags)} pipeline(s) sem tags. "
                               "Adicionar tags para melhor organização e rastreamento de custos.",
                "priority": "low"
            })

        return recommendations
