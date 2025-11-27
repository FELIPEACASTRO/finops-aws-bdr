"""
Testes unitários para FASE 3.4 - IoT & Edge Services.

IoT Core, IoT Analytics, Greengrass, IoT Events.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.iot_service import (
    IoTCoreService, IoTThing, IoTThingType, IoTPolicy, IoTCertificate
)
from src.finops_aws.services.iotanalytics_service import (
    IoTAnalyticsService, IoTAnalyticsChannel, IoTAnalyticsDatastore,
    IoTAnalyticsPipeline, IoTAnalyticsDataset
)
from src.finops_aws.services.greengrass_service import (
    GreengrassService, GreengrassCoreDevice, GreengrassDeployment,
    GreengrassComponent, GreengrassClientDevice
)
from src.finops_aws.services.iotevents_service import (
    IoTEventsService, IoTEventsDetectorModel, IoTEventsInput, IoTEventsAlarmModel
)
from src.finops_aws.core.factories import ServiceFactory


class TestIoTThingDataclass:
    """Testes para IoTThing dataclass."""

    def test_thing_basic(self):
        """Testa criação básica de thing."""
        thing = IoTThing(
            thing_name="sensor-001",
            thing_arn="arn:aws:iot:us-east-1:123456789012:thing/sensor-001"
        )
        assert thing.thing_name == "sensor-001"
        assert thing.has_type is False
        assert thing.has_attributes is False

    def test_thing_with_type(self):
        """Testa thing com tipo."""
        thing = IoTThing(
            thing_name="sensor-001",
            thing_type_name="TemperatureSensor"
        )
        assert thing.has_type is True

    def test_thing_with_attributes(self):
        """Testa thing com atributos."""
        thing = IoTThing(
            thing_name="sensor-001",
            attributes={"location": "factory-1", "model": "v2"}
        )
        assert thing.has_attributes is True
        assert thing.attributes_count == 2

    def test_thing_billing_group(self):
        """Testa thing com billing group."""
        thing = IoTThing(
            thing_name="sensor-001",
            billing_group_name="production-sensors"
        )
        assert thing.has_billing_group is True

    def test_thing_to_dict(self):
        """Testa conversão para dicionário."""
        thing = IoTThing(thing_name="test-thing")
        result = thing.to_dict()
        assert result["thing_name"] == "test-thing"


class TestIoTThingTypeDataclass:
    """Testes para IoTThingType dataclass."""

    def test_thing_type_basic(self):
        """Testa criação básica de thing type."""
        tt = IoTThingType(
            thing_type_name="TemperatureSensor",
            thing_type_arn="arn:aws:iot:us-east-1:123456789012:thingtype/TemperatureSensor"
        )
        assert tt.thing_type_name == "TemperatureSensor"
        assert tt.is_deprecated is False
        assert tt.is_active is True

    def test_thing_type_deprecated(self):
        """Testa thing type deprecated."""
        tt = IoTThingType(
            thing_type_name="OldSensor",
            deprecated=True
        )
        assert tt.is_deprecated is True
        assert tt.is_active is False

    def test_thing_type_searchable_attributes(self):
        """Testa atributos pesquisáveis."""
        tt = IoTThingType(
            thing_type_name="Sensor",
            searchable_attributes=["location", "model", "firmware"]
        )
        assert tt.searchable_attributes_count == 3

    def test_thing_type_to_dict(self):
        """Testa conversão para dicionário."""
        tt = IoTThingType(thing_type_name="TestType")
        result = tt.to_dict()
        assert result["thing_type_name"] == "TestType"


class TestIoTPolicyDataclass:
    """Testes para IoTPolicy dataclass."""

    def test_policy_basic(self):
        """Testa criação básica de policy."""
        policy = IoTPolicy(
            policy_name="device-policy",
            policy_arn="arn:aws:iot:us-east-1:123456789012:policy/device-policy"
        )
        assert policy.policy_name == "device-policy"
        assert policy.has_document is False

    def test_policy_with_document(self):
        """Testa policy com documento."""
        policy = IoTPolicy(
            policy_name="device-policy",
            policy_document='{"Version": "2012-10-17"}'
        )
        assert policy.has_document is True

    def test_policy_version(self):
        """Testa versão da policy."""
        policy = IoTPolicy(
            policy_name="device-policy",
            default_version_id="3"
        )
        assert policy.version == 3

    def test_policy_to_dict(self):
        """Testa conversão para dicionário."""
        policy = IoTPolicy(policy_name="test-policy")
        result = policy.to_dict()
        assert result["policy_name"] == "test-policy"


class TestIoTCertificateDataclass:
    """Testes para IoTCertificate dataclass."""

    def test_certificate_active(self):
        """Testa certificado ativo."""
        cert = IoTCertificate(
            certificate_id="abc123",
            status="ACTIVE"
        )
        assert cert.is_active is True
        assert cert.is_inactive is False
        assert cert.is_revoked is False

    def test_certificate_inactive(self):
        """Testa certificado inativo."""
        cert = IoTCertificate(
            certificate_id="abc123",
            status="INACTIVE"
        )
        assert cert.is_active is False
        assert cert.is_inactive is True

    def test_certificate_revoked(self):
        """Testa certificado revogado."""
        cert = IoTCertificate(
            certificate_id="abc123",
            status="REVOKED"
        )
        assert cert.is_revoked is True

    def test_certificate_pending_transfer(self):
        """Testa certificado em transferência."""
        cert = IoTCertificate(
            certificate_id="abc123",
            status="PENDING_TRANSFER"
        )
        assert cert.is_pending_transfer is True

    def test_certificate_to_dict(self):
        """Testa conversão para dicionário."""
        cert = IoTCertificate(certificate_id="test-cert")
        result = cert.to_dict()
        assert "certificate_id" in result


class TestIoTCoreService:
    """Testes para IoTCoreService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = IoTCoreService(mock_factory)
        assert service._client_factory == mock_factory
        assert service._iot_client is None

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_iot = MagicMock()
        mock_iot.list_things.return_value = {"things": []}
        mock_factory.get_client.return_value = mock_iot

        service = IoTCoreService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "iot"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_iot = MagicMock()
        
        mock_iot.get_paginator.return_value.paginate.return_value = [{
            "things": [], "thingTypes": [], "policies": [], "certificates": []
        }]
        
        mock_factory.get_client.return_value = mock_iot
        service = IoTCoreService(mock_factory)
        
        result = service.get_resources()
        
        assert "things" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_iot = MagicMock()
        
        mock_iot.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_iot
        service = IoTCoreService(mock_factory)
        
        result = service.get_metrics()
        
        assert "things_count" in result

    def test_service_get_recommendations(self):
        """Testa get_recommendations."""
        mock_factory = MagicMock()
        mock_iot = MagicMock()
        
        mock_iot.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_iot
        service = IoTCoreService(mock_factory)
        
        result = service.get_recommendations()
        
        assert isinstance(result, list)


