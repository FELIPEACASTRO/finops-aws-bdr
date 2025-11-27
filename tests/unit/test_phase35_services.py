"""
Testes unitários para FASE 3.5 - Media Services.

MediaConvert, MediaLive, MediaPackage, IVS.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.mediaconvert_service import (
    MediaConvertService, MediaConvertJob, MediaConvertQueue, MediaConvertPreset
)
from src.finops_aws.services.medialive_service import (
    MediaLiveService, MediaLiveChannel, MediaLiveInput, MediaLiveInputSecurityGroup
)
from src.finops_aws.services.mediapackage_service import (
    MediaPackageService, MediaPackageChannel, MediaPackageOriginEndpoint, MediaPackageHarvestJob
)
from src.finops_aws.services.ivs_service import (
    IVSService, IVSChannel, IVSStream, IVSRecordingConfiguration, IVSPlaybackKeyPair
)
from src.finops_aws.core.factories import ServiceFactory


class TestMediaConvertJobDataclass:
    """Testes para MediaConvertJob dataclass."""

    def test_job_complete(self):
        """Testa job completo."""
        job = MediaConvertJob(
            job_id="job-001",
            status="COMPLETE"
        )
        assert job.is_complete is True
        assert job.is_error is False
        assert job.is_progressing is False

    def test_job_error(self):
        """Testa job com erro."""
        job = MediaConvertJob(
            job_id="job-001",
            status="ERROR",
            error_message="Input file not found"
        )
        assert job.is_error is True
        assert job.has_error is True

    def test_job_progressing(self):
        """Testa job em progresso."""
        job = MediaConvertJob(
            job_id="job-001",
            status="PROGRESSING"
        )
        assert job.is_progressing is True

    def test_job_submitted(self):
        """Testa job submetido."""
        job = MediaConvertJob(
            job_id="job-001",
            status="SUBMITTED"
        )
        assert job.is_submitted is True

    def test_job_canceled(self):
        """Testa job cancelado."""
        job = MediaConvertJob(
            job_id="job-001",
            status="CANCELED"
        )
        assert job.is_canceled is True

    def test_job_output_groups(self):
        """Testa grupos de saída."""
        job = MediaConvertJob(
            job_id="job-001",
            settings={"OutputGroups": [{"Name": "HLS"}, {"Name": "DASH"}]}
        )
        assert job.output_groups_count == 2

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = MediaConvertJob(job_id="test-job")
        result = job.to_dict()
        assert result["job_id"] == "test-job"


class TestMediaConvertQueueDataclass:
    """Testes para MediaConvertQueue dataclass."""

    def test_queue_active(self):
        """Testa queue ativo."""
        queue = MediaConvertQueue(
            name="default",
            status="ACTIVE"
        )
        assert queue.is_active is True
        assert queue.is_paused is False

    def test_queue_paused(self):
        """Testa queue pausada."""
        queue = MediaConvertQueue(
            name="default",
            status="PAUSED"
        )
        assert queue.is_paused is True

    def test_queue_on_demand(self):
        """Testa queue on-demand."""
        queue = MediaConvertQueue(
            name="default",
            pricing_plan="ON_DEMAND"
        )
        assert queue.is_on_demand is True
        assert queue.is_reserved is False

    def test_queue_reserved(self):
        """Testa queue reservada."""
        queue = MediaConvertQueue(
            name="reserved-queue",
            pricing_plan="RESERVED",
            reservation_plan_settings={"ReservedSlots": 10}
        )
        assert queue.is_reserved is True
        assert queue.has_reserved_slots is True
        assert queue.reserved_slots == 10

    def test_queue_to_dict(self):
        """Testa conversão para dicionário."""
        queue = MediaConvertQueue(name="test-queue")
        result = queue.to_dict()
        assert result["name"] == "test-queue"


class TestMediaConvertPresetDataclass:
    """Testes para MediaConvertPreset dataclass."""

    def test_preset_custom(self):
        """Testa preset customizado."""
        preset = MediaConvertPreset(
            name="my-preset",
            type="CUSTOM"
        )
        assert preset.is_custom is True
        assert preset.is_system is False

    def test_preset_system(self):
        """Testa preset do sistema."""
        preset = MediaConvertPreset(
            name="System-Preset",
            type="SYSTEM"
        )
        assert preset.is_system is True
        assert preset.is_custom is False

    def test_preset_with_video(self):
        """Testa preset com vídeo."""
        preset = MediaConvertPreset(
            name="video-preset",
            settings={"VideoDescription": {"Codec": "H_264"}}
        )
        assert preset.has_video_settings is True

    def test_preset_with_audio(self):
        """Testa preset com áudio."""
        preset = MediaConvertPreset(
            name="audio-preset",
            settings={"AudioDescriptions": [{"Codec": "AAC"}]}
        )
        assert preset.has_audio_settings is True

    def test_preset_to_dict(self):
        """Testa conversão para dicionário."""
        preset = MediaConvertPreset(name="test-preset")
        result = preset.to_dict()
        assert result["name"] == "test-preset"


class TestMediaConvertService:
    """Testes para MediaConvertService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = MediaConvertService(mock_factory)
        assert service._client_factory == mock_factory
        assert service._mediaconvert_client is None

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_queues.return_value = {"Queues": []}
        mock_factory.get_client.return_value = mock_client

        service = MediaConvertService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "mediaconvert"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        mock_client.list_jobs.return_value = {"Jobs": []}
        
        mock_factory.get_client.return_value = mock_client
        service = MediaConvertService(mock_factory)
        
        result = service.get_resources()
        
        assert "queues" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        mock_client.list_jobs.return_value = {"Jobs": []}
        
        mock_factory.get_client.return_value = mock_client
        service = MediaConvertService(mock_factory)
        
        result = service.get_metrics()
        
        assert "queues_count" in result


