"""
EMR FinOps Service - Análise de Custos de Big Data

FASE 2 - Prioridade 1: Analytics (alto custo)
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters EMR (Provisioned e Serverless)
- Análise de utilização de instâncias
- Recomendações de Spot, Savings Plans
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class EMRCluster:
    """Representa um cluster EMR"""
    cluster_id: str
    name: str
    status: str
    state_change_reason: str = ""
    normalized_instance_hours: int = 0
    master_public_dns: Optional[str] = None
    release_label: str = ""
    applications: List[str] = field(default_factory=list)
    instance_collection_type: str = "INSTANCE_GROUP"
    log_uri: Optional[str] = None
    auto_terminate: bool = False
    termination_protected: bool = False
    visible_to_all_users: bool = True
    created_time: Optional[datetime] = None
    ready_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cluster_id': self.cluster_id,
            'name': self.name,
            'status': self.status,
            'normalized_instance_hours': self.normalized_instance_hours,
            'release_label': self.release_label,
            'applications': self.applications,
            'instance_collection_type': self.instance_collection_type,
            'auto_terminate': self.auto_terminate,
            'termination_protected': self.termination_protected,
            'created_time': self.created_time.isoformat() if self.created_time else None
        }


@dataclass
class EMRInstanceGroup:
    """Representa um grupo de instâncias EMR"""
    instance_group_id: str
    name: str
    instance_type: str
    instance_group_type: str  # MASTER, CORE, TASK
    requested_instance_count: int
    running_instance_count: int
    status: str
    market: str  # ON_DEMAND, SPOT
    bid_price: Optional[str] = None
    ebs_volumes: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'instance_group_id': self.instance_group_id,
            'name': self.name,
            'instance_type': self.instance_type,
            'instance_group_type': self.instance_group_type,
            'requested_instance_count': self.requested_instance_count,
            'running_instance_count': self.running_instance_count,
            'market': self.market,
            'status': self.status
        }


@dataclass
class EMRServerlessApplication:
    """Representa uma aplicação EMR Serverless"""
    application_id: str
    name: str
    arn: str
    state: str
    type: str  # SPARK, HIVE
    release_label: str
    auto_start_enabled: bool = True
    auto_stop_enabled: bool = True
    idle_timeout_minutes: int = 15
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'application_id': self.application_id,
            'name': self.name,
            'state': self.state,
            'type': self.type,
            'release_label': self.release_label,
            'auto_start_enabled': self.auto_start_enabled,
            'auto_stop_enabled': self.auto_stop_enabled,
            'idle_timeout_minutes': self.idle_timeout_minutes
        }


class EMRService(BaseAWSService):
    """
    Serviço FinOps para análise de custos EMR
    
    Analisa clusters EMR, EMR Serverless e fornece
    recomendações de otimização de custos.
    """
    
    def __init__(
        self,
        emr_client=None,
        emr_serverless_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._emr_client = emr_client
        self._emr_serverless_client = emr_serverless_client
    
    @property
    def emr_client(self):
        if self._emr_client is None:
            import boto3
            self._emr_client = boto3.client('emr')
        return self._emr_client
    
    @property
    def emr_serverless_client(self):
        if self._emr_serverless_client is None:
            import boto3
            self._emr_serverless_client = boto3.client('emr-serverless')
        return self._emr_serverless_client
    
    def get_service_name(self) -> str:
        return "Amazon EMR"
    
    def health_check(self) -> bool:
        try:
            self.emr_client.list_clusters(ClusterStates=['RUNNING', 'WAITING'])
            return True
        except Exception:
            return False
    
    
    def get_clusters(self, states: List[str] = None) -> List[EMRCluster]:
        """Lista clusters EMR"""
        clusters = []
        
        if states is None:
            states = ['RUNNING', 'WAITING', 'STARTING', 'BOOTSTRAPPING']
        
        paginator = self.emr_client.get_paginator('list_clusters')
        
        for page in paginator.paginate(ClusterStates=states):
            for cluster_summary in page.get('Clusters', []):
                cluster_id = cluster_summary['Id']
                
                try:
                    detail = self.emr_client.describe_cluster(ClusterId=cluster_id)
                    cluster_info = detail['Cluster']
                    
                    apps = [app['Name'] for app in cluster_info.get('Applications', [])]
                    
                    cluster = EMRCluster(
                        cluster_id=cluster_id,
                        name=cluster_info['Name'],
                        status=cluster_info['Status']['State'],
                        state_change_reason=cluster_info['Status'].get('StateChangeReason', {}).get('Message', ''),
                        normalized_instance_hours=cluster_info.get('NormalizedInstanceHours', 0),
                        master_public_dns=cluster_info.get('MasterPublicDnsName'),
                        release_label=cluster_info.get('ReleaseLabel', ''),
                        applications=apps,
                        instance_collection_type=cluster_info.get('InstanceCollectionType', 'INSTANCE_GROUP'),
                        log_uri=cluster_info.get('LogUri'),
                        auto_terminate=cluster_info.get('AutoTerminate', False),
                        termination_protected=cluster_info.get('TerminationProtected', False),
                        visible_to_all_users=cluster_info.get('VisibleToAllUsers', True),
                        created_time=cluster_summary.get('Status', {}).get('Timeline', {}).get('CreationDateTime'),
                        ready_time=cluster_summary.get('Status', {}).get('Timeline', {}).get('ReadyDateTime'),
                        end_time=cluster_summary.get('Status', {}).get('Timeline', {}).get('EndDateTime')
                    )
                    clusters.append(cluster)
                except Exception:
                    pass
        
        return clusters
    
    
    def get_cluster_instance_groups(self, cluster_id: str) -> List[EMRInstanceGroup]:
        """Lista grupos de instâncias de um cluster"""
        groups = []
        
        response = self.emr_client.list_instance_groups(ClusterId=cluster_id)
        
        for ig in response.get('InstanceGroups', []):
            group = EMRInstanceGroup(
                instance_group_id=ig['Id'],
                name=ig.get('Name', ''),
                instance_type=ig['InstanceType'],
                instance_group_type=ig['InstanceGroupType'],
                requested_instance_count=ig.get('RequestedInstanceCount', 0),
                running_instance_count=ig.get('RunningInstanceCount', 0),
                status=ig['Status']['State'],
                market=ig.get('Market', 'ON_DEMAND'),
                bid_price=ig.get('BidPrice'),
                ebs_volumes=ig.get('EbsBlockDevices', [])
            )
            groups.append(group)
        
        return groups
    
    
    def get_serverless_applications(self) -> List[EMRServerlessApplication]:
        """Lista aplicações EMR Serverless"""
        applications = []
        
        try:
            paginator = self.emr_serverless_client.get_paginator('list_applications')
            
            for page in paginator.paginate():
                for app in page.get('applications', []):
                    application = EMRServerlessApplication(
                        application_id=app['id'],
                        name=app['name'],
                        arn=app['arn'],
                        state=app['state'],
                        type=app['type'],
                        release_label=app.get('releaseLabel', ''),
                        auto_start_enabled=app.get('autoStartConfiguration', {}).get('enabled', True),
                        auto_stop_enabled=app.get('autoStopConfiguration', {}).get('enabled', True),
                        idle_timeout_minutes=app.get('autoStopConfiguration', {}).get('idleTimeoutMinutes', 15),
                        created_at=app.get('createdAt'),
                        updated_at=app.get('updatedAt')
                    )
                    applications.append(application)
        except Exception:
            pass
        
        return applications
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        clusters = self.get_clusters()
        for cluster in clusters:
            res = cluster.to_dict()
            res['resource_type'] = 'cluster'
            resources.append(res)
        
        serverless = self.get_serverless_applications()
        for app in serverless:
            res = app.to_dict()
            res['resource_type'] = 'serverless'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de EMR"""
        clusters = self.get_clusters()
        serverless = self.get_serverless_applications()
        
        total_instance_hours = sum(c.normalized_instance_hours for c in clusters)
        
        applications_used = {}
        for cluster in clusters:
            for app in cluster.applications:
                applications_used[app] = applications_used.get(app, 0) + 1
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(clusters) + len(serverless),
            metrics={
                'active_clusters': len(clusters),
                'serverless_applications': len(serverless),
                'total_normalized_instance_hours': total_instance_hours,
                'applications_used': applications_used,
                'auto_terminate_enabled': len([c for c in clusters if c.auto_terminate])
            },
            period_days=7,
            collected_at=datetime.utcnow()
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para EMR"""
        recommendations = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            if not cluster.auto_terminate:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_id,
                    resource_type='EMR Cluster',
                    recommendation_type='AUTO_TERMINATE',
                    title='Auto-terminate não habilitado',
                    description=f'Cluster {cluster.name} ({cluster.cluster_id}) não tem auto-terminate. '
                               f'Considere habilitar para evitar custos de clusters ociosos.',
                    estimated_savings=100.0,
                    priority='HIGH',
                    action='Habilitar auto-terminate'
                ))
            
            try:
                instance_groups = self.get_cluster_instance_groups(cluster.cluster_id)
                
                on_demand_task = [g for g in instance_groups 
                                 if g.instance_group_type == 'TASK' and g.market == 'ON_DEMAND']
                
                for group in on_demand_task:
                    if group.running_instance_count > 0:
                        recommendations.append(ServiceRecommendation(
                            resource_id=f'{cluster.cluster_id}/{group.instance_group_id}',
                            resource_type='EMR Instance Group',
                            recommendation_type='SPOT_OPPORTUNITY',
                            title=f'Task nodes On-Demand detectados',
                            description=f'Cluster {cluster.name} tem {group.running_instance_count} task nodes On-Demand. '
                                       f'Task nodes são ideais para Spot Instances (economia até 90%).',
                            estimated_savings=group.running_instance_count * 50,
                            priority='HIGH',
                            action='Migrar task nodes para Spot'
                        ))
                
                old_instance_types = ['m4.', 'm3.', 'c4.', 'c3.', 'r4.', 'r3.']
                for group in instance_groups:
                    for old_type in old_instance_types:
                        if group.instance_type.startswith(old_type):
                            recommendations.append(ServiceRecommendation(
                                resource_id=f'{cluster.cluster_id}/{group.instance_group_id}',
                                resource_type='EMR Instance Group',
                                recommendation_type='MODERNIZE',
                                title=f'Instance type legado: {group.instance_type}',
                                description=f'Grupo {group.name} usa {group.instance_type}. '
                                           f'Considere migrar para tipos mais recentes (m6i, c6i, r6i).',
                                estimated_savings=20.0,
                                priority='MEDIUM',
                                action='Atualizar para instance types modernos'
                            ))
                            break
                
            except Exception:
                pass
            
            if cluster.status == 'WAITING':
                if cluster.created_time:
                    age_hours = (datetime.utcnow() - cluster.created_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours > 24:
                        recommendations.append(ServiceRecommendation(
                            resource_id=cluster.cluster_id,
                            resource_type='EMR Cluster',
                            recommendation_type='IDLE_CLUSTER',
                            title=f'Cluster idle por muito tempo',
                            description=f'Cluster {cluster.name} está em WAITING há {int(age_hours)} horas. '
                                       f'Considere terminar se não for mais necessário.',
                            estimated_savings=age_hours * 5,
                            priority='HIGH',
                            action='Terminar cluster ocioso'
                        ))
        
        return recommendations
