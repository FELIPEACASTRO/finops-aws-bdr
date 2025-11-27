"""
Testes unitários para FASE 4.1 - Security & Identity Services.

IAM, Security Hub, Macie.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from src.finops_aws.services.iam_service import (
    IAMService, IAMUser, IAMRole, IAMPolicy
)
from src.finops_aws.services.securityhub_service import (
    SecurityHubService, SecurityHubStandard, SecurityHubFinding, SecurityHubInsight
)
from src.finops_aws.services.macie_service import (
    MacieService, MacieClassificationJob, MacieBucket, MacieFinding
)
from src.finops_aws.core.factories import ServiceFactory


class TestIAMUserDataclass:
    """Testes para IAMUser dataclass."""

    def test_user_with_console_access(self):
        """Testa usuário com acesso ao console."""
        user = IAMUser(user_name="test", password_last_used=datetime.now(timezone.utc))
        assert user.has_console_access is True

    def test_user_without_console_access(self):
        """Testa usuário sem acesso ao console."""
        user = IAMUser(user_name="test")
        assert user.has_console_access is False

    def test_user_with_access_keys(self):
        """Testa usuário com access keys."""
        user = IAMUser(user_name="test", access_keys=[{"Status": "Active"}])
        assert user.has_access_keys is True
        assert user.active_access_keys == 1

    def test_user_with_mfa(self):
        """Testa usuário com MFA."""
        user = IAMUser(user_name="test", mfa_devices=[{"SerialNumber": "arn:..."}])
        assert user.has_mfa is True

    def test_user_without_mfa(self):
        """Testa usuário sem MFA."""
        user = IAMUser(user_name="test")
        assert user.has_mfa is False

    def test_user_with_permissions_boundary(self):
        """Testa usuário com permissions boundary."""
        user = IAMUser(user_name="test", permissions_boundary={"PermissionsBoundaryArn": "arn:..."})
        assert user.has_permissions_boundary is True

    def test_user_with_groups(self):
        """Testa usuário com grupos."""
        user = IAMUser(user_name="test", groups=["admin", "developers"])
        assert user.has_groups is True

    def test_user_inactive(self):
        """Testa usuário inativo."""
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        user = IAMUser(user_name="test", password_last_used=old_date)
        assert user.is_inactive is True

    def test_user_active(self):
        """Testa usuário ativo."""
        recent_date = datetime.now(timezone.utc) - timedelta(days=10)
        user = IAMUser(user_name="test", password_last_used=recent_date)
        assert user.is_inactive is False

    def test_user_to_dict(self):
        """Testa conversão para dicionário."""
        user = IAMUser(user_name="test-user", user_id="AIDA123")
        result = user.to_dict()
        assert result["user_name"] == "test-user"


class TestIAMRoleDataclass:
    """Testes para IAMRole dataclass."""

    def test_role_service_role(self):
        """Testa service role."""
        role = IAMRole(
            role_name="test",
            assume_role_policy_document={
                "Statement": [{"Principal": {"Service": ["lambda.amazonaws.com"]}}]
            }
        )
        assert role.is_service_role is True

    def test_role_cross_account(self):
        """Testa cross-account role."""
        role = IAMRole(
            role_name="test",
            assume_role_policy_document={
                "Statement": [{"Principal": {"AWS": ["arn:aws:iam::123456789012:root"]}}]
            }
        )
        assert role.is_cross_account is True

    def test_role_with_permissions_boundary(self):
        """Testa role com permissions boundary."""
        role = IAMRole(role_name="test", permissions_boundary={"PermissionsBoundaryArn": "arn:..."})
        assert role.has_permissions_boundary is True

    def test_role_recently_used(self):
        """Testa role usada recentemente."""
        role = IAMRole(
            role_name="test",
            last_used={"LastUsedDate": datetime.now(timezone.utc) - timedelta(days=10)}
        )
        assert role.is_recently_used is True

    def test_role_unused(self):
        """Testa role não usada."""
        role = IAMRole(
            role_name="test",
            last_used={"LastUsedDate": datetime.now(timezone.utc) - timedelta(days=100)}
        )
        assert role.is_unused is True

    def test_role_never_used(self):
        """Testa role nunca usada."""
        role = IAMRole(role_name="test")
        assert role.is_unused is True

    def test_role_to_dict(self):
        """Testa conversão para dicionário."""
        role = IAMRole(role_name="test-role", role_id="AROA123")
        result = role.to_dict()
        assert result["role_name"] == "test-role"


class TestIAMPolicyDataclass:
    """Testes para IAMPolicy dataclass."""

    def test_policy_attached(self):
        """Testa policy anexada."""
        policy = IAMPolicy(policy_name="test", attachment_count=2)
        assert policy.is_attached is True
        assert policy.is_unattached is False

    def test_policy_unattached(self):
        """Testa policy não anexada."""
        policy = IAMPolicy(policy_name="test", attachment_count=0)
        assert policy.is_unattached is True

    def test_policy_permissions_boundary(self):
        """Testa policy usada como permissions boundary."""
        policy = IAMPolicy(policy_name="test", permissions_boundary_usage_count=1)
        assert policy.is_permissions_boundary is True

    def test_policy_aws_managed(self):
        """Testa policy AWS managed."""
        policy = IAMPolicy(policy_name="test", arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess")
        assert policy.is_aws_managed is True
        assert policy.is_customer_managed is False

    def test_policy_customer_managed(self):
        """Testa policy customer managed."""
        policy = IAMPolicy(policy_name="test", arn="arn:aws:iam::123456789012:policy/MyPolicy")
        assert policy.is_customer_managed is True

    def test_policy_to_dict(self):
        """Testa conversão para dicionário."""
        policy = IAMPolicy(policy_name="test-policy", policy_id="ANPA123")
        result = policy.to_dict()
        assert result["policy_name"] == "test-policy"


class TestIAMService:
    """Testes para IAMService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = IAMService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_users.return_value = {"Users": []}
        mock_factory.get_client.return_value = mock_client

        service = IAMService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestSecurityHubStandardDataclass:
    """Testes para SecurityHubStandard dataclass."""

    def test_standard_ready(self):
        """Testa padrão pronto."""
        std = SecurityHubStandard(name="test", standards_status="READY")
        assert std.is_ready is True

    def test_standard_pending(self):
        """Testa padrão pendente."""
        std = SecurityHubStandard(name="test", standards_status="PENDING")
        assert std.is_pending is True

    def test_standard_incomplete(self):
        """Testa padrão incompleto."""
        std = SecurityHubStandard(name="test", standards_status="INCOMPLETE")
        assert std.is_incomplete is True

    def test_standard_failed(self):
        """Testa padrão com falha."""
        std = SecurityHubStandard(name="test", standards_status="FAILED")
        assert std.is_failed is True

    def test_standard_to_dict(self):
        """Testa conversão para dicionário."""
        std = SecurityHubStandard(standards_arn="arn:...", name="CIS AWS")
        result = std.to_dict()
        assert result["name"] == "CIS AWS"


