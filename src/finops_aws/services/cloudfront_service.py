"""
CloudFront FinOps Service - Análise de Custos de CDN

FASE 2 - Prioridade 1: Networking (alto custo de transferência)
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de distribuições CloudFront
- Análise de requests e transferência de dados
- Recomendações de cache e price class
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class CloudFrontDistribution:
    """Representa uma distribuição CloudFront"""
    distribution_id: str
    domain_name: str
    status: str
    enabled: bool
    price_class: str
    http_version: str
    is_ipv6_enabled: bool
    default_root_object: str = ""
    aliases: List[str] = field(default_factory=list)
    origins: List[Dict] = field(default_factory=list)
    cache_behaviors: int = 0
    web_acl_id: Optional[str] = None
    logging_enabled: bool = False
    last_modified: Optional[datetime] = None
    comment: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'distribution_id': self.distribution_id,
            'domain_name': self.domain_name,
            'status': self.status,
            'enabled': self.enabled,
            'price_class': self.price_class,
            'http_version': self.http_version,
            'is_ipv6_enabled': self.is_ipv6_enabled,
            'aliases': self.aliases,
            'origins_count': len(self.origins),
            'cache_behaviors': self.cache_behaviors,
            'web_acl_id': self.web_acl_id,
            'logging_enabled': self.logging_enabled,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        }


class CloudFrontService(BaseAWSService):
    """
    Serviço FinOps para análise de custos CloudFront
    
    Analisa distribuições CloudFront, métricas de requests
    e transferência, e fornece recomendações de otimização.
    """
    
    def __init__(
        self,
        cloudfront_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._cloudfront_client = cloudfront_client
    
    @property
    def cloudfront_client(self):
        if self._cloudfront_client is None:
            import boto3
            self._cloudfront_client = boto3.client('cloudfront')
        return self._cloudfront_client
    
    def get_service_name(self) -> str:
        return "Amazon CloudFront"
    
    def health_check(self) -> bool:
        try:
            self.cloudfront_client.list_distributions(MaxItems='1')
            return True
        except Exception:
            return False
    
    
    def get_distributions(self) -> List[CloudFrontDistribution]:
        """Lista todas as distribuições CloudFront"""
        distributions = []
        
        paginator = self.cloudfront_client.get_paginator('list_distributions')
        
        for page in paginator.paginate():
            dist_list = page.get('DistributionList', {})
            for dist in dist_list.get('Items', []):
                aliases = dist.get('Aliases', {}).get('Items', [])
                origins = dist.get('Origins', {}).get('Items', [])
                
                distribution = CloudFrontDistribution(
                    distribution_id=dist['Id'],
                    domain_name=dist['DomainName'],
                    status=dist['Status'],
                    enabled=dist['Enabled'],
                    price_class=dist.get('PriceClass', 'PriceClass_All'),
                    http_version=dist.get('HttpVersion', 'http2'),
                    is_ipv6_enabled=dist.get('IsIPV6Enabled', True),
                    default_root_object=dist.get('DefaultRootObject', ''),
                    aliases=aliases,
                    origins=[{'id': o['Id'], 'domain': o['DomainName']} for o in origins],
                    cache_behaviors=dist.get('CacheBehaviors', {}).get('Quantity', 0),
                    web_acl_id=dist.get('WebACLId'),
                    logging_enabled=dist.get('Logging', {}).get('Enabled', False),
                    last_modified=dist.get('LastModifiedTime'),
                    comment=dist.get('Comment', '')
                )
                distributions.append(distribution)
        
        return distributions
    
    
    def get_distribution_metrics(self, distribution_id: str, days: int = 7) -> Dict[str, Any]:
        """Obtém métricas de uma distribuição"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        
        requests = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/CloudFront',
            MetricName='Requests',
            Dimensions=[
                {'Name': 'DistributionId', 'Value': distribution_id},
                {'Name': 'Region', 'Value': 'Global'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if requests.get('Datapoints'):
            metrics['total_requests'] = int(sum(d['Sum'] for d in requests['Datapoints']))
        
        bytes_downloaded = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/CloudFront',
            MetricName='BytesDownloaded',
            Dimensions=[
                {'Name': 'DistributionId', 'Value': distribution_id},
                {'Name': 'Region', 'Value': 'Global'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if bytes_downloaded.get('Datapoints'):
            total_bytes = sum(d['Sum'] for d in bytes_downloaded['Datapoints'])
            metrics['bytes_downloaded_gb'] = round(total_bytes / (1024**3), 2)
        
        error_rate = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/CloudFront',
            MetricName='4xxErrorRate',
            Dimensions=[
                {'Name': 'DistributionId', 'Value': distribution_id},
                {'Name': 'Region', 'Value': 'Global'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average']
        )
        if error_rate.get('Datapoints'):
            metrics['error_rate_4xx'] = round(
                sum(d['Average'] for d in error_rate['Datapoints']) / len(error_rate['Datapoints']), 2
            )
        
        cache_hit = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/CloudFront',
            MetricName='CacheHitRate',
            Dimensions=[
                {'Name': 'DistributionId', 'Value': distribution_id},
                {'Name': 'Region', 'Value': 'Global'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average']
        )
        if cache_hit.get('Datapoints'):
            metrics['cache_hit_rate'] = round(
                sum(d['Average'] for d in cache_hit['Datapoints']) / len(cache_hit['Datapoints']), 2
            )
        
        return metrics
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        distributions = self.get_distributions()
        return [dist.to_dict() for dist in distributions]
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de CloudFront"""
        distributions = self.get_distributions()
        
        total_requests = 0
        total_bytes = 0
        price_classes = {}
        
        for dist in distributions:
            price_classes[dist.price_class] = price_classes.get(dist.price_class, 0) + 1
            
            try:
                metrics = self.get_distribution_metrics(dist.distribution_id, days=7)
                total_requests += metrics.get('total_requests', 0)
                total_bytes += metrics.get('bytes_downloaded_gb', 0)
            except Exception:
                pass
        
        enabled_count = len([d for d in distributions if d.enabled])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(distributions),
            metrics={
                'total_distributions': len(distributions),
                'enabled_distributions': enabled_count,
                'disabled_distributions': len(distributions) - enabled_count,
                'total_requests_7d': total_requests,
                'total_transfer_gb_7d': round(total_bytes, 2),
                'price_classes': price_classes
            },
            period_days=7,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para CloudFront"""
        recommendations = []
        distributions = self.get_distributions()
        
        for dist in distributions:
            if not dist.enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=dist.distribution_id,
                    resource_type='CloudFront Distribution',
                    recommendation_type='DISABLED_RESOURCE',
                    title='Distribuição desabilitada',
                    description=f'Distribuição {dist.distribution_id} está desabilitada. '
                               f'Considere remover se não for mais necessária.',
                    estimated_savings=5.0,
                    priority='LOW',
                    action='Remover distribuição não utilizada'
                ))
                continue
            
            try:
                metrics = self.get_distribution_metrics(dist.distribution_id, days=30)
                
                if metrics.get('total_requests', 0) == 0:
                    recommendations.append(ServiceRecommendation(
                        resource_id=dist.distribution_id,
                        resource_type='CloudFront Distribution',
                        recommendation_type='UNUSED_RESOURCE',
                        title='Distribuição sem tráfego',
                        description=f'Distribuição {dist.distribution_id} não teve requests nos últimos 30 dias. '
                                   f'Considere desabilitar ou remover.',
                        estimated_savings=10.0,
                        priority='MEDIUM',
                        action='Desabilitar ou remover distribuição'
                    ))
                
                cache_hit = metrics.get('cache_hit_rate', 100)
                if cache_hit < 70:
                    recommendations.append(ServiceRecommendation(
                        resource_id=dist.distribution_id,
                        resource_type='CloudFront Distribution',
                        recommendation_type='LOW_CACHE_HIT',
                        title=f'Taxa de cache hit baixa ({cache_hit}%)',
                        description=f'Distribuição {dist.distribution_id} tem cache hit rate de apenas {cache_hit}%. '
                                   f'Otimize TTLs e cache behaviors para reduzir custos de origin.',
                        estimated_savings=metrics.get('bytes_downloaded_gb', 0) * 0.085 * 0.3,
                        priority='HIGH',
                        action='Otimizar políticas de cache'
                    ))
                
            except Exception:
                pass
            
            if dist.price_class == 'PriceClass_All':
                recommendations.append(ServiceRecommendation(
                    resource_id=dist.distribution_id,
                    resource_type='CloudFront Distribution',
                    recommendation_type='PRICE_CLASS_OPTIMIZATION',
                    title='Avaliar Price Class',
                    description=f'Distribuição {dist.distribution_id} usa PriceClass_All (todas as regiões). '
                               f'Se seu tráfego é majoritariamente de NA/EU, considere PriceClass_100 ou _200.',
                    estimated_savings=50.0,
                    priority='MEDIUM',
                    action='Avaliar mudança de Price Class'
                ))
            
            if not dist.logging_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=dist.distribution_id,
                    resource_type='CloudFront Distribution',
                    recommendation_type='MONITORING',
                    title='Logging não habilitado',
                    description=f'Distribuição {dist.distribution_id} não tem logging habilitado. '
                               f'Considere habilitar para análise de tráfego e otimização.',
                    estimated_savings=0.0,
                    priority='LOW',
                    action='Habilitar access logging'
                ))
            
            if dist.http_version == 'http1.1':
                recommendations.append(ServiceRecommendation(
                    resource_id=dist.distribution_id,
                    resource_type='CloudFront Distribution',
                    recommendation_type='PERFORMANCE',
                    title='Atualizar para HTTP/2 ou HTTP/3',
                    description=f'Distribuição {dist.distribution_id} usa HTTP/1.1. '
                               f'Atualize para HTTP/2 ou HTTP/3 para melhor performance.',
                    estimated_savings=0.0,
                    priority='LOW',
                    action='Atualizar HTTP version'
                ))
        
        return recommendations
