"""
Testes Unitários - FASE 3.0: AI/ML Services

Cobertura de testes para:
- BedrockService: Modelos de fundação, modelos customizados, provisioned throughput
- ComprehendService: Endpoints, entity recognizers, document classifiers
- RekognitionService: Projetos, versões, stream processors, face collections
- TextractService: Adapters, versões, jobs
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.finops_aws.services.bedrock_service import (
    BedrockService,
    FoundationModel,
    CustomModel,
    ProvisionedModelThroughput,
    ModelCustomizationJob
)
from src.finops_aws.services.comprehend_service import (
    ComprehendService,
    ComprehendEndpoint,
    EntityRecognizer,
    DocumentClassifier,
    ComprehendJob
)
from src.finops_aws.services.rekognition_service import (
    RekognitionService,
    RekognitionProject,
    ProjectVersion,
    StreamProcessor,
    FaceCollection
)
from src.finops_aws.services.textract_service import (
    TextractService,
    TextractAdapter,
    AdapterVersion,
    TextractJob,
    LendingAnalysisJob
)
from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory


class TestFoundationModelDataclass:
    """Testes para dataclass FoundationModel."""
    
    def test_foundation_model_basic(self):
        """Testa criação básica de FoundationModel."""
        model = FoundationModel(
            model_id="anthropic.claude-v2",
            model_name="Claude v2",
            provider_name="Anthropic"
        )
        assert model.model_id == "anthropic.claude-v2"
        assert model.model_name == "Claude v2"
        assert model.provider_name == "Anthropic"
    
    def test_foundation_model_is_active(self):
        """Testa propriedade is_active."""
        model_active = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            model_lifecycle_status="ACTIVE"
        )
        model_legacy = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            model_lifecycle_status="LEGACY"
        )
        assert model_active.is_active is True
        assert model_legacy.is_active is False
    
    def test_foundation_model_supports_fine_tuning(self):
        """Testa propriedade supports_fine_tuning."""
        model_ft = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            customizations_supported=["FINE_TUNING"]
        )
        model_no_ft = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            customizations_supported=[]
        )
        assert model_ft.supports_fine_tuning is True
        assert model_no_ft.supports_fine_tuning is False
    
    def test_foundation_model_is_multimodal(self):
        """Testa propriedade is_multimodal."""
        model_mm = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            input_modalities=["TEXT", "IMAGE"],
            output_modalities=["TEXT"]
        )
        model_text = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            input_modalities=["TEXT"],
            output_modalities=["TEXT"]
        )
        assert model_mm.is_multimodal is True
        assert model_text.is_multimodal is False
    
    def test_foundation_model_supports_streaming(self):
        """Testa propriedade supports_streaming."""
        model_stream = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            response_streaming_supported=True
        )
        assert model_stream.supports_streaming is True
    
    def test_foundation_model_inference_types(self):
        """Testa propriedades de inference types."""
        model = FoundationModel(
            model_id="test", model_name="Test", provider_name="Test",
            inference_types_supported=["ON_DEMAND", "PROVISIONED"]
        )
        assert model.supports_on_demand is True
        assert model.supports_provisioned is True
    
    def test_foundation_model_to_dict(self):
        """Testa conversão para dicionário."""
        model = FoundationModel(
            model_id="anthropic.claude-v2",
            model_name="Claude v2",
            provider_name="Anthropic",
            input_modalities=["TEXT"],
            output_modalities=["TEXT"],
            customizations_supported=["FINE_TUNING"],
            inference_types_supported=["ON_DEMAND"],
            response_streaming_supported=True
        )
        data = model.to_dict()
        assert data["model_id"] == "anthropic.claude-v2"
        assert data["is_active"] is True
        assert data["supports_fine_tuning"] is True
        assert data["supports_streaming"] is True


class TestCustomModelDataclass:
    """Testes para dataclass CustomModel."""
    
    def test_custom_model_basic(self):
        """Testa criação básica de CustomModel."""
        model = CustomModel(
            model_arn="arn:aws:bedrock:us-east-1:123456789012:custom-model/my-model",
            model_name="my-model",
            base_model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2",
            job_arn="arn:aws:bedrock:us-east-1:123456789012:model-customization-job/123"
        )
        assert model.model_name == "my-model"
        assert model.is_fine_tuned is True
    
    def test_custom_model_continued_pretrained(self):
        """Testa modelo com continued pre-training."""
        model = CustomModel(
            model_arn="arn", model_name="test", base_model_arn="arn", job_arn="arn",
            customization_type="CONTINUED_PRE_TRAINING"
        )
        assert model.is_continued_pretrained is True
        assert model.is_fine_tuned is False
    
    def test_custom_model_has_encryption(self):
        """Testa propriedade has_encryption."""
        model_encrypted = CustomModel(
            model_arn="arn", model_name="test", base_model_arn="arn", job_arn="arn",
            model_kms_key_arn="arn:aws:kms:us-east-1:123456789012:key/123"
        )
        model_no_encryption = CustomModel(
            model_arn="arn", model_name="test", base_model_arn="arn", job_arn="arn"
        )
        assert model_encrypted.has_encryption is True
        assert model_no_encryption.has_encryption is False
    
    def test_custom_model_to_dict(self):
        """Testa conversão para dicionário."""
        model = CustomModel(
            model_arn="arn", model_name="test", base_model_arn="arn", job_arn="arn"
        )
        data = model.to_dict()
        assert "model_name" in data
        assert "is_fine_tuned" in data
        assert "has_encryption" in data


class TestProvisionedModelThroughputDataclass:
    """Testes para dataclass ProvisionedModelThroughput."""
    
    def test_provisioned_throughput_basic(self):
        """Testa criação básica de ProvisionedModelThroughput."""
        pt = ProvisionedModelThroughput(
            provisioned_model_arn="arn:aws:bedrock:us-east-1:123456789012:provisioned-model/test",
            provisioned_model_name="test-pt",
            model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2",
            model_units=5,
            desired_model_units=5
        )
        assert pt.provisioned_model_name == "test-pt"
        assert pt.model_units == 5
    
    def test_provisioned_throughput_is_active(self):
        """Testa propriedade is_active."""
        pt_active = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=1, desired_model_units=1,
            status="InService"
        )
        pt_creating = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=1, desired_model_units=1,
            status="Creating"
        )
        assert pt_active.is_active is True
        assert pt_creating.is_active is False
        assert pt_creating.is_creating is True
    
    def test_provisioned_throughput_is_scaling(self):
        """Testa propriedade is_scaling."""
        pt_scaling = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=5, desired_model_units=10
        )
        pt_stable = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=5, desired_model_units=5
        )
        assert pt_scaling.is_scaling is True
        assert pt_stable.is_scaling is False
    
    def test_provisioned_throughput_commitment(self):
        """Testa propriedades de commitment."""
        pt_committed = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=1, desired_model_units=1,
            commitment_duration="SixMonths"
        )
        pt_no_commit = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=1, desired_model_units=1
        )
        assert pt_committed.has_commitment is True
        assert pt_committed.commitment_type == "6 meses"
        assert pt_no_commit.has_commitment is False
        assert pt_no_commit.commitment_type == "Sem commitment"
    
    def test_provisioned_throughput_estimated_cost(self):
        """Testa custo estimado."""
        pt = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=2, desired_model_units=2
        )
        assert pt.estimated_monthly_cost > 0
    
    def test_provisioned_throughput_to_dict(self):
        """Testa conversão para dicionário."""
        pt = ProvisionedModelThroughput(
            provisioned_model_arn="arn", provisioned_model_name="test",
            model_arn="arn", model_units=1, desired_model_units=1
        )
        data = pt.to_dict()
        assert "is_active" in data
        assert "has_commitment" in data
        assert "estimated_monthly_cost" in data


class TestModelCustomizationJobDataclass:
    """Testes para dataclass ModelCustomizationJob."""
    
    def test_customization_job_basic(self):
        """Testa criação básica de ModelCustomizationJob."""
        job = ModelCustomizationJob(
            job_arn="arn:aws:bedrock:us-east-1:123456789012:model-customization-job/123",
            job_name="my-job",
            base_model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2"
        )
        assert job.job_name == "my-job"
        assert job.is_in_progress is True
    
    def test_customization_job_status(self):
        """Testa propriedades de status."""
        job_completed = ModelCustomizationJob(
            job_arn="arn", job_name="test", base_model_arn="arn",
            status="Completed"
        )
        job_failed = ModelCustomizationJob(
            job_arn="arn", job_name="test", base_model_arn="arn",
            status="Failed"
        )
        assert job_completed.is_completed is True
        assert job_failed.is_failed is True
    
    def test_customization_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = ModelCustomizationJob(
            job_arn="arn", job_name="test", base_model_arn="arn"
        )
        data = job.to_dict()
        assert "is_completed" in data
        assert "is_failed" in data


class TestBedrockService:
    """Testes para BedrockService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        bedrock_client = Mock()
        factory.get_client.return_value = bedrock_client
        return factory
    
    def test_bedrock_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = BedrockService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_bedrock_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_foundation_models.return_value = {
            'modelSummaries': []
        }
        service = BedrockService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_bedrock_service_health_check_unhealthy(self, mock_client_factory):
        """Testa health check não saudável."""
        mock_client_factory.get_client.return_value.list_foundation_models.side_effect = Exception("Error")
        service = BedrockService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "unhealthy"
    
    def test_bedrock_service_get_foundation_models(self, mock_client_factory):
        """Testa listagem de modelos de fundação."""
        mock_client_factory.get_client.return_value.list_foundation_models.return_value = {
            'modelSummaries': [
                {
                    'modelId': 'anthropic.claude-v2',
                    'modelName': 'Claude v2',
                    'providerName': 'Anthropic',
                    'inputModalities': ['TEXT'],
                    'outputModalities': ['TEXT'],
                    'responseStreamingSupported': True
                }
            ]
        }
        service = BedrockService(mock_client_factory)
        models = service.get_foundation_models()
        assert len(models) == 1
        assert models[0].model_id == 'anthropic.claude-v2'
    
    def test_bedrock_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        client.list_foundation_models.return_value = {'modelSummaries': []}
        client.list_custom_models.return_value = {'modelSummaries': []}
        client.list_provisioned_model_throughputs.return_value = {'provisionedModelSummaries': []}
        client.list_model_customization_jobs.return_value = {'modelCustomizationJobSummaries': []}
        
        service = BedrockService(mock_client_factory)
        resources = service.get_resources()
        assert "foundation_models" in resources
        assert "custom_models" in resources
        assert "provisioned_throughputs" in resources
        assert "summary" in resources
    
    def test_bedrock_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        client.list_foundation_models.return_value = {'modelSummaries': []}
        client.list_custom_models.return_value = {'modelSummaries': []}
        client.list_provisioned_model_throughputs.return_value = {'provisionedModelSummaries': []}
        client.list_model_customization_jobs.return_value = {'modelCustomizationJobSummaries': []}
        
        service = BedrockService(mock_client_factory)
        metrics = service.get_metrics()
        assert "foundation_models_available" in metrics
        assert "estimated_monthly_provisioned_cost" in metrics
    
    def test_bedrock_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        client.list_foundation_models.return_value = {'modelSummaries': []}
        client.list_custom_models.return_value = {'modelSummaries': []}
        client.list_provisioned_model_throughputs.return_value = {
            'provisionedModelSummaries': [
                {
                    'provisionedModelArn': 'arn',
                    'provisionedModelName': 'test',
                    'modelArn': 'arn',
                    'modelUnits': 5,
                    'desiredModelUnits': 5,
                    'status': 'InService'
                }
            ]
        }
        client.list_model_customization_jobs.return_value = {'modelCustomizationJobSummaries': []}
        
        service = BedrockService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestComprehendEndpointDataclass:
    """Testes para dataclass ComprehendEndpoint."""
    
    def test_comprehend_endpoint_basic(self):
        """Testa criação básica de ComprehendEndpoint."""
        endpoint = ComprehendEndpoint(
            endpoint_arn="arn:aws:comprehend:us-east-1:123456789012:document-classifier-endpoint/test",
            endpoint_name="test-endpoint"
        )
        assert endpoint.endpoint_name == "test-endpoint"
        assert endpoint.is_active is True
    
    def test_comprehend_endpoint_status(self):
        """Testa propriedades de status."""
        ep_creating = ComprehendEndpoint(
            endpoint_arn="arn", endpoint_name="test", status="CREATING"
        )
        ep_updating = ComprehendEndpoint(
            endpoint_arn="arn", endpoint_name="test", status="UPDATING"
        )
        assert ep_creating.is_creating is True
        assert ep_updating.is_updating is True
    
    def test_comprehend_endpoint_scaling(self):
        """Testa propriedade is_scaling."""
        ep_scaling = ComprehendEndpoint(
            endpoint_arn="arn", endpoint_name="test",
            current_inference_units=2, desired_inference_units=5
        )
        assert ep_scaling.is_scaling is True
    
    def test_comprehend_endpoint_cost(self):
        """Testa custo estimado."""
        endpoint = ComprehendEndpoint(
            endpoint_arn="arn", endpoint_name="test",
            current_inference_units=2
        )
        assert endpoint.estimated_monthly_cost > 0
    
    def test_comprehend_endpoint_to_dict(self):
        """Testa conversão para dicionário."""
        endpoint = ComprehendEndpoint(endpoint_arn="arn", endpoint_name="test")
        data = endpoint.to_dict()
        assert "is_active" in data
        assert "estimated_monthly_cost" in data


