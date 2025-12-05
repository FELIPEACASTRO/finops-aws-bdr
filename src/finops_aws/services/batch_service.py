"""
AWS Batch FinOps Service

Análise de custos e otimização para AWS Batch:
- Job queues e compute environments
- Job definitions e execuções
- Scheduling policies
- Recomendações de otimização (Spot, rightsizing)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class BatchComputeEnvironment:
    """Representa um Compute Environment do AWS Batch"""
    compute_environment_name: str
    compute_environment_arn: str
    ecs_cluster_arn: str = ''
    state: str = 'ENABLED'
    status: str = 'VALID'
    type: str = 'MANAGED'
    service_role: str = ''
    compute_resources: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_enabled(self) -> bool:
        return self.state == 'ENABLED'
    
    @property
    def is_managed(self) -> bool:
        return self.type == 'MANAGED'
    
    @property
    def is_fargate(self) -> bool:
        return self.compute_resources.get('type', '').startswith('FARGATE')
    
    @property
    def is_spot(self) -> bool:
        return 'SPOT' in self.compute_resources.get('type', '')
    
    @property
    def min_vcpus(self) -> int:
        return self.compute_resources.get('minvCpus', 0)
    
    @property
    def max_vcpus(self) -> int:
        return self.compute_resources.get('maxvCpus', 0)
    
    @property
    def desired_vcpus(self) -> int:
        return self.compute_resources.get('desiredvCpus', 0)
    
    @property
    def instance_types(self) -> List[str]:
        return self.compute_resources.get('instanceTypes', [])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'compute_environment_name': self.compute_environment_name,
            'compute_environment_arn': self.compute_environment_arn,
            'ecs_cluster_arn': self.ecs_cluster_arn,
            'state': self.state,
            'status': self.status,
            'type': self.type,
            'is_enabled': self.is_enabled,
            'is_managed': self.is_managed,
            'is_fargate': self.is_fargate,
            'is_spot': self.is_spot,
            'min_vcpus': self.min_vcpus,
            'max_vcpus': self.max_vcpus,
            'desired_vcpus': self.desired_vcpus,
            'instance_types': self.instance_types,
            'tags': self.tags
        }


@dataclass
class BatchJobQueue:
    """Representa uma Job Queue do AWS Batch"""
    job_queue_name: str
    job_queue_arn: str
    state: str = 'ENABLED'
    status: str = 'VALID'
    priority: int = 1
    compute_environment_order: List[Dict[str, Any]] = field(default_factory=list)
    scheduling_policy_arn: str = ''
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_enabled(self) -> bool:
        return self.state == 'ENABLED'
    
    @property
    def has_scheduling_policy(self) -> bool:
        return bool(self.scheduling_policy_arn)
    
    @property
    def compute_environment_count(self) -> int:
        return len(self.compute_environment_order)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_queue_name': self.job_queue_name,
            'job_queue_arn': self.job_queue_arn,
            'state': self.state,
            'status': self.status,
            'priority': self.priority,
            'is_enabled': self.is_enabled,
            'has_scheduling_policy': self.has_scheduling_policy,
            'compute_environment_count': self.compute_environment_count,
            'tags': self.tags
        }


@dataclass
class BatchJobDefinition:
    """Representa uma Job Definition do AWS Batch"""
    job_definition_name: str
    job_definition_arn: str
    revision: int = 1
    status: str = 'ACTIVE'
    type: str = 'container'
    platform_capabilities: List[str] = field(default_factory=list)
    container_properties: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[Dict[str, int]] = None
    retry_strategy: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        return self.status == 'ACTIVE'
    
    @property
    def is_fargate(self) -> bool:
        return 'FARGATE' in self.platform_capabilities
    
    @property
    def vcpus(self) -> float:
        return float(self.container_properties.get('vcpus', 0))
    
    @property
    def memory_mb(self) -> int:
        return self.container_properties.get('memory', 0)
    
    @property
    def has_timeout(self) -> bool:
        return self.timeout is not None and 'attemptDurationSeconds' in (self.timeout or {})
    
    @property
    def timeout_seconds(self) -> int:
        if self.timeout:
            return self.timeout.get('attemptDurationSeconds', 0)
        return 0
    
    @property
    def has_retry(self) -> bool:
        return self.retry_strategy is not None
    
    @property
    def max_retries(self) -> int:
        if self.retry_strategy:
            return self.retry_strategy.get('attempts', 1)
        return 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_definition_name': self.job_definition_name,
            'job_definition_arn': self.job_definition_arn,
            'revision': self.revision,
            'status': self.status,
            'type': self.type,
            'is_active': self.is_active,
            'is_fargate': self.is_fargate,
            'vcpus': self.vcpus,
            'memory_mb': self.memory_mb,
            'has_timeout': self.has_timeout,
            'timeout_seconds': self.timeout_seconds,
            'has_retry': self.has_retry,
            'max_retries': self.max_retries,
            'tags': self.tags
        }


class BatchService(BaseAWSService):
    """Serviço FinOps para análise de AWS Batch"""
    
    def __init__(self, client_factory):
        self.client_factory = client_factory
        self._batch_client = None
    
    @property
    def batch_client(self):
        if self._batch_client is None:
            self._batch_client = self.client_factory.get_client('batch')
        return self._batch_client
    
    @property
    def service_name(self) -> str:
        return "AWS Batch"
    
    def health_check(self) -> bool:
        try:
            self.batch_client.describe_compute_environments(maxResults=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_compute_environments(self) -> List[BatchComputeEnvironment]:
        environments = []
        try:
            paginator = self.batch_client.get_paginator('describe_compute_environments')
            for page in paginator.paginate():
                for env in page.get('computeEnvironments', []):
                    environments.append(BatchComputeEnvironment(
                        compute_environment_name=env.get('computeEnvironmentName', ''),
                        compute_environment_arn=env.get('computeEnvironmentArn', ''),
                        ecs_cluster_arn=env.get('ecsClusterArn', ''),
                        state=env.get('state', 'ENABLED'),
                        status=env.get('status', 'VALID'),
                        type=env.get('type', 'MANAGED'),
                        service_role=env.get('serviceRole', ''),
                        compute_resources=env.get('computeResources', {}),
                        tags=env.get('tags', {})
                    ))
        except Exception as e:  # noqa: E722
            pass
        return environments
    
    def get_job_queues(self) -> List[BatchJobQueue]:
        queues = []
        try:
            paginator = self.batch_client.get_paginator('describe_job_queues')
            for page in paginator.paginate():
                for queue in page.get('jobQueues', []):
                    queues.append(BatchJobQueue(
                        job_queue_name=queue.get('jobQueueName', ''),
                        job_queue_arn=queue.get('jobQueueArn', ''),
                        state=queue.get('state', 'ENABLED'),
                        status=queue.get('status', 'VALID'),
                        priority=queue.get('priority', 1),
                        compute_environment_order=queue.get('computeEnvironmentOrder', []),
                        scheduling_policy_arn=queue.get('schedulingPolicyArn', ''),
                        tags=queue.get('tags', {})
                    ))
        except Exception as e:  # noqa: E722
            pass
        return queues
    
    def get_job_definitions(self, status: str = 'ACTIVE') -> List[BatchJobDefinition]:
        definitions = []
        try:
            paginator = self.batch_client.get_paginator('describe_job_definitions')
            for page in paginator.paginate(status=status):
                for job_def in page.get('jobDefinitions', []):
                    definitions.append(BatchJobDefinition(
                        job_definition_name=job_def.get('jobDefinitionName', ''),
                        job_definition_arn=job_def.get('jobDefinitionArn', ''),
                        revision=job_def.get('revision', 1),
                        status=job_def.get('status', 'ACTIVE'),
                        type=job_def.get('type', 'container'),
                        platform_capabilities=job_def.get('platformCapabilities', []),
                        container_properties=job_def.get('containerProperties', {}),
                        timeout=job_def.get('timeout'),
                        retry_strategy=job_def.get('retryStrategy'),
                        tags=job_def.get('tags', {})
                    ))
        except Exception as e:  # noqa: E722
            pass
        return definitions
    
    def get_resources(self) -> Dict[str, Any]:
        compute_envs = self.get_compute_environments()
        job_queues = self.get_job_queues()
        job_definitions = self.get_job_definitions()
        
        return {
            'compute_environments': [env.to_dict() for env in compute_envs],
            'job_queues': [q.to_dict() for q in job_queues],
            'job_definitions': [jd.to_dict() for jd in job_definitions],
            'summary': {
                'total_compute_environments': len(compute_envs),
                'managed_environments': sum(1 for e in compute_envs if e.is_managed),
                'spot_environments': sum(1 for e in compute_envs if e.is_spot),
                'fargate_environments': sum(1 for e in compute_envs if e.is_fargate),
                'total_job_queues': len(job_queues),
                'enabled_queues': sum(1 for q in job_queues if q.is_enabled),
                'total_job_definitions': len(job_definitions),
                'active_definitions': sum(1 for jd in job_definitions if jd.is_active)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        return {
            'compute_environment_count': resources['summary']['total_compute_environments'],
            'spot_usage_ratio': (
                resources['summary']['spot_environments'] / 
                max(resources['summary']['total_compute_environments'], 1)
            ),
            'fargate_usage_ratio': (
                resources['summary']['fargate_environments'] / 
                max(resources['summary']['total_compute_environments'], 1)
            ),
            'job_queue_count': resources['summary']['total_job_queues'],
            'job_definition_count': resources['summary']['total_job_definitions']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        compute_envs = self.get_compute_environments()
        job_definitions = self.get_job_definitions()
        
        for env in compute_envs:
            if env.is_managed and not env.is_spot and not env.is_fargate:
                recommendations.append(ServiceRecommendation(
                    resource_id=env.compute_environment_name,
                    resource_type='BatchComputeEnvironment',
                    title='Considerar uso de Spot Instances',
                    recommendation=f'Compute environment {env.compute_environment_name} usa On-Demand. '
                                 f'Considere migrar para Spot instances para economia de até 90%.',
                    action='Migrar para SPOT ou SPOT_CAPACITY_OPTIMIZED',
                    estimated_savings=None,
                    priority='high',
                    category='cost_optimization'
                ))
            
            if env.min_vcpus > 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=env.compute_environment_name,
                    resource_type='BatchComputeEnvironment',
                    title='Reduzir minvCpus para zero',
                    recommendation=f'Compute environment {env.compute_environment_name} tem minvCpus={env.min_vcpus}. '
                                 f'Considere definir como 0 para evitar custos quando ocioso.',
                    action='Definir minvCpus=0',
                    estimated_savings=None,
                    priority='medium',
                    category='cost_optimization'
                ))
        
        for job_def in job_definitions:
            if not job_def.has_timeout:
                recommendations.append(ServiceRecommendation(
                    resource_id=job_def.job_definition_name,
                    resource_type='BatchJobDefinition',
                    title='Definir timeout para job',
                    recommendation=f'Job definition {job_def.job_definition_name} não tem timeout definido. '
                                 f'Jobs sem timeout podem executar indefinidamente, aumentando custos.',
                    action='Definir attemptDurationSeconds no timeout',
                    estimated_savings=None,
                    priority='medium',
                    category='cost_optimization'
                ))
        
        return recommendations