class TestIoTAnalyticsChannelDataclass:
    """Testes para IoTAnalyticsChannel dataclass."""

    def test_channel_basic(self):
        """Testa criação básica de channel."""
        channel = IoTAnalyticsChannel(
            channel_name="sensor-data",
            status="ACTIVE"
        )
        assert channel.channel_name == "sensor-data"
        assert channel.is_active is True

    def test_channel_retention(self):
        """Testa retenção do channel."""
        channel = IoTAnalyticsChannel(
            channel_name="sensor-data",
            retention_period={"numberOfDays": 30}
        )
        assert channel.retention_days == 30
        assert channel.has_unlimited_retention is False

    def test_channel_unlimited_retention(self):
        """Testa retenção ilimitada."""
        channel = IoTAnalyticsChannel(
            channel_name="sensor-data",
            retention_period={"unlimited": True}
        )
        assert channel.retention_days == -1
        assert channel.has_unlimited_retention is True

    def test_channel_customer_s3(self):
        """Testa channel com S3 gerenciado pelo cliente."""
        channel = IoTAnalyticsChannel(
            channel_name="sensor-data",
            storage={"customerManagedS3": {"bucket": "my-bucket"}}
        )
        assert channel.uses_customer_managed_s3 is True
        assert channel.uses_service_managed_s3 is False

    def test_channel_to_dict(self):
        """Testa conversão para dicionário."""
        channel = IoTAnalyticsChannel(channel_name="test-channel")
        result = channel.to_dict()
        assert result["channel_name"] == "test-channel"


class TestIoTAnalyticsDatastoreDataclass:
    """Testes para IoTAnalyticsDatastore dataclass."""

    def test_datastore_basic(self):
        """Testa criação básica de datastore."""
        ds = IoTAnalyticsDatastore(
            datastore_name="sensor-store",
            status="ACTIVE"
        )
        assert ds.datastore_name == "sensor-store"
        assert ds.is_active is True

    def test_datastore_parquet(self):
        """Testa datastore com formato Parquet."""
        ds = IoTAnalyticsDatastore(
            datastore_name="sensor-store",
            file_format_configuration={"parquetConfiguration": {}}
        )
        assert ds.uses_parquet is True
        assert ds.uses_json is False

    def test_datastore_json(self):
        """Testa datastore com formato JSON."""
        ds = IoTAnalyticsDatastore(
            datastore_name="sensor-store",
            file_format_configuration={"jsonConfiguration": {}}
        )
        assert ds.uses_json is True
        assert ds.uses_parquet is False

    def test_datastore_to_dict(self):
        """Testa conversão para dicionário."""
        ds = IoTAnalyticsDatastore(datastore_name="test-store")
        result = ds.to_dict()
        assert result["datastore_name"] == "test-store"


