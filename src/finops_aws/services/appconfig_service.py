"""
AWS AppConfig FinOps Service.

Análise de custos e métricas do AWS AppConfig para feature flags e configurações.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class AppConfigApplication:
    """Representa uma aplicação AppConfig."""
    
    id: str = ""
    name: str = ""
    description: str = ""
    
    @property
    def has_description(self) -> bool:
        """Verifica se tem descrição."""
        return bool(self.description)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "has_description": self.has_description
        }


@dataclass
class AppConfigEnvironment:
    """Representa um ambiente AppConfig."""
    
    application_id: str = ""
    id: str = ""
    name: str = ""
    description: str = ""
    state: str = ""
    monitors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def is_ready(self) -> bool:
        """Verifica se ambiente está pronto."""
        return self.state.upper() == "READY_FOR_DEPLOYMENT"
    
    @property
    def is_deploying(self) -> bool:
        """Verifica se está em deploy."""
        return self.state.upper() == "DEPLOYING"
    
    @property
    def is_rolled_back(self) -> bool:
        """Verifica se foi rolled back."""
        return self.state.upper() == "ROLLED_BACK"
    
    @property
    def has_monitors(self) -> bool:
        """Verifica se tem monitores."""
        return bool(self.monitors)
    
    @property
    def monitors_count(self) -> int:
        """Retorna quantidade de monitores."""
        return len(self.monitors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "application_id": self.application_id,
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "is_ready": self.is_ready,
            "has_monitors": self.has_monitors,
            "monitors_count": self.monitors_count
        }


@dataclass
class AppConfigProfile:
    """Representa um perfil de configuração AppConfig."""
    
    application_id: str = ""
    id: str = ""
    name: str = ""
    description: str = ""
    location_uri: str = ""
    retrieval_role_arn: str = ""
    validators: List[Dict[str, Any]] = field(default_factory=list)
    type: str = ""
    kms_key_identifier: str = ""
    
    @property
    def is_freeform(self) -> bool:
        """Verifica se é tipo freeform."""
        return self.type.upper() == "AWS.FREEFORM"
    
    @property
    def is_feature_flags(self) -> bool:
        """Verifica se é feature flags."""
        return self.type.upper() == "AWS.APPCONFIG.FEATUREFLAGS"
    
    @property
    def uses_ssm(self) -> bool:
        """Verifica se usa SSM."""
        return "ssm-document" in self.location_uri.lower()
    
    @property
    def uses_s3(self) -> bool:
        """Verifica se usa S3."""
        return "s3://" in self.location_uri.lower()
    
    @property
    def uses_secrets_manager(self) -> bool:
        """Verifica se usa Secrets Manager."""
        return "secretsmanager" in self.location_uri.lower()
    
    @property
    def has_validators(self) -> bool:
        """Verifica se tem validadores."""
        return bool(self.validators)
    
    @property
    def has_kms(self) -> bool:
        """Verifica se usa KMS."""
        return bool(self.kms_key_identifier)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "application_id": self.application_id,
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "is_feature_flags": self.is_feature_flags,
            "has_validators": self.has_validators,
            "has_kms": self.has_kms
        }


@dataclass
class AppConfigDeploymentStrategy:
    """Representa uma estratégia de deployment AppConfig."""
    
    id: str = ""
    name: str = ""
    description: str = ""
    deployment_duration_in_minutes: int = 0
    growth_factor: float = 0.0
    growth_type: str = ""
    final_bake_time_in_minutes: int = 0
    replicate_to: str = ""
    
    @property
    def is_linear(self) -> bool:
        """Verifica se é crescimento linear."""
        return self.growth_type.upper() == "LINEAR"
    
    @property
    def is_exponential(self) -> bool:
        """Verifica se é crescimento exponencial."""
        return self.growth_type.upper() == "EXPONENTIAL"
    
    @property
    def is_all_at_once(self) -> bool:
        """Verifica se é all at once."""
        return self.growth_factor >= 100.0
    
    @property
    def has_bake_time(self) -> bool:
        """Verifica se tem bake time."""
        return self.final_bake_time_in_minutes > 0
    
    @property
    def is_replicated(self) -> bool:
        """Verifica se é replicado."""
        return self.replicate_to.upper() == "SSM_DOCUMENT"
    
    @property
    def total_duration_minutes(self) -> int:
        """Calcula duração total em minutos."""
        return self.deployment_duration_in_minutes + self.final_bake_time_in_minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "deployment_duration_in_minutes": self.deployment_duration_in_minutes,
            "growth_factor": self.growth_factor,
            "growth_type": self.growth_type,
            "is_linear": self.is_linear,
            "is_all_at_once": self.is_all_at_once,
            "total_duration_minutes": self.total_duration_minutes
        }


class AppConfigService(BaseAWSService):
    """Serviço FinOps para AWS AppConfig."""

    def __init__(self, client_factory):
        """Inicializa o serviço AppConfig."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente AppConfig."""
        return self._client_factory.get_client("appconfig")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.list_applications(MaxResults=1)
            return {"status": "healthy", "service": "appconfig"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "appconfig", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos AppConfig."""
        client = self._get_client()
        
        applications = self._list_applications(client)
        environments = self._list_environments(client, applications)
        profiles = self._list_profiles(client, applications)
        strategies = self._list_deployment_strategies(client)
        
        return {
            "applications": [a.to_dict() for a in applications],
            "environments": [e.to_dict() for e in environments],
            "configuration_profiles": [p.to_dict() for p in profiles],
            "deployment_strategies": [s.to_dict() for s in strategies],
            "summary": {
                "total_applications": len(applications),
                "total_environments": len(environments),
                "total_profiles": len(profiles),
                "feature_flags_profiles": len([p for p in profiles if p.is_feature_flags]),
                "total_strategies": len(strategies)
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos AppConfig."""
        resources = self.get_resources()
        
        config_calls = 0
        feature_flag_calls = 0
        
        estimated_cost = (config_calls * 0.0000008) + (feature_flag_calls * 0.000002)
        
        return {
            "estimated_monthly": estimated_cost,
            "cost_factors": {
                "configuration_calls": "$0.0000008 per call",
                "feature_flag_calls": "$0.000002 per call",
                "applications": "No charge for applications",
                "environments": "No charge for environments"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas AppConfig."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "applications_count": summary["total_applications"],
            "environments_count": summary["total_environments"],
            "profiles_count": summary["total_profiles"],
            "feature_flags_profiles": summary["feature_flags_profiles"],
            "strategies_count": summary["total_strategies"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de otimização."""
        recommendations = []
        resources = self.get_resources()
        
        for env in resources["environments"]:
            if not env.get("has_monitors"):
                recommendations.append({
                    "type": "ADD_MONITORS",
                    "resource": env["name"],
                    "description": f"Ambiente '{env['name']}' sem monitores de rollback",
                    "impact": "high",
                    "action": "Adicionar CloudWatch Alarms para rollback automático"
                })
        
        for profile in resources["configuration_profiles"]:
            if not profile.get("has_validators"):
                recommendations.append({
                    "type": "ADD_VALIDATORS",
                    "resource": profile["name"],
                    "description": f"Perfil '{profile['name']}' sem validadores",
                    "impact": "medium",
                    "action": "Adicionar validadores JSON Schema ou Lambda"
                })
        
        return recommendations

    def _list_applications(self, client) -> List[AppConfigApplication]:
        """Lista aplicações AppConfig."""
        applications = []
        try:
            paginator = client.get_paginator("list_applications")
            for page in paginator.paginate():
                for app in page.get("Items", []):
                    applications.append(AppConfigApplication(
                        id=app.get("Id", ""),
                        name=app.get("Name", ""),
                        description=app.get("Description", "")
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing applications: {e}")
        return applications

    def _list_environments(self, client, applications: List[AppConfigApplication]) -> List[AppConfigEnvironment]:
        """Lista ambientes AppConfig."""
        environments = []
        try:
            for app in applications:
                paginator = client.get_paginator("list_environments")
                for page in paginator.paginate(ApplicationId=app.id):
                    for env in page.get("Items", []):
                        environments.append(AppConfigEnvironment(
                            application_id=app.id,
                            id=env.get("Id", ""),
                            name=env.get("Name", ""),
                            description=env.get("Description", ""),
                            state=env.get("State", ""),
                            monitors=env.get("Monitors", [])
                        ))
        except Exception as e:
            self.logger.warning(f"Error listing environments: {e}")
        return environments

    def _list_profiles(self, client, applications: List[AppConfigApplication]) -> List[AppConfigProfile]:
        """Lista perfis de configuração AppConfig."""
        profiles = []
        try:
            for app in applications:
                paginator = client.get_paginator("list_configuration_profiles")
                for page in paginator.paginate(ApplicationId=app.id):
                    for profile in page.get("Items", []):
                        profiles.append(AppConfigProfile(
                            application_id=app.id,
                            id=profile.get("Id", ""),
                            name=profile.get("Name", ""),
                            location_uri=profile.get("LocationUri", ""),
                            validators=profile.get("Validators", []),
                            type=profile.get("Type", ""),
                            kms_key_identifier=profile.get("KmsKeyIdentifier", "")
                        ))
        except Exception as e:
            self.logger.warning(f"Error listing profiles: {e}")
        return profiles

    def _list_deployment_strategies(self, client) -> List[AppConfigDeploymentStrategy]:
        """Lista estratégias de deployment AppConfig."""
        strategies = []
        try:
            paginator = client.get_paginator("list_deployment_strategies")
            for page in paginator.paginate():
                for strategy in page.get("Items", []):
                    strategies.append(AppConfigDeploymentStrategy(
                        id=strategy.get("Id", ""),
                        name=strategy.get("Name", ""),
                        description=strategy.get("Description", ""),
                        deployment_duration_in_minutes=strategy.get("DeploymentDurationInMinutes", 0),
                        growth_factor=strategy.get("GrowthFactor", 0.0),
                        growth_type=strategy.get("GrowthType", ""),
                        final_bake_time_in_minutes=strategy.get("FinalBakeTimeInMinutes", 0),
                        replicate_to=strategy.get("ReplicateTo", "")
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing deployment strategies: {e}")
        return strategies