class TestMediaLiveChannelDataclass:
    """Testes para MediaLiveChannel dataclass."""

    def test_channel_running(self):
        """Testa channel rodando."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            state="RUNNING"
        )
        assert channel.is_running is True
        assert channel.is_idle is False

    def test_channel_idle(self):
        """Testa channel ocioso."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            state="IDLE"
        )
        assert channel.is_idle is True

    def test_channel_starting(self):
        """Testa channel iniciando."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            state="STARTING"
        )
        assert channel.is_starting is True

    def test_channel_stopping(self):
        """Testa channel parando."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            state="STOPPING"
        )
        assert channel.is_stopping is True

    def test_channel_standard_class(self):
        """Testa channel classe standard."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            channel_class="STANDARD"
        )
        assert channel.is_standard_class is True
        assert channel.is_single_pipeline is False
        assert channel.estimated_hourly_cost == pytest.approx(3.0)

    def test_channel_single_pipeline(self):
        """Testa channel single pipeline."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            channel_class="SINGLE_PIPELINE"
        )
        assert channel.is_single_pipeline is True
        assert channel.estimated_hourly_cost == pytest.approx(1.5)

    def test_channel_inputs_outputs(self):
        """Testa inputs e outputs."""
        channel = MediaLiveChannel(
            channel_id="ch-001",
            input_attachments=[{"Id": "inp1"}, {"Id": "inp2"}],
            destinations=[{"Id": "dest1"}]
        )
        assert channel.inputs_count == 2
        assert channel.outputs_count == 1

    def test_channel_to_dict(self):
        """Testa conversão para dicionário."""
        channel = MediaLiveChannel(channel_id="test-ch")
        result = channel.to_dict()
        assert result["channel_id"] == "test-ch"


class TestMediaLiveInputDataclass:
    """Testes para MediaLiveInput dataclass."""

    def test_input_attached(self):
        """Testa input anexado."""
        inp = MediaLiveInput(
            input_id="inp-001",
            state="ATTACHED"
        )
        assert inp.is_attached is True
        assert inp.is_detached is False

    def test_input_detached(self):
        """Testa input desanexado."""
        inp = MediaLiveInput(
            input_id="inp-001",
            state="DETACHED"
        )
        assert inp.is_detached is True

    def test_input_creating(self):
        """Testa input sendo criado."""
        inp = MediaLiveInput(
            input_id="inp-001",
            state="CREATING"
        )
        assert inp.is_creating is True

    def test_input_url_pull(self):
        """Testa input URL pull."""
        inp = MediaLiveInput(
            input_id="inp-001",
            type="URL_PULL"
        )
        assert inp.is_url_pull is True

    def test_input_rtmp_push(self):
        """Testa input RTMP push."""
        inp = MediaLiveInput(
            input_id="inp-001",
            type="RTMP_PUSH"
        )
        assert inp.is_rtmp_push is True

    def test_input_rtp_push(self):
        """Testa input RTP push."""
        inp = MediaLiveInput(
            input_id="inp-001",
            type="RTP_PUSH"
        )
        assert inp.is_rtp_push is True

    def test_input_channels_count(self):
        """Testa contagem de canais."""
        inp = MediaLiveInput(
            input_id="inp-001",
            attached_channels=["ch1", "ch2", "ch3"]
        )
        assert inp.channels_count == 3

    def test_input_to_dict(self):
        """Testa conversão para dicionário."""
        inp = MediaLiveInput(input_id="test-input")
        result = inp.to_dict()
        assert result["input_id"] == "test-input"