class TestIoTAnalyticsPipelineDataclass:
    """Testes para IoTAnalyticsPipeline dataclass."""

    def test_pipeline_basic(self):
        """Testa criação básica de pipeline."""
        pipeline = IoTAnalyticsPipeline(
            pipeline_name="data-pipeline",
            activities=[{"channel": {}}, {"datastore": {}}]
        )
        assert pipeline.pipeline_name == "data-pipeline"
        assert pipeline.activities_count == 2

    def test_pipeline_lambda(self):
        """Testa pipeline com Lambda."""
        pipeline = IoTAnalyticsPipeline(
            pipeline_name="data-pipeline",
            activities=[{"lambda": {"lambdaName": "processor"}}]
        )
        assert pipeline.has_lambda_activity is True

    def test_pipeline_filter(self):
        """Testa pipeline com filtro."""
        pipeline = IoTAnalyticsPipeline(
            pipeline_name="data-pipeline",
            activities=[{"filter": {"expression": "temp > 30"}}]
        )
        assert pipeline.has_filter_activity is True

    def test_pipeline_reprocessing(self):
        """Testa pipeline em reprocessamento."""
        pipeline = IoTAnalyticsPipeline(
            pipeline_name="data-pipeline",
            reprocessing_summaries=[{"status": "RUNNING"}]
        )
        assert pipeline.is_reprocessing is True

    def test_pipeline_to_dict(self):
        """Testa conversão para dicionário."""
        pipeline = IoTAnalyticsPipeline(pipeline_name="test-pipeline")
        result = pipeline.to_dict()
        assert result["pipeline_name"] == "test-pipeline"


class TestIoTAnalyticsDatasetDataclass:
    """Testes para IoTAnalyticsDataset dataclass."""

    def test_dataset_basic(self):
        """Testa criação básica de dataset."""
        dataset = IoTAnalyticsDataset(
            dataset_name="hourly-report",
            status="ACTIVE"
        )
        assert dataset.dataset_name == "hourly-report"
        assert dataset.is_active is True

    def test_dataset_triggers(self):
        """Testa dataset com triggers."""
        dataset = IoTAnalyticsDataset(
            dataset_name="hourly-report",
            triggers=[{"schedule": {"expression": "rate(1 hour)"}}]
        )
        assert dataset.triggers_count == 1
        assert dataset.has_schedule_trigger is True

    def test_dataset_content_delivery(self):
        """Testa dataset com entrega de conteúdo."""
        dataset = IoTAnalyticsDataset(
            dataset_name="hourly-report",
            content_delivery_rules=[{"destination": {"s3DestinationConfiguration": {}}}]
        )
        assert dataset.has_content_delivery is True

    def test_dataset_to_dict(self):
        """Testa conversão para dicionário."""
        dataset = IoTAnalyticsDataset(dataset_name="test-dataset")
        result = dataset.to_dict()
        assert result["dataset_name"] == "test-dataset"


