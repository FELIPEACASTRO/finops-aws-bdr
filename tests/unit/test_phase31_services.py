"""
Testes Unitários - FASE 3.1: Analytics Services

Cobertura de testes para:
- AthenaService: Workgroups, catálogos, prepared statements
- QuickSightService: Dashboards, datasets, analyses, users
- DataSyncService: Tasks, locations, agents, executions
- LakeFormationService: Databases, tables, tags, permissions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.finops_aws.services.athena_service import (
    AthenaService,
    AthenaWorkgroup,
    AthenaDataCatalog,
    AthenaPreparedStatement,
    AthenaQueryExecution
)
from src.finops_aws.services.quicksight_service import (
    QuickSightService,
    QuickSightDashboard,
    QuickSightDataSet,
    QuickSightAnalysis,
    QuickSightUser
)
from src.finops_aws.services.datasync_service import (
    DataSyncService,
    DataSyncTask,
    DataSyncLocation,
    DataSyncTaskExecution,
    DataSyncAgent
)
from src.finops_aws.services.lakeformation_service import (
    LakeFormationService,
    LakeFormationDatabase,
    LakeFormationTable,
    LakeFormationPermission,
    LFTag,
    DataLakeSettings
)
from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory


class TestAthenaWorkgroupDataclass:
    """Testes para dataclass AthenaWorkgroup."""
    
    def test_athena_workgroup_basic(self):
        """Testa criação básica de AthenaWorkgroup."""
        wg = AthenaWorkgroup(name="primary")
        assert wg.name == "primary"
        assert wg.is_enabled is True
    
    def test_athena_workgroup_disabled(self):
        """Testa workgroup desabilitado."""
        wg = AthenaWorkgroup(name="test", state="DISABLED")
        assert wg.is_enabled is False
    
    def test_athena_workgroup_query_limit(self):
        """Testa limite de query."""
        wg = AthenaWorkgroup(
            name="test",
            bytes_scanned_cutoff_per_query=10737418240  # 10GB
        )
        assert wg.has_query_limit is True
        assert wg.query_limit_gb == 10.0
    
    def test_athena_workgroup_metrics(self):
        """Testa propriedade has_metrics."""
        wg_metrics = AthenaWorkgroup(
            name="test",
            publish_cloudwatch_metrics_enabled=True
        )
        assert wg_metrics.has_metrics is True
    
    def test_athena_workgroup_encryption(self):
        """Testa propriedade has_encryption."""
        wg = AthenaWorkgroup(
            name="test",
            encryption_configuration={"EncryptionOption": "SSE_S3"}
        )
        assert wg.has_encryption is True
    
    def test_athena_workgroup_to_dict(self):
        """Testa conversão para dicionário."""
        wg = AthenaWorkgroup(name="test")
        data = wg.to_dict()
        assert "name" in data
        assert "is_enabled" in data
        assert "has_query_limit" in data


class TestAthenaDataCatalogDataclass:
    """Testes para dataclass AthenaDataCatalog."""
    
    def test_data_catalog_basic(self):
        """Testa criação básica de AthenaDataCatalog."""
        catalog = AthenaDataCatalog(name="AwsDataCatalog")
        assert catalog.name == "AwsDataCatalog"
        assert catalog.is_glue is True
    
    def test_data_catalog_hive(self):
        """Testa catálogo Hive."""
        catalog = AthenaDataCatalog(name="hive-catalog", catalog_type="HIVE")
        assert catalog.is_hive is True
        assert catalog.is_glue is False
    
    def test_data_catalog_lambda(self):
        """Testa catálogo Lambda."""
        catalog = AthenaDataCatalog(name="lambda-catalog", catalog_type="LAMBDA")
        assert catalog.is_lambda is True
    
    def test_data_catalog_to_dict(self):
        """Testa conversão para dicionário."""
        catalog = AthenaDataCatalog(name="test")
        data = catalog.to_dict()
        assert "name" in data
        assert "is_glue" in data


class TestAthenaQueryExecutionDataclass:
    """Testes para dataclass AthenaQueryExecution."""
    
    def test_query_execution_basic(self):
        """Testa criação básica de AthenaQueryExecution."""
        query = AthenaQueryExecution(query_execution_id="test-id")
        assert query.query_execution_id == "test-id"
        assert query.is_succeeded is True
    
    def test_query_execution_failed(self):
        """Testa query falhada."""
        query = AthenaQueryExecution(query_execution_id="test", state="FAILED")
        assert query.is_failed is True
        assert query.is_succeeded is False
    
    def test_query_execution_running(self):
        """Testa query em execução."""
        query = AthenaQueryExecution(query_execution_id="test", state="RUNNING")
        assert query.is_running is True
    
    def test_query_execution_metrics(self):
        """Testa métricas de query."""
        query = AthenaQueryExecution(
            query_execution_id="test",
            data_scanned_bytes=1073741824,  # 1GB
            execution_time_ms=5000
        )
        assert query.data_scanned_gb == 1.0
        assert query.execution_time_seconds == 5.0
    
    def test_query_execution_cost(self):
        """Testa custo estimado."""
        query = AthenaQueryExecution(
            query_execution_id="test",
            data_scanned_bytes=1099511627776  # 1TB
        )
        assert query.estimated_cost == 5.0  # $5/TB
    
    def test_query_execution_to_dict(self):
        """Testa conversão para dicionário."""
        query = AthenaQueryExecution(query_execution_id="test")
        data = query.to_dict()
        assert "is_succeeded" in data
        assert "estimated_cost" in data


class TestAthenaService:
    """Testes para AthenaService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        athena_client = Mock()
        factory.get_client.return_value = athena_client
        return factory
    
    def test_athena_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = AthenaService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_athena_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_work_groups.return_value = {
            'WorkGroups': []
        }
        service = AthenaService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_athena_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'WorkGroups': []}]
        client.get_paginator.return_value = paginator
        
        service = AthenaService(mock_client_factory)
        resources = service.get_resources()
        assert "workgroups" in resources
        assert "data_catalogs" in resources
        assert "summary" in resources
    
    def test_athena_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'WorkGroups': []}]
        client.get_paginator.return_value = paginator
        
        service = AthenaService(mock_client_factory)
        metrics = service.get_metrics()
        assert "workgroups_count" in metrics
        assert "catalog_types" in metrics
    
    def test_athena_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'WorkGroups': []}]
        client.get_paginator.return_value = paginator
        
        service = AthenaService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestQuickSightDashboardDataclass:
    """Testes para dataclass QuickSightDashboard."""
    
    def test_dashboard_basic(self):
        """Testa criação básica de QuickSightDashboard."""
        dashboard = QuickSightDashboard(dashboard_id="test-id", name="Test Dashboard")
        assert dashboard.name == "Test Dashboard"
        assert dashboard.is_published is False
    
    def test_dashboard_published(self):
        """Testa dashboard publicado."""
        dashboard = QuickSightDashboard(
            dashboard_id="test",
            name="Test",
            published_version_number=1
        )
        assert dashboard.is_published is True
    
    def test_dashboard_versions(self):
        """Testa múltiplas versões."""
        dashboard = QuickSightDashboard(
            dashboard_id="test",
            name="Test",
            version_number=5
        )
        assert dashboard.has_multiple_versions is True
    
    def test_dashboard_to_dict(self):
        """Testa conversão para dicionário."""
        dashboard = QuickSightDashboard(dashboard_id="test", name="Test")
        data = dashboard.to_dict()
        assert "is_published" in data
        assert "has_multiple_versions" in data


