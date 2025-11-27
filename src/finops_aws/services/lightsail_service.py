"""
AWS Lightsail Service para FinOps.

Análise de custos e otimização de recursos Lightsail.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class LightsailInstance:
    """Instância Lightsail."""
    name: str
    arn: str = ""
    blueprint_id: str = ""
    blueprint_name: str = ""
    bundle_id: str = ""
    created_at: Optional[datetime] = None
    location: Dict[str, Any] = field(default_factory=dict)
    hardware: Dict[str, Any] = field(default_factory=dict)
    networking: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    username: str = ""
    ssh_key_name: str = ""
    is_static_ip: bool = False
    private_ip_address: str = ""
    public_ip_address: str = ""
    ipv6_addresses: List[str] = field(default_factory=list)
    ip_address_type: str = ""
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.state.get('name', '') == 'running'

    @property
    def is_stopped(self) -> bool:
        """Verifica se está parada."""
        return self.state.get('name', '') == 'stopped'

    @property
    def is_pending(self) -> bool:
        """Verifica se está pending."""
        return self.state.get('name', '') == 'pending'

    @property
    def cpu_count(self) -> int:
        """Número de CPUs."""
        return self.hardware.get('cpuCount', 1)

    @property
    def ram_size_gb(self) -> float:
        """Tamanho da RAM em GB."""
        return self.hardware.get('ramSizeInGb', 0.5)

    @property
    def disk_size_gb(self) -> int:
        """Tamanho do disco em GB."""
        disks = self.hardware.get('disks', [])
        return sum(d.get('sizeInGb', 0) for d in disks)

    @property
    def availability_zone(self) -> str:
        """Availability zone."""
        return self.location.get('availabilityZone', '')

    @property
    def region(self) -> str:
        """Região."""
        return self.location.get('regionName', '')

    @property
    def has_static_ip(self) -> bool:
        """Verifica se tem IP estático."""
        return self.is_static_ip

    @property
    def has_ipv6(self) -> bool:
        """Verifica se tem IPv6."""
        return len(self.ipv6_addresses) > 0

    @property
    def monthly_transfer_gb(self) -> int:
        """Transferência mensal em GB."""
        return self.networking.get('monthlyTransfer', {}).get('gbPerMonthAllocated', 0)

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado baseado no bundle."""
        bundle_costs = {
            "nano": 3.5,
            "micro": 5.0,
            "small": 10.0,
            "medium": 20.0,
            "large": 40.0,
            "xlarge": 80.0,
            "2xlarge": 160.0
        }
        for size, cost in bundle_costs.items():
            if size in self.bundle_id.lower():
                return cost
        return 5.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "blueprint_id": self.blueprint_id,
            "blueprint_name": self.blueprint_name,
            "bundle_id": self.bundle_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "region": self.region,
            "availability_zone": self.availability_zone,
            "is_running": self.is_running,
            "is_stopped": self.is_stopped,
            "cpu_count": self.cpu_count,
            "ram_size_gb": self.ram_size_gb,
            "disk_size_gb": self.disk_size_gb,
            "has_static_ip": self.has_static_ip,
            "has_ipv6": self.has_ipv6,
            "monthly_transfer_gb": self.monthly_transfer_gb,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class LightsailDatabase:
    """Banco de dados Lightsail."""
    name: str
    arn: str = ""
    relational_database_blueprint_id: str = ""
    relational_database_bundle_id: str = ""
    master_database_name: str = ""
    hardware: Dict[str, Any] = field(default_factory=dict)
    state: str = "available"
    engine: str = ""
    engine_version: str = ""
    created_at: Optional[datetime] = None
    location: Dict[str, Any] = field(default_factory=dict)
    master_endpoint: Dict[str, Any] = field(default_factory=dict)
    backup_retention_enabled: bool = True
    preferred_backup_window: str = ""
    preferred_maintenance_window: str = ""
    publicly_accessible: bool = False
    ca_certificate_identifier: str = ""
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.state == "available"

    @property
    def is_stopped(self) -> bool:
        """Verifica se está parado."""
        return self.state == "stopped"

    @property
    def cpu_count(self) -> int:
        """Número de CPUs."""
        return self.hardware.get('cpuCount', 1)

    @property
    def ram_size_gb(self) -> float:
        """Tamanho da RAM em GB."""
        return self.hardware.get('ramSizeInGb', 1.0)

    @property
    def disk_size_gb(self) -> int:
        """Tamanho do disco em GB."""
        return self.hardware.get('diskSizeInGb', 40)

    @property
    def is_mysql(self) -> bool:
        """Verifica se é MySQL."""
        return 'mysql' in self.engine.lower()

    @property
    def is_postgres(self) -> bool:
        """Verifica se é PostgreSQL."""
        return 'postgres' in self.engine.lower()

    @property
    def has_backup_enabled(self) -> bool:
        """Verifica se backup está habilitado."""
        return self.backup_retention_enabled

    @property
    def is_public(self) -> bool:
        """Verifica se é público."""
        return self.publicly_accessible

    @property
    def endpoint_address(self) -> str:
        """Endereço do endpoint."""
        return self.master_endpoint.get('address', '')

    @property
    def endpoint_port(self) -> int:
        """Porta do endpoint."""
        return self.master_endpoint.get('port', 0)

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado."""
        bundle_costs = {
            "micro": 15.0,
            "small": 30.0,
            "medium": 60.0,
            "large": 115.0
        }
        for size, cost in bundle_costs.items():
            if size in self.relational_database_bundle_id.lower():
                return cost
        return 15.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "arn": self.arn,
            "engine": self.engine,
            "engine_version": self.engine_version,
            "state": self.state,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_available": self.is_available,
            "cpu_count": self.cpu_count,
            "ram_size_gb": self.ram_size_gb,
            "disk_size_gb": self.disk_size_gb,
            "is_mysql": self.is_mysql,
            "is_postgres": self.is_postgres,
            "has_backup_enabled": self.has_backup_enabled,
            "is_public": self.is_public,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class LightsailContainer:
    """Serviço de container Lightsail."""
    container_service_name: str
    arn: str = ""
    created_at: Optional[datetime] = None
    location: Dict[str, Any] = field(default_factory=dict)
    power: str = "nano"
    power_id: str = ""
    state: str = "RUNNING"
    scale: int = 1
    current_deployment: Dict[str, Any] = field(default_factory=dict)
    next_deployment: Dict[str, Any] = field(default_factory=dict)
    is_disabled: bool = False
    principal_arn: str = ""
    private_domain_name: str = ""
    public_domain_names: Dict[str, List[str]] = field(default_factory=dict)
    url: str = ""
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.state == "RUNNING"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pending."""
        return self.state == "PENDING"

    @property
    def is_disabled_state(self) -> bool:
        """Verifica se está desabilitado."""
        return self.is_disabled or self.state == "DISABLED"

    @property
    def nodes_count(self) -> int:
        """Número de nós."""
        return self.scale

    @property
    def has_deployment(self) -> bool:
        """Verifica se tem deployment atual."""
        return bool(self.current_deployment)

    @property
    def has_custom_domains(self) -> bool:
        """Verifica se tem domínios customizados."""
        return bool(self.public_domain_names)

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado."""
        power_costs = {
            "nano": 7.0,
            "micro": 10.0,
            "small": 25.0,
            "medium": 50.0,
            "large": 100.0,
            "xlarge": 200.0
        }
        cost_per_node = power_costs.get(self.power.lower(), 7.0)
        return cost_per_node * self.scale

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "container_service_name": self.container_service_name,
            "arn": self.arn,
            "power": self.power,
            "state": self.state,
            "scale": self.scale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_running": self.is_running,
            "is_disabled": self.is_disabled_state,
            "nodes_count": self.nodes_count,
            "has_deployment": self.has_deployment,
            "has_custom_domains": self.has_custom_domains,
            "url": self.url,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


class LightsailService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Lightsail."""

    def __init__(self, client_factory):
        """Inicializa o serviço Lightsail."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._lightsail_client = None

    @property
    def lightsail_client(self):
        """Cliente Lightsail com lazy loading."""
        if self._lightsail_client is None:
            self._lightsail_client = self._client_factory.get_client('lightsail')
        return self._lightsail_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Lightsail."""
        try:
            self.lightsail_client.get_instances()
            return {
                "service": "lightsail",
                "status": "healthy",
                "message": "Lightsail service is accessible"
            }
        except Exception as e:
            return {
                "service": "lightsail",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_instances(self) -> List[LightsailInstance]:
        """Lista instâncias Lightsail."""
        instances = []
        try:
            response = self.lightsail_client.get_instances()
            for inst in response.get('instances', []):
                instances.append(LightsailInstance(
                    name=inst.get('name', ''),
                    arn=inst.get('arn', ''),
                    blueprint_id=inst.get('blueprintId', ''),
                    blueprint_name=inst.get('blueprintName', ''),
                    bundle_id=inst.get('bundleId', ''),
                    created_at=inst.get('createdAt'),
                    location=inst.get('location', {}),
                    hardware=inst.get('hardware', {}),
                    networking=inst.get('networking', {}),
                    state=inst.get('state', {}),
                    username=inst.get('username', ''),
                    ssh_key_name=inst.get('sshKeyName', ''),
                    is_static_ip=inst.get('isStaticIp', False),
                    private_ip_address=inst.get('privateIpAddress', ''),
                    public_ip_address=inst.get('publicIpAddress', ''),
                    ipv6_addresses=inst.get('ipv6Addresses', []),
                    ip_address_type=inst.get('ipAddressType', ''),
                    tags=inst.get('tags', [])
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar instâncias: {e}")
        return instances

    def get_databases(self) -> List[LightsailDatabase]:
        """Lista bancos de dados Lightsail."""
        databases = []
        try:
            response = self.lightsail_client.get_relational_databases()
            for db in response.get('relationalDatabases', []):
                databases.append(LightsailDatabase(
                    name=db.get('name', ''),
                    arn=db.get('arn', ''),
                    relational_database_blueprint_id=db.get('relationalDatabaseBlueprintId', ''),
                    relational_database_bundle_id=db.get('relationalDatabaseBundleId', ''),
                    master_database_name=db.get('masterDatabaseName', ''),
                    hardware=db.get('hardware', {}),
                    state=db.get('state', 'available'),
                    engine=db.get('engine', ''),
                    engine_version=db.get('engineVersion', ''),
                    created_at=db.get('createdAt'),
                    location=db.get('location', {}),
                    master_endpoint=db.get('masterEndpoint', {}),
                    backup_retention_enabled=db.get('backupRetentionEnabled', True),
                    preferred_backup_window=db.get('preferredBackupWindow', ''),
                    preferred_maintenance_window=db.get('preferredMaintenanceWindow', ''),
                    publicly_accessible=db.get('publiclyAccessible', False),
                    ca_certificate_identifier=db.get('caCertificateIdentifier', ''),
                    tags=db.get('tags', [])
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar bancos de dados: {e}")
        return databases

    def get_container_services(self) -> List[LightsailContainer]:
        """Lista serviços de container Lightsail."""
        containers = []
        try:
            response = self.lightsail_client.get_container_services()
            for svc in response.get('containerServices', []):
                containers.append(LightsailContainer(
                    container_service_name=svc.get('containerServiceName', ''),
                    arn=svc.get('arn', ''),
                    created_at=svc.get('createdAt'),
                    location=svc.get('location', {}),
                    power=svc.get('power', 'nano'),
                    power_id=svc.get('powerId', ''),
                    state=svc.get('state', 'RUNNING'),
                    scale=svc.get('scale', 1),
                    current_deployment=svc.get('currentDeployment', {}),
                    next_deployment=svc.get('nextDeployment', {}),
                    is_disabled=svc.get('isDisabled', False),
                    principal_arn=svc.get('principalArn', ''),
                    private_domain_name=svc.get('privateDomainName', ''),
                    public_domain_names=svc.get('publicDomainNames', {}),
                    url=svc.get('url', ''),
                    tags=svc.get('tags', [])
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar container services: {e}")
        return containers

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Lightsail."""
        instances = self.get_instances()
        databases = self.get_databases()
        containers = self.get_container_services()

        total_cost = sum(i.estimated_monthly_cost for i in instances if i.is_running)
        total_cost += sum(d.estimated_monthly_cost for d in databases if d.is_available)
        total_cost += sum(c.estimated_monthly_cost for c in containers if c.is_running)

        return {
            "instances": [i.to_dict() for i in instances],
            "databases": [d.to_dict() for d in databases],
            "container_services": [c.to_dict() for c in containers],
            "summary": {
                "total_instances": len(instances),
                "running_instances": len([i for i in instances if i.is_running]),
                "stopped_instances": len([i for i in instances if i.is_stopped]),
                "total_databases": len(databases),
                "available_databases": len([d for d in databases if d.is_available]),
                "public_databases": len([d for d in databases if d.is_public]),
                "total_container_services": len(containers),
                "running_containers": len([c for c in containers if c.is_running]),
                "estimated_monthly_cost": total_cost
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Lightsail."""
        instances = self.get_instances()
        databases = self.get_databases()
        containers = self.get_container_services()

        return {
            "instances_count": len(instances),
            "running_instances": len([i for i in instances if i.is_running]),
            "stopped_instances": len([i for i in instances if i.is_stopped]),
            "instances_with_static_ip": len([i for i in instances if i.has_static_ip]),
            "total_instance_vcpus": sum(i.cpu_count for i in instances if i.is_running),
            "total_instance_ram_gb": sum(i.ram_size_gb for i in instances if i.is_running),
            "databases_count": len(databases),
            "mysql_databases": len([d for d in databases if d.is_mysql]),
            "postgres_databases": len([d for d in databases if d.is_postgres]),
            "public_databases": len([d for d in databases if d.is_public]),
            "containers_count": len(containers),
            "running_containers": len([c for c in containers if c.is_running]),
            "total_container_nodes": sum(c.nodes_count for c in containers if c.is_running),
            "estimated_monthly_cost": (
                sum(i.estimated_monthly_cost for i in instances if i.is_running) +
                sum(d.estimated_monthly_cost for d in databases if d.is_available) +
                sum(c.estimated_monthly_cost for c in containers if c.is_running)
            )
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Lightsail."""
        recommendations = []
        instances = self.get_instances()
        databases = self.get_databases()
        containers = self.get_container_services()

        # Verificar instâncias paradas
        stopped = [i for i in instances if i.is_stopped]
        if stopped:
            recommendations.append({
                "resource_type": "LightsailInstance",
                "resource_id": "multiple",
                "recommendation": "Remover instâncias paradas",
                "description": f"{len(stopped)} instância(s) parada(s). "
                               "Considerar remover se não for mais necessário.",
                "estimated_savings": sum(i.estimated_monthly_cost for i in stopped),
                "priority": "medium"
            })

        # Verificar bancos públicos
        public_dbs = [d for d in databases if d.is_public]
        if public_dbs:
            recommendations.append({
                "resource_type": "LightsailDatabase",
                "resource_id": "multiple",
                "recommendation": "Desabilitar acesso público",
                "description": f"{len(public_dbs)} banco(s) com acesso público. "
                               "Considerar desabilitar para maior segurança.",
                "priority": "high"
            })

        # Verificar containers desabilitados
        disabled_containers = [c for c in containers if c.is_disabled_state]
        if disabled_containers:
            recommendations.append({
                "resource_type": "LightsailContainer",
                "resource_id": "multiple",
                "recommendation": "Remover containers desabilitados",
                "description": f"{len(disabled_containers)} serviço(s) de container desabilitado(s). "
                               "Considerar remover se não for mais necessário.",
                "priority": "low"
            })

        return recommendations
