"""
Cognito FinOps Service

Análise de custos e otimização para Amazon Cognito:
- User Pools
- Identity Pools
- User Pool Clients
- Resource Servers
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class UserPool:
    """Representa um User Pool do Cognito"""
    id: str
    name: str
    status: str = 'Enabled'
    creation_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    estimated_number_of_users: int = 0
    mfa_configuration: str = 'OFF'
    sms_configuration: Optional[Dict] = None
    email_configuration: Optional[Dict] = None
    admin_create_user_config: Optional[Dict] = None
    user_pool_tags: Dict[str, str] = field(default_factory=dict)
    deletion_protection: str = 'INACTIVE'
    
    @property
    def has_mfa(self) -> bool:
        return self.mfa_configuration != 'OFF'
    
    @property
    def mfa_required(self) -> bool:
        return self.mfa_configuration == 'ON'
    
    @property
    def has_sms_config(self) -> bool:
        return self.sms_configuration is not None
    
    @property
    def has_ses_config(self) -> bool:
        if self.email_configuration:
            return self.email_configuration.get('EmailSendingAccount') == 'DEVELOPER'
        return False
    
    @property
    def has_deletion_protection(self) -> bool:
        return self.deletion_protection == 'ACTIVE'
    
    @property
    def user_tier(self) -> str:
        if self.estimated_number_of_users > 50000:
            return 'ENTERPRISE'
        elif self.estimated_number_of_users > 5000:
            return 'GROWTH'
        return 'STARTER'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'estimated_number_of_users': self.estimated_number_of_users,
            'mfa_configuration': self.mfa_configuration,
            'has_mfa': self.has_mfa,
            'mfa_required': self.mfa_required,
            'has_sms_config': self.has_sms_config,
            'has_ses_config': self.has_ses_config,
            'has_deletion_protection': self.has_deletion_protection,
            'user_tier': self.user_tier
        }


@dataclass
class UserPoolClient:
    """Representa um App Client de User Pool"""
    client_id: str
    user_pool_id: str
    client_name: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token_validity: int = 30
    access_token_validity: int = 60
    id_token_validity: int = 60
    token_validity_units: Dict = field(default_factory=dict)
    explicit_auth_flows: List[str] = field(default_factory=list)
    supported_identity_providers: List[str] = field(default_factory=list)
    callback_urls: List[str] = field(default_factory=list)
    logout_urls: List[str] = field(default_factory=list)
    allowed_oauth_flows: List[str] = field(default_factory=list)
    allowed_oauth_scopes: List[str] = field(default_factory=list)
    
    @property
    def has_secret(self) -> bool:
        return self.client_secret is not None
    
    @property
    def uses_oauth(self) -> bool:
        return len(self.allowed_oauth_flows) > 0
    
    @property
    def has_social_providers(self) -> bool:
        social_providers = {'Facebook', 'Google', 'LoginWithAmazon', 'SignInWithApple'}
        return any(p in social_providers for p in self.supported_identity_providers)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'client_id': self.client_id,
            'user_pool_id': self.user_pool_id,
            'client_name': self.client_name,
            'has_secret': self.has_secret,
            'refresh_token_validity': self.refresh_token_validity,
            'uses_oauth': self.uses_oauth,
            'has_social_providers': self.has_social_providers,
            'explicit_auth_flows': self.explicit_auth_flows,
            'supported_identity_providers': self.supported_identity_providers
        }


@dataclass
class IdentityPool:
    """Representa um Identity Pool do Cognito"""
    identity_pool_id: str
    identity_pool_name: str
    allow_unauthenticated_identities: bool = False
    allow_classic_flow: bool = False
    cognito_identity_providers: List[Dict] = field(default_factory=list)
    supported_login_providers: Dict[str, str] = field(default_factory=dict)
    saml_provider_arns: List[str] = field(default_factory=list)
    open_id_connect_provider_arns: List[str] = field(default_factory=list)
    identity_pool_tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def allows_guest_access(self) -> bool:
        return self.allow_unauthenticated_identities
    
    @property
    def provider_count(self) -> int:
        return (
            len(self.cognito_identity_providers) +
            len(self.supported_login_providers) +
            len(self.saml_provider_arns) +
            len(self.open_id_connect_provider_arns)
        )
    
    @property
    def has_cognito_user_pool(self) -> bool:
        return len(self.cognito_identity_providers) > 0
    
    @property
    def has_social_providers(self) -> bool:
        return len(self.supported_login_providers) > 0
    
    @property
    def has_enterprise_providers(self) -> bool:
        return len(self.saml_provider_arns) > 0 or len(self.open_id_connect_provider_arns) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'identity_pool_id': self.identity_pool_id,
            'identity_pool_name': self.identity_pool_name,
            'allows_guest_access': self.allows_guest_access,
            'allow_classic_flow': self.allow_classic_flow,
            'provider_count': self.provider_count,
            'has_cognito_user_pool': self.has_cognito_user_pool,
            'has_social_providers': self.has_social_providers,
            'has_enterprise_providers': self.has_enterprise_providers
        }


@dataclass
class ResourceServer:
    """Representa um Resource Server do Cognito"""
    identifier: str
    name: str
    user_pool_id: str
    scopes: List[Dict] = field(default_factory=list)
    
    @property
    def scope_count(self) -> int:
        return len(self.scopes)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'identifier': self.identifier,
            'name': self.name,
            'user_pool_id': self.user_pool_id,
            'scope_count': self.scope_count,
            'scopes': [s.get('ScopeName', '') for s in self.scopes]
        }


class CognitoService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Amazon Cognito
    
    Analisa User Pools, Identity Pools, App Clients
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._cognito_idp_client = None
        self._cognito_identity_client = None
    
    @property
    def cognito_idp_client(self):
        if self._cognito_idp_client is None:
            if self._client_factory:
                self._cognito_idp_client = self._client_factory.get_client('cognito-idp')
            else:
                import boto3
                self._cognito_idp_client = boto3.client('cognito-idp')
        return self._cognito_idp_client
    
    @property
    def cognito_identity_client(self):
        if self._cognito_identity_client is None:
            if self._client_factory:
                self._cognito_identity_client = self._client_factory.get_client('cognito-identity')
            else:
                import boto3
                self._cognito_identity_client = boto3.client('cognito-identity')
        return self._cognito_identity_client
    
    @property
    def service_name(self) -> str:
        return "Amazon Cognito"
    
    def health_check(self) -> bool:
        try:
            self.cognito_idp_client.list_user_pools(MaxResults=1)
            return True
        except Exception:
            return False
    
    def get_user_pools(self) -> List[UserPool]:
        user_pools = []
        try:
            paginator = self.cognito_idp_client.get_paginator('list_user_pools')
            for page in paginator.paginate(MaxResults=60):
                for pool in page.get('UserPools', []):
                    try:
                        details = self.cognito_idp_client.describe_user_pool(
                            UserPoolId=pool['Id']
                        )
                        pool_detail = details.get('UserPool', {})
                        user_pools.append(UserPool(
                            id=pool_detail.get('Id', pool['Id']),
                            name=pool_detail.get('Name', pool['Name']),
                            status=pool_detail.get('Status', 'Enabled'),
                            creation_date=pool_detail.get('CreationDate'),
                            last_modified_date=pool_detail.get('LastModifiedDate'),
                            estimated_number_of_users=pool_detail.get('EstimatedNumberOfUsers', 0),
                            mfa_configuration=pool_detail.get('MfaConfiguration', 'OFF'),
                            sms_configuration=pool_detail.get('SmsConfiguration'),
                            email_configuration=pool_detail.get('EmailConfiguration'),
                            admin_create_user_config=pool_detail.get('AdminCreateUserConfig'),
                            user_pool_tags=pool_detail.get('UserPoolTags', {}),
                            deletion_protection=pool_detail.get('DeletionProtection', 'INACTIVE')
                        ))
                    except Exception:
                        user_pools.append(UserPool(
                            id=pool['Id'],
                            name=pool['Name'],
                            creation_date=pool.get('CreationDate'),
                            last_modified_date=pool.get('LastModifiedDate')
                        ))
        except Exception:
            pass
        return user_pools
    
    def get_user_pool_clients(self, user_pool_id: str) -> List[UserPoolClient]:
        clients = []
        try:
            paginator = self.cognito_idp_client.get_paginator('list_user_pool_clients')
            for page in paginator.paginate(UserPoolId=user_pool_id, MaxResults=60):
                for client in page.get('UserPoolClients', []):
                    try:
                        details = self.cognito_idp_client.describe_user_pool_client(
                            UserPoolId=user_pool_id,
                            ClientId=client['ClientId']
                        )
                        client_detail = details.get('UserPoolClient', {})
                        clients.append(UserPoolClient(
                            client_id=client_detail.get('ClientId', client['ClientId']),
                            user_pool_id=user_pool_id,
                            client_name=client_detail.get('ClientName', client.get('ClientName')),
                            client_secret=client_detail.get('ClientSecret'),
                            refresh_token_validity=client_detail.get('RefreshTokenValidity', 30),
                            access_token_validity=client_detail.get('AccessTokenValidity', 60),
                            id_token_validity=client_detail.get('IdTokenValidity', 60),
                            explicit_auth_flows=client_detail.get('ExplicitAuthFlows', []),
                            supported_identity_providers=client_detail.get('SupportedIdentityProviders', []),
                            callback_urls=client_detail.get('CallbackURLs', []),
                            logout_urls=client_detail.get('LogoutURLs', []),
                            allowed_oauth_flows=client_detail.get('AllowedOAuthFlows', []),
                            allowed_oauth_scopes=client_detail.get('AllowedOAuthScopes', [])
                        ))
                    except Exception:
                        clients.append(UserPoolClient(
                            client_id=client['ClientId'],
                            user_pool_id=user_pool_id,
                            client_name=client.get('ClientName')
                        ))
        except Exception:
            pass
        return clients
    
    def get_identity_pools(self) -> List[IdentityPool]:
        identity_pools = []
        try:
            paginator = self.cognito_identity_client.get_paginator('list_identity_pools')
            for page in paginator.paginate(MaxResults=60):
                for pool in page.get('IdentityPools', []):
                    try:
                        details = self.cognito_identity_client.describe_identity_pool(
                            IdentityPoolId=pool['IdentityPoolId']
                        )
                        identity_pools.append(IdentityPool(
                            identity_pool_id=details.get('IdentityPoolId', pool['IdentityPoolId']),
                            identity_pool_name=details.get('IdentityPoolName', pool['IdentityPoolName']),
                            allow_unauthenticated_identities=details.get('AllowUnauthenticatedIdentities', False),
                            allow_classic_flow=details.get('AllowClassicFlow', False),
                            cognito_identity_providers=details.get('CognitoIdentityProviders', []),
                            supported_login_providers=details.get('SupportedLoginProviders', {}),
                            saml_provider_arns=details.get('SamlProviderARNs', []),
                            open_id_connect_provider_arns=details.get('OpenIdConnectProviderARNs', []),
                            identity_pool_tags=details.get('IdentityPoolTags', {})
                        ))
                    except Exception:
                        identity_pools.append(IdentityPool(
                            identity_pool_id=pool['IdentityPoolId'],
                            identity_pool_name=pool['IdentityPoolName']
                        ))
        except Exception:
            pass
        return identity_pools
    
    def get_resources(self) -> Dict[str, Any]:
        user_pools = self.get_user_pools()
        identity_pools = self.get_identity_pools()
        
        all_clients = []
        for pool in user_pools:
            clients = self.get_user_pool_clients(pool.id)
            all_clients.extend(clients)
        
        total_users = sum(p.estimated_number_of_users for p in user_pools)
        pools_without_mfa = sum(1 for p in user_pools if not p.has_mfa)
        pools_with_guest = sum(1 for p in identity_pools if p.allows_guest_access)
        
        return {
            'user_pools': [p.to_dict() for p in user_pools],
            'user_pool_clients': [c.to_dict() for c in all_clients],
            'identity_pools': [p.to_dict() for p in identity_pools],
            'summary': {
                'total_user_pools': len(user_pools),
                'total_identity_pools': len(identity_pools),
                'total_app_clients': len(all_clients),
                'total_estimated_users': total_users,
                'pools_without_mfa': pools_without_mfa,
                'identity_pools_with_guest_access': pools_with_guest
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        return {
            'service': self.service_name,
            'user_pools_count': resources['summary']['total_user_pools'],
            'identity_pools_count': resources['summary']['total_identity_pools'],
            'total_users': resources['summary']['total_estimated_users']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        user_pools = self.get_user_pools()
        identity_pools = self.get_identity_pools()
        
        for pool in user_pools:
            if not pool.has_mfa:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pool.id,
                    recommendation_type='SECURITY',
                    title='Enable MFA for User Pool',
                    description=f'User Pool {pool.name} does not have MFA enabled. This reduces account security.',
                    action='Enable MFA (SMS or TOTP) for enhanced security',
                    priority='HIGH',
                    impact='HIGH'
                ))
            
            if not pool.has_deletion_protection:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pool.id,
                    recommendation_type='SECURITY',
                    title='Enable Deletion Protection',
                    description=f'User Pool {pool.name} does not have deletion protection enabled.',
                    action='Enable deletion protection to prevent accidental deletion',
                    priority='MEDIUM',
                    impact='HIGH'
                ))
            
            if pool.estimated_number_of_users == 0:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pool.id,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Review Empty User Pool',
                    description=f'User Pool {pool.name} has no users. Consider if it is still needed.',
                    action='Delete unused User Pool or verify it is intentionally empty',
                    priority='LOW',
                    impact='LOW'
                ))
            
            if pool.has_sms_config and pool.estimated_number_of_users > 1000:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pool.id,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Review SMS MFA Costs',
                    description=f'User Pool {pool.name} uses SMS with {pool.estimated_number_of_users} users. SMS costs can be significant.',
                    action='Consider TOTP MFA as a cost-effective alternative to SMS',
                    estimated_savings=pool.estimated_number_of_users * 0.01,
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
        
        for pool in identity_pools:
            if pool.allows_guest_access:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pool.identity_pool_id,
                    recommendation_type='SECURITY',
                    title='Review Guest Access',
                    description=f'Identity Pool {pool.identity_pool_name} allows unauthenticated access.',
                    action='Verify guest access is intentional and properly scoped with IAM roles',
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
            
            if pool.provider_count == 0:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pool.identity_pool_id,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Identity Pool Has No Providers',
                    description=f'Identity Pool {pool.identity_pool_name} has no identity providers configured.',
                    action='Configure providers or delete unused Identity Pool',
                    priority='LOW',
                    impact='LOW'
                ))
        
        return recommendations