class TestMediaLiveInputSecurityGroupDataclass:
    """Testes para MediaLiveInputSecurityGroup dataclass."""

    def test_sg_idle(self):
        """Testa security group ocioso."""
        sg = MediaLiveInputSecurityGroup(
            security_group_id="sg-001",
            state="IDLE"
        )
        assert sg.is_idle is True
        assert sg.is_in_use is False

    def test_sg_in_use(self):
        """Testa security group em uso."""
        sg = MediaLiveInputSecurityGroup(
            security_group_id="sg-001",
            state="IN_USE"
        )
        assert sg.is_in_use is True

    def test_sg_rules_count(self):
        """Testa contagem de regras."""
        sg = MediaLiveInputSecurityGroup(
            security_group_id="sg-001",
            whitelist_rules=[{"Cidr": "10.0.0.0/8"}, {"Cidr": "192.168.0.0/16"}]
        )
        assert sg.rules_count == 2

    def test_sg_to_dict(self):
        """Testa conversão para dicionário."""
        sg = MediaLiveInputSecurityGroup(security_group_id="test-sg")
        result = sg.to_dict()
        assert result["security_group_id"] == "test-sg"


class TestMediaLiveService:
    """Testes para MediaLiveService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = MediaLiveService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_channels.return_value = {"Channels": []}
        mock_factory.get_client.return_value = mock_client

        service = MediaLiveService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = MediaLiveService(mock_factory)
        
        result = service.get_resources()
        
        assert "channels" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = MediaLiveService(mock_factory)
        
        result = service.get_metrics()
        
        assert "channels_count" in result


class TestMediaPackageChannelDataclass:
    """Testes para MediaPackageChannel dataclass."""

    def test_channel_basic(self):
        """Testa canal básico."""
        channel = MediaPackageChannel(
            channel_id="ch-001"
        )
        assert channel.channel_id == "ch-001"
        assert channel.has_ingress_logs is False
        assert channel.has_egress_logs is False

    def test_channel_with_logs(self):
        """Testa canal com logs."""
        channel = MediaPackageChannel(
            channel_id="ch-001",
            ingress_access_logs={"LogGroupName": "/aws/mediapackage"},
            egress_access_logs={"LogGroupName": "/aws/mediapackage"}
        )
        assert channel.has_ingress_logs is True
        assert channel.has_egress_logs is True

    def test_channel_ingest_endpoints(self):
        """Testa endpoints de ingestão."""
        channel = MediaPackageChannel(
            channel_id="ch-001",
            hls_ingest={"ingestEndpoints": [{"Id": "ep1"}, {"Id": "ep2"}]}
        )
        assert channel.ingest_endpoints_count == 2

    def test_channel_tags(self):
        """Testa tags."""
        channel = MediaPackageChannel(
            channel_id="ch-001",
            tags={"env": "prod"}
        )
        assert channel.has_tags is True

    def test_channel_to_dict(self):
        """Testa conversão para dicionário."""
        channel = MediaPackageChannel(channel_id="test-ch")
        result = channel.to_dict()
        assert result["channel_id"] == "test-ch"


class TestMediaPackageOriginEndpointDataclass:
    """Testes para MediaPackageOriginEndpoint dataclass."""

    def test_endpoint_allow(self):
        """Testa endpoint com origination ALLOW."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            origination="ALLOW"
        )
        assert ep.is_allow is True
        assert ep.is_deny is False

    def test_endpoint_deny(self):
        """Testa endpoint com origination DENY."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            origination="DENY"
        )
        assert ep.is_deny is True

    def test_endpoint_hls(self):
        """Testa endpoint com HLS."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            hls_package={"SegmentDurationSeconds": 6}
        )
        assert ep.has_hls is True

    def test_endpoint_dash(self):
        """Testa endpoint com DASH."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            dash_package={"SegmentDurationSeconds": 6}
        )
        assert ep.has_dash is True

    def test_endpoint_cmaf(self):
        """Testa endpoint com CMAF."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            cmaf_package={"SegmentDurationSeconds": 6}
        )
        assert ep.has_cmaf is True

    def test_endpoint_mss(self):
        """Testa endpoint com MSS."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            mss_package={"SegmentDurationSeconds": 6}
        )
        assert ep.has_mss is True

    def test_endpoint_time_delay(self):
        """Testa endpoint com atraso."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            time_delay_seconds=30
        )
        assert ep.has_time_delay is True

    def test_endpoint_startover(self):
        """Testa endpoint com startover."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            startover_window_seconds=3600
        )
        assert ep.has_startover is True

    def test_endpoint_whitelist(self):
        """Testa endpoint com whitelist."""
        ep = MediaPackageOriginEndpoint(
            endpoint_id="ep-001",
            whitelist=["10.0.0.1", "10.0.0.2"]
        )
        assert ep.has_whitelist is True

    def test_endpoint_to_dict(self):
        """Testa conversão para dicionário."""
        ep = MediaPackageOriginEndpoint(endpoint_id="test-ep")
        result = ep.to_dict()
        assert result["endpoint_id"] == "test-ep"


class TestMediaPackageHarvestJobDataclass:
    """Testes para MediaPackageHarvestJob dataclass."""

    def test_job_in_progress(self):
        """Testa job em progresso."""
        job = MediaPackageHarvestJob(
            harvest_job_id="job-001",
            status="IN_PROGRESS"
        )
        assert job.is_in_progress is True
        assert job.is_succeeded is False

    def test_job_succeeded(self):
        """Testa job com sucesso."""
        job = MediaPackageHarvestJob(
            harvest_job_id="job-001",
            status="SUCCEEDED"
        )
        assert job.is_succeeded is True

    def test_job_failed(self):
        """Testa job com falha."""
        job = MediaPackageHarvestJob(
            harvest_job_id="job-001",
            status="FAILED"
        )
        assert job.is_failed is True

    def test_job_s3_destination(self):
        """Testa destino S3."""
        job = MediaPackageHarvestJob(
            harvest_job_id="job-001",
            s3_destination={"BucketName": "my-bucket", "ManifestKey": "video/manifest"}
        )
        assert job.s3_bucket == "my-bucket"
        assert job.s3_manifest_key == "video/manifest"

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = MediaPackageHarvestJob(harvest_job_id="test-job")
        result = job.to_dict()
        assert result["harvest_job_id"] == "test-job"


class TestMediaPackageService:
    """Testes para MediaPackageService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = MediaPackageService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_channels.return_value = {"Channels": []}
        mock_factory.get_client.return_value = mock_client

        service = MediaPackageService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = MediaPackageService(mock_factory)
        
        result = service.get_resources()
        
        assert "channels" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = MediaPackageService(mock_factory)
        
        result = service.get_metrics()
        
        assert "channels_count" in result