class TestQuickSightDataSetDataclass:
    """Testes para dataclass QuickSightDataSet."""
    
    def test_dataset_basic(self):
        """Testa criação básica de QuickSightDataSet."""
        dataset = QuickSightDataSet(data_set_id="test-id", name="Test Dataset")
        assert dataset.name == "Test Dataset"
        assert dataset.is_spice is True
    
    def test_dataset_direct_query(self):
        """Testa dataset direct query."""
        dataset = QuickSightDataSet(
            data_set_id="test",
            name="Test",
            import_mode="DIRECT_QUERY"
        )
        assert dataset.is_direct_query is True
        assert dataset.is_spice is False
    
    def test_dataset_spice_capacity(self):
        """Testa capacidade SPICE."""
        dataset = QuickSightDataSet(
            data_set_id="test",
            name="Test",
            consumed_spice_capacity_in_bytes=10737418240  # 10GB
        )
        assert dataset.spice_capacity_gb == 10.0
    
    def test_dataset_spice_cost(self):
        """Testa custo SPICE."""
        dataset = QuickSightDataSet(
            data_set_id="test",
            name="Test",
            consumed_spice_capacity_in_bytes=10737418240  # 10GB
        )
        assert abs(dataset.estimated_spice_cost_monthly - 3.8) < 0.1  # 10 * 0.38
    
    def test_dataset_security(self):
        """Testa propriedades de segurança."""
        dataset = QuickSightDataSet(
            data_set_id="test",
            name="Test",
            row_level_permission_data_set={"Arn": "arn"},
            column_level_permission_rules_applied=True
        )
        assert dataset.has_row_level_security is True
        assert dataset.has_column_level_security is True
    
    def test_dataset_to_dict(self):
        """Testa conversão para dicionário."""
        dataset = QuickSightDataSet(data_set_id="test", name="Test")
        data = dataset.to_dict()
        assert "is_spice" in data
        assert "estimated_spice_cost_monthly" in data


