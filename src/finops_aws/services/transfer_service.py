"""
AWS Transfer Family FinOps Service

Análise de custos e otimização para AWS Transfer Family:
- Servidores SFTP, FTPS, FTP, AS2
- Usuários e workflows
- Conectores
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class TransferServer:
    """Representa um servidor do AWS Transfer Family"""
    server_id: str
    arn: str
    domain: str = 'S3'
    endpoint_type: str = 'PUBLIC'
    identity_provider_type: str = 'SERVICE_MANAGED'
    protocols: List[str] = field(default_factory=list)
    state: str = 'ONLINE'
    user_count: int = 0
    logging_role: str = ''
    security_policy_name: str = ''
    structured_log_destinations: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_online(self) -> bool:
        return self.state == 'ONLINE'
    
    @property
    def is_offline(self) -> bool:
        return self.state == 'OFFLINE'
    
    @property
    def is_public(self) -> bool:
        return self.endpoint_type == 'PUBLIC'
    
    @property
    def is_vpc(self) -> bool:
        return self.endpoint_type == 'VPC'
    
    @property
    def is_vpc_endpoint(self) -> bool:
        return self.endpoint_type == 'VPC_ENDPOINT'
    
    @property
    def supports_sftp(self) -> bool:
        return 'SFTP' in self.protocols
    
    @property
    def supports_ftps(self) -> bool:
        return 'FTPS' in self.protocols
    
    @property
    def supports_ftp(self) -> bool:
        return 'FTP' in self.protocols
    
    @property
    def supports_as2(self) -> bool:
        return 'AS2' in self.protocols
    
    @property
    def uses_s3(self) -> bool:
        return self.domain == 'S3'
    
    @property
    def uses_efs(self) -> bool:
        return self.domain == 'EFS'
    
    @property
    def has_logging(self) -> bool:
        return bool(self.logging_role) or bool(self.structured_log_destinations)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'server_id': self.server_id,
            'arn': self.arn,
            'domain': self.domain,
            'endpoint_type': self.endpoint_type,
            'identity_provider_type': self.identity_provider_type,
            'protocols': self.protocols,
            'state': self.state,
            'is_online': self.is_online,
            'is_public': self.is_public,
            'is_vpc': self.is_vpc,
            'supports_sftp': self.supports_sftp,
            'supports_ftps': self.supports_ftps,
            'supports_ftp': self.supports_ftp,
            'supports_as2': self.supports_as2,
            'uses_s3': self.uses_s3,
            'uses_efs': self.uses_efs,
            'user_count': self.user_count,
            'has_logging': self.has_logging,
            'security_policy_name': self.security_policy_name,
            'tags': self.tags
        }


@dataclass
class TransferUser:
    """Representa um usuário do AWS Transfer Family"""
    user_name: str
    server_id: str
    arn: str = ''
    home_directory: str = ''
    home_directory_type: str = 'PATH'
    role: str = ''
    ssh_public_key_count: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def uses_logical_directory(self) -> bool:
        return self.home_directory_type == 'LOGICAL'
    
    @property
    def has_ssh_keys(self) -> bool:
        return self.ssh_public_key_count > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_name': self.user_name,
            'server_id': self.server_id,
            'arn': self.arn,
            'home_directory': self.home_directory,
            'home_directory_type': self.home_directory_type,
            'uses_logical_directory': self.uses_logical_directory,
            'has_ssh_keys': self.has_ssh_keys,
            'ssh_public_key_count': self.ssh_public_key_count,
            'tags': self.tags
        }


@dataclass
class TransferConnector:
    """Representa um conector do AWS Transfer Family"""
    connector_id: str
    arn: str
    url: str = ''
    access_role: str = ''
    logging_role: str = ''
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def has_logging(self) -> bool:
        return bool(self.logging_role)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'connector_id': self.connector_id,
            'arn': self.arn,
            'url': self.url,
            'has_logging': self.has_logging,
            'tags': self.tags
        }


class TransferFamilyService(BaseAWSService):
    """Serviço FinOps para análise de AWS Transfer Family"""
    
    def __init__(self, client_factory):
        self.client_factory = client_factory
        self._transfer_client = None
    
    @property
    def transfer_client(self):
        if self._transfer_client is None:
            self._transfer_client = self.client_factory.get_client('transfer')
        return self._transfer_client
    
    @property
    def service_name(self) -> str:
        return "AWS Transfer Family"
    
    def health_check(self) -> bool:
        try:
            self.transfer_client.list_servers(MaxResults=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_servers(self) -> List[TransferServer]:
        servers = []
        try:
            paginator = self.transfer_client.get_paginator('list_servers')
            for page in paginator.paginate():
                for server_item in page.get('Servers', []):
                    server_id = server_item.get('ServerId', '')
                    try:
                        details = self.transfer_client.describe_server(ServerId=server_id)
                        server = details.get('Server', {})
                        servers.append(TransferServer(
                            server_id=server.get('ServerId', ''),
                            arn=server.get('Arn', ''),
                            domain=server.get('Domain', 'S3'),
                            endpoint_type=server.get('EndpointType', 'PUBLIC'),
                            identity_provider_type=server.get('IdentityProviderType', 'SERVICE_MANAGED'),
                            protocols=server.get('Protocols', []),
                            state=server.get('State', 'ONLINE'),
                            user_count=server.get('UserCount', 0),
                            logging_role=server.get('LoggingRole', ''),
                            security_policy_name=server.get('SecurityPolicyName', ''),
                            structured_log_destinations=server.get('StructuredLogDestinations', []),
                            tags=server.get('Tags', {})
                        ))
                    except Exception as e:  # noqa: E722
                        servers.append(TransferServer(
                            server_id=server_id,
                            arn=server_item.get('Arn', ''),
                            domain=server_item.get('Domain', 'S3'),
                            endpoint_type=server_item.get('EndpointType', 'PUBLIC'),
                            identity_provider_type=server_item.get('IdentityProviderType', 'SERVICE_MANAGED'),
                            state=server_item.get('State', 'ONLINE'),
                            user_count=server_item.get('UserCount', 0)
                        ))
        except Exception as e:  # noqa: E722
            pass
        return servers
    
    def get_users(self, server_id: str) -> List[TransferUser]:
        users = []
        try:
            paginator = self.transfer_client.get_paginator('list_users')
            for page in paginator.paginate(ServerId=server_id):
                for user_item in page.get('Users', []):
                    users.append(TransferUser(
                        user_name=user_item.get('UserName', ''),
                        server_id=server_id,
                        arn=user_item.get('Arn', ''),
                        home_directory=user_item.get('HomeDirectory', ''),
                        home_directory_type=user_item.get('HomeDirectoryType', 'PATH'),
                        role=user_item.get('Role', ''),
                        ssh_public_key_count=user_item.get('SshPublicKeyCount', 0)
                    ))
        except Exception as e:  # noqa: E722
            pass
        return users
    
    def get_connectors(self) -> List[TransferConnector]:
        connectors = []
        try:
            paginator = self.transfer_client.get_paginator('list_connectors')
            for page in paginator.paginate():
                for conn in page.get('Connectors', []):
                    connectors.append(TransferConnector(
                        connector_id=conn.get('ConnectorId', ''),
                        arn=conn.get('Arn', ''),
                        url=conn.get('Url', ''),
                        access_role=conn.get('AccessRole', ''),
                        logging_role=conn.get('LoggingRole', '')
                    ))
        except Exception as e:  # noqa: E722
            pass
        return connectors
    
    def get_resources(self) -> Dict[str, Any]:
        servers = self.get_servers()
        connectors = self.get_connectors()
        
        all_users = []
        for server in servers:
            users = self.get_users(server.server_id)
            all_users.extend(users)
        
        return {
            'servers': [s.to_dict() for s in servers],
            'users': [u.to_dict() for u in all_users],
            'connectors': [c.to_dict() for c in connectors],
            'summary': {
                'total_servers': len(servers),
                'online_servers': sum(1 for s in servers if s.is_online),
                'offline_servers': sum(1 for s in servers if s.is_offline),
                'public_servers': sum(1 for s in servers if s.is_public),
                'vpc_servers': sum(1 for s in servers if s.is_vpc),
                'sftp_servers': sum(1 for s in servers if s.supports_sftp),
                'ftps_servers': sum(1 for s in servers if s.supports_ftps),
                's3_backend': sum(1 for s in servers if s.uses_s3),
                'efs_backend': sum(1 for s in servers if s.uses_efs),
                'total_users': len(all_users),
                'total_connectors': len(connectors)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        total_servers = max(resources['summary']['total_servers'], 1)
        
        return {
            'server_count': resources['summary']['total_servers'],
            'online_ratio': resources['summary']['online_servers'] / total_servers,
            'public_ratio': resources['summary']['public_servers'] / total_servers,
            'user_count': resources['summary']['total_users'],
            'connector_count': resources['summary']['total_connectors'],
            'sftp_usage_ratio': resources['summary']['sftp_servers'] / total_servers
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        servers = self.get_servers()
        
        for server in servers:
            if server.is_offline:
                recommendations.append(ServiceRecommendation(
                    resource_id=server.server_id,
                    resource_type='TransferServer',
                    title='Servidor offline ainda gera custos',
                    recommendation=f'Servidor {server.server_id} está OFFLINE mas ainda gera custos. '
                                 f'Considere excluir se não for mais necessário.',
                    action='Excluir servidor ou reativar se necessário',
                    estimated_savings=None,
                    priority='high',
                    category='cost_optimization'
                ))
            
            if not server.has_logging:
                recommendations.append(ServiceRecommendation(
                    resource_id=server.server_id,
                    resource_type='TransferServer',
                    title='Habilitar logging para auditoria',
                    recommendation=f'Servidor {server.server_id} não tem logging habilitado. '
                                 f'Habilite para auditoria de segurança e troubleshooting.',
                    action='Configurar loggingRole ou structuredLogDestinations',
                    estimated_savings=None,
                    priority='medium',
                    category='security'
                ))
            
            if server.is_public and server.supports_ftp:
                recommendations.append(ServiceRecommendation(
                    resource_id=server.server_id,
                    resource_type='TransferServer',
                    title='FTP público é inseguro',
                    recommendation=f'Servidor {server.server_id} é público e suporta FTP (não criptografado). '
                                 f'Considere usar apenas SFTP ou FTPS para segurança.',
                    action='Remover protocolo FTP ou migrar para VPC endpoint',
                    estimated_savings=None,
                    priority='high',
                    category='security'
                ))
            
            if server.user_count == 0 and server.is_online:
                recommendations.append(ServiceRecommendation(
                    resource_id=server.server_id,
                    resource_type='TransferServer',
                    title='Servidor sem usuários',
                    recommendation=f'Servidor {server.server_id} está online mas não tem usuários. '
                                 f'Verifique se ainda é necessário.',
                    action='Adicionar usuários ou excluir servidor',
                    estimated_savings=None,
                    priority='medium',
                    category='cost_optimization'
                ))
        
        return recommendations
