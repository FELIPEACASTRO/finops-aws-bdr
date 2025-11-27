"""
Testes unitários para FASE 4.0 - Developer Tools & Application Integration.

X-Ray, CloudFormation, SSM, AppConfig, SQS.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.xray_service import (
    XRayService, XRayGroup, XRaySamplingRule, XRayEncryptionConfig
)
from src.finops_aws.services.cloudformation_service import (
    CloudFormationService, CloudFormationStack, CloudFormationStackSet, CloudFormationChangeSet
)
from src.finops_aws.services.ssm_service import (
    SSMService, SSMParameter, SSMDocument, SSMManagedInstance
)
from src.finops_aws.services.appconfig_service import (
    AppConfigService, AppConfigApplication, AppConfigEnvironment, 
    AppConfigProfile, AppConfigDeploymentStrategy
)
from src.finops_aws.services.sqs_service import SQSService, SQSQueue
from src.finops_aws.core.factories import ServiceFactory


class TestXRayGroupDataclass:
    """Testes para XRayGroup dataclass."""

    def test_group_with_insights(self):
        """Testa grupo com Insights."""
        group = XRayGroup(
            group_name="test-group",
            insights_configuration={"InsightsEnabled": True}
        )
        assert group.has_insights is True

    def test_group_with_notifications(self):
        """Testa grupo com notificações."""
        group = XRayGroup(
            group_name="test-group",
            insights_configuration={"NotificationsEnabled": True}
        )
        assert group.has_notifications is True

    def test_group_with_filter(self):
        """Testa grupo com filtro."""
        group = XRayGroup(group_name="test-group", filter_expression="service()")
        assert group.has_filter is True

    def test_group_with_tags(self):
        """Testa grupo com tags."""
        group = XRayGroup(group_name="test-group", tags={"env": "prod"})
        assert group.has_tags is True

    def test_group_to_dict(self):
        """Testa conversão para dicionário."""
        group = XRayGroup(group_name="test-group")
        result = group.to_dict()
        assert result["group_name"] == "test-group"


class TestXRaySamplingRuleDataclass:
    """Testes para XRaySamplingRule dataclass."""

    def test_rule_default(self):
        """Testa regra default."""
        rule = XRaySamplingRule(rule_name="Default")
        assert rule.is_default_rule is True

    def test_rule_low_sampling(self):
        """Testa regra com baixo sampling."""
        rule = XRaySamplingRule(rule_name="test", fixed_rate=0.05)
        assert rule.has_low_sampling is True

    def test_rule_high_sampling(self):
        """Testa regra com alto sampling."""
        rule = XRaySamplingRule(rule_name="test", fixed_rate=0.8)
        assert rule.has_high_sampling is True

    def test_rule_with_reservoir(self):
        """Testa regra com reservoir."""
        rule = XRaySamplingRule(rule_name="test", reservoir_size=10)
        assert rule.has_reservoir is True

    def test_rule_wildcard(self):
        """Testa regra com wildcard."""
        rule = XRaySamplingRule(rule_name="test", service_name="*")
        assert rule.is_wildcard is True

    def test_rule_to_dict(self):
        """Testa conversão para dicionário."""
        rule = XRaySamplingRule(rule_name="test-rule")
        result = rule.to_dict()
        assert result["rule_name"] == "test-rule"


class TestXRayEncryptionConfigDataclass:
    """Testes para XRayEncryptionConfig dataclass."""

    def test_encryption_active(self):
        """Testa criptografia ativa."""
        config = XRayEncryptionConfig(status="ACTIVE")
        assert config.is_active is True

    def test_encryption_updating(self):
        """Testa criptografia atualizando."""
        config = XRayEncryptionConfig(status="UPDATING")
        assert config.is_updating is True

    def test_encryption_kms(self):
        """Testa criptografia KMS."""
        config = XRayEncryptionConfig(type="KMS", key_id="arn:...")
        assert config.uses_kms is True

    def test_encryption_default(self):
        """Testa criptografia padrão."""
        config = XRayEncryptionConfig(type="NONE")
        assert config.uses_default is True

    def test_encryption_to_dict(self):
        """Testa conversão para dicionário."""
        config = XRayEncryptionConfig(status="ACTIVE")
        result = config.to_dict()
        assert result["status"] == "ACTIVE"


class TestXRayService:
    """Testes para XRayService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = XRayService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.get_sampling_rules.return_value = {}
        mock_factory.get_client.return_value = mock_client

        service = XRayService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        mock_client.get_encryption_config.return_value = {"EncryptionConfig": {}}
        
        mock_factory.get_client.return_value = mock_client
        service = XRayService(mock_factory)
        
        result = service.get_resources()
        
        assert "groups" in result
        assert "summary" in result


