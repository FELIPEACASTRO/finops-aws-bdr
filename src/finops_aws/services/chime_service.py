"""
AWS Chime Service para FinOps.

Análise de custos e otimização de comunicações.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class ChimeAccount:
    """Account Chime."""
    account_id: str
    name: str = ""
    account_type: str = "Team"
    created_timestamp: Optional[datetime] = None
    default_license: str = "Pro"
    supported_licenses: List[str] = field(default_factory=list)
    account_status: str = "Active"
    signin_delegate_groups: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.account_status == "Active"

    @property
    def is_suspended(self) -> bool:
        """Verifica se está suspenso."""
        return self.account_status == "Suspended"

    @property
    def is_team(self) -> bool:
        """Verifica se é Team."""
        return self.account_type == "Team"

    @property
    def is_enterprise_directory(self) -> bool:
        """Verifica se é Enterprise Directory."""
        return self.account_type == "EnterpriseDirectory"

    @property
    def is_enterprise_lwp(self) -> bool:
        """Verifica se é Enterprise LWP."""
        return self.account_type == "EnterpriseLWA"

    @property
    def is_enterprise_oidc(self) -> bool:
        """Verifica se é Enterprise OIDC."""
        return self.account_type == "EnterpriseOIDC"

    @property
    def uses_pro_license(self) -> bool:
        """Verifica se usa licença Pro."""
        return self.default_license == "Pro"

    @property
    def uses_basic_license(self) -> bool:
        """Verifica se usa licença Basic."""
        return self.default_license == "Basic"

    @property
    def has_delegate_groups(self) -> bool:
        """Verifica se tem grupos delegados."""
        return len(self.signin_delegate_groups) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "account_id": self.account_id,
            "name": self.name,
            "account_type": self.account_type,
            "account_status": self.account_status,
            "is_active": self.is_active,
            "default_license": self.default_license,
            "uses_pro_license": self.uses_pro_license,
            "has_delegate_groups": self.has_delegate_groups,
            "created_timestamp": self.created_timestamp.isoformat() if self.created_timestamp else None
        }


@dataclass
class ChimeUser:
    """User Chime."""
    user_id: str
    account_id: str = ""
    primary_email: str = ""
    primary_provisioned_number: str = ""
    display_name: str = ""
    license_type: str = "Pro"
    user_type: str = "PrivateUser"
    user_registration_status: str = "Registered"
    user_invitation_status: str = ""
    registered_on: Optional[datetime] = None
    invited_on: Optional[datetime] = None
    alexa_for_business_metadata: Dict[str, Any] = field(default_factory=dict)
    personal_pin: str = ""

    @property
    def is_registered(self) -> bool:
        """Verifica se está registrado."""
        return self.user_registration_status == "Registered"

    @property
    def is_unregistered(self) -> bool:
        """Verifica se não está registrado."""
        return self.user_registration_status == "Unregistered"

    @property
    def is_suspended(self) -> bool:
        """Verifica se está suspenso."""
        return self.user_registration_status == "Suspended"

    @property
    def uses_pro_license(self) -> bool:
        """Verifica se usa licença Pro."""
        return self.license_type == "Pro"

    @property
    def uses_basic_license(self) -> bool:
        """Verifica se usa licença Basic."""
        return self.license_type == "Basic"

    @property
    def uses_plus_license(self) -> bool:
        """Verifica se usa licença Plus."""
        return self.license_type == "Plus"

    @property
    def is_private_user(self) -> bool:
        """Verifica se é usuário privado."""
        return self.user_type == "PrivateUser"

    @property
    def is_shared_device(self) -> bool:
        """Verifica se é dispositivo compartilhado."""
        return self.user_type == "SharedDevice"

    @property
    def has_phone_number(self) -> bool:
        """Verifica se tem número de telefone."""
        return bool(self.primary_provisioned_number)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "user_id": self.user_id,
            "account_id": self.account_id,
            "primary_email": self.primary_email,
            "display_name": self.display_name,
            "license_type": self.license_type,
            "user_type": self.user_type,
            "is_registered": self.is_registered,
            "uses_pro_license": self.uses_pro_license,
            "has_phone_number": self.has_phone_number,
            "registered_on": self.registered_on.isoformat() if self.registered_on else None
        }


@dataclass
class ChimePhoneNumber:
    """Phone Number Chime."""
    phone_number_id: str
    e164_phone_number: str = ""
    country: str = ""
    type: str = "Local"
    product_type: str = "BusinessCalling"
    status: str = "Unassigned"
    calling_name: str = ""
    calling_name_status: str = ""
    created_timestamp: Optional[datetime] = None
    updated_timestamp: Optional[datetime] = None
    deletion_timestamp: Optional[datetime] = None
    order_id: str = ""

    @property
    def is_assigned(self) -> bool:
        """Verifica se está atribuído."""
        return self.status == "Assigned"

    @property
    def is_unassigned(self) -> bool:
        """Verifica se não está atribuído."""
        return self.status == "Unassigned"

    @property
    def is_deleted(self) -> bool:
        """Verifica se foi deletado."""
        return self.status == "Deleted"

    @property
    def is_release_in_progress(self) -> bool:
        """Verifica se está em processo de liberação."""
        return self.status == "ReleaseInProgress"

    @property
    def is_local(self) -> bool:
        """Verifica se é local."""
        return self.type == "Local"

    @property
    def is_toll_free(self) -> bool:
        """Verifica se é toll-free."""
        return self.type == "TollFree"

    @property
    def is_business_calling(self) -> bool:
        """Verifica se é business calling."""
        return self.product_type == "BusinessCalling"

    @property
    def is_voice_connector(self) -> bool:
        """Verifica se é voice connector."""
        return self.product_type == "VoiceConnector"

    @property
    def is_sip_media_app(self) -> bool:
        """Verifica se é SIP media app."""
        return self.product_type == "SipMediaApplicationDialIn"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "phone_number_id": self.phone_number_id,
            "e164_phone_number": self.e164_phone_number,
            "country": self.country,
            "type": self.type,
            "product_type": self.product_type,
            "status": self.status,
            "is_assigned": self.is_assigned,
            "is_local": self.is_local,
            "is_toll_free": self.is_toll_free,
            "created_timestamp": self.created_timestamp.isoformat() if self.created_timestamp else None
        }


class ChimeService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Chime."""

    def __init__(self, client_factory):
        """Inicializa o serviço Chime."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._chime_client = None

    @property
    def chime_client(self):
        """Cliente Chime com lazy loading."""
        if self._chime_client is None:
            self._chime_client = self._client_factory.get_client('chime')
        return self._chime_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Chime."""
        try:
            self.chime_client.list_accounts(MaxResults=1)
            return {
                "service": "chime",
                "status": "healthy",
                "message": "Chime service is accessible"
            }
        except Exception as e:
            return {
                "service": "chime",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_accounts(self) -> List[ChimeAccount]:
        """Lista accounts."""
        accounts = []
        try:
            paginator = self.chime_client.get_paginator('list_accounts')
            for page in paginator.paginate():
                for acc in page.get('Accounts', []):
                    accounts.append(ChimeAccount(
                        account_id=acc.get('AccountId', ''),
                        name=acc.get('Name', ''),
                        account_type=acc.get('AccountType', 'Team'),
                        created_timestamp=acc.get('CreatedTimestamp'),
                        default_license=acc.get('DefaultLicense', 'Pro'),
                        supported_licenses=acc.get('SupportedLicenses', []),
                        account_status=acc.get('AccountStatus', 'Active'),
                        signin_delegate_groups=acc.get('SigninDelegateGroups', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar accounts: {e}")
        return accounts

    def get_phone_numbers(self) -> List[ChimePhoneNumber]:
        """Lista phone numbers."""
        phone_numbers = []
        try:
            paginator = self.chime_client.get_paginator('list_phone_numbers')
            for page in paginator.paginate():
                for pn in page.get('PhoneNumbers', []):
                    phone_numbers.append(ChimePhoneNumber(
                        phone_number_id=pn.get('PhoneNumberId', ''),
                        e164_phone_number=pn.get('E164PhoneNumber', ''),
                        country=pn.get('Country', ''),
                        type=pn.get('Type', 'Local'),
                        product_type=pn.get('ProductType', 'BusinessCalling'),
                        status=pn.get('Status', 'Unassigned'),
                        calling_name=pn.get('CallingName', ''),
                        calling_name_status=pn.get('CallingNameStatus', ''),
                        created_timestamp=pn.get('CreatedTimestamp'),
                        updated_timestamp=pn.get('UpdatedTimestamp'),
                        deletion_timestamp=pn.get('DeletionTimestamp'),
                        order_id=pn.get('OrderId', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar phone numbers: {e}")
        return phone_numbers

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Chime."""
        accounts = self.get_accounts()
        phone_numbers = self.get_phone_numbers()

        return {
            "accounts": [a.to_dict() for a in accounts],
            "phone_numbers": [pn.to_dict() for pn in phone_numbers],
            "summary": {
                "total_accounts": len(accounts),
                "active_accounts": len([a for a in accounts if a.is_active]),
                "suspended_accounts": len([a for a in accounts if a.is_suspended]),
                "team_accounts": len([a for a in accounts if a.is_team]),
                "enterprise_accounts": len([a for a in accounts if a.is_enterprise_directory or a.is_enterprise_lwp]),
                "total_phone_numbers": len(phone_numbers),
                "assigned_phone_numbers": len([pn for pn in phone_numbers if pn.is_assigned]),
                "unassigned_phone_numbers": len([pn for pn in phone_numbers if pn.is_unassigned]),
                "local_numbers": len([pn for pn in phone_numbers if pn.is_local]),
                "toll_free_numbers": len([pn for pn in phone_numbers if pn.is_toll_free])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Chime."""
        accounts = self.get_accounts()
        phone_numbers = self.get_phone_numbers()

        return {
            "accounts_count": len(accounts),
            "active_accounts": len([a for a in accounts if a.is_active]),
            "suspended_accounts": len([a for a in accounts if a.is_suspended]),
            "team_accounts": len([a for a in accounts if a.is_team]),
            "pro_license_accounts": len([a for a in accounts if a.uses_pro_license]),
            "basic_license_accounts": len([a for a in accounts if a.uses_basic_license]),
            "phone_numbers_count": len(phone_numbers),
            "assigned_phone_numbers": len([pn for pn in phone_numbers if pn.is_assigned]),
            "unassigned_phone_numbers": len([pn for pn in phone_numbers if pn.is_unassigned]),
            "local_numbers": len([pn for pn in phone_numbers if pn.is_local]),
            "toll_free_numbers": len([pn for pn in phone_numbers if pn.is_toll_free]),
            "business_calling_numbers": len([pn for pn in phone_numbers if pn.is_business_calling]),
            "voice_connector_numbers": len([pn for pn in phone_numbers if pn.is_voice_connector])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Chime."""
        recommendations = []
        accounts = self.get_accounts()
        phone_numbers = self.get_phone_numbers()

        unassigned = [pn for pn in phone_numbers if pn.is_unassigned]
        if unassigned:
            recommendations.append({
                "resource_type": "ChimePhoneNumber",
                "resource_id": "multiple",
                "recommendation": "Liberar números não utilizados",
                "description": f"{len(unassigned)} número(s) de telefone não atribuído(s). "
                               "Considerar liberar para economizar custos.",
                "priority": "medium"
            })

        suspended = [a for a in accounts if a.is_suspended]
        if suspended:
            recommendations.append({
                "resource_type": "ChimeAccount",
                "resource_id": "multiple",
                "recommendation": "Remover contas suspensas",
                "description": f"{len(suspended)} conta(s) suspensa(s). "
                               "Considerar remover se não forem mais necessárias.",
                "priority": "low"
            })

        return recommendations