class TestIVSChannelDataclass:
    """Testes para IVSChannel dataclass."""

    def test_channel_low_latency(self):
        """Testa channel baixa latência."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            latency_mode="LOW"
        )
        assert channel.is_low_latency is True
        assert channel.is_normal_latency is False

    def test_channel_normal_latency(self):
        """Testa channel latência normal."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            latency_mode="NORMAL"
        )
        assert channel.is_normal_latency is True

    def test_channel_standard_type(self):
        """Testa channel tipo standard."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            type="STANDARD"
        )
        assert channel.is_standard_type is True
        assert channel.is_basic_type is False
        assert channel.estimated_hourly_cost == pytest.approx(2.0)

    def test_channel_basic_type(self):
        """Testa channel tipo basic."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            type="BASIC"
        )
        assert channel.is_basic_type is True
        assert channel.estimated_hourly_cost == pytest.approx(0.20)

    def test_channel_with_recording(self):
        """Testa channel com gravação."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            recording_configuration_arn="arn:aws:ivs:us-east-1:123:recording/rc1"
        )
        assert channel.has_recording is True

    def test_channel_authorized(self):
        """Testa channel autorizado."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            authorized=True
        )
        assert channel.is_authorized is True

    def test_channel_insecure(self):
        """Testa channel inseguro."""
        channel = IVSChannel(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            insecure_ingest=True
        )
        assert channel.is_insecure is True

    def test_channel_to_dict(self):
        """Testa conversão para dicionário."""
        channel = IVSChannel(channel_arn="test-arn")
        result = channel.to_dict()
        assert result["channel_arn"] == "test-arn"


