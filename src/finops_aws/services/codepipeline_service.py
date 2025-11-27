"""
AWS CodePipeline FinOps Service

Análise de pipelines de CI/CD, execuções e recomendações de otimização.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Pipeline:
    """Representa um pipeline CodePipeline"""
    name: str
    arn: Optional[str] = None
    role_arn: Optional[str] = None
    version: int = 1
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    stages: List[Dict] = field(default_factory=list)
    pipeline_type: str = 'V1'
    execution_mode: str = 'SUPERSEDED'
    
    @property
    def stage_count(self) -> int:
        return len(self.stages)
    
    @property
    def action_count(self) -> int:
        count = 0
        for stage in self.stages:
            count += len(stage.get('actions', []))
        return count
    
    @property
    def is_v2_pipeline(self) -> bool:
        return self.pipeline_type == 'V2'
    
    @property
    def uses_parallel_execution(self) -> bool:
        return self.execution_mode == 'PARALLEL'
    
    @property
    def uses_queued_execution(self) -> bool:
        return self.execution_mode == 'QUEUED'
    
    @property
    def has_manual_approval(self) -> bool:
        for stage in self.stages:
            for action in stage.get('actions', []):
                if action.get('actionTypeId', {}).get('category') == 'Approval':
                    return True
        return False
    
    @property
    def has_deploy_stage(self) -> bool:
        for stage in self.stages:
            for action in stage.get('actions', []):
                if action.get('actionTypeId', {}).get('category') == 'Deploy':
                    return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'version': self.version,
            'stage_count': self.stage_count,
            'action_count': self.action_count,
            'pipeline_type': self.pipeline_type,
            'execution_mode': self.execution_mode,
            'is_v2_pipeline': self.is_v2_pipeline,
            'uses_parallel_execution': self.uses_parallel_execution,
            'uses_queued_execution': self.uses_queued_execution,
            'has_manual_approval': self.has_manual_approval,
            'has_deploy_stage': self.has_deploy_stage
        }


@dataclass
class PipelineExecution:
    """Representa uma execução de pipeline"""
    pipeline_name: str
    execution_id: str
    status: str = 'InProgress'
    status_summary: Optional[str] = None
    start_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    trigger_type: str = 'StartPipelineExecution'
    
    @property
    def is_successful(self) -> bool:
        return self.status == 'Succeeded'
    
    @property
    def is_failed(self) -> bool:
        return self.status == 'Failed'
    
    @property
    def is_in_progress(self) -> bool:
        return self.status == 'InProgress'
    
    @property
    def is_stopped(self) -> bool:
        return self.status in ['Stopped', 'Stopping']
    
    @property
    def is_manual_trigger(self) -> bool:
        return self.trigger_type == 'StartPipelineExecution'
    
    @property
    def is_webhook_trigger(self) -> bool:
        return self.trigger_type == 'Webhook'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pipeline_name': self.pipeline_name,
            'execution_id': self.execution_id,
            'status': self.status,
            'status_summary': self.status_summary,
            'trigger_type': self.trigger_type,
            'is_successful': self.is_successful,
            'is_failed': self.is_failed,
            'is_in_progress': self.is_in_progress,
            'is_stopped': self.is_stopped,
            'is_manual_trigger': self.is_manual_trigger,
            'is_webhook_trigger': self.is_webhook_trigger
        }


@dataclass
class Webhook:
    """Representa um webhook de pipeline"""
    name: str
    arn: Optional[str] = None
    pipeline_name: str = ''
    target_action: str = ''
    authentication: str = 'GITHUB_HMAC'
    filters: List[Dict] = field(default_factory=list)
    url: Optional[str] = None
    
    @property
    def is_github_webhook(self) -> bool:
        return 'GITHUB' in self.authentication
    
    @property
    def has_filters(self) -> bool:
        return len(self.filters) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'pipeline_name': self.pipeline_name,
            'target_action': self.target_action,
            'authentication': self.authentication,
            'filter_count': len(self.filters),
            'is_github_webhook': self.is_github_webhook,
            'has_filters': self.has_filters
        }


class CodePipelineService(BaseAWSService):
    """Serviço FinOps para AWS CodePipeline"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._codepipeline_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "codepipeline"
    
    @property
    def codepipeline_client(self):
        if self._codepipeline_client is None:
            if self._client_factory:
                self._codepipeline_client = self._client_factory.get_client('codepipeline')
            else:
                import boto3
                self._codepipeline_client = boto3.client('codepipeline')
        return self._codepipeline_client
    
    def health_check(self) -> bool:
        try:
            self.codepipeline_client.list_pipelines(maxResults=1)
            return True
        except Exception:
            return False
    
    def get_pipelines(self) -> List[Pipeline]:
        pipelines = []
        try:
            paginator = self.codepipeline_client.get_paginator('list_pipelines')
            
            for page in paginator.paginate():
                for pipeline_summary in page.get('pipelines', []):
                    pipeline_name = pipeline_summary.get('name', '')
                    
                    try:
                        response = self.codepipeline_client.get_pipeline(name=pipeline_name)
                        pipeline_data = response.get('pipeline', {})
                        metadata = response.get('metadata', {})
                        
                        pipelines.append(Pipeline(
                            name=pipeline_data.get('name', pipeline_name),
                            arn=metadata.get('pipelineArn'),
                            role_arn=pipeline_data.get('roleArn'),
                            version=pipeline_data.get('version', 1),
                            created=metadata.get('created'),
                            updated=metadata.get('updated'),
                            stages=pipeline_data.get('stages', []),
                            pipeline_type=pipeline_data.get('pipelineType', 'V1'),
                            execution_mode=pipeline_data.get('executionMode', 'SUPERSEDED')
                        ))
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter detalhes do pipeline {pipeline_name}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar pipelines: {e}")
        
        return pipelines
    
    def get_pipeline_executions(self, pipeline_name: str, max_results: int = 10) -> List[PipelineExecution]:
        executions = []
        try:
            response = self.codepipeline_client.list_pipeline_executions(
                pipelineName=pipeline_name,
                maxResults=max_results
            )
            
            for execution in response.get('pipelineExecutionSummaries', []):
                trigger = execution.get('trigger', {})
                executions.append(PipelineExecution(
                    pipeline_name=pipeline_name,
                    execution_id=execution.get('pipelineExecutionId', ''),
                    status=execution.get('status', 'InProgress'),
                    status_summary=execution.get('statusSummary'),
                    start_time=execution.get('startTime'),
                    last_update_time=execution.get('lastUpdateTime'),
                    trigger_type=trigger.get('triggerType', 'StartPipelineExecution')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar execuções do pipeline {pipeline_name}: {e}")
        
        return executions
    
    def get_webhooks(self) -> List[Webhook]:
        webhooks = []
        try:
            paginator = self.codepipeline_client.get_paginator('list_webhooks')
            
            for page in paginator.paginate():
                for webhook in page.get('webhooks', []):
                    definition = webhook.get('definition', {})
                    webhooks.append(Webhook(
                        name=definition.get('name', ''),
                        arn=webhook.get('arn'),
                        pipeline_name=definition.get('targetPipeline', ''),
                        target_action=definition.get('targetAction', ''),
                        authentication=definition.get('authentication', 'GITHUB_HMAC'),
                        filters=definition.get('filters', []),
                        url=webhook.get('url')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar webhooks: {e}")
        
        return webhooks
    
    def get_resources(self) -> Dict[str, Any]:
        pipelines = self.get_pipelines()
        webhooks = self.get_webhooks()
        
        return {
            'pipelines': [p.to_dict() for p in pipelines],
            'webhooks': [w.to_dict() for w in webhooks],
            'summary': {
                'total_pipelines': len(pipelines),
                'total_webhooks': len(webhooks),
                'v2_pipelines': sum(1 for p in pipelines if p.is_v2_pipeline),
                'v1_pipelines': sum(1 for p in pipelines if not p.is_v2_pipeline),
                'pipelines_with_manual_approval': sum(1 for p in pipelines if p.has_manual_approval),
                'pipelines_with_deploy': sum(1 for p in pipelines if p.has_deploy_stage),
                'total_stages': sum(p.stage_count for p in pipelines),
                'total_actions': sum(p.action_count for p in pipelines)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        pipelines = self.get_pipelines()
        
        metrics = {
            'total_pipelines': len(pipelines),
            'pipeline_types': {
                'v1': sum(1 for p in pipelines if not p.is_v2_pipeline),
                'v2': sum(1 for p in pipelines if p.is_v2_pipeline)
            },
            'execution_modes': {},
            'average_stages': sum(p.stage_count for p in pipelines) / max(len(pipelines), 1),
            'average_actions': sum(p.action_count for p in pipelines) / max(len(pipelines), 1),
            'manual_approval_usage': sum(1 for p in pipelines if p.has_manual_approval)
        }
        
        for pipeline in pipelines:
            mode = pipeline.execution_mode
            metrics['execution_modes'][mode] = metrics['execution_modes'].get(mode, 0) + 1
        
        return metrics
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        pipelines = self.get_pipelines()
        
        for pipeline in pipelines:
            if not pipeline.is_v2_pipeline:
                recommendations.append({
                    'resource_id': pipeline.name,
                    'resource_type': 'CodePipeline',
                    'title': 'Migrar para Pipeline V2',
                    'description': f'Pipeline {pipeline.name} usa versão V1. V2 oferece mais recursos e melhor precificação.',
                    'action': 'Migrar para Pipeline V2 para acessar novos recursos',
                    'estimated_savings': 'Médio',
                    'priority': 'MEDIUM'
                })
            
            if pipeline.stage_count > 10:
                recommendations.append({
                    'resource_id': pipeline.name,
                    'resource_type': 'CodePipeline',
                    'title': 'Pipeline com muitos stages',
                    'description': f'Pipeline {pipeline.name} tem {pipeline.stage_count} stages. Considere simplificar.',
                    'action': 'Consolidar stages para reduzir complexidade e tempo de execução',
                    'estimated_savings': 'Baixo',
                    'priority': 'LOW'
                })
            
            if not pipeline.has_deploy_stage:
                recommendations.append({
                    'resource_id': pipeline.name,
                    'resource_type': 'CodePipeline',
                    'title': 'Pipeline sem stage de deploy',
                    'description': f'Pipeline {pipeline.name} não tem stage de deploy configurado.',
                    'action': 'Verificar se pipeline está completo ou é apenas para CI',
                    'estimated_savings': 'N/A',
                    'priority': 'LOW'
                })
            
            executions = self.get_pipeline_executions(pipeline.name, max_results=20)
            failed_count = sum(1 for e in executions if e.is_failed)
            if len(executions) > 0 and failed_count / len(executions) > 0.3:
                recommendations.append({
                    'resource_id': pipeline.name,
                    'resource_type': 'CodePipeline',
                    'title': 'Alta taxa de falhas',
                    'description': f'Pipeline {pipeline.name} tem {failed_count}/{len(executions)} execuções falhando (>{30}%).',
                    'action': 'Investigar causas de falhas para reduzir re-execuções e custos',
                    'estimated_savings': 'Médio',
                    'priority': 'HIGH'
                })
        
        return recommendations
