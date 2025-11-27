"""
AWS Security Hub FinOps Service.

Análise de custos e métricas do AWS Security Hub para segurança centralizada.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class SecurityHubStandard:
    """Representa um padrão de segurança Security Hub."""
    
    standards_arn: str = ""
    standards_subscription_arn: str = ""
    standards_status: str = ""
    standards_status_reason: Dict[str, Any] = field(default_factory=dict)
    enabled_by_default: bool = False
    name: str = ""
    description: str = ""
    
    @property
    def is_ready(self) -> bool:
        """Verifica se padrão está pronto."""
        return self.standards_status.upper() == "READY"
    
    @property
    def is_pending(self) -> bool:
        """Verifica se padrão está pendente."""
        return self.standards_status.upper() == "PENDING"
    
    @property
    def is_incomplete(self) -> bool:
        """Verifica se padrão está incompleto."""
        return self.standards_status.upper() == "INCOMPLETE"
    
    @property
    def is_deleting(self) -> bool:
        """Verifica se padrão está sendo deletado."""
        return self.standards_status.upper() == "DELETING"
    
    @property
    def is_failed(self) -> bool:
        """Verifica se padrão falhou."""
        return self.standards_status.upper() == "FAILED"
    
    @property
    def has_status_reason(self) -> bool:
        """Verifica se tem razão de status."""
        return bool(self.standards_status_reason)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "standards_arn": self.standards_arn,
            "name": self.name,
            "standards_status": self.standards_status,
            "is_ready": self.is_ready,
            "is_failed": self.is_failed,
            "enabled_by_default": self.enabled_by_default
        }


@dataclass
class SecurityHubFinding:
    """Representa um finding Security Hub."""
    
    id: str = ""
    product_arn: str = ""
    generator_id: str = ""
    aws_account_id: str = ""
    types: List[str] = field(default_factory=list)
    severity: Dict[str, Any] = field(default_factory=dict)
    title: str = ""
    description: str = ""
    workflow: Dict[str, Any] = field(default_factory=dict)
    record_state: str = ""
    compliance: Dict[str, Any] = field(default_factory=dict)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def severity_label(self) -> str:
        """Retorna label de severidade."""
        return self.severity.get("Label", "INFORMATIONAL")
    
    @property
    def is_critical(self) -> bool:
        """Verifica se é crítico."""
        return self.severity_label.upper() == "CRITICAL"
    
    @property
    def is_high(self) -> bool:
        """Verifica se é alto."""
        return self.severity_label.upper() == "HIGH"
    
    @property
    def is_medium(self) -> bool:
        """Verifica se é médio."""
        return self.severity_label.upper() == "MEDIUM"
    
    @property
    def is_low(self) -> bool:
        """Verifica se é baixo."""
        return self.severity_label.upper() == "LOW"
    
    @property
    def is_informational(self) -> bool:
        """Verifica se é informacional."""
        return self.severity_label.upper() == "INFORMATIONAL"
    
    @property
    def workflow_status(self) -> str:
        """Retorna status do workflow."""
        return self.workflow.get("Status", "NEW")
    
    @property
    def is_new(self) -> bool:
        """Verifica se é novo."""
        return self.workflow_status.upper() == "NEW"
    
    @property
    def is_notified(self) -> bool:
        """Verifica se foi notificado."""
        return self.workflow_status.upper() == "NOTIFIED"
    
    @property
    def is_resolved(self) -> bool:
        """Verifica se foi resolvido."""
        return self.workflow_status.upper() == "RESOLVED"
    
    @property
    def is_suppressed(self) -> bool:
        """Verifica se foi suprimido."""
        return self.workflow_status.upper() == "SUPPRESSED"
    
    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.record_state.upper() == "ACTIVE"
    
    @property
    def is_archived(self) -> bool:
        """Verifica se está arquivado."""
        return self.record_state.upper() == "ARCHIVED"
    
    @property
    def compliance_status(self) -> str:
        """Retorna status de compliance."""
        return self.compliance.get("Status", "UNKNOWN")
    
    @property
    def is_passed(self) -> bool:
        """Verifica se passou compliance."""
        return self.compliance_status.upper() == "PASSED"
    
    @property
    def is_failed_compliance(self) -> bool:
        """Verifica se falhou compliance."""
        return self.compliance_status.upper() == "FAILED"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "title": self.title,
            "severity_label": self.severity_label,
            "is_critical": self.is_critical,
            "is_high": self.is_high,
            "workflow_status": self.workflow_status,
            "is_active": self.is_active,
            "compliance_status": self.compliance_status
        }


@dataclass 
class SecurityHubInsight:
    """Representa um insight Security Hub."""
    
    insight_arn: str = ""
    name: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)
    group_by_attribute: str = ""
    
    @property
    def has_filters(self) -> bool:
        """Verifica se tem filtros."""
        return bool(self.filters)
    
    @property
    def has_group_by(self) -> bool:
        """Verifica se tem group by."""
        return bool(self.group_by_attribute)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "insight_arn": self.insight_arn,
            "name": self.name,
            "group_by_attribute": self.group_by_attribute,
            "has_filters": self.has_filters
        }


class SecurityHubService(BaseAWSService):
    """Serviço FinOps para AWS Security Hub."""

    def __init__(self, client_factory):
        """Inicializa o serviço Security Hub."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente Security Hub."""
        return self._client_factory.get_client("securityhub")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.describe_hub()
            return {"status": "healthy", "service": "securityhub"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "securityhub", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos Security Hub."""
        client = self._get_client()
        
        standards = self._list_standards(client)
        insights = self._list_insights(client)
        findings_summary = self._get_findings_summary(client)
        
        return {
            "standards": [s.to_dict() for s in standards],
            "insights": [i.to_dict() for i in insights],
            "findings_summary": findings_summary,
            "summary": {
                "total_standards": len(standards),
                "ready_standards": len([s for s in standards if s.is_ready]),
                "total_insights": len(insights),
                "critical_findings": findings_summary.get("critical", 0),
                "high_findings": findings_summary.get("high", 0)
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos Security Hub."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        standards_cost = summary["ready_standards"] * 0.0010
        findings_cost = (summary["critical_findings"] + summary["high_findings"]) * 0.00003
        
        return {
            "estimated_monthly": standards_cost + findings_cost,
            "cost_factors": {
                "security_checks": "$0.0010 per check per account",
                "findings_ingested": "$0.00003 per finding",
                "automation_rules": "Included"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas Security Hub."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "standards_count": summary["total_standards"],
            "ready_standards": summary["ready_standards"],
            "insights_count": summary["total_insights"],
            "critical_findings": summary["critical_findings"],
            "high_findings": summary["high_findings"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de segurança."""
        recommendations = []
        resources = self.get_resources()
        
        for standard in resources["standards"]:
            if standard.get("is_failed"):
                recommendations.append({
                    "type": "FIX_FAILED_STANDARD",
                    "resource": standard["name"],
                    "description": f"Padrão '{standard['name']}' falhou na habilitação",
                    "impact": "high",
                    "action": "Verificar e corrigir configuração do padrão"
                })
        
        if resources["findings_summary"].get("critical", 0) > 0:
            recommendations.append({
                "type": "ADDRESS_CRITICAL_FINDINGS",
                "resource": "Security Hub",
                "description": f"{resources['findings_summary']['critical']} findings críticos encontrados",
                "impact": "critical",
                "action": "Revisar e remediar findings críticos imediatamente"
            })
        
        return recommendations

    def _list_standards(self, client) -> List[SecurityHubStandard]:
        """Lista padrões de segurança."""
        standards = []
        try:
            paginator = client.get_paginator("get_enabled_standards")
            for page in paginator.paginate():
                for std in page.get("StandardsSubscriptions", []):
                    standards.append(SecurityHubStandard(
                        standards_arn=std.get("StandardsArn", ""),
                        standards_subscription_arn=std.get("StandardsSubscriptionArn", ""),
                        standards_status=std.get("StandardsStatus", ""),
                        standards_status_reason=std.get("StandardsStatusReason", {})
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing standards: {e}")
        return standards

    def _list_insights(self, client) -> List[SecurityHubInsight]:
        """Lista insights."""
        insights = []
        try:
            paginator = client.get_paginator("get_insights")
            for page in paginator.paginate():
                for insight in page.get("Insights", []):
                    insights.append(SecurityHubInsight(
                        insight_arn=insight.get("InsightArn", ""),
                        name=insight.get("Name", ""),
                        filters=insight.get("Filters", {}),
                        group_by_attribute=insight.get("GroupByAttribute", "")
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing insights: {e}")
        return insights

    def _get_findings_summary(self, client) -> Dict[str, int]:
        """Obtém resumo de findings."""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        try:
            response = client.get_findings(
                Filters={"RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]},
                MaxResults=100
            )
            for finding in response.get("Findings", []):
                severity = finding.get("Severity", {}).get("Label", "").lower()
                if severity in summary:
                    summary[severity] += 1
        except Exception as e:
            self.logger.warning(f"Error getting findings summary: {e}")
        return summary
