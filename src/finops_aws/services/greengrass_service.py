"""
AWS IoT Greengrass Service para FinOps.

Análise de custos e otimização de recursos IoT Greengrass.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class GreengrassCoreDevice:
    """Core Device Greengrass."""
    core_device_thing_name: str
    status: str = "HEALTHY"
    last_status_update_timestamp: Optional[datetime] = None
    platform: str = ""
    architecture: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Verifica se está saudável."""
        return self.status == "HEALTHY"

    @property
    def is_unhealthy(self) -> bool:
        """Verifica se está com problemas."""
        return self.status == "UNHEALTHY"

    @property
    def is_offline(self) -> bool:
        """Verifica se está offline."""
        return self.status not in ["HEALTHY", "UNHEALTHY"]

    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return len(self.tags) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "core_device_thing_name": self.core_device_thing_name,
            "status": self.status,
            "is_healthy": self.is_healthy,
            "is_unhealthy": self.is_unhealthy,
            "is_offline": self.is_offline,
            "platform": self.platform,
            "architecture": self.architecture,
            "last_status_update": self.last_status_update_timestamp.isoformat() if self.last_status_update_timestamp else None
        }


@dataclass
class GreengrassDeployment:
    """Deployment Greengrass."""
    deployment_id: str
    deployment_name: str = ""
    target_arn: str = ""
    deployment_status: str = "ACTIVE"
    is_latest_for_target: bool = True
    creation_timestamp: Optional[datetime] = None
    revision_id: str = ""
    parent_target_arn: str = ""

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.deployment_status == "ACTIVE"

    @property
    def is_completed(self) -> bool:
        """Verifica se está completo."""
        return self.deployment_status == "COMPLETED"

    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.deployment_status == "FAILED"

    @property
    def is_canceled(self) -> bool:
        """Verifica se foi cancelado."""
        return self.deployment_status == "CANCELED"

    @property
    def has_parent_target(self) -> bool:
        """Verifica se tem parent target."""
        return bool(self.parent_target_arn)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "deployment_id": self.deployment_id,
            "deployment_name": self.deployment_name,
            "target_arn": self.target_arn,
            "deployment_status": self.deployment_status,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_latest_for_target": self.is_latest_for_target,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None
        }


@dataclass
class GreengrassComponent:
    """Component Greengrass."""
    component_name: str
    arn: str = ""
    latest_version: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def component_version(self) -> str:
        """Versão do componente."""
        return self.latest_version.get('componentVersion', '')

    @property
    def creation_timestamp(self) -> Optional[datetime]:
        """Timestamp de criação."""
        return self.latest_version.get('creationTimestamp')

    @property
    def publisher(self) -> str:
        """Publisher do componente."""
        return self.latest_version.get('publisher', '')

    @property
    def is_aws_provided(self) -> bool:
        """Verifica se é fornecido pela AWS."""
        return self.publisher.lower() == 'aws'

    @property
    def is_custom(self) -> bool:
        """Verifica se é customizado."""
        return not self.is_aws_provided and bool(self.publisher)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "component_name": self.component_name,
            "arn": self.arn,
            "component_version": self.component_version,
            "publisher": self.publisher,
            "is_aws_provided": self.is_aws_provided,
            "is_custom": self.is_custom,
            "description": self.description
        }


@dataclass
class GreengrassClientDevice:
    """Client Device Greengrass."""
    thing_name: str
    associated_at: Optional[datetime] = None

    @property
    def has_association_date(self) -> bool:
        """Verifica se tem data de associação."""
        return self.associated_at is not None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "thing_name": self.thing_name,
            "associated_at": self.associated_at.isoformat() if self.associated_at else None
        }


