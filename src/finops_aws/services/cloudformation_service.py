"""
AWS CloudFormation FinOps Service.

Análise de custos e métricas do CloudFormation para Infrastructure as Code.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class CloudFormationStack:
    """Representa uma stack CloudFormation."""
    
    stack_id: str = ""
    stack_name: str = ""
    stack_status: str = ""
    creation_time: Optional[datetime] = None
    last_updated_time: Optional[datetime] = None
    deletion_time: Optional[datetime] = None
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    enable_termination_protection: bool = False
    drift_information: Dict[str, Any] = field(default_factory=dict)
    role_arn: str = ""
    
    @property
    def is_complete(self) -> bool:
        """Verifica se stack está completa."""
        return "COMPLETE" in self.stack_status and "FAILED" not in self.stack_status
    
    @property
    def is_in_progress(self) -> bool:
        """Verifica se stack está em progresso."""
        return "IN_PROGRESS" in self.stack_status
    
    @property
    def is_failed(self) -> bool:
        """Verifica se stack falhou."""
        return "FAILED" in self.stack_status or "ROLLBACK" in self.stack_status
    
    @property
    def is_deleted(self) -> bool:
        """Verifica se stack foi deletada."""
        return "DELETE_COMPLETE" in self.stack_status
    
    @property
    def has_drift(self) -> bool:
        """Verifica se stack tem drift."""
        status = self.drift_information.get("StackDriftStatus", "")
        return status == "DRIFTED"
    
    @property
    def has_termination_protection(self) -> bool:
        """Verifica se tem proteção de terminação."""
        return bool(self.enable_termination_protection)
    
    @property
    def has_iam_capability(self) -> bool:
        """Verifica se tem capability IAM."""
        return "CAPABILITY_IAM" in self.capabilities or "CAPABILITY_NAMED_IAM" in self.capabilities
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    @property
    def has_outputs(self) -> bool:
        """Verifica se tem outputs."""
        return bool(self.outputs)
    
    @property
    def has_role(self) -> bool:
        """Verifica se tem role IAM."""
        return bool(self.role_arn)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "stack_id": self.stack_id,
            "stack_name": self.stack_name,
            "stack_status": self.stack_status,
            "is_complete": self.is_complete,
            "is_failed": self.is_failed,
            "has_drift": self.has_drift,
            "has_termination_protection": self.has_termination_protection,
            "has_iam_capability": self.has_iam_capability,
            "has_tags": self.has_tags
        }


@dataclass
class CloudFormationStackSet:
    """Representa um StackSet CloudFormation."""
    
    stack_set_id: str = ""
    stack_set_name: str = ""
    status: str = ""
    description: str = ""
    permission_model: str = ""
    auto_deployment: Dict[str, Any] = field(default_factory=dict)
    managed_execution: Dict[str, Any] = field(default_factory=dict)
    regions: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Verifica se StackSet está ativo."""
        return self.status.upper() == "ACTIVE"
    
    @property
    def is_deleted(self) -> bool:
        """Verifica se StackSet foi deletado."""
        return self.status.upper() == "DELETED"
    
    @property
    def uses_self_managed(self) -> bool:
        """Verifica se usa modelo self-managed."""
        return self.permission_model.upper() == "SELF_MANAGED"
    
    @property
    def uses_service_managed(self) -> bool:
        """Verifica se usa modelo service-managed."""
        return self.permission_model.upper() == "SERVICE_MANAGED"
    
    @property
    def has_auto_deployment(self) -> bool:
        """Verifica se tem auto deployment."""
        return bool(self.auto_deployment.get("Enabled", False))
    
    @property
    def has_managed_execution(self) -> bool:
        """Verifica se tem managed execution."""
        return bool(self.managed_execution.get("Active", False))
    
    @property
    def is_multi_region(self) -> bool:
        """Verifica se é multi-região."""
        return len(self.regions) > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "stack_set_id": self.stack_set_id,
            "stack_set_name": self.stack_set_name,
            "status": self.status,
            "permission_model": self.permission_model,
            "is_active": self.is_active,
            "uses_service_managed": self.uses_service_managed,
            "has_auto_deployment": self.has_auto_deployment,
            "is_multi_region": self.is_multi_region,
            "regions_count": len(self.regions)
        }


@dataclass
class CloudFormationChangeSet:
    """Representa um ChangeSet CloudFormation."""
    
    change_set_id: str = ""
    change_set_name: str = ""
    stack_id: str = ""
    stack_name: str = ""
    status: str = ""
    execution_status: str = ""
    status_reason: str = ""
    creation_time: Optional[datetime] = None
    changes: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def is_available(self) -> bool:
        """Verifica se ChangeSet está disponível."""
        return self.status.upper() == "CREATE_COMPLETE"
    
    @property
    def is_pending(self) -> bool:
        """Verifica se ChangeSet está pendente."""
        return self.status.upper() == "CREATE_PENDING"
    
    @property
    def is_failed(self) -> bool:
        """Verifica se ChangeSet falhou."""
        return "FAILED" in self.status.upper()
    
    @property
    def is_executable(self) -> bool:
        """Verifica se ChangeSet é executável."""
        return self.execution_status.upper() == "AVAILABLE"
    
    @property
    def has_changes(self) -> bool:
        """Verifica se tem mudanças."""
        return bool(self.changes)
    
    @property
    def changes_count(self) -> int:
        """Retorna quantidade de mudanças."""
        return len(self.changes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "change_set_id": self.change_set_id,
            "change_set_name": self.change_set_name,
            "stack_name": self.stack_name,
            "status": self.status,
            "execution_status": self.execution_status,
            "is_available": self.is_available,
            "is_executable": self.is_executable,
            "changes_count": self.changes_count
        }


