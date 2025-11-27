"""AWS Control Tower Service - Governança centralizada."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ControlTowerEnrolledAccount:
    """Representa uma conta inscrita no Control Tower."""
    account_id: str
    account_name: str
    email: str
    enrollment_status: str = "ENROLLED"
    last_updated: Optional[str] = None

    @property
    def is_enrolled(self) -> bool:
        return self.enrollment_status == "ENROLLED"

    @property
    def is_pending(self) -> bool:
        return self.enrollment_status == "PENDING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "enrollment_status": self.enrollment_status,
            "is_enrolled": self.is_enrolled,
        }


@dataclass
class ControlTowerGuardrail:
    """Representa um guardrail do Control Tower."""
    guardrail_id: str
    name: str
    description: str
    guardrail_type: str
    status: str = "ENABLED"
    compliance_status: str = "COMPLIANT"

    @property
    def is_enabled(self) -> bool:
        return self.status == "ENABLED"

    @property
    def is_disabled(self) -> bool:
        return self.status == "DISABLED"

    @property
    def is_preventive(self) -> bool:
        return self.guardrail_type == "PREVENTIVE"

    @property
    def is_detective(self) -> bool:
        return self.guardrail_type == "DETECTIVE"

    @property
    def is_compliant(self) -> bool:
        return self.compliance_status == "COMPLIANT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guardrail_id": self.guardrail_id,
            "name": self.name,
            "guardrail_type": self.guardrail_type,
            "status": self.status,
            "compliance_status": self.compliance_status,
            "is_compliant": self.is_compliant,
        }


class ControlTowerService(BaseAWSService):
    """Serviço Control Tower para governança centralizada."""

    def __init__(self, client_factory):
        super().__init__()
        self._client_factory = client_factory

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._client_factory.get_client("controltower")
            client.describe_landing_zone_configuration()
            return {"status": "healthy"}
        except Exception as e:
            logger.error(f"Control Tower health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém contas e guardrails."""
        try:
            client = self._client_factory.get_client("controltower")
            
            accounts = []
            guardrails = []
            
            try:
                enrolled_response = client.list_enrolled_accounts()
                for acc_data in enrolled_response.get("enrolledAccounts", []):
                    account = ControlTowerEnrolledAccount(
                        account_id=acc_data.get("AccountId", ""),
                        account_name=acc_data.get("AccountName", ""),
                        email=acc_data.get("Email", ""),
                        enrollment_status=acc_data.get("EnrollmentStatus", "ENROLLED"),
                    )
                    accounts.append(account)
            except Exception as e:
                logger.warning(f"Could not list enrolled accounts: {str(e)}")
            
            try:
                guardrails_response = client.list_guardrails()
                for gr_data in guardrails_response.get("guardrailSummaries", []):
                    guardrail = ControlTowerGuardrail(
                        guardrail_id=gr_data.get("GuardrailId", ""),
                        name=gr_data.get("Name", ""),
                        description=gr_data.get("Description", ""),
                        guardrail_type=gr_data.get("GuardrailType", ""),
                        status=gr_data.get("Status", "ENABLED"),
                    )
                    guardrails.append(guardrail)
            except Exception as e:
                logger.warning(f"Could not list guardrails: {str(e)}")
            
            return {
                "accounts": accounts,
                "account_count": len(accounts),
                "guardrails": guardrails,
                "guardrail_count": len(guardrails),
            }
        except Exception as e:
            logger.error(f"Error getting Control Tower resources: {str(e)}")
            return {
                "accounts": [],
                "account_count": 0,
                "guardrails": [],
                "guardrail_count": 0,
                "error": str(e),
            }

    def get_costs(self) -> Dict[str, Any]:
        """Calcula custos de governança."""
        try:
            resources = self.get_resources()
            accounts = resources.get("accounts", [])
            
            cost_per_account = 100.0
            total_cost = len(accounts) * cost_per_account
            
            return {
                "monthly_governance_cost": total_cost,
                "account_count": len(accounts),
                "cost_per_account": cost_per_account,
            }
        except Exception as e:
            logger.error(f"Error calculating costs: {str(e)}")
            return {"monthly_governance_cost": 0, "error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas."""
        resources = self.get_resources()
        accounts = resources.get("accounts", [])
        guardrails = resources.get("guardrails", [])
        
        return {
            "enrolled_accounts": len(accounts),
            "total_guardrails": len(guardrails),
            "enabled_guardrails": sum(1 for g in guardrails if g.is_enabled),
            "compliant_guardrails": sum(1 for g in guardrails if g.is_compliant),
        }

    def get_recommendations(self) -> Dict[str, Any]:
        """Retorna recomendações."""
        resources = self.get_resources()
        guardrails = resources.get("guardrails", [])
        
        recommendations = []
        non_compliant = sum(1 for g in guardrails if not g.is_compliant)
        
        if non_compliant > 0:
            recommendations.append({
                "type": "GUARDRAIL_VIOLATION",
                "description": f"{non_compliant} guardrails não conformes",
                "action": "Review and remediate non-compliant guardrails",
            })
        
        return {"recommendations": recommendations}
