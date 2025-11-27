"""
AWS Global Accelerator Service para FinOps.

Análise de custos e otimização de aceleradores globais.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class GlobalAccelerator:
    """Acelerador Global AWS."""
    accelerator_arn: str
    name: str = ""
    ip_address_type: str = "IPV4"
    enabled: bool = True
    ip_sets: List[Dict[str, Any]] = field(default_factory=list)
    dns_name: str = ""
    status: str = "DEPLOYED"
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None

    @property
    def is_enabled(self) -> bool:
        """Verifica se está habilitado."""
        return self.enabled

    @property
    def is_deployed(self) -> bool:
        """Verifica se está deployado."""
        return self.status == "DEPLOYED"

    @property
    def is_in_progress(self) -> bool:
        """Verifica se está em progresso."""
        return self.status == "IN_PROGRESS"

    @property
    def supports_ipv6(self) -> bool:
        """Verifica se suporta IPv6."""
        return self.ip_address_type == "DUAL_STACK"

    @property
    def static_ip_count(self) -> int:
        """Número de IPs estáticos."""
        return sum(len(ip_set.get('IpAddresses', [])) for ip_set in self.ip_sets)

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado ($0.025/hora por acelerador + $0.015/GB transferido)."""
        base_cost = 0.025 * 24 * 30  # ~$18/mês por acelerador
        return base_cost if self.is_enabled else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "accelerator_arn": self.accelerator_arn,
            "name": self.name,
            "ip_address_type": self.ip_address_type,
            "enabled": self.enabled,
            "dns_name": self.dns_name,
            "status": self.status,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "is_enabled": self.is_enabled,
            "is_deployed": self.is_deployed,
            "supports_ipv6": self.supports_ipv6,
            "static_ip_count": self.static_ip_count,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class AcceleratorListener:
    """Listener do Global Accelerator."""
    listener_arn: str
    port_ranges: List[Dict[str, int]] = field(default_factory=list)
    protocol: str = "TCP"
    client_affinity: str = "NONE"

    @property
    def is_tcp(self) -> bool:
        """Verifica se é TCP."""
        return self.protocol == "TCP"

    @property
    def is_udp(self) -> bool:
        """Verifica se é UDP."""
        return self.protocol == "UDP"

    @property
    def has_client_affinity(self) -> bool:
        """Verifica se tem client affinity."""
        return self.client_affinity != "NONE"

    @property
    def port_count(self) -> int:
        """Número de port ranges."""
        return len(self.port_ranges)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "listener_arn": self.listener_arn,
            "port_ranges": self.port_ranges,
            "protocol": self.protocol,
            "client_affinity": self.client_affinity,
            "is_tcp": self.is_tcp,
            "is_udp": self.is_udp,
            "has_client_affinity": self.has_client_affinity,
            "port_count": self.port_count
        }


@dataclass
class EndpointGroup:
    """Grupo de endpoints do Global Accelerator."""
    endpoint_group_arn: str
    endpoint_group_region: str = ""
    traffic_dial_percentage: float = 100.0
    health_check_port: int = 80
    health_check_protocol: str = "TCP"
    health_check_path: str = "/"
    health_check_interval_seconds: int = 30
    threshold_count: int = 3
    endpoint_descriptions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_fully_utilized(self) -> bool:
        """Verifica se está 100% utilizado."""
        return self.traffic_dial_percentage == 100.0

    @property
    def is_disabled(self) -> bool:
        """Verifica se está desabilitado (0%)."""
        return self.traffic_dial_percentage == 0.0

    @property
    def endpoint_count(self) -> int:
        """Número de endpoints."""
        return len(self.endpoint_descriptions)

    @property
    def has_health_check(self) -> bool:
        """Verifica se tem health check configurado."""
        return self.health_check_port > 0

    @property
    def healthy_endpoints(self) -> int:
        """Número de endpoints saudáveis."""
        return len([e for e in self.endpoint_descriptions if e.get('HealthState') == 'HEALTHY'])

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "endpoint_group_arn": self.endpoint_group_arn,
            "endpoint_group_region": self.endpoint_group_region,
            "traffic_dial_percentage": self.traffic_dial_percentage,
            "health_check_port": self.health_check_port,
            "health_check_protocol": self.health_check_protocol,
            "is_fully_utilized": self.is_fully_utilized,
            "is_disabled": self.is_disabled,
            "endpoint_count": self.endpoint_count,
            "healthy_endpoints": self.healthy_endpoints,
            "has_health_check": self.has_health_check
        }


