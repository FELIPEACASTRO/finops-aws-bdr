"""
AWS IAM FinOps Service.

Análise de custos e métricas do AWS IAM para segurança e identidade.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class IAMUser:
    """Representa um usuário IAM."""
    
    user_name: str = ""
    user_id: str = ""
    arn: str = ""
    path: str = ""
    create_date: Optional[datetime] = None
    password_last_used: Optional[datetime] = None
    permissions_boundary: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    access_keys: List[Dict[str, Any]] = field(default_factory=list)
    mfa_devices: List[Dict[str, Any]] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    
    @property
    def has_console_access(self) -> bool:
        """Verifica se tem acesso ao console."""
        return self.password_last_used is not None
    
    @property
    def has_access_keys(self) -> bool:
        """Verifica se tem access keys."""
        return bool(self.access_keys)
    
    @property
    def has_mfa(self) -> bool:
        """Verifica se tem MFA."""
        return bool(self.mfa_devices)
    
    @property
    def has_permissions_boundary(self) -> bool:
        """Verifica se tem permissions boundary."""
        return bool(self.permissions_boundary)
    
    @property
    def has_groups(self) -> bool:
        """Verifica se pertence a grupos."""
        return bool(self.groups)
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    @property
    def active_access_keys(self) -> int:
        """Retorna quantidade de access keys ativas."""
        return len([k for k in self.access_keys if k.get("Status") == "Active"])
    
    @property
    def is_inactive(self) -> bool:
        """Verifica se usuário está inativo (90+ dias sem login)."""
        if not self.password_last_used:
            return True
        days_inactive = (datetime.now(timezone.utc) - self.password_last_used).days
        return days_inactive > 90
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "user_name": self.user_name,
            "user_id": self.user_id,
            "has_console_access": self.has_console_access,
            "has_access_keys": self.has_access_keys,
            "has_mfa": self.has_mfa,
            "active_access_keys": self.active_access_keys,
            "is_inactive": self.is_inactive,
            "has_groups": self.has_groups
        }


@dataclass
class IAMRole:
    """Representa uma role IAM."""
    
    role_name: str = ""
    role_id: str = ""
    arn: str = ""
    path: str = ""
    create_date: Optional[datetime] = None
    max_session_duration: int = 3600
    description: str = ""
    assume_role_policy_document: Dict[str, Any] = field(default_factory=dict)
    permissions_boundary: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    last_used: Optional[Dict[str, Any]] = None
    
    @property
    def is_service_role(self) -> bool:
        """Verifica se é service role."""
        principals = self._get_principals()
        return any("amazonaws.com" in str(p) for p in principals)
    
    @property
    def is_cross_account(self) -> bool:
        """Verifica se permite cross-account access."""
        principals = self._get_principals()
        return any("arn:aws:iam::" in str(p) for p in principals)
    
    @property
    def has_permissions_boundary(self) -> bool:
        """Verifica se tem permissions boundary."""
        return bool(self.permissions_boundary)
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    @property
    def has_description(self) -> bool:
        """Verifica se tem descrição."""
        return bool(self.description)
    
    @property
    def is_recently_used(self) -> bool:
        """Verifica se foi usada recentemente (30 dias)."""
        if not self.last_used:
            return False
        last_used_date = self.last_used.get("LastUsedDate")
        if not last_used_date:
            return False
        days = (datetime.now(timezone.utc) - last_used_date).days
        return days <= 30
    
    @property
    def is_unused(self) -> bool:
        """Verifica se não foi usada nos últimos 90 dias."""
        if not self.last_used:
            return True
        last_used_date = self.last_used.get("LastUsedDate")
        if not last_used_date:
            return True
        days = (datetime.now(timezone.utc) - last_used_date).days
        return days > 90
    
    def _get_principals(self) -> List[Any]:
        """Obtém principals da policy de assume role."""
        statements = self.assume_role_policy_document.get("Statement", [])
        principals = []
        for stmt in statements:
            principal = stmt.get("Principal", {})
            if isinstance(principal, dict):
                principals.extend(principal.get("Service", []))
                principals.extend(principal.get("AWS", []))
            elif isinstance(principal, str):
                principals.append(principal)
        return principals
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "role_name": self.role_name,
            "role_id": self.role_id,
            "is_service_role": self.is_service_role,
            "is_cross_account": self.is_cross_account,
            "has_permissions_boundary": self.has_permissions_boundary,
            "is_recently_used": self.is_recently_used,
            "is_unused": self.is_unused
        }


@dataclass
class IAMPolicy:
    """Representa uma policy IAM."""
    
    policy_name: str = ""
    policy_id: str = ""
    arn: str = ""
    path: str = ""
    default_version_id: str = ""
    attachment_count: int = 0
    permissions_boundary_usage_count: int = 0
    is_attachable: bool = True
    create_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_attached(self) -> bool:
        """Verifica se está anexada."""
        return self.attachment_count > 0
    
    @property
    def is_unattached(self) -> bool:
        """Verifica se não está anexada."""
        return self.attachment_count == 0
    
    @property
    def is_permissions_boundary(self) -> bool:
        """Verifica se é usada como permissions boundary."""
        return self.permissions_boundary_usage_count > 0
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    @property
    def has_description(self) -> bool:
        """Verifica se tem descrição."""
        return bool(self.description)
    
    @property
    def is_aws_managed(self) -> bool:
        """Verifica se é policy AWS managed."""
        return "arn:aws:iam::aws:" in self.arn
    
    @property
    def is_customer_managed(self) -> bool:
        """Verifica se é policy customer managed."""
        return not self.is_aws_managed
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "policy_name": self.policy_name,
            "policy_id": self.policy_id,
            "arn": self.arn,
            "attachment_count": self.attachment_count,
            "is_attached": self.is_attached,
            "is_aws_managed": self.is_aws_managed,
            "is_customer_managed": self.is_customer_managed
        }


class IAMService(BaseAWSService):
    """Serviço FinOps para AWS IAM."""

    def __init__(self, client_factory):
        """Inicializa o serviço IAM."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente IAM."""
        return self._client_factory.get_client("iam")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.list_users(MaxItems=1)
            return {"status": "healthy", "service": "iam"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "iam", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos IAM."""
        client = self._get_client()
        
        users = self._list_users(client)
        roles = self._list_roles(client)
        policies = self._list_policies(client)
        
        users_without_mfa = [u for u in users if not u.has_mfa]
        inactive_users = [u for u in users if u.is_inactive]
        unused_roles = [r for r in roles if r.is_unused]
        unattached_policies = [p for p in policies if p.is_unattached]
        
        return {
            "users": [u.to_dict() for u in users],
            "roles": [r.to_dict() for r in roles],
            "policies": [p.to_dict() for p in policies],
            "summary": {
                "total_users": len(users),
                "users_without_mfa": len(users_without_mfa),
                "inactive_users": len(inactive_users),
                "total_roles": len(roles),
                "unused_roles": len(unused_roles),
                "total_policies": len(policies),
                "unattached_policies": len(unattached_policies)
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos IAM."""
        return {
            "estimated_monthly": 0.0,
            "cost_factors": {
                "iam_users": "IAM é gratuito",
                "iam_roles": "IAM é gratuito",
                "iam_policies": "IAM é gratuito"
            },
            "note": "IAM não tem custos diretos, mas impacta segurança"
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas IAM."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "users_count": summary["total_users"],
            "users_without_mfa": summary["users_without_mfa"],
            "inactive_users": summary["inactive_users"],
            "roles_count": summary["total_roles"],
            "unused_roles": summary["unused_roles"],
            "policies_count": summary["total_policies"],
            "unattached_policies": summary["unattached_policies"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de segurança."""
        recommendations = []
        resources = self.get_resources()
        
        for user in resources["users"]:
            if not user.get("has_mfa") and user.get("has_console_access"):
                recommendations.append({
                    "type": "ENABLE_MFA",
                    "resource": user["user_name"],
                    "description": f"Usuário '{user['user_name']}' sem MFA habilitado",
                    "impact": "critical",
                    "action": "Habilitar MFA para o usuário"
                })
            
            if user.get("is_inactive"):
                recommendations.append({
                    "type": "REMOVE_INACTIVE_USER",
                    "resource": user["user_name"],
                    "description": f"Usuário '{user['user_name']}' inativo há mais de 90 dias",
                    "impact": "high",
                    "action": "Revisar e possivelmente remover usuário"
                })
        
        for role in resources["roles"]:
            if role.get("is_unused"):
                recommendations.append({
                    "type": "REMOVE_UNUSED_ROLE",
                    "resource": role["role_name"],
                    "description": f"Role '{role['role_name']}' não usada há mais de 90 dias",
                    "impact": "medium",
                    "action": "Revisar e possivelmente remover role"
                })
        
        for policy in resources["policies"]:
            if not policy.get("is_attached") and policy.get("is_customer_managed"):
                recommendations.append({
                    "type": "REMOVE_UNATTACHED_POLICY",
                    "resource": policy["policy_name"],
                    "description": f"Policy '{policy['policy_name']}' não está anexada a nada",
                    "impact": "low",
                    "action": "Revisar e possivelmente remover policy"
                })
        
        return recommendations

    def _list_users(self, client) -> List[IAMUser]:
        """Lista usuários IAM."""
        users = []
        try:
            paginator = client.get_paginator("list_users")
            for page in paginator.paginate():
                for user in page.get("Users", []):
                    tags = {t["Key"]: t["Value"] for t in user.get("Tags", [])}
                    users.append(IAMUser(
                        user_name=user.get("UserName", ""),
                        user_id=user.get("UserId", ""),
                        arn=user.get("Arn", ""),
                        path=user.get("Path", ""),
                        create_date=user.get("CreateDate"),
                        password_last_used=user.get("PasswordLastUsed"),
                        permissions_boundary=user.get("PermissionsBoundary", {}),
                        tags=tags
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing users: {e}")
        return users

    def _list_roles(self, client) -> List[IAMRole]:
        """Lista roles IAM."""
        roles = []
        try:
            paginator = client.get_paginator("list_roles")
            for page in paginator.paginate():
                for role in page.get("Roles", []):
                    tags = {t["Key"]: t["Value"] for t in role.get("Tags", [])}
                    roles.append(IAMRole(
                        role_name=role.get("RoleName", ""),
                        role_id=role.get("RoleId", ""),
                        arn=role.get("Arn", ""),
                        path=role.get("Path", ""),
                        create_date=role.get("CreateDate"),
                        max_session_duration=role.get("MaxSessionDuration", 3600),
                        description=role.get("Description", ""),
                        assume_role_policy_document=role.get("AssumeRolePolicyDocument", {}),
                        permissions_boundary=role.get("PermissionsBoundary", {}),
                        tags=tags
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing roles: {e}")
        return roles

    def _list_policies(self, client) -> List[IAMPolicy]:
        """Lista policies IAM."""
        policies = []
        try:
            paginator = client.get_paginator("list_policies")
            for page in paginator.paginate(Scope="Local"):
                for policy in page.get("Policies", []):
                    tags = {t["Key"]: t["Value"] for t in policy.get("Tags", [])}
                    policies.append(IAMPolicy(
                        policy_name=policy.get("PolicyName", ""),
                        policy_id=policy.get("PolicyId", ""),
                        arn=policy.get("Arn", ""),
                        path=policy.get("Path", ""),
                        default_version_id=policy.get("DefaultVersionId", ""),
                        attachment_count=policy.get("AttachmentCount", 0),
                        permissions_boundary_usage_count=policy.get("PermissionsBoundaryUsageCount", 0),
                        is_attachable=policy.get("IsAttachable", True),
                        create_date=policy.get("CreateDate"),
                        update_date=policy.get("UpdateDate"),
                        description=policy.get("Description", ""),
                        tags=tags
                    ))
        except Exception as e:
            self.logger.warning(f"Error listing policies: {e}")
        return policies
