"""
AWS DMS (Database Migration Service) para FinOps.

Análise de custos e otimização de migrações de banco de dados.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class DMSReplicationInstance:
    """Replication Instance DMS."""
    replication_instance_identifier: str
    replication_instance_arn: str = ""
    replication_instance_class: str = ""
    allocated_storage: int = 0
    status: str = "available"
    engine_version: str = ""
    auto_minor_version_upgrade: bool = True
    publicly_accessible: bool = False
    multi_az: bool = False
    availability_zone: str = ""
    vpc_security_groups: List[Dict[str, str]] = field(default_factory=list)
    replication_subnet_group_identifier: str = ""
    preferred_maintenance_window: str = ""
    kms_key_id: str = ""
    free_until: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.status == "available"

    @property
    def is_creating(self) -> bool:
        """Verifica se está sendo criado."""
        return self.status == "creating"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.status == "deleting"

    @property
    def is_modifying(self) -> bool:
        """Verifica se está sendo modificado."""
        return self.status == "modifying"

    @property
    def is_multi_az(self) -> bool:
        """Verifica se é Multi-AZ."""
        return self.multi_az

    @property
    def is_publicly_accessible(self) -> bool:
        """Verifica se é publicamente acessível."""
        return self.publicly_accessible

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_key_id)

    @property
    def instance_size(self) -> str:
        """Tamanho da instância."""
        parts = self.replication_instance_class.split('.')
        return parts[-1] if len(parts) >= 2 else ""

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora estimado."""
        size_costs = {
            'small': 0.05, 'medium': 0.10, 'large': 0.20,
            'xlarge': 0.40, '2xlarge': 0.80, '4xlarge': 1.60
        }
        return size_costs.get(self.instance_size, 0.20) * (2 if self.is_multi_az else 1)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "replication_instance_identifier": self.replication_instance_identifier,
            "replication_instance_arn": self.replication_instance_arn,
            "replication_instance_class": self.replication_instance_class,
            "allocated_storage": self.allocated_storage,
            "status": self.status,
            "is_available": self.is_available,
            "is_multi_az": self.is_multi_az,
            "has_encryption": self.has_encryption,
            "estimated_hourly_cost": self.estimated_hourly_cost
        }


@dataclass
class DMSEndpoint:
    """Endpoint DMS."""
    endpoint_identifier: str
    endpoint_arn: str = ""
    endpoint_type: str = "source"
    engine_name: str = ""
    server_name: str = ""
    port: int = 0
    database_name: str = ""
    username: str = ""
    status: str = "active"
    ssl_mode: str = "none"
    kms_key_id: str = ""
    extra_connection_attributes: str = ""

    @property
    def is_source(self) -> bool:
        """Verifica se é source."""
        return self.endpoint_type.lower() == "source"

    @property
    def is_target(self) -> bool:
        """Verifica se é target."""
        return self.endpoint_type.lower() == "target"

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "active"

    @property
    def has_ssl(self) -> bool:
        """Verifica se usa SSL."""
        return self.ssl_mode != "none"

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_key_id)

    @property
    def is_rds(self) -> bool:
        """Verifica se é RDS."""
        return "rds" in self.engine_name.lower() or self.engine_name in ['aurora', 'aurora-postgresql']

    @property
    def is_s3(self) -> bool:
        """Verifica se é S3."""
        return self.engine_name.lower() == "s3"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "endpoint_identifier": self.endpoint_identifier,
            "endpoint_arn": self.endpoint_arn,
            "endpoint_type": self.endpoint_type,
            "engine_name": self.engine_name,
            "is_source": self.is_source,
            "is_target": self.is_target,
            "is_active": self.is_active,
            "has_ssl": self.has_ssl,
            "has_encryption": self.has_encryption
        }


