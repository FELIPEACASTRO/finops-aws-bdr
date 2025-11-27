"""AWS Organizations Service - Gerenciamento multi-conta."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Organization:
    """Representa uma organização AWS."""
    arn: str
    id: str
    root_id: str
    master_account_id: str
    master_account_email: str
    feature_set: str = "ALL"

    @property
    def is_all_features(self) -> bool:
        return self.feature_set == "ALL"

    @property
    def is_consolidated_billing(self) -> bool:
        return self.feature_set == "CONSOLIDATED_BILLING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "arn": self.arn,
            "master_account_id": self.master_account_id,
            "feature_set": self.feature_set,
            "is_all_features": self.is_all_features,
        }


@dataclass
class Account:
    """Representa uma conta na organização."""
    id: str
    name: str
    email: str
    arn: str
    status: str = "ACTIVE"
    joined_method: str = "CREATED"
    joined_timestamp: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    @property
    def is_suspended(self) -> bool:
        return self.status == "SUSPENDED"

    @property
    def is_created(self) -> bool:
        return self.joined_method == "CREATED"

    @property
    def is_invited(self) -> bool:
        return self.joined_method == "INVITED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "is_active": self.is_active,
        }


@dataclass
class OrganizationalUnit:
    """Representa uma unidade organizacional."""
    id: str
    name: str
    arn: str
    parent_id: str
    account_count: int = 0

    @property
    def is_root(self) -> bool:
        return self.name == "Root"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arn": self.arn,
            "account_count": self.account_count,
            "is_root": self.is_root,
        }


class OrganizationsService(BaseAWSService):
    """Serviço Organizations para gerenciamento multi-conta."""

    def __init__(self, client_factory):
        super().__init__()
        self._client_factory = client_factory

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._client_factory.get_client("organizations")
            client.describe_organization()
            return {"status": "healthy"}
        except Exception as e:
            logger.error(f"Organizations health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém organização e contas."""
        try:
            client = self._client_factory.get_client("organizations")
            
            org_data = client.describe_organization().get("Organization", {})
            org = Organization(
                arn=org_data.get("Arn", ""),
                id=org_data.get("Id", ""),
                root_id=org_data.get("RootId", ""),
                master_account_id=org_data.get("MasterAccountId", ""),
                master_account_email=org_data.get("MasterAccountEmail", ""),
                feature_set=org_data.get("FeatureSet", "ALL"),
            )
            
            accounts = []
            paginator = client.get_paginator("list_accounts")
            for page in paginator.paginate():
                for acc_data in page.get("Accounts", []):
                    account = Account(
                        id=acc_data.get("Id", ""),
                        name=acc_data.get("Name", ""),
                        email=acc_data.get("Email", ""),
                        arn=acc_data.get("Arn", ""),
                        status=acc_data.get("Status", "ACTIVE"),
                        joined_method=acc_data.get("JoinedMethod", "CREATED"),
                        joined_timestamp=acc_data.get("JoinedTimestamp"),
                    )
                    accounts.append(account)
            
            return {
                "organization": org,
                "accounts": accounts,
                "account_count": len(accounts),
            }
        except Exception as e:
            logger.error(f"Error getting Organizations resources: {str(e)}")
            return {"organization": None, "accounts": [], "account_count": 0, "error": str(e)}

    def get_costs(self) -> Dict[str, Any]:
        """Calcula custos consolidados."""
        try:
            resources = self.get_resources()
            accounts = resources.get("accounts", [])
            
            consolidated_cost = len(accounts) * 5.0
            
            return {
                "consolidated_billing_cost": consolidated_cost,
                "account_count": len(accounts),
                "active_accounts": sum(1 for a in accounts if a.is_active),
            }
        except Exception as e:
            logger.error(f"Error calculating costs: {str(e)}")
            return {"consolidated_billing_cost": 0, "error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas."""
        resources = self.get_resources()
        accounts = resources.get("accounts", [])
        
        return {
            "total_accounts": len(accounts),
            "active_accounts": sum(1 for a in accounts if a.is_active),
            "suspended_accounts": sum(1 for a in accounts if a.is_suspended),
        }

    def get_recommendations(self) -> Dict[str, Any]:
        """Retorna recomendações."""
        resources = self.get_resources()
        accounts = resources.get("accounts", [])
        
        recommendations = []
        suspended = sum(1 for a in accounts if a.is_suspended)
        
        if suspended > 0:
            recommendations.append({
                "type": "SUSPENDED_ACCOUNTS",
                "description": f"{suspended} contas suspensas",
                "action": "Review and consolidate suspended accounts",
            })
        
        return {"recommendations": recommendations}