class GreengrassService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS IoT Greengrass."""

    def __init__(self, client_factory):
        """Inicializa o serviço Greengrass."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._greengrassv2_client = None

    @property
    def greengrassv2_client(self):
        """Cliente Greengrass V2 com lazy loading."""
        if self._greengrassv2_client is None:
            self._greengrassv2_client = self._client_factory.get_client('greengrassv2')
        return self._greengrassv2_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Greengrass."""
        try:
            self.greengrassv2_client.list_core_devices(maxResults=1)
            return {
                "service": "greengrassv2",
                "status": "healthy",
                "message": "Greengrass V2 service is accessible"
            }
        except Exception as e:
            return {
                "service": "greengrassv2",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_core_devices(self) -> List[GreengrassCoreDevice]:
        """Lista core devices."""
        devices = []
        try:
            paginator = self.greengrassv2_client.get_paginator('list_core_devices')
            for page in paginator.paginate():
                for device in page.get('coreDevices', []):
                    devices.append(GreengrassCoreDevice(
                        core_device_thing_name=device.get('coreDeviceThingName', ''),
                        status=device.get('status', 'HEALTHY'),
                        last_status_update_timestamp=device.get('lastStatusUpdateTimestamp'),
                        platform=device.get('platform', ''),
                        architecture=device.get('architecture', ''),
                        tags=device.get('tags', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar core devices: {e}")
        return devices

    def get_deployments(self) -> List[GreengrassDeployment]:
        """Lista deployments."""
        deployments = []
        try:
            paginator = self.greengrassv2_client.get_paginator('list_deployments')
            for page in paginator.paginate():
                for dep in page.get('deployments', []):
                    deployments.append(GreengrassDeployment(
                        deployment_id=dep.get('deploymentId', ''),
                        deployment_name=dep.get('deploymentName', ''),
                        target_arn=dep.get('targetArn', ''),
                        deployment_status=dep.get('deploymentStatus', 'ACTIVE'),
                        is_latest_for_target=dep.get('isLatestForTarget', True),
                        creation_timestamp=dep.get('creationTimestamp'),
                        revision_id=dep.get('revisionId', ''),
                        parent_target_arn=dep.get('parentTargetArn', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar deployments: {e}")
        return deployments

    def get_components(self) -> List[GreengrassComponent]:
        """Lista componentes."""
        components = []
        try:
            paginator = self.greengrassv2_client.get_paginator('list_components')
            for page in paginator.paginate():
                for comp in page.get('components', []):
                    components.append(GreengrassComponent(
                        component_name=comp.get('componentName', ''),
                        arn=comp.get('arn', ''),
                        latest_version=comp.get('latestVersion', {}),
                        description=comp.get('description', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar componentes: {e}")
        return components

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Greengrass."""
        core_devices = self.get_core_devices()
        deployments = self.get_deployments()
        components = self.get_components()

        return {
            "core_devices": [d.to_dict() for d in core_devices],
            "deployments": [d.to_dict() for d in deployments[:50]],
            "components": [c.to_dict() for c in components],
            "summary": {
                "total_core_devices": len(core_devices),
                "healthy_devices": len([d for d in core_devices if d.is_healthy]),
                "unhealthy_devices": len([d for d in core_devices if d.is_unhealthy]),
                "offline_devices": len([d for d in core_devices if d.is_offline]),
                "total_deployments": len(deployments),
                "active_deployments": len([d for d in deployments if d.is_active]),
                "completed_deployments": len([d for d in deployments if d.is_completed]),
                "failed_deployments": len([d for d in deployments if d.is_failed]),
                "total_components": len(components),
                "aws_components": len([c for c in components if c.is_aws_provided]),
                "custom_components": len([c for c in components if c.is_custom])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Greengrass."""
        core_devices = self.get_core_devices()
        deployments = self.get_deployments()
        components = self.get_components()

        return {
            "core_devices_count": len(core_devices),
            "healthy_devices": len([d for d in core_devices if d.is_healthy]),
            "unhealthy_devices": len([d for d in core_devices if d.is_unhealthy]),
            "offline_devices": len([d for d in core_devices if d.is_offline]),
            "deployments_count": len(deployments),
            "active_deployments": len([d for d in deployments if d.is_active]),
            "completed_deployments": len([d for d in deployments if d.is_completed]),
            "failed_deployments": len([d for d in deployments if d.is_failed]),
            "canceled_deployments": len([d for d in deployments if d.is_canceled]),
            "components_count": len(components),
            "aws_components": len([c for c in components if c.is_aws_provided]),
            "custom_components": len([c for c in components if c.is_custom])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Greengrass."""
        recommendations = []
        core_devices = self.get_core_devices()
        deployments = self.get_deployments()

        unhealthy = [d for d in core_devices if d.is_unhealthy]
        if unhealthy:
            recommendations.append({
                "resource_type": "GreengrassCoreDevice",
                "resource_id": "multiple",
                "recommendation": "Investigar core devices com problemas",
                "description": f"{len(unhealthy)} core device(s) com status UNHEALTHY. "
                               "Verificar logs e conectividade.",
                "priority": "high"
            })

        offline = [d for d in core_devices if d.is_offline]
        if offline:
            recommendations.append({
                "resource_type": "GreengrassCoreDevice",
                "resource_id": "multiple",
                "recommendation": "Verificar core devices offline",
                "description": f"{len(offline)} core device(s) offline. "
                               "Verificar conectividade e estado do dispositivo.",
                "priority": "high"
            })

        failed = [d for d in deployments if d.is_failed]
        if failed:
            recommendations.append({
                "resource_type": "GreengrassDeployment",
                "resource_id": "multiple",
                "recommendation": "Investigar deployments com falha",
                "description": f"{len(failed)} deployment(s) com falha. "
                               "Verificar logs e configuração.",
                "priority": "medium"
            })

        return recommendations
