"""
AWS API Gateway FinOps Service

Análise de custos e otimização para AWS API Gateway:
- REST APIs (v1)
- HTTP APIs (v2)
- WebSocket APIs
- Stages, deployments e usage plans
- Recomendações de otimização (caching, throttling)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class RestAPI:
    """Representa uma REST API do API Gateway"""
    id: str
    name: str
    description: str = ''
    created_date: Optional[datetime] = None
    api_key_source: str = 'HEADER'
    endpoint_configuration: Dict[str, Any] = field(default_factory=dict)
    policy: str = ''
    tags: Dict[str, str] = field(default_factory=dict)
    disable_execute_api_endpoint: bool = False
    
    @property
    def endpoint_type(self) -> str:
        types = self.endpoint_configuration.get('types', ['EDGE'])
        return types[0] if types else 'EDGE'
    
    @property
    def is_regional(self) -> bool:
        return self.endpoint_type == 'REGIONAL'
    
    @property
    def is_edge(self) -> bool:
        return self.endpoint_type == 'EDGE'
    
    @property
    def is_private(self) -> bool:
        return self.endpoint_type == 'PRIVATE'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'endpoint_type': self.endpoint_type,
            'is_regional': self.is_regional,
            'is_edge': self.is_edge,
            'is_private': self.is_private,
            'api_key_source': self.api_key_source,
            'disable_execute_api_endpoint': self.disable_execute_api_endpoint,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'tags': self.tags
        }


@dataclass
class HttpAPI:
    """Representa uma HTTP API (v2) do API Gateway"""
    api_id: str
    name: str
    protocol_type: str = 'HTTP'
    api_endpoint: str = ''
    description: str = ''
    created_date: Optional[datetime] = None
    disable_execute_api_endpoint: bool = False
    cors_configuration: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_http(self) -> bool:
        return self.protocol_type == 'HTTP'
    
    @property
    def is_websocket(self) -> bool:
        return self.protocol_type == 'WEBSOCKET'
    
    @property
    def has_cors(self) -> bool:
        return bool(self.cors_configuration)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'api_id': self.api_id,
            'name': self.name,
            'protocol_type': self.protocol_type,
            'api_endpoint': self.api_endpoint,
            'description': self.description,
            'is_http': self.is_http,
            'is_websocket': self.is_websocket,
            'has_cors': self.has_cors,
            'disable_execute_api_endpoint': self.disable_execute_api_endpoint,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'tags': self.tags
        }


@dataclass
class APIStage:
    """Representa um Stage de API"""
    stage_name: str
    deployment_id: str = ''
    description: str = ''
    cache_cluster_enabled: bool = False
    cache_cluster_size: str = ''
    cache_cluster_status: str = ''
    method_settings: Dict[str, Any] = field(default_factory=dict)
    throttling_burst_limit: int = 0
    throttling_rate_limit: float = 0.0
    tracing_enabled: bool = False
    created_date: Optional[datetime] = None
    last_updated_date: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    api_id: str = ''
    
    @property
    def has_caching(self) -> bool:
        return self.cache_cluster_enabled
    
    @property
    def has_throttling(self) -> bool:
        return self.throttling_burst_limit > 0 or self.throttling_rate_limit > 0
    
    @property
    def has_tracing(self) -> bool:
        return self.tracing_enabled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stage_name': self.stage_name,
            'api_id': self.api_id,
            'deployment_id': self.deployment_id,
            'description': self.description,
            'has_caching': self.has_caching,
            'cache_cluster_size': self.cache_cluster_size,
            'cache_cluster_status': self.cache_cluster_status,
            'has_throttling': self.has_throttling,
            'throttling_burst_limit': self.throttling_burst_limit,
            'throttling_rate_limit': self.throttling_rate_limit,
            'has_tracing': self.has_tracing,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_updated_date': self.last_updated_date.isoformat() if self.last_updated_date else None,
            'tags': self.tags
        }


@dataclass
class UsagePlan:
    """Representa um Usage Plan do API Gateway"""
    id: str
    name: str
    description: str = ''
    api_stages: List[Dict[str, str]] = field(default_factory=list)
    throttle: Dict[str, Any] = field(default_factory=dict)
    quota: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def has_throttle(self) -> bool:
        return bool(self.throttle)
    
    @property
    def has_quota(self) -> bool:
        return bool(self.quota)
    
    @property
    def throttle_burst_limit(self) -> int:
        return self.throttle.get('burstLimit', 0)
    
    @property
    def throttle_rate_limit(self) -> float:
        return self.throttle.get('rateLimit', 0.0)
    
    @property
    def quota_limit(self) -> int:
        return self.quota.get('limit', 0)
    
    @property
    def quota_period(self) -> str:
        return self.quota.get('period', '')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'api_stages': self.api_stages,
            'has_throttle': self.has_throttle,
            'has_quota': self.has_quota,
            'throttle_burst_limit': self.throttle_burst_limit,
            'throttle_rate_limit': self.throttle_rate_limit,
            'quota_limit': self.quota_limit,
            'quota_period': self.quota_period,
            'tags': self.tags
        }


class APIGatewayService(BaseAWSService):
    """Serviço FinOps para análise de AWS API Gateway"""
    
    def __init__(self, client_factory):
        self.client_factory = client_factory
        self._apigw_client = None
        self._apigwv2_client = None
    
    @property
    def apigw_client(self):
        if self._apigw_client is None:
            self._apigw_client = self.client_factory.get_client('apigateway')
        return self._apigw_client
    
    @property
    def apigwv2_client(self):
        if self._apigwv2_client is None:
            self._apigwv2_client = self.client_factory.get_client('apigatewayv2')
        return self._apigwv2_client
    
    @property
    def service_name(self) -> str:
        return "AWS API Gateway"
    
    def health_check(self) -> bool:
        try:
            self.apigw_client.get_rest_apis(limit=1)
            return True
        except Exception:
            return False
    
    def get_rest_apis(self) -> List[RestAPI]:
        apis = []
        try:
            paginator = self.apigw_client.get_paginator('get_rest_apis')
            for page in paginator.paginate():
                for api in page.get('items', []):
                    apis.append(RestAPI(
                        id=api.get('id', ''),
                        name=api.get('name', ''),
                        description=api.get('description', ''),
                        created_date=api.get('createdDate'),
                        api_key_source=api.get('apiKeySource', 'HEADER'),
                        endpoint_configuration=api.get('endpointConfiguration', {}),
                        policy=api.get('policy', ''),
                        tags=api.get('tags', {}),
                        disable_execute_api_endpoint=api.get('disableExecuteApiEndpoint', False)
                    ))
        except Exception:
            pass
        return apis
    
    def get_http_apis(self) -> List[HttpAPI]:
        apis = []
        try:
            paginator = self.apigwv2_client.get_paginator('get_apis')
            for page in paginator.paginate():
                for api in page.get('Items', []):
                    apis.append(HttpAPI(
                        api_id=api.get('ApiId', ''),
                        name=api.get('Name', ''),
                        protocol_type=api.get('ProtocolType', 'HTTP'),
                        api_endpoint=api.get('ApiEndpoint', ''),
                        description=api.get('Description', ''),
                        created_date=api.get('CreatedDate'),
                        disable_execute_api_endpoint=api.get('DisableExecuteApiEndpoint', False),
                        cors_configuration=api.get('CorsConfiguration', {}),
                        tags=api.get('Tags', {})
                    ))
        except Exception:
            pass
        return apis
    
    def get_stages(self, rest_api_id: str) -> List[APIStage]:
        stages = []
        try:
            response = self.apigw_client.get_stages(restApiId=rest_api_id)
            for stage in response.get('item', []):
                method_settings = stage.get('methodSettings', {})
                default_settings = method_settings.get('*/*', {})
                
                stages.append(APIStage(
                    stage_name=stage.get('stageName', ''),
                    api_id=rest_api_id,
                    deployment_id=stage.get('deploymentId', ''),
                    description=stage.get('description', ''),
                    cache_cluster_enabled=stage.get('cacheClusterEnabled', False),
                    cache_cluster_size=stage.get('cacheClusterSize', ''),
                    cache_cluster_status=stage.get('cacheClusterStatus', ''),
                    method_settings=method_settings,
                    throttling_burst_limit=default_settings.get('throttlingBurstLimit', 0),
                    throttling_rate_limit=default_settings.get('throttlingRateLimit', 0.0),
                    tracing_enabled=stage.get('tracingEnabled', False),
                    created_date=stage.get('createdDate'),
                    last_updated_date=stage.get('lastUpdatedDate'),
                    tags=stage.get('tags', {})
                ))
        except Exception:
            pass
        return stages
    
    def get_usage_plans(self) -> List[UsagePlan]:
        plans = []
        try:
            paginator = self.apigw_client.get_paginator('get_usage_plans')
            for page in paginator.paginate():
                for plan in page.get('items', []):
                    plans.append(UsagePlan(
                        id=plan.get('id', ''),
                        name=plan.get('name', ''),
                        description=plan.get('description', ''),
                        api_stages=plan.get('apiStages', []),
                        throttle=plan.get('throttle', {}),
                        quota=plan.get('quota', {}),
                        tags=plan.get('tags', {})
                    ))
        except Exception:
            pass
        return plans
    
    def get_resources(self) -> Dict[str, Any]:
        rest_apis = self.get_rest_apis()
        http_apis = self.get_http_apis()
        usage_plans = self.get_usage_plans()
        
        all_stages = []
        for api in rest_apis:
            stages = self.get_stages(api.id)
            all_stages.extend(stages)
        
        websocket_apis = [api for api in http_apis if api.is_websocket]
        http_only_apis = [api for api in http_apis if api.is_http]
        
        return {
            'rest_apis': [api.to_dict() for api in rest_apis],
            'http_apis': [api.to_dict() for api in http_only_apis],
            'websocket_apis': [api.to_dict() for api in websocket_apis],
            'stages': [s.to_dict() for s in all_stages],
            'usage_plans': [p.to_dict() for p in usage_plans],
            'summary': {
                'total_rest_apis': len(rest_apis),
                'total_http_apis': len(http_only_apis),
                'total_websocket_apis': len(websocket_apis),
                'regional_apis': sum(1 for api in rest_apis if api.is_regional),
                'edge_apis': sum(1 for api in rest_apis if api.is_edge),
                'private_apis': sum(1 for api in rest_apis if api.is_private),
                'total_stages': len(all_stages),
                'stages_with_caching': sum(1 for s in all_stages if s.has_caching),
                'stages_with_tracing': sum(1 for s in all_stages if s.has_tracing),
                'total_usage_plans': len(usage_plans)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        total_apis = (resources['summary']['total_rest_apis'] + 
                     resources['summary']['total_http_apis'] + 
                     resources['summary']['total_websocket_apis'])
        total_stages = max(resources['summary']['total_stages'], 1)
        
        return {
            'total_api_count': total_apis,
            'rest_api_count': resources['summary']['total_rest_apis'],
            'http_api_count': resources['summary']['total_http_apis'],
            'websocket_api_count': resources['summary']['total_websocket_apis'],
            'caching_enabled_ratio': resources['summary']['stages_with_caching'] / total_stages,
            'tracing_enabled_ratio': resources['summary']['stages_with_tracing'] / total_stages,
            'usage_plan_count': resources['summary']['total_usage_plans']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        rest_apis = self.get_rest_apis()
        http_apis = self.get_http_apis()
        
        for api in rest_apis:
            stages = self.get_stages(api.id)
            for stage in stages:
                if not stage.has_caching:
                    recommendations.append(ServiceRecommendation(
                        resource_id=f'{api.name}/{stage.stage_name}',
                        resource_type='APIStage',
                        title='Habilitar caching para reduzir custos',
                        recommendation=f'Stage {stage.stage_name} da API {api.name} não tem caching. '
                                     f'Habilitar cache pode reduzir chamadas ao backend e custos.',
                        action='Habilitar cache cluster no stage',
                        estimated_savings=None,
                        priority='medium',
                        category='cost_optimization'
                    ))
                
                if not stage.has_throttling:
                    recommendations.append(ServiceRecommendation(
                        resource_id=f'{api.name}/{stage.stage_name}',
                        resource_type='APIStage',
                        title='Configurar throttling para proteção',
                        recommendation=f'Stage {stage.stage_name} da API {api.name} não tem throttling. '
                                     f'Configure limites para evitar custos inesperados.',
                        action='Definir throttlingBurstLimit e throttlingRateLimit',
                        estimated_savings=None,
                        priority='high',
                        category='cost_optimization'
                    ))
            
            if api.is_edge:
                recommendations.append(ServiceRecommendation(
                    resource_id=api.name,
                    resource_type='RestAPI',
                    title='Considerar endpoint Regional',
                    recommendation=f'API {api.name} usa endpoint EDGE. '
                                 f'Se o tráfego é majoritariamente regional, '
                                 f'considere mudar para REGIONAL para reduzir custos.',
                    action='Migrar para endpoint REGIONAL',
                    estimated_savings=None,
                    priority='low',
                    category='cost_optimization'
                ))
        
        for api in rest_apis:
            recommendations.append(ServiceRecommendation(
                resource_id=api.name,
                resource_type='RestAPI',
                title='Avaliar migração para HTTP API',
                recommendation=f'REST API {api.name} pode ser candidata a migração para HTTP API. '
                             f'HTTP APIs são até 70% mais baratas que REST APIs.',
                action='Avaliar migração para HTTP API v2',
                estimated_savings=None,
                priority='medium',
                category='cost_optimization'
            ))
        
        return recommendations