class TestSecurityHubFindingDataclass:
    """Testes para SecurityHubFinding dataclass."""

    def test_finding_critical(self):
        """Testa finding crítico."""
        finding = SecurityHubFinding(id="123", severity={"Label": "CRITICAL"})
        assert finding.is_critical is True
        assert finding.severity_label == "CRITICAL"

    def test_finding_high(self):
        """Testa finding alto."""
        finding = SecurityHubFinding(id="123", severity={"Label": "HIGH"})
        assert finding.is_high is True

    def test_finding_medium(self):
        """Testa finding médio."""
        finding = SecurityHubFinding(id="123", severity={"Label": "MEDIUM"})
        assert finding.is_medium is True

    def test_finding_low(self):
        """Testa finding baixo."""
        finding = SecurityHubFinding(id="123", severity={"Label": "LOW"})
        assert finding.is_low is True

    def test_finding_informational(self):
        """Testa finding informacional."""
        finding = SecurityHubFinding(id="123", severity={"Label": "INFORMATIONAL"})
        assert finding.is_informational is True

    def test_finding_new(self):
        """Testa finding novo."""
        finding = SecurityHubFinding(id="123", workflow={"Status": "NEW"})
        assert finding.is_new is True

    def test_finding_resolved(self):
        """Testa finding resolvido."""
        finding = SecurityHubFinding(id="123", workflow={"Status": "RESOLVED"})
        assert finding.is_resolved is True

    def test_finding_suppressed(self):
        """Testa finding suprimido."""
        finding = SecurityHubFinding(id="123", workflow={"Status": "SUPPRESSED"})
        assert finding.is_suppressed is True

    def test_finding_active(self):
        """Testa finding ativo."""
        finding = SecurityHubFinding(id="123", record_state="ACTIVE")
        assert finding.is_active is True

    def test_finding_archived(self):
        """Testa finding arquivado."""
        finding = SecurityHubFinding(id="123", record_state="ARCHIVED")
        assert finding.is_archived is True

    def test_finding_passed(self):
        """Testa finding passou compliance."""
        finding = SecurityHubFinding(id="123", compliance={"Status": "PASSED"})
        assert finding.is_passed is True

    def test_finding_failed_compliance(self):
        """Testa finding falhou compliance."""
        finding = SecurityHubFinding(id="123", compliance={"Status": "FAILED"})
        assert finding.is_failed_compliance is True

    def test_finding_to_dict(self):
        """Testa conversão para dicionário."""
        finding = SecurityHubFinding(id="finding-123", title="Test Finding")
        result = finding.to_dict()
        assert result["id"] == "finding-123"