class TestCloudFormationStackDataclass:
    """Testes para CloudFormationStack dataclass."""

    def test_stack_complete(self):
        """Testa stack completa."""
        stack = CloudFormationStack(stack_name="test", stack_status="CREATE_COMPLETE")
        assert stack.is_complete is True

    def test_stack_in_progress(self):
        """Testa stack em progresso."""
        stack = CloudFormationStack(stack_name="test", stack_status="CREATE_IN_PROGRESS")
        assert stack.is_in_progress is True

    def test_stack_failed(self):
        """Testa stack com falha."""
        stack = CloudFormationStack(stack_name="test", stack_status="CREATE_FAILED")
        assert stack.is_failed is True

    def test_stack_deleted(self):
        """Testa stack deletada."""
        stack = CloudFormationStack(stack_name="test", stack_status="DELETE_COMPLETE")
        assert stack.is_deleted is True

    def test_stack_drift(self):
        """Testa stack com drift."""
        stack = CloudFormationStack(
            stack_name="test",
            drift_information={"StackDriftStatus": "DRIFTED"}
        )
        assert stack.has_drift is True

    def test_stack_protection(self):
        """Testa stack com proteção."""
        stack = CloudFormationStack(stack_name="test", enable_termination_protection=True)
        assert stack.has_termination_protection is True

    def test_stack_iam_capability(self):
        """Testa stack com IAM capability."""
        stack = CloudFormationStack(stack_name="test", capabilities=["CAPABILITY_IAM"])
        assert stack.has_iam_capability is True

    def test_stack_to_dict(self):
        """Testa conversão para dicionário."""
        stack = CloudFormationStack(stack_name="test-stack")
        result = stack.to_dict()
        assert result["stack_name"] == "test-stack"


class TestCloudFormationStackSetDataclass:
    """Testes para CloudFormationStackSet dataclass."""

    def test_stackset_active(self):
        """Testa StackSet ativo."""
        ss = CloudFormationStackSet(stack_set_name="test", status="ACTIVE")
        assert ss.is_active is True

    def test_stackset_deleted(self):
        """Testa StackSet deletado."""
        ss = CloudFormationStackSet(stack_set_name="test", status="DELETED")
        assert ss.is_deleted is True

    def test_stackset_self_managed(self):
        """Testa StackSet self-managed."""
        ss = CloudFormationStackSet(stack_set_name="test", permission_model="SELF_MANAGED")
        assert ss.uses_self_managed is True

    def test_stackset_service_managed(self):
        """Testa StackSet service-managed."""
        ss = CloudFormationStackSet(stack_set_name="test", permission_model="SERVICE_MANAGED")
        assert ss.uses_service_managed is True

    def test_stackset_auto_deployment(self):
        """Testa StackSet com auto deployment."""
        ss = CloudFormationStackSet(stack_set_name="test", auto_deployment={"Enabled": True})
        assert ss.has_auto_deployment is True

    def test_stackset_multi_region(self):
        """Testa StackSet multi-região."""
        ss = CloudFormationStackSet(stack_set_name="test", regions=["us-east-1", "eu-west-1"])
        assert ss.is_multi_region is True

    def test_stackset_to_dict(self):
        """Testa conversão para dicionário."""
        ss = CloudFormationStackSet(stack_set_name="test-ss")
        result = ss.to_dict()
        assert result["stack_set_name"] == "test-ss"


