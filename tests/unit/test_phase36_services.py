"""
Testes unitários para FASE 3.6 - Migration & Transfer Services.

DMS, MGN, Snow Family, Data Pipeline.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.dms_service import (
    DMSService, DMSReplicationInstance, DMSEndpoint, DMSReplicationTask
)
from src.finops_aws.services.mgn_service import (
    MGNService, MGNSourceServer, MGNJob, MGNLaunchConfiguration
)
from src.finops_aws.services.snowfamily_service import (
    SnowFamilyService, SnowballJob, SnowballCluster
)
from src.finops_aws.services.datapipeline_service import (
    DataPipelineService, DataPipeline, DataPipelineObject, DataPipelineTaskRun
)
from src.finops_aws.core.factories import ServiceFactory


class TestDMSReplicationInstanceDataclass:
    """Testes para DMSReplicationInstance dataclass."""

    def test_instance_available(self):
        """Testa instância disponível."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            status="available"
        )
        assert inst.is_available is True
        assert inst.is_creating is False

    def test_instance_creating(self):
        """Testa instância sendo criada."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            status="creating"
        )
        assert inst.is_creating is True

    def test_instance_deleting(self):
        """Testa instância sendo deletada."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            status="deleting"
        )
        assert inst.is_deleting is True

    def test_instance_modifying(self):
        """Testa instância sendo modificada."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            status="modifying"
        )
        assert inst.is_modifying is True

    def test_instance_multi_az(self):
        """Testa instância Multi-AZ."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            multi_az=True
        )
        assert inst.is_multi_az is True

    def test_instance_publicly_accessible(self):
        """Testa instância publicamente acessível."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            publicly_accessible=True
        )
        assert inst.is_publicly_accessible is True

    def test_instance_encrypted(self):
        """Testa instância com criptografia."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            kms_key_id="arn:aws:kms:..."
        )
        assert inst.has_encryption is True

    def test_instance_size(self):
        """Testa tamanho da instância."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            replication_instance_class="dms.r5.xlarge"
        )
        assert inst.instance_size == "xlarge"

    def test_instance_cost_estimation(self):
        """Testa estimativa de custo."""
        inst = DMSReplicationInstance(
            replication_instance_identifier="ri-001",
            replication_instance_class="dms.r5.large",
            multi_az=True
        )
        assert inst.estimated_hourly_cost == pytest.approx(0.40)

    def test_instance_to_dict(self):
        """Testa conversão para dicionário."""
        inst = DMSReplicationInstance(replication_instance_identifier="test-ri")
        result = inst.to_dict()
        assert result["replication_instance_identifier"] == "test-ri"


class TestDMSEndpointDataclass:
    """Testes para DMSEndpoint dataclass."""

    def test_endpoint_source(self):
        """Testa endpoint source."""
        ep = DMSEndpoint(
            endpoint_identifier="ep-001",
            endpoint_type="source"
        )
        assert ep.is_source is True
        assert ep.is_target is False

    def test_endpoint_target(self):
        """Testa endpoint target."""
        ep = DMSEndpoint(
            endpoint_identifier="ep-001",
            endpoint_type="target"
        )
        assert ep.is_target is True

    def test_endpoint_active(self):
        """Testa endpoint ativo."""
        ep = DMSEndpoint(
            endpoint_identifier="ep-001",
            status="active"
        )
        assert ep.is_active is True

    def test_endpoint_ssl(self):
        """Testa endpoint com SSL."""
        ep = DMSEndpoint(
            endpoint_identifier="ep-001",
            ssl_mode="require"
        )
        assert ep.has_ssl is True

    def test_endpoint_no_ssl(self):
        """Testa endpoint sem SSL."""
        ep = DMSEndpoint(
            endpoint_identifier="ep-001",
            ssl_mode="none"
        )
        assert ep.has_ssl is False

    def test_endpoint_s3(self):
        """Testa endpoint S3."""
        ep = DMSEndpoint(
            endpoint_identifier="ep-001",
            engine_name="s3"
        )
        assert ep.is_s3 is True

    def test_endpoint_to_dict(self):
        """Testa conversão para dicionário."""
        ep = DMSEndpoint(endpoint_identifier="test-ep")
        result = ep.to_dict()
        assert result["endpoint_identifier"] == "test-ep"


class TestDMSReplicationTaskDataclass:
    """Testes para DMSReplicationTask dataclass."""

    def test_task_running(self):
        """Testa task rodando."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            status="running"
        )
        assert task.is_running is True
        assert task.is_stopped is False

    def test_task_stopped(self):
        """Testa task parada."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            status="stopped"
        )
        assert task.is_stopped is True

    def test_task_starting(self):
        """Testa task iniciando."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            status="starting"
        )
        assert task.is_starting is True

    def test_task_ready(self):
        """Testa task pronta."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            status="ready"
        )
        assert task.is_ready is True

    def test_task_full_load(self):
        """Testa task full-load."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            migration_type="full-load"
        )
        assert task.is_full_load is True
        assert task.is_cdc is False

    def test_task_cdc(self):
        """Testa task CDC."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            migration_type="cdc"
        )
        assert task.is_cdc is True

    def test_task_full_load_and_cdc(self):
        """Testa task full-load e CDC."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            migration_type="full-load-and-cdc"
        )
        assert task.is_full_load_and_cdc is True

    def test_task_stop_reason(self):
        """Testa razão de parada."""
        task = DMSReplicationTask(
            replication_task_identifier="task-001",
            stop_reason="Error"
        )
        assert task.has_stop_reason is True

    def test_task_to_dict(self):
        """Testa conversão para dicionário."""
        task = DMSReplicationTask(replication_task_identifier="test-task")
        result = task.to_dict()
        assert result["replication_task_identifier"] == "test-task"


