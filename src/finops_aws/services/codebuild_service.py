"""
AWS CodeBuild FinOps Service

Análise de projetos de build, custos de compute e recomendações de otimização.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class BuildProject:
    """Representa um projeto CodeBuild"""
    name: str
    arn: Optional[str] = None
    description: Optional[str] = None
    source_type: str = 'NO_SOURCE'
    environment_type: str = 'LINUX_CONTAINER'
    compute_type: str = 'BUILD_GENERAL1_SMALL'
    image: str = 'aws/codebuild/standard:5.0'
    timeout_in_minutes: int = 60
    queued_timeout_in_minutes: int = 480
    badge_enabled: bool = False
    concurrent_build_limit: Optional[int] = None
    cache_type: str = 'NO_CACHE'
    encryption_key: Optional[str] = None
    vpc_config: Dict = field(default_factory=dict)
    logs_config: Dict = field(default_factory=dict)
    created: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    
    @property
    def is_small_compute(self) -> bool:
        return 'SMALL' in self.compute_type
    
    @property
    def is_medium_compute(self) -> bool:
        return 'MEDIUM' in self.compute_type
    
    @property
    def is_large_compute(self) -> bool:
        return 'LARGE' in self.compute_type or '2XLARGE' in self.compute_type
    
    @property
    def is_arm_based(self) -> bool:
        return 'ARM' in self.environment_type
    
    @property
    def is_gpu_enabled(self) -> bool:
        return 'GPU' in self.compute_type
    
    @property
    def has_cache(self) -> bool:
        return self.cache_type != 'NO_CACHE'
    
    @property
    def has_vpc(self) -> bool:
        return bool(self.vpc_config.get('vpcId'))
    
    @property
    def has_encryption(self) -> bool:
        return self.encryption_key is not None
    
    @property
    def has_cloudwatch_logs(self) -> bool:
        cw_logs = self.logs_config.get('cloudWatchLogs', {})
        return cw_logs.get('status') == 'ENABLED'
    
    @property
    def has_s3_logs(self) -> bool:
        s3_logs = self.logs_config.get('s3Logs', {})
        return s3_logs.get('status') == 'ENABLED'
    
    @property
    def has_concurrent_limit(self) -> bool:
        return self.concurrent_build_limit is not None
    
    @property
    def timeout_hours(self) -> float:
        return self.timeout_in_minutes / 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'description': self.description,
            'source_type': self.source_type,
            'environment_type': self.environment_type,
            'compute_type': self.compute_type,
            'image': self.image,
            'timeout_in_minutes': self.timeout_in_minutes,
            'queued_timeout_in_minutes': self.queued_timeout_in_minutes,
            'badge_enabled': self.badge_enabled,
            'concurrent_build_limit': self.concurrent_build_limit,
            'cache_type': self.cache_type,
            'is_small_compute': self.is_small_compute,
            'is_medium_compute': self.is_medium_compute,
            'is_large_compute': self.is_large_compute,
            'is_arm_based': self.is_arm_based,
            'is_gpu_enabled': self.is_gpu_enabled,
            'has_cache': self.has_cache,
            'has_vpc': self.has_vpc,
            'has_encryption': self.has_encryption,
            'has_cloudwatch_logs': self.has_cloudwatch_logs,
            'has_s3_logs': self.has_s3_logs,
            'has_concurrent_limit': self.has_concurrent_limit,
            'timeout_hours': self.timeout_hours
        }


@dataclass
class BuildHistory:
    """Representa o histórico de builds de um projeto"""
    project_name: str
    build_id: str
    build_number: int = 0
    build_status: str = 'IN_PROGRESS'
    source_version: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    phases: List[Dict] = field(default_factory=list)
    
    @property
    def is_successful(self) -> bool:
        return self.build_status == 'SUCCEEDED'
    
    @property
    def is_failed(self) -> bool:
        return self.build_status == 'FAILED'
    
    @property
    def is_in_progress(self) -> bool:
        return self.build_status == 'IN_PROGRESS'
    
    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_name': self.project_name,
            'build_id': self.build_id,
            'build_number': self.build_number,
            'build_status': self.build_status,
            'source_version': self.source_version,
            'duration_seconds': self.duration_seconds,
            'duration_minutes': self.duration_minutes,
            'is_successful': self.is_successful,
            'is_failed': self.is_failed,
            'is_in_progress': self.is_in_progress
        }


@dataclass
class ReportGroup:
    """Representa um grupo de relatórios CodeBuild"""
    name: str
    arn: Optional[str] = None
    type: str = 'TEST'
    export_config_type: str = 'NO_EXPORT'
    created: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    status: str = 'ACTIVE'
    
    @property
    def is_test_report(self) -> bool:
        return self.type == 'TEST'
    
    @property
    def is_code_coverage(self) -> bool:
        return self.type == 'CODE_COVERAGE'
    
    @property
    def exports_to_s3(self) -> bool:
        return self.export_config_type == 'S3'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'type': self.type,
            'export_config_type': self.export_config_type,
            'status': self.status,
            'is_test_report': self.is_test_report,
            'is_code_coverage': self.is_code_coverage,
            'exports_to_s3': self.exports_to_s3
        }


class CodeBuildService(BaseAWSService):
    """Serviço FinOps para AWS CodeBuild"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._codebuild_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "codebuild"
    
    @property
    def codebuild_client(self):
        if self._codebuild_client is None:
            if self._client_factory:
                self._codebuild_client = self._client_factory.get_client('codebuild')
            else:
                import boto3
                self._codebuild_client = boto3.client('codebuild')
        return self._codebuild_client
    
    def health_check(self) -> bool:
        try:
            self.codebuild_client.list_projects(maxResults=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_projects(self) -> List[BuildProject]:
        projects = []
        try:
            paginator = self.codebuild_client.get_paginator('list_projects')
            project_names = []
            
            for page in paginator.paginate():
                project_names.extend(page.get('projects', []))
            
            if project_names:
                for i in range(0, len(project_names), 100):
                    batch = project_names[i:i+100]
                    response = self.codebuild_client.batch_get_projects(names=batch)
                    
                    for project in response.get('projects', []):
                        env = project.get('environment', {})
                        projects.append(BuildProject(
                            name=project.get('name', ''),
                            arn=project.get('arn'),
                            description=project.get('description'),
                            source_type=project.get('source', {}).get('type', 'NO_SOURCE'),
                            environment_type=env.get('type', 'LINUX_CONTAINER'),
                            compute_type=env.get('computeType', 'BUILD_GENERAL1_SMALL'),
                            image=env.get('image', ''),
                            timeout_in_minutes=project.get('timeoutInMinutes', 60),
                            queued_timeout_in_minutes=project.get('queuedTimeoutInMinutes', 480),
                            badge_enabled=project.get('badge', {}).get('badgeEnabled', False),
                            concurrent_build_limit=project.get('concurrentBuildLimit'),
                            cache_type=project.get('cache', {}).get('type', 'NO_CACHE'),
                            encryption_key=project.get('encryptionKey'),
                            vpc_config=project.get('vpcConfig', {}),
                            logs_config=project.get('logsConfig', {}),
                            created=project.get('created'),
                            last_modified=project.get('lastModified')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar projetos CodeBuild: {e}")
        
        return projects
    
    def get_build_history(self, project_name: str, max_results: int = 10) -> List[BuildHistory]:
        builds = []
        try:
            response = self.codebuild_client.list_builds_for_project(
                projectName=project_name,
                sortOrder='DESCENDING'
            )
            
            build_ids = response.get('ids', [])[:max_results]
            
            if build_ids:
                details = self.codebuild_client.batch_get_builds(ids=build_ids)
                
                for build in details.get('builds', []):
                    start_time = build.get('startTime')
                    end_time = build.get('endTime')
                    duration = 0
                    if start_time and end_time:
                        duration = int((end_time - start_time).total_seconds())
                    
                    builds.append(BuildHistory(
                        project_name=project_name,
                        build_id=build.get('id', ''),
                        build_number=build.get('buildNumber', 0),
                        build_status=build.get('buildStatus', 'IN_PROGRESS'),
                        source_version=build.get('sourceVersion'),
                        start_time=start_time,
                        end_time=end_time,
                        duration_seconds=duration,
                        phases=build.get('phases', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de builds: {e}")
        
        return builds
    
    def get_report_groups(self) -> List[ReportGroup]:
        report_groups = []
        try:
            paginator = self.codebuild_client.get_paginator('list_report_groups')
            group_arns = []
            
            for page in paginator.paginate():
                group_arns.extend(page.get('reportGroups', []))
            
            if group_arns:
                for i in range(0, len(group_arns), 100):
                    batch = group_arns[i:i+100]
                    response = self.codebuild_client.batch_get_report_groups(reportGroupArns=batch)
                    
                    for group in response.get('reportGroups', []):
                        export_config = group.get('exportConfig', {})
                        report_groups.append(ReportGroup(
                            name=group.get('name', ''),
                            arn=group.get('arn'),
                            type=group.get('type', 'TEST'),
                            export_config_type=export_config.get('exportConfigType', 'NO_EXPORT'),
                            created=group.get('created'),
                            last_modified=group.get('lastModified'),
                            status=group.get('status', 'ACTIVE')
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar report groups: {e}")
        
        return report_groups
    
    def get_resources(self) -> Dict[str, Any]:
        projects = self.get_projects()
        report_groups = self.get_report_groups()
        
        return {
            'projects': [p.to_dict() for p in projects],
            'report_groups': [r.to_dict() for r in report_groups],
            'summary': {
                'total_projects': len(projects),
                'total_report_groups': len(report_groups),
                'projects_with_cache': sum(1 for p in projects if p.has_cache),
                'projects_with_vpc': sum(1 for p in projects if p.has_vpc),
                'projects_with_encryption': sum(1 for p in projects if p.has_encryption),
                'large_compute_projects': sum(1 for p in projects if p.is_large_compute),
                'gpu_enabled_projects': sum(1 for p in projects if p.is_gpu_enabled),
                'arm_based_projects': sum(1 for p in projects if p.is_arm_based)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        projects = self.get_projects()
        
        metrics = {
            'total_projects': len(projects),
            'compute_distribution': {
                'small': sum(1 for p in projects if p.is_small_compute),
                'medium': sum(1 for p in projects if p.is_medium_compute),
                'large': sum(1 for p in projects if p.is_large_compute)
            },
            'environment_types': {},
            'cache_usage': sum(1 for p in projects if p.has_cache),
            'vpc_integration': sum(1 for p in projects if p.has_vpc),
            'encryption_enabled': sum(1 for p in projects if p.has_encryption)
        }
        
        for project in projects:
            env_type = project.environment_type
            metrics['environment_types'][env_type] = metrics['environment_types'].get(env_type, 0) + 1
        
        return metrics
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        projects = self.get_projects()
        
        for project in projects:
            if project.is_large_compute and not project.has_cache:
                recommendations.append({
                    'resource_id': project.name,
                    'resource_type': 'CodeBuild Project',
                    'title': 'Habilitar cache para projeto com compute grande',
                    'description': f'Projeto {project.name} usa compute {project.compute_type} sem cache. Cache pode reduzir tempo e custo de build.',
                    'action': 'Habilitar cache S3 ou local para reduzir tempo de build',
                    'estimated_savings': 'Médio',
                    'priority': 'HIGH'
                })
            
            if project.is_gpu_enabled:
                recommendations.append({
                    'resource_id': project.name,
                    'resource_type': 'CodeBuild Project',
                    'title': 'Revisar necessidade de GPU',
                    'description': f'Projeto {project.name} usa GPU ({project.compute_type}). GPUs têm custo elevado.',
                    'action': 'Verificar se GPU é realmente necessária para o build',
                    'estimated_savings': 'Alto',
                    'priority': 'HIGH'
                })
            
            if not project.is_arm_based and project.is_small_compute:
                recommendations.append({
                    'resource_id': project.name,
                    'resource_type': 'CodeBuild Project',
                    'title': 'Considerar migração para ARM',
                    'description': f'Projeto {project.name} pode se beneficiar de instâncias ARM (Graviton) com melhor custo-benefício.',
                    'action': 'Testar build com ARM_CONTAINER para reduzir custos',
                    'estimated_savings': 'Baixo a Médio',
                    'priority': 'MEDIUM'
                })
            
            if project.timeout_hours > 4:
                recommendations.append({
                    'resource_id': project.name,
                    'resource_type': 'CodeBuild Project',
                    'title': 'Timeout excessivo configurado',
                    'description': f'Projeto {project.name} tem timeout de {project.timeout_hours:.1f} horas. Builds longos aumentam custos.',
                    'action': 'Revisar e reduzir timeout se builds normalmente terminam mais rápido',
                    'estimated_savings': 'Baixo',
                    'priority': 'LOW'
                })
            
            if not project.has_cloudwatch_logs and not project.has_s3_logs:
                recommendations.append({
                    'resource_id': project.name,
                    'resource_type': 'CodeBuild Project',
                    'title': 'Logs não configurados',
                    'description': f'Projeto {project.name} não tem logs configurados. Dificulta troubleshooting.',
                    'action': 'Habilitar CloudWatch Logs ou S3 Logs para auditoria',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
        
        return recommendations
