"""
AWS Elastic Beanstalk Service para FinOps.

Análise de custos e otimização de aplicações Elastic Beanstalk.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class BeanstalkApplication:
    """Aplicação Elastic Beanstalk."""
    application_name: str
    description: str = ""
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    versions: List[str] = field(default_factory=list)
    configuration_templates: List[str] = field(default_factory=list)
    resource_lifecycle_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def versions_count(self) -> int:
        """Número de versões."""
        return len(self.versions)

    @property
    def templates_count(self) -> int:
        """Número de templates."""
        return len(self.configuration_templates)

    @property
    def has_lifecycle_policy(self) -> bool:
        """Verifica se tem política de lifecycle."""
        return bool(self.resource_lifecycle_config)

    @property
    def age_days(self) -> int:
        """Idade da aplicação em dias."""
        if self.date_created:
            return (datetime.now(self.date_created.tzinfo) - self.date_created).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "application_name": self.application_name,
            "description": self.description,
            "date_created": self.date_created.isoformat() if self.date_created else None,
            "versions_count": self.versions_count,
            "templates_count": self.templates_count,
            "has_lifecycle_policy": self.has_lifecycle_policy,
            "age_days": self.age_days
        }


@dataclass
class BeanstalkEnvironment:
    """Ambiente Elastic Beanstalk."""
    environment_id: str
    environment_name: str = ""
    application_name: str = ""
    version_label: str = ""
    solution_stack_name: str = ""
    platform_arn: str = ""
    status: str = "Ready"
    health: str = "Green"
    health_status: str = "Ok"
    cname: str = ""
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    tier: Dict[str, Any] = field(default_factory=dict)
    environment_links: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        """Verifica se está ready."""
        return self.status == "Ready"

    @property
    def is_updating(self) -> bool:
        """Verifica se está atualizando."""
        return self.status == "Updating"

    @property
    def is_terminating(self) -> bool:
        """Verifica se está terminando."""
        return self.status == "Terminating"

    @property
    def is_healthy(self) -> bool:
        """Verifica se está saudável."""
        return self.health in ["Green", "Grey"]

    @property
    def has_warnings(self) -> bool:
        """Verifica se tem avisos."""
        return self.health == "Yellow"

    @property
    def has_errors(self) -> bool:
        """Verifica se tem erros."""
        return self.health == "Red"

    @property
    def tier_name(self) -> str:
        """Nome do tier."""
        return self.tier.get('Name', 'WebServer')

    @property
    def tier_type(self) -> str:
        """Tipo do tier."""
        return self.tier.get('Type', 'Standard')

    @property
    def is_web_server(self) -> bool:
        """Verifica se é web server."""
        return self.tier_name == "WebServer"

    @property
    def is_worker(self) -> bool:
        """Verifica se é worker."""
        return self.tier_name == "Worker"

    @property
    def platform(self) -> str:
        """Plataforma do ambiente."""
        if self.solution_stack_name:
            return self.solution_stack_name.split(' ')[0] if ' ' in self.solution_stack_name else self.solution_stack_name
        return "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "environment_id": self.environment_id,
            "environment_name": self.environment_name,
            "application_name": self.application_name,
            "version_label": self.version_label,
            "status": self.status,
            "health": self.health,
            "health_status": self.health_status,
            "cname": self.cname,
            "date_created": self.date_created.isoformat() if self.date_created else None,
            "is_ready": self.is_ready,
            "is_healthy": self.is_healthy,
            "has_warnings": self.has_warnings,
            "has_errors": self.has_errors,
            "tier_name": self.tier_name,
            "is_web_server": self.is_web_server,
            "is_worker": self.is_worker,
            "platform": self.platform
        }


@dataclass
class BeanstalkApplicationVersion:
    """Versão de aplicação Elastic Beanstalk."""
    application_name: str
    version_label: str
    description: str = ""
    source_bundle: Dict[str, Any] = field(default_factory=dict)
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    status: str = "Processed"

    @property
    def is_processed(self) -> bool:
        """Verifica se está processada."""
        return self.status == "Processed"

    @property
    def is_processing(self) -> bool:
        """Verifica se está processando."""
        return self.status == "Processing"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == "Failed"

    @property
    def s3_bucket(self) -> str:
        """Bucket S3 do source bundle."""
        return self.source_bundle.get('S3Bucket', '')

    @property
    def s3_key(self) -> str:
        """Key S3 do source bundle."""
        return self.source_bundle.get('S3Key', '')

    @property
    def age_days(self) -> int:
        """Idade da versão em dias."""
        if self.date_created:
            return (datetime.now(self.date_created.tzinfo) - self.date_created).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "application_name": self.application_name,
            "version_label": self.version_label,
            "description": self.description,
            "status": self.status,
            "date_created": self.date_created.isoformat() if self.date_created else None,
            "is_processed": self.is_processed,
            "is_failed": self.is_failed,
            "age_days": self.age_days
        }


class ElasticBeanstalkService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Elastic Beanstalk."""

    def __init__(self, client_factory):
        """Inicializa o serviço Elastic Beanstalk."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._eb_client = None

    @property
    def eb_client(self):
        """Cliente Elastic Beanstalk com lazy loading."""
        if self._eb_client is None:
            self._eb_client = self._client_factory.get_client('elasticbeanstalk')
        return self._eb_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Elastic Beanstalk."""
        try:
            self.eb_client.describe_applications()
            return {
                "service": "elasticbeanstalk",
                "status": "healthy",
                "message": "Elastic Beanstalk service is accessible"
            }
        except Exception as e:
            return {
                "service": "elasticbeanstalk",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_applications(self) -> List[BeanstalkApplication]:
        """Lista aplicações."""
        applications = []
        try:
            response = self.eb_client.describe_applications()
            for app in response.get('Applications', []):
                applications.append(BeanstalkApplication(
                    application_name=app.get('ApplicationName', ''),
                    description=app.get('Description', ''),
                    date_created=app.get('DateCreated'),
                    date_updated=app.get('DateUpdated'),
                    versions=app.get('Versions', []),
                    configuration_templates=app.get('ConfigurationTemplates', []),
                    resource_lifecycle_config=app.get('ResourceLifecycleConfig', {})
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar aplicações: {e}")
        return applications

    def get_environments(self) -> List[BeanstalkEnvironment]:
        """Lista ambientes."""
        environments = []
        try:
            response = self.eb_client.describe_environments()
            for env in response.get('Environments', []):
                environments.append(BeanstalkEnvironment(
                    environment_id=env.get('EnvironmentId', ''),
                    environment_name=env.get('EnvironmentName', ''),
                    application_name=env.get('ApplicationName', ''),
                    version_label=env.get('VersionLabel', ''),
                    solution_stack_name=env.get('SolutionStackName', ''),
                    platform_arn=env.get('PlatformArn', ''),
                    status=env.get('Status', 'Ready'),
                    health=env.get('Health', 'Green'),
                    health_status=env.get('HealthStatus', 'Ok'),
                    cname=env.get('CNAME', ''),
                    date_created=env.get('DateCreated'),
                    date_updated=env.get('DateUpdated'),
                    tier=env.get('Tier', {}),
                    environment_links=env.get('EnvironmentLinks', [])
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar ambientes: {e}")
        return environments

    def get_application_versions(self, application_name: str = None) -> List[BeanstalkApplicationVersion]:
        """Lista versões de aplicação."""
        versions = []
        try:
            params = {}
            if application_name:
                params['ApplicationName'] = application_name
            
            response = self.eb_client.describe_application_versions(**params)
            for ver in response.get('ApplicationVersions', []):
                versions.append(BeanstalkApplicationVersion(
                    application_name=ver.get('ApplicationName', ''),
                    version_label=ver.get('VersionLabel', ''),
                    description=ver.get('Description', ''),
                    source_bundle=ver.get('SourceBundle', {}),
                    date_created=ver.get('DateCreated'),
                    date_updated=ver.get('DateUpdated'),
                    status=ver.get('Status', 'Processed')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar versões: {e}")
        return versions

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Elastic Beanstalk."""
        applications = self.get_applications()
        environments = self.get_environments()
        versions = self.get_application_versions()

        return {
            "applications": [a.to_dict() for a in applications],
            "environments": [e.to_dict() for e in environments],
            "application_versions": [v.to_dict() for v in versions[:50]],
            "summary": {
                "total_applications": len(applications),
                "applications_with_lifecycle": len([a for a in applications if a.has_lifecycle_policy]),
                "total_environments": len(environments),
                "ready_environments": len([e for e in environments if e.is_ready]),
                "healthy_environments": len([e for e in environments if e.is_healthy]),
                "warning_environments": len([e for e in environments if e.has_warnings]),
                "error_environments": len([e for e in environments if e.has_errors]),
                "web_server_environments": len([e for e in environments if e.is_web_server]),
                "worker_environments": len([e for e in environments if e.is_worker]),
                "total_versions": len(versions)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Elastic Beanstalk."""
        applications = self.get_applications()
        environments = self.get_environments()
        versions = self.get_application_versions()

        return {
            "applications_count": len(applications),
            "applications_with_lifecycle": len([a for a in applications if a.has_lifecycle_policy]),
            "environments_count": len(environments),
            "environment_status": {
                "ready": len([e for e in environments if e.is_ready]),
                "updating": len([e for e in environments if e.is_updating]),
                "terminating": len([e for e in environments if e.is_terminating])
            },
            "environment_health": {
                "green": len([e for e in environments if e.health == "Green"]),
                "yellow": len([e for e in environments if e.health == "Yellow"]),
                "red": len([e for e in environments if e.health == "Red"]),
                "grey": len([e for e in environments if e.health == "Grey"])
            },
            "environment_tiers": {
                "web_server": len([e for e in environments if e.is_web_server]),
                "worker": len([e for e in environments if e.is_worker])
            },
            "versions_count": len(versions),
            "failed_versions": len([v for v in versions if v.is_failed])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Elastic Beanstalk."""
        recommendations = []
        applications = self.get_applications()
        environments = self.get_environments()
        versions = self.get_application_versions()

        # Verificar aplicações sem lifecycle policy
        no_lifecycle = [a for a in applications if not a.has_lifecycle_policy]
        if no_lifecycle:
            recommendations.append({
                "resource_type": "BeanstalkApplication",
                "resource_id": "multiple",
                "recommendation": "Configurar lifecycle policy",
                "description": f"{len(no_lifecycle)} aplicação(ões) sem lifecycle policy. "
                               "Configurar para limpeza automática de versões antigas.",
                "priority": "medium"
            })

        # Verificar ambientes com erros
        error_envs = [e for e in environments if e.has_errors]
        if error_envs:
            recommendations.append({
                "resource_type": "BeanstalkEnvironment",
                "resource_id": "multiple",
                "recommendation": "Investigar ambientes com erros",
                "description": f"{len(error_envs)} ambiente(s) com saúde Red. "
                               "Investigar e resolver problemas.",
                "priority": "high"
            })

        # Verificar ambientes com avisos
        warning_envs = [e for e in environments if e.has_warnings]
        if warning_envs:
            recommendations.append({
                "resource_type": "BeanstalkEnvironment",
                "resource_id": "multiple",
                "recommendation": "Verificar ambientes com avisos",
                "description": f"{len(warning_envs)} ambiente(s) com saúde Yellow. "
                               "Verificar possíveis problemas.",
                "priority": "medium"
            })

        # Verificar versões antigas
        old_versions = [v for v in versions if v.age_days > 90]
        if len(old_versions) > 20:
            recommendations.append({
                "resource_type": "BeanstalkApplicationVersion",
                "resource_id": "multiple",
                "recommendation": "Limpar versões antigas",
                "description": f"{len(old_versions)} versão(ões) com mais de 90 dias. "
                               "Configurar lifecycle policy para limpeza automática.",
                "priority": "low"
            })

        return recommendations
