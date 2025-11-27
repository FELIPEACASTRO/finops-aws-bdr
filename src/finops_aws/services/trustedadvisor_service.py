"""AWS Trusted Advisor Service - Otimização e recomendações."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class TrustedAdvisorCheck:
    """Representa uma verificação Trusted Advisor."""
    check_id: str
    name: str
    description: str
    category: str
    metadata: List[str]
    resources_summary: Dict[str, int]
    resource_flagged_count: int = 0
    resource_processed_count: int = 0
    resource_suppressed_count: int = 0
    status: str = "unknown"
    timestamp: Optional[str] = None
    flagged_resources: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.flagged_resources is None:
            self.flagged_resources = []

    @property
    def is_warning(self) -> bool:
        return self.status == "warning"

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    @property
    def has_flagged_resources(self) -> bool:
        return self.resource_flagged_count > 0

    @property
    def cost_optimized(self) -> bool:
        return self.category == "cost_optimizing" and self.is_ok

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "flagged_resources": self.resource_flagged_count,
            "has_issues": self.has_flagged_resources,
        }


class TrustedAdvisorService(BaseAWSService):
    """Serviço Trusted Advisor para otimização AWS."""

    def __init__(self, client_factory):
        super().__init__()
        self._client_factory = client_factory

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._client_factory.get_client("support")
            client.describe_trusted_advisor_checks()
            return {"status": "healthy"}
        except Exception as e:
            logger.error(f"Trusted Advisor health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém verificações Trusted Advisor."""
        try:
            client = self._client_factory.get_client("support")
            
            checks = client.describe_trusted_advisor_checks().get("checks", [])
            
            advisor_checks = []
            for check_data in checks:
                check = TrustedAdvisorCheck(
                    check_id=check_data.get("id", ""),
                    name=check_data.get("name", ""),
                    description=check_data.get("description", ""),
                    category=check_data.get("category", ""),
                    metadata=check_data.get("metadata", []),
                    resources_summary=check_data.get("resourcesSummary", {}),
                )
                advisor_checks.append(check)

            return {
                "checks": advisor_checks,
                "check_count": len(advisor_checks),
            }
        except Exception as e:
            logger.error(f"Error getting Trusted Advisor resources: {str(e)}")
            return {"checks": [], "check_count": 0, "error": str(e)}

    def get_costs(self) -> Dict[str, Any]:
        """Calcula economia potencial."""
        try:
            resources = self.get_resources()
            checks = resources.get("checks", [])
            
            total_savings = 0.0
            for check in checks:
                if "flagged_resources" in check.__dict__:
                    total_savings += len(check.flagged_resources) * 10.0
            
            return {
                "estimated_monthly_savings": total_savings,
                "check_count": len(checks),
            }
        except Exception as e:
            logger.error(f"Error calculating costs: {str(e)}")
            return {"estimated_monthly_savings": 0, "error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas."""
        resources = self.get_resources()
        return {
            "total_checks": len(resources.get("checks", [])),
            "warning_checks": sum(1 for c in resources.get("checks", []) if c.is_warning),
            "error_checks": sum(1 for c in resources.get("checks", []) if c.is_error),
        }

    def get_recommendations(self) -> Dict[str, Any]:
        """Retorna recomendações."""
        resources = self.get_resources()
        checks = resources.get("checks", [])
        
        recommendations = []
        for check in checks:
            if check.is_warning or check.is_error:
                recommendations.append({
                    "check": check.name,
                    "status": check.status,
                    "action": f"Review {check.name} for optimization",
                })
        
        return {"recommendations": recommendations}