class TestEntityRecognizerDataclass:
    """Testes para dataclass EntityRecognizer."""
    
    def test_entity_recognizer_basic(self):
        """Testa criação básica de EntityRecognizer."""
        recognizer = EntityRecognizer(
            entity_recognizer_arn="arn:aws:comprehend:us-east-1:123456789012:entity-recognizer/test",
            recognizer_name="test-recognizer"
        )
        assert recognizer.recognizer_name == "test-recognizer"
        assert recognizer.is_trained is True
    
    def test_entity_recognizer_status(self):
        """Testa propriedades de status."""
        rec_training = EntityRecognizer(
            entity_recognizer_arn="arn", recognizer_name="test", status="TRAINING"
        )
        rec_failed = EntityRecognizer(
            entity_recognizer_arn="arn", recognizer_name="test", status="IN_ERROR"
        )
        assert rec_training.is_training is True
        assert rec_failed.is_failed is True
    
    def test_entity_recognizer_encryption(self):
        """Testa propriedade has_encryption."""
        rec_encrypted = EntityRecognizer(
            entity_recognizer_arn="arn", recognizer_name="test",
            model_kms_key_id="key-123"
        )
        assert rec_encrypted.has_encryption is True
    
    def test_entity_recognizer_to_dict(self):
        """Testa conversão para dicionário."""
        recognizer = EntityRecognizer(entity_recognizer_arn="arn", recognizer_name="test")
        data = recognizer.to_dict()
        assert "is_trained" in data
        assert "has_encryption" in data


