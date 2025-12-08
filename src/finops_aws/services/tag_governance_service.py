"""
FinOps AWS - Tag Governance Service
Governança de tags AWS para alocação de custos e compliance

Funcionalidades:
- Validação de tags obrigatórias
- Cálculo de cobertura de tags
- Detecção de recursos sem tags
- Geração de relatórios de compliance

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Template Method: Fluxo padrão de análise
"""
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import os

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger


@dataclass
class TagPolicy:
    """Política de tags obrigatórias"""
    policy_id: str
    required_tags: List[str]
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    scope: str = "account"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'required_tags': self.required_tags,
            'validation_rules': self.validation_rules,
            'scope': self.scope
        }


@dataclass
class TagCoverageResult:
    """Resultado de análise de cobertura de tags"""
    scope: str
    total_resources: int
    fully_tagged_resources: int
    partially_tagged_resources: int
    untagged_resources: int
    coverage_percent: float
    compliance_percent: float
    missing_tags_by_resource: Dict[str, List[str]] = field(default_factory=dict)
    tag_statistics: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scope': self.scope,
            'total_resources': self.total_resources,
            'fully_tagged_resources': self.fully_tagged_resources,
            'partially_tagged_resources': self.partially_tagged_resources,
            'untagged_resources': self.untagged_resources,
            'coverage_percent': round(self.coverage_percent, 2),
            'compliance_percent': round(self.compliance_percent, 2),
            'missing_tags_summary': {
                tag: len([r for r, tags in self.missing_tags_by_resource.items() if tag in tags])
                for tag in set(t for tags in self.missing_tags_by_resource.values() for t in tags)
            },
            'tag_statistics': self.tag_statistics
        }


@dataclass
class ResourceTagInfo:
    """Informações de tags de um recurso"""
    resource_id: str
    resource_arn: str
    resource_type: str
    service: str
    region: str
    tags: Dict[str, str]
    missing_required_tags: List[str] = field(default_factory=list)
    is_compliant: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_arn': self.resource_arn,
            'resource_type': self.resource_type,
            'service': self.service,
            'region': self.region,
            'tags': self.tags,
            'missing_required_tags': self.missing_required_tags,
            'is_compliant': self.is_compliant
        }


