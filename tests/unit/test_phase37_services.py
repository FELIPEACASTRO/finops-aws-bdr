"""
Testes unitários para FASE 3.7 - End User Computing Services.

AppStream, WorkDocs, Chime.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.appstream_service import (
    AppStreamService, AppStreamFleet, AppStreamStack, AppStreamImage
)
from src.finops_aws.services.workdocs_service import (
    WorkDocsService, WorkDocsUser, WorkDocsFolder, WorkDocsDocument
)
from src.finops_aws.services.chime_service import (
    ChimeService, ChimeAccount, ChimeUser, ChimePhoneNumber
)
from src.finops_aws.core.factories import ServiceFactory


class TestAppStreamFleetDataclass:
    """Testes para AppStreamFleet dataclass."""

    def test_fleet_running(self):
        """Testa fleet rodando."""
        fleet = AppStreamFleet(name="fleet-001", state="RUNNING")
        assert fleet.is_running is True
        assert fleet.is_stopped is False

    def test_fleet_stopped(self):
        """Testa fleet parada."""
        fleet = AppStreamFleet(name="fleet-001", state="STOPPED")
        assert fleet.is_stopped is True

    def test_fleet_starting(self):
        """Testa fleet iniciando."""
        fleet = AppStreamFleet(name="fleet-001", state="STARTING")
        assert fleet.is_starting is True

    def test_fleet_stopping(self):
        """Testa fleet parando."""
        fleet = AppStreamFleet(name="fleet-001", state="STOPPING")
        assert fleet.is_stopping is True

    def test_fleet_always_on(self):
        """Testa fleet always-on."""
        fleet = AppStreamFleet(name="fleet-001", fleet_type="ALWAYS_ON")
        assert fleet.is_always_on is True
        assert fleet.is_on_demand is False

    def test_fleet_on_demand(self):
        """Testa fleet on-demand."""
        fleet = AppStreamFleet(name="fleet-001", fleet_type="ON_DEMAND")
        assert fleet.is_on_demand is True

    def test_fleet_elastic(self):
        """Testa fleet elastic."""
        fleet = AppStreamFleet(name="fleet-001", fleet_type="ELASTIC")
        assert fleet.is_elastic is True

    def test_fleet_capacity(self):
        """Testa capacidade da fleet."""
        fleet = AppStreamFleet(
            name="fleet-001",
            compute_capacity_status={
                "Desired": 10, "Running": 8, "InUse": 4, "Available": 4
            }
        )
        assert fleet.desired_capacity == 10
        assert fleet.running_capacity == 8
        assert fleet.in_use_capacity == 4
        assert fleet.available_capacity == 4
        assert fleet.utilization_percentage == pytest.approx(50.0)

    def test_fleet_platform_windows(self):
        """Testa fleet Windows."""
        fleet = AppStreamFleet(name="fleet-001", platform="WINDOWS")
        assert fleet.is_windows is True

    def test_fleet_platform_linux(self):
        """Testa fleet Amazon Linux."""
        fleet = AppStreamFleet(name="fleet-001", platform="AMAZON_LINUX2")
        assert fleet.is_amazon_linux is True

    def test_fleet_to_dict(self):
        """Testa conversão para dicionário."""
        fleet = AppStreamFleet(name="test-fleet")
        result = fleet.to_dict()
        assert result["name"] == "test-fleet"


class TestAppStreamStackDataclass:
    """Testes para AppStreamStack dataclass."""

    def test_stack_storage_connectors(self):
        """Testa stack com conectores de storage."""
        stack = AppStreamStack(
            name="stack-001",
            storage_connectors=[{"ConnectorType": "HOMEFOLDERS"}]
        )
        assert stack.has_storage_connectors is True
        assert "HOMEFOLDERS" in stack.storage_types

    def test_stack_urls(self):
        """Testa stack com URLs."""
        stack = AppStreamStack(
            name="stack-001",
            redirect_url="https://example.com",
            feedback_url="https://feedback.example.com"
        )
        assert stack.has_redirect_url is True
        assert stack.has_feedback_url is True

    def test_stack_embed_domains(self):
        """Testa stack com domínios de embedding."""
        stack = AppStreamStack(
            name="stack-001",
            embed_host_domains=["example.com"]
        )
        assert stack.has_embed_domains is True

    def test_stack_to_dict(self):
        """Testa conversão para dicionário."""
        stack = AppStreamStack(name="test-stack")
        result = stack.to_dict()
        assert result["name"] == "test-stack"


class TestAppStreamImageDataclass:
    """Testes para AppStreamImage dataclass."""

    def test_image_available(self):
        """Testa image disponível."""
        image = AppStreamImage(name="image-001", state="AVAILABLE")
        assert image.is_available is True
        assert image.is_pending is False

    def test_image_pending(self):
        """Testa image pendente."""
        image = AppStreamImage(name="image-001", state="PENDING")
        assert image.is_pending is True

    def test_image_failed(self):
        """Testa image com falha."""
        image = AppStreamImage(name="image-001", state="FAILED")
        assert image.is_failed is True

    def test_image_private(self):
        """Testa image privada."""
        image = AppStreamImage(name="image-001", visibility="PRIVATE")
        assert image.is_private is True
        assert image.is_public is False

    def test_image_public(self):
        """Testa image pública."""
        image = AppStreamImage(name="image-001", visibility="PUBLIC")
        assert image.is_public is True

    def test_image_shared(self):
        """Testa image compartilhada."""
        image = AppStreamImage(name="image-001", visibility="SHARED")
        assert image.is_shared is True

    def test_image_applications(self):
        """Testa aplicações da image."""
        image = AppStreamImage(
            name="image-001",
            applications=[{"Name": "App1"}, {"Name": "App2"}]
        )
        assert image.applications_count == 2

    def test_image_to_dict(self):
        """Testa conversão para dicionário."""
        image = AppStreamImage(name="test-image")
        result = image.to_dict()
        assert result["name"] == "test-image"


class TestAppStreamService:
    """Testes para AppStreamService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = AppStreamService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_fleets.return_value = {"Fleets": []}
        mock_factory.get_client.return_value = mock_client

        service = AppStreamService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = AppStreamService(mock_factory)
        
        result = service.get_resources()
        
        assert "fleets" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = AppStreamService(mock_factory)
        
        result = service.get_metrics()
        
        assert "fleets_count" in result