class TestDocumentClassifierDataclass:
    """Testes para dataclass DocumentClassifier."""
    
    def test_document_classifier_basic(self):
        """Testa criação básica de DocumentClassifier."""
        classifier = DocumentClassifier(
            document_classifier_arn="arn:aws:comprehend:us-east-1:123456789012:document-classifier/test",
            classifier_name="test-classifier"
        )
        assert classifier.classifier_name == "test-classifier"
        assert classifier.is_multi_class is True
    
    def test_document_classifier_mode(self):
        """Testa propriedades de modo."""
        clf_multi_label = DocumentClassifier(
            document_classifier_arn="arn", classifier_name="test",
            mode="MULTI_LABEL"
        )
        assert clf_multi_label.is_multi_label is True
        assert clf_multi_label.is_multi_class is False
    
    def test_document_classifier_to_dict(self):
        """Testa conversão para dicionário."""
        classifier = DocumentClassifier(document_classifier_arn="arn", classifier_name="test")
        data = classifier.to_dict()
        assert "is_trained" in data
        assert "is_multi_class" in data


class TestComprehendService:
    """Testes para ComprehendService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        comprehend_client = Mock()
        factory.get_client.return_value = comprehend_client
        return factory
    
    def test_comprehend_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = ComprehendService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_comprehend_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_endpoints.return_value = {
            'EndpointPropertiesList': []
        }
        service = ComprehendService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_comprehend_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'EndpointPropertiesList': []}]
        client.get_paginator.return_value = paginator
        
        service = ComprehendService(mock_client_factory)
        resources = service.get_resources()
        assert "endpoints" in resources
        assert "entity_recognizers" in resources
        assert "document_classifiers" in resources
        assert "summary" in resources
    
    def test_comprehend_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'EndpointPropertiesList': []}]
        client.get_paginator.return_value = paginator
        
        service = ComprehendService(mock_client_factory)
        metrics = service.get_metrics()
        assert "endpoints_count" in metrics
        assert "estimated_monthly_cost" in metrics
    
    def test_comprehend_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'EndpointPropertiesList': []}]
        client.get_paginator.return_value = paginator
        
        service = ComprehendService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestRekognitionProjectDataclass:
    """Testes para dataclass RekognitionProject."""
    
    def test_rekognition_project_basic(self):
        """Testa criação básica de RekognitionProject."""
        project = RekognitionProject(
            project_arn="arn:aws:rekognition:us-east-1:123456789012:project/test/123",
            project_name="test-project"
        )
        assert project.project_name == "test-project"
        assert project.is_active is True
    
    def test_rekognition_project_status(self):
        """Testa propriedades de status."""
        proj_deleting = RekognitionProject(
            project_arn="arn", project_name="test", status="DELETING"
        )
        assert proj_deleting.is_deleting is True
    
    def test_rekognition_project_features(self):
        """Testa propriedades de features."""
        project = RekognitionProject(
            project_arn="arn", project_name="test",
            auto_update="ENABLED", feature="CUSTOM_LABELS"
        )
        assert project.has_auto_update is True
        assert project.is_custom_labels is True
    
    def test_rekognition_project_to_dict(self):
        """Testa conversão para dicionário."""
        project = RekognitionProject(project_arn="arn", project_name="test")
        data = project.to_dict()
        assert "is_active" in data
        assert "has_auto_update" in data


class TestProjectVersionDataclass:
    """Testes para dataclass ProjectVersion."""
    
    def test_project_version_basic(self):
        """Testa criação básica de ProjectVersion."""
        version = ProjectVersion(
            project_version_arn="arn:aws:rekognition:us-east-1:123456789012:project/test/version/1",
            version_name="v1"
        )
        assert version.version_name == "v1"
        assert version.is_running is True
    
    def test_project_version_status(self):
        """Testa propriedades de status."""
        ver_training = ProjectVersion(
            project_version_arn="arn", version_name="v1", status="TRAINING_IN_PROGRESS"
        )
        ver_stopped = ProjectVersion(
            project_version_arn="arn", version_name="v1", status="STOPPED"
        )
        assert ver_training.is_training is True
        assert ver_stopped.is_stopped is True
    
    def test_project_version_costs(self):
        """Testa custos estimados."""
        version = ProjectVersion(
            project_version_arn="arn", version_name="v1",
            billable_training_time_in_seconds=3600,
            min_inference_units=2
        )
        assert version.training_hours == 1.0
        assert version.estimated_training_cost > 0
        assert version.estimated_inference_cost_monthly > 0
    
    def test_project_version_to_dict(self):
        """Testa conversão para dicionário."""
        version = ProjectVersion(project_version_arn="arn", version_name="v1")
        data = version.to_dict()
        assert "is_running" in data
        assert "estimated_training_cost" in data


class TestStreamProcessorDataclass:
    """Testes para dataclass StreamProcessor."""
    
    def test_stream_processor_basic(self):
        """Testa criação básica de StreamProcessor."""
        processor = StreamProcessor(
            stream_processor_name="test-processor"
        )
        assert processor.stream_processor_name == "test-processor"
        assert processor.is_running is True
    
    def test_stream_processor_status(self):
        """Testa propriedades de status."""
        sp_stopped = StreamProcessor(
            stream_processor_name="test", status="STOPPED"
        )
        sp_starting = StreamProcessor(
            stream_processor_name="test", status="STARTING"
        )
        assert sp_stopped.is_stopped is True
        assert sp_starting.is_starting is True
    
    def test_stream_processor_features(self):
        """Testa propriedades de features."""
        processor = StreamProcessor(
            stream_processor_name="test",
            notification_channel={"SNSTopicArn": "arn"},
            settings={"FaceSearch": {"CollectionId": "test"}}
        )
        assert processor.has_notifications is True
        assert processor.has_face_search is True
    
    def test_stream_processor_to_dict(self):
        """Testa conversão para dicionário."""
        processor = StreamProcessor(stream_processor_name="test")
        data = processor.to_dict()
        assert "is_running" in data
        assert "estimated_monthly_cost" in data


class TestFaceCollectionDataclass:
    """Testes para dataclass FaceCollection."""
    
    def test_face_collection_basic(self):
        """Testa criação básica de FaceCollection."""
        collection = FaceCollection(
            collection_id="test-collection",
            collection_arn="arn:aws:rekognition:us-east-1:123456789012:collection/test"
        )
        assert collection.collection_id == "test-collection"
        assert collection.is_empty is True
    
    def test_face_collection_with_faces(self):
        """Testa coleção com faces."""
        collection = FaceCollection(
            collection_id="test", collection_arn="arn",
            face_count=100, user_count=10
        )
        assert collection.is_empty is False
        assert collection.has_users is True
        assert collection.estimated_storage_cost_monthly > 0
    
    def test_face_collection_to_dict(self):
        """Testa conversão para dicionário."""
        collection = FaceCollection(collection_id="test", collection_arn="arn")
        data = collection.to_dict()
        assert "is_empty" in data
        assert "estimated_storage_cost_monthly" in data


class TestRekognitionService:
    """Testes para RekognitionService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        rekognition_client = Mock()
        factory.get_client.return_value = rekognition_client
        return factory
    
    def test_rekognition_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = RekognitionService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_rekognition_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_collections.return_value = {
            'CollectionIds': []
        }
        service = RekognitionService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_rekognition_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'ProjectDescriptions': []}]
        client.get_paginator.return_value = paginator
        
        service = RekognitionService(mock_client_factory)
        resources = service.get_resources()
        assert "projects" in resources
        assert "stream_processors" in resources
        assert "face_collections" in resources
        assert "summary" in resources
    
    def test_rekognition_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'ProjectDescriptions': []}]
        client.get_paginator.return_value = paginator
        
        service = RekognitionService(mock_client_factory)
        metrics = service.get_metrics()
        assert "projects_count" in metrics
        assert "total_faces" in metrics
    
    def test_rekognition_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'ProjectDescriptions': []}]
        client.get_paginator.return_value = paginator
        
        service = RekognitionService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestTextractAdapterDataclass:
    """Testes para dataclass TextractAdapter."""
    
    def test_textract_adapter_basic(self):
        """Testa criação básica de TextractAdapter."""
        adapter = TextractAdapter(
            adapter_id="test-adapter-id",
            adapter_name="test-adapter"
        )
        assert adapter.adapter_name == "test-adapter"
        assert adapter.is_active is True
    
    def test_textract_adapter_features(self):
        """Testa propriedades de features."""
        adapter = TextractAdapter(
            adapter_id="test", adapter_name="test",
            feature_types=["QUERIES", "TABLES", "FORMS"],
            auto_update="ENABLED"
        )
        assert adapter.supports_queries is True
        assert adapter.supports_tables is True
        assert adapter.supports_forms is True
        assert adapter.has_auto_update is True
    
    def test_textract_adapter_to_dict(self):
        """Testa conversão para dicionário."""
        adapter = TextractAdapter(adapter_id="test", adapter_name="test")
        data = adapter.to_dict()
        assert "is_active" in data
        assert "supports_queries" in data


