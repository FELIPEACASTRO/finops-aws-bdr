"""
ECS Service - Análise de custos e métricas do Amazon ECS/Fargate

FASE 2 do Roadmap FinOps AWS
Objetivo: Análise completa de Containers

Autor: FinOps AWS Team
Data: Novembro 2025
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from botocore.exceptions import ClientError

from .base_service import (
    BaseAWSService,
    ServiceCost,
    ServiceMetrics,
    ServiceRecommendation
)
from ..utils.logger import setup_logger
from ..utils.aws_helpers import handle_aws_error, get_aws_region

logger = setup_logger(__name__)


@dataclass
class ECSCluster:
    """Representa um cluster ECS"""
    cluster_arn: str
    cluster_name: str
    status: str
    registered_container_instances: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    active_services: int = 0
    capacity_providers: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ECSService:
    """Representa um serviço ECS"""
    service_arn: str
    service_name: str
    cluster_arn: str
    status: str
    desired_count: int = 0
    running_count: int = 0
    pending_count: int = 0
    launch_type: str = "EC2"
    task_definition: str = ""
    deployment_controller: str = "ECS"
    scheduling_strategy: str = "REPLICA"
    cpu: int = 0
    memory: int = 0


@dataclass
class ECSTask:
    """Representa uma task ECS"""
    task_arn: str
    task_definition_arn: str
    cluster_arn: str
    last_status: str
    desired_status: str
    launch_type: str = "EC2"
    cpu: str = "0"
    memory: str = "0"
    started_at: Optional[datetime] = None
    connectivity: str = "CONNECTED"
    health_status: str = "UNKNOWN"


class ECSContainerService(BaseAWSService):
    """
    Serviço para análise completa do Amazon ECS/Fargate
    
    Coleta custos, métricas de uso e recomendações de otimização
    para clusters, serviços e tasks ECS.
    
    Suporta injeção de dependências para Clean Architecture.
    """
    
    SERVICE_NAME = "Amazon ECS"
    SERVICE_FILTER = "Amazon Elastic Container Service"
    
    def __init__(
        self,
        ecs_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o ECSContainerService
        
        Args:
            ecs_client: Cliente ECS injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        super().__init__(cost_client=cost_client, cloudwatch_client=cloudwatch_client)
        self._ecs_client = ecs_client
    
    @property
    def ecs_client(self):
        """Lazy loading do cliente ECS"""
        if self._ecs_client is None:
            self._ecs_client = boto3.client('ecs', region_name=self.region)
        return self._ecs_client
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.ecs_client.list_clusters(maxResults=1)
            return True
        except Exception:
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os clusters e serviços ECS"""
        clusters = self.get_clusters()
        resources = []
        
        for cluster in clusters:
            resources.append({
                'cluster_name': cluster.cluster_name,
                'type': 'cluster',
                'running_tasks': cluster.running_tasks,
                'active_services': cluster.active_services
            })
        
        return resources
    
    def get_clusters(self) -> List[ECSCluster]:
        """
        Obtém lista de todos os clusters ECS
        
        Returns:
            Lista de ECSCluster
        """
        try:
            clusters = []
            
            cluster_arns = []
            paginator = self.ecs_client.get_paginator('list_clusters')
            for page in paginator.paginate():
                cluster_arns.extend(page.get('clusterArns', []))
            
            if not cluster_arns:
                return []
            
            for i in range(0, len(cluster_arns), 100):
                batch = cluster_arns[i:i+100]
                response = self.ecs_client.describe_clusters(
                    clusters=batch,
                    include=['SETTINGS', 'STATISTICS', 'ATTACHMENTS']
                )
                
                for cluster_data in response.get('clusters', []):
                    stats = {s['name']: s['value'] for s in cluster_data.get('statistics', [])}
                    
                    cluster = ECSCluster(
                        cluster_arn=cluster_data['clusterArn'],
                        cluster_name=cluster_data['clusterName'],
                        status=cluster_data['status'],
                        registered_container_instances=cluster_data.get('registeredContainerInstancesCount', 0),
                        running_tasks=int(stats.get('runningTasksCount', cluster_data.get('runningTasksCount', 0))),
                        pending_tasks=int(stats.get('pendingTasksCount', cluster_data.get('pendingTasksCount', 0))),
                        active_services=int(stats.get('activeServicesCount', cluster_data.get('activeServicesCount', 0))),
                        capacity_providers=cluster_data.get('capacityProviders', []),
                        settings={s['name']: s['value'] for s in cluster_data.get('settings', [])}
                    )
                    clusters.append(cluster)
            
            logger.info(f"Found {len(clusters)} ECS clusters")
            return clusters
            
        except ClientError as e:
            handle_aws_error(e, "get_ecs_clusters")
            return []
    
    def get_services(self, cluster_arn: str) -> List[ECSService]:
        """
        Obtém serviços de um cluster específico
        
        Args:
            cluster_arn: ARN do cluster
            
        Returns:
            Lista de ECSService
        """
        try:
            services = []
            
            service_arns = []
            paginator = self.ecs_client.get_paginator('list_services')
            for page in paginator.paginate(cluster=cluster_arn):
                service_arns.extend(page.get('serviceArns', []))
            
            if not service_arns:
                return []
            
            for i in range(0, len(service_arns), 10):
                batch = service_arns[i:i+10]
                response = self.ecs_client.describe_services(
                    cluster=cluster_arn,
                    services=batch
                )
                
                for svc_data in response.get('services', []):
                    service = ECSService(
                        service_arn=svc_data['serviceArn'],
                        service_name=svc_data['serviceName'],
                        cluster_arn=svc_data['clusterArn'],
                        status=svc_data['status'],
                        desired_count=svc_data.get('desiredCount', 0),
                        running_count=svc_data.get('runningCount', 0),
                        pending_count=svc_data.get('pendingCount', 0),
                        launch_type=svc_data.get('launchType', 'EC2'),
                        task_definition=svc_data.get('taskDefinition', ''),
                        deployment_controller=svc_data.get('deploymentController', {}).get('type', 'ECS'),
                        scheduling_strategy=svc_data.get('schedulingStrategy', 'REPLICA')
                    )
                    services.append(service)
            
            return services
            
        except ClientError as e:
            handle_aws_error(e, "get_ecs_services")
            return []
    
    def get_tasks(self, cluster_arn: str, service_name: Optional[str] = None) -> List[ECSTask]:
        """
        Obtém tasks de um cluster/serviço
        
        Args:
            cluster_arn: ARN do cluster
            service_name: Nome do serviço (opcional)
            
        Returns:
            Lista de ECSTask
        """
        try:
            tasks = []
            
            task_arns = []
            params = {'cluster': cluster_arn}
            if service_name:
                params['serviceName'] = service_name
            
            paginator = self.ecs_client.get_paginator('list_tasks')
            for page in paginator.paginate(**params):
                task_arns.extend(page.get('taskArns', []))
            
            if not task_arns:
                return []
            
            for i in range(0, len(task_arns), 100):
                batch = task_arns[i:i+100]
                response = self.ecs_client.describe_tasks(
                    cluster=cluster_arn,
                    tasks=batch
                )
                
                for task_data in response.get('tasks', []):
                    task = ECSTask(
                        task_arn=task_data['taskArn'],
                        task_definition_arn=task_data['taskDefinitionArn'],
                        cluster_arn=task_data['clusterArn'],
                        last_status=task_data['lastStatus'],
                        desired_status=task_data['desiredStatus'],
                        launch_type=task_data.get('launchType', 'EC2'),
                        cpu=task_data.get('cpu', '0'),
                        memory=task_data.get('memory', '0'),
                        started_at=task_data.get('startedAt'),
                        connectivity=task_data.get('connectivity', 'CONNECTED'),
                        health_status=task_data.get('healthStatus', 'UNKNOWN')
                    )
                    tasks.append(task)
            
            return tasks
            
        except ClientError as e:
            handle_aws_error(e, "get_ecs_tasks")
            return []
    
    def get_service_metrics(self, cluster_name: str, service_name: str) -> Dict[str, Any]:
        """
        Obtém métricas de um serviço específico
        
        Args:
            cluster_name: Nome do cluster
            service_name: Nome do serviço
            
        Returns:
            Dicionário com métricas
        """
        dimensions = [
            {'Name': 'ClusterName', 'Value': cluster_name},
            {'Name': 'ServiceName', 'Value': service_name}
        ]
        
        metrics = {
            'cpu_utilization': self.get_cloudwatch_metric(
                'AWS/ECS', 'CPUUtilization', dimensions
            ),
            'memory_utilization': self.get_cloudwatch_metric(
                'AWS/ECS', 'MemoryUtilization', dimensions
            )
        }
        
        return metrics
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do ECS"""
        clusters = self.get_clusters()
        
        total_services = sum(c.active_services for c in clusters)
        total_running_tasks = sum(c.running_tasks for c in clusters)
        total_pending_tasks = sum(c.pending_tasks for c in clusters)
        total_container_instances = sum(c.registered_container_instances for c in clusters)
        
        fargate_clusters = sum(1 for c in clusters if 'FARGATE' in c.capacity_providers)
        ec2_clusters = sum(1 for c in clusters if c.registered_container_instances > 0)
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(clusters),
            metrics={
                'cluster_count': len(clusters),
                'total_services': total_services,
                'total_running_tasks': total_running_tasks,
                'total_pending_tasks': total_pending_tasks,
                'total_container_instances': total_container_instances,
                'fargate_clusters': fargate_clusters,
                'ec2_clusters': ec2_clusters,
                'active_clusters': sum(1 for c in clusters if c.status == 'ACTIVE')
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para ECS"""
        recommendations = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            if cluster.running_tasks == 0 and cluster.active_services == 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type='ECSCluster',
                    recommendation_type='UNUSED_RESOURCE',
                    description=f'Cluster {cluster.cluster_name} não tem tasks ou serviços em execução. '
                               'Considere deletar se não estiver sendo usado.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    implementation_effort='LOW',
                    details={
                        'running_tasks': 0,
                        'active_services': 0,
                        'container_instances': cluster.registered_container_instances
                    }
                ))
            
            if cluster.pending_tasks > 0 and cluster.pending_tasks > cluster.running_tasks * 0.1:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type='ECSCluster',
                    recommendation_type='SCALE_CAPACITY',
                    description=f'Cluster {cluster.cluster_name} tem {cluster.pending_tasks} tasks pendentes. '
                               'Considere adicionar mais capacidade.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    implementation_effort='MEDIUM',
                    details={
                        'pending_tasks': cluster.pending_tasks,
                        'running_tasks': cluster.running_tasks,
                        'suggestion': 'Adicionar capacity providers ou instâncias'
                    }
                ))
            
            services = self.get_services(cluster.cluster_arn)
            for service in services:
                if service.running_count < service.desired_count:
                    recommendations.append(ServiceRecommendation(
                        resource_id=service.service_arn,
                        resource_type='ECSService',
                        recommendation_type='SERVICE_UNHEALTHY',
                        description=f'Serviço {service.service_name} tem menos tasks rodando ({service.running_count}) '
                                   f'do que desejado ({service.desired_count}).',
                        estimated_savings=0.0,
                        priority='HIGH',
                        implementation_effort='MEDIUM',
                        details={
                            'desired_count': service.desired_count,
                            'running_count': service.running_count,
                            'pending_count': service.pending_count
                        }
                    ))
                
                if service.launch_type == 'EC2':
                    metrics = self.get_service_metrics(cluster.cluster_name, service.service_name)
                    cpu_util = metrics.get('cpu_utilization', {}).get('average', 0)
                    memory_util = metrics.get('memory_utilization', {}).get('average', 0)
                    
                    if cpu_util < 10 and memory_util < 20 and service.running_count > 0:
                        recommendations.append(ServiceRecommendation(
                            resource_id=service.service_arn,
                            resource_type='ECSService',
                            recommendation_type='RIGHTSIZE',
                            description=f'Serviço {service.service_name} tem baixa utilização. '
                                       f'CPU: {cpu_util:.1f}%, Memória: {memory_util:.1f}%.',
                            estimated_savings=0.0,
                            priority='MEDIUM',
                            implementation_effort='MEDIUM',
                            details={
                                'cpu_utilization': cpu_util,
                                'memory_utilization': memory_util,
                                'suggestion': 'Reduzir task definition CPU/Memory ou considerar Fargate Spot'
                            }
                        ))
                
                if service.launch_type == 'EC2' and 'FARGATE' in cluster.capacity_providers:
                    recommendations.append(ServiceRecommendation(
                        resource_id=service.service_arn,
                        resource_type='ECSService',
                        recommendation_type='MIGRATE_TO_FARGATE',
                        description=f'Serviço {service.service_name} roda em EC2 mas cluster suporta Fargate. '
                                   'Considere migrar para Fargate para simplificar operações.',
                        estimated_savings=0.0,
                        priority='LOW',
                        implementation_effort='MEDIUM',
                        details={
                            'current_launch_type': 'EC2',
                            'suggested_launch_type': 'FARGATE',
                            'benefits': 'Menos gestão de infraestrutura, pay-per-use'
                        }
                    ))
        
        logger.info(f"Generated {len(recommendations)} ECS recommendations")
        return recommendations
    
    def get_fargate_cost_analysis(self) -> Dict[str, Any]:
        """
        Analisa custos Fargate vs EC2
        
        Returns:
            Análise comparativa de custos
        """
        clusters = self.get_clusters()
        analysis = {
            'fargate_tasks': 0,
            'ec2_tasks': 0,
            'fargate_vcpu_hours': 0.0,
            'fargate_memory_gb_hours': 0.0,
            'ec2_container_instances': 0
        }
        
        for cluster in clusters:
            analysis['ec2_container_instances'] += cluster.registered_container_instances
            
            tasks = self.get_tasks(cluster.cluster_arn)
            for task in tasks:
                if task.launch_type == 'FARGATE':
                    analysis['fargate_tasks'] += 1
                    try:
                        cpu_vcpu = int(task.cpu) / 1024
                        memory_gb = int(task.memory) / 1024
                        analysis['fargate_vcpu_hours'] += cpu_vcpu
                        analysis['fargate_memory_gb_hours'] += memory_gb
                    except ValueError:
                        pass
                else:
                    analysis['ec2_tasks'] += 1
        
        analysis['estimated_fargate_hourly_cost'] = (
            analysis['fargate_vcpu_hours'] * 0.04048 +
            analysis['fargate_memory_gb_hours'] * 0.004445
        )
        
        return analysis