class TestDMSService:
    """Testes para DMSService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = DMSService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_replication_instances.return_value = {"ReplicationInstances": []}
        mock_factory.get_client.return_value = mock_client

        service = DMSService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = DMSService(mock_factory)
        
        result = service.get_resources()
        
        assert "replication_instances" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = DMSService(mock_factory)
        
        result = service.get_metrics()
        
        assert "replication_instances_count" in result


class TestMGNSourceServerDataclass:
    """Testes para MGNSourceServer dataclass."""

    def test_server_ready_for_test(self):
        """Testa servidor pronto para teste."""
        server = MGNSourceServer(
            source_server_id="s-001",
            life_cycle={"state": "READY_FOR_TEST"}
        )
        assert server.is_ready_for_test is True
        assert server.is_ready_for_cutover is False

    def test_server_ready_for_cutover(self):
        """Testa servidor pronto para cutover."""
        server = MGNSourceServer(
            source_server_id="s-001",
            life_cycle={"state": "READY_FOR_CUTOVER"}
        )
        assert server.is_ready_for_cutover is True

    def test_server_cutover(self):
        """Testa servidor com cutover."""
        server = MGNSourceServer(
            source_server_id="s-001",
            life_cycle={"state": "CUTOVER"}
        )
        assert server.is_cutover is True

    def test_server_disconnected(self):
        """Testa servidor desconectado."""
        server = MGNSourceServer(
            source_server_id="s-001",
            life_cycle={"state": "DISCONNECTED"}
        )
        assert server.is_disconnected is True

    def test_server_not_ready(self):
        """Testa servidor não pronto."""
        server = MGNSourceServer(
            source_server_id="s-001",
            life_cycle={"state": "NOT_READY"}
        )
        assert server.is_not_ready is True

    def test_server_launched_instance(self):
        """Testa servidor com instância lançada."""
        server = MGNSourceServer(
            source_server_id="s-001",
            launched_instance={"ec2InstanceID": "i-123"}
        )
        assert server.has_launched_instance is True
        assert server.launched_instance_id == "i-123"

    def test_server_agent_based(self):
        """Testa servidor baseado em agente."""
        server = MGNSourceServer(
            source_server_id="s-001",
            replication_type="AGENT_BASED"
        )
        assert server.is_agent_based is True

    def test_server_replicating(self):
        """Testa servidor replicando."""
        server = MGNSourceServer(
            source_server_id="s-001",
            data_replication_info={"dataReplicationState": "CONTINUOUS"}
        )
        assert server.is_replicating is True

    def test_server_initial_sync(self):
        """Testa servidor em sync inicial."""
        server = MGNSourceServer(
            source_server_id="s-001",
            data_replication_info={"dataReplicationState": "INITIAL_SYNC"}
        )
        assert server.is_initial_sync is True

    def test_server_to_dict(self):
        """Testa conversão para dicionário."""
        server = MGNSourceServer(source_server_id="test-server")
        result = server.to_dict()
        assert result["source_server_id"] == "test-server"


class TestMGNJobDataclass:
    """Testes para MGNJob dataclass."""

    def test_job_pending(self):
        """Testa job pendente."""
        job = MGNJob(
            job_id="job-001",
            status="PENDING"
        )
        assert job.is_pending is True
        assert job.is_completed is False

    def test_job_started(self):
        """Testa job iniciado."""
        job = MGNJob(
            job_id="job-001",
            status="STARTED"
        )
        assert job.is_started is True

    def test_job_completed(self):
        """Testa job completado."""
        job = MGNJob(
            job_id="job-001",
            status="COMPLETED"
        )
        assert job.is_completed is True

    def test_job_launch(self):
        """Testa job de lançamento."""
        job = MGNJob(
            job_id="job-001",
            job_type="LAUNCH"
        )
        assert job.is_launch_job is True

    def test_job_terminate(self):
        """Testa job de terminação."""
        job = MGNJob(
            job_id="job-001",
            job_type="TERMINATE"
        )
        assert job.is_terminate_job is True

    def test_job_test(self):
        """Testa job de teste."""
        job = MGNJob(
            job_id="job-001",
            initiated_by="START_TEST"
        )
        assert job.is_test is True

    def test_job_cutover(self):
        """Testa job de cutover."""
        job = MGNJob(
            job_id="job-001",
            initiated_by="START_CUTOVER"
        )
        assert job.is_cutover is True

    def test_job_servers_count(self):
        """Testa contagem de servidores."""
        job = MGNJob(
            job_id="job-001",
            participating_servers=[{"serverId": "s1"}, {"serverId": "s2"}]
        )
        assert job.servers_count == 2

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = MGNJob(job_id="test-job")
        result = job.to_dict()
        assert result["job_id"] == "test-job"


class TestMGNLaunchConfigurationDataclass:
    """Testes para MGNLaunchConfiguration dataclass."""

    def test_config_legacy_bios(self):
        """Testa config BIOS legacy."""
        config = MGNLaunchConfiguration(
            source_server_id="s-001",
            boot_mode="LEGACY_BIOS"
        )
        assert config.uses_legacy_bios is True
        assert config.uses_uefi is False

    def test_config_uefi(self):
        """Testa config UEFI."""
        config = MGNLaunchConfiguration(
            source_server_id="s-001",
            boot_mode="UEFI"
        )
        assert config.uses_uefi is True

    def test_config_launches_stopped(self):
        """Testa config que lança parado."""
        config = MGNLaunchConfiguration(
            source_server_id="s-001",
            launch_disposition="STOPPED"
        )
        assert config.launches_stopped is True

    def test_config_launches_started(self):
        """Testa config que lança iniciado."""
        config = MGNLaunchConfiguration(
            source_server_id="s-001",
            launch_disposition="STARTED"
        )
        assert config.launches_started is True

    def test_config_has_template(self):
        """Testa config com template."""
        config = MGNLaunchConfiguration(
            source_server_id="s-001",
            ec2_launch_template_id="lt-123"
        )
        assert config.has_template is True

    def test_config_uses_right_sizing(self):
        """Testa config com right-sizing."""
        config = MGNLaunchConfiguration(
            source_server_id="s-001",
            target_instance_type_right_sizing_method="BASIC"
        )
        assert config.uses_right_sizing is True

    def test_config_to_dict(self):
        """Testa conversão para dicionário."""
        config = MGNLaunchConfiguration(source_server_id="test-server")
        result = config.to_dict()
        assert result["source_server_id"] == "test-server"


class TestMGNService:
    """Testes para MGNService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = MGNService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_source_servers.return_value = {"items": []}
        mock_factory.get_client.return_value = mock_client

        service = MGNService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = MGNService(mock_factory)
        
        result = service.get_resources()
        
        assert "source_servers" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = MGNService(mock_factory)
        
        result = service.get_metrics()
        
        assert "source_servers_count" in result