class TestAdapterVersionDataclass:
    """Testes para dataclass AdapterVersion."""
    
    def test_adapter_version_basic(self):
        """Testa criação básica de AdapterVersion."""
        version = AdapterVersion(
            adapter_id="test-adapter",
            adapter_version="1"
        )
        assert version.adapter_version == "1"
        assert version.is_active is True
    
    def test_adapter_version_status(self):
        """Testa propriedades de status."""
        ver_training = AdapterVersion(
            adapter_id="test", adapter_version="1", status="TRAINING"
        )
        ver_failed = AdapterVersion(
            adapter_id="test", adapter_version="1", status="FAILED"
        )
        assert ver_training.is_training is True
        assert ver_failed.is_failed is True
    
    def test_adapter_version_encryption(self):
        """Testa propriedade has_encryption."""
        ver_encrypted = AdapterVersion(
            adapter_id="test", adapter_version="1",
            kms_key_id="key-123"
        )
        assert ver_encrypted.has_encryption is True
    
    def test_adapter_version_f1_score(self):
        """Testa cálculo de F1 score."""
        version = AdapterVersion(
            adapter_id="test", adapter_version="1",
            evaluation_metrics=[{"F1Score": 0.9}, {"F1Score": 0.8}]
        )
        assert abs(version.average_f1_score - 0.85) < 0.001
    
    def test_adapter_version_to_dict(self):
        """Testa conversão para dicionário."""
        version = AdapterVersion(adapter_id="test", adapter_version="1")
        data = version.to_dict()
        assert "is_active" in data
        assert "average_f1_score" in data


