"""
Testes unitários para FASE 4.2 - Management & Governance Services.

Trusted Advisor, Organizations, Control Tower.
"""

import pytest
from unittest.mock import MagicMock

from src.finops_aws.services.trustedadvisor_service import (
    TrustedAdvisorService, TrustedAdvisorCheck
)
from src.finops_aws.services.organizations_service import (
    OrganizationsService, Organization, Account, OrganizationalUnit
)
from src.finops_aws.services.controltower_service import (
    ControlTowerService, ControlTowerEnrolledAccount, ControlTowerGuardrail
)
from src.finops_aws.core.factories import ServiceFactory


class TestTrustedAdvisorCheckDataclass:
    """Testes para TrustedAdvisorCheck dataclass."""

    def test_check_warning_status(self):
        """Testa check com status warning."""
        check = TrustedAdvisorCheck(
            check_id="123", name="test", description="desc",
            category="cost_optimizing", metadata=[],
            resources_summary={}, status="warning"
        )
        assert check.is_warning is True

    def test_check_error_status(self):
        """Testa check com status error."""
        check = TrustedAdvisorCheck(
            check_id="123", name="test", description="desc",
            category="cost_optimizing", metadata=[],
            resources_summary={}, status="error"
        )
        assert check.is_error is True

    def test_check_ok_status(self):
        """Testa check com status ok."""
        check = TrustedAdvisorCheck(
            check_id="123", name="test", description="desc",
            category="cost_optimizing", metadata=[],
            resources_summary={}, status="ok"
        )
        assert check.is_ok is True

    def test_check_has_flagged_resources(self):
        """Testa check com recursos flagged."""
        check = TrustedAdvisorCheck(
            check_id="123", name="test", description="desc",
            category="cost_optimizing", metadata=[],
            resources_summary={}, resource_flagged_count=5
        )
        assert check.has_flagged_resources is True

    def test_check_cost_optimized(self):
        """Testa check otimizado de custo."""
        check = TrustedAdvisorCheck(
            check_id="123", name="test", description="desc",
            category="cost_optimizing", metadata=[],
            resources_summary={}, status="ok"
        )
        assert check.cost_optimized is True

    def test_check_to_dict(self):
        """Testa conversão para dicionário."""
        check = TrustedAdvisorCheck(
            check_id="check-123", name="Test Check",
            description="desc", category="cost_optimizing",
            metadata=[], resources_summary={}
        )
        result = check.to_dict()
        assert result["check_id"] == "check-123"


class TestTrustedAdvisorService:
    """Testes para TrustedAdvisorService."""

    def test_service_init(self):
        """Testa inicialização."""
        mock_factory = MagicMock()
        service = TrustedAdvisorService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_trusted_advisor_checks.return_value = {}
        mock_factory.get_client.return_value = mock_client

        service = TrustedAdvisorService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestOrganizationDataclass:
    """Testes para Organization dataclass."""

    def test_organization_all_features(self):
        """Testa organização com all features."""
        org = Organization(
            arn="arn:...", id="o-123", root_id="r-123",
            master_account_id="123456789012",
            master_account_email="master@example.com",
            feature_set="ALL"
        )
        assert org.is_all_features is True

    def test_organization_consolidated_billing(self):
        """Testa organização com consolidated billing."""
        org = Organization(
            arn="arn:...", id="o-123", root_id="r-123",
            master_account_id="123456789012",
            master_account_email="master@example.com",
            feature_set="CONSOLIDATED_BILLING"
        )
        assert org.is_consolidated_billing is True

    def test_organization_to_dict(self):
        """Testa conversão para dicionário."""
        org = Organization(
            arn="arn:...", id="o-123", root_id="r-123",
            master_account_id="123456789012",
            master_account_email="master@example.com"
        )
        result = org.to_dict()
        assert result["id"] == "o-123"


class TestAccountDataclass:
    """Testes para Account dataclass."""

    def test_account_active(self):
        """Testa conta ativa."""
        account = Account(id="123", name="test", email="test@example.com", arn="arn:...", status="ACTIVE")
        assert account.is_active is True

    def test_account_suspended(self):
        """Testa conta suspensa."""
        account = Account(id="123", name="test", email="test@example.com", arn="arn:...", status="SUSPENDED")
        assert account.is_suspended is True

    def test_account_created(self):
        """Testa conta criada."""
        account = Account(id="123", name="test", email="test@example.com", arn="arn:...", joined_method="CREATED")
        assert account.is_created is True

    def test_account_invited(self):
        """Testa conta convidada."""
        account = Account(id="123", name="test", email="test@example.com", arn="arn:...", joined_method="INVITED")
        assert account.is_invited is True

    def test_account_to_dict(self):
        """Testa conversão para dicionário."""
        account = Account(id="acc-123", name="Test", email="test@example.com", arn="arn:...")
        result = account.to_dict()
        assert result["id"] == "acc-123"


