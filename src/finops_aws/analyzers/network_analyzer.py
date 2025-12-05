"""
Network Analyzer - Análise de serviços de rede AWS

Serviços cobertos:
- VPC
- ELB/ALB/NLB
- CloudFront
- Route53
- API Gateway
- Direct Connect
- Transit Gateway

Design Pattern: Strategy
"""
from typing import Dict, List, Any
from datetime import datetime
import logging

from .base_analyzer import (
    BaseAnalyzer,
    Recommendation,
    Priority,
    Impact
)

logger = logging.getLogger(__name__)


class NetworkAnalyzer(BaseAnalyzer):
    """Analyzer para serviços de rede AWS."""
    
    name = "NetworkAnalyzer"
    
    def _get_client(self, region: str) -> Any:
        """Retorna clientes boto3 para rede."""
        import boto3
        return {
            'elbv2': boto3.client('elbv2', region_name=region),
            'elb': boto3.client('elb', region_name=region),
            'cloudfront': boto3.client('cloudfront'),
            'apigateway': boto3.client('apigateway', region_name=region),
        }
    
    def _collect_resources(self, clients: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta recursos de rede."""
        resources = {}
        
        elbv2 = clients.get('elbv2')
        if elbv2:
            try:
                resources['load_balancers'] = elbv2.describe_load_balancers()
                resources['target_groups'] = elbv2.describe_target_groups()
                resources['elbv2_client'] = elbv2
            except Exception as e:
                logger.warning(f"Erro coletando ELBv2: {e}")
        
        elb = clients.get('elb')
        if elb:
            try:
                resources['classic_lbs'] = elb.describe_load_balancers()
            except Exception as e:
                logger.warning(f"Erro coletando Classic ELB: {e}")
        
        cloudfront = clients.get('cloudfront')
        if cloudfront:
            try:
                resources['distributions'] = cloudfront.list_distributions()
            except Exception as e:
                logger.warning(f"Erro coletando CloudFront: {e}")
        
        apigateway = clients.get('apigateway')
        if apigateway:
            try:
                resources['rest_apis'] = apigateway.get_rest_apis()
            except Exception as e:
                logger.warning(f"Erro coletando API Gateway: {e}")
        
        return resources
    
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """Analisa recursos e gera recomendações."""
        recommendations = []
        metrics = {}
        
        recommendations.extend(self._analyze_load_balancers(resources, metrics))
        recommendations.extend(self._analyze_classic_elb(resources, metrics))
        recommendations.extend(self._analyze_cloudfront(resources, metrics))
        recommendations.extend(self._analyze_api_gateway(resources, metrics))
        
        return recommendations, metrics
    
    def _analyze_load_balancers(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa Application/Network Load Balancers."""
        recommendations = []
        lbs_data = resources.get('load_balancers', {})
        elbv2 = resources.get('elbv2_client')
        
        lbs = lbs_data.get('LoadBalancers', [])
        metrics['load_balancers_v2'] = len(lbs)
        
        if not elbv2:
            return recommendations
        
        for lb in lbs:
            lb_arn = lb.get('LoadBalancerArn', '')
            lb_name = lb.get('LoadBalancerName', '')
            lb_type = lb.get('Type', 'application')
            
            try:
                tgs = elbv2.describe_target_groups(LoadBalancerArn=lb_arn)
                has_targets = False
                
                for tg in tgs.get('TargetGroups', []):
                    health = elbv2.describe_target_health(
                        TargetGroupArn=tg['TargetGroupArn']
                    )
                    if health.get('TargetHealthDescriptions'):
                        has_targets = True
                        break
                
                if not has_targets:
                    cost = 16.20 if lb_type == 'application' else 22.50
                    recommendations.append(self._create_recommendation(
                        rec_type='ELB_NO_TARGETS',
                        resource_id=lb_name,
                        description=f'Load Balancer {lb_name} ({lb_type}) sem targets registrados',
                        service='ELB Analysis',
                        priority=Priority.HIGH,
                        savings=cost
                    ))
            except Exception:
                pass
        
        target_groups_data = resources.get('target_groups', {})
        metrics['target_groups'] = len(target_groups_data.get('TargetGroups', []))
        
        return recommendations
    
    def _analyze_classic_elb(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa Classic Load Balancers."""
        recommendations = []
        classic_data = resources.get('classic_lbs', {})
        
        classic_lbs = classic_data.get('LoadBalancerDescriptions', [])
        metrics['classic_load_balancers'] = len(classic_lbs)
        
        for lb in classic_lbs:
            lb_name = lb.get('LoadBalancerName', '')
            recommendations.append(self._create_recommendation(
                rec_type='ELB_CLASSIC',
                resource_id=lb_name,
                description=f'Classic ELB {lb_name} - considere migrar para ALB/NLB',
                service='ELB Analysis',
                priority=Priority.LOW
            ))
        
        return recommendations
    
    def _analyze_cloudfront(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa distribuições CloudFront."""
        recommendations = []
        distributions_data = resources.get('distributions', {})
        
        dist_list = distributions_data.get('DistributionList', {})
        distributions = dist_list.get('Items', [])
        metrics['cloudfront_distributions'] = len(distributions)
        
        for dist in distributions:
            dist_id = dist.get('Id', '')
            
            if not dist.get('HttpVersion', '').startswith('http2'):
                recommendations.append(self._create_recommendation(
                    rec_type='CLOUDFRONT_HTTP2',
                    resource_id=dist_id,
                    description=f'CloudFront {dist_id} não usa HTTP/2 - habilitar para melhor performance',
                    service='CloudFront Optimization',
                    priority=Priority.LOW
                ))
        
        return recommendations
    
    def _analyze_api_gateway(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa APIs do API Gateway."""
        recommendations = []
        apis_data = resources.get('rest_apis', {})
        
        apis = apis_data.get('items', [])
        metrics['api_gateway_apis'] = len(apis)
        
        return recommendations
    
    def _get_services_list(self) -> List[str]:
        """Retorna serviços analisados."""
        return ['ELB/ALB/NLB', 'Classic ELB', 'CloudFront', 'API Gateway']