class TestWorkDocsUserDataclass:
    """Testes para WorkDocsUser dataclass."""

    def test_user_active(self):
        """Testa usuário ativo."""
        user = WorkDocsUser(user_id="user-001", status="ACTIVE")
        assert user.is_active is True
        assert user.is_inactive is False

    def test_user_inactive(self):
        """Testa usuário inativo."""
        user = WorkDocsUser(user_id="user-001", status="INACTIVE")
        assert user.is_inactive is True

    def test_user_pending(self):
        """Testa usuário pendente."""
        user = WorkDocsUser(user_id="user-001", status="PENDING")
        assert user.is_pending is True

    def test_user_type_user(self):
        """Testa tipo usuário."""
        user = WorkDocsUser(user_id="user-001", type="USER")
        assert user.is_user is True

    def test_user_type_admin(self):
        """Testa tipo admin."""
        user = WorkDocsUser(user_id="user-001", type="ADMIN")
        assert user.is_admin is True

    def test_user_type_poweruser(self):
        """Testa tipo power user."""
        user = WorkDocsUser(user_id="user-001", type="POWERUSER")
        assert user.is_poweruser is True

    def test_user_to_dict(self):
        """Testa conversão para dicionário."""
        user = WorkDocsUser(user_id="test-user")
        result = user.to_dict()
        assert result["user_id"] == "test-user"


class TestWorkDocsFolderDataclass:
    """Testes para WorkDocsFolder dataclass."""

    def test_folder_active(self):
        """Testa folder ativo."""
        folder = WorkDocsFolder(folder_id="folder-001", resource_state="ACTIVE")
        assert folder.is_active is True

    def test_folder_recycling(self):
        """Testa folder na lixeira."""
        folder = WorkDocsFolder(folder_id="folder-001", resource_state="RECYCLING")
        assert folder.is_recycling is True

    def test_folder_recycled(self):
        """Testa folder reciclado."""
        folder = WorkDocsFolder(folder_id="folder-001", resource_state="RECYCLED")
        assert folder.is_recycled is True

    def test_folder_restoring(self):
        """Testa folder restaurando."""
        folder = WorkDocsFolder(folder_id="folder-001", resource_state="RESTORING")
        assert folder.is_restoring is True

    def test_folder_labels(self):
        """Testa folder com labels."""
        folder = WorkDocsFolder(folder_id="folder-001", labels=["important"])
        assert folder.has_labels is True

    def test_folder_to_dict(self):
        """Testa conversão para dicionário."""
        folder = WorkDocsFolder(folder_id="test-folder")
        result = folder.to_dict()
        assert result["folder_id"] == "test-folder"