class TestIVSStreamDataclass:
    """Testes para IVSStream dataclass."""

    def test_stream_live(self):
        """Testa stream ao vivo."""
        stream = IVSStream(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            state="LIVE"
        )
        assert stream.is_live is True
        assert stream.is_offline is False

    def test_stream_offline(self):
        """Testa stream offline."""
        stream = IVSStream(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            state="OFFLINE"
        )
        assert stream.is_offline is True

    def test_stream_healthy(self):
        """Testa stream saudável."""
        stream = IVSStream(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            health="HEALTHY"
        )
        assert stream.is_healthy is True
        assert stream.is_starving is False

    def test_stream_starving(self):
        """Testa stream com problemas."""
        stream = IVSStream(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            health="STARVING"
        )
        assert stream.is_starving is True

    def test_stream_viewers(self):
        """Testa viewers."""
        stream = IVSStream(
            channel_arn="arn:aws:ivs:us-east-1:123:channel/ch1",
            viewer_count=150
        )
        assert stream.has_viewers is True

    def test_stream_to_dict(self):
        """Testa conversão para dicionário."""
        stream = IVSStream(channel_arn="test-arn")
        result = stream.to_dict()
        assert result["channel_arn"] == "test-arn"


class TestIVSRecordingConfigurationDataclass:
    """Testes para IVSRecordingConfiguration dataclass."""

    def test_config_active(self):
        """Testa config ativa."""
        config = IVSRecordingConfiguration(
            recording_configuration_arn="arn:...",
            state="ACTIVE"
        )
        assert config.is_active is True
        assert config.is_creating is False
        assert config.is_failed is False

    def test_config_creating(self):
        """Testa config sendo criada."""
        config = IVSRecordingConfiguration(
            recording_configuration_arn="arn:...",
            state="CREATING"
        )
        assert config.is_creating is True

    def test_config_failed(self):
        """Testa config com falha."""
        config = IVSRecordingConfiguration(
            recording_configuration_arn="arn:...",
            state="CREATE_FAILED"
        )
        assert config.is_failed is True

    def test_config_s3_bucket(self):
        """Testa bucket S3."""
        config = IVSRecordingConfiguration(
            recording_configuration_arn="arn:...",
            destination_configuration={"s3": {"bucketName": "my-recordings"}}
        )
        assert config.s3_bucket == "my-recordings"

    def test_config_thumbnails(self):
        """Testa thumbnails."""
        config = IVSRecordingConfiguration(
            recording_configuration_arn="arn:...",
            thumbnail_configuration={"recordingMode": "INTERVAL"}
        )
        assert config.has_thumbnails is True

    def test_config_reconnect_window(self):
        """Testa janela de reconexão."""
        config = IVSRecordingConfiguration(
            recording_configuration_arn="arn:...",
            recording_reconnect_window_seconds=60
        )
        assert config.has_reconnect_window is True

    def test_config_to_dict(self):
        """Testa conversão para dicionário."""
        config = IVSRecordingConfiguration(recording_configuration_arn="test-arn")
        result = config.to_dict()
        assert result["recording_configuration_arn"] == "test-arn"


class TestIVSPlaybackKeyPairDataclass:
    """Testes para IVSPlaybackKeyPair dataclass."""

    def test_key_pair_basic(self):
        """Testa key pair básico."""
        kp = IVSPlaybackKeyPair(
            key_pair_arn="arn:...",
            name="my-key",
            fingerprint="abc123def456"
        )
        assert kp.name == "my-key"

    def test_key_pair_to_dict(self):
        """Testa conversão para dicionário."""
        kp = IVSPlaybackKeyPair(key_pair_arn="test-arn")
        result = kp.to_dict()
        assert result["key_pair_arn"] == "test-arn"


class TestIVSService:
    """Testes para IVSService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = IVSService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_channels.return_value = {"channels": []}
        mock_factory.get_client.return_value = mock_client

        service = IVSService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = IVSService(mock_factory)
        
        result = service.get_resources()
        
        assert "channels" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = IVSService(mock_factory)
        
        result = service.get_metrics()
        
        assert "channels_count" in result


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_mediaconvert_service(self):
        """Testa obtenção do MediaConvertService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_mediaconvert_service()
        
        assert isinstance(service, MediaConvertService)

    def test_factory_get_medialive_service(self):
        """Testa obtenção do MediaLiveService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_medialive_service()
        
        assert isinstance(service, MediaLiveService)

    def test_factory_get_mediapackage_service(self):
        """Testa obtenção do MediaPackageService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_mediapackage_service()
        
        assert isinstance(service, MediaPackageService)

    def test_factory_get_ivs_service(self):
        """Testa obtenção do IVSService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_ivs_service()
        
        assert isinstance(service, IVSService)

    def test_factory_get_all_services_includes_media(self):
        """Testa que get_all_services inclui serviços Media."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'mediaconvert' in services
        assert 'medialive' in services
        assert 'mediapackage' in services
        assert 'ivs' in services