class TestTextractJobDataclass:
    """Testes para dataclass TextractJob."""
    
    def test_textract_job_basic(self):
        """Testa criação básica de TextractJob."""
        job = TextractJob(job_id="test-job-id")
        assert job.job_id == "test-job-id"
        assert job.is_succeeded is True
    
    def test_textract_job_status(self):
        """Testa propriedades de status."""
        job_failed = TextractJob(job_id="test", job_status="FAILED")
        job_in_progress = TextractJob(job_id="test", job_status="IN_PROGRESS")
        assert job_failed.is_failed is True
        assert job_in_progress.is_in_progress is True
    
    def test_textract_job_api_types(self):
        """Testa propriedades de tipo de API."""
        job_detect = TextractJob(job_id="test", api_type="DetectDocumentText")
        job_analyze = TextractJob(job_id="test", api_type="AnalyzeDocument")
        job_expense = TextractJob(job_id="test", api_type="AnalyzeExpense")
        assert job_detect.is_document_detection is True
        assert job_analyze.is_document_analysis is True
        assert job_expense.is_expense_analysis is True
    
    def test_textract_job_cost(self):
        """Testa custo estimado."""
        job = TextractJob(job_id="test", pages_processed=100)
        assert job.estimated_cost > 0
    
    def test_textract_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = TextractJob(job_id="test")
        data = job.to_dict()
        assert "is_succeeded" in data
        assert "estimated_cost" in data