class TestWorkDocsDocumentDataclass:
    """Testes para WorkDocsDocument dataclass."""

    def test_document_active(self):
        """Testa documento ativo."""
        doc = WorkDocsDocument(document_id="doc-001", resource_state="ACTIVE")
        assert doc.is_active is True

    def test_document_recycling(self):
        """Testa documento na lixeira."""
        doc = WorkDocsDocument(document_id="doc-001", resource_state="RECYCLING")
        assert doc.is_recycling is True

    def test_document_labels(self):
        """Testa documento com labels."""
        doc = WorkDocsDocument(document_id="doc-001", labels=["confidential"])
        assert doc.has_labels is True

    def test_document_version(self):
        """Testa versão do documento."""
        doc = WorkDocsDocument(
            document_id="doc-001",
            latest_version_metadata={"Id": "v1", "ContentType": "application/pdf", "Size": 1024}
        )
        assert doc.version_id == "v1"
        assert doc.content_type == "application/pdf"
        assert doc.size_bytes == 1024

    def test_document_to_dict(self):
        """Testa conversão para dicionário."""
        doc = WorkDocsDocument(document_id="test-doc")
        result = doc.to_dict()
        assert result["document_id"] == "test-doc"


class TestWorkDocsService:
    """Testes para WorkDocsService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = WorkDocsService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_users.return_value = {"Users": []}
        mock_factory.get_client.return_value = mock_client

        service = WorkDocsService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = WorkDocsService(mock_factory)
        
        result = service.get_resources()
        
        assert "users" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = WorkDocsService(mock_factory)
        
        result = service.get_metrics()
        
        assert "users_count" in result


class TestChimeAccountDataclass:
    """Testes para ChimeAccount dataclass."""

    def test_account_active(self):
        """Testa account ativo."""
        acc = ChimeAccount(account_id="acc-001", account_status="Active")
        assert acc.is_active is True
        assert acc.is_suspended is False

    def test_account_suspended(self):
        """Testa account suspenso."""
        acc = ChimeAccount(account_id="acc-001", account_status="Suspended")
        assert acc.is_suspended is True

    def test_account_team(self):
        """Testa account Team."""
        acc = ChimeAccount(account_id="acc-001", account_type="Team")
        assert acc.is_team is True

    def test_account_enterprise_directory(self):
        """Testa account Enterprise Directory."""
        acc = ChimeAccount(account_id="acc-001", account_type="EnterpriseDirectory")
        assert acc.is_enterprise_directory is True

    def test_account_pro_license(self):
        """Testa account com licença Pro."""
        acc = ChimeAccount(account_id="acc-001", default_license="Pro")
        assert acc.uses_pro_license is True

    def test_account_basic_license(self):
        """Testa account com licença Basic."""
        acc = ChimeAccount(account_id="acc-001", default_license="Basic")
        assert acc.uses_basic_license is True

    def test_account_delegate_groups(self):
        """Testa account com grupos delegados."""
        acc = ChimeAccount(account_id="acc-001", signin_delegate_groups=[{"GroupName": "admins"}])
        assert acc.has_delegate_groups is True

    def test_account_to_dict(self):
        """Testa conversão para dicionário."""
        acc = ChimeAccount(account_id="test-acc")
        result = acc.to_dict()
        assert result["account_id"] == "test-acc"


class TestChimeUserDataclass:
    """Testes para ChimeUser dataclass."""

    def test_user_registered(self):
        """Testa usuário registrado."""
        user = ChimeUser(user_id="user-001", user_registration_status="Registered")
        assert user.is_registered is True
        assert user.is_unregistered is False

    def test_user_unregistered(self):
        """Testa usuário não registrado."""
        user = ChimeUser(user_id="user-001", user_registration_status="Unregistered")
        assert user.is_unregistered is True

    def test_user_suspended(self):
        """Testa usuário suspenso."""
        user = ChimeUser(user_id="user-001", user_registration_status="Suspended")
        assert user.is_suspended is True

    def test_user_pro_license(self):
        """Testa usuário com licença Pro."""
        user = ChimeUser(user_id="user-001", license_type="Pro")
        assert user.uses_pro_license is True

    def test_user_basic_license(self):
        """Testa usuário com licença Basic."""
        user = ChimeUser(user_id="user-001", license_type="Basic")
        assert user.uses_basic_license is True

    def test_user_plus_license(self):
        """Testa usuário com licença Plus."""
        user = ChimeUser(user_id="user-001", license_type="Plus")
        assert user.uses_plus_license is True

    def test_user_private(self):
        """Testa usuário privado."""
        user = ChimeUser(user_id="user-001", user_type="PrivateUser")
        assert user.is_private_user is True

    def test_user_shared_device(self):
        """Testa usuário dispositivo compartilhado."""
        user = ChimeUser(user_id="user-001", user_type="SharedDevice")
        assert user.is_shared_device is True

    def test_user_phone(self):
        """Testa usuário com telefone."""
        user = ChimeUser(user_id="user-001", primary_provisioned_number="+15551234567")
        assert user.has_phone_number is True

    def test_user_to_dict(self):
        """Testa conversão para dicionário."""
        user = ChimeUser(user_id="test-user")
        result = user.to_dict()
        assert result["user_id"] == "test-user"


class TestChimePhoneNumberDataclass:
    """Testes para ChimePhoneNumber dataclass."""

    def test_phone_assigned(self):
        """Testa número atribuído."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", status="Assigned")
        assert pn.is_assigned is True
        assert pn.is_unassigned is False

    def test_phone_unassigned(self):
        """Testa número não atribuído."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", status="Unassigned")
        assert pn.is_unassigned is True

    def test_phone_deleted(self):
        """Testa número deletado."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", status="Deleted")
        assert pn.is_deleted is True

    def test_phone_release_in_progress(self):
        """Testa número em liberação."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", status="ReleaseInProgress")
        assert pn.is_release_in_progress is True

    def test_phone_local(self):
        """Testa número local."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", type="Local")
        assert pn.is_local is True
        assert pn.is_toll_free is False

    def test_phone_toll_free(self):
        """Testa número toll-free."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", type="TollFree")
        assert pn.is_toll_free is True

    def test_phone_business_calling(self):
        """Testa número business calling."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", product_type="BusinessCalling")
        assert pn.is_business_calling is True

    def test_phone_voice_connector(self):
        """Testa número voice connector."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", product_type="VoiceConnector")
        assert pn.is_voice_connector is True

    def test_phone_sip_media_app(self):
        """Testa número SIP media app."""
        pn = ChimePhoneNumber(phone_number_id="pn-001", product_type="SipMediaApplicationDialIn")
        assert pn.is_sip_media_app is True

    def test_phone_to_dict(self):
        """Testa conversão para dicionário."""
        pn = ChimePhoneNumber(phone_number_id="test-pn")
        result = pn.to_dict()
        assert result["phone_number_id"] == "test-pn"


class TestChimeService:
    """Testes para ChimeService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = ChimeService(mock_factory)
        assert service._client_factory == mock_factory

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_client.list_accounts.return_value = {"Accounts": []}
        mock_factory.get_client.return_value = mock_client

        service = ChimeService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = ChimeService(mock_factory)
        
        result = service.get_resources()
        
        assert "accounts" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_client = MagicMock()
        
        mock_client.get_paginator.return_value.paginate.return_value = [{}]
        
        mock_factory.get_client.return_value = mock_client
        service = ChimeService(mock_factory)
        
        result = service.get_metrics()
        
        assert "accounts_count" in result


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_factory_get_appstream_service(self):
        """Testa obtenção do AppStreamService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_appstream_service()
        
        assert isinstance(service, AppStreamService)

    def test_factory_get_workdocs_service(self):
        """Testa obtenção do WorkDocsService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_workdocs_service()
        
        assert isinstance(service, WorkDocsService)

    def test_factory_get_chime_service(self):
        """Testa obtenção do ChimeService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_chime_service()
        
        assert isinstance(service, ChimeService)

    def test_factory_get_all_services_includes_enduser(self):
        """Testa que get_all_services inclui serviços de End User Computing."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'appstream' in services
        assert 'workdocs' in services
        assert 'chime' in services