class TestCloudFormationChangeSetDataclass:
    """Testes para CloudFormationChangeSet dataclass."""

    def test_changeset_available(self):
        """Testa ChangeSet disponível."""
        cs = CloudFormationChangeSet(change_set_name="test", status="CREATE_COMPLETE")
        assert cs.is_available is True

    def test_changeset_pending(self):
        """Testa ChangeSet pendente."""
        cs = CloudFormationChangeSet(change_set_name="test", status="CREATE_PENDING")
        assert cs.is_pending is True

    def test_changeset_failed(self):
        """Testa ChangeSet com falha."""
        cs = CloudFormationChangeSet(change_set_name="test", status="FAILED")
        assert cs.is_failed is True

    def test_changeset_executable(self):
        """Testa ChangeSet executável."""
        cs = CloudFormationChangeSet(change_set_name="test", execution_status="AVAILABLE")
        assert cs.is_executable is True

    def test_changeset_with_changes(self):
        """Testa ChangeSet com mudanças."""
        cs = CloudFormationChangeSet(change_set_name="test", changes=[{"Type": "Resource"}])
        assert cs.has_changes is True
        assert cs.changes_count == 1

    def test_changeset_to_dict(self):
        """Testa conversão para dicionário."""
        cs = CloudFormationChangeSet(change_set_name="test-cs")
        result = cs.to_dict()
        assert result["change_set_name"] == "test-cs"