class CloudFormationService(BaseAWSService):
    """Serviço FinOps para AWS CloudFormation."""

    def __init__(self, client_factory):
        """Inicializa o serviço CloudFormation."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente CloudFormation."""
        return self._client_factory.get_client("cloudformation")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.list_stacks(StackStatusFilter=["CREATE_COMPLETE"])
            return {"status": "healthy", "service": "cloudformation"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "cloudformation", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos CloudFormation."""
        client = self._get_client()
        
        stacks = self._list_stacks(client)
        stack_sets = self._list_stack_sets(client)
        
        active_stacks = [s for s in stacks if s.is_complete]
        failed_stacks = [s for s in stacks if s.is_failed]
        drifted_stacks = [s for s in stacks if s.has_drift]
        
        return {
            "stacks": [s.to_dict() for s in stacks],
            "stack_sets": [ss.to_dict() for ss in stack_sets],
            "summary": {
                "total_stacks": len(stacks),
                "active_stacks": len(active_stacks),
                "failed_stacks": len(failed_stacks),
                "drifted_stacks": len(drifted_stacks),
                "total_stack_sets": len(stack_sets),
                "protected_stacks": len([s for s in stacks if s.has_termination_protection])
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos CloudFormation."""
        return {
            "estimated_monthly": 0.0,
            "cost_factors": {
                "stacks": "CloudFormation é gratuito, custos são dos recursos provisionados",
                "stack_sets": "Cobrado por operações em StackSets",
                "handler_operations": "Cobrado por operações de handler"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas CloudFormation."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "stacks_count": summary["total_stacks"],
            "active_stacks": summary["active_stacks"],
            "failed_stacks": summary["failed_stacks"],
            "drifted_stacks": summary["drifted_stacks"],
            "stack_sets_count": summary["total_stack_sets"],
            "protected_stacks": summary["protected_stacks"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de otimização."""
        recommendations = []
        resources = self.get_resources()
        
        for stack in resources["stacks"]:
            if stack.get("has_drift"):
                recommendations.append({
                    "type": "FIX_DRIFT",
                    "resource": stack["stack_name"],
                    "description": f"Stack '{stack['stack_name']}' tem drift detectado",
                    "impact": "high",
                    "action": "Revisar e corrigir drift"
                })
            
            if not stack.get("has_termination_protection") and stack.get("is_complete"):
                recommendations.append({
                    "type": "ENABLE_PROTECTION",
                    "resource": stack["stack_name"],
                    "description": f"Stack '{stack['stack_name']}' sem proteção de terminação",
                    "impact": "medium",
                    "action": "Habilitar termination protection"
                })
        
        return recommendations

    def _list_stacks(self, client) -> List[CloudFormationStack]:
        """Lista stacks CloudFormation."""
        stacks = []
        try:
            paginator = client.get_paginator("describe_stacks")
            for page in paginator.paginate():
                for stack in page.get("Stacks", []):
                    tags = {t["Key"]: t["Value"] for t in stack.get("Tags", [])}
                    stacks.append(CloudFormationStack(
                        stack_id=stack.get("StackId", ""),
                        stack_name=stack.get("StackName", ""),
                        stack_status=stack.get("StackStatus", ""),
                        creation_time=stack.get("CreationTime"),
                        last_updated_time=stack.get("LastUpdatedTime"),
                        description=stack.get("Description", ""),
                        parameters=stack.get("Parameters", []),
                        outputs=stack.get("Outputs", []),
                        capabilities=stack.get("Capabilities", []),
                        tags=tags,
                        enable_termination_protection=stack.get("EnableTerminationProtection", False),
                        drift_information=stack.get("DriftInformation", {}),
                        role_arn=stack.get("RoleARN", "")
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing stacks: {e}")
        return stacks

    def _list_stack_sets(self, client) -> List[CloudFormationStackSet]:
        """Lista StackSets CloudFormation."""
        stack_sets = []
        try:
            paginator = client.get_paginator("list_stack_sets")
            for page in paginator.paginate():
                for ss in page.get("Summaries", []):
                    stack_sets.append(CloudFormationStackSet(
                        stack_set_id=ss.get("StackSetId", ""),
                        stack_set_name=ss.get("StackSetName", ""),
                        status=ss.get("Status", ""),
                        description=ss.get("Description", ""),
                        permission_model=ss.get("PermissionModel", ""),
                        auto_deployment=ss.get("AutoDeployment", {}),
                        managed_execution=ss.get("ManagedExecution", {})
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing stack sets: {e}")
        return stack_sets