class TestSnowballJobDataclass:
    """Testes para SnowballJob dataclass."""

    def test_job_new(self):
        """Testa job novo."""
        job = SnowballJob(
            job_id="job-001",
            job_state="New"
        )
        assert job.is_new is True

    def test_job_preparing_appliance(self):
        """Testa job preparando appliance."""
        job = SnowballJob(
            job_id="job-001",
            job_state="PreparingAppliance"
        )
        assert job.is_preparing_appliance is True

    def test_job_in_transit_to_customer(self):
        """Testa job em trânsito para cliente."""
        job = SnowballJob(
            job_id="job-001",
            job_state="InTransitToCustomer"
        )
        assert job.is_in_transit_to_customer is True

    def test_job_with_customer(self):
        """Testa job com cliente."""
        job = SnowballJob(
            job_id="job-001",
            job_state="WithCustomer"
        )
        assert job.is_with_customer is True

    def test_job_in_transit_to_aws(self):
        """Testa job em trânsito para AWS."""
        job = SnowballJob(
            job_id="job-001",
            job_state="InTransitToAWS"
        )
        assert job.is_in_transit_to_aws is True

    def test_job_complete(self):
        """Testa job completo."""
        job = SnowballJob(
            job_id="job-001",
            job_state="Complete"
        )
        assert job.is_complete is True

    def test_job_cancelled(self):
        """Testa job cancelado."""
        job = SnowballJob(
            job_id="job-001",
            job_state="Cancelled"
        )
        assert job.is_cancelled is True

    def test_job_import(self):
        """Testa job de importação."""
        job = SnowballJob(
            job_id="job-001",
            job_type="IMPORT"
        )
        assert job.is_import_job is True

    def test_job_export(self):
        """Testa job de exportação."""
        job = SnowballJob(
            job_id="job-001",
            job_type="EXPORT"
        )
        assert job.is_export_job is True

    def test_job_local_use(self):
        """Testa job de uso local."""
        job = SnowballJob(
            job_id="job-001",
            job_type="LOCAL_USE"
        )
        assert job.is_local_use is True

    def test_job_snowball_edge(self):
        """Testa job Snowball Edge."""
        job = SnowballJob(
            job_id="job-001",
            snowball_type="EDGE_STORAGE_OPTIMIZED"
        )
        assert job.is_snowball_edge is True

    def test_job_snowcone(self):
        """Testa job Snowcone."""
        job = SnowballJob(
            job_id="job-001",
            snowball_type="SNC1_HDD"
        )
        assert job.is_snowcone is True

    def test_job_capacity(self):
        """Testa capacidade."""
        job = SnowballJob(
            job_id="job-001",
            snowball_capacity_preference="T80"
        )
        assert job.capacity_tb == 80

    def test_job_encrypted(self):
        """Testa job criptografado."""
        job = SnowballJob(
            job_id="job-001",
            kms_key_arn="arn:aws:kms:..."
        )
        assert job.has_encryption is True

    def test_job_cluster(self):
        """Testa job de cluster."""
        job = SnowballJob(
            job_id="job-001",
            cluster_id="cluster-001"
        )
        assert job.is_cluster_job is True

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = SnowballJob(job_id="test-job")
        result = job.to_dict()
        assert result["job_id"] == "test-job"


