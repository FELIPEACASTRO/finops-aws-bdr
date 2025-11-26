"""
WAF FinOps Service

Análise de custos e otimização para AWS WAF:
- Web ACLs
- Rule Groups
- IP Sets
- Regex Pattern Sets
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class WebACL:
    """Representa uma Web ACL do WAF"""
    name: str
    id: str
    arn: Optional[str] = None
    description: Optional[str] = None
    scope: str = 'REGIONAL'
    default_action: str = 'ALLOW'
    rules: List[Dict] = field(default_factory=list)
    visibility_config: Dict = field(default_factory=dict)
    capacity: int = 0
    managed_by_firewall_manager: bool = False
    
    @property
    def rule_count(self) -> int:
        return len(self.rules)
    
    @property
    def is_cloudfront(self) -> bool:
        return self.scope == 'CLOUDFRONT'
    
    @property
    def is_regional(self) -> bool:
        return self.scope == 'REGIONAL'
    
    @property
    def has_logging(self) -> bool:
        return self.visibility_config.get('cloudWatchMetricsEnabled', False)
    
    @property
    def has_sampled_requests(self) -> bool:
        return self.visibility_config.get('sampledRequestsEnabled', False)
    
    @property
    def blocks_by_default(self) -> bool:
        return self.default_action == 'BLOCK'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'id': self.id,
            'arn': self.arn,
            'description': self.description,
            'scope': self.scope,
            'default_action': self.default_action,
            'rule_count': self.rule_count,
            'capacity': self.capacity,
            'is_cloudfront': self.is_cloudfront,
            'is_regional': self.is_regional,
            'has_logging': self.has_logging,
            'has_sampled_requests': self.has_sampled_requests,
            'blocks_by_default': self.blocks_by_default,
            'managed_by_firewall_manager': self.managed_by_firewall_manager
        }


@dataclass
class RuleGroup:
    """Representa um Rule Group do WAF"""
    name: str
    id: str
    arn: Optional[str] = None
    description: Optional[str] = None
    scope: str = 'REGIONAL'
    capacity: int = 0
    rules: List[Dict] = field(default_factory=list)
    visibility_config: Dict = field(default_factory=dict)
    
    @property
    def rule_count(self) -> int:
        return len(self.rules)
    
    @property
    def has_metrics(self) -> bool:
        return self.visibility_config.get('cloudWatchMetricsEnabled', False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'id': self.id,
            'arn': self.arn,
            'description': self.description,
            'scope': self.scope,
            'capacity': self.capacity,
            'rule_count': self.rule_count,
            'has_metrics': self.has_metrics
        }


@dataclass
class IPSet:
    """Representa um IP Set do WAF"""
    name: str
    id: str
    arn: Optional[str] = None
    description: Optional[str] = None
    scope: str = 'REGIONAL'
    ip_address_version: str = 'IPV4'
    addresses: List[str] = field(default_factory=list)
    
    @property
    def address_count(self) -> int:
        return len(self.addresses)
    
    @property
    def is_ipv6(self) -> bool:
        return self.ip_address_version == 'IPV6'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'id': self.id,
            'arn': self.arn,
            'description': self.description,
            'scope': self.scope,
            'ip_address_version': self.ip_address_version,
            'address_count': self.address_count,
            'is_ipv6': self.is_ipv6
        }


@dataclass
class RegexPatternSet:
    """Representa um Regex Pattern Set do WAF"""
    name: str
    id: str
    arn: Optional[str] = None
    description: Optional[str] = None
    scope: str = 'REGIONAL'
    regular_expression_list: List[str] = field(default_factory=list)
    
    @property
    def pattern_count(self) -> int:
        return len(self.regular_expression_list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'id': self.id,
            'arn': self.arn,
            'description': self.description,
            'scope': self.scope,
            'pattern_count': self.pattern_count
        }


class WAFService(BaseAWSService):
    """
    Serviço FinOps para análise de custos AWS WAF
    
    Analisa Web ACLs, Rule Groups, IP Sets
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._wafv2_client = None
    
    @property
    def wafv2_client(self):
        if self._wafv2_client is None:
            if self._client_factory:
                self._wafv2_client = self._client_factory.get_client('wafv2')
            else:
                import boto3
                self._wafv2_client = boto3.client('wafv2')
        return self._wafv2_client
    
    @property
    def service_name(self) -> str:
        return "AWS WAF"
    
    def health_check(self) -> bool:
        try:
            self.wafv2_client.list_web_acls(Scope='REGIONAL', Limit=1)
            return True
        except Exception:
            return False
    
    def get_web_acls(self, scope: str = 'REGIONAL') -> List[WebACL]:
        web_acls = []
        try:
            response = self.wafv2_client.list_web_acls(Scope=scope, Limit=100)
            for acl in response.get('WebACLs', []):
                try:
                    details = self.wafv2_client.get_web_acl(
                        Name=acl['Name'],
                        Scope=scope,
                        Id=acl['Id']
                    )
                    acl_detail = details.get('WebACL', {})
                    web_acls.append(WebACL(
                        name=acl_detail.get('Name', acl['Name']),
                        id=acl_detail.get('Id', acl['Id']),
                        arn=acl_detail.get('ARN', acl.get('ARN')),
                        description=acl_detail.get('Description'),
                        scope=scope,
                        default_action=list(acl_detail.get('DefaultAction', {'Allow': {}}).keys())[0].upper(),
                        rules=acl_detail.get('Rules', []),
                        visibility_config=acl_detail.get('VisibilityConfig', {}),
                        capacity=acl_detail.get('Capacity', 0),
                        managed_by_firewall_manager=acl_detail.get('ManagedByFirewallManager', False)
                    ))
                except Exception:
                    web_acls.append(WebACL(
                        name=acl['Name'],
                        id=acl['Id'],
                        arn=acl.get('ARN'),
                        scope=scope
                    ))
        except Exception:
            pass
        return web_acls
    
    def get_rule_groups(self, scope: str = 'REGIONAL') -> List[RuleGroup]:
        rule_groups = []
        try:
            response = self.wafv2_client.list_rule_groups(Scope=scope, Limit=100)
            for rg in response.get('RuleGroups', []):
                try:
                    details = self.wafv2_client.get_rule_group(
                        Name=rg['Name'],
                        Scope=scope,
                        Id=rg['Id']
                    )
                    rg_detail = details.get('RuleGroup', {})
                    rule_groups.append(RuleGroup(
                        name=rg_detail.get('Name', rg['Name']),
                        id=rg_detail.get('Id', rg['Id']),
                        arn=rg_detail.get('ARN', rg.get('ARN')),
                        description=rg_detail.get('Description'),
                        scope=scope,
                        capacity=rg_detail.get('Capacity', 0),
                        rules=rg_detail.get('Rules', []),
                        visibility_config=rg_detail.get('VisibilityConfig', {})
                    ))
                except Exception:
                    rule_groups.append(RuleGroup(
                        name=rg['Name'],
                        id=rg['Id'],
                        arn=rg.get('ARN'),
                        scope=scope
                    ))
        except Exception:
            pass
        return rule_groups
    
    def get_ip_sets(self, scope: str = 'REGIONAL') -> List[IPSet]:
        ip_sets = []
        try:
            response = self.wafv2_client.list_ip_sets(Scope=scope, Limit=100)
            for ip_set in response.get('IPSets', []):
                try:
                    details = self.wafv2_client.get_ip_set(
                        Name=ip_set['Name'],
                        Scope=scope,
                        Id=ip_set['Id']
                    )
                    ip_detail = details.get('IPSet', {})
                    ip_sets.append(IPSet(
                        name=ip_detail.get('Name', ip_set['Name']),
                        id=ip_detail.get('Id', ip_set['Id']),
                        arn=ip_detail.get('ARN', ip_set.get('ARN')),
                        description=ip_detail.get('Description'),
                        scope=scope,
                        ip_address_version=ip_detail.get('IPAddressVersion', 'IPV4'),
                        addresses=ip_detail.get('Addresses', [])
                    ))
                except Exception:
                    ip_sets.append(IPSet(
                        name=ip_set['Name'],
                        id=ip_set['Id'],
                        arn=ip_set.get('ARN'),
                        scope=scope
                    ))
        except Exception:
            pass
        return ip_sets
    
    def get_regex_pattern_sets(self, scope: str = 'REGIONAL') -> List[RegexPatternSet]:
        regex_sets = []
        try:
            response = self.wafv2_client.list_regex_pattern_sets(Scope=scope, Limit=100)
            for regex_set in response.get('RegexPatternSets', []):
                try:
                    details = self.wafv2_client.get_regex_pattern_set(
                        Name=regex_set['Name'],
                        Scope=scope,
                        Id=regex_set['Id']
                    )
                    regex_detail = details.get('RegexPatternSet', {})
                    regex_sets.append(RegexPatternSet(
                        name=regex_detail.get('Name', regex_set['Name']),
                        id=regex_detail.get('Id', regex_set['Id']),
                        arn=regex_detail.get('ARN', regex_set.get('ARN')),
                        description=regex_detail.get('Description'),
                        scope=scope,
                        regular_expression_list=[r.get('RegexString', '') for r in regex_detail.get('RegularExpressionList', [])]
                    ))
                except Exception:
                    regex_sets.append(RegexPatternSet(
                        name=regex_set['Name'],
                        id=regex_set['Id'],
                        arn=regex_set.get('ARN'),
                        scope=scope
                    ))
        except Exception:
            pass
        return regex_sets
    
    def get_resources(self) -> Dict[str, Any]:
        regional_acls = self.get_web_acls('REGIONAL')
        regional_rule_groups = self.get_rule_groups('REGIONAL')
        regional_ip_sets = self.get_ip_sets('REGIONAL')
        regional_regex_sets = self.get_regex_pattern_sets('REGIONAL')
        
        total_capacity = sum(acl.capacity for acl in regional_acls)
        acls_without_logging = sum(1 for acl in regional_acls if not acl.has_logging)
        
        return {
            'web_acls': [acl.to_dict() for acl in regional_acls],
            'rule_groups': [rg.to_dict() for rg in regional_rule_groups],
            'ip_sets': [ip.to_dict() for ip in regional_ip_sets],
            'regex_pattern_sets': [rs.to_dict() for rs in regional_regex_sets],
            'summary': {
                'total_web_acls': len(regional_acls),
                'total_rule_groups': len(regional_rule_groups),
                'total_ip_sets': len(regional_ip_sets),
                'total_regex_pattern_sets': len(regional_regex_sets),
                'total_capacity_used': total_capacity,
                'acls_without_logging': acls_without_logging
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        return {
            'service': self.service_name,
            'web_acls_count': resources['summary']['total_web_acls'],
            'rule_groups_count': resources['summary']['total_rule_groups'],
            'total_capacity': resources['summary']['total_capacity_used']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        web_acls = self.get_web_acls('REGIONAL')
        
        for acl in web_acls:
            if not acl.has_logging:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=acl.id,
                    recommendation_type='SECURITY',
                    title='Enable CloudWatch Metrics',
                    description=f'Web ACL {acl.name} does not have CloudWatch metrics enabled. This limits visibility into WAF activity.',
                    action='Enable CloudWatch metrics in visibility configuration',
                    priority='HIGH',
                    impact='HIGH'
                ))
            
            if not acl.has_sampled_requests:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=acl.id,
                    recommendation_type='OPERATIONAL',
                    title='Enable Sampled Requests',
                    description=f'Web ACL {acl.name} does not capture sampled requests. This limits debugging capability.',
                    action='Enable sampled requests in visibility configuration',
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
            
            if acl.rule_count == 0:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=acl.id,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Remove Empty Web ACL',
                    description=f'Web ACL {acl.name} has no rules configured but still incurs monthly charges.',
                    action='Add rules or delete unused Web ACL',
                    estimated_savings=5.00,
                    priority='MEDIUM',
                    impact='LOW'
                ))
            
            if acl.capacity > 4000:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=acl.id,
                    recommendation_type='COST_OPTIMIZATION',
                    title='High WAF Capacity Usage',
                    description=f'Web ACL {acl.name} uses {acl.capacity} WCUs. Consider optimizing rules to reduce capacity costs.',
                    action='Review and consolidate rules to reduce WCU usage',
                    priority='LOW',
                    impact='MEDIUM'
                ))
        
        return recommendations
