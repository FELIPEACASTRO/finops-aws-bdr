"""
AWS Textract Service para FinOps.

Análise de custos e otimização de extração de texto de documentos.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class TextractAdapter:
    """Adapter de processamento Textract."""
    adapter_id: str
    adapter_name: str = ""
    status: str = "ACTIVE"
    creation_time: Optional[datetime] = None
    feature_types: List[str] = field(default_factory=list)
    auto_update: str = "DISABLED"
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se adapter está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "CREATING"

    @property
    def has_auto_update(self) -> bool:
        """Verifica se tem auto update."""
        return self.auto_update == "ENABLED"

    @property
    def supports_queries(self) -> bool:
        """Verifica se suporta queries."""
        return "QUERIES" in self.feature_types

    @property
    def supports_tables(self) -> bool:
        """Verifica se suporta tabelas."""
        return "TABLES" in self.feature_types

    @property
    def supports_forms(self) -> bool:
        """Verifica se suporta formulários."""
        return "FORMS" in self.feature_types

    @property
    def age_days(self) -> int:
        """Idade do adapter em dias."""
        if self.creation_time:
            return (datetime.now(self.creation_time.tzinfo) - self.creation_time).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "status": self.status,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "feature_types": self.feature_types,
            "auto_update": self.auto_update,
            "is_active": self.is_active,
            "is_creating": self.is_creating,
            "has_auto_update": self.has_auto_update,
            "supports_queries": self.supports_queries,
            "supports_tables": self.supports_tables,
            "supports_forms": self.supports_forms,
            "age_days": self.age_days
        }


@dataclass
class AdapterVersion:
    """Versão de adapter Textract."""
    adapter_id: str
    adapter_version: str
    status: str = "ACTIVE"
    creation_time: Optional[datetime] = None
    feature_types: List[str] = field(default_factory=list)
    status_message: str = ""
    dataset_config: Dict[str, Any] = field(default_factory=dict)
    kms_key_id: Optional[str] = None
    output_config: Dict[str, Any] = field(default_factory=dict)
    evaluation_metrics: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_training(self) -> bool:
        """Verifica se está treinando."""
        return self.status == "TRAINING"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "FAILED"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.kms_key_id is not None

    @property
    def average_f1_score(self) -> float:
        """F1 score médio das métricas de avaliação."""
        if not self.evaluation_metrics:
            return 0.0
        f1_scores = [m.get('F1Score', 0) for m in self.evaluation_metrics]
        return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "status": self.status,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "feature_types": self.feature_types,
            "status_message": self.status_message,
            "kms_key_id": self.kms_key_id,
            "is_active": self.is_active,
            "is_training": self.is_training,
            "is_failed": self.is_failed,
            "has_encryption": self.has_encryption,
            "average_f1_score": self.average_f1_score
        }


@dataclass
class TextractJob:
    """Job de análise Textract."""
    job_id: str
    job_tag: str = ""
    job_status: str = "SUCCEEDED"
    document_location: Dict[str, Any] = field(default_factory=dict)
    status_message: str = ""
    api_type: str = "DetectDocumentText"
    feature_types: List[str] = field(default_factory=list)
    pages_processed: int = 0

    @property
    def is_succeeded(self) -> bool:
        """Verifica se foi bem sucedido."""
        return self.job_status == "SUCCEEDED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.job_status == "FAILED"

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.job_status == "IN_PROGRESS"

    @property
    def is_partial_success(self) -> bool:
        """Verifica se teve sucesso parcial."""
        return self.job_status == "PARTIAL_SUCCESS"

    @property
    def is_document_detection(self) -> bool:
        """Verifica se é detecção de documento."""
        return self.api_type == "DetectDocumentText"

    @property
    def is_document_analysis(self) -> bool:
        """Verifica se é análise de documento."""
        return self.api_type == "AnalyzeDocument"

    @property
    def is_expense_analysis(self) -> bool:
        """Verifica se é análise de despesas."""
        return self.api_type == "AnalyzeExpense"

    @property
    def estimated_cost(self) -> float:
        """Custo estimado baseado em páginas e tipo."""
        if self.is_document_detection:
            return self.pages_processed * 0.0015
        elif self.is_document_analysis:
            return self.pages_processed * 0.015
        elif self.is_expense_analysis:
            return self.pages_processed * 0.01
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "job_tag": self.job_tag,
            "job_status": self.job_status,
            "status_message": self.status_message,
            "api_type": self.api_type,
            "feature_types": self.feature_types,
            "pages_processed": self.pages_processed,
            "is_succeeded": self.is_succeeded,
            "is_failed": self.is_failed,
            "is_in_progress": self.is_in_progress,
            "is_partial_success": self.is_partial_success,
            "is_document_detection": self.is_document_detection,
            "is_document_analysis": self.is_document_analysis,
            "is_expense_analysis": self.is_expense_analysis,
            "estimated_cost": self.estimated_cost
        }


@dataclass
class LendingAnalysisJob:
    """Job de análise de empréstimos Textract."""
    job_id: str
    job_tag: str = ""
    job_status: str = "SUCCEEDED"
    status_message: str = ""
    document_metadata: Dict[str, Any] = field(default_factory=dict)
    kms_key_id: Optional[str] = None
    output_config: Dict[str, Any] = field(default_factory=dict)
    creation_time: Optional[datetime] = None

    @property
    def is_succeeded(self) -> bool:
        """Verifica se foi bem sucedido."""
        return self.job_status == "SUCCEEDED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.job_status == "FAILED"

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.job_status == "IN_PROGRESS"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.kms_key_id is not None

    @property
    def pages_count(self) -> int:
        """Número de páginas."""
        return self.document_metadata.get('Pages', 0)

    @property
    def estimated_cost(self) -> float:
        """Custo estimado para lending analysis."""
        return self.pages_count * 0.07  # $0.07 por página

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "job_tag": self.job_tag,
            "job_status": self.job_status,
            "status_message": self.status_message,
            "kms_key_id": self.kms_key_id,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "is_succeeded": self.is_succeeded,
            "is_failed": self.is_failed,
            "is_in_progress": self.is_in_progress,
            "has_encryption": self.has_encryption,
            "pages_count": self.pages_count,
            "estimated_cost": self.estimated_cost
        }


class TextractService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Textract."""

    def __init__(self, client_factory):
        """Inicializa o serviço Textract."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._textract_client = None

    @property
    def textract_client(self):
        """Cliente Textract com lazy loading."""
        if self._textract_client is None:
            self._textract_client = self._client_factory.get_client('textract')
        return self._textract_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Textract."""
        try:
            self.textract_client.list_adapters(MaxResults=1)
            return {
                "service": "textract",
                "status": "healthy",
                "message": "Textract service is accessible"
            }
        except Exception as e:
            return {
                "service": "textract",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_adapters(self) -> List[TextractAdapter]:
        """Lista adapters Textract."""
        adapters = []
        try:
            paginator = self.textract_client.get_paginator('list_adapters')
            for page in paginator.paginate():
                for adapter in page.get('Adapters', []):
                    adapters.append(TextractAdapter(
                        adapter_id=adapter.get('AdapterId', ''),
                        adapter_name=adapter.get('AdapterName', ''),
                        creation_time=adapter.get('CreationTime'),
                        feature_types=adapter.get('FeatureTypes', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar adapters: {e}")
        return adapters

    def get_adapter_versions(self, adapter_id: str) -> List[AdapterVersion]:
        """Lista versões de um adapter."""
        versions = []
        try:
            paginator = self.textract_client.get_paginator('list_adapter_versions')
            for page in paginator.paginate(AdapterId=adapter_id):
                for ver in page.get('AdapterVersions', []):
                    try:
                        details = self.textract_client.get_adapter_version(
                            AdapterId=adapter_id,
                            AdapterVersion=ver.get('AdapterVersion', '')
                        )
                        versions.append(AdapterVersion(
                            adapter_id=adapter_id,
                            adapter_version=details.get('AdapterVersion', ''),
                            status=details.get('Status', 'ACTIVE'),
                            creation_time=details.get('CreationTime'),
                            feature_types=details.get('FeatureTypes', []),
                            status_message=details.get('StatusMessage', ''),
                            dataset_config=details.get('DatasetConfig', {}),
                            kms_key_id=details.get('KMSKeyId'),
                            output_config=details.get('OutputConfig', {}),
                            evaluation_metrics=details.get('EvaluationMetrics', [])
                        ))
                    except Exception as e:  # noqa: E722
                        versions.append(AdapterVersion(
                            adapter_id=adapter_id,
                            adapter_version=ver.get('AdapterVersion', ''),
                            status=ver.get('Status', 'ACTIVE'),
                            creation_time=ver.get('CreationTime'),
                            feature_types=ver.get('FeatureTypes', [])
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar versões do adapter: {e}")
        return versions

    def get_document_analysis_jobs(self) -> List[TextractJob]:
        """Lista jobs de análise de documentos recentes."""
        jobs = []
        return jobs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Textract."""
        adapters = self.get_adapters()
        all_versions = []
        for adapter in adapters:
            versions = self.get_adapter_versions(adapter.adapter_id)
            all_versions.extend(versions)

        active_adapters = [a for a in adapters if a.is_active]
        
        return {
            "adapters": [a.to_dict() for a in adapters],
            "adapter_versions": [v.to_dict() for v in all_versions],
            "summary": {
                "total_adapters": len(adapters),
                "active_adapters": len(active_adapters),
                "total_versions": len(all_versions),
                "active_versions": len([v for v in all_versions if v.is_active]),
                "training_versions": len([v for v in all_versions if v.is_training]),
                "failed_versions": len([v for v in all_versions if v.is_failed]),
                "encrypted_versions": len([v for v in all_versions if v.has_encryption]),
                "adapters_with_queries": len([a for a in adapters if a.supports_queries]),
                "adapters_with_tables": len([a for a in adapters if a.supports_tables]),
                "adapters_with_forms": len([a for a in adapters if a.supports_forms])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Textract."""
        adapters = self.get_adapters()
        all_versions = []
        for adapter in adapters:
            versions = self.get_adapter_versions(adapter.adapter_id)
            all_versions.extend(versions)

        return {
            "adapters_count": len(adapters),
            "active_adapters": len([a for a in adapters if a.is_active]),
            "versions_count": len(all_versions),
            "active_versions": len([v for v in all_versions if v.is_active]),
            "training_versions": len([v for v in all_versions if v.is_training]),
            "average_f1_score": sum(v.average_f1_score for v in all_versions) / len(all_versions) if all_versions else 0.0,
            "encrypted_versions": len([v for v in all_versions if v.has_encryption]),
            "adapters_with_auto_update": len([a for a in adapters if a.has_auto_update]),
            "feature_coverage": {
                "queries": len([a for a in adapters if a.supports_queries]),
                "tables": len([a for a in adapters if a.supports_tables]),
                "forms": len([a for a in adapters if a.supports_forms])
            }
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Textract."""
        recommendations = []
        adapters = self.get_adapters()
        all_versions = []
        for adapter in adapters:
            versions = self.get_adapter_versions(adapter.adapter_id)
            all_versions.extend(versions)

        # Verificar versões com baixo F1 score
        for ver in all_versions:
            if ver.is_active and ver.average_f1_score < 0.7 and ver.average_f1_score > 0:
                recommendations.append({
                    "resource_type": "AdapterVersion",
                    "resource_id": f"{ver.adapter_id}/{ver.adapter_version}",
                    "recommendation": "Retreinar adapter com baixo F1 score",
                    "description": f"Versão '{ver.adapter_version}' tem F1 score de {ver.average_f1_score:.2f}. "
                                   "Considerar retreinar com mais dados.",
                    "priority": "high"
                })

        # Verificar versões sem criptografia
        for ver in all_versions:
            if ver.is_active and not ver.has_encryption:
                recommendations.append({
                    "resource_type": "AdapterVersion",
                    "resource_id": f"{ver.adapter_id}/{ver.adapter_version}",
                    "recommendation": "Habilitar criptografia KMS",
                    "description": f"Versão '{ver.adapter_version}' sem criptografia. "
                                   "Recomendado para segurança de dados.",
                    "priority": "medium"
                })

        # Verificar versões falhadas
        failed_versions = [v for v in all_versions if v.is_failed]
        if failed_versions:
            recommendations.append({
                "resource_type": "AdapterVersion",
                "resource_id": "multiple",
                "recommendation": "Investigar versões falhadas",
                "description": f"{len(failed_versions)} versão(ões) de adapter falharam. "
                               "Verificar dados de treinamento e configuração.",
                "priority": "high"
            })

        # Verificar adapters antigos sem auto-update
        for adapter in adapters:
            if adapter.is_active and adapter.age_days > 180 and not adapter.has_auto_update:
                recommendations.append({
                    "resource_type": "TextractAdapter",
                    "resource_id": adapter.adapter_name,
                    "recommendation": "Habilitar auto-update",
                    "description": f"Adapter '{adapter.adapter_name}' tem {adapter.age_days} dias "
                                   "e não tem auto-update. Considerar habilitar para melhorias automáticas.",
                    "priority": "low"
                })

        # Recomendar uso de batching para alto volume
        if len(adapters) > 5:
            recommendations.append({
                "resource_type": "Textract",
                "resource_id": "general",
                "recommendation": "Considerar Bulk Document Processing",
                "description": "Com múltiplos adapters, considerar usar processamento em lote "
                               "para otimizar custos e throughput.",
                "priority": "medium"
            })

        return recommendations
