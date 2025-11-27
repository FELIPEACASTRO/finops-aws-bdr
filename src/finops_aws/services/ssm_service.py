"""
AWS Systems Manager (SSM) FinOps Service.

Análise de custos e métricas do AWS Systems Manager.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class SSMParameter:
    """Representa um parâmetro SSM."""
    
    name: str = ""
    type: str = ""
    key_id: str = ""
    last_modified_date: Optional[datetime] = None
    last_modified_user: str = ""
    version: int = 0
    tier: str = ""
    policies: List[Dict[str, Any]] = field(default_factory=list)
    data_type: str = ""
    
    @property
    def is_secure_string(self) -> bool:
        """Verifica se é SecureString."""
        return self.type.upper() == "SECURESTRING"
    
    @property
    def is_string(self) -> bool:
        """Verifica se é String."""
        return self.type.upper() == "STRING"
    
    @property
    def is_string_list(self) -> bool:
        """Verifica se é StringList."""
        return self.type.upper() == "STRINGLIST"
    
    @property
    def is_advanced(self) -> bool:
        """Verifica se é tier Advanced."""
        return self.tier.upper() == "ADVANCED"
    
    @property
    def is_standard(self) -> bool:
        """Verifica se é tier Standard."""
        return self.tier.upper() == "STANDARD"
    
    @property
    def is_intelligent_tiering(self) -> bool:
        """Verifica se usa Intelligent-Tiering."""
        return self.tier.upper() == "INTELLIGENT-TIERING"
    
    @property
    def has_kms(self) -> bool:
        """Verifica se usa KMS."""
        return bool(self.key_id)
    
    @property
    def has_policies(self) -> bool:
        """Verifica se tem políticas."""
        return bool(self.policies)
    
    @property
    def monthly_cost(self) -> float:
        """Calcula custo mensal estimado."""
        if self.is_advanced:
            return 0.05
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "type": self.type,
            "tier": self.tier,
            "version": self.version,
            "is_secure_string": self.is_secure_string,
            "is_advanced": self.is_advanced,
            "has_kms": self.has_kms,
            "monthly_cost": self.monthly_cost
        }


@dataclass
class SSMDocument:
    """Representa um documento SSM."""
    
    name: str = ""
    document_type: str = ""
    document_format: str = ""
    document_version: str = ""
    owner: str = ""
    status: str = ""
    platform_types: List[str] = field(default_factory=list)
    target_type: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Verifica se documento está ativo."""
        return self.status.upper() == "ACTIVE"
    
    @property
    def is_creating(self) -> bool:
        """Verifica se está criando."""
        return self.status.upper() == "CREATING"
    
    @property
    def is_updating(self) -> bool:
        """Verifica se está atualizando."""
        return self.status.upper() == "UPDATING"
    
    @property
    def is_deleting(self) -> bool:
        """Verifica se está deletando."""
        return self.status.upper() == "DELETING"
    
    @property
    def is_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status.upper() == "FAILED"
    
    @property
    def is_command(self) -> bool:
        """Verifica se é tipo Command."""
        return self.document_type.upper() == "COMMAND"
    
    @property
    def is_automation(self) -> bool:
        """Verifica se é tipo Automation."""
        return self.document_type.upper() == "AUTOMATION"
    
    @property
    def is_policy(self) -> bool:
        """Verifica se é tipo Policy."""
        return self.document_type.upper() == "POLICY"
    
    @property
    def is_session(self) -> bool:
        """Verifica se é tipo Session."""
        return self.document_type.upper() == "SESSION"
    
    @property
    def is_package(self) -> bool:
        """Verifica se é tipo Package."""
        return self.document_type.upper() == "PACKAGE"
    
    @property
    def supports_linux(self) -> bool:
        """Verifica se suporta Linux."""
        return "Linux" in self.platform_types
    
    @property
    def supports_windows(self) -> bool:
        """Verifica se suporta Windows."""
        return "Windows" in self.platform_types
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "document_type": self.document_type,
            "document_format": self.document_format,
            "status": self.status,
            "is_active": self.is_active,
            "is_automation": self.is_automation,
            "platform_types": self.platform_types
        }