class TestSnowballClusterDataclass:
    """Testes para SnowballCluster dataclass."""

    def test_cluster_awaiting_quorum(self):
        """Testa cluster aguardando quórum."""
        cluster = SnowballCluster(
            cluster_id="cluster-001",
            cluster_state="AwaitingQuorum"
        )
        assert cluster.is_awaiting_quorum is True

    def test_cluster_pending(self):
        """Testa cluster pendente."""
        cluster = SnowballCluster(
            cluster_id="cluster-001",
            cluster_state="Pending"
        )
        assert cluster.is_pending is True

    def test_cluster_in_use(self):
        """Testa cluster em uso."""
        cluster = SnowballCluster(
            cluster_id="cluster-001",
            cluster_state="InUse"
        )
        assert cluster.is_in_use is True

    def test_cluster_complete(self):
        """Testa cluster completo."""
        cluster = SnowballCluster(
            cluster_id="cluster-001",
            cluster_state="Complete"
        )
        assert cluster.is_complete is True

    def test_cluster_cancelled(self):
        """Testa cluster cancelado."""
        cluster = SnowballCluster(
            cluster_id="cluster-001",
            cluster_state="Cancelled"
        )
        assert cluster.is_cancelled is True

    def test_cluster_encrypted(self):
        """Testa cluster criptografado."""
        cluster = SnowballCluster(
            cluster_id="cluster-001",
            kms_key_arn="arn:aws:kms:..."
        )
        assert cluster.has_encryption is True

    def test_cluster_to_dict(self):
        """Testa conversão para dicionário."""
        cluster = SnowballCluster(cluster_id="test-cluster")
        result = cluster.to_dict()
        assert result["cluster_id"] == "test-cluster"


