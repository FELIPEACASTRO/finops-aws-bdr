"""
OpenSearch FinOps Service - Análise de Custos do Amazon OpenSearch Service

FASE 2.4 - Serviços Não-Serverless de Alto Custo
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de domínios OpenSearch
- Análise de instâncias e storage
- Métricas de utilização
- Recomendações de otimização de custos
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class OpenSearchDomain:
    """Representa um domínio OpenSearch"""
    domain_name: str
    domain_id: str
    arn: str
    engine_version: str
    endpoint: Optional[str] = None
    endpoints: Dict[str, str] = field(default_factory=dict)
    processing: bool = False
    upgrade_processing: bool = False
    created: bool = True
    deleted: bool = False
    cluster_config: Dict[str, Any] = field(default_factory=dict)
    ebs_options: Dict[str, Any] = field(default_factory=dict)
    access_policies: Optional[str] = None
    snapshot_options: Dict[str, Any] = field(default_factory=dict)
    vpc_options: Dict[str, Any] = field(default_factory=dict)
    cognito_options: Dict[str, Any] = field(default_factory=dict)
    encryption_at_rest_options: Dict[str, Any] = field(default_factory=dict)
    node_to_node_encryption_options: Dict[str, Any] = field(default_factory=dict)
    advanced_options: Dict[str, str] = field(default_factory=dict)
    log_publishing_options: Dict[str, Any] = field(default_factory=dict)
    domain_endpoint_options: Dict[str, Any] = field(default_factory=dict)
    advanced_security_options: Dict[str, Any] = field(default_factory=dict)
    auto_tune_options: Dict[str, Any] = field(default_factory=dict)
    off_peak_window_options: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def instance_type(self) -> str:
        return self.cluster_config.get('InstanceType', 'unknown')
    
    @property
    def instance_count(self) -> int:
        return self.cluster_config.get('InstanceCount', 0)
    
    @property
    def dedicated_master_enabled(self) -> bool:
        return self.cluster_config.get('DedicatedMasterEnabled', False)
    
    @property
    def dedicated_master_type(self) -> Optional[str]:
        return self.cluster_config.get('DedicatedMasterType')
    
    @property
    def dedicated_master_count(self) -> int:
        return self.cluster_config.get('DedicatedMasterCount', 0)
    
    @property
    def zone_awareness_enabled(self) -> bool:
        return self.cluster_config.get('ZoneAwarenessEnabled', False)
    
    @property
    def availability_zone_count(self) -> int:
        zone_config = self.cluster_config.get('ZoneAwarenessConfig', {})
        return zone_config.get('AvailabilityZoneCount', 1)
    
    @property
    def warm_enabled(self) -> bool:
        return self.cluster_config.get('WarmEnabled', False)
    
    @property
    def warm_count(self) -> int:
        return self.cluster_config.get('WarmCount', 0)
    
    @property
    def warm_type(self) -> Optional[str]:
        return self.cluster_config.get('WarmType')
    
    @property
    def cold_storage_enabled(self) -> bool:
        cold = self.cluster_config.get('ColdStorageOptions', {})
        return cold.get('Enabled', False)
    
    @property
    def ebs_enabled(self) -> bool:
        return self.ebs_options.get('EBSEnabled', False)
    
    @property
    def volume_type(self) -> str:
        return self.ebs_options.get('VolumeType', 'gp2')
    
    @property
    def volume_size_gb(self) -> int:
        return self.ebs_options.get('VolumeSize', 0)
    
    @property
    def iops(self) -> Optional[int]:
        return self.ebs_options.get('Iops')
    
    @property
    def throughput(self) -> Optional[int]:
        return self.ebs_options.get('Throughput')
    
    @property
    def is_vpc(self) -> bool:
        return bool(self.vpc_options.get('VPCId'))
    
    @property
    def vpc_id(self) -> Optional[str]:
        return self.vpc_options.get('VPCId')
    
    @property
    def subnet_ids(self) -> List[str]:
        return self.vpc_options.get('SubnetIds', [])
    
    @property
    def has_encryption_at_rest(self) -> bool:
        return self.encryption_at_rest_options.get('Enabled', False)
    
    @property
    def has_node_to_node_encryption(self) -> bool:
        return self.node_to_node_encryption_options.get('Enabled', False)
    
    @property
    def has_fine_grained_access(self) -> bool:
        return self.advanced_security_options.get('Enabled', False)
    
    @property
    def auto_tune_state(self) -> str:
        return self.auto_tune_options.get('State', 'DISABLED')
    
    @property
    def is_auto_tune_enabled(self) -> bool:
        return self.auto_tune_state in ['ENABLED', 'ENABLE_IN_PROGRESS']
    
    @property
    def https_required(self) -> bool:
        return self.domain_endpoint_options.get('EnforceHTTPS', False)
    
    @property
    def tls_security_policy(self) -> str:
        return self.domain_endpoint_options.get('TLSSecurityPolicy', 'Policy-Min-TLS-1-0-2019-07')
    
    @property
    def total_storage_gb(self) -> int:
        return self.volume_size_gb * self.instance_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'domain_name': self.domain_name,
            'domain_id': self.domain_id,
            'arn': self.arn,
            'engine_version': self.engine_version,
            'endpoint': self.endpoint,
            'instance_type': self.instance_type,
            'instance_count': self.instance_count,
            'dedicated_master_enabled': self.dedicated_master_enabled,
            'dedicated_master_type': self.dedicated_master_type,
            'dedicated_master_count': self.dedicated_master_count,
            'zone_awareness_enabled': self.zone_awareness_enabled,
            'availability_zone_count': self.availability_zone_count,
            'warm_enabled': self.warm_enabled,
            'warm_count': self.warm_count,
            'cold_storage_enabled': self.cold_storage_enabled,
            'ebs_enabled': self.ebs_enabled,
            'volume_type': self.volume_type,
            'volume_size_gb': self.volume_size_gb,
            'total_storage_gb': self.total_storage_gb,
            'is_vpc': self.is_vpc,
            'has_encryption_at_rest': self.has_encryption_at_rest,
            'has_node_to_node_encryption': self.has_node_to_node_encryption,
            'has_fine_grained_access': self.has_fine_grained_access,
            'is_auto_tune_enabled': self.is_auto_tune_enabled,
            'https_required': self.https_required,
            'tags': self.tags
        }


class OpenSearchService(BaseAWSService):
    """
    Serviço FinOps para Amazon OpenSearch Service
    
    Analisa domínios OpenSearch e Elasticsearch e fornece
    recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._opensearch_client = None
        self._cloudwatch_client = None
    
    @property
    def opensearch_client(self):
        if self._opensearch_client is None:
            from ..core.factories import AWSServiceType
            self._opensearch_client = self.client_factory.get_client(AWSServiceType.OPENSEARCH)
        return self._opensearch_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            from ..core.factories import AWSServiceType
            self._cloudwatch_client = self.client_factory.get_client(AWSServiceType.CLOUDWATCH)
        return self._cloudwatch_client
    
    def get_service_name(self) -> str:
        return "OpenSearch"
    
    def health_check(self) -> bool:
        try:
            self.opensearch_client.list_domain_names()
            return True
        except Exception as e:
            logger.error(f"OpenSearch health check failed: {e}")
            return False
    
    def get_domains(self) -> List[OpenSearchDomain]:
        """Lista todos os domínios OpenSearch"""
        domains = []
        
        try:
            response = self.opensearch_client.list_domain_names()
            domain_names = [d['DomainName'] for d in response.get('DomainNames', [])]
            
            if domain_names:
                for domain_name in domain_names:
                    domain = self._get_domain_details(domain_name)
                    if domain:
                        domains.append(domain)
            
            logger.info(f"Found {len(domains)} OpenSearch domains")
            
        except Exception as e:
            logger.error(f"Error listing OpenSearch domains: {e}")
        
        return domains
    
    def _get_domain_details(self, domain_name: str) -> Optional[OpenSearchDomain]:
        """Obtém detalhes de um domínio"""
        try:
            response = self.opensearch_client.describe_domain(DomainName=domain_name)
            data = response.get('DomainStatus', {})
            
            tags = {}
            try:
                arn = data.get('ARN', '')
                if arn:
                    tag_response = self.opensearch_client.list_tags(ARN=arn)
                    for tag in tag_response.get('TagList', []):
                        tags[tag['Key']] = tag['Value']
            except Exception:
                pass
            
            return OpenSearchDomain(
                domain_name=data.get('DomainName', ''),
                domain_id=data.get('DomainId', ''),
                arn=data.get('ARN', ''),
                engine_version=data.get('EngineVersion', ''),
                endpoint=data.get('Endpoint'),
                endpoints=data.get('Endpoints', {}),
                processing=data.get('Processing', False),
                upgrade_processing=data.get('UpgradeProcessing', False),
                created=data.get('Created', True),
                deleted=data.get('Deleted', False),
                cluster_config=data.get('ClusterConfig', {}),
                ebs_options=data.get('EBSOptions', {}),
                access_policies=data.get('AccessPolicies'),
                snapshot_options=data.get('SnapshotOptions', {}),
                vpc_options=data.get('VPCOptions', {}),
                cognito_options=data.get('CognitoOptions', {}),
                encryption_at_rest_options=data.get('EncryptionAtRestOptions', {}),
                node_to_node_encryption_options=data.get('NodeToNodeEncryptionOptions', {}),
                advanced_options=data.get('AdvancedOptions', {}),
                log_publishing_options=data.get('LogPublishingOptions', {}),
                domain_endpoint_options=data.get('DomainEndpointOptions', {}),
                advanced_security_options=data.get('AdvancedSecurityOptions', {}),
                auto_tune_options=data.get('AutoTuneOptions', {}),
                off_peak_window_options=data.get('OffPeakWindowOptions', {}),
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error describing domain {domain_name}: {e}")
            return None
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos OpenSearch"""
        domains = self.get_domains()
        
        total_instances = sum(d.instance_count for d in domains)
        total_storage = sum(d.total_storage_gb for d in domains)
        
        return {
            'domains': [d.to_dict() for d in domains],
            'summary': {
                'total_domains': len(domains),
                'total_data_nodes': total_instances,
                'total_storage_gb': total_storage,
                'vpc_domains': len([d for d in domains if d.is_vpc]),
                'encrypted_domains': len([d for d in domains if d.has_encryption_at_rest]),
                'auto_tune_enabled': len([d for d in domains if d.is_auto_tune_enabled]),
                'dedicated_master_domains': len([d for d in domains if d.dedicated_master_enabled]),
                'warm_storage_domains': len([d for d in domains if d.warm_enabled])
            }
        }
    
    def get_costs(self) -> List[ServiceCost]:
        """Retorna estimativas de custo para domínios OpenSearch"""
        costs = []
        domains = self.get_domains()
        
        for domain in domains:
            instance_cost = self._get_instance_hourly_rate(domain.instance_type) * 24 * 30 * domain.instance_count
            
            master_cost = 0.0
            if domain.dedicated_master_enabled and domain.dedicated_master_type:
                master_cost = self._get_instance_hourly_rate(domain.dedicated_master_type) * 24 * 30 * domain.dedicated_master_count
            
            storage_cost = 0.0
            if domain.ebs_enabled:
                storage_rate = 0.10 if domain.volume_type == 'gp2' else 0.08
                storage_cost = domain.total_storage_gb * storage_rate
            
            warm_cost = 0.0
            if domain.warm_enabled and domain.warm_type:
                warm_cost = self._get_warm_instance_rate(domain.warm_type) * 24 * 30 * domain.warm_count
            
            total_cost = instance_cost + master_cost + storage_cost + warm_cost
            
            costs.append(ServiceCost(
                service_name='OpenSearch',
                resource_id=domain.arn,
                cost=total_cost,
                period='monthly_estimate',
                currency='USD',
                metadata={
                    'domain_name': domain.domain_name,
                    'instance_type': domain.instance_type,
                    'instance_count': domain.instance_count,
                    'storage_gb': domain.total_storage_gb,
                    'has_warm': domain.warm_enabled
                }
            ))
        
        return costs
    
    def _get_instance_hourly_rate(self, instance_type: str) -> float:
        """Retorna taxa horária estimada"""
        rates = {
            't3.small.search': 0.036,
            't3.medium.search': 0.073,
            'm5.large.search': 0.142,
            'm5.xlarge.search': 0.284,
            'm5.2xlarge.search': 0.567,
            'm6g.large.search': 0.128,
            'm6g.xlarge.search': 0.255,
            'r5.large.search': 0.186,
            'r5.xlarge.search': 0.372,
            'r5.2xlarge.search': 0.744,
            'r6g.large.search': 0.167,
            'r6g.xlarge.search': 0.335,
            'c5.large.search': 0.125,
            'c5.xlarge.search': 0.250,
            'c6g.large.search': 0.112,
            'c6g.xlarge.search': 0.224,
        }
        return rates.get(instance_type, 0.15)
    
    def _get_warm_instance_rate(self, instance_type: str) -> float:
        """Retorna taxa horária para UltraWarm"""
        rates = {
            'ultrawarm1.medium.search': 0.24,
            'ultrawarm1.large.search': 0.48,
        }
        return rates.get(instance_type, 0.30)
    
    def get_metrics(self) -> List[ServiceMetrics]:
        """Retorna métricas dos domínios OpenSearch"""
        metrics = []
        domains = self.get_domains()
        
        for domain in domains:
            try:
                cpu = self._get_domain_metric(domain.domain_name, 'CPUUtilization')
                storage_free = self._get_domain_metric(domain.domain_name, 'FreeStorageSpace')
                
                if cpu is not None:
                    metrics.append(ServiceMetrics(
                        service_name='OpenSearch',
                        resource_id=domain.arn,
                        metric_name='CPUUtilization',
                        value=cpu,
                        unit='Percent',
                        period='last_hour',
                        metadata={'domain_name': domain.domain_name}
                    ))
                
                if storage_free is not None:
                    metrics.append(ServiceMetrics(
                        service_name='OpenSearch',
                        resource_id=domain.arn,
                        metric_name='FreeStorageSpace',
                        value=storage_free,
                        unit='Megabytes',
                        period='last_hour',
                        metadata={'domain_name': domain.domain_name}
                    ))
                
            except Exception as e:
                logger.warning(f"Error getting metrics for {domain.domain_name}: {e}")
        
        return metrics
    
    def _get_domain_metric(self, domain_name: str, metric_name: str) -> Optional[float]:
        """Obtém métrica do CloudWatch"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ES',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'DomainName', 'Value': domain_name},
                    {'Name': 'ClientId', 'Value': self._get_account_id()}
                ],
                StartTime=datetime.now(timezone.utc) - timedelta(hours=1),
                EndTime=datetime.now(timezone.utc),
                Period=3600,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                return datapoints[-1].get('Average')
            return None
            
        except Exception as e:
            logger.debug(f"Could not get metric {metric_name}: {e}")
            return None
    
    def _get_account_id(self) -> str:
        """Obtém Account ID"""
        try:
            from ..core.factories import AWSServiceType
            sts = self.client_factory.get_client(AWSServiceType.STS)
            return sts.get_caller_identity()['Account']
        except Exception:
            return '000000000000'
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para OpenSearch"""
        recommendations = []
        domains = self.get_domains()
        
        for domain in domains:
            if not domain.has_encryption_at_rest:
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='SECURITY',
                    title='Habilitar criptografia at-rest',
                    description=f'Domínio {domain.domain_name} não possui criptografia at-rest. '
                               f'Habilite para proteção de dados.',
                    action='Habilitar encryption at rest (requer novo domínio)',
                    estimated_savings=0.0,
                    priority='HIGH',
                    metadata={'domain_name': domain.domain_name}
                ))
            
            if not domain.has_node_to_node_encryption:
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='SECURITY',
                    title='Habilitar criptografia node-to-node',
                    description=f'Domínio {domain.domain_name} não possui criptografia entre nós. '
                               f'Habilite para comunicação segura.',
                    action='Habilitar node-to-node encryption',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    metadata={'domain_name': domain.domain_name}
                ))
            
            if not domain.is_vpc:
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='SECURITY',
                    title='Migrar para VPC',
                    description=f'Domínio {domain.domain_name} usa endpoint público. '
                               f'Configure em VPC para maior segurança.',
                    action='Criar novo domínio em VPC e migrar dados',
                    estimated_savings=0.0,
                    priority='HIGH',
                    metadata={'domain_name': domain.domain_name}
                ))
            
            if not domain.is_auto_tune_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='COST_OPTIMIZATION',
                    title='Habilitar Auto-Tune',
                    description=f'Domínio {domain.domain_name} não tem Auto-Tune. '
                               f'Habilite para otimização automática de performance.',
                    action='Habilitar Auto-Tune',
                    estimated_savings=0.0,
                    priority='LOW',
                    metadata={'domain_name': domain.domain_name}
                ))
            
            if domain.ebs_enabled and domain.volume_type == 'gp2':
                storage_savings = domain.total_storage_gb * 0.02 * 12
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='COST_OPTIMIZATION',
                    title='Migrar EBS de gp2 para gp3',
                    description=f'Domínio {domain.domain_name} usa volumes gp2. '
                               f'Migre para gp3 para melhor custo-benefício.',
                    action='Alterar volume type para gp3',
                    estimated_savings=storage_savings,
                    priority='MEDIUM',
                    metadata={
                        'domain_name': domain.domain_name,
                        'current_type': 'gp2',
                        'storage_gb': domain.total_storage_gb
                    }
                ))
            
            if not domain.zone_awareness_enabled and domain.instance_count >= 2:
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='OPERATIONAL',
                    title='Habilitar Zone Awareness',
                    description=f'Domínio {domain.domain_name} tem múltiplas instâncias sem HA. '
                               f'Habilite zone awareness para alta disponibilidade.',
                    action='Habilitar zone awareness com 2+ AZs',
                    estimated_savings=0.0,
                    priority='HIGH',
                    metadata={'domain_name': domain.domain_name}
                ))
            
            if not domain.dedicated_master_enabled and domain.instance_count >= 3:
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='OPERATIONAL',
                    title='Adicionar dedicated master nodes',
                    description=f'Domínio {domain.domain_name} tem {domain.instance_count} nós sem masters dedicados. '
                               f'Adicione para estabilidade.',
                    action='Configurar 3 dedicated master nodes',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    metadata={'domain_name': domain.domain_name}
                ))
            
            if not domain.warm_enabled and domain.total_storage_gb > 500:
                warm_savings = domain.total_storage_gb * 0.05
                recommendations.append(ServiceRecommendation(
                    resource_id=domain.arn,
                    resource_type='OpenSearch Domain',
                    recommendation_type='COST_OPTIMIZATION',
                    title='Considerar UltraWarm para dados históricos',
                    description=f'Domínio {domain.domain_name} tem {domain.total_storage_gb}GB. '
                               f'Use UltraWarm para dados menos acessados.',
                    action='Habilitar UltraWarm e migrar índices antigos',
                    estimated_savings=warm_savings,
                    priority='MEDIUM',
                    metadata={
                        'domain_name': domain.domain_name,
                        'current_storage_gb': domain.total_storage_gb
                    }
                ))
        
        logger.info(f"Generated {len(recommendations)} OpenSearch recommendations")
        return recommendations
