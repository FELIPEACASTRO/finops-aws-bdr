"""
SageMaker FinOps Service - Análise de Custos de ML

FASE 2 - Prioridade 2: ML/AI (alto custo)
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Notebooks, Endpoints, Training Jobs
- Análise de utilização de instâncias ML
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class SageMakerNotebook:
    """Representa um Notebook Instance"""
    notebook_instance_name: str
    notebook_instance_arn: str
    notebook_instance_status: str
    instance_type: str
    role_arn: str
    subnet_id: Optional[str] = None
    volume_size_in_gb: int = 5
    direct_internet_access: str = "Enabled"
    root_access: str = "Enabled"
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'notebook_instance_name': self.notebook_instance_name,
            'notebook_instance_status': self.notebook_instance_status,
            'instance_type': self.instance_type,
            'volume_size_in_gb': self.volume_size_in_gb,
            'direct_internet_access': self.direct_internet_access,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class SageMakerEndpoint:
    """Representa um Endpoint de Inferência"""
    endpoint_name: str
    endpoint_arn: str
    endpoint_status: str
    endpoint_config_name: str
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    production_variants: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint_name': self.endpoint_name,
            'endpoint_status': self.endpoint_status,
            'endpoint_config_name': self.endpoint_config_name,
            'production_variants': len(self.production_variants),
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class SageMakerTrainingJob:
    """Representa um Training Job"""
    training_job_name: str
    training_job_arn: str
    training_job_status: str
    secondary_status: str
    creation_time: Optional[datetime]
    training_end_time: Optional[datetime]
    billable_seconds: int = 0
    instance_type: str = ""
    instance_count: int = 1
    volume_size_in_gb: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'training_job_name': self.training_job_name,
            'training_job_status': self.training_job_status,
            'billable_seconds': self.billable_seconds,
            'instance_type': self.instance_type,
            'instance_count': self.instance_count,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


class SageMakerService(BaseAWSService):
    """
    Serviço FinOps para análise de custos SageMaker
    """
    
    def __init__(
        self,
        sagemaker_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._sagemaker_client = sagemaker_client
    
    @property
    def sagemaker_client(self):
        if self._sagemaker_client is None:
            import boto3
            self._sagemaker_client = boto3.client('sagemaker')
        return self._sagemaker_client
    
    def get_service_name(self) -> str:
        return "Amazon SageMaker"
    
    def health_check(self) -> bool:
        try:
            self.sagemaker_client.list_notebook_instances(MaxResults=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    
    def get_notebook_instances(self) -> List[SageMakerNotebook]:
        """Lista Notebook Instances"""
        notebooks = []
        
        paginator = self.sagemaker_client.get_paginator('list_notebook_instances')
        
        for page in paginator.paginate():
            for nb in page.get('NotebookInstances', []):
                notebook = SageMakerNotebook(
                    notebook_instance_name=nb['NotebookInstanceName'],
                    notebook_instance_arn=nb['NotebookInstanceArn'],
                    notebook_instance_status=nb['NotebookInstanceStatus'],
                    instance_type=nb['InstanceType'],
                    role_arn='',
                    creation_time=nb.get('CreationTime'),
                    last_modified_time=nb.get('LastModifiedTime')
                )
                notebooks.append(notebook)
        
        return notebooks
    
    
    def get_endpoints(self) -> List[SageMakerEndpoint]:
        """Lista Endpoints de Inferência"""
        endpoints = []
        
        paginator = self.sagemaker_client.get_paginator('list_endpoints')
        
        for page in paginator.paginate():
            for ep in page.get('Endpoints', []):
                try:
                    detail = self.sagemaker_client.describe_endpoint(
                        EndpointName=ep['EndpointName']
                    )
                    
                    endpoint = SageMakerEndpoint(
                        endpoint_name=ep['EndpointName'],
                        endpoint_arn=ep['EndpointArn'],
                        endpoint_status=ep['EndpointStatus'],
                        endpoint_config_name=detail.get('EndpointConfigName', ''),
                        creation_time=ep.get('CreationTime'),
                        last_modified_time=ep.get('LastModifiedTime'),
                        production_variants=detail.get('ProductionVariants', [])
                    )
                    endpoints.append(endpoint)
                except Exception as e:  # noqa: E722
                    pass
        
        return endpoints
    
    
    def get_training_jobs(self, days: int = 30) -> List[SageMakerTrainingJob]:
        """Lista Training Jobs recentes"""
        jobs = []
        
        creation_time_after = datetime.now(timezone.utc) - timedelta(days=days)
        
        paginator = self.sagemaker_client.get_paginator('list_training_jobs')
        
        for page in paginator.paginate(CreationTimeAfter=creation_time_after):
            for job in page.get('TrainingJobSummaries', []):
                try:
                    detail = self.sagemaker_client.describe_training_job(
                        TrainingJobName=job['TrainingJobName']
                    )
                    
                    resource_config = detail.get('ResourceConfig', {})
                    
                    training_job = SageMakerTrainingJob(
                        training_job_name=job['TrainingJobName'],
                        training_job_arn=job['TrainingJobArn'],
                        training_job_status=job['TrainingJobStatus'],
                        secondary_status=detail.get('SecondaryStatus', ''),
                        creation_time=job.get('CreationTime'),
                        training_end_time=job.get('TrainingEndTime'),
                        billable_seconds=detail.get('BillableTimeInSeconds', 0),
                        instance_type=resource_config.get('InstanceType', ''),
                        instance_count=resource_config.get('InstanceCount', 1),
                        volume_size_in_gb=resource_config.get('VolumeSizeInGB', 0)
                    )
                    jobs.append(training_job)
                except Exception as e:  # noqa: E722
                    pass
        
        return jobs
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for nb in self.get_notebook_instances():
            res = nb.to_dict()
            res['resource_type'] = 'notebook'
            resources.append(res)
        
        for ep in self.get_endpoints():
            res = ep.to_dict()
            res['resource_type'] = 'endpoint'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de SageMaker"""
        notebooks = self.get_notebook_instances()
        endpoints = self.get_endpoints()
        training_jobs = self.get_training_jobs(days=30)
        
        running_notebooks = len([n for n in notebooks if n.notebook_instance_status == 'InService'])
        active_endpoints = len([e for e in endpoints if e.endpoint_status == 'InService'])
        
        total_training_hours = sum(j.billable_seconds / 3600 for j in training_jobs)
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(notebooks) + len(endpoints),
            metrics={
                'notebook_instances': len(notebooks),
                'running_notebooks': running_notebooks,
                'endpoints': len(endpoints),
                'active_endpoints': active_endpoints,
                'training_jobs_30d': len(training_jobs),
                'total_training_hours_30d': round(total_training_hours, 2)
            },
            period_days=30,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para SageMaker"""
        recommendations = []
        notebooks = self.get_notebook_instances()
        endpoints = self.get_endpoints()
        
        for nb in notebooks:
            if nb.notebook_instance_status == 'InService':
                if nb.last_modified_time:
                    idle_hours = (datetime.now(timezone.utc) - nb.last_modified_time.replace(tzinfo=None)).total_seconds() / 3600
                    if idle_hours > 24:
                        recommendations.append(ServiceRecommendation(
                            resource_id=nb.notebook_instance_name,
                            resource_type='SageMaker Notebook',
                            recommendation_type='IDLE_NOTEBOOK',
                            title=f'Notebook ocioso há {int(idle_hours)}h',
                            description=f'Notebook {nb.notebook_instance_name} ({nb.instance_type}) '
                                       f'está em execução há {int(idle_hours)}h sem modificações. '
                                       f'Notebooks ociosos continuam cobrando.',
                            estimated_savings=50.0,
                            priority='HIGH',
                            action='Parar notebook ocioso'
                        ))
            
            if nb.direct_internet_access == 'Enabled':
                recommendations.append(ServiceRecommendation(
                    resource_id=nb.notebook_instance_name,
                    resource_type='SageMaker Notebook',
                    recommendation_type='SECURITY',
                    title='Acesso direto à internet habilitado',
                    description=f'Notebook {nb.notebook_instance_name} tem acesso direto à internet. '
                               f'Considere usar VPC para maior segurança.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    action='Configurar notebook em VPC'
                ))
        
        for ep in endpoints:
            if ep.endpoint_status == 'InService':
                if len(ep.production_variants) == 1:
                    recommendations.append(ServiceRecommendation(
                        resource_id=ep.endpoint_name,
                        resource_type='SageMaker Endpoint',
                        recommendation_type='SINGLE_VARIANT',
                        title='Endpoint com única variante',
                        description=f'Endpoint {ep.endpoint_name} tem apenas uma production variant. '
                                   f'Considere auto-scaling ou serverless inference.',
                        estimated_savings=30.0,
                        priority='MEDIUM',
                        action='Avaliar Serverless Inference'
                    ))
        
        return recommendations