class TestSnowFamilyService:
    """Testes para SnowFamilyService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = SnowFamilyService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_jobs.return_value = {"JobListEntries": []}
        mock_factory.get_client.return_value = mock_client

        service = SnowFamilyService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = SnowFamilyService(mock_factory)
        
        result = service.get_resources()
        
        assert "jobs" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = SnowFamilyService(mock_factory)
        
        result = service.get_metrics()
        
        assert "total_jobs" in result


class TestDataPipelineDataclass:
    """Testes para DataPipeline dataclass."""

    def test_pipeline_pending(self):
        """Testa pipeline pendente."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            state="PENDING"
        )
        assert pipeline.is_pending is True

    def test_pipeline_scheduled(self):
        """Testa pipeline agendado."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            state="SCHEDULED"
        )
        assert pipeline.is_scheduled is True

    def test_pipeline_running(self):
        """Testa pipeline rodando."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            state="RUNNING"
        )
        assert pipeline.is_running is True

    def test_pipeline_finished(self):
        """Testa pipeline finalizado."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            state="FINISHED"
        )
        assert pipeline.is_finished is True

    def test_pipeline_paused(self):
        """Testa pipeline pausado."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            state="PAUSED"
        )
        assert pipeline.is_paused is True

    def test_pipeline_healthy(self):
        """Testa pipeline saudável."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            health_status="HEALTHY"
        )
        assert pipeline.is_healthy is True

    def test_pipeline_error(self):
        """Testa pipeline com erro."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            health_status="ERROR"
        )
        assert pipeline.is_error is True

    def test_pipeline_tags(self):
        """Testa pipeline com tags."""
        pipeline = DataPipeline(
            pipeline_id="pl-001",
            tags=[{"key": "env", "value": "prod"}]
        )
        assert pipeline.has_tags is True

    def test_pipeline_to_dict(self):
        """Testa conversão para dicionário."""
        pipeline = DataPipeline(pipeline_id="test-pipeline")
        result = pipeline.to_dict()
        assert result["pipeline_id"] == "test-pipeline"


