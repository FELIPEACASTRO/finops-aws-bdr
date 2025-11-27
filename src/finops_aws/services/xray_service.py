"""
AWS X-Ray FinOps Service.

Análise de custos e métricas do AWS X-Ray para distributed tracing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class XRayGroup:
    """Representa um grupo X-Ray."""
    
    group_name: str = ""
    group_arn: str = ""
    filter_expression: str = ""
    insights_configuration: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def has_insights(self) -> bool:
        """Verifica se tem Insights habilitado."""
        return bool(self.insights_configuration.get("InsightsEnabled", False))
    
    @property
    def has_notifications(self) -> bool:
        """Verifica se tem notificações habilitadas."""
        return bool(self.insights_configuration.get("NotificationsEnabled", False))
    
    @property
    def has_filter(self) -> bool:
        """Verifica se tem filtro."""
        return bool(self.filter_expression)
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "group_name": self.group_name,
            "group_arn": self.group_arn,
            "filter_expression": self.filter_expression,
            "has_insights": self.has_insights,
            "has_notifications": self.has_notifications,
            "has_filter": self.has_filter,
            "has_tags": self.has_tags
        }


@dataclass
class XRaySamplingRule:
    """Representa uma regra de sampling X-Ray."""
    
    rule_name: str = ""
    rule_arn: str = ""
    priority: int = 0
    fixed_rate: float = 0.0
    reservoir_size: int = 0
    service_name: str = ""
    service_type: str = ""
    host: str = ""
    http_method: str = ""
    url_path: str = ""
    version: int = 1
    attributes: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_default_rule(self) -> bool:
        """Verifica se é regra padrão."""
        return self.rule_name.lower() == "default"
    
    @property
    def has_low_sampling(self) -> bool:
        """Verifica se tem baixa taxa de sampling."""
        return self.fixed_rate < 0.1
    
    @property
    def has_high_sampling(self) -> bool:
        """Verifica se tem alta taxa de sampling."""
        return self.fixed_rate >= 0.5
    
    @property
    def has_reservoir(self) -> bool:
        """Verifica se tem reservoir."""
        return self.reservoir_size > 0
    
    @property
    def has_attributes(self) -> bool:
        """Verifica se tem atributos."""
        return bool(self.attributes)
    
    @property
    def is_wildcard(self) -> bool:
        """Verifica se usa wildcard."""
        return self.service_name == "*" or self.host == "*"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "rule_name": self.rule_name,
            "rule_arn": self.rule_arn,
            "priority": self.priority,
            "fixed_rate": self.fixed_rate,
            "reservoir_size": self.reservoir_size,
            "is_default_rule": self.is_default_rule,
            "has_low_sampling": self.has_low_sampling,
            "has_high_sampling": self.has_high_sampling
        }


@dataclass
class XRayEncryptionConfig:
    """Representa configuração de criptografia X-Ray."""
    
    key_id: str = ""
    status: str = ""
    type: str = ""
    
    @property
    def is_active(self) -> bool:
        """Verifica se criptografia está ativa."""
        return self.status.upper() == "ACTIVE"
    
    @property
    def is_updating(self) -> bool:
        """Verifica se está atualizando."""
        return self.status.upper() == "UPDATING"
    
    @property
    def uses_kms(self) -> bool:
        """Verifica se usa KMS."""
        return self.type.upper() == "KMS"
    
    @property
    def uses_default(self) -> bool:
        """Verifica se usa criptografia padrão."""
        return self.type.upper() == "NONE" or not self.key_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "key_id": self.key_id,
            "status": self.status,
            "type": self.type,
            "is_active": self.is_active,
            "uses_kms": self.uses_kms
        }


class XRayService(BaseAWSService):
    """Serviço FinOps para AWS X-Ray."""

    def __init__(self, client_factory):
        """Inicializa o serviço X-Ray."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente X-Ray."""
        return self._client_factory.get_client("xray")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.get_sampling_rules()
            return {"status": "healthy", "service": "xray"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "xray", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos X-Ray."""
        client = self._get_client()
        
        groups = self._list_groups(client)
        sampling_rules = self._list_sampling_rules(client)
        encryption = self._get_encryption_config(client)
        
        return {
            "groups": [g.to_dict() for g in groups],
            "sampling_rules": [r.to_dict() for r in sampling_rules],
            "encryption_config": encryption.to_dict() if encryption else {},
            "summary": {
                "total_groups": len(groups),
                "total_sampling_rules": len(sampling_rules),
                "groups_with_insights": len([g for g in groups if g.has_insights]),
                "high_sampling_rules": len([r for r in sampling_rules if r.has_high_sampling])
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos X-Ray."""
        resources = self.get_resources()
        
        return {
            "estimated_monthly": 0.0,
            "cost_factors": {
                "traces_recorded": "based on volume",
                "traces_scanned": "based on volume",
                "insights_enabled": resources["summary"]["groups_with_insights"]
            },
            "optimization_potential": self._calculate_optimization_potential(resources)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas X-Ray."""
        resources = self.get_resources()
        
        return {
            "groups_count": resources["summary"]["total_groups"],
            "sampling_rules_count": resources["summary"]["total_sampling_rules"],
            "groups_with_insights": resources["summary"]["groups_with_insights"],
            "high_sampling_rules": resources["summary"]["high_sampling_rules"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de otimização."""
        recommendations = []
        resources = self.get_resources()
        
        for rule in resources["sampling_rules"]:
            if rule.get("has_high_sampling") and not rule.get("is_default_rule"):
                recommendations.append({
                    "type": "REDUCE_SAMPLING_RATE",
                    "resource": rule["rule_name"],
                    "description": f"Regra '{rule['rule_name']}' tem alta taxa de sampling ({rule['fixed_rate']*100}%)",
                    "impact": "medium",
                    "estimated_savings": "10-50% em custos de X-Ray"
                })
        
        return recommendations

    def _list_groups(self, client) -> List[XRayGroup]:
        """Lista grupos X-Ray."""
        groups = []
        try:
            paginator = client.get_paginator("get_groups")
            for page in paginator.paginate():
                for group in page.get("Groups", []):
                    groups.append(XRayGroup(
                        group_name=group.get("GroupName", ""),
                        group_arn=group.get("GroupARN", ""),
                        filter_expression=group.get("FilterExpression", ""),
                        insights_configuration=group.get("InsightsConfiguration", {})
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing X-Ray groups: {e}")
        return groups

    def _list_sampling_rules(self, client) -> List[XRaySamplingRule]:
        """Lista regras de sampling."""
        rules = []
        try:
            paginator = client.get_paginator("get_sampling_rules")
            for page in paginator.paginate():
                for record in page.get("SamplingRuleRecords", []):
                    rule = record.get("SamplingRule", {})
                    rules.append(XRaySamplingRule(
                        rule_name=rule.get("RuleName", ""),
                        rule_arn=rule.get("RuleARN", ""),
                        priority=rule.get("Priority", 0),
                        fixed_rate=rule.get("FixedRate", 0.0),
                        reservoir_size=rule.get("ReservoirSize", 0),
                        service_name=rule.get("ServiceName", ""),
                        service_type=rule.get("ServiceType", ""),
                        host=rule.get("Host", ""),
                        http_method=rule.get("HTTPMethod", ""),
                        url_path=rule.get("URLPath", ""),
                        version=rule.get("Version", 1),
                        attributes=rule.get("Attributes", {})
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing sampling rules: {e}")
        return rules

    def _get_encryption_config(self, client) -> Optional[XRayEncryptionConfig]:
        """Obtém configuração de criptografia."""
        try:
            response = client.get_encryption_config()
            config = response.get("EncryptionConfig", {})
            return XRayEncryptionConfig(
                key_id=config.get("KeyId", ""),
                status=config.get("Status", ""),
                type=config.get("Type", "")
            )
        except Exception as e:
            self.logger.warning(f"Error getting encryption config: {e}")
            return None

    def _calculate_optimization_potential(self, resources: Dict) -> str:
        """Calcula potencial de otimização."""
        high_sampling = resources["summary"]["high_sampling_rules"]
        if high_sampling > 2:
            return "high"
        elif high_sampling > 0:
            return "medium"
        return "low"