@dataclass
class SSMManagedInstance:
    """Representa uma instância gerenciada SSM."""
    
    instance_id: str = ""
    ping_status: str = ""
    last_ping_date_time: Optional[datetime] = None
    platform_type: str = ""
    platform_name: str = ""
    platform_version: str = ""
    activation_id: str = ""
    iam_role: str = ""
    registration_date: Optional[datetime] = None
    resource_type: str = ""
    name: str = ""
    ip_address: str = ""
    computer_name: str = ""
    association_status: str = ""
    last_association_execution_date: Optional[datetime] = None
    agent_version: str = ""
    is_latest_version: bool = False
    
    @property
    def is_online(self) -> bool:
        """Verifica se instância está online."""
        return self.ping_status.upper() == "ONLINE"
    
    @property
    def is_connection_lost(self) -> bool:
        """Verifica se perdeu conexão."""
        return self.ping_status.upper() == "CONNECTIONLOST"
    
    @property
    def is_inactive(self) -> bool:
        """Verifica se está inativa."""
        return self.ping_status.upper() == "INACTIVE"
    
    @property
    def is_ec2(self) -> bool:
        """Verifica se é EC2."""
        return self.resource_type.upper() == "EC2INSTANCE"
    
    @property
    def is_managed_instance(self) -> bool:
        """Verifica se é managed instance."""
        return self.resource_type.upper() == "MANAGEDINSTANCE"
    
    @property
    def is_linux(self) -> bool:
        """Verifica se é Linux."""
        return self.platform_type.upper() == "LINUX"
    
    @property
    def is_windows(self) -> bool:
        """Verifica se é Windows."""
        return self.platform_type.upper() == "WINDOWS"
    
    @property
    def needs_update(self) -> bool:
        """Verifica se precisa atualização."""
        return not self.is_latest_version
    
    @property
    def has_association(self) -> bool:
        """Verifica se tem association."""
        return self.association_status.upper() == "SUCCESS"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "instance_id": self.instance_id,
            "name": self.name,
            "ping_status": self.ping_status,
            "platform_type": self.platform_type,
            "is_online": self.is_online,
            "is_ec2": self.is_ec2,
            "needs_update": self.needs_update,
            "agent_version": self.agent_version
        }