class TestOrganizationalUnitDataclass:
    """Testes para OrganizationalUnit dataclass."""

    def test_ou_root(self):
        """Testa OU raiz."""
        ou = OrganizationalUnit(id="r-123", name="Root", arn="arn:...", parent_id="")
        assert ou.is_root is True

    def test_ou_not_root(self):
        """Testa OU não raiz."""
        ou = OrganizationalUnit(id="ou-123", name="Finance", arn="arn:...", parent_id="r-123")
        assert ou.is_root is False

    def test_ou_to_dict(self):
        """Testa conversão para dicionário."""
        ou = OrganizationalUnit(id="ou-123", name="Finance", arn="arn:...", parent_id="r-123")
        result = ou.to_dict()
        assert result["id"] == "ou-123"


class TestOrganizationsService:
    """Testes para OrganizationsService."""

    def test_service_init(self):
        """Testa inicialização."""
        mock_factory = MagicMock()
        service = OrganizationsService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_organization.return_value = {}
        mock_factory.get_client.return_value = mock_client

        service = OrganizationsService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestControlTowerEnrolledAccountDataclass:
    """Testes para ControlTowerEnrolledAccount dataclass."""

    def test_account_enrolled(self):
        """Testa conta inscrita."""
        account = ControlTowerEnrolledAccount(
            account_id="123", account_name="test",
            email="test@example.com", enrollment_status="ENROLLED"
        )
        assert account.is_enrolled is True

    def test_account_pending(self):
        """Testa conta pendente."""
        account = ControlTowerEnrolledAccount(
            account_id="123", account_name="test",
            email="test@example.com", enrollment_status="PENDING"
        )
        assert account.is_pending is True

    def test_account_to_dict(self):
        """Testa conversão para dicionário."""
        account = ControlTowerEnrolledAccount(
            account_id="acc-123", account_name="Test",
            email="test@example.com"
        )
        result = account.to_dict()
        assert result["account_id"] == "acc-123"


class TestControlTowerGuardrailDataclass:
    """Testes para ControlTowerGuardrail dataclass."""

    def test_guardrail_enabled(self):
        """Testa guardrail ativado."""
        gr = ControlTowerGuardrail(
            guardrail_id="gr-123", name="test",
            description="desc", guardrail_type="PREVENTIVE", status="ENABLED"
        )
        assert gr.is_enabled is True

    def test_guardrail_disabled(self):
        """Testa guardrail desativado."""
        gr = ControlTowerGuardrail(
            guardrail_id="gr-123", name="test",
            description="desc", guardrail_type="PREVENTIVE", status="DISABLED"
        )
        assert gr.is_disabled is True

    def test_guardrail_preventive(self):
        """Testa guardrail preventivo."""
        gr = ControlTowerGuardrail(
            guardrail_id="gr-123", name="test",
            description="desc", guardrail_type="PREVENTIVE"
        )
        assert gr.is_preventive is True

    def test_guardrail_detective(self):
        """Testa guardrail detective."""
        gr = ControlTowerGuardrail(
            guardrail_id="gr-123", name="test",
            description="desc", guardrail_type="DETECTIVE"
        )
        assert gr.is_detective is True

    def test_guardrail_compliant(self):
        """Testa guardrail conforme."""
        gr = ControlTowerGuardrail(
            guardrail_id="gr-123", name="test",
            description="desc", guardrail_type="PREVENTIVE",
            compliance_status="COMPLIANT"
        )
        assert gr.is_compliant is True

    def test_guardrail_to_dict(self):
        """Testa conversão para dicionário."""
        gr = ControlTowerGuardrail(
            guardrail_id="gr-123", name="Test",
            description="desc", guardrail_type="PREVENTIVE"
        )
        result = gr.to_dict()
        assert result["guardrail_id"] == "gr-123"


class TestControlTowerService:
    """Testes para ControlTowerService."""

    def test_service_init(self):
        """Testa inicialização."""
        mock_factory = MagicMock()
        service = ControlTowerService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_landing_zone_configuration.return_value = {}
        mock_factory.get_client.return_value = mock_client

        service = ControlTowerService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_trustedadvisor_service(self):
        """Testa obtenção do TrustedAdvisorService."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_trustedadvisor_service()
        
        assert isinstance(service, TrustedAdvisorService)

    def test_factory_get_organizations_service(self):
        """Testa obtenção do OrganizationsService."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_organizations_service()
        
        assert isinstance(service, OrganizationsService)

    def test_factory_get_controltower_service(self):
        """Testa obtenção do ControlTowerService."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_controltower_service()
        
        assert isinstance(service, ControlTowerService)

    def test_factory_get_all_services_includes_phase42(self):
        """Testa que get_all_services inclui serviços da FASE 4.2."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'trustedadvisor' in services
        assert 'organizations' in services
        assert 'controltower' in services