class GlobalAcceleratorService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Global Accelerator."""

    def __init__(self, client_factory):
        """Inicializa o serviço Global Accelerator."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._ga_client = None

    @property
    def ga_client(self):
        """Cliente Global Accelerator com lazy loading."""
        if self._ga_client is None:
            self._ga_client = self._client_factory.get_client('globalaccelerator')
        return self._ga_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Global Accelerator."""
        try:
            self.ga_client.list_accelerators(MaxResults=1)
            return {
                "service": "globalaccelerator",
                "status": "healthy",
                "message": "Global Accelerator service is accessible"
            }
        except Exception as e:
            return {
                "service": "globalaccelerator",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_accelerators(self) -> List[GlobalAccelerator]:
        """Lista aceleradores globais."""
        accelerators = []
        try:
            paginator = self.ga_client.get_paginator('list_accelerators')
            for page in paginator.paginate():
                for acc in page.get('Accelerators', []):
                    accelerators.append(GlobalAccelerator(
                        accelerator_arn=acc.get('AcceleratorArn', ''),
                        name=acc.get('Name', ''),
                        ip_address_type=acc.get('IpAddressType', 'IPV4'),
                        enabled=acc.get('Enabled', True),
                        ip_sets=acc.get('IpSets', []),
                        dns_name=acc.get('DnsName', ''),
                        status=acc.get('Status', 'DEPLOYED'),
                        created_time=acc.get('CreatedTime'),
                        last_modified_time=acc.get('LastModifiedTime')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar aceleradores: {e}")
        return accelerators

    def get_listeners(self, accelerator_arn: str) -> List[AcceleratorListener]:
        """Lista listeners de um acelerador."""
        listeners = []
        try:
            paginator = self.ga_client.get_paginator('list_listeners')
            for page in paginator.paginate(AcceleratorArn=accelerator_arn):
                for listener in page.get('Listeners', []):
                    listeners.append(AcceleratorListener(
                        listener_arn=listener.get('ListenerArn', ''),
                        port_ranges=listener.get('PortRanges', []),
                        protocol=listener.get('Protocol', 'TCP'),
                        client_affinity=listener.get('ClientAffinity', 'NONE')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar listeners: {e}")
        return listeners

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Global Accelerator."""
        accelerators = self.get_accelerators()
        all_listeners = []
        
        for acc in accelerators[:10]:  # Limitar para evitar timeout
            listeners = self.get_listeners(acc.accelerator_arn)
            all_listeners.extend(listeners)

        total_cost = sum(acc.estimated_monthly_cost for acc in accelerators)

        return {
            "accelerators": [acc.to_dict() for acc in accelerators],
            "listeners": [l.to_dict() for l in all_listeners],
            "summary": {
                "total_accelerators": len(accelerators),
                "enabled_accelerators": len([a for a in accelerators if a.is_enabled]),
                "deployed_accelerators": len([a for a in accelerators if a.is_deployed]),
                "dual_stack_accelerators": len([a for a in accelerators if a.supports_ipv6]),
                "total_static_ips": sum(a.static_ip_count for a in accelerators),
                "total_listeners": len(all_listeners),
                "estimated_monthly_cost": total_cost
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Global Accelerator."""
        accelerators = self.get_accelerators()

        return {
            "accelerators_count": len(accelerators),
            "enabled_accelerators": len([a for a in accelerators if a.is_enabled]),
            "disabled_accelerators": len([a for a in accelerators if not a.is_enabled]),
            "deployed_accelerators": len([a for a in accelerators if a.is_deployed]),
            "in_progress_accelerators": len([a for a in accelerators if a.is_in_progress]),
            "ipv4_only": len([a for a in accelerators if a.ip_address_type == "IPV4"]),
            "dual_stack": len([a for a in accelerators if a.supports_ipv6]),
            "total_static_ips": sum(a.static_ip_count for a in accelerators),
            "estimated_monthly_cost": sum(a.estimated_monthly_cost for a in accelerators)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Global Accelerator."""
        recommendations = []
        accelerators = self.get_accelerators()

        # Verificar aceleradores desabilitados
        disabled = [a for a in accelerators if not a.is_enabled]
        if disabled:
            recommendations.append({
                "resource_type": "GlobalAccelerator",
                "resource_id": "multiple",
                "recommendation": "Remover aceleradores desabilitados",
                "description": f"{len(disabled)} acelerador(es) desabilitados. "
                               "Considerar remover se não for mais necessário.",
                "priority": "low"
            })

        # Verificar IPv6
        ipv4_only = [a for a in accelerators if not a.supports_ipv6 and a.is_enabled]
        if ipv4_only:
            recommendations.append({
                "resource_type": "GlobalAccelerator",
                "resource_id": "multiple",
                "recommendation": "Considerar dual-stack para suporte IPv6",
                "description": f"{len(ipv4_only)} acelerador(es) usando apenas IPv4. "
                               "Considerar dual-stack para melhor compatibilidade.",
                "priority": "low"
            })

        return recommendations