class TestQuickSightUserDataclass:
    """Testes para dataclass QuickSightUser."""
    
    def test_user_basic(self):
        """Testa criação básica de QuickSightUser."""
        user = QuickSightUser(user_name="test-user")
        assert user.user_name == "test-user"
        assert user.is_reader is True
    
    def test_user_roles(self):
        """Testa diferentes roles."""
        admin = QuickSightUser(user_name="admin", role="ADMIN")
        author = QuickSightUser(user_name="author", role="AUTHOR")
        reader = QuickSightUser(user_name="reader", role="READER")
        
        assert admin.is_admin is True
        assert author.is_author is True
        assert reader.is_reader is True
    
    def test_user_cost(self):
        """Testa custo estimado por role."""
        author = QuickSightUser(user_name="author", role="AUTHOR")
        reader = QuickSightUser(user_name="reader", role="READER")
        
        assert author.estimated_monthly_cost == 24.0
        assert reader.estimated_monthly_cost == 0.30
    
    def test_user_to_dict(self):
        """Testa conversão para dicionário."""
        user = QuickSightUser(user_name="test")
        data = user.to_dict()
        assert "is_admin" in data
        assert "estimated_monthly_cost" in data


class TestQuickSightService:
    """Testes para QuickSightService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        quicksight_client = Mock()
        sts_client = Mock()
        sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        
        def get_client_side_effect(service_name):
            if service_name == 'sts':
                return sts_client
            return quicksight_client
        
        factory.get_client.side_effect = get_client_side_effect
        return factory
    
    def test_quicksight_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = QuickSightService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_quicksight_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        qs_client = mock_client_factory.get_client('quicksight')
        paginator = Mock()
        paginator.paginate.return_value = [{'DashboardSummaryList': []}]
        qs_client.get_paginator.return_value = paginator
        
        service = QuickSightService(mock_client_factory)
        resources = service.get_resources()
        assert "dashboards" in resources
        assert "data_sets" in resources
        assert "analyses" in resources
        assert "users" in resources
        assert "summary" in resources
    
    def test_quicksight_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        qs_client = mock_client_factory.get_client('quicksight')
        paginator = Mock()
        paginator.paginate.return_value = [{'DashboardSummaryList': []}]
        qs_client.get_paginator.return_value = paginator
        
        service = QuickSightService(mock_client_factory)
        metrics = service.get_metrics()
        assert "dashboards_count" in metrics
        assert "total_estimated_monthly_cost" in metrics
    
    def test_quicksight_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        qs_client = mock_client_factory.get_client('quicksight')
        paginator = Mock()
        paginator.paginate.return_value = [{'DashboardSummaryList': []}]
        qs_client.get_paginator.return_value = paginator
        
        service = QuickSightService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestDataSyncTaskDataclass:
    """Testes para dataclass DataSyncTask."""
    
    def test_datasync_task_basic(self):
        """Testa criação básica de DataSyncTask."""
        task = DataSyncTask(task_arn="arn:aws:datasync:us-east-1:123:task/task-123")
        assert task.is_available is True
    
    def test_datasync_task_running(self):
        """Testa task em execução."""
        task = DataSyncTask(task_arn="arn", status="RUNNING")
        assert task.is_running is True
        assert task.is_available is False
    
    def test_datasync_task_schedule(self):
        """Testa propriedade has_schedule."""
        task = DataSyncTask(
            task_arn="arn",
            schedule={"ScheduleExpression": "cron(0 12 * * ? *)"}
        )
        assert task.has_schedule is True
    
    def test_datasync_task_logging(self):
        """Testa propriedade has_logging."""
        task = DataSyncTask(
            task_arn="arn",
            cloud_watch_log_group_arn="arn:aws:logs:us-east-1:123:log-group:test"
        )
        assert task.has_logging is True
    
    def test_datasync_task_error(self):
        """Testa propriedade has_error."""
        task = DataSyncTask(task_arn="arn", error_code="InvalidRequest")
        assert task.has_error is True
    
    def test_datasync_task_to_dict(self):
        """Testa conversão para dicionário."""
        task = DataSyncTask(task_arn="arn", name="test-task")
        data = task.to_dict()
        assert "is_available" in data
        assert "has_schedule" in data


class TestDataSyncLocationDataclass:
    """Testes para dataclass DataSyncLocation."""
    
    def test_location_s3(self):
        """Testa localização S3."""
        location = DataSyncLocation(
            location_arn="arn",
            location_uri="s3://my-bucket/prefix/",
            location_type="S3"
        )
        assert location.is_s3 is True
    
    def test_location_efs(self):
        """Testa localização EFS."""
        location = DataSyncLocation(
            location_arn="arn",
            location_uri="efs://fs-123/",
            location_type="EFS"
        )
        assert location.is_efs is True
    
    def test_location_nfs(self):
        """Testa localização NFS."""
        location = DataSyncLocation(
            location_arn="arn",
            location_uri="nfs://server/path",
            location_type="NFS"
        )
        assert location.is_nfs is True
    
    def test_location_to_dict(self):
        """Testa conversão para dicionário."""
        location = DataSyncLocation(location_arn="arn", location_uri="s3://bucket/")
        data = location.to_dict()
        assert "is_s3" in data
        assert "is_efs" in data


class TestDataSyncAgentDataclass:
    """Testes para dataclass DataSyncAgent."""
    
    def test_agent_basic(self):
        """Testa criação básica de DataSyncAgent."""
        agent = DataSyncAgent(agent_arn="arn", name="my-agent")
        assert agent.name == "my-agent"
        assert agent.is_online is True
    
    def test_agent_offline(self):
        """Testa agente offline."""
        agent = DataSyncAgent(agent_arn="arn", status="OFFLINE")
        assert agent.is_offline is True
        assert agent.is_online is False
    
    def test_agent_private_link(self):
        """Testa agente com PrivateLink."""
        agent = DataSyncAgent(
            agent_arn="arn",
            endpoint_type="PRIVATE_LINK"
        )
        assert agent.uses_private_link is True
        assert agent.is_public is False
    
    def test_agent_to_dict(self):
        """Testa conversão para dicionário."""
        agent = DataSyncAgent(agent_arn="arn", name="test")
        data = agent.to_dict()
        assert "is_online" in data
        assert "uses_private_link" in data


class TestDataSyncTaskExecutionDataclass:
    """Testes para dataclass DataSyncTaskExecution."""
    
    def test_execution_basic(self):
        """Testa criação básica de DataSyncTaskExecution."""
        execution = DataSyncTaskExecution(task_execution_arn="arn")
        assert execution.is_success is True
    
    def test_execution_error(self):
        """Testa execução com erro."""
        execution = DataSyncTaskExecution(task_execution_arn="arn", status="ERROR")
        assert execution.is_error is True
    
    def test_execution_metrics(self):
        """Testa métricas de execução."""
        execution = DataSyncTaskExecution(
            task_execution_arn="arn",
            bytes_transferred=10737418240  # 10GB
        )
        assert execution.bytes_transferred_gb == 10.0
    
    def test_execution_cost(self):
        """Testa custo estimado."""
        execution = DataSyncTaskExecution(
            task_execution_arn="arn",
            bytes_transferred=107374182400  # 100GB
        )
        assert abs(execution.estimated_cost - 1.25) < 0.01  # 100 * 0.0125
    
    def test_execution_progress(self):
        """Testa progresso."""
        execution = DataSyncTaskExecution(
            task_execution_arn="arn",
            bytes_transferred=500,
            estimated_bytes_to_transfer=1000,
            status="TRANSFERRING"
        )
        assert execution.progress_percent == 50.0
    
    def test_execution_to_dict(self):
        """Testa conversão para dicionário."""
        execution = DataSyncTaskExecution(task_execution_arn="arn")
        data = execution.to_dict()
        assert "is_success" in data
        assert "estimated_cost" in data


class TestDataSyncService:
    """Testes para DataSyncService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        datasync_client = Mock()
        factory.get_client.return_value = datasync_client
        return factory
    
    def test_datasync_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = DataSyncService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_datasync_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_tasks.return_value = {
            'Tasks': []
        }
        service = DataSyncService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_datasync_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Tasks': []}]
        client.get_paginator.return_value = paginator
        
        service = DataSyncService(mock_client_factory)
        resources = service.get_resources()
        assert "tasks" in resources
        assert "locations" in resources
        assert "agents" in resources
        assert "summary" in resources
    
    def test_datasync_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Tasks': []}]
        client.get_paginator.return_value = paginator
        
        service = DataSyncService(mock_client_factory)
        metrics = service.get_metrics()
        assert "tasks_count" in metrics
        assert "location_types" in metrics
    
    def test_datasync_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Tasks': []}]
        client.get_paginator.return_value = paginator
        
        service = DataSyncService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestLakeFormationDatabaseDataclass:
    """Testes para dataclass LakeFormationDatabase."""
    
    def test_database_basic(self):
        """Testa criação básica de LakeFormationDatabase."""
        db = LakeFormationDatabase(name="my_database")
        assert db.name == "my_database"
        assert db.has_location is False
    
    def test_database_with_location(self):
        """Testa database com localização."""
        db = LakeFormationDatabase(
            name="test",
            location_uri="s3://my-bucket/data/"
        )
        assert db.has_location is True
        assert db.is_s3_location is True
    
    def test_database_permissions(self):
        """Testa permissões padrão."""
        db = LakeFormationDatabase(
            name="test",
            create_table_default_permissions=[{"Principal": {"IAMAllowedPrincipals": {}}}]
        )
        assert db.has_default_permissions is True
    
    def test_database_to_dict(self):
        """Testa conversão para dicionário."""
        db = LakeFormationDatabase(name="test")
        data = db.to_dict()
        assert "has_location" in data
        assert "is_s3_location" in data