class TestIoTAnalyticsService:
    """Testes para IoTAnalyticsService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = IoTAnalyticsService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_channels.return_value = {"channelSummaries": []}
        mock_factory.get_client.return_value = mock_client

        service = IoTAnalyticsService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = IoTAnalyticsService(mock_factory)
        
        result = service.get_resources()
        
        assert "channels" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = IoTAnalyticsService(mock_factory)
        
        result = service.get_metrics()
        
        assert "channels_count" in result


class TestGreengrassCoreDeviceDataclass:
    """Testes para GreengrassCoreDevice dataclass."""

    def test_device_healthy(self):
        """Testa device saudável."""
        device = GreengrassCoreDevice(
            core_device_thing_name="core-001",
            status="HEALTHY"
        )
        assert device.is_healthy is True
        assert device.is_unhealthy is False
        assert device.is_offline is False

    def test_device_unhealthy(self):
        """Testa device com problemas."""
        device = GreengrassCoreDevice(
            core_device_thing_name="core-001",
            status="UNHEALTHY"
        )
        assert device.is_healthy is False
        assert device.is_unhealthy is True

    def test_device_offline(self):
        """Testa device offline."""
        device = GreengrassCoreDevice(
            core_device_thing_name="core-001",
            status="OFFLINE"
        )
        assert device.is_offline is True

    def test_device_tags(self):
        """Testa device com tags."""
        device = GreengrassCoreDevice(
            core_device_thing_name="core-001",
            tags={"env": "prod"}
        )
        assert device.has_tags is True

    def test_device_to_dict(self):
        """Testa conversão para dicionário."""
        device = GreengrassCoreDevice(core_device_thing_name="test-device")
        result = device.to_dict()
        assert result["core_device_thing_name"] == "test-device"


class TestGreengrassDeploymentDataclass:
    """Testes para GreengrassDeployment dataclass."""

    def test_deployment_active(self):
        """Testa deployment ativo."""
        dep = GreengrassDeployment(
            deployment_id="dep-001",
            deployment_status="ACTIVE"
        )
        assert dep.is_active is True
        assert dep.is_completed is False

    def test_deployment_completed(self):
        """Testa deployment completo."""
        dep = GreengrassDeployment(
            deployment_id="dep-001",
            deployment_status="COMPLETED"
        )
        assert dep.is_completed is True

    def test_deployment_failed(self):
        """Testa deployment com falha."""
        dep = GreengrassDeployment(
            deployment_id="dep-001",
            deployment_status="FAILED"
        )
        assert dep.is_failed is True

    def test_deployment_canceled(self):
        """Testa deployment cancelado."""
        dep = GreengrassDeployment(
            deployment_id="dep-001",
            deployment_status="CANCELED"
        )
        assert dep.is_canceled is True

    def test_deployment_to_dict(self):
        """Testa conversão para dicionário."""
        dep = GreengrassDeployment(deployment_id="test-dep")
        result = dep.to_dict()
        assert result["deployment_id"] == "test-dep"


class TestGreengrassComponentDataclass:
    """Testes para GreengrassComponent dataclass."""

    def test_component_aws(self):
        """Testa componente AWS."""
        comp = GreengrassComponent(
            component_name="aws.greengrass.Nucleus",
            latest_version={"publisher": "AWS", "componentVersion": "2.10.0"}
        )
        assert comp.is_aws_provided is True
        assert comp.is_custom is False
        assert comp.component_version == "2.10.0"

    def test_component_custom(self):
        """Testa componente customizado."""
        comp = GreengrassComponent(
            component_name="my.custom.component",
            latest_version={"publisher": "MyCompany", "componentVersion": "1.0.0"}
        )
        assert comp.is_aws_provided is False
        assert comp.is_custom is True

    def test_component_to_dict(self):
        """Testa conversão para dicionário."""
        comp = GreengrassComponent(component_name="test-component")
        result = comp.to_dict()
        assert result["component_name"] == "test-component"


class TestGreengrassService:
    """Testes para GreengrassService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = GreengrassService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_core_devices.return_value = {"coreDevices": []}
        mock_factory.get_client.return_value = mock_client

        service = GreengrassService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = GreengrassService(mock_factory)
        
        result = service.get_resources()
        
        assert "core_devices" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = GreengrassService(mock_factory)
        
        result = service.get_metrics()
        
        assert "core_devices_count" in result


class TestIoTEventsDetectorModelDataclass:
    """Testes para IoTEventsDetectorModel dataclass."""

    def test_detector_active(self):
        """Testa detector ativo."""
        detector = IoTEventsDetectorModel(
            detector_model_name="temperature-detector",
            status="ACTIVE"
        )
        assert detector.is_active is True
        assert detector.is_inactive is False

    def test_detector_batch_evaluation(self):
        """Testa detector com avaliação batch."""
        detector = IoTEventsDetectorModel(
            detector_model_name="temperature-detector",
            evaluation_method="BATCH"
        )
        assert detector.uses_batch_evaluation is True
        assert detector.uses_serial_evaluation is False

    def test_detector_serial_evaluation(self):
        """Testa detector com avaliação serial."""
        detector = IoTEventsDetectorModel(
            detector_model_name="temperature-detector",
            evaluation_method="SERIAL"
        )
        assert detector.uses_serial_evaluation is True

    def test_detector_with_key(self):
        """Testa detector com key."""
        detector = IoTEventsDetectorModel(
            detector_model_name="temperature-detector",
            key="deviceId"
        )
        assert detector.has_key is True

    def test_detector_to_dict(self):
        """Testa conversão para dicionário."""
        detector = IoTEventsDetectorModel(detector_model_name="test-detector")
        result = detector.to_dict()
        assert result["detector_model_name"] == "test-detector"


