"""
EKS FinOps Service - Análise de Custos do Amazon Elastic Kubernetes Service

FASE 2.4 - Serviços Não-Serverless de Alto Custo
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters EKS
- Análise de node groups e Fargate profiles
- Métricas de utilização de recursos
- Recomendações de otimização de custos
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EKSNodeGroup:
    """Representa um Node Group do EKS"""
    nodegroup_name: str
    nodegroup_arn: str
    cluster_name: str
    status: str
    capacity_type: str = "ON_DEMAND"
    scaling_config: Dict[str, int] = field(default_factory=dict)
    instance_types: List[str] = field(default_factory=list)
    subnets: List[str] = field(default_factory=list)
    ami_type: str = "AL2_x86_64"
    disk_size: int = 20
    labels: Dict[str, str] = field(default_factory=dict)
    taints: List[Dict[str, str]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    launch_template: Optional[Dict[str, str]] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    health: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def min_size(self) -> int:
        return self.scaling_config.get('minSize', 0)
    
    @property
    def max_size(self) -> int:
        return self.scaling_config.get('maxSize', 0)
    
    @property
    def desired_size(self) -> int:
        return self.scaling_config.get('desiredSize', 0)
    
    @property
    def is_spot(self) -> bool:
        return self.capacity_type == "SPOT"
    
    @property
    def is_on_demand(self) -> bool:
        return self.capacity_type == "ON_DEMAND"
    
    @property
    def primary_instance_type(self) -> str:
        return self.instance_types[0] if self.instance_types else "unknown"
    
    @property
    def is_healthy(self) -> bool:
        issues = self.health.get('issues', [])
        return len(issues) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodegroup_name': self.nodegroup_name,
            'nodegroup_arn': self.nodegroup_arn,
            'cluster_name': self.cluster_name,
            'status': self.status,
            'capacity_type': self.capacity_type,
            'instance_types': self.instance_types,
            'ami_type': self.ami_type,
            'disk_size': self.disk_size,
            'min_size': self.min_size,
            'max_size': self.max_size,
            'desired_size': self.desired_size,
            'is_spot': self.is_spot,
            'is_healthy': self.is_healthy,
            'labels': self.labels,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class EKSFargateProfile:
    """Representa um Fargate Profile do EKS"""
    fargate_profile_name: str
    fargate_profile_arn: str
    cluster_name: str
    status: str
    pod_execution_role_arn: str
    subnets: List[str] = field(default_factory=list)
    selectors: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    @property
    def namespace_count(self) -> int:
        namespaces = set()
        for selector in self.selectors:
            if 'namespace' in selector:
                namespaces.add(selector['namespace'])
        return len(namespaces)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fargate_profile_name': self.fargate_profile_name,
            'fargate_profile_arn': self.fargate_profile_arn,
            'cluster_name': self.cluster_name,
            'status': self.status,
            'pod_execution_role_arn': self.pod_execution_role_arn,
            'subnets': self.subnets,
            'selectors': self.selectors,
            'namespace_count': self.namespace_count,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class EKSAddon:
    """Representa um Add-on do EKS"""
    addon_name: str
    addon_version: str
    cluster_name: str
    status: str
    service_account_role_arn: Optional[str] = None
    health: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_healthy(self) -> bool:
        return self.status == "ACTIVE"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'addon_name': self.addon_name,
            'addon_version': self.addon_version,
            'cluster_name': self.cluster_name,
            'status': self.status,
            'service_account_role_arn': self.service_account_role_arn,
            'is_healthy': self.is_healthy,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class EKSCluster:
    """Representa um cluster EKS"""
    name: str
    arn: str
    status: str
    version: str
    endpoint: Optional[str] = None
    role_arn: Optional[str] = None
    resources_vpc_config: Dict[str, Any] = field(default_factory=dict)
    kubernetes_network_config: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    identity: Dict[str, Any] = field(default_factory=dict)
    certificate_authority: Dict[str, str] = field(default_factory=dict)
    platform_version: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    encryption_config: List[Dict[str, Any]] = field(default_factory=list)
    connector_config: Optional[Dict[str, Any]] = None
    health: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    node_groups: List[EKSNodeGroup] = field(default_factory=list)
    fargate_profiles: List[EKSFargateProfile] = field(default_factory=list)
    addons: List[EKSAddon] = field(default_factory=list)
    
    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"
    
    @property
    def is_public(self) -> bool:
        return self.resources_vpc_config.get('endpointPublicAccess', False)
    
    @property
    def is_private(self) -> bool:
        return self.resources_vpc_config.get('endpointPrivateAccess', False)
    
    @property
    def vpc_id(self) -> Optional[str]:
        return self.resources_vpc_config.get('vpcId')
    
    @property
    def subnet_ids(self) -> List[str]:
        return self.resources_vpc_config.get('subnetIds', [])
    
    @property
    def security_group_ids(self) -> List[str]:
        return self.resources_vpc_config.get('securityGroupIds', [])
    
    @property
    def has_encryption(self) -> bool:
        return len(self.encryption_config) > 0
    
    @property
    def has_logging_enabled(self) -> bool:
        cluster_logging = self.logging.get('clusterLogging', [])
        for log_config in cluster_logging:
            if log_config.get('enabled', False):
                return True
        return False
    
    @property
    def enabled_log_types(self) -> List[str]:
        enabled = []
        cluster_logging = self.logging.get('clusterLogging', [])
        for log_config in cluster_logging:
            if log_config.get('enabled', False):
                enabled.extend(log_config.get('types', []))
        return enabled
    
    @property
    def total_node_count(self) -> int:
        return sum(ng.desired_size for ng in self.node_groups)
    
    @property
    def has_fargate(self) -> bool:
        return len(self.fargate_profiles) > 0
    
    @property
    def uses_spot_instances(self) -> bool:
        return any(ng.is_spot for ng in self.node_groups)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'status': self.status,
            'version': self.version,
            'endpoint': self.endpoint,
            'platform_version': self.platform_version,
            'vpc_id': self.vpc_id,
            'is_public': self.is_public,
            'is_private': self.is_private,
            'has_encryption': self.has_encryption,
            'has_logging_enabled': self.has_logging_enabled,
            'enabled_log_types': self.enabled_log_types,
            'total_node_count': self.total_node_count,
            'node_groups_count': len(self.node_groups),
            'fargate_profiles_count': len(self.fargate_profiles),
            'addons_count': len(self.addons),
            'has_fargate': self.has_fargate,
            'uses_spot_instances': self.uses_spot_instances,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'node_groups': [ng.to_dict() for ng in self.node_groups],
            'fargate_profiles': [fp.to_dict() for fp in self.fargate_profiles],
            'addons': [addon.to_dict() for addon in self.addons]
        }


class EKSService(BaseAWSService):
    """
    Serviço FinOps para Amazon Elastic Kubernetes Service (EKS)
    
    Analisa clusters EKS, node groups, Fargate profiles e fornece
    recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._eks_client = None
        self._cloudwatch_client = None
    
    @property
    def eks_client(self):
        if self._eks_client is None:
            from ..core.factories import AWSServiceType
            self._eks_client = self.client_factory.get_client(AWSServiceType.EKS)
        return self._eks_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            from ..core.factories import AWSServiceType
            self._cloudwatch_client = self.client_factory.get_client(AWSServiceType.CLOUDWATCH)
        return self._cloudwatch_client
    
    def get_service_name(self) -> str:
        return "EKS"
    
    def health_check(self) -> bool:
        try:
            self.eks_client.list_clusters(maxResults=1)
            return True
        except Exception as e:
            logger.error(f"EKS health check failed: {e}")
            return False
    
    def get_clusters(self) -> List[EKSCluster]:
        """Lista todos os clusters EKS com detalhes completos"""
        clusters = []
        
        try:
            paginator = self.eks_client.get_paginator('list_clusters')
            
            for page in paginator.paginate():
                for cluster_name in page.get('clusters', []):
                    try:
                        cluster = self._get_cluster_details(cluster_name)
                        if cluster:
                            clusters.append(cluster)
                    except Exception as e:
                        logger.warning(f"Error getting cluster {cluster_name}: {e}")
            
            logger.info(f"Found {len(clusters)} EKS clusters")
            
        except Exception as e:
            logger.error(f"Error listing EKS clusters: {e}")
        
        return clusters
    
    def _get_cluster_details(self, cluster_name: str) -> Optional[EKSCluster]:
        """Obtém detalhes completos de um cluster"""
        try:
            response = self.eks_client.describe_cluster(name=cluster_name)
            cluster_data = response.get('cluster', {})
            
            cluster = EKSCluster(
                name=cluster_data.get('name', ''),
                arn=cluster_data.get('arn', ''),
                status=cluster_data.get('status', ''),
                version=cluster_data.get('version', ''),
                endpoint=cluster_data.get('endpoint'),
                role_arn=cluster_data.get('roleArn'),
                resources_vpc_config=cluster_data.get('resourcesVpcConfig', {}),
                kubernetes_network_config=cluster_data.get('kubernetesNetworkConfig', {}),
                logging=cluster_data.get('logging', {}),
                identity=cluster_data.get('identity', {}),
                certificate_authority=cluster_data.get('certificateAuthority', {}),
                platform_version=cluster_data.get('platformVersion'),
                tags=cluster_data.get('tags', {}),
                encryption_config=cluster_data.get('encryptionConfig', []),
                health=cluster_data.get('health', {}),
                created_at=cluster_data.get('createdAt')
            )
            
            cluster.node_groups = self._get_node_groups(cluster_name)
            cluster.fargate_profiles = self._get_fargate_profiles(cluster_name)
            cluster.addons = self._get_addons(cluster_name)
            
            return cluster
            
        except Exception as e:
            logger.error(f"Error describing cluster {cluster_name}: {e}")
            return None
    
    def _get_node_groups(self, cluster_name: str) -> List[EKSNodeGroup]:
        """Lista node groups de um cluster"""
        node_groups = []
        
        try:
            paginator = self.eks_client.get_paginator('list_nodegroups')
            
            for page in paginator.paginate(clusterName=cluster_name):
                for ng_name in page.get('nodegroups', []):
                    try:
                        response = self.eks_client.describe_nodegroup(
                            clusterName=cluster_name,
                            nodegroupName=ng_name
                        )
                        ng_data = response.get('nodegroup', {})
                        
                        node_group = EKSNodeGroup(
                            nodegroup_name=ng_data.get('nodegroupName', ''),
                            nodegroup_arn=ng_data.get('nodegroupArn', ''),
                            cluster_name=ng_data.get('clusterName', ''),
                            status=ng_data.get('status', ''),
                            capacity_type=ng_data.get('capacityType', 'ON_DEMAND'),
                            scaling_config=ng_data.get('scalingConfig', {}),
                            instance_types=ng_data.get('instanceTypes', []),
                            subnets=ng_data.get('subnets', []),
                            ami_type=ng_data.get('amiType', 'AL2_x86_64'),
                            disk_size=ng_data.get('diskSize', 20),
                            labels=ng_data.get('labels', {}),
                            taints=ng_data.get('taints', []),
                            tags=ng_data.get('tags', {}),
                            launch_template=ng_data.get('launchTemplate'),
                            created_at=ng_data.get('createdAt'),
                            modified_at=ng_data.get('modifiedAt'),
                            health=ng_data.get('health', {})
                        )
                        node_groups.append(node_group)
                        
                    except Exception as e:
                        logger.warning(f"Error getting node group {ng_name}: {e}")
            
        except Exception as e:
            logger.warning(f"Error listing node groups for {cluster_name}: {e}")
        
        return node_groups
    
    def _get_fargate_profiles(self, cluster_name: str) -> List[EKSFargateProfile]:
        """Lista Fargate profiles de um cluster"""
        profiles = []
        
        try:
            paginator = self.eks_client.get_paginator('list_fargate_profiles')
            
            for page in paginator.paginate(clusterName=cluster_name):
                for profile_name in page.get('fargateProfileNames', []):
                    try:
                        response = self.eks_client.describe_fargate_profile(
                            clusterName=cluster_name,
                            fargateProfileName=profile_name
                        )
                        fp_data = response.get('fargateProfile', {})
                        
                        profile = EKSFargateProfile(
                            fargate_profile_name=fp_data.get('fargateProfileName', ''),
                            fargate_profile_arn=fp_data.get('fargateProfileArn', ''),
                            cluster_name=fp_data.get('clusterName', ''),
                            status=fp_data.get('status', ''),
                            pod_execution_role_arn=fp_data.get('podExecutionRoleArn', ''),
                            subnets=fp_data.get('subnets', []),
                            selectors=fp_data.get('selectors', []),
                            tags=fp_data.get('tags', {}),
                            created_at=fp_data.get('createdAt')
                        )
                        profiles.append(profile)
                        
                    except Exception as e:
                        logger.warning(f"Error getting Fargate profile {profile_name}: {e}")
            
        except Exception as e:
            logger.warning(f"Error listing Fargate profiles for {cluster_name}: {e}")
        
        return profiles
    
    def _get_addons(self, cluster_name: str) -> List[EKSAddon]:
        """Lista add-ons de um cluster"""
        addons = []
        
        try:
            paginator = self.eks_client.get_paginator('list_addons')
            
            for page in paginator.paginate(clusterName=cluster_name):
                for addon_name in page.get('addons', []):
                    try:
                        response = self.eks_client.describe_addon(
                            clusterName=cluster_name,
                            addonName=addon_name
                        )
                        addon_data = response.get('addon', {})
                        
                        addon = EKSAddon(
                            addon_name=addon_data.get('addonName', ''),
                            addon_version=addon_data.get('addonVersion', ''),
                            cluster_name=addon_data.get('clusterName', ''),
                            status=addon_data.get('status', ''),
                            service_account_role_arn=addon_data.get('serviceAccountRoleArn'),
                            health=addon_data.get('health', {}),
                            created_at=addon_data.get('createdAt'),
                            modified_at=addon_data.get('modifiedAt'),
                            tags=addon_data.get('tags', {})
                        )
                        addons.append(addon)
                        
                    except Exception as e:
                        logger.warning(f"Error getting addon {addon_name}: {e}")
            
        except Exception as e:
            logger.warning(f"Error listing addons for {cluster_name}: {e}")
        
        return addons
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Retorna todos os recursos EKS"""
        clusters = self.get_clusters()
        
        resources = []
        for cluster in clusters:
            resources.append({
                'resource_id': cluster.arn,
                'resource_type': 'EKS Cluster',
                'name': cluster.name,
                'status': cluster.status,
                'node_groups': len(cluster.node_groups),
                'fargate_profiles': len(cluster.fargate_profiles),
                'total_nodes': cluster.total_node_count,
                'has_encryption': cluster.has_encryption,
                'uses_spot': cluster.uses_spot_instances
            })
        return resources
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """Retorna estimativas de custo para clusters EKS"""
        clusters = self.get_clusters()
        total_cost = 0.0
        cost_by_resource = {}
        
        for cluster in clusters:
            cluster_cost = 0.10 * 24 * period_days
            
            for ng in cluster.node_groups:
                node_count = ng.desired_size
                hourly_rate = self._estimate_instance_hourly_rate(ng.primary_instance_type)
                if ng.is_spot:
                    hourly_rate *= 0.3
                node_cost = hourly_rate * 24 * period_days * node_count
                cluster_cost += node_cost
            
            total_cost += cluster_cost
            cost_by_resource[cluster.name] = cluster_cost
        
        return ServiceCost(
            service_name='EKS',
            total_cost=total_cost,
            period_days=period_days,
            cost_by_resource=cost_by_resource,
            currency='USD'
        )
    
    def _estimate_instance_hourly_rate(self, instance_type: str) -> float:
        """Estima custo por hora de um tipo de instância"""
        rates = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            't3.xlarge': 0.1664,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'm5.4xlarge': 0.768,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
            'c5.2xlarge': 0.34,
            'r5.large': 0.126,
            'r5.xlarge': 0.252,
            'r5.2xlarge': 0.504,
        }
        return rates.get(instance_type, 0.10)
    
    def get_metrics(self) -> ServiceMetrics:
        """Retorna métricas dos clusters EKS"""
        clusters = self.get_clusters()
        
        total_nodes = sum(c.total_node_count for c in clusters)
        active_clusters = len([c for c in clusters if c.is_active])
        
        metrics_data = {
            'total_clusters': len(clusters),
            'active_clusters': active_clusters,
            'total_nodes': total_nodes,
            'total_node_groups': sum(len(c.node_groups) for c in clusters),
            'total_fargate_profiles': sum(len(c.fargate_profiles) for c in clusters),
            'clusters_with_encryption': len([c for c in clusters if c.has_encryption]),
            'clusters_using_spot': len([c for c in clusters if c.uses_spot_instances])
        }
        
        utilization = (active_clusters / len(clusters) * 100) if clusters else 0.0
        
        return ServiceMetrics(
            service_name='EKS',
            resource_count=len(clusters),
            metrics=metrics_data,
            utilization=utilization
        )
    
    def _get_cluster_metric(self, cluster_name: str, metric_name: str) -> Optional[float]:
        """Obtém uma métrica específica do cluster"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EKS',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'ClusterName', 'Value': cluster_name}
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
            logger.debug(f"Could not get metric {metric_name} for {cluster_name}: {e}")
            return None
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para EKS"""
        recommendations = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            if not cluster.has_encryption:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.arn,
                    resource_type='EKS Cluster',
                    recommendation_type='SECURITY',
                    title='Habilitar criptografia de secrets',
                    description=f'Cluster {cluster.name} não possui criptografia de secrets habilitada. '
                               f'Considere habilitar encryption at rest usando KMS.',
                    action='Habilitar encryption config com KMS key',
                    estimated_savings=0.0,
                    priority='HIGH',
                    details={'cluster_name': cluster.name}
                ))
            
            if cluster.is_public and not cluster.is_private:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.arn,
                    resource_type='EKS Cluster',
                    recommendation_type='SECURITY',
                    title='Restringir acesso público ao endpoint',
                    description=f'Cluster {cluster.name} tem endpoint público habilitado sem acesso privado. '
                               f'Considere habilitar acesso privado e restringir público.',
                    action='Habilitar private endpoint access',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    details={'cluster_name': cluster.name}
                ))
            
            if not cluster.has_logging_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.arn,
                    resource_type='EKS Cluster',
                    recommendation_type='OPERATIONAL',
                    title='Habilitar logging do control plane',
                    description=f'Cluster {cluster.name} não possui logging habilitado. '
                               f'Habilite logs para auditoria e troubleshooting.',
                    action='Habilitar api, audit, authenticator, controllerManager, scheduler logs',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    details={'cluster_name': cluster.name}
                ))
            
            for ng in cluster.node_groups:
                if ng.is_on_demand and ng.desired_size >= 3:
                    estimated_savings = self._calculate_spot_savings(ng)
                    recommendations.append(ServiceRecommendation(
                        resource_id=ng.nodegroup_arn,
                        resource_type='EKS Node Group',
                        recommendation_type='COST_OPTIMIZATION',
                        title='Considerar uso de Spot Instances',
                        description=f'Node group {ng.nodegroup_name} usa apenas instâncias On-Demand. '
                                   f'Considere usar Spot Instances para workloads tolerantes a interrupções.',
                        action='Migrar para capacity type SPOT ou criar node group misto',
                        estimated_savings=estimated_savings,
                        priority='MEDIUM',
                        details={
                            'cluster_name': cluster.name,
                            'node_group': ng.nodegroup_name,
                            'instance_types': ng.instance_types,
                            'current_nodes': ng.desired_size
                        }
                    ))
                
                if ng.max_size == ng.min_size and ng.max_size > 1:
                    recommendations.append(ServiceRecommendation(
                        resource_id=ng.nodegroup_arn,
                        resource_type='EKS Node Group',
                        recommendation_type='COST_OPTIMIZATION',
                        title='Habilitar auto-scaling',
                        description=f'Node group {ng.nodegroup_name} tem min/max size iguais ({ng.max_size}). '
                                   f'Configure Cluster Autoscaler para escalar automaticamente.',
                        action='Configurar diferentes valores para min/max size',
                        estimated_savings=0.0,
                        priority='LOW',
                        details={
                            'cluster_name': cluster.name,
                            'node_group': ng.nodegroup_name
                        }
                    ))
                
                if not ng.is_healthy:
                    recommendations.append(ServiceRecommendation(
                        resource_id=ng.nodegroup_arn,
                        resource_type='EKS Node Group',
                        recommendation_type='OPERATIONAL',
                        title='Node group com problemas de saúde',
                        description=f'Node group {ng.nodegroup_name} possui issues reportados. '
                                   f'Verifique o status e resolva os problemas.',
                        action='Investigar health issues do node group',
                        estimated_savings=0.0,
                        priority='HIGH',
                        details={
                            'cluster_name': cluster.name,
                            'node_group': ng.nodegroup_name,
                            'health': ng.health
                        }
                    ))
            
            if not cluster.has_fargate and len(cluster.node_groups) > 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.arn,
                    resource_type='EKS Cluster',
                    recommendation_type='COST_OPTIMIZATION',
                    title='Considerar Fargate para workloads específicos',
                    description=f'Cluster {cluster.name} usa apenas node groups. '
                               f'Fargate pode ser mais econômico para workloads esporádicos ou batch.',
                    action='Avaliar migração de workloads adequados para Fargate',
                    estimated_savings=0.0,
                    priority='LOW',
                    details={'cluster_name': cluster.name}
                ))
        
        logger.info(f"Generated {len(recommendations)} EKS recommendations")
        return recommendations
    
    def _calculate_spot_savings(self, node_group: EKSNodeGroup) -> float:
        """Calcula economia estimada ao usar Spot Instances"""
        hourly_rate = self._estimate_instance_hourly_rate(node_group.primary_instance_type)
        on_demand_cost = hourly_rate * 24 * 30 * node_group.desired_size
        spot_cost = on_demand_cost * 0.3
        return on_demand_cost - spot_cost
