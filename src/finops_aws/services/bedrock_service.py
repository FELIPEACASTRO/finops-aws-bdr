"""
AWS Bedrock Service para FinOps.

Análise de custos e otimização de modelos de fundação e inferência.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class FoundationModel:
    """Modelo de fundação AWS Bedrock."""
    model_id: str
    model_name: str
    provider_name: str
    input_modalities: List[str] = field(default_factory=list)
    output_modalities: List[str] = field(default_factory=list)
    customizations_supported: List[str] = field(default_factory=list)
    inference_types_supported: List[str] = field(default_factory=list)
    model_lifecycle_status: str = "ACTIVE"
    response_streaming_supported: bool = False

    @property
    def is_active(self) -> bool:
        """Verifica se modelo está ativo."""
        return self.model_lifecycle_status == "ACTIVE"

    @property
    def supports_fine_tuning(self) -> bool:
        """Verifica se suporta fine-tuning."""
        return "FINE_TUNING" in self.customizations_supported

    @property
    def supports_streaming(self) -> bool:
        """Verifica se suporta streaming."""
        return self.response_streaming_supported

    @property
    def is_multimodal(self) -> bool:
        """Verifica se é multimodal."""
        return len(self.input_modalities) > 1 or len(self.output_modalities) > 1

    @property
    def supports_on_demand(self) -> bool:
        """Verifica se suporta inferência on-demand."""
        return "ON_DEMAND" in self.inference_types_supported

    @property
    def supports_provisioned(self) -> bool:
        """Verifica se suporta provisioned throughput."""
        return "PROVISIONED" in self.inference_types_supported

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "input_modalities": self.input_modalities,
            "output_modalities": self.output_modalities,
            "customizations_supported": self.customizations_supported,
            "inference_types_supported": self.inference_types_supported,
            "model_lifecycle_status": self.model_lifecycle_status,
            "response_streaming_supported": self.response_streaming_supported,
            "is_active": self.is_active,
            "supports_fine_tuning": self.supports_fine_tuning,
            "supports_streaming": self.supports_streaming,
            "is_multimodal": self.is_multimodal,
            "supports_on_demand": self.supports_on_demand,
            "supports_provisioned": self.supports_provisioned
        }


@dataclass
class CustomModel:
    """Modelo customizado Bedrock."""
    model_arn: str
    model_name: str
    base_model_arn: str
    job_arn: str
    creation_time: Optional[datetime] = None
    model_kms_key_arn: Optional[str] = None
    customization_type: str = "FINE_TUNING"

    @property
    def is_fine_tuned(self) -> bool:
        """Verifica se é fine-tuned."""
        return self.customization_type == "FINE_TUNING"

    @property
    def is_continued_pretrained(self) -> bool:
        """Verifica se é continued pre-training."""
        return self.customization_type == "CONTINUED_PRE_TRAINING"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.model_kms_key_arn is not None

    @property
    def age_days(self) -> int:
        """Idade do modelo em dias."""
        if self.creation_time:
            return (datetime.now(self.creation_time.tzinfo) - self.creation_time).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "model_arn": self.model_arn,
            "model_name": self.model_name,
            "base_model_arn": self.base_model_arn,
            "job_arn": self.job_arn,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "model_kms_key_arn": self.model_kms_key_arn,
            "customization_type": self.customization_type,
            "is_fine_tuned": self.is_fine_tuned,
            "is_continued_pretrained": self.is_continued_pretrained,
            "has_encryption": self.has_encryption,
            "age_days": self.age_days
        }


@dataclass
class ProvisionedModelThroughput:
    """Provisioned throughput para modelo Bedrock."""
    provisioned_model_arn: str
    provisioned_model_name: str
    model_arn: str
    model_units: int
    desired_model_units: int
    status: str = "InService"
    commitment_duration: Optional[str] = None
    commitment_expiration_time: Optional[datetime] = None
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    foundation_model_arn: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "InService"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "Creating"

    @property
    def has_commitment(self) -> bool:
        """Verifica se tem commitment."""
        return self.commitment_duration is not None

    @property
    def is_scaling(self) -> bool:
        """Verifica se está escalando."""
        return self.model_units != self.desired_model_units

    @property
    def commitment_type(self) -> str:
        """Tipo de commitment."""
        if self.commitment_duration == "OneMonth":
            return "1 mês"
        elif self.commitment_duration == "SixMonths":
            return "6 meses"
        return "Sem commitment"

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado baseado em model units."""
        cost_per_unit = 50.0  # Estimativa base
        return self.model_units * cost_per_unit * 730  # horas/mês

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "provisioned_model_arn": self.provisioned_model_arn,
            "provisioned_model_name": self.provisioned_model_name,
            "model_arn": self.model_arn,
            "model_units": self.model_units,
            "desired_model_units": self.desired_model_units,
            "status": self.status,
            "commitment_duration": self.commitment_duration,
            "commitment_expiration_time": self.commitment_expiration_time.isoformat() if self.commitment_expiration_time else None,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "last_modified_time": self.last_modified_time.isoformat() if self.last_modified_time else None,
            "foundation_model_arn": self.foundation_model_arn,
            "is_active": self.is_active,
            "is_creating": self.is_creating,
            "has_commitment": self.has_commitment,
            "is_scaling": self.is_scaling,
            "commitment_type": self.commitment_type,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class ModelCustomizationJob:
    """Job de customização de modelo Bedrock."""
    job_arn: str
    job_name: str
    base_model_arn: str
    status: str = "InProgress"
    customization_type: str = "FINE_TUNING"
    creation_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    output_model_arn: Optional[str] = None
    output_model_name: Optional[str] = None
    role_arn: Optional[str] = None
    training_data_config: Dict[str, Any] = field(default_factory=dict)
    validation_data_config: Dict[str, Any] = field(default_factory=dict)
    hyper_parameters: Dict[str, str] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.status == "Completed"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "Failed"

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.status == "InProgress"

    @property
    def duration_hours(self) -> float:
        """Duração do job em horas."""
        if self.creation_time and self.end_time:
            return (self.end_time - self.creation_time).total_seconds() / 3600
        return 0.0

    @property
    def has_validation_data(self) -> bool:
        """Verifica se tem dados de validação."""
        return bool(self.validation_data_config)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "job_arn": self.job_arn,
            "job_name": self.job_name,
            "base_model_arn": self.base_model_arn,
            "status": self.status,
            "customization_type": self.customization_type,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "last_modified_time": self.last_modified_time.isoformat() if self.last_modified_time else None,
            "output_model_arn": self.output_model_arn,
            "output_model_name": self.output_model_name,
            "role_arn": self.role_arn,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_in_progress": self.is_in_progress,
            "duration_hours": self.duration_hours,
            "has_validation_data": self.has_validation_data
        }