class TagGovernanceService(BaseAWSService):
    """
    Serviço de Governança de Tags AWS
    
    Funcionalidades:
    - Define políticas de tags obrigatórias
    - Analisa cobertura de tags por conta/região/serviço
    - Identifica recursos não conformes
    - Gera recomendações de tagging
    
    AWS APIs utilizadas:
    - resourcegroupstaggingapi:GetResources
    - resourcegroupstaggingapi:GetTagKeys
    - resourcegroupstaggingapi:GetTagValues
    """
    
    DEFAULT_REQUIRED_TAGS = [
        'Environment',
        'Owner',
        'CostCenter',
        'Application',
        'Project'
    ]
    
    STANDARD_ENVIRONMENTS = ['production', 'prod', 'staging', 'development', 'dev', 'test', 'qa']
    
    def __init__(self, client_factory=None, required_tags: Optional[List[str]] = None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "tag_governance"
        self.required_tags = required_tags or self.DEFAULT_REQUIRED_TAGS
        self._tag_policy = TagPolicy(
            policy_id="default",
            required_tags=self.required_tags,
            validation_rules={
                'Environment': {'allowed_values': self.STANDARD_ENVIRONMENTS},
                'Owner': {'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+$'}
            }
        )
    
    def _get_client(self, region: str = None):
        """Obtém cliente boto3 para Resource Groups Tagging API"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('resourcegroupstaggingapi', region_name=region)
        return boto3.client('resourcegroupstaggingapi', region_name=region)
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_client()
            client.get_tag_keys()
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para acessar Resource Groups Tagging API")
            return False
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            return False
    
    def set_tag_policy(self, required_tags: List[str], validation_rules: Optional[Dict] = None):
        """Define política de tags obrigatórias"""
        self.required_tags = required_tags
        self._tag_policy = TagPolicy(
            policy_id="custom",
            required_tags=required_tags,
            validation_rules=validation_rules or {}
        )
        self.logger.info(f"Política de tags atualizada: {required_tags}")
    
    def get_tag_policy(self) -> TagPolicy:
        """Retorna política de tags atual"""
        return self._tag_policy
    
    def get_all_tags_in_use(self, region: str = None) -> Dict[str, List[str]]:
        """Obtém todas as tags em uso na conta"""
        tags_in_use: Dict[str, Set[str]] = {}
        
        try:
            client = self._get_client(region)
            
            tag_keys_response = client.get_tag_keys()
            tag_keys = tag_keys_response.get('TagKeys', [])
            
            for key in tag_keys:
                try:
                    values_response = client.get_tag_values(Key=key)
                    values = values_response.get('TagValues', [])
                    tags_in_use[key] = set(values)
                except Exception:
                    tags_in_use[key] = set()
            
            return {k: list(v) for k, v in tags_in_use.items()}
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter tags em uso: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Erro ao obter tags: {e}")
            return {}
    
    def get_resources_with_tags(
        self, 
        region: str = None,
        resource_types: Optional[List[str]] = None,
        tag_filters: Optional[Dict[str, List[str]]] = None
    ) -> List[ResourceTagInfo]:
        """Obtém recursos com suas tags"""
        resources = []
        
        try:
            client = self._get_client(region)
            
            params: Dict[str, Any] = {'ResourcesPerPage': 100}
            
            if resource_types:
                params['ResourceTypeFilters'] = resource_types
            
            if tag_filters:
                params['TagFilters'] = [
                    {'Key': k, 'Values': v} for k, v in tag_filters.items()
                ]
            
            pagination_token = None
            while True:
                if pagination_token:
                    params['PaginationToken'] = pagination_token
                
                response = client.get_resources(**params)
                
                for resource in response.get('ResourceTagMappingList', []):
                    arn = resource.get('ResourceARN', '')
                    tags = {t['Key']: t['Value'] for t in resource.get('Tags', [])}
                    
                    resource_parts = arn.split(':')
                    service = resource_parts[2] if len(resource_parts) > 2 else ''
                    resource_region = resource_parts[3] if len(resource_parts) > 3 else ''
                    resource_type = resource_parts[5].split('/')[0] if len(resource_parts) > 5 else ''
                    resource_id = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]
                    
                    missing_tags = [t for t in self.required_tags if t not in tags]
                    is_compliant = len(missing_tags) == 0
                    
                    resources.append(ResourceTagInfo(
                        resource_id=resource_id,
                        resource_arn=arn,
                        resource_type=resource_type,
                        service=service,
                        region=resource_region,
                        tags=tags,
                        missing_required_tags=missing_tags,
                        is_compliant=is_compliant
                    ))
                
                pagination_token = response.get('PaginationToken')
                if not pagination_token:
                    break
            
            self.logger.info(f"Encontrados {len(resources)} recursos com tags")
            return resources
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: resourcegroupstaggingapi:GetResources")
            else:
                self.logger.error(f"Erro ao obter recursos: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter recursos com tags: {e}")
            return []
    
    def analyze_tag_coverage(self, region: str = None) -> TagCoverageResult:
        """Analisa cobertura de tags na conta/região"""
        resources = self.get_resources_with_tags(region)
        
        if not resources:
            return TagCoverageResult(
                scope=region or 'account',
                total_resources=0,
                fully_tagged_resources=0,
                partially_tagged_resources=0,
                untagged_resources=0,
                coverage_percent=0.0,
                compliance_percent=0.0
            )
        
        fully_tagged = 0
        partially_tagged = 0
        untagged = 0
        missing_by_resource: Dict[str, List[str]] = {}
        tag_stats: Dict[str, int] = {tag: 0 for tag in self.required_tags}
        
        for resource in resources:
            if resource.is_compliant:
                fully_tagged += 1
            elif resource.missing_required_tags:
                if len(resource.missing_required_tags) == len(self.required_tags):
                    untagged += 1
                else:
                    partially_tagged += 1
                missing_by_resource[resource.resource_id] = resource.missing_required_tags
            
            for tag in self.required_tags:
                if tag in resource.tags:
                    tag_stats[tag] += 1
        
        total = len(resources)
        coverage_percent = ((fully_tagged + partially_tagged) / total * 100) if total > 0 else 0
        compliance_percent = (fully_tagged / total * 100) if total > 0 else 0
        
        return TagCoverageResult(
            scope=region or 'account',
            total_resources=total,
            fully_tagged_resources=fully_tagged,
            partially_tagged_resources=partially_tagged,
            untagged_resources=untagged,
            coverage_percent=coverage_percent,
            compliance_percent=compliance_percent,
            missing_tags_by_resource=missing_by_resource,
            tag_statistics={k: v for k, v in tag_stats.items()}
        )
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Obtém recursos não conformes"""
        resources = self.get_resources_with_tags()
        non_compliant = [r for r in resources if not r.is_compliant]
        return [r.to_dict() for r in non_compliant[:100]]
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """Obtém estimativa de shadow cost (recursos sem tags)"""
        coverage = self.analyze_tag_coverage()
        
        shadow_cost_estimate = coverage.untagged_resources * 50
        
        return ServiceCost(
            service_name='tag_governance',
            total_cost=shadow_cost_estimate,
            period_days=period_days,
            cost_by_resource={
                'untagged_resources': shadow_cost_estimate
            },
            trend='STABLE',
            currency='USD'
        )
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas de governança de tags"""
        coverage = self.analyze_tag_coverage()
        
        return ServiceMetrics(
            service_name='tag_governance',
            resource_count=coverage.total_resources,
            metrics={
                'coverage_percent': coverage.coverage_percent,
                'compliance_percent': coverage.compliance_percent,
                'fully_tagged': coverage.fully_tagged_resources,
                'partially_tagged': coverage.partially_tagged_resources,
                'untagged': coverage.untagged_resources,
                'tag_statistics': coverage.tag_statistics,
                'required_tags': self.required_tags
            },
            utilization=coverage.compliance_percent
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de melhoria de tagging"""
        recommendations: List[ServiceRecommendation] = []
        coverage = self.analyze_tag_coverage()
        
        if coverage.compliance_percent < 80:
            recommendations.append(ServiceRecommendation(
                resource_id='tag_compliance',
                resource_type='tag_governance',
                recommendation_type='LOW_TAG_COMPLIANCE',
                description=(
                    f'Apenas {coverage.compliance_percent:.1f}% dos recursos possuem todas as tags obrigatórias. '
                    f'Tags obrigatórias: {", ".join(self.required_tags)}. '
                    f'Recursos não conformes: {coverage.total_resources - coverage.fully_tagged_resources}. '
                    f'A falta de tags dificulta alocação de custos e governança.'
                ),
                estimated_savings=coverage.untagged_resources * 50,
                priority='HIGH',
                title=f'Apenas {coverage.compliance_percent:.1f}% de compliance de tags',
                action='Implementar automação para aplicar tags obrigatórias'
            ))
        
        if coverage.untagged_resources > 0:
            recommendations.append(ServiceRecommendation(
                resource_id='shadow_cost',
                resource_type='tag_governance',
                recommendation_type='SHADOW_COST',
                description=(
                    f'{coverage.untagged_resources} recursos não possuem nenhuma das tags obrigatórias. '
                    f'Estes recursos representam "Shadow Cost" - custos que não podem ser alocados '
                    f'a nenhum time, produto ou centro de custo.'
                ),
                estimated_savings=coverage.untagged_resources * 50,
                priority='MEDIUM',
                title=f'{coverage.untagged_resources} recursos sem tags (Shadow Cost)',
                action='Identificar proprietários e aplicar tags obrigatórias'
            ))
        
        for tag, count in coverage.tag_statistics.items():
            if coverage.total_resources > 0:
                tag_coverage = count / coverage.total_resources * 100
                if tag_coverage < 50:
                    recommendations.append(ServiceRecommendation(
                        resource_id=f'tag_{tag.lower()}',
                        resource_type='tag_governance',
                        recommendation_type='MISSING_TAG',
                        description=(
                            f'A tag obrigatória "{tag}" está presente em apenas {count} de '
                            f'{coverage.total_resources} recursos ({tag_coverage:.1f}%). '
                            f'Esta tag é importante para: '
                            + ('alocação de custos' if tag == 'CostCenter' else
                               'identificação de ambiente' if tag == 'Environment' else
                               'identificação de proprietário' if tag == 'Owner' else
                               'rastreamento de aplicação')
                        ),
                        estimated_savings=0,
                        priority='MEDIUM',
                        title=f'Tag "{tag}" presente em apenas {tag_coverage:.1f}% dos recursos',
                        action=f'Aplicar tag "{tag}" nos recursos faltantes'
                    ))
        
        return recommendations
    
    def analyze_usage(self) -> Dict[str, Any]:
        """Analisa padrões de uso de tags"""
        coverage = self.analyze_tag_coverage()
        tags_in_use = self.get_all_tags_in_use()
        recommendations = self.get_recommendations()
        
        return {
            'service': 'tag_governance',
            'summary': {
                'total_resources': coverage.total_resources,
                'compliant_resources': coverage.fully_tagged_resources,
                'compliance_percent': coverage.compliance_percent,
                'coverage_percent': coverage.coverage_percent
            },
            'tag_policy': self._tag_policy.to_dict(),
            'tags_in_use_count': len(tags_in_use),
            'coverage_by_tag': coverage.tag_statistics,
            'recommendations_count': len(recommendations),
            'optimization_opportunities': [r.title for r in recommendations]
        }