class TestCloudFormationService:
    """Testes para CloudFormationService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = CloudFormationService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_stacks.return_value = {"StackSummaries": []}
        mock_factory.get_client.return_value = mock_client

        service = CloudFormationService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestSSMParameterDataclass:
    """Testes para SSMParameter dataclass."""

    def test_param_secure_string(self):
        """Testa parâmetro SecureString."""
        param = SSMParameter(name="test", type="SecureString")
        assert param.is_secure_string is True

    def test_param_string(self):
        """Testa parâmetro String."""
        param = SSMParameter(name="test", type="String")
        assert param.is_string is True

    def test_param_string_list(self):
        """Testa parâmetro StringList."""
        param = SSMParameter(name="test", type="StringList")
        assert param.is_string_list is True

    def test_param_advanced(self):
        """Testa parâmetro Advanced."""
        param = SSMParameter(name="test", tier="Advanced")
        assert param.is_advanced is True
        assert param.monthly_cost == pytest.approx(0.05)

    def test_param_standard(self):
        """Testa parâmetro Standard."""
        param = SSMParameter(name="test", tier="Standard")
        assert param.is_standard is True
        assert param.monthly_cost == pytest.approx(0.0)

    def test_param_intelligent_tiering(self):
        """Testa parâmetro Intelligent-Tiering."""
        param = SSMParameter(name="test", tier="Intelligent-Tiering")
        assert param.is_intelligent_tiering is True

    def test_param_with_kms(self):
        """Testa parâmetro com KMS."""
        param = SSMParameter(name="test", key_id="arn:...")
        assert param.has_kms is True

    def test_param_to_dict(self):
        """Testa conversão para dicionário."""
        param = SSMParameter(name="test-param")
        result = param.to_dict()
        assert result["name"] == "test-param"


class TestSSMDocumentDataclass:
    """Testes para SSMDocument dataclass."""

    def test_doc_active(self):
        """Testa documento ativo."""
        doc = SSMDocument(name="test", status="Active")
        assert doc.is_active is True

    def test_doc_creating(self):
        """Testa documento criando."""
        doc = SSMDocument(name="test", status="Creating")
        assert doc.is_creating is True

    def test_doc_command(self):
        """Testa documento Command."""
        doc = SSMDocument(name="test", document_type="Command")
        assert doc.is_command is True

    def test_doc_automation(self):
        """Testa documento Automation."""
        doc = SSMDocument(name="test", document_type="Automation")
        assert doc.is_automation is True

    def test_doc_policy(self):
        """Testa documento Policy."""
        doc = SSMDocument(name="test", document_type="Policy")
        assert doc.is_policy is True

    def test_doc_session(self):
        """Testa documento Session."""
        doc = SSMDocument(name="test", document_type="Session")
        assert doc.is_session is True

    def test_doc_linux(self):
        """Testa documento Linux."""
        doc = SSMDocument(name="test", platform_types=["Linux"])
        assert doc.supports_linux is True

    def test_doc_windows(self):
        """Testa documento Windows."""
        doc = SSMDocument(name="test", platform_types=["Windows"])
        assert doc.supports_windows is True

    def test_doc_to_dict(self):
        """Testa conversão para dicionário."""
        doc = SSMDocument(name="test-doc")
        result = doc.to_dict()
        assert result["name"] == "test-doc"


class TestSSMManagedInstanceDataclass:
    """Testes para SSMManagedInstance dataclass."""

    def test_instance_online(self):
        """Testa instância online."""
        inst = SSMManagedInstance(instance_id="i-123", ping_status="Online")
        assert inst.is_online is True

    def test_instance_connection_lost(self):
        """Testa instância com conexão perdida."""
        inst = SSMManagedInstance(instance_id="i-123", ping_status="ConnectionLost")
        assert inst.is_connection_lost is True

    def test_instance_inactive(self):
        """Testa instância inativa."""
        inst = SSMManagedInstance(instance_id="i-123", ping_status="Inactive")
        assert inst.is_inactive is True

    def test_instance_ec2(self):
        """Testa instância EC2."""
        inst = SSMManagedInstance(instance_id="i-123", resource_type="EC2Instance")
        assert inst.is_ec2 is True

    def test_instance_managed(self):
        """Testa managed instance."""
        inst = SSMManagedInstance(instance_id="mi-123", resource_type="ManagedInstance")
        assert inst.is_managed_instance is True

    def test_instance_linux(self):
        """Testa instância Linux."""
        inst = SSMManagedInstance(instance_id="i-123", platform_type="Linux")
        assert inst.is_linux is True

    def test_instance_windows(self):
        """Testa instância Windows."""
        inst = SSMManagedInstance(instance_id="i-123", platform_type="Windows")
        assert inst.is_windows is True

    def test_instance_needs_update(self):
        """Testa instância que precisa atualização."""
        inst = SSMManagedInstance(instance_id="i-123", is_latest_version=False)
        assert inst.needs_update is True

    def test_instance_to_dict(self):
        """Testa conversão para dicionário."""
        inst = SSMManagedInstance(instance_id="i-123")
        result = inst.to_dict()
        assert result["instance_id"] == "i-123"


class TestSSMService:
    """Testes para SSMService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = SSMService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_parameters.return_value = {"Parameters": []}
        mock_factory.get_client.return_value = mock_client

        service = SSMService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestAppConfigApplicationDataclass:
    """Testes para AppConfigApplication dataclass."""

    def test_app_with_description(self):
        """Testa aplicação com descrição."""
        app = AppConfigApplication(name="test", description="Test app")
        assert app.has_description is True

    def test_app_to_dict(self):
        """Testa conversão para dicionário."""
        app = AppConfigApplication(id="app-123", name="test-app")
        result = app.to_dict()
        assert result["id"] == "app-123"