class TestIoTEventsInputDataclass:
    """Testes para IoTEventsInput dataclass."""

    def test_input_active(self):
        """Testa input ativo."""
        inp = IoTEventsInput(
            input_name="sensor-input",
            status="ACTIVE"
        )
        assert inp.is_active is True

    def test_input_with_definition(self):
        """Testa input com definição."""
        inp = IoTEventsInput(
            input_name="sensor-input",
            input_definition={"attributes": [{"jsonPath": "$.temperature"}]}
        )
        assert inp.has_definition is True
        assert inp.attributes_count == 1

    def test_input_to_dict(self):
        """Testa conversão para dicionário."""
        inp = IoTEventsInput(input_name="test-input")
        result = inp.to_dict()
        assert result["input_name"] == "test-input"


class TestIoTEventsAlarmModelDataclass:
    """Testes para IoTEventsAlarmModel dataclass."""

    def test_alarm_active(self):
        """Testa alarm ativo."""
        alarm = IoTEventsAlarmModel(
            alarm_model_name="temperature-alarm",
            status="ACTIVE"
        )
        assert alarm.is_active is True

    def test_alarm_severity_critical(self):
        """Testa alarm crítico."""
        alarm = IoTEventsAlarmModel(
            alarm_model_name="temperature-alarm",
            severity=9
        )
        assert alarm.is_critical is True
        assert alarm.is_high is False

    def test_alarm_severity_high(self):
        """Testa alarm alta severidade."""
        alarm = IoTEventsAlarmModel(
            alarm_model_name="temperature-alarm",
            severity=6
        )
        assert alarm.is_high is True
        assert alarm.is_critical is False

    def test_alarm_severity_medium(self):
        """Testa alarm média severidade."""
        alarm = IoTEventsAlarmModel(
            alarm_model_name="temperature-alarm",
            severity=4
        )
        assert alarm.is_medium is True

    def test_alarm_severity_low(self):
        """Testa alarm baixa severidade."""
        alarm = IoTEventsAlarmModel(
            alarm_model_name="temperature-alarm",
            severity=2
        )
        assert alarm.is_low is True

    def test_alarm_version(self):
        """Testa versão do alarm."""
        alarm = IoTEventsAlarmModel(
            alarm_model_name="temperature-alarm",
            alarm_model_version="5"
        )
        assert alarm.version_number == 5

    def test_alarm_to_dict(self):
        """Testa conversão para dicionário."""
        alarm = IoTEventsAlarmModel(alarm_model_name="test-alarm")
        result = alarm.to_dict()
        assert result["alarm_model_name"] == "test-alarm"


class TestIoTEventsService:
    """Testes para IoTEventsService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = IoTEventsService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_detector_models.return_value = {"detectorModelSummaries": []}
        mock_factory.get_client.return_value = mock_client

        service = IoTEventsService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.list_detector_models.return_value = {"detectorModelSummaries": []}
        mock_client.list_inputs.return_value = {"inputSummaries": []}
        mock_client.list_alarm_models.return_value = {"alarmModelSummaries": []}
        
        mock_factory.get_client.return_value = mock_client
        service = IoTEventsService(mock_factory)
        
        result = service.get_resources()
        
        assert "detector_models" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.list_detector_models.return_value = {"detectorModelSummaries": []}
        mock_client.list_inputs.return_value = {"inputSummaries": []}
        mock_client.list_alarm_models.return_value = {"alarmModelSummaries": []}
        
        mock_factory.get_client.return_value = mock_client
        service = IoTEventsService(mock_factory)
        
        result = service.get_metrics()
        
        assert "detector_models_count" in result


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_service_factory_get_iot_service(self):
        """Testa obtenção do IoTCoreService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_iot_service()
        
        assert isinstance(service, IoTCoreService)

    def test_service_factory_get_iotanalytics_service(self):
        """Testa obtenção do IoTAnalyticsService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_iotanalytics_service()
        
        assert isinstance(service, IoTAnalyticsService)

    def test_service_factory_get_greengrass_service(self):
        """Testa obtenção do GreengrassService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_greengrass_service()
        
        assert isinstance(service, GreengrassService)

    def test_service_factory_get_iotevents_service(self):
        """Testa obtenção do IoTEventsService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_iotevents_service()
        
        assert isinstance(service, IoTEventsService)

    def test_service_factory_get_all_services_includes_iot(self):
        """Testa que get_all_services inclui serviços IoT."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'iot' in services
        assert 'iotanalytics' in services
        assert 'greengrass' in services
        assert 'iotevents' in services