class SSMService(BaseAWSService):
    """Serviço FinOps para AWS Systems Manager."""

    def __init__(self, client_factory):
        """Inicializa o serviço SSM."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente SSM."""
        return self._client_factory.get_client("ssm")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.describe_parameters(MaxResults=1)
            return {"status": "healthy", "service": "ssm"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "ssm", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos SSM."""
        client = self._get_client()
        
        parameters = self._list_parameters(client)
        documents = self._list_documents(client)
        instances = self._list_managed_instances(client)
        
        advanced_params = [p for p in parameters if p.is_advanced]
        secure_params = [p for p in parameters if p.is_secure_string]
        online_instances = [i for i in instances if i.is_online]
        
        return {
            "parameters": [p.to_dict() for p in parameters],
            "documents": [d.to_dict() for d in documents],
            "managed_instances": [i.to_dict() for i in instances],
            "summary": {
                "total_parameters": len(parameters),
                "advanced_parameters": len(advanced_params),
                "secure_parameters": len(secure_params),
                "total_documents": len(documents),
                "total_managed_instances": len(instances),
                "online_instances": len(online_instances)
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos SSM."""
        resources = self.get_resources()
        
        advanced_params = resources["summary"]["advanced_parameters"]
        advanced_cost = advanced_params * 0.05
        
        return {
            "estimated_monthly": advanced_cost,
            "cost_factors": {
                "advanced_parameters": advanced_cost,
                "standard_parameters": 0.0,
                "on_demand_automation": "pay per step",
                "session_manager": "free for basic usage"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas SSM."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "parameters_count": summary["total_parameters"],
            "advanced_parameters": summary["advanced_parameters"],
            "secure_parameters": summary["secure_parameters"],
            "documents_count": summary["total_documents"],
            "managed_instances": summary["total_managed_instances"],
            "online_instances": summary["online_instances"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de otimização."""
        recommendations = []
        resources = self.get_resources()
        
        for instance in resources["managed_instances"]:
            if instance.get("needs_update"):
                recommendations.append({
                    "type": "UPDATE_AGENT",
                    "resource": instance["instance_id"],
                    "description": f"Instância '{instance['instance_id']}' precisa atualizar SSM Agent",
                    "impact": "medium",
                    "action": "Atualizar SSM Agent para versão mais recente"
                })
            
            if not instance.get("is_online"):
                recommendations.append({
                    "type": "CHECK_CONNECTIVITY",
                    "resource": instance["instance_id"],
                    "description": f"Instância '{instance['instance_id']}' não está online",
                    "impact": "high",
                    "action": "Verificar conectividade e status do SSM Agent"
                })
        
        for param in resources["parameters"]:
            if param.get("is_advanced") and not param.get("has_policies"):
                recommendations.append({
                    "type": "REVIEW_TIER",
                    "resource": param["name"],
                    "description": f"Parâmetro '{param['name']}' é Advanced mas pode não precisar",
                    "impact": "low",
                    "action": "Avaliar se tier Standard é suficiente"
                })
        
        return recommendations

    def _list_parameters(self, client) -> List[SSMParameter]:
        """Lista parâmetros SSM."""
        parameters = []
        try:
            paginator = client.get_paginator("describe_parameters")
            for page in paginator.paginate():
                for param in page.get("Parameters", []):
                    parameters.append(SSMParameter(
                        name=param.get("Name", ""),
                        type=param.get("Type", ""),
                        key_id=param.get("KeyId", ""),
                        last_modified_date=param.get("LastModifiedDate"),
                        last_modified_user=param.get("LastModifiedUser", ""),
                        version=param.get("Version", 0),
                        tier=param.get("Tier", "Standard"),
                        policies=param.get("Policies", []),
                        data_type=param.get("DataType", "")
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing parameters: {e}")
        return parameters

    def _list_documents(self, client) -> List[SSMDocument]:
        """Lista documentos SSM."""
        documents = []
        try:
            paginator = client.get_paginator("list_documents")
            for page in paginator.paginate(Filters=[{"Key": "Owner", "Values": ["Self"]}]):
                for doc in page.get("DocumentIdentifiers", []):
                    tags = {t["Key"]: t["Value"] for t in doc.get("Tags", [])}
                    documents.append(SSMDocument(
                        name=doc.get("Name", ""),
                        document_type=doc.get("DocumentType", ""),
                        document_format=doc.get("DocumentFormat", ""),
                        document_version=doc.get("DocumentVersion", ""),
                        owner=doc.get("Owner", ""),
                        status=doc.get("Status", ""),
                        platform_types=doc.get("PlatformTypes", []),
                        target_type=doc.get("TargetType", ""),
                        tags=tags
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing documents: {e}")
        return documents

    def _list_managed_instances(self, client) -> List[SSMManagedInstance]:
        """Lista instâncias gerenciadas SSM."""
        instances = []
        try:
            paginator = client.get_paginator("describe_instance_information")
            for page in paginator.paginate():
                for inst in page.get("InstanceInformationList", []):
                    instances.append(SSMManagedInstance(
                        instance_id=inst.get("InstanceId", ""),
                        ping_status=inst.get("PingStatus", ""),
                        last_ping_date_time=inst.get("LastPingDateTime"),
                        platform_type=inst.get("PlatformType", ""),
                        platform_name=inst.get("PlatformName", ""),
                        platform_version=inst.get("PlatformVersion", ""),
                        activation_id=inst.get("ActivationId", ""),
                        iam_role=inst.get("IamRole", ""),
                        registration_date=inst.get("RegistrationDate"),
                        resource_type=inst.get("ResourceType", ""),
                        name=inst.get("Name", ""),
                        ip_address=inst.get("IPAddress", ""),
                        computer_name=inst.get("ComputerName", ""),
                        association_status=inst.get("AssociationStatus", ""),
                        last_association_execution_date=inst.get("LastAssociationExecutionDate"),
                        agent_version=inst.get("AgentVersion", ""),
                        is_latest_version=inst.get("IsLatestVersion", False)
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing managed instances: {e}")
        return instances