class TestLakeFormationTableDataclass:
    """Testes para dataclass LakeFormationTable."""
    
    def test_table_basic(self):
        """Testa criação básica de LakeFormationTable."""
        table = LakeFormationTable(name="my_table", database_name="my_db")
        assert table.name == "my_table"
        assert table.is_external is True
    
    def test_table_governed(self):
        """Testa tabela governada."""
        table = LakeFormationTable(
            name="test",
            database_name="db",
            table_type="GOVERNED"
        )
        assert table.is_governed is True
        assert table.is_external is False
    
    def test_table_partitions(self):
        """Testa partições."""
        table = LakeFormationTable(
            name="test",
            database_name="db",
            partition_keys=[{"Name": "year"}, {"Name": "month"}]
        )
        assert table.has_partitions is True
        assert table.partition_count == 2
    
    def test_table_columns(self):
        """Testa contagem de colunas."""
        table = LakeFormationTable(
            name="test",
            database_name="db",
            storage_descriptor={"Columns": [{"Name": "col1"}, {"Name": "col2"}]}
        )
        assert table.columns_count == 2
    
    def test_table_to_dict(self):
        """Testa conversão para dicionário."""
        table = LakeFormationTable(name="test", database_name="db")
        data = table.to_dict()
        assert "is_external" in data
        assert "has_partitions" in data