class TestDataPipelineObjectDataclass:
    """Testes para DataPipelineObject dataclass."""

    def test_object_activity(self):
        """Testa objeto de atividade."""
        obj = DataPipelineObject(
            object_id="obj-001",
            fields=[{"key": "type", "stringValue": "CopyActivity"}]
        )
        assert obj.is_activity is True

    def test_object_data_node(self):
        """Testa objeto de data node."""
        obj = DataPipelineObject(
            object_id="obj-001",
            fields=[{"key": "type", "stringValue": "S3DataNode"}]
        )
        assert obj.is_data_node is True

    def test_object_schedule(self):
        """Testa objeto de schedule."""
        obj = DataPipelineObject(
            object_id="obj-001",
            fields=[{"key": "type", "stringValue": "Schedule"}]
        )
        assert obj.is_schedule is True

    def test_object_resource(self):
        """Testa objeto de resource."""
        obj = DataPipelineObject(
            object_id="obj-001",
            fields=[{"key": "type", "stringValue": "Ec2Resource"}]
        )
        assert obj.is_resource is True

    def test_object_to_dict(self):
        """Testa conversão para dicionário."""
        obj = DataPipelineObject(object_id="test-obj")
        result = obj.to_dict()
        assert result["object_id"] == "test-obj"


class TestDataPipelineTaskRunDataclass:
    """Testes para DataPipelineTaskRun dataclass."""

    def test_task_waiting(self):
        """Testa task aguardando."""
        task = DataPipelineTaskRun(
            task_id="task-001",
            task_status="WAITING_ON_DEPENDENCIES"
        )
        assert task.is_waiting is True

    def test_task_running(self):
        """Testa task rodando."""
        task = DataPipelineTaskRun(
            task_id="task-001",
            task_status="RUNNING"
        )
        assert task.is_running is True

    def test_task_finished(self):
        """Testa task finalizada."""
        task = DataPipelineTaskRun(
            task_id="task-001",
            task_status="FINISHED"
        )
        assert task.is_finished is True

    def test_task_failed(self):
        """Testa task com falha."""
        task = DataPipelineTaskRun(
            task_id="task-001",
            task_status="FAILED"
        )
        assert task.is_failed is True

    def test_task_cancelled(self):
        """Testa task cancelada."""
        task = DataPipelineTaskRun(
            task_id="task-001",
            task_status="CANCELLED"
        )
        assert task.is_cancelled is True

    def test_task_cascade_failed(self):
        """Testa task com falha em cascata."""
        task = DataPipelineTaskRun(
            task_id="task-001",
            task_status="CASCADE_FAILED"
        )
        assert task.is_cascade_failed is True

    def test_task_to_dict(self):
        """Testa conversão para dicionário."""
        task = DataPipelineTaskRun(task_id="test-task")
        result = task.to_dict()
        assert result["task_id"] == "test-task"


class TestDataPipelineService:
    """Testes para DataPipelineService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = DataPipelineService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_pipelines.return_value = {"pipelineIdList": []}
        mock_factory.get_client.return_value = mock_client

        service = DataPipelineService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = DataPipelineService(mock_factory)
        
        result = service.get_resources()
        
        assert "pipelines" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = DataPipelineService(mock_factory)
        
        result = service.get_metrics()
        
        assert "pipelines_count" in result


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_dms_service(self):
        """Testa obtenção do DMSService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_dms_service()
        
        assert isinstance(service, DMSService)

    def test_factory_get_mgn_service(self):
        """Testa obtenção do MGNService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_mgn_service()
        
        assert isinstance(service, MGNService)

    def test_factory_get_snowfamily_service(self):
        """Testa obtenção do SnowFamilyService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_snowfamily_service()
        
        assert isinstance(service, SnowFamilyService)

    def test_factory_get_datapipeline_service(self):
        """Testa obtenção do DataPipelineService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_datapipeline_service()
        
        assert isinstance(service, DataPipelineService)

    def test_factory_get_all_services_includes_migration(self):
        """Testa que get_all_services inclui serviços de migração."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'dms' in services
        assert 'mgn' in services
        assert 'snowfamily' in services
        assert 'datapipeline' in services
