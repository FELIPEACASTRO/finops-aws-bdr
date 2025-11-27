"""
AWS CodeDeploy FinOps Service

Análise de aplicações de deploy, deployment groups e recomendações de otimização.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DeploymentApplication:
    """Representa uma aplicação CodeDeploy"""
    name: str
    application_id: Optional[str] = None
    compute_platform: str = 'Server'
    create_time: Optional[datetime] = None
    linked_to_github: bool = False
    
    @property
    def is_ec2_server(self) -> bool:
        return self.compute_platform == 'Server'
    
    @property
    def is_lambda(self) -> bool:
        return self.compute_platform == 'Lambda'
    
    @property
    def is_ecs(self) -> bool:
        return self.compute_platform == 'ECS'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'application_id': self.application_id,
            'compute_platform': self.compute_platform,
            'linked_to_github': self.linked_to_github,
            'is_ec2_server': self.is_ec2_server,
            'is_lambda': self.is_lambda,
            'is_ecs': self.is_ecs
        }


@dataclass
class DeploymentGroup:
    """Representa um deployment group"""
    name: str
    application_name: str
    deployment_group_id: Optional[str] = None
    deployment_config_name: str = 'CodeDeployDefault.OneAtATime'
    service_role_arn: Optional[str] = None
    auto_scaling_groups: List[str] = field(default_factory=list)
    ec2_tag_filters: List[Dict] = field(default_factory=list)
    on_premises_tag_filters: List[Dict] = field(default_factory=list)
    trigger_configurations: List[Dict] = field(default_factory=list)
    alarm_configuration: Dict = field(default_factory=dict)
    auto_rollback_configuration: Dict = field(default_factory=dict)
    deployment_style: Dict = field(default_factory=dict)
    blue_green_deployment_configuration: Dict = field(default_factory=dict)
    target_revision: Dict = field(default_factory=dict)
    compute_platform: str = 'Server'
    
    @property
    def has_auto_scaling(self) -> bool:
        return len(self.auto_scaling_groups) > 0
    
    @property
    def has_alarms(self) -> bool:
        return self.alarm_configuration.get('enabled', False)
    
    @property
    def has_auto_rollback(self) -> bool:
        return self.auto_rollback_configuration.get('enabled', False)
    
    @property
    def is_blue_green(self) -> bool:
        return self.deployment_style.get('deploymentType') == 'BLUE_GREEN'
    
    @property
    def is_in_place(self) -> bool:
        return self.deployment_style.get('deploymentType') == 'IN_PLACE'
    
    @property
    def has_triggers(self) -> bool:
        return len(self.trigger_configurations) > 0
    
    @property
    def uses_load_balancer(self) -> bool:
        return self.deployment_style.get('deploymentOption') == 'WITH_TRAFFIC_CONTROL'
    
    @property
    def instance_count(self) -> int:
        return len(self.ec2_tag_filters) + len(self.on_premises_tag_filters)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'application_name': self.application_name,
            'deployment_group_id': self.deployment_group_id,
            'deployment_config_name': self.deployment_config_name,
            'compute_platform': self.compute_platform,
            'auto_scaling_group_count': len(self.auto_scaling_groups),
            'has_auto_scaling': self.has_auto_scaling,
            'has_alarms': self.has_alarms,
            'has_auto_rollback': self.has_auto_rollback,
            'is_blue_green': self.is_blue_green,
            'is_in_place': self.is_in_place,
            'has_triggers': self.has_triggers,
            'uses_load_balancer': self.uses_load_balancer
        }


@dataclass
class Deployment:
    """Representa um deployment"""
    deployment_id: str
    application_name: str
    deployment_group_name: str
    status: str = 'Created'
    create_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    deployment_config_name: str = ''
    revision_type: str = 'S3'
    rollback_info: Dict = field(default_factory=dict)
    deployment_overview: Dict = field(default_factory=dict)
    compute_platform: str = 'Server'
    
    @property
    def is_successful(self) -> bool:
        return self.status == 'Succeeded'
    
    @property
    def is_failed(self) -> bool:
        return self.status == 'Failed'
    
    @property
    def is_in_progress(self) -> bool:
        return self.status in ['Created', 'Queued', 'InProgress']
    
    @property
    def is_stopped(self) -> bool:
        return self.status == 'Stopped'
    
    @property
    def was_rolled_back(self) -> bool:
        return bool(self.rollback_info.get('rollbackDeploymentId'))
    
    @property
    def instances_succeeded(self) -> int:
        return self.deployment_overview.get('Succeeded', 0)
    
    @property
    def instances_failed(self) -> int:
        return self.deployment_overview.get('Failed', 0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'deployment_id': self.deployment_id,
            'application_name': self.application_name,
            'deployment_group_name': self.deployment_group_name,
            'status': self.status,
            'deployment_config_name': self.deployment_config_name,
            'revision_type': self.revision_type,
            'compute_platform': self.compute_platform,
            'is_successful': self.is_successful,
            'is_failed': self.is_failed,
            'is_in_progress': self.is_in_progress,
            'was_rolled_back': self.was_rolled_back,
            'instances_succeeded': self.instances_succeeded,
            'instances_failed': self.instances_failed
        }


@dataclass
class DeploymentConfig:
    """Representa uma configuração de deployment"""
    name: str
    deployment_config_id: Optional[str] = None
    compute_platform: str = 'Server'
    minimum_healthy_hosts: Dict = field(default_factory=dict)
    traffic_routing_config: Dict = field(default_factory=dict)
    
    @property
    def is_all_at_once(self) -> bool:
        return 'AllAtOnce' in self.name
    
    @property
    def is_one_at_a_time(self) -> bool:
        return 'OneAtATime' in self.name
    
    @property
    def is_half_at_a_time(self) -> bool:
        return 'HalfAtATime' in self.name
    
    @property
    def is_canary(self) -> bool:
        return self.traffic_routing_config.get('type') == 'TimeBasedCanary'
    
    @property
    def is_linear(self) -> bool:
        return self.traffic_routing_config.get('type') == 'TimeBasedLinear'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'deployment_config_id': self.deployment_config_id,
            'compute_platform': self.compute_platform,
            'is_all_at_once': self.is_all_at_once,
            'is_one_at_a_time': self.is_one_at_a_time,
            'is_half_at_a_time': self.is_half_at_a_time,
            'is_canary': self.is_canary,
            'is_linear': self.is_linear
        }


class CodeDeployService(BaseAWSService):
    """Serviço FinOps para AWS CodeDeploy"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._codedeploy_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "codedeploy"
    
    @property
    def codedeploy_client(self):
        if self._codedeploy_client is None:
            if self._client_factory:
                self._codedeploy_client = self._client_factory.get_client('codedeploy')
            else:
                import boto3
                self._codedeploy_client = boto3.client('codedeploy')
        return self._codedeploy_client
    
    def health_check(self) -> bool:
        try:
            self.codedeploy_client.list_applications(maxResults=1)
            return True
        except Exception:
            return False
    
    def get_applications(self) -> List[DeploymentApplication]:
        applications = []
        try:
            paginator = self.codedeploy_client.get_paginator('list_applications')
            app_names = []
            
            for page in paginator.paginate():
                app_names.extend(page.get('applications', []))
            
            if app_names:
                for i in range(0, len(app_names), 100):
                    batch = app_names[i:i+100]
                    response = self.codedeploy_client.batch_get_applications(applicationNames=batch)
                    
                    for app in response.get('applicationsInfo', []):
                        applications.append(DeploymentApplication(
                            name=app.get('applicationName', ''),
                            application_id=app.get('applicationId'),
                            compute_platform=app.get('computePlatform', 'Server'),
                            create_time=app.get('createTime'),
                            linked_to_github=app.get('linkedToGitHub', False)
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar aplicações CodeDeploy: {e}")
        
        return applications
    
    def get_deployment_groups(self, application_name: str) -> List[DeploymentGroup]:
        groups = []
        try:
            paginator = self.codedeploy_client.get_paginator('list_deployment_groups')
            group_names = []
            
            for page in paginator.paginate(applicationName=application_name):
                group_names.extend(page.get('deploymentGroups', []))
            
            if group_names:
                for i in range(0, len(group_names), 25):
                    batch = group_names[i:i+25]
                    response = self.codedeploy_client.batch_get_deployment_groups(
                        applicationName=application_name,
                        deploymentGroupNames=batch
                    )
                    
                    for group in response.get('deploymentGroupsInfo', []):
                        groups.append(DeploymentGroup(
                            name=group.get('deploymentGroupName', ''),
                            application_name=application_name,
                            deployment_group_id=group.get('deploymentGroupId'),
                            deployment_config_name=group.get('deploymentConfigName', ''),
                            service_role_arn=group.get('serviceRoleArn'),
                            auto_scaling_groups=[asg.get('name', '') for asg in group.get('autoScalingGroups', [])],
                            ec2_tag_filters=group.get('ec2TagFilters', []),
                            on_premises_tag_filters=group.get('onPremisesInstanceTagFilters', []),
                            trigger_configurations=group.get('triggerConfigurations', []),
                            alarm_configuration=group.get('alarmConfiguration', {}),
                            auto_rollback_configuration=group.get('autoRollbackConfiguration', {}),
                            deployment_style=group.get('deploymentStyle', {}),
                            blue_green_deployment_configuration=group.get('blueGreenDeploymentConfiguration', {}),
                            target_revision=group.get('targetRevision', {}),
                            compute_platform=group.get('computePlatform', 'Server')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar deployment groups para {application_name}: {e}")
        
        return groups
    
    def get_deployments(self, application_name: str = None, max_results: int = 50) -> List[Deployment]:
        deployments = []
        try:
            params = {}
            if application_name:
                params['applicationName'] = application_name
            
            response = self.codedeploy_client.list_deployments(**params)
            deployment_ids = response.get('deployments', [])[:max_results]
            
            if deployment_ids:
                for i in range(0, len(deployment_ids), 25):
                    batch = deployment_ids[i:i+25]
                    details = self.codedeploy_client.batch_get_deployments(deploymentIds=batch)
                    
                    for deployment in details.get('deploymentsInfo', []):
                        deployments.append(Deployment(
                            deployment_id=deployment.get('deploymentId', ''),
                            application_name=deployment.get('applicationName', ''),
                            deployment_group_name=deployment.get('deploymentGroupName', ''),
                            status=deployment.get('status', 'Created'),
                            create_time=deployment.get('createTime'),
                            complete_time=deployment.get('completeTime'),
                            deployment_config_name=deployment.get('deploymentConfigName', ''),
                            revision_type=deployment.get('revision', {}).get('revisionType', 'S3'),
                            rollback_info=deployment.get('rollbackInfo', {}),
                            deployment_overview=deployment.get('deploymentOverview', {}),
                            compute_platform=deployment.get('computePlatform', 'Server')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar deployments: {e}")
        
        return deployments
    
    def get_deployment_configs(self) -> List[DeploymentConfig]:
        configs = []
        try:
            paginator = self.codedeploy_client.get_paginator('list_deployment_configs')
            
            for page in paginator.paginate():
                for config_name in page.get('deploymentConfigsList', []):
                    try:
                        response = self.codedeploy_client.get_deployment_config(
                            deploymentConfigName=config_name
                        )
                        config = response.get('deploymentConfigInfo', {})
                        
                        configs.append(DeploymentConfig(
                            name=config.get('deploymentConfigName', config_name),
                            deployment_config_id=config.get('deploymentConfigId'),
                            compute_platform=config.get('computePlatform', 'Server'),
                            minimum_healthy_hosts=config.get('minimumHealthyHosts', {}),
                            traffic_routing_config=config.get('trafficRoutingConfig', {})
                        ))
                    except Exception:
                        pass
        except Exception as e:
            self.logger.error(f"Erro ao listar deployment configs: {e}")
        
        return configs
    
    def get_resources(self) -> Dict[str, Any]:
        applications = self.get_applications()
        all_groups = []
        
        for app in applications:
            groups = self.get_deployment_groups(app.name)
            all_groups.extend(groups)
        
        configs = self.get_deployment_configs()
        
        return {
            'applications': [a.to_dict() for a in applications],
            'deployment_groups': [g.to_dict() for g in all_groups],
            'deployment_configs': [c.to_dict() for c in configs],
            'summary': {
                'total_applications': len(applications),
                'total_deployment_groups': len(all_groups),
                'total_configs': len(configs),
                'ec2_applications': sum(1 for a in applications if a.is_ec2_server),
                'lambda_applications': sum(1 for a in applications if a.is_lambda),
                'ecs_applications': sum(1 for a in applications if a.is_ecs),
                'blue_green_groups': sum(1 for g in all_groups if g.is_blue_green),
                'groups_with_auto_rollback': sum(1 for g in all_groups if g.has_auto_rollback),
                'groups_with_alarms': sum(1 for g in all_groups if g.has_alarms)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        applications = self.get_applications()
        deployments = self.get_deployments(max_results=100)
        
        metrics = {
            'total_applications': len(applications),
            'compute_platforms': {
                'server': sum(1 for a in applications if a.is_ec2_server),
                'lambda': sum(1 for a in applications if a.is_lambda),
                'ecs': sum(1 for a in applications if a.is_ecs)
            },
            'deployment_stats': {
                'total': len(deployments),
                'succeeded': sum(1 for d in deployments if d.is_successful),
                'failed': sum(1 for d in deployments if d.is_failed),
                'in_progress': sum(1 for d in deployments if d.is_in_progress),
                'rolled_back': sum(1 for d in deployments if d.was_rolled_back)
            }
        }
        
        if len(deployments) > 0:
            metrics['success_rate'] = metrics['deployment_stats']['succeeded'] / len(deployments) * 100
        else:
            metrics['success_rate'] = 0
        
        return metrics
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        applications = self.get_applications()
        
        for app in applications:
            groups = self.get_deployment_groups(app.name)
            
            for group in groups:
                if not group.has_auto_rollback:
                    recommendations.append({
                        'resource_id': f"{app.name}/{group.name}",
                        'resource_type': 'CodeDeploy Deployment Group',
                        'title': 'Habilitar auto rollback',
                        'description': f'Deployment group {group.name} não tem auto rollback. Falhas podem causar downtime.',
                        'action': 'Habilitar auto rollback em caso de falha de deployment',
                        'estimated_savings': 'N/A',
                        'priority': 'HIGH'
                    })
                
                if not group.has_alarms and group.is_blue_green:
                    recommendations.append({
                        'resource_id': f"{app.name}/{group.name}",
                        'resource_type': 'CodeDeploy Deployment Group',
                        'title': 'Configurar alarmes para Blue/Green',
                        'description': f'Deployment group {group.name} usa Blue/Green sem alarmes CloudWatch.',
                        'action': 'Adicionar alarmes para detectar problemas durante deployment',
                        'estimated_savings': 'N/A',
                        'priority': 'MEDIUM'
                    })
                
                if group.is_in_place and group.has_auto_scaling:
                    recommendations.append({
                        'resource_id': f"{app.name}/{group.name}",
                        'resource_type': 'CodeDeploy Deployment Group',
                        'title': 'Considerar Blue/Green para Auto Scaling',
                        'description': f'Deployment group {group.name} usa in-place com Auto Scaling. Blue/Green oferece zero downtime.',
                        'action': 'Avaliar migração para Blue/Green deployment',
                        'estimated_savings': 'N/A',
                        'priority': 'MEDIUM'
                    })
        
        deployments = self.get_deployments(max_results=50)
        failed = sum(1 for d in deployments if d.is_failed)
        if len(deployments) > 10 and failed / len(deployments) > 0.2:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'CodeDeploy',
                'title': 'Alta taxa de falhas em deployments',
                'description': f'{failed}/{len(deployments)} deployments recentes falharam (>{20}%).',
                'action': 'Investigar causas de falhas para melhorar confiabilidade',
                'estimated_savings': 'Médio',
                'priority': 'HIGH'
            })
        
        return recommendations