class TestLakeFormationPermissionDataclass:
    """Testes para dataclass LakeFormationPermission."""
    
    def test_permission_basic(self):
        """Testa criação básica de LakeFormationPermission."""
        perm = LakeFormationPermission(
            principal={"DataLakePrincipalIdentifier": "arn:aws:iam::123:role/MyRole"},
            resource={"Database": {"Name": "mydb"}},
            permissions=["SELECT"]
        )
        assert perm.principal_type == "IAM_ROLE"
        assert perm.resource_type == "DATABASE"
    
    def test_permission_full_access(self):
        """Testa acesso completo."""
        perm = LakeFormationPermission(
            permissions=["ALL"]
        )
        assert perm.is_full_access is True
    
    def test_permission_grant_option(self):
        """Testa opção de grant."""
        perm = LakeFormationPermission(
            permissions=["SELECT"],
            permissions_with_grant_option=["SELECT"]
        )
        assert perm.has_grant_option is True
    
    def test_permission_to_dict(self):
        """Testa conversão para dicionário."""
        perm = LakeFormationPermission()
        data = perm.to_dict()
        assert "principal_type" in data
        assert "resource_type" in data


class TestLFTagDataclass:
    """Testes para dataclass LFTag."""
    
    def test_lf_tag_basic(self):
        """Testa criação básica de LFTag."""
        tag = LFTag(tag_key="environment", tag_values=["dev", "prod", "test"])
        assert tag.tag_key == "environment"
        assert tag.values_count == 3
    
    def test_lf_tag_to_dict(self):
        """Testa conversão para dicionário."""
        tag = LFTag(tag_key="test", tag_values=["a", "b"])
        data = tag.to_dict()
        assert "tag_key" in data
        assert "values_count" in data