class BedrockService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Bedrock."""

    def __init__(self, client_factory):
        """Inicializa o serviço Bedrock."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._bedrock_client = None
        self._bedrock_runtime_client = None

    @property
    def bedrock_client(self):
        """Cliente Bedrock com lazy loading."""
        if self._bedrock_client is None:
            self._bedrock_client = self._client_factory.get_client('bedrock')
        return self._bedrock_client

    @property
    def bedrock_runtime_client(self):
        """Cliente Bedrock Runtime com lazy loading."""
        if self._bedrock_runtime_client is None:
            self._bedrock_runtime_client = self._client_factory.get_client('bedrock-runtime')
        return self._bedrock_runtime_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Bedrock."""
        try:
            self.bedrock_client.list_foundation_models(maxResults=1)
            return {
                "service": "bedrock",
                "status": "healthy",
                "message": "Bedrock service is accessible"
            }
        except Exception as e:
            return {
                "service": "bedrock",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_foundation_models(self) -> List[FoundationModel]:
        """Lista modelos de fundação disponíveis."""
        models = []
        try:
            response = self.bedrock_client.list_foundation_models()
            for model in response.get('modelSummaries', []):
                models.append(FoundationModel(
                    model_id=model.get('modelId', ''),
                    model_name=model.get('modelName', ''),
                    provider_name=model.get('providerName', ''),
                    input_modalities=model.get('inputModalities', []),
                    output_modalities=model.get('outputModalities', []),
                    customizations_supported=model.get('customizationsSupported', []),
                    inference_types_supported=model.get('inferenceTypesSupported', []),
                    model_lifecycle_status=model.get('modelLifecycle', {}).get('status', 'ACTIVE'),
                    response_streaming_supported=model.get('responseStreamingSupported', False)
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar modelos de fundação: {e}")
        return models

    def get_custom_models(self) -> List[CustomModel]:
        """Lista modelos customizados."""
        models = []
        try:
            response = self.bedrock_client.list_custom_models()
            for model in response.get('modelSummaries', []):
                models.append(CustomModel(
                    model_arn=model.get('modelArn', ''),
                    model_name=model.get('modelName', ''),
                    base_model_arn=model.get('baseModelArn', ''),
                    job_arn=model.get('jobArn', ''),
                    creation_time=model.get('creationTime'),
                    model_kms_key_arn=model.get('modelKmsKeyArn'),
                    customization_type=model.get('customizationType', 'FINE_TUNING')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar modelos customizados: {e}")
        return models

    def get_provisioned_throughputs(self) -> List[ProvisionedModelThroughput]:
        """Lista provisioned throughputs."""
        throughputs = []
        try:
            response = self.bedrock_client.list_provisioned_model_throughputs()
            for pt in response.get('provisionedModelSummaries', []):
                throughputs.append(ProvisionedModelThroughput(
                    provisioned_model_arn=pt.get('provisionedModelArn', ''),
                    provisioned_model_name=pt.get('provisionedModelName', ''),
                    model_arn=pt.get('modelArn', ''),
                    model_units=pt.get('modelUnits', 0),
                    desired_model_units=pt.get('desiredModelUnits', 0),
                    status=pt.get('status', 'InService'),
                    commitment_duration=pt.get('commitmentDuration'),
                    commitment_expiration_time=pt.get('commitmentExpirationTime'),
                    creation_time=pt.get('creationTime'),
                    last_modified_time=pt.get('lastModifiedTime'),
                    foundation_model_arn=pt.get('foundationModelArn')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar provisioned throughputs: {e}")
        return throughputs

    def get_customization_jobs(self) -> List[ModelCustomizationJob]:
        """Lista jobs de customização."""
        jobs = []
        try:
            response = self.bedrock_client.list_model_customization_jobs()
            for job in response.get('modelCustomizationJobSummaries', []):
                jobs.append(ModelCustomizationJob(
                    job_arn=job.get('jobArn', ''),
                    job_name=job.get('jobName', ''),
                    base_model_arn=job.get('baseModelArn', ''),
                    status=job.get('status', 'InProgress'),
                    customization_type=job.get('customizationType', 'FINE_TUNING'),
                    creation_time=job.get('creationTime'),
                    end_time=job.get('endTime'),
                    last_modified_time=job.get('lastModifiedTime')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar jobs de customização: {e}")
        return jobs

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Bedrock."""
        foundation_models = self.get_foundation_models()
        custom_models = self.get_custom_models()
        provisioned_throughputs = self.get_provisioned_throughputs()
        customization_jobs = self.get_customization_jobs()

        return {
            "foundation_models": [m.to_dict() for m in foundation_models],
            "custom_models": [m.to_dict() for m in custom_models],
            "provisioned_throughputs": [pt.to_dict() for pt in provisioned_throughputs],
            "customization_jobs": [j.to_dict() for j in customization_jobs],
            "summary": {
                "total_foundation_models": len(foundation_models),
                "total_custom_models": len(custom_models),
                "total_provisioned_throughputs": len(provisioned_throughputs),
                "active_provisioned": len([pt for pt in provisioned_throughputs if pt.is_active]),
                "total_customization_jobs": len(customization_jobs),
                "completed_jobs": len([j for j in customization_jobs if j.is_completed]),
                "failed_jobs": len([j for j in customization_jobs if j.is_failed]),
                "multimodal_models": len([m for m in foundation_models if m.is_multimodal]),
                "fine_tunable_models": len([m for m in foundation_models if m.supports_fine_tuning])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Bedrock."""
        foundation_models = self.get_foundation_models()
        custom_models = self.get_custom_models()
        provisioned_throughputs = self.get_provisioned_throughputs()
        customization_jobs = self.get_customization_jobs()

        total_model_units = sum(pt.model_units for pt in provisioned_throughputs)
        estimated_monthly_cost = sum(pt.estimated_monthly_cost for pt in provisioned_throughputs)

        return {
            "foundation_models_available": len(foundation_models),
            "custom_models_count": len(custom_models),
            "provisioned_throughputs_count": len(provisioned_throughputs),
            "total_model_units": total_model_units,
            "estimated_monthly_provisioned_cost": estimated_monthly_cost,
            "active_customization_jobs": len([j for j in customization_jobs if j.is_in_progress]),
            "models_with_encryption": len([m for m in custom_models if m.has_encryption]),
            "providers": list(set(m.provider_name for m in foundation_models)),
            "streaming_capable_models": len([m for m in foundation_models if m.supports_streaming]),
            "on_demand_models": len([m for m in foundation_models if m.supports_on_demand])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Bedrock."""
        recommendations = []
        provisioned_throughputs = self.get_provisioned_throughputs()
        custom_models = self.get_custom_models()
        customization_jobs = self.get_customization_jobs()

        # Verificar provisioned throughputs sem commitment
        for pt in provisioned_throughputs:
            if pt.is_active and not pt.has_commitment:
                recommendations.append({
                    "resource_type": "ProvisionedThroughput",
                    "resource_id": pt.provisioned_model_name,
                    "recommendation": "Considerar commitment para reduzir custos",
                    "description": f"Provisioned throughput '{pt.provisioned_model_name}' sem commitment. "
                                   "Commitment de 1 ou 6 meses pode reduzir custos significativamente.",
                    "estimated_savings": pt.estimated_monthly_cost * 0.3,
                    "priority": "high"
                })

        # Verificar modelos customizados sem criptografia
        for model in custom_models:
            if not model.has_encryption:
                recommendations.append({
                    "resource_type": "CustomModel",
                    "resource_id": model.model_name,
                    "recommendation": "Habilitar criptografia KMS",
                    "description": f"Modelo customizado '{model.model_name}' sem criptografia KMS. "
                                   "Recomendado para segurança de dados.",
                    "priority": "medium"
                })

        # Verificar jobs de customização falhados
        failed_jobs = [j for j in customization_jobs if j.is_failed]
        if failed_jobs:
            recommendations.append({
                "resource_type": "CustomizationJob",
                "resource_id": "multiple",
                "recommendation": "Investigar jobs de customização falhados",
                "description": f"{len(failed_jobs)} job(s) de customização falharam. "
                               "Verificar logs e dados de treinamento.",
                "priority": "high"
            })

        # Verificar provisioned throughputs escalando
        scaling_pts = [pt for pt in provisioned_throughputs if pt.is_scaling]
        for pt in scaling_pts:
            recommendations.append({
                "resource_type": "ProvisionedThroughput",
                "resource_id": pt.provisioned_model_name,
                "recommendation": "Monitorar escalamento em progresso",
                "description": f"Provisioned throughput '{pt.provisioned_model_name}' está escalando "
                               f"de {pt.model_units} para {pt.desired_model_units} units.",
                "priority": "low"
            })

        return recommendations
