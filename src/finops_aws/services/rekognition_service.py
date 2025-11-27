"""
AWS Rekognition Service para FinOps.

Análise de custos e otimização de análise de imagem e vídeo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class RekognitionProject:
    """Projeto Rekognition Custom Labels."""
    project_arn: str
    project_name: str = ""
    status: str = "CREATED"
    creation_timestamp: Optional[datetime] = None
    auto_update: str = "DISABLED"
    feature: str = "CUSTOM_LABELS"

    @property
    def is_active(self) -> bool:
        """Verifica se projeto está ativo."""
        return self.status == "CREATED"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.status == "DELETING"

    @property
    def has_auto_update(self) -> bool:
        """Verifica se tem auto update."""
        return self.auto_update == "ENABLED"

    @property
    def is_custom_labels(self) -> bool:
        """Verifica se é Custom Labels."""
        return self.feature == "CUSTOM_LABELS"

    @property
    def age_days(self) -> int:
        """Idade do projeto em dias."""
        if self.creation_timestamp:
            return (datetime.now(self.creation_timestamp.tzinfo) - self.creation_timestamp).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "project_arn": self.project_arn,
            "project_name": self.project_name,
            "status": self.status,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None,
            "auto_update": self.auto_update,
            "feature": self.feature,
            "is_active": self.is_active,
            "is_deleting": self.is_deleting,
            "has_auto_update": self.has_auto_update,
            "is_custom_labels": self.is_custom_labels,
            "age_days": self.age_days
        }


@dataclass
class ProjectVersion:
    """Versão de projeto Rekognition."""
    project_version_arn: str
    version_name: str = ""
    status: str = "RUNNING"
    creation_timestamp: Optional[datetime] = None
    training_end_timestamp: Optional[datetime] = None
    billable_training_time_in_seconds: int = 0
    output_config: Dict[str, Any] = field(default_factory=dict)
    training_data_result: Dict[str, Any] = field(default_factory=dict)
    testing_data_result: Dict[str, Any] = field(default_factory=dict)
    evaluation_result: Dict[str, Any] = field(default_factory=dict)
    min_inference_units: int = 1
    max_inference_units: int = 1
    source_project_version_arn: Optional[str] = None
    kms_key_id: Optional[str] = None

    @property
    def is_running(self) -> bool:
        """Verifica se está em execução."""
        return self.status == "RUNNING"

    @property
    def is_training(self) -> bool:
        """Verifica se está treinando."""
        return self.status in ["TRAINING_IN_PROGRESS", "TRAINING"]

    @property
    def is_trained(self) -> bool:
        """Verifica se foi treinado."""
        return self.status == "TRAINING_COMPLETED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "TRAINING_FAILED"

    @property
    def is_stopped(self) -> bool:
        """Verifica se está parado."""
        return self.status == "STOPPED"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.kms_key_id is not None

    @property
    def training_hours(self) -> float:
        """Horas de treinamento."""
        return self.billable_training_time_in_seconds / 3600

    @property
    def estimated_training_cost(self) -> float:
        """Custo estimado de treinamento."""
        cost_per_hour = 1.00  # Estimativa base
        return self.training_hours * cost_per_hour

    @property
    def estimated_inference_cost_monthly(self) -> float:
        """Custo mensal estimado de inferência."""
        if self.is_running:
            cost_per_unit_hour = 4.00  # Estimativa base
            return self.min_inference_units * cost_per_unit_hour * 730
        return 0.0

    @property
    def f1_score(self) -> float:
        """F1 score do modelo."""
        return self.evaluation_result.get('F1Score', 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "project_version_arn": self.project_version_arn,
            "version_name": self.version_name,
            "status": self.status,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None,
            "training_end_timestamp": self.training_end_timestamp.isoformat() if self.training_end_timestamp else None,
            "billable_training_time_in_seconds": self.billable_training_time_in_seconds,
            "min_inference_units": self.min_inference_units,
            "max_inference_units": self.max_inference_units,
            "kms_key_id": self.kms_key_id,
            "is_running": self.is_running,
            "is_training": self.is_training,
            "is_trained": self.is_trained,
            "is_failed": self.is_failed,
            "is_stopped": self.is_stopped,
            "has_encryption": self.has_encryption,
            "training_hours": self.training_hours,
            "estimated_training_cost": self.estimated_training_cost,
            "estimated_inference_cost_monthly": self.estimated_inference_cost_monthly,
            "f1_score": self.f1_score
        }


@dataclass 
class StreamProcessor:
    """Stream processor Rekognition Video."""
    stream_processor_name: str
    status: str = "RUNNING"
    creation_timestamp: Optional[datetime] = None
    last_update_timestamp: Optional[datetime] = None
    stream_processor_arn: Optional[str] = None
    input_config: Dict[str, Any] = field(default_factory=dict)
    output_config: Dict[str, Any] = field(default_factory=dict)
    role_arn: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    notification_channel: Dict[str, Any] = field(default_factory=dict)
    kms_key_id: Optional[str] = None
    regions_of_interest: List[Dict[str, Any]] = field(default_factory=list)
    data_sharing_preference: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        """Verifica se está em execução."""
        return self.status == "RUNNING"

    @property
    def is_stopped(self) -> bool:
        """Verifica se está parado."""
        return self.status == "STOPPED"

    @property
    def is_starting(self) -> bool:
        """Verifica se está iniciando."""
        return self.status == "STARTING"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.kms_key_id is not None

    @property
    def has_notifications(self) -> bool:
        """Verifica se tem notificações configuradas."""
        return bool(self.notification_channel)

    @property
    def has_face_search(self) -> bool:
        """Verifica se tem face search."""
        return 'FaceSearch' in self.settings

    @property
    def has_connected_home(self) -> bool:
        """Verifica se tem Connected Home."""
        return 'ConnectedHome' in self.settings

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado."""
        if self.is_running:
            return 0.12 * 730 * 60  # $0.12 por minuto de vídeo processado
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "stream_processor_name": self.stream_processor_name,
            "status": self.status,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None,
            "last_update_timestamp": self.last_update_timestamp.isoformat() if self.last_update_timestamp else None,
            "stream_processor_arn": self.stream_processor_arn,
            "role_arn": self.role_arn,
            "kms_key_id": self.kms_key_id,
            "is_running": self.is_running,
            "is_stopped": self.is_stopped,
            "is_starting": self.is_starting,
            "has_encryption": self.has_encryption,
            "has_notifications": self.has_notifications,
            "has_face_search": self.has_face_search,
            "has_connected_home": self.has_connected_home,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class FaceCollection:
    """Coleção de faces Rekognition."""
    collection_id: str
    collection_arn: str = ""
    face_count: int = 0
    creation_timestamp: Optional[datetime] = None
    face_model_version: str = ""
    user_count: int = 0

    @property
    def is_empty(self) -> bool:
        """Verifica se está vazia."""
        return self.face_count == 0

    @property
    def has_users(self) -> bool:
        """Verifica se tem usuários associados."""
        return self.user_count > 0

    @property
    def age_days(self) -> int:
        """Idade da coleção em dias."""
        if self.creation_timestamp:
            return (datetime.now(self.creation_timestamp.tzinfo) - self.creation_timestamp).days
        return 0

    @property
    def estimated_storage_cost_monthly(self) -> float:
        """Custo mensal estimado de armazenamento."""
        cost_per_face = 0.00001  # $0.00001 por face/mês
        return self.face_count * cost_per_face

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "collection_id": self.collection_id,
            "collection_arn": self.collection_arn,
            "face_count": self.face_count,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None,
            "face_model_version": self.face_model_version,
            "user_count": self.user_count,
            "is_empty": self.is_empty,
            "has_users": self.has_users,
            "age_days": self.age_days,
            "estimated_storage_cost_monthly": self.estimated_storage_cost_monthly
        }


