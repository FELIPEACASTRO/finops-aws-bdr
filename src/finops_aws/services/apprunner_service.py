"""
AWS App Runner Service para FinOps.

Análise de custos e otimização de aplicações App Runner.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class AppRunnerService:
    """Serviço App Runner."""
    service_arn: str
    service_name: str = ""
    service_id: str = ""
    service_url: str = ""
    status: str = "RUNNING"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_configuration: Dict[str, Any] = field(default_factory=dict)
    instance_configuration: Dict[str, Any] = field(default_factory=dict)
    auto_scaling_configuration_summary: Dict[str, Any] = field(default_factory=dict)
    health_check_configuration: Dict[str, Any] = field(default_factory=dict)
    network_configuration: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.status == "RUNNING"

    @property
    def is_paused(self) -> bool:
        """Verifica se está pausado."""
        return self.status == "PAUSED"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status in ["CREATE_IN_PROGRESS", "OPERATION_IN_PROGRESS"]

    @property
    def cpu(self) -> str:
        """CPU configurada."""
        return self.instance_configuration.get('Cpu', '1024')

    @property
    def memory(self) -> str:
        """Memória configurada."""
        return self.instance_configuration.get('Memory', '2048')

    @property
    def cpu_vcpu(self) -> float:
        """CPU em vCPU."""
        try:
            return int(self.cpu) / 1024
        except (ValueError, TypeError):
            return 1.0

    @property
    def memory_gb(self) -> float:
        """Memória em GB."""
        try:
            return int(self.memory) / 1024
        except (ValueError, TypeError):
            return 2.0

    @property
    def min_instances(self) -> int:
        """Mínimo de instâncias."""
        return self.auto_scaling_configuration_summary.get('MinSize', 1)

    @property
    def max_instances(self) -> int:
        """Máximo de instâncias."""
        return self.auto_scaling_configuration_summary.get('MaxSize', 25)

    @property
    def uses_ecr(self) -> bool:
        """Verifica se usa ECR."""
        image_repo = self.source_configuration.get('ImageRepository', {})
        return 'ecr' in image_repo.get('ImageRepositoryType', '').lower()

    @property
    def uses_github(self) -> bool:
        """Verifica se usa GitHub."""
        return 'CodeRepository' in self.source_configuration

    @property
    def has_vpc_connector(self) -> bool:
        """Verifica se tem VPC connector."""
        egress_config = self.network_configuration.get('EgressConfiguration', {})
        return egress_config.get('EgressType') == 'VPC'

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado (baseado em vCPU + GB)."""
        vcpu_cost = self.cpu_vcpu * 0.064
        memory_cost = self.memory_gb * 0.007
        return vcpu_cost + memory_cost

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado (assumindo 720h)."""
        return self.estimated_hourly_cost * 720 * self.min_instances

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "service_arn": self.service_arn,
            "service_name": self.service_name,
            "service_url": self.service_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "cpu_vcpu": self.cpu_vcpu,
            "memory_gb": self.memory_gb,
            "min_instances": self.min_instances,
            "max_instances": self.max_instances,
            "uses_ecr": self.uses_ecr,
            "uses_github": self.uses_github,
            "has_vpc_connector": self.has_vpc_connector,
            "estimated_hourly_cost": self.estimated_hourly_cost,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class AppRunnerAutoScalingConfiguration:
    """Configuração de auto scaling do App Runner."""
    auto_scaling_configuration_arn: str
    auto_scaling_configuration_name: str = ""
    auto_scaling_configuration_revision: int = 1
    status: str = "ACTIVE"
    max_concurrency: int = 100
    min_size: int = 1
    max_size: int = 25
    created_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_inactive(self) -> bool:
        """Verifica se está inativo."""
        return self.status == "INACTIVE"

    @property
    def can_scale_to_zero(self) -> bool:
        """Verifica se pode escalar para zero."""
        return self.min_size == 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "auto_scaling_configuration_arn": self.auto_scaling_configuration_arn,
            "auto_scaling_configuration_name": self.auto_scaling_configuration_name,
            "auto_scaling_configuration_revision": self.auto_scaling_configuration_revision,
            "status": self.status,
            "max_concurrency": self.max_concurrency,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "is_active": self.is_active,
            "can_scale_to_zero": self.can_scale_to_zero
        }


@dataclass
class AppRunnerVpcConnector:
    """VPC Connector do App Runner."""
    vpc_connector_arn: str
    vpc_connector_name: str = ""
    vpc_connector_revision: int = 1
    status: str = "ACTIVE"
    subnets: List[str] = field(default_factory=list)
    security_groups: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def subnets_count(self) -> int:
        """Número de subnets."""
        return len(self.subnets)

    @property
    def security_groups_count(self) -> int:
        """Número de security groups."""
        return len(self.security_groups)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "vpc_connector_arn": self.vpc_connector_arn,
            "vpc_connector_name": self.vpc_connector_name,
            "vpc_connector_revision": self.vpc_connector_revision,
            "status": self.status,
            "subnets_count": self.subnets_count,
            "security_groups_count": self.security_groups_count,
            "is_active": self.is_active
        }


class AppRunnerServiceManager(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS App Runner."""

    def __init__(self, client_factory):
        """Inicializa o serviço App Runner."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._apprunner_client = None

    @property
    def apprunner_client(self):
        """Cliente App Runner com lazy loading."""
        if self._apprunner_client is None:
            self._apprunner_client = self._client_factory.get_client('apprunner')
        return self._apprunner_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço App Runner."""
        try:
            self.apprunner_client.list_services(MaxResults=1)
            return {
                "service": "apprunner",
                "status": "healthy",
                "message": "App Runner service is accessible"
            }
        except Exception as e:
            return {
                "service": "apprunner",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_services(self) -> List[AppRunnerService]:
        """Lista serviços App Runner."""
        services = []
        try:
            paginator = self.apprunner_client.get_paginator('list_services')
            for page in paginator.paginate():
                for svc in page.get('ServiceSummaryList', []):
                    try:
                        details = self.apprunner_client.describe_service(
                            ServiceArn=svc.get('ServiceArn', '')
                        )
                        svc_detail = details.get('Service', {})
                        services.append(AppRunnerService(
                            service_arn=svc_detail.get('ServiceArn', ''),
                            service_name=svc_detail.get('ServiceName', ''),
                            service_id=svc_detail.get('ServiceId', ''),
                            service_url=svc_detail.get('ServiceUrl', ''),
                            status=svc_detail.get('Status', 'RUNNING'),
                            created_at=svc_detail.get('CreatedAt'),
                            updated_at=svc_detail.get('UpdatedAt'),
                            source_configuration=svc_detail.get('SourceConfiguration', {}),
                            instance_configuration=svc_detail.get('InstanceConfiguration', {}),
                            auto_scaling_configuration_summary=svc_detail.get('AutoScalingConfigurationSummary', {}),
                            health_check_configuration=svc_detail.get('HealthCheckConfiguration', {}),
                            network_configuration=svc_detail.get('NetworkConfiguration', {})
                        ))
                    except Exception:
                        services.append(AppRunnerService(
                            service_arn=svc.get('ServiceArn', ''),
                            service_name=svc.get('ServiceName', ''),
                            status=svc.get('Status', 'RUNNING')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar serviços: {e}")
        return services

    def get_auto_scaling_configurations(self) -> List[AppRunnerAutoScalingConfiguration]:
        """Lista configurações de auto scaling."""
        configs = []
        try:
            paginator = self.apprunner_client.get_paginator('list_auto_scaling_configurations')
            for page in paginator.paginate():
                for config in page.get('AutoScalingConfigurationSummaryList', []):
                    configs.append(AppRunnerAutoScalingConfiguration(
                        auto_scaling_configuration_arn=config.get('AutoScalingConfigurationArn', ''),
                        auto_scaling_configuration_name=config.get('AutoScalingConfigurationName', ''),
                        auto_scaling_configuration_revision=config.get('AutoScalingConfigurationRevision', 1),
                        status=config.get('Status', 'ACTIVE')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar auto scaling configs: {e}")
        return configs

    def get_vpc_connectors(self) -> List[AppRunnerVpcConnector]:
        """Lista VPC connectors."""
        connectors = []
        try:
            paginator = self.apprunner_client.get_paginator('list_vpc_connectors')
            for page in paginator.paginate():
                for conn in page.get('VpcConnectors', []):
                    connectors.append(AppRunnerVpcConnector(
                        vpc_connector_arn=conn.get('VpcConnectorArn', ''),
                        vpc_connector_name=conn.get('VpcConnectorName', ''),
                        vpc_connector_revision=conn.get('VpcConnectorRevision', 1),
                        status=conn.get('Status', 'ACTIVE'),
                        subnets=conn.get('Subnets', []),
                        security_groups=conn.get('SecurityGroups', []),
                        created_at=conn.get('CreatedAt')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar VPC connectors: {e}")
        return connectors

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos App Runner."""
        services = self.get_services()
        auto_scaling_configs = self.get_auto_scaling_configurations()
        vpc_connectors = self.get_vpc_connectors()

        total_cost = sum(s.estimated_monthly_cost for s in services if s.is_running)

        return {
            "services": [s.to_dict() for s in services],
            "auto_scaling_configurations": [c.to_dict() for c in auto_scaling_configs],
            "vpc_connectors": [v.to_dict() for v in vpc_connectors],
            "summary": {
                "total_services": len(services),
                "running_services": len([s for s in services if s.is_running]),
                "paused_services": len([s for s in services if s.is_paused]),
                "services_with_vpc": len([s for s in services if s.has_vpc_connector]),
                "services_using_ecr": len([s for s in services if s.uses_ecr]),
                "services_using_github": len([s for s in services if s.uses_github]),
                "total_auto_scaling_configs": len(auto_scaling_configs),
                "total_vpc_connectors": len(vpc_connectors),
                "estimated_monthly_cost": total_cost
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do App Runner."""
        services = self.get_services()
        auto_scaling_configs = self.get_auto_scaling_configurations()
        vpc_connectors = self.get_vpc_connectors()

        return {
            "services_count": len(services),
            "running_services": len([s for s in services if s.is_running]),
            "paused_services": len([s for s in services if s.is_paused]),
            "services_with_vpc": len([s for s in services if s.has_vpc_connector]),
            "total_vcpu": sum(s.cpu_vcpu * s.min_instances for s in services if s.is_running),
            "total_memory_gb": sum(s.memory_gb * s.min_instances for s in services if s.is_running),
            "auto_scaling_configs_count": len(auto_scaling_configs),
            "active_auto_scaling_configs": len([c for c in auto_scaling_configs if c.is_active]),
            "vpc_connectors_count": len(vpc_connectors),
            "estimated_monthly_cost": sum(s.estimated_monthly_cost for s in services if s.is_running)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para App Runner."""
        recommendations = []
        services = self.get_services()

        # Verificar serviços sem VPC connector
        no_vpc = [s for s in services if s.is_running and not s.has_vpc_connector]
        if no_vpc:
            recommendations.append({
                "resource_type": "AppRunnerService",
                "resource_id": "multiple",
                "recommendation": "Considerar VPC connector",
                "description": f"{len(no_vpc)} serviço(s) sem VPC connector. "
                               "Considerar para acesso a recursos privados.",
                "priority": "low"
            })

        # Verificar serviços com min_instances alto
        high_min = [s for s in services if s.is_running and s.min_instances > 5]
        if high_min:
            recommendations.append({
                "resource_type": "AppRunnerService",
                "resource_id": "multiple",
                "recommendation": "Revisar mínimo de instâncias",
                "description": f"{len(high_min)} serviço(s) com min_instances > 5. "
                               "Avaliar se necessário para custo otimizado.",
                "priority": "medium"
            })

        # Verificar serviços pausados antigos
        paused = [s for s in services if s.is_paused]
        if paused:
            recommendations.append({
                "resource_type": "AppRunnerService",
                "resource_id": "multiple",
                "recommendation": "Remover serviços pausados",
                "description": f"{len(paused)} serviço(s) pausados. "
                               "Considerar remover se não for mais necessário.",
                "priority": "low"
            })

        return recommendations