@dataclass
class DMSReplicationTask:
    """Replication Task DMS."""
    replication_task_identifier: str
    replication_task_arn: str = ""
    source_endpoint_arn: str = ""
    target_endpoint_arn: str = ""
    replication_instance_arn: str = ""
    migration_type: str = "full-load"
    status: str = "running"
    stop_reason: str = ""
    replication_task_creation_date: Optional[datetime] = None
    replication_task_start_date: Optional[datetime] = None
    table_mappings: str = ""
    replication_task_settings: str = ""
    cdc_start_position: str = ""

    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self.status == "running"

    @property
    def is_stopped(self) -> bool:
        """Verifica se está parado."""
        return self.status == "stopped"

    @property
    def is_starting(self) -> bool:
        """Verifica se está iniciando."""
        return self.status == "starting"

    @property
    def is_ready(self) -> bool:
        """Verifica se está pronto."""
        return self.status == "ready"

    @property
    def is_full_load(self) -> bool:
        """Verifica se é full-load."""
        return self.migration_type == "full-load"

    @property
    def is_cdc(self) -> bool:
        """Verifica se é CDC."""
        return self.migration_type == "cdc"

    @property
    def is_full_load_and_cdc(self) -> bool:
        """Verifica se é full-load e CDC."""
        return self.migration_type == "full-load-and-cdc"

    @property
    def has_stop_reason(self) -> bool:
        """Verifica se tem razão de parada."""
        return bool(self.stop_reason)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "replication_task_identifier": self.replication_task_identifier,
            "replication_task_arn": self.replication_task_arn,
            "migration_type": self.migration_type,
            "status": self.status,
            "is_running": self.is_running,
            "is_stopped": self.is_stopped,
            "is_full_load": self.is_full_load,
            "is_cdc": self.is_cdc
        }