class TestLendingAnalysisJobDataclass:
    """Testes para dataclass LendingAnalysisJob."""
    
    def test_lending_job_basic(self):
        """Testa criação básica de LendingAnalysisJob."""
        job = LendingAnalysisJob(job_id="test-lending-job")
        assert job.job_id == "test-lending-job"
        assert job.is_succeeded is True
    
    def test_lending_job_cost(self):
        """Testa custo estimado."""
        job = LendingAnalysisJob(
            job_id="test",
            document_metadata={"Pages": 10}
        )
        assert job.pages_count == 10
        assert abs(job.estimated_cost - 0.7) < 0.001  # 10 * 0.07
    
    def test_lending_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = LendingAnalysisJob(job_id="test")
        data = job.to_dict()
        assert "is_succeeded" in data
        assert "estimated_cost" in data


class TestTextractService:
    """Testes para TextractService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        textract_client = Mock()
        factory.get_client.return_value = textract_client
        return factory
    
    def test_textract_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = TextractService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_textract_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_adapters.return_value = {
            'Adapters': []
        }
        service = TextractService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_textract_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Adapters': []}]
        client.get_paginator.return_value = paginator
        
        service = TextractService(mock_client_factory)
        resources = service.get_resources()
        assert "adapters" in resources
        assert "adapter_versions" in resources
        assert "summary" in resources
    
    def test_textract_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Adapters': []}]
        client.get_paginator.return_value = paginator
        
        service = TextractService(mock_client_factory)
        metrics = service.get_metrics()
        assert "adapters_count" in metrics
        assert "feature_coverage" in metrics
    
    def test_textract_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Adapters': []}]
        client.get_paginator.return_value = paginator
        
        service = TextractService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""
    
    def test_service_factory_get_bedrock_service(self):
        """Testa obtenção do BedrockService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_bedrock = Mock()
        factory.register_mock('bedrock', mock_bedrock)
        
        service = factory.get_bedrock_service()
        assert service == mock_bedrock
    
    def test_service_factory_get_comprehend_service(self):
        """Testa obtenção do ComprehendService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_comprehend = Mock()
        factory.register_mock('comprehend', mock_comprehend)
        
        service = factory.get_comprehend_service()
        assert service == mock_comprehend
    
    def test_service_factory_get_rekognition_service(self):
        """Testa obtenção do RekognitionService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_rekognition = Mock()
        factory.register_mock('rekognition', mock_rekognition)
        
        service = factory.get_rekognition_service()
        assert service == mock_rekognition
    
    def test_service_factory_get_textract_service(self):
        """Testa obtenção do TextractService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_textract = Mock()
        factory.register_mock('textract', mock_textract)
        
        service = factory.get_textract_service()
        assert service == mock_textract
    
    def test_service_factory_get_all_services_includes_aiml(self):
        """Testa que get_all_services inclui serviços AI/ML."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        
        factory.register_mock('bedrock', Mock())
        factory.register_mock('comprehend', Mock())
        factory.register_mock('rekognition', Mock())
        factory.register_mock('textract', Mock())
        factory.register_mock('cost', Mock())
        factory.register_mock('metrics', Mock())
        factory.register_mock('optimizer', Mock())
        
        all_services = factory.get_all_services()
        assert 'bedrock' in all_services
        assert 'comprehend' in all_services
        assert 'rekognition' in all_services
        assert 'textract' in all_services