class TestAppConfigEnvironmentDataclass:
    """Testes para AppConfigEnvironment dataclass."""

    def test_env_ready(self):
        """Testa ambiente pronto."""
        env = AppConfigEnvironment(name="test", state="READY_FOR_DEPLOYMENT")
        assert env.is_ready is True

    def test_env_deploying(self):
        """Testa ambiente em deploy."""
        env = AppConfigEnvironment(name="test", state="DEPLOYING")
        assert env.is_deploying is True

    def test_env_rolled_back(self):
        """Testa ambiente rolled back."""
        env = AppConfigEnvironment(name="test", state="ROLLED_BACK")
        assert env.is_rolled_back is True

    def test_env_with_monitors(self):
        """Testa ambiente com monitores."""
        env = AppConfigEnvironment(name="test", monitors=[{"AlarmArn": "arn:..."}])
        assert env.has_monitors is True
        assert env.monitors_count == 1

    def test_env_to_dict(self):
        """Testa conversão para dicionário."""
        env = AppConfigEnvironment(id="env-123", name="test-env")
        result = env.to_dict()
        assert result["id"] == "env-123"


class TestAppConfigProfileDataclass:
    """Testes para AppConfigProfile dataclass."""

    def test_profile_freeform(self):
        """Testa perfil freeform."""
        profile = AppConfigProfile(name="test", type="AWS.Freeform")
        assert profile.is_freeform is True

    def test_profile_feature_flags(self):
        """Testa perfil feature flags."""
        profile = AppConfigProfile(name="test", type="AWS.AppConfig.FeatureFlags")
        assert profile.is_feature_flags is True

    def test_profile_ssm(self):
        """Testa perfil SSM."""
        profile = AppConfigProfile(name="test", location_uri="ssm-document://doc")
        assert profile.uses_ssm is True

    def test_profile_s3(self):
        """Testa perfil S3."""
        profile = AppConfigProfile(name="test", location_uri="s3://bucket/key")
        assert profile.uses_s3 is True

    def test_profile_secrets_manager(self):
        """Testa perfil Secrets Manager."""
        profile = AppConfigProfile(name="test", location_uri="secretsmanager://secret")
        assert profile.uses_secrets_manager is True

    def test_profile_with_validators(self):
        """Testa perfil com validadores."""
        profile = AppConfigProfile(name="test", validators=[{"Type": "JSON_SCHEMA"}])
        assert profile.has_validators is True

    def test_profile_with_kms(self):
        """Testa perfil com KMS."""
        profile = AppConfigProfile(name="test", kms_key_identifier="arn:...")
        assert profile.has_kms is True

    def test_profile_to_dict(self):
        """Testa conversão para dicionário."""
        profile = AppConfigProfile(id="prof-123", name="test-profile")
        result = profile.to_dict()
        assert result["id"] == "prof-123"


class TestAppConfigDeploymentStrategyDataclass:
    """Testes para AppConfigDeploymentStrategy dataclass."""

    def test_strategy_linear(self):
        """Testa estratégia linear."""
        strategy = AppConfigDeploymentStrategy(name="test", growth_type="LINEAR")
        assert strategy.is_linear is True

    def test_strategy_exponential(self):
        """Testa estratégia exponencial."""
        strategy = AppConfigDeploymentStrategy(name="test", growth_type="EXPONENTIAL")
        assert strategy.is_exponential is True

    def test_strategy_all_at_once(self):
        """Testa estratégia all at once."""
        strategy = AppConfigDeploymentStrategy(name="test", growth_factor=100.0)
        assert strategy.is_all_at_once is True

    def test_strategy_with_bake_time(self):
        """Testa estratégia com bake time."""
        strategy = AppConfigDeploymentStrategy(name="test", final_bake_time_in_minutes=10)
        assert strategy.has_bake_time is True

    def test_strategy_total_duration(self):
        """Testa duração total."""
        strategy = AppConfigDeploymentStrategy(
            name="test",
            deployment_duration_in_minutes=20,
            final_bake_time_in_minutes=10
        )
        assert strategy.total_duration_minutes == 30

    def test_strategy_to_dict(self):
        """Testa conversão para dicionário."""
        strategy = AppConfigDeploymentStrategy(id="strat-123", name="test-strategy")
        result = strategy.to_dict()
        assert result["id"] == "strat-123"


