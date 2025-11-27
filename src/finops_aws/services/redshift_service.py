"""
Redshift FinOps Service - Análise de Custos de Data Warehouse

FASE 2 - Prioridade 1: Analytics (alto custo)
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters Redshift (Provisioned e Serverless)
- Análise de utilização e performance
- Recomendações de rightsizing e Reserved Nodes
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class RedshiftCluster:
    """Representa um cluster Redshift Provisioned"""
    cluster_identifier: str
    node_type: str
    number_of_nodes: int
    cluster_status: str
    availability_zone: str
    db_name: str
    master_username: str
    cluster_create_time: Optional[datetime] = None
    encrypted: bool = False
    enhanced_vpc_routing: bool = False
    publicly_accessible: bool = False
    vpc_id: Optional[str] = None
    elastic_ip: Optional[str] = None
    automated_snapshot_retention: int = 1
    manual_snapshot_retention: int = -1
    cluster_version: str = "1.0"
    allow_version_upgrade: bool = True
    maintenance_track: str = "current"
    total_storage_capacity_gb: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cluster_identifier': self.cluster_identifier,
            'node_type': self.node_type,
            'number_of_nodes': self.number_of_nodes,
            'cluster_status': self.cluster_status,
            'availability_zone': self.availability_zone,
            'encrypted': self.encrypted,
            'enhanced_vpc_routing': self.enhanced_vpc_routing,
            'publicly_accessible': self.publicly_accessible,
            'automated_snapshot_retention': self.automated_snapshot_retention,
            'total_storage_capacity_gb': self.total_storage_capacity_gb,
            'cluster_create_time': self.cluster_create_time.isoformat() if self.cluster_create_time else None
        }


@dataclass
class RedshiftServerlessWorkgroup:
    """Representa um workgroup Redshift Serverless"""
    workgroup_name: str
    workgroup_arn: str
    namespace_name: str
    status: str
    base_capacity: int
    enhanced_vpc_routing: bool = False
    publicly_accessible: bool = False
    security_group_ids: List[str] = field(default_factory=list)
    subnet_ids: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    creation_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'workgroup_name': self.workgroup_name,
            'workgroup_arn': self.workgroup_arn,
            'namespace_name': self.namespace_name,
            'status': self.status,
            'base_capacity': self.base_capacity,
            'enhanced_vpc_routing': self.enhanced_vpc_routing,
            'publicly_accessible': self.publicly_accessible,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass  
class RedshiftReservedNode:
    """Representa um Reserved Node Redshift"""
    reserved_node_id: str
    node_type: str
    node_count: int
    state: str
    offering_type: str
    start_time: datetime
    duration: int
    fixed_price: float
    usage_price: float
    recurring_charges: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reserved_node_id': self.reserved_node_id,
            'node_type': self.node_type,
            'node_count': self.node_count,
            'state': self.state,
            'offering_type': self.offering_type,
            'start_time': self.start_time.isoformat(),
            'fixed_price': self.fixed_price
        }


class RedshiftService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Redshift
    
    Analisa clusters Redshift Provisioned e Serverless,
    Reserved Nodes e fornece recomendações de otimização.
    """
    
    def __init__(
        self,
        redshift_client=None,
        redshift_serverless_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._redshift_client = redshift_client
        self._redshift_serverless_client = redshift_serverless_client
    
    @property
    def redshift_client(self):
        if self._redshift_client is None:
            import boto3
            self._redshift_client = boto3.client('redshift')
        return self._redshift_client
    
    @property
    def redshift_serverless_client(self):
        if self._redshift_serverless_client is None:
            import boto3
            self._redshift_serverless_client = boto3.client('redshift-serverless')
        return self._redshift_serverless_client
    
    def get_service_name(self) -> str:
        return "Amazon Redshift"
    
    def health_check(self) -> bool:
        try:
            self.redshift_client.describe_clusters(MaxRecords=20)
            return True
        except Exception:
            return False
    
    
    def get_clusters(self) -> List[RedshiftCluster]:
        """Lista todos os clusters Redshift Provisioned"""
        clusters = []
        
        paginator = self.redshift_client.get_paginator('describe_clusters')
        
        for page in paginator.paginate():
            for cluster in page.get('Clusters', []):
                storage_gb = 0
                if cluster.get('ClusterNodes'):
                    for node in cluster['ClusterNodes']:
                        storage_gb += node.get('NodeSize', 0) or 0
                
                redshift_cluster = RedshiftCluster(
                    cluster_identifier=cluster['ClusterIdentifier'],
                    node_type=cluster['NodeType'],
                    number_of_nodes=cluster['NumberOfNodes'],
                    cluster_status=cluster['ClusterStatus'],
                    availability_zone=cluster['AvailabilityZone'],
                    db_name=cluster['DBName'],
                    master_username=cluster['MasterUsername'],
                    cluster_create_time=cluster.get('ClusterCreateTime'),
                    encrypted=cluster.get('Encrypted', False),
                    enhanced_vpc_routing=cluster.get('EnhancedVpcRouting', False),
                    publicly_accessible=cluster.get('PubliclyAccessible', False),
                    vpc_id=cluster.get('VpcId'),
                    automated_snapshot_retention=cluster.get('AutomatedSnapshotRetentionPeriod', 1),
                    manual_snapshot_retention=cluster.get('ManualSnapshotRetentionPeriod', -1),
                    cluster_version=cluster.get('ClusterVersion', '1.0'),
                    allow_version_upgrade=cluster.get('AllowVersionUpgrade', True),
                    maintenance_track=cluster.get('MaintenanceTrackName', 'current'),
                    total_storage_capacity_gb=storage_gb
                )
                clusters.append(redshift_cluster)
        
        return clusters
    
    
    def get_serverless_workgroups(self) -> List[RedshiftServerlessWorkgroup]:
        """Lista workgroups Redshift Serverless"""
        workgroups = []
        
        try:
            paginator = self.redshift_serverless_client.get_paginator('list_workgroups')
            
            for page in paginator.paginate():
                for wg in page.get('workgroups', []):
                    workgroup = RedshiftServerlessWorkgroup(
                        workgroup_name=wg['workgroupName'],
                        workgroup_arn=wg['workgroupArn'],
                        namespace_name=wg.get('namespaceName', ''),
                        status=wg['status'],
                        base_capacity=wg.get('baseCapacity', 0),
                        enhanced_vpc_routing=wg.get('enhancedVpcRouting', False),
                        publicly_accessible=wg.get('publiclyAccessible', False),
                        security_group_ids=wg.get('securityGroupIds', []),
                        subnet_ids=wg.get('subnetIds', []),
                        endpoint=wg.get('endpoint', {}).get('address'),
                        creation_date=wg.get('creationDate')
                    )
                    workgroups.append(workgroup)
        except Exception:
            pass
        
        return workgroups
    
    
    def get_reserved_nodes(self, state: str = 'active') -> List[RedshiftReservedNode]:
        """Lista Reserved Nodes"""
        reserved = []
        
        response = self.redshift_client.describe_reserved_nodes()
        
        for rn in response.get('ReservedNodes', []):
            if rn['State'].lower() == state:
                reserved_node = RedshiftReservedNode(
                    reserved_node_id=rn['ReservedNodeId'],
                    node_type=rn['NodeType'],
                    node_count=rn['NodeCount'],
                    state=rn['State'],
                    offering_type=rn['OfferingType'],
                    start_time=rn['StartTime'],
                    duration=rn['Duration'],
                    fixed_price=rn['FixedPrice'],
                    usage_price=rn['UsagePrice'],
                    recurring_charges=rn.get('RecurringCharges', [])
                )
                reserved.append(reserved_node)
        
        return reserved
    
    
    def get_cluster_metrics(self, cluster_id: str, days: int = 7) -> Dict[str, Any]:
        """Obtém métricas de um cluster"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        
        cpu = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        if cpu.get('Datapoints'):
            metrics['cpu_avg'] = round(sum(d['Average'] for d in cpu['Datapoints']) / len(cpu['Datapoints']), 2)
            metrics['cpu_max'] = round(max(d['Maximum'] for d in cpu['Datapoints']), 2)
        
        storage = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='PercentageDiskSpaceUsed',
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average']
        )
        if storage.get('Datapoints'):
            metrics['disk_used_pct'] = round(sum(d['Average'] for d in storage['Datapoints']) / len(storage['Datapoints']), 2)
        
        queries = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='DatabaseConnections',
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        if queries.get('Datapoints'):
            metrics['connections_avg'] = round(sum(d['Average'] for d in queries['Datapoints']) / len(queries['Datapoints']), 2)
            metrics['connections_max'] = int(max(d['Maximum'] for d in queries['Datapoints']))
        
        return metrics
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        clusters = self.get_clusters()
        for cluster in clusters:
            res = cluster.to_dict()
            res['type'] = 'provisioned'
            resources.append(res)
        
        workgroups = self.get_serverless_workgroups()
        for wg in workgroups:
            res = wg.to_dict()
            res['type'] = 'serverless'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Redshift"""
        clusters = self.get_clusters()
        workgroups = self.get_serverless_workgroups()
        reserved = self.get_reserved_nodes()
        
        node_types = {}
        total_nodes = 0
        
        for cluster in clusters:
            total_nodes += cluster.number_of_nodes
            node_types[cluster.node_type] = node_types.get(cluster.node_type, 0) + cluster.number_of_nodes
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(clusters) + len(workgroups),
            metrics={
                'provisioned_clusters': len(clusters),
                'serverless_workgroups': len(workgroups),
                'total_nodes': total_nodes,
                'node_types': node_types,
                'reserved_nodes': len(reserved),
                'reserved_node_count': sum(rn.node_count for rn in reserved)
            },
            period_days=7,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Redshift"""
        recommendations = []
        clusters = self.get_clusters()
        reserved = self.get_reserved_nodes()
        workgroups = self.get_serverless_workgroups()
        
        for cluster in clusters:
            try:
                metrics = self.get_cluster_metrics(cluster.cluster_identifier, days=14)
                
                cpu_avg = metrics.get('cpu_avg', 100)
                if cpu_avg < 20:
                    recommendations.append(ServiceRecommendation(
                        resource_id=cluster.cluster_identifier,
                        resource_type='Redshift Cluster',
                        recommendation_type='UNDERUTILIZED',
                        title=f'Cluster subutilizado (CPU média: {cpu_avg}%)',
                        description=f'Cluster {cluster.cluster_identifier} ({cluster.node_type} x{cluster.number_of_nodes}) '
                                   f'tem CPU média de {cpu_avg}%. Considere reduzir nós ou migrar para Serverless.',
                        estimated_savings=cluster.number_of_nodes * 100,
                        priority='HIGH',
                        action='Reduzir número de nós ou migrar para Serverless'
                    ))
                
                disk_pct = metrics.get('disk_used_pct', 0)
                if disk_pct < 30:
                    recommendations.append(ServiceRecommendation(
                        resource_id=cluster.cluster_identifier,
                        resource_type='Redshift Cluster',
                        recommendation_type='STORAGE_OVERSIZED',
                        title=f'Storage subutilizado ({disk_pct}% usado)',
                        description=f'Cluster {cluster.cluster_identifier} usa apenas {disk_pct}% do storage. '
                                   f'Considere usar node type menor ou RA3 com managed storage.',
                        estimated_savings=50.0,
                        priority='MEDIUM',
                        action='Considerar RA3 nodes com managed storage'
                    ))
                
            except Exception:
                pass
            
            if not cluster.encrypted:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_identifier,
                    resource_type='Redshift Cluster',
                    recommendation_type='SECURITY',
                    title='Cluster sem criptografia',
                    description=f'Cluster {cluster.cluster_identifier} não tem criptografia habilitada. '
                               f'Considere habilitar para conformidade e segurança.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Habilitar criptografia KMS'
                ))
            
            if cluster.publicly_accessible:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_identifier,
                    resource_type='Redshift Cluster',
                    recommendation_type='SECURITY',
                    title='Cluster publicamente acessível',
                    description=f'Cluster {cluster.cluster_identifier} é publicamente acessível. '
                               f'Considere restringir acesso via VPC.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Desabilitar acesso público'
                ))
            
            if cluster.node_type.startswith(('dc1.', 'dc2.', 'ds1.', 'ds2.')):
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_identifier,
                    resource_type='Redshift Cluster',
                    recommendation_type='MODERNIZE',
                    title=f'Modernizar node type {cluster.node_type}',
                    description=f'Cluster {cluster.cluster_identifier} usa node type legado. '
                               f'Considere migrar para RA3 para melhor custo-benefício.',
                    estimated_savings=cluster.number_of_nodes * 50,
                    priority='MEDIUM',
                    action='Migrar para RA3 nodes'
                ))
        
        total_on_demand = sum(c.number_of_nodes for c in clusters)
        total_reserved = sum(rn.node_count for rn in reserved)
        
        if total_on_demand > 0 and total_reserved < total_on_demand * 0.5:
            uncovered = total_on_demand - total_reserved
            recommendations.append(ServiceRecommendation(
                resource_id='redshift-fleet',
                resource_type='Redshift Fleet',
                recommendation_type='RESERVED_NODES',
                title=f'Baixa cobertura de Reserved Nodes ({total_reserved}/{total_on_demand})',
                description=f'Apenas {total_reserved} de {total_on_demand} nós têm cobertura de Reserved Nodes. '
                           f'Considere comprar RN para os {uncovered} nós descobertos.',
                estimated_savings=uncovered * 200 * 12,
                priority='HIGH',
                action='Comprar Reserved Nodes'
            ))
        
        if len(clusters) > 0 and len(workgroups) == 0:
            small_clusters = [c for c in clusters if c.number_of_nodes <= 2]
            for cluster in small_clusters:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_identifier,
                    resource_type='Redshift Cluster',
                    recommendation_type='SERVERLESS_CANDIDATE',
                    title='Candidato a Redshift Serverless',
                    description=f'Cluster pequeno {cluster.cluster_identifier} pode se beneficiar '
                               f'de Redshift Serverless para workloads variáveis.',
                    estimated_savings=100.0,
                    priority='MEDIUM',
                    action='Avaliar migração para Serverless'
                ))
        
        return recommendations