class DMSService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS DMS."""

    def __init__(self, client_factory):
        """Inicializa o serviço DMS."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._dms_client = None

    @property
    def dms_client(self):
        """Cliente DMS com lazy loading."""
        if self._dms_client is None:
            self._dms_client = self._client_factory.get_client('dms')
        return self._dms_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço DMS."""
        try:
            self.dms_client.describe_replication_instances(MaxRecords=1)
            return {
                "service": "dms",
                "status": "healthy",
                "message": "DMS service is accessible"
            }
        except Exception as e:
            return {
                "service": "dms",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_replication_instances(self) -> List[DMSReplicationInstance]:
        """Lista replication instances."""
        instances = []
        try:
            paginator = self.dms_client.get_paginator('describe_replication_instances')
            for page in paginator.paginate():
                for inst in page.get('ReplicationInstances', []):
                    instances.append(DMSReplicationInstance(
                        replication_instance_identifier=inst.get('ReplicationInstanceIdentifier', ''),
                        replication_instance_arn=inst.get('ReplicationInstanceArn', ''),
                        replication_instance_class=inst.get('ReplicationInstanceClass', ''),
                        allocated_storage=inst.get('AllocatedStorage', 0),
                        status=inst.get('ReplicationInstanceStatus', 'available'),
                        engine_version=inst.get('EngineVersion', ''),
                        auto_minor_version_upgrade=inst.get('AutoMinorVersionUpgrade', True),
                        publicly_accessible=inst.get('PubliclyAccessible', False),
                        multi_az=inst.get('MultiAZ', False),
                        availability_zone=inst.get('AvailabilityZone', ''),
                        vpc_security_groups=inst.get('VpcSecurityGroups', []),
                        replication_subnet_group_identifier=inst.get('ReplicationSubnetGroup', {}).get('ReplicationSubnetGroupIdentifier', ''),
                        preferred_maintenance_window=inst.get('PreferredMaintenanceWindow', ''),
                        kms_key_id=inst.get('KmsKeyId', ''),
                        free_until=inst.get('FreeUntil')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar replication instances: {e}")
        return instances

    def get_endpoints(self) -> List[DMSEndpoint]:
        """Lista endpoints."""
        endpoints = []
        try:
            paginator = self.dms_client.get_paginator('describe_endpoints')
            for page in paginator.paginate():
                for ep in page.get('Endpoints', []):
                    endpoints.append(DMSEndpoint(
                        endpoint_identifier=ep.get('EndpointIdentifier', ''),
                        endpoint_arn=ep.get('EndpointArn', ''),
                        endpoint_type=ep.get('EndpointType', 'source'),
                        engine_name=ep.get('EngineName', ''),
                        server_name=ep.get('ServerName', ''),
                        port=ep.get('Port', 0),
                        database_name=ep.get('DatabaseName', ''),
                        username=ep.get('Username', ''),
                        status=ep.get('Status', 'active'),
                        ssl_mode=ep.get('SslMode', 'none'),
                        kms_key_id=ep.get('KmsKeyId', ''),
                        extra_connection_attributes=ep.get('ExtraConnectionAttributes', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar endpoints: {e}")
        return endpoints

    def get_replication_tasks(self) -> List[DMSReplicationTask]:
        """Lista replication tasks."""
        tasks = []
        try:
            paginator = self.dms_client.get_paginator('describe_replication_tasks')
            for page in paginator.paginate():
                for task in page.get('ReplicationTasks', []):
                    tasks.append(DMSReplicationTask(
                        replication_task_identifier=task.get('ReplicationTaskIdentifier', ''),
                        replication_task_arn=task.get('ReplicationTaskArn', ''),
                        source_endpoint_arn=task.get('SourceEndpointArn', ''),
                        target_endpoint_arn=task.get('TargetEndpointArn', ''),
                        replication_instance_arn=task.get('ReplicationInstanceArn', ''),
                        migration_type=task.get('MigrationType', 'full-load'),
                        status=task.get('Status', 'running'),
                        stop_reason=task.get('StopReason', ''),
                        replication_task_creation_date=task.get('ReplicationTaskCreationDate'),
                        replication_task_start_date=task.get('ReplicationTaskStartDate'),
                        table_mappings=task.get('TableMappings', ''),
                        cdc_start_position=task.get('CdcStartPosition', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar replication tasks: {e}")
        return tasks

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos DMS."""
        instances = self.get_replication_instances()
        endpoints = self.get_endpoints()
        tasks = self.get_replication_tasks()

        return {
            "replication_instances": [i.to_dict() for i in instances],
            "endpoints": [e.to_dict() for e in endpoints],
            "replication_tasks": [t.to_dict() for t in tasks],
            "summary": {
                "total_instances": len(instances),
                "available_instances": len([i for i in instances if i.is_available]),
                "multi_az_instances": len([i for i in instances if i.is_multi_az]),
                "encrypted_instances": len([i for i in instances if i.has_encryption]),
                "total_endpoints": len(endpoints),
                "source_endpoints": len([e for e in endpoints if e.is_source]),
                "target_endpoints": len([e for e in endpoints if e.is_target]),
                "total_tasks": len(tasks),
                "running_tasks": len([t for t in tasks if t.is_running]),
                "stopped_tasks": len([t for t in tasks if t.is_stopped]),
                "estimated_hourly_cost": sum(i.estimated_hourly_cost for i in instances if i.is_available)
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do DMS."""
        instances = self.get_replication_instances()
        endpoints = self.get_endpoints()
        tasks = self.get_replication_tasks()

        return {
            "replication_instances_count": len(instances),
            "available_instances": len([i for i in instances if i.is_available]),
            "multi_az_instances": len([i for i in instances if i.is_multi_az]),
            "encrypted_instances": len([i for i in instances if i.has_encryption]),
            "publicly_accessible_instances": len([i for i in instances if i.is_publicly_accessible]),
            "total_allocated_storage_gb": sum(i.allocated_storage for i in instances),
            "endpoints_count": len(endpoints),
            "source_endpoints": len([e for e in endpoints if e.is_source]),
            "target_endpoints": len([e for e in endpoints if e.is_target]),
            "ssl_enabled_endpoints": len([e for e in endpoints if e.has_ssl]),
            "tasks_count": len(tasks),
            "running_tasks": len([t for t in tasks if t.is_running]),
            "full_load_tasks": len([t for t in tasks if t.is_full_load]),
            "cdc_tasks": len([t for t in tasks if t.is_cdc])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para DMS."""
        recommendations = []
        instances = self.get_replication_instances()
        endpoints = self.get_endpoints()

        no_encryption = [i for i in instances if not i.has_encryption]
        if no_encryption:
            recommendations.append({
                "resource_type": "DMSReplicationInstance",
                "resource_id": "multiple",
                "recommendation": "Habilitar criptografia",
                "description": f"{len(no_encryption)} instância(s) sem criptografia KMS. "
                               "Habilitar para maior segurança.",
                "priority": "high"
            })

        public_instances = [i for i in instances if i.is_publicly_accessible]
        if public_instances:
            recommendations.append({
                "resource_type": "DMSReplicationInstance",
                "resource_id": "multiple",
                "recommendation": "Remover acesso público",
                "description": f"{len(public_instances)} instância(s) publicamente acessível(is). "
                               "Considerar remover acesso público.",
                "priority": "high"
            })

        no_ssl = [e for e in endpoints if not e.has_ssl]
        if no_ssl:
            recommendations.append({
                "resource_type": "DMSEndpoint",
                "resource_id": "multiple",
                "recommendation": "Habilitar SSL",
                "description": f"{len(no_ssl)} endpoint(s) sem SSL. "
                               "Habilitar para conexões seguras.",
                "priority": "medium"
            })

        return recommendations
