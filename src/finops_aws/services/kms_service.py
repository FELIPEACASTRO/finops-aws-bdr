"""
AWS KMS FinOps Service

Análise de chaves KMS, aliases e recomendações de criptografia.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class KMSKey:
    """Representa uma chave KMS"""
    key_id: str
    arn: Optional[str] = None
    description: Optional[str] = None
    key_state: str = 'Enabled'
    key_usage: str = 'ENCRYPT_DECRYPT'
    key_spec: str = 'SYMMETRIC_DEFAULT'
    key_manager: str = 'CUSTOMER'
    origin: str = 'AWS_KMS'
    creation_date: Optional[datetime] = None
    deletion_date: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    enabled: bool = True
    multi_region: bool = False
    aliases: List[str] = field(default_factory=list)
    
    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.key_state == 'Enabled'
    
    @property
    def is_customer_managed(self) -> bool:
        return self.key_manager == 'CUSTOMER'
    
    @property
    def is_aws_managed(self) -> bool:
        return self.key_manager == 'AWS'
    
    @property
    def is_symmetric(self) -> bool:
        return 'SYMMETRIC' in self.key_spec
    
    @property
    def is_asymmetric(self) -> bool:
        return 'RSA' in self.key_spec or 'ECC' in self.key_spec
    
    @property
    def is_pending_deletion(self) -> bool:
        return self.key_state == 'PendingDeletion'
    
    @property
    def is_imported(self) -> bool:
        return self.origin == 'EXTERNAL'
    
    @property
    def is_multi_region(self) -> bool:
        return self.multi_region
    
    @property
    def has_alias(self) -> bool:
        return len(self.aliases) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key_id': self.key_id,
            'arn': self.arn,
            'description': self.description,
            'key_state': self.key_state,
            'key_usage': self.key_usage,
            'key_spec': self.key_spec,
            'key_manager': self.key_manager,
            'origin': self.origin,
            'is_enabled': self.is_enabled,
            'is_customer_managed': self.is_customer_managed,
            'is_aws_managed': self.is_aws_managed,
            'is_symmetric': self.is_symmetric,
            'is_asymmetric': self.is_asymmetric,
            'is_pending_deletion': self.is_pending_deletion,
            'is_imported': self.is_imported,
            'is_multi_region': self.is_multi_region,
            'has_alias': self.has_alias,
            'alias_count': len(self.aliases)
        }


@dataclass
class KeyAlias:
    """Representa um alias de chave KMS"""
    alias_name: str
    alias_arn: Optional[str] = None
    target_key_id: Optional[str] = None
    creation_date: Optional[datetime] = None
    last_updated_date: Optional[datetime] = None
    
    @property
    def is_aws_alias(self) -> bool:
        return self.alias_name.startswith('alias/aws/')
    
    @property
    def is_custom_alias(self) -> bool:
        return not self.is_aws_alias
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alias_name': self.alias_name,
            'alias_arn': self.alias_arn,
            'target_key_id': self.target_key_id,
            'is_aws_alias': self.is_aws_alias,
            'is_custom_alias': self.is_custom_alias
        }


@dataclass
class Grant:
    """Representa um grant de chave KMS"""
    key_id: str
    grant_id: str
    grantee_principal: str = ''
    retiring_principal: Optional[str] = None
    operations: List[str] = field(default_factory=list)
    name: Optional[str] = None
    creation_date: Optional[datetime] = None
    
    @property
    def operation_count(self) -> int:
        return len(self.operations)
    
    @property
    def allows_decrypt(self) -> bool:
        return 'Decrypt' in self.operations
    
    @property
    def allows_encrypt(self) -> bool:
        return 'Encrypt' in self.operations
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key_id': self.key_id,
            'grant_id': self.grant_id,
            'grantee_principal': self.grantee_principal,
            'name': self.name,
            'operations': self.operations,
            'operation_count': self.operation_count,
            'allows_decrypt': self.allows_decrypt,
            'allows_encrypt': self.allows_encrypt
        }


class KMSService(BaseAWSService):
    """Serviço FinOps para AWS KMS"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._kms_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "kms"
    
    @property
    def kms_client(self):
        if self._kms_client is None:
            if self._client_factory:
                self._kms_client = self._client_factory.get_client('kms')
            else:
                import boto3
                self._kms_client = boto3.client('kms')
        return self._kms_client
    
    def health_check(self) -> bool:
        try:
            self.kms_client.list_keys(Limit=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_keys(self) -> List[KMSKey]:
        keys = []
        try:
            paginator = self.kms_client.get_paginator('list_keys')
            
            for page in paginator.paginate():
                for key_entry in page.get('Keys', []):
                    key_id = key_entry.get('KeyId', '')
                    
                    try:
                        response = self.kms_client.describe_key(KeyId=key_id)
                        metadata = response.get('KeyMetadata', {})
                        
                        key = KMSKey(
                            key_id=key_id,
                            arn=metadata.get('Arn'),
                            description=metadata.get('Description'),
                            key_state=metadata.get('KeyState', 'Enabled'),
                            key_usage=metadata.get('KeyUsage', 'ENCRYPT_DECRYPT'),
                            key_spec=metadata.get('KeySpec', 'SYMMETRIC_DEFAULT'),
                            key_manager=metadata.get('KeyManager', 'CUSTOMER'),
                            origin=metadata.get('Origin', 'AWS_KMS'),
                            creation_date=metadata.get('CreationDate'),
                            deletion_date=metadata.get('DeletionDate'),
                            valid_to=metadata.get('ValidTo'),
                            enabled=metadata.get('Enabled', True),
                            multi_region=metadata.get('MultiRegion', False)
                        )
                        
                        try:
                            aliases_response = self.kms_client.list_aliases(KeyId=key_id)
                            key.aliases = [a.get('AliasName', '') for a in aliases_response.get('Aliases', [])]
                        except Exception as e:  # noqa: E722
                            pass
                        
                        keys.append(key)
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter detalhes da chave {key_id}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar chaves KMS: {e}")
        
        return keys
    
    def get_aliases(self) -> List[KeyAlias]:
        aliases = []
        try:
            paginator = self.kms_client.get_paginator('list_aliases')
            
            for page in paginator.paginate():
                for alias in page.get('Aliases', []):
                    aliases.append(KeyAlias(
                        alias_name=alias.get('AliasName', ''),
                        alias_arn=alias.get('AliasArn'),
                        target_key_id=alias.get('TargetKeyId'),
                        creation_date=alias.get('CreationDate'),
                        last_updated_date=alias.get('LastUpdatedDate')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar aliases: {e}")
        
        return aliases
    
    def get_grants(self, key_id: str) -> List[Grant]:
        grants = []
        try:
            paginator = self.kms_client.get_paginator('list_grants')
            
            for page in paginator.paginate(KeyId=key_id):
                for grant in page.get('Grants', []):
                    grants.append(Grant(
                        key_id=key_id,
                        grant_id=grant.get('GrantId', ''),
                        grantee_principal=grant.get('GranteePrincipal', ''),
                        retiring_principal=grant.get('RetiringPrincipal'),
                        operations=grant.get('Operations', []),
                        name=grant.get('Name'),
                        creation_date=grant.get('CreationDate')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar grants para {key_id}: {e}")
        
        return grants
    
    def get_resources(self) -> Dict[str, Any]:
        keys = self.get_keys()
        aliases = self.get_aliases()
        
        return {
            'keys': [k.to_dict() for k in keys],
            'aliases': [a.to_dict() for a in aliases],
            'summary': {
                'total_keys': len(keys),
                'enabled_keys': sum(1 for k in keys if k.is_enabled),
                'customer_managed_keys': sum(1 for k in keys if k.is_customer_managed),
                'aws_managed_keys': sum(1 for k in keys if k.is_aws_managed),
                'symmetric_keys': sum(1 for k in keys if k.is_symmetric),
                'asymmetric_keys': sum(1 for k in keys if k.is_asymmetric),
                'multi_region_keys': sum(1 for k in keys if k.is_multi_region),
                'pending_deletion': sum(1 for k in keys if k.is_pending_deletion),
                'total_aliases': len(aliases),
                'custom_aliases': sum(1 for a in aliases if a.is_custom_alias)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        keys = self.get_keys()
        
        return {
            'total_keys': len(keys),
            'key_states': {
                'enabled': sum(1 for k in keys if k.is_enabled),
                'disabled': sum(1 for k in keys if not k.is_enabled and not k.is_pending_deletion),
                'pending_deletion': sum(1 for k in keys if k.is_pending_deletion)
            },
            'key_managers': {
                'customer': sum(1 for k in keys if k.is_customer_managed),
                'aws': sum(1 for k in keys if k.is_aws_managed)
            },
            'key_types': {
                'symmetric': sum(1 for k in keys if k.is_symmetric),
                'asymmetric': sum(1 for k in keys if k.is_asymmetric)
            },
            'key_origins': {
                'aws_kms': sum(1 for k in keys if not k.is_imported),
                'imported': sum(1 for k in keys if k.is_imported)
            }
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        keys = self.get_keys()
        
        customer_keys = [k for k in keys if k.is_customer_managed]
        
        for key in customer_keys:
            if not key.is_enabled and not key.is_pending_deletion:
                recommendations.append({
                    'resource_id': key.key_id,
                    'resource_type': 'KMS Key',
                    'title': 'Chave desabilitada',
                    'description': f'Chave {key.key_id} está desabilitada mas não agendada para exclusão.',
                    'action': 'Avaliar se a chave ainda é necessária ou agendar exclusão',
                    'estimated_savings': 'Baixo',
                    'priority': 'LOW'
                })
            
            if not key.has_alias:
                recommendations.append({
                    'resource_id': key.key_id,
                    'resource_type': 'KMS Key',
                    'title': 'Chave sem alias',
                    'description': f'Chave {key.key_id} não tem alias configurado.',
                    'action': 'Criar alias para facilitar identificação e uso da chave',
                    'estimated_savings': 'N/A',
                    'priority': 'LOW'
                })
            
            if key.is_imported:
                recommendations.append({
                    'resource_id': key.key_id,
                    'resource_type': 'KMS Key',
                    'title': 'Chave importada',
                    'description': f'Chave {key.key_id} foi importada. Requer gerenciamento manual de expiração.',
                    'action': 'Monitorar validade e planejar rotação de material criptográfico',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
        
        if len(customer_keys) > 50:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'KMS',
                'title': f'Grande número de chaves gerenciadas ({len(customer_keys)})',
                'description': f'Conta tem {len(customer_keys)} chaves customer-managed. Cada chave custa $1/mês.',
                'action': 'Revisar e consolidar chaves onde possível para reduzir custos',
                'estimated_savings': 'Médio',
                'priority': 'MEDIUM'
            })
        
        return recommendations