class TestSecurityHubInsightDataclass:
    """Testes para SecurityHubInsight dataclass."""

    def test_insight_with_filters(self):
        """Testa insight com filtros."""
        insight = SecurityHubInsight(name="test", filters={"SeverityLabel": [{"Value": "CRITICAL"}]})
        assert insight.has_filters is True

    def test_insight_with_group_by(self):
        """Testa insight com group by."""
        insight = SecurityHubInsight(name="test", group_by_attribute="ResourceType")
        assert insight.has_group_by is True

    def test_insight_to_dict(self):
        """Testa conversão para dicionário."""
        insight = SecurityHubInsight(insight_arn="arn:...", name="Critical Findings")
        result = insight.to_dict()
        assert result["name"] == "Critical Findings"


class TestSecurityHubService:
    """Testes para SecurityHubService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = SecurityHubService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_hub.return_value = {}
        mock_factory.get_client.return_value = mock_client

        service = SecurityHubService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestMacieClassificationJobDataclass:
    """Testes para MacieClassificationJob dataclass."""

    def test_job_running(self):
        """Testa job rodando."""
        job = MacieClassificationJob(job_id="123", job_status="RUNNING")
        assert job.is_running is True

    def test_job_paused(self):
        """Testa job pausado."""
        job = MacieClassificationJob(job_id="123", job_status="PAUSED")
        assert job.is_paused is True

    def test_job_complete(self):
        """Testa job completo."""
        job = MacieClassificationJob(job_id="123", job_status="COMPLETE")
        assert job.is_complete is True

    def test_job_cancelled(self):
        """Testa job cancelado."""
        job = MacieClassificationJob(job_id="123", job_status="CANCELLED")
        assert job.is_cancelled is True

    def test_job_one_time(self):
        """Testa job único."""
        job = MacieClassificationJob(job_id="123", job_type="ONE_TIME")
        assert job.is_one_time is True

    def test_job_scheduled(self):
        """Testa job agendado."""
        job = MacieClassificationJob(job_id="123", job_type="SCHEDULED")
        assert job.is_scheduled is True

    def test_job_with_sampling(self):
        """Testa job com sampling."""
        job = MacieClassificationJob(job_id="123", sampling_percentage=50)
        assert job.uses_sampling is True

    def test_job_without_sampling(self):
        """Testa job sem sampling."""
        job = MacieClassificationJob(job_id="123", sampling_percentage=100)
        assert job.uses_sampling is False

    def test_job_to_dict(self):
        """Testa conversão para dicionário."""
        job = MacieClassificationJob(job_id="job-123", name="Test Job")
        result = job.to_dict()
        assert result["job_id"] == "job-123"


class TestMacieBucketDataclass:
    """Testes para MacieBucket dataclass."""

    def test_bucket_public(self):
        """Testa bucket público."""
        bucket = MacieBucket(bucket_name="test", public_access={"effectivePermission": "PUBLIC"})
        assert bucket.is_public is True

    def test_bucket_not_public(self):
        """Testa bucket não público."""
        bucket = MacieBucket(bucket_name="test", public_access={"effectivePermission": "NOT_PUBLIC"})
        assert bucket.is_not_public is True

    def test_bucket_external_shared(self):
        """Testa bucket compartilhado externamente."""
        bucket = MacieBucket(bucket_name="test", shared_access="EXTERNAL")
        assert bucket.is_external_shared is True
        assert bucket.is_shared is True

    def test_bucket_internal_shared(self):
        """Testa bucket compartilhado internamente."""
        bucket = MacieBucket(bucket_name="test", shared_access="INTERNAL")
        assert bucket.is_internal_shared is True

    def test_bucket_not_shared(self):
        """Testa bucket não compartilhado."""
        bucket = MacieBucket(bucket_name="test", shared_access="NOT_SHARED")
        assert bucket.is_not_shared is True

    def test_bucket_with_sensitivity(self):
        """Testa bucket com sensibilidade."""
        bucket = MacieBucket(bucket_name="test", sensitivity_score=30)
        assert bucket.has_sensitivity is True

    def test_bucket_high_sensitivity(self):
        """Testa bucket com alta sensibilidade."""
        bucket = MacieBucket(bucket_name="test", sensitivity_score=75)
        assert bucket.is_high_sensitivity is True

    def test_bucket_size_in_gb(self):
        """Testa tamanho em GB."""
        bucket = MacieBucket(bucket_name="test", size_in_bytes=1073741824)
        assert bucket.size_in_gb == pytest.approx(1.0)

    def test_bucket_to_dict(self):
        """Testa conversão para dicionário."""
        bucket = MacieBucket(bucket_name="test-bucket", account_id="123456789012")
        result = bucket.to_dict()
        assert result["bucket_name"] == "test-bucket"


class TestMacieFindingDataclass:
    """Testes para MacieFinding dataclass."""

    def test_finding_high_severity(self):
        """Testa finding alta severidade."""
        finding = MacieFinding(id="123", severity={"score": 8.0})
        assert finding.is_high_severity is True

    def test_finding_medium_severity(self):
        """Testa finding média severidade."""
        finding = MacieFinding(id="123", severity={"score": 5.0})
        assert finding.is_medium_severity is True

    def test_finding_low_severity(self):
        """Testa finding baixa severidade."""
        finding = MacieFinding(id="123", severity={"score": 2.0})
        assert finding.is_low_severity is True

    def test_finding_archived(self):
        """Testa finding arquivado."""
        finding = MacieFinding(id="123", archived=True)
        assert finding.is_archived is True

    def test_finding_policy(self):
        """Testa finding de policy."""
        finding = MacieFinding(id="123", category="POLICY")
        assert finding.is_policy_finding is True

    def test_finding_sensitive_data(self):
        """Testa finding de dados sensíveis."""
        finding = MacieFinding(id="123", category="CLASSIFICATION")
        assert finding.is_sensitive_data_finding is True

    def test_finding_to_dict(self):
        """Testa conversão para dicionário."""
        finding = MacieFinding(id="finding-123", title="Test Finding")
        result = finding.to_dict()
        assert result["id"] == "finding-123"


class TestMacieService:
    """Testes para MacieService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = MacieService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.get_macie_session.return_value = {}
        mock_factory.get_client.return_value = mock_client

        service = MacieService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_iam_service(self):
        """Testa obtenção do IAMService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_iam_service()
        
        assert isinstance(service, IAMService)

    def test_factory_get_securityhub_service(self):
        """Testa obtenção do SecurityHubService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_securityhub_service()
        
        assert isinstance(service, SecurityHubService)

    def test_factory_get_macie_service(self):
        """Testa obtenção do MacieService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_macie_service()
        
        assert isinstance(service, MacieService)

    def test_factory_get_all_services_includes_phase41(self):
        """Testa que get_all_services inclui serviços da FASE 4.1."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'iam' in services
        assert 'securityhub' in services
        assert 'macie' in services
