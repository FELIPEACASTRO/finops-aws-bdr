"""
AWS Comprehend Service para FinOps.

Análise de custos e otimização de processamento de linguagem natural.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class ComprehendEndpoint:
    """Endpoint de inferência Comprehend."""
    endpoint_arn: str
    endpoint_name: str = ""
    status: str = "IN_SERVICE"
    model_arn: Optional[str] = None
    desired_model_arn: Optional[str] = None
    desired_inference_units: int = 1
    current_inference_units: int = 1
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    data_access_role_arn: Optional[str] = None
    desired_data_access_role_arn: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Verifica se endpoint está ativo."""
        return self.status == "IN_SERVICE"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "CREATING"

    @property
    def is_updating(self) -> bool:
        """Verifica se está atualizando."""
        return self.status == "UPDATING"

    @property
    def is_scaling(self) -> bool:
        """Verifica se está escalando."""
        return self.current_inference_units != self.desired_inference_units

    @property
    def age_days(self) -> int:
        """Idade do endpoint em dias."""
        if self.creation_time:
            return (datetime.now(self.creation_time.tzinfo) - self.creation_time).days
        return 0

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado por inference unit."""
        cost_per_unit_hour = 0.50  # Estimativa base
        return self.current_inference_units * cost_per_unit_hour * 730

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "endpoint_arn": self.endpoint_arn,
            "endpoint_name": self.endpoint_name,
            "status": self.status,
            "model_arn": self.model_arn,
            "desired_inference_units": self.desired_inference_units,
            "current_inference_units": self.current_inference_units,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "last_modified_time": self.last_modified_time.isoformat() if self.last_modified_time else None,
            "is_active": self.is_active,
            "is_creating": self.is_creating,
            "is_updating": self.is_updating,
            "is_scaling": self.is_scaling,
            "age_days": self.age_days,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class EntityRecognizer:
    """Reconhecedor de entidades customizado."""
    entity_recognizer_arn: str
    recognizer_name: str = ""
    language_code: str = "en"
    status: str = "TRAINED"
    version_name: Optional[str] = None
    model_kms_key_id: Optional[str] = None
    creation_time: Optional[datetime] = None
    training_start_time: Optional[datetime] = None
    training_end_time: Optional[datetime] = None
    input_data_config: Dict[str, Any] = field(default_factory=dict)
    recognizer_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_trained(self) -> bool:
        """Verifica se está treinado."""
        return self.status == "TRAINED"

    @property
    def is_training(self) -> bool:
        """Verifica se está treinando."""
        return self.status == "TRAINING"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status in ["IN_ERROR", "FAILED"]

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.model_kms_key_id is not None

    @property
    def training_duration_hours(self) -> float:
        """Duração do treinamento em horas."""
        if self.training_start_time and self.training_end_time:
            return (self.training_end_time - self.training_start_time).total_seconds() / 3600
        return 0.0

    @property
    def entity_types_count(self) -> int:
        """Número de tipos de entidade."""
        return len(self.recognizer_metadata.get('EntityTypes', []))

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "entity_recognizer_arn": self.entity_recognizer_arn,
            "recognizer_name": self.recognizer_name,
            "language_code": self.language_code,
            "status": self.status,
            "version_name": self.version_name,
            "model_kms_key_id": self.model_kms_key_id,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "training_start_time": self.training_start_time.isoformat() if self.training_start_time else None,
            "training_end_time": self.training_end_time.isoformat() if self.training_end_time else None,
            "is_trained": self.is_trained,
            "is_training": self.is_training,
            "is_failed": self.is_failed,
            "has_encryption": self.has_encryption,
            "training_duration_hours": self.training_duration_hours,
            "entity_types_count": self.entity_types_count
        }


@dataclass
class DocumentClassifier:
    """Classificador de documentos customizado."""
    document_classifier_arn: str
    classifier_name: str = ""
    language_code: str = "en"
    status: str = "TRAINED"
    version_name: Optional[str] = None
    model_kms_key_id: Optional[str] = None
    mode: str = "MULTI_CLASS"
    creation_time: Optional[datetime] = None
    training_start_time: Optional[datetime] = None
    training_end_time: Optional[datetime] = None
    input_data_config: Dict[str, Any] = field(default_factory=dict)
    output_data_config: Dict[str, Any] = field(default_factory=dict)
    classifier_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_trained(self) -> bool:
        """Verifica se está treinado."""
        return self.status == "TRAINED"

    @property
    def is_training(self) -> bool:
        """Verifica se está treinando."""
        return self.status == "TRAINING"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status in ["IN_ERROR", "FAILED"]

    @property
    def is_multi_class(self) -> bool:
        """Verifica se é multi-class."""
        return self.mode == "MULTI_CLASS"

    @property
    def is_multi_label(self) -> bool:
        """Verifica se é multi-label."""
        return self.mode == "MULTI_LABEL"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.model_kms_key_id is not None

    @property
    def training_duration_hours(self) -> float:
        """Duração do treinamento em horas."""
        if self.training_start_time and self.training_end_time:
            return (self.training_end_time - self.training_start_time).total_seconds() / 3600
        return 0.0

    @property
    def labels_count(self) -> int:
        """Número de labels."""
        return self.classifier_metadata.get('NumberOfLabels', 0)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "document_classifier_arn": self.document_classifier_arn,
            "classifier_name": self.classifier_name,
            "language_code": self.language_code,
            "status": self.status,
            "version_name": self.version_name,
            "model_kms_key_id": self.model_kms_key_id,
            "mode": self.mode,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "training_start_time": self.training_start_time.isoformat() if self.training_start_time else None,
            "training_end_time": self.training_end_time.isoformat() if self.training_end_time else None,
            "is_trained": self.is_trained,
            "is_training": self.is_training,
            "is_failed": self.is_failed,
            "is_multi_class": self.is_multi_class,
            "is_multi_label": self.is_multi_label,
            "has_encryption": self.has_encryption,
            "training_duration_hours": self.training_duration_hours,
            "labels_count": self.labels_count
        }


@dataclass
class ComprehendJob:
    """Job de análise Comprehend."""
    job_id: str
    job_name: str = ""
    job_type: str = "ENTITIES"
    job_status: str = "COMPLETED"
    submit_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data_config: Dict[str, Any] = field(default_factory=dict)
    output_data_config: Dict[str, Any] = field(default_factory=dict)
    language_code: str = "en"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.job_status == "COMPLETED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.job_status == "FAILED"

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.job_status == "IN_PROGRESS"

    @property
    def duration_minutes(self) -> float:
        """Duração do job em minutos."""
        if self.submit_time and self.end_time:
            return (self.end_time - self.submit_time).total_seconds() / 60
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_id": self.job_id,
            "job_name": self.job_name,
            "job_type": self.job_type,
            "job_status": self.job_status,
            "submit_time": self.submit_time.isoformat() if self.submit_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "language_code": self.language_code,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_in_progress": self.is_in_progress,
            "duration_minutes": self.duration_minutes
        }


class ComprehendService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Comprehend."""

    def __init__(self, client_factory):
        """Inicializa o serviço Comprehend."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._comprehend_client = None

    @property
    def comprehend_client(self):
        """Cliente Comprehend com lazy loading."""
        if self._comprehend_client is None:
            self._comprehend_client = self._client_factory.get_client('comprehend')
        return self._comprehend_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Comprehend."""
        try:
            self.comprehend_client.list_endpoints(MaxResults=1)
            return {
                "service": "comprehend",
                "status": "healthy",
                "message": "Comprehend service is accessible"
            }
        except Exception as e:
            return {
                "service": "comprehend",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_endpoints(self) -> List[ComprehendEndpoint]:
        """Lista endpoints de inferência."""
        endpoints = []
        try:
            paginator = self.comprehend_client.get_paginator('list_endpoints')
            for page in paginator.paginate():
                for ep in page.get('EndpointPropertiesList', []):
                    endpoints.append(ComprehendEndpoint(
                        endpoint_arn=ep.get('EndpointArn', ''),
                        endpoint_name=ep.get('EndpointArn', '').split('/')[-1],
                        status=ep.get('Status', 'IN_SERVICE'),
                        model_arn=ep.get('ModelArn'),
                        desired_model_arn=ep.get('DesiredModelArn'),
                        desired_inference_units=ep.get('DesiredInferenceUnits', 1),
                        current_inference_units=ep.get('CurrentInferenceUnits', 1),
                        creation_time=ep.get('CreationTime'),
                        last_modified_time=ep.get('LastModifiedTime'),
                        data_access_role_arn=ep.get('DataAccessRoleArn'),
                        desired_data_access_role_arn=ep.get('DesiredDataAccessRoleArn')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar endpoints: {e}")
        return endpoints

    def get_entity_recognizers(self) -> List[EntityRecognizer]:
        """Lista reconhecedores de entidades."""
        recognizers = []
        try:
            paginator = self.comprehend_client.get_paginator('list_entity_recognizers')
            for page in paginator.paginate():
                for rec in page.get('EntityRecognizerPropertiesList', []):
                    recognizers.append(EntityRecognizer(
                        entity_recognizer_arn=rec.get('EntityRecognizerArn', ''),
                        recognizer_name=rec.get('EntityRecognizerArn', '').split('/')[-1],
                        language_code=rec.get('LanguageCode', 'en'),
                        status=rec.get('Status', 'TRAINED'),
                        version_name=rec.get('VersionName'),
                        model_kms_key_id=rec.get('ModelKmsKeyId'),
                        creation_time=rec.get('SubmitTime'),
                        training_start_time=rec.get('TrainingStartTime'),
                        training_end_time=rec.get('TrainingEndTime'),
                        input_data_config=rec.get('InputDataConfig', {}),
                        recognizer_metadata=rec.get('RecognizerMetadata', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar entity recognizers: {e}")
        return recognizers

    def get_document_classifiers(self) -> List[DocumentClassifier]:
        """Lista classificadores de documentos."""
        classifiers = []
        try:
            paginator = self.comprehend_client.get_paginator('list_document_classifiers')
            for page in paginator.paginate():
                for clf in page.get('DocumentClassifierPropertiesList', []):
                    classifiers.append(DocumentClassifier(
                        document_classifier_arn=clf.get('DocumentClassifierArn', ''),
                        classifier_name=clf.get('DocumentClassifierArn', '').split('/')[-1],
                        language_code=clf.get('LanguageCode', 'en'),
                        status=clf.get('Status', 'TRAINED'),
                        version_name=clf.get('VersionName'),
                        model_kms_key_id=clf.get('ModelKmsKeyId'),
                        mode=clf.get('Mode', 'MULTI_CLASS'),
                        creation_time=clf.get('SubmitTime'),
                        training_start_time=clf.get('TrainingStartTime'),
                        training_end_time=clf.get('TrainingEndTime'),
                        input_data_config=clf.get('InputDataConfig', {}),
                        output_data_config=clf.get('OutputDataConfig', {}),
                        classifier_metadata=clf.get('ClassifierMetadata', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar document classifiers: {e}")
        return classifiers

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Comprehend."""
        endpoints = self.get_endpoints()
        entity_recognizers = self.get_entity_recognizers()
        document_classifiers = self.get_document_classifiers()

        return {
            "endpoints": [e.to_dict() for e in endpoints],
            "entity_recognizers": [r.to_dict() for r in entity_recognizers],
            "document_classifiers": [c.to_dict() for c in document_classifiers],
            "summary": {
                "total_endpoints": len(endpoints),
                "active_endpoints": len([e for e in endpoints if e.is_active]),
                "total_entity_recognizers": len(entity_recognizers),
                "trained_recognizers": len([r for r in entity_recognizers if r.is_trained]),
                "total_document_classifiers": len(document_classifiers),
                "trained_classifiers": len([c for c in document_classifiers if c.is_trained]),
                "total_inference_units": sum(e.current_inference_units for e in endpoints),
                "encrypted_models": len([r for r in entity_recognizers if r.has_encryption]) + 
                                   len([c for c in document_classifiers if c.has_encryption])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Comprehend."""
        endpoints = self.get_endpoints()
        entity_recognizers = self.get_entity_recognizers()
        document_classifiers = self.get_document_classifiers()

        total_inference_units = sum(e.current_inference_units for e in endpoints)
        estimated_monthly_cost = sum(e.estimated_monthly_cost for e in endpoints)

        return {
            "endpoints_count": len(endpoints),
            "active_endpoints": len([e for e in endpoints if e.is_active]),
            "total_inference_units": total_inference_units,
            "estimated_monthly_cost": estimated_monthly_cost,
            "entity_recognizers_count": len(entity_recognizers),
            "document_classifiers_count": len(document_classifiers),
            "training_in_progress": len([r for r in entity_recognizers if r.is_training]) + 
                                   len([c for c in document_classifiers if c.is_training]),
            "failed_models": len([r for r in entity_recognizers if r.is_failed]) + 
                            len([c for c in document_classifiers if c.is_failed]),
            "languages_used": list(set([r.language_code for r in entity_recognizers] + 
                                      [c.language_code for c in document_classifiers]))
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Comprehend."""
        recommendations = []
        endpoints = self.get_endpoints()
        entity_recognizers = self.get_entity_recognizers()
        document_classifiers = self.get_document_classifiers()

        # Verificar endpoints com muitas inference units
        for ep in endpoints:
            if ep.is_active and ep.current_inference_units > 5:
                recommendations.append({
                    "resource_type": "ComprehendEndpoint",
                    "resource_id": ep.endpoint_name,
                    "recommendation": "Avaliar necessidade de inference units",
                    "description": f"Endpoint '{ep.endpoint_name}' tem {ep.current_inference_units} inference units. "
                                   "Considerar reduzir se utilização for baixa.",
                    "estimated_savings": ep.estimated_monthly_cost * 0.3,
                    "priority": "high"
                })

        # Verificar endpoints antigos
        for ep in endpoints:
            if ep.is_active and ep.age_days > 180:
                recommendations.append({
                    "resource_type": "ComprehendEndpoint",
                    "resource_id": ep.endpoint_name,
                    "recommendation": "Revisar endpoint antigo",
                    "description": f"Endpoint '{ep.endpoint_name}' tem {ep.age_days} dias. "
                                   "Verificar se ainda está sendo utilizado.",
                    "priority": "medium"
                })

        # Verificar modelos sem criptografia
        for rec in entity_recognizers:
            if rec.is_trained and not rec.has_encryption:
                recommendations.append({
                    "resource_type": "EntityRecognizer",
                    "resource_id": rec.recognizer_name,
                    "recommendation": "Habilitar criptografia KMS",
                    "description": f"Entity recognizer '{rec.recognizer_name}' sem criptografia. "
                                   "Recomendado para segurança.",
                    "priority": "medium"
                })

        for clf in document_classifiers:
            if clf.is_trained and not clf.has_encryption:
                recommendations.append({
                    "resource_type": "DocumentClassifier",
                    "resource_id": clf.classifier_name,
                    "recommendation": "Habilitar criptografia KMS",
                    "description": f"Document classifier '{clf.classifier_name}' sem criptografia. "
                                   "Recomendado para segurança.",
                    "priority": "medium"
                })

        # Verificar modelos falhados
        failed_recognizers = [r for r in entity_recognizers if r.is_failed]
        failed_classifiers = [c for c in document_classifiers if c.is_failed]
        
        if failed_recognizers or failed_classifiers:
            recommendations.append({
                "resource_type": "ComprehendModel",
                "resource_id": "multiple",
                "recommendation": "Investigar modelos falhados",
                "description": f"{len(failed_recognizers)} entity recognizer(s) e "
                               f"{len(failed_classifiers)} classifier(s) falharam. "
                               "Verificar dados e configuração.",
                "priority": "high"
            })

        return recommendations