class RekognitionService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Rekognition."""

    def __init__(self, client_factory):
        """Inicializa o serviço Rekognition."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._rekognition_client = None

    @property
    def rekognition_client(self):
        """Cliente Rekognition com lazy loading."""
        if self._rekognition_client is None:
            self._rekognition_client = self._client_factory.get_client('rekognition')
        return self._rekognition_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Rekognition."""
        try:
            self.rekognition_client.list_collections(MaxResults=1)
            return {
                "service": "rekognition",
                "status": "healthy",
                "message": "Rekognition service is accessible"
            }
        except Exception as e:
            return {
                "service": "rekognition",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_projects(self) -> List[RekognitionProject]:
        """Lista projetos Custom Labels."""
        projects = []
        try:
            paginator = self.rekognition_client.get_paginator('describe_projects')
            for page in paginator.paginate():
                for proj in page.get('ProjectDescriptions', []):
                    projects.append(RekognitionProject(
                        project_arn=proj.get('ProjectArn', ''),
                        project_name=proj.get('ProjectArn', '').split('/')[-1],
                        status=proj.get('Status', 'CREATED'),
                        creation_timestamp=proj.get('CreationTimestamp'),
                        auto_update=proj.get('AutoUpdate', 'DISABLED'),
                        feature=proj.get('Feature', 'CUSTOM_LABELS')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar projetos: {e}")
        return projects

    def get_project_versions(self, project_arn: str) -> List[ProjectVersion]:
        """Lista versões de um projeto."""
        versions = []
        try:
            paginator = self.rekognition_client.get_paginator('describe_project_versions')
            for page in paginator.paginate(ProjectArn=project_arn):
                for ver in page.get('ProjectVersionDescriptions', []):
                    versions.append(ProjectVersion(
                        project_version_arn=ver.get('ProjectVersionArn', ''),
                        version_name=ver.get('ProjectVersionArn', '').split('/')[-1],
                        status=ver.get('Status', 'RUNNING'),
                        creation_timestamp=ver.get('CreationTimestamp'),
                        training_end_timestamp=ver.get('TrainingEndTimestamp'),
                        billable_training_time_in_seconds=ver.get('BillableTrainingTimeInSeconds', 0),
                        output_config=ver.get('OutputConfig', {}),
                        training_data_result=ver.get('TrainingDataResult', {}),
                        testing_data_result=ver.get('TestingDataResult', {}),
                        evaluation_result=ver.get('EvaluationResult', {}),
                        min_inference_units=ver.get('MinInferenceUnits', 1),
                        max_inference_units=ver.get('MaxInferenceUnits', 1),
                        source_project_version_arn=ver.get('SourceProjectVersionArn'),
                        kms_key_id=ver.get('KmsKeyId')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar versões do projeto: {e}")
        return versions

    def get_stream_processors(self) -> List[StreamProcessor]:
        """Lista stream processors."""
        processors = []
        try:
            paginator = self.rekognition_client.get_paginator('list_stream_processors')
            for page in paginator.paginate():
                for sp in page.get('StreamProcessors', []):
                    try:
                        details = self.rekognition_client.describe_stream_processor(
                            Name=sp.get('Name', '')
                        )
                        processors.append(StreamProcessor(
                            stream_processor_name=details.get('Name', ''),
                            status=details.get('Status', 'RUNNING'),
                            creation_timestamp=details.get('CreationTimestamp'),
                            last_update_timestamp=details.get('LastUpdateTimestamp'),
                            stream_processor_arn=details.get('StreamProcessorArn'),
                            input_config=details.get('Input', {}),
                            output_config=details.get('Output', {}),
                            role_arn=details.get('RoleArn'),
                            settings=details.get('Settings', {}),
                            notification_channel=details.get('NotificationChannel', {}),
                            kms_key_id=details.get('KmsKeyId'),
                            regions_of_interest=details.get('RegionsOfInterest', []),
                            data_sharing_preference=details.get('DataSharingPreference', {})
                        ))
                    except Exception:
                        continue
        except Exception as e:
            self.logger.error(f"Erro ao listar stream processors: {e}")
        return processors

    def get_face_collections(self) -> List[FaceCollection]:
        """Lista coleções de faces."""
        collections = []
        try:
            paginator = self.rekognition_client.get_paginator('list_collections')
            for page in paginator.paginate():
                for coll_id in page.get('CollectionIds', []):
                    try:
                        details = self.rekognition_client.describe_collection(
                            CollectionId=coll_id
                        )
                        collections.append(FaceCollection(
                            collection_id=coll_id,
                            collection_arn=details.get('CollectionARN', ''),
                            face_count=details.get('FaceCount', 0),
                            creation_timestamp=details.get('CreationTimestamp'),
                            face_model_version=details.get('FaceModelVersion', ''),
                            user_count=details.get('UserCount', 0)
                        ))
                    except Exception:
                        continue
        except Exception as e:
            self.logger.error(f"Erro ao listar coleções de faces: {e}")
        return collections

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Rekognition."""
        projects = self.get_projects()
        all_versions = []
        for proj in projects:
            versions = self.get_project_versions(proj.project_arn)
            all_versions.extend(versions)
        
        stream_processors = self.get_stream_processors()
        face_collections = self.get_face_collections()

        return {
            "projects": [p.to_dict() for p in projects],
            "project_versions": [v.to_dict() for v in all_versions],
            "stream_processors": [sp.to_dict() for sp in stream_processors],
            "face_collections": [fc.to_dict() for fc in face_collections],
            "summary": {
                "total_projects": len(projects),
                "total_versions": len(all_versions),
                "running_versions": len([v for v in all_versions if v.is_running]),
                "total_stream_processors": len(stream_processors),
                "running_processors": len([sp for sp in stream_processors if sp.is_running]),
                "total_face_collections": len(face_collections),
                "total_faces_stored": sum(fc.face_count for fc in face_collections),
                "empty_collections": len([fc for fc in face_collections if fc.is_empty])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Rekognition."""
        projects = self.get_projects()
        all_versions = []
        for proj in projects:
            versions = self.get_project_versions(proj.project_arn)
            all_versions.extend(versions)
        
        stream_processors = self.get_stream_processors()
        face_collections = self.get_face_collections()

        running_versions = [v for v in all_versions if v.is_running]
        running_processors = [sp for sp in stream_processors if sp.is_running]

        return {
            "projects_count": len(projects),
            "versions_count": len(all_versions),
            "running_versions": len(running_versions),
            "total_training_hours": sum(v.training_hours for v in all_versions),
            "estimated_training_cost": sum(v.estimated_training_cost for v in all_versions),
            "estimated_inference_cost_monthly": sum(v.estimated_inference_cost_monthly for v in running_versions),
            "stream_processors_count": len(stream_processors),
            "running_processors": len(running_processors),
            "estimated_streaming_cost_monthly": sum(sp.estimated_monthly_cost for sp in running_processors),
            "face_collections_count": len(face_collections),
            "total_faces": sum(fc.face_count for fc in face_collections),
            "estimated_storage_cost_monthly": sum(fc.estimated_storage_cost_monthly for fc in face_collections)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Rekognition."""
        recommendations = []
        projects = self.get_projects()
        all_versions = []
        for proj in projects:
            versions = self.get_project_versions(proj.project_arn)
            all_versions.extend(versions)
        
        stream_processors = self.get_stream_processors()
        face_collections = self.get_face_collections()

        # Verificar versões em execução com baixo F1
        for ver in all_versions:
            if ver.is_running and ver.f1_score < 0.7:
                recommendations.append({
                    "resource_type": "ProjectVersion",
                    "resource_id": ver.version_name,
                    "recommendation": "Retreinar modelo com baixo F1 score",
                    "description": f"Versão '{ver.version_name}' tem F1 score de {ver.f1_score:.2f}. "
                                   "Considerar retreinar com mais dados.",
                    "priority": "high"
                })

        # Verificar versões em execução sem criptografia
        for ver in all_versions:
            if ver.is_running and not ver.has_encryption:
                recommendations.append({
                    "resource_type": "ProjectVersion",
                    "resource_id": ver.version_name,
                    "recommendation": "Habilitar criptografia KMS",
                    "description": f"Versão '{ver.version_name}' sem criptografia. "
                                   "Recomendado para segurança de dados.",
                    "priority": "medium"
                })

        # Verificar stream processors parados
        stopped_processors = [sp for sp in stream_processors if sp.is_stopped]
        for sp in stopped_processors:
            recommendations.append({
                "resource_type": "StreamProcessor",
                "resource_id": sp.stream_processor_name,
                "recommendation": "Avaliar exclusão de stream processor parado",
                "description": f"Stream processor '{sp.stream_processor_name}' está parado. "
                               "Considerar excluir se não for mais necessário.",
                "priority": "low"
            })

        # Verificar coleções de faces vazias
        empty_collections = [fc for fc in face_collections if fc.is_empty]
        for fc in empty_collections:
            recommendations.append({
                "resource_type": "FaceCollection",
                "resource_id": fc.collection_id,
                "recommendation": "Excluir coleção de faces vazia",
                "description": f"Coleção '{fc.collection_id}' não contém faces. "
                               "Considerar excluir para manter ambiente organizado.",
                "priority": "low"
            })

        # Verificar coleções antigas
        old_collections = [fc for fc in face_collections if fc.age_days > 365]
        for fc in old_collections:
            recommendations.append({
                "resource_type": "FaceCollection",
                "resource_id": fc.collection_id,
                "recommendation": "Revisar coleção antiga",
                "description": f"Coleção '{fc.collection_id}' tem {fc.age_days} dias. "
                               "Verificar se ainda está sendo utilizada.",
                "priority": "medium"
            })

        return recommendations