class TestDataLakeSettingsDataclass:
    """Testes para dataclass DataLakeSettings."""
    
    def test_settings_basic(self):
        """Testa criação básica de DataLakeSettings."""
        settings = DataLakeSettings()
        assert settings.admins_count == 0
    
    def test_settings_with_admins(self):
        """Testa settings com admins."""
        settings = DataLakeSettings(
            data_lake_admins=[
                {"DataLakePrincipalIdentifier": "arn:aws:iam::123:role/Admin"}
            ]
        )
        assert settings.admins_count == 1
    
    def test_settings_permissions(self):
        """Testa permissões padrão."""
        settings = DataLakeSettings(
            create_database_default_permissions=[{}],
            create_table_default_permissions=[{}]
        )
        assert settings.has_default_db_permissions is True
        assert settings.has_default_table_permissions is True
    
    def test_settings_external_filtering(self):
        """Testa filtragem externa."""
        settings = DataLakeSettings(allow_external_data_filtering=True)
        assert settings.allows_external_filtering is True
    
    def test_settings_to_dict(self):
        """Testa conversão para dicionário."""
        settings = DataLakeSettings()
        data = settings.to_dict()
        assert "admins_count" in data
        assert "allows_external_filtering" in data


class TestLakeFormationService:
    """Testes para LakeFormationService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        lf_client = Mock()
        glue_client = Mock()
        
        def get_client_side_effect(service_name):
            if service_name == 'glue':
                return glue_client
            return lf_client
        
        factory.get_client.side_effect = get_client_side_effect
        return factory
    
    def test_lakeformation_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = LakeFormationService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_lakeformation_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        lf_client = mock_client_factory.get_client('lakeformation')
        lf_client.get_data_lake_settings.return_value = {
            'DataLakeSettings': {}
        }
        service = LakeFormationService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_lakeformation_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        lf_client = mock_client_factory.get_client('lakeformation')
        glue_client = mock_client_factory.get_client('glue')
        
        lf_client.get_data_lake_settings.return_value = {'DataLakeSettings': {}}
        
        lf_paginator = Mock()
        lf_paginator.paginate.return_value = [{'LFTags': []}]
        lf_client.get_paginator.return_value = lf_paginator
        
        glue_paginator = Mock()
        glue_paginator.paginate.return_value = [{'DatabaseList': []}]
        glue_client.get_paginator.return_value = glue_paginator
        
        service = LakeFormationService(mock_client_factory)
        resources = service.get_resources()
        assert "databases" in resources
        assert "tables" in resources
        assert "lf_tags" in resources
        assert "summary" in resources
    
    def test_lakeformation_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        lf_client = mock_client_factory.get_client('lakeformation')
        glue_client = mock_client_factory.get_client('glue')
        
        lf_client.get_data_lake_settings.return_value = {'DataLakeSettings': {}}
        
        lf_paginator = Mock()
        lf_paginator.paginate.return_value = [{'LFTags': []}]
        lf_client.get_paginator.return_value = lf_paginator
        
        glue_paginator = Mock()
        glue_paginator.paginate.return_value = [{'DatabaseList': []}]
        glue_client.get_paginator.return_value = glue_paginator
        
        service = LakeFormationService(mock_client_factory)
        metrics = service.get_metrics()
        assert "databases_count" in metrics
        assert "permission_types" in metrics
    
    def test_lakeformation_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        lf_client = mock_client_factory.get_client('lakeformation')
        glue_client = mock_client_factory.get_client('glue')
        
        lf_client.get_data_lake_settings.return_value = {'DataLakeSettings': {}}
        
        lf_paginator = Mock()
        lf_paginator.paginate.return_value = [{'LFTags': []}]
        lf_client.get_paginator.return_value = lf_paginator
        
        glue_paginator = Mock()
        glue_paginator.paginate.return_value = [{'DatabaseList': []}]
        glue_client.get_paginator.return_value = glue_paginator
        
        service = LakeFormationService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""
    
    def test_service_factory_get_athena_service(self):
        """Testa obtenção do AthenaService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_athena = Mock()
        factory.register_mock('athena', mock_athena)
        
        service = factory.get_athena_service()
        assert service == mock_athena
    
    def test_service_factory_get_quicksight_service(self):
        """Testa obtenção do QuickSightService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_quicksight = Mock()
        factory.register_mock('quicksight', mock_quicksight)
        
        service = factory.get_quicksight_service()
        assert service == mock_quicksight
    
    def test_service_factory_get_datasync_service(self):
        """Testa obtenção do DataSyncService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_datasync = Mock()
        factory.register_mock('datasync', mock_datasync)
        
        service = factory.get_datasync_service()
        assert service == mock_datasync
    
    def test_service_factory_get_lakeformation_service(self):
        """Testa obtenção do LakeFormationService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_lakeformation = Mock()
        factory.register_mock('lakeformation', mock_lakeformation)
        
        service = factory.get_lakeformation_service()
        assert service == mock_lakeformation
    
    def test_service_factory_get_all_services_includes_analytics(self):
        """Testa que get_all_services inclui serviços Analytics."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        
        factory.register_mock('athena', Mock())
        factory.register_mock('quicksight', Mock())
        factory.register_mock('datasync', Mock())
        factory.register_mock('lakeformation', Mock())
        factory.register_mock('cost', Mock())
        factory.register_mock('metrics', Mock())
        factory.register_mock('optimizer', Mock())
        
        all_services = factory.get_all_services()
        assert 'athena' in all_services
        assert 'quicksight' in all_services
        assert 'datasync' in all_services
        assert 'lakeformation' in all_services