class TestAppConfigService:
    """Testes para AppConfigService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = AppConfigService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_applications.return_value = {"Items": []}
        mock_factory.get_client.return_value = mock_client

        service = AppConfigService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestSQSQueueDataclass:
    """Testes para SQSQueue dataclass."""

    def test_queue_fifo(self):
        """Testa fila FIFO."""
        queue = SQSQueue(queue_name="test.fifo", fifo_queue=True)
        assert queue.is_fifo is True
        assert queue.is_standard is False

    def test_queue_standard(self):
        """Testa fila standard."""
        queue = SQSQueue(queue_name="test", fifo_queue=False)
        assert queue.is_standard is True

    def test_queue_with_dlq(self):
        """Testa fila com DLQ."""
        queue = SQSQueue(
            queue_name="test",
            redrive_policy={"deadLetterTargetArn": "arn:..."}
        )
        assert queue.has_dlq is True
        assert queue.max_receives == 0

    def test_queue_with_encryption_kms(self):
        """Testa fila com criptografia KMS."""
        queue = SQSQueue(queue_name="test", kms_master_key_id="arn:...")
        assert queue.has_encryption is True
        assert queue.uses_kms is True

    def test_queue_with_encryption_sqs(self):
        """Testa fila com criptografia SSE-SQS."""
        queue = SQSQueue(queue_name="test", sqs_managed_sse_enabled=True)
        assert queue.has_encryption is True
        assert queue.uses_sse_sqs is True

    def test_queue_long_polling(self):
        """Testa fila com long polling."""
        queue = SQSQueue(queue_name="test", receive_message_wait_time_seconds=20)
        assert queue.has_long_polling is True

    def test_queue_with_delay(self):
        """Testa fila com delay."""
        queue = SQSQueue(queue_name="test", delay_seconds=60)
        assert queue.has_delay is True

    def test_queue_with_messages(self):
        """Testa fila com mensagens."""
        queue = SQSQueue(queue_name="test", approximate_number_of_messages=10)
        assert queue.has_messages is True

    def test_queue_total_messages(self):
        """Testa total de mensagens."""
        queue = SQSQueue(
            queue_name="test",
            approximate_number_of_messages=10,
            approximate_number_of_messages_not_visible=5,
            approximate_number_of_messages_delayed=2
        )
        assert queue.total_messages == 17

    def test_queue_to_dict(self):
        """Testa conversão para dicionário."""
        queue = SQSQueue(queue_url="url", queue_name="test-queue")
        result = queue.to_dict()
        assert result["queue_name"] == "test-queue"


class TestSQSService:
    """Testes para SQSService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = SQSService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_queues.return_value = {"QueueUrls": []}
        mock_factory.get_client.return_value = mock_client

        service = SQSService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_xray_service(self):
        """Testa obtenção do XRayService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_xray_service()
        
        assert isinstance(service, XRayService)

    def test_factory_get_cloudformation_service(self):
        """Testa obtenção do CloudFormationService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_cloudformation_service()
        
        assert isinstance(service, CloudFormationService)

    def test_factory_get_ssm_service(self):
        """Testa obtenção do SSMService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_ssm_service()
        
        assert isinstance(service, SSMService)

    def test_factory_get_appconfig_service(self):
        """Testa obtenção do AppConfigService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_appconfig_service()
        
        assert isinstance(service, AppConfigService)

    def test_factory_get_sqs_service(self):
        """Testa obtenção do SQSService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_sqs_service()
        
        assert isinstance(service, SQSService)

    def test_factory_get_all_services_includes_phase40(self):
        """Testa que get_all_services inclui serviços da FASE 4.0."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'xray' in services
        assert 'cloudformation' in services
        assert 'ssm' in services
        assert 'appconfig' in services
        assert 'sqs' in services
