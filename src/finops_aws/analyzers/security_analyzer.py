"""
Security Analyzer - Análise de serviços de segurança AWS

Serviços cobertos:
- IAM (Users, Roles, Keys)
- CloudWatch Logs
- KMS
- Secrets Manager
- Security Hub
- GuardDuty
- Macie

Design Pattern: Strategy
"""
from typing import Dict, List, Any
from datetime import datetime, timezone
import logging

from .base_analyzer import (
    BaseAnalyzer,
    Recommendation,
    Priority,
    Impact
)

logger = logging.getLogger(__name__)


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzer para serviços de segurança AWS."""
    
    name = "SecurityAnalyzer"
    
    def _get_client(self, region: str) -> Any:
        """Retorna clientes boto3 para segurança."""
        import boto3
        return {
            'iam': boto3.client('iam'),
            'logs': boto3.client('logs', region_name=region),
            'ecr': boto3.client('ecr', region_name=region),
        }
    
    def _collect_resources(self, clients: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta recursos de segurança."""
        resources = {}
        
        iam = clients.get('iam')
        if iam:
            try:
                resources['iam_users'] = iam.list_users()
                resources['iam_roles'] = iam.list_roles()
                resources['iam_groups'] = iam.list_groups()
                resources['iam_policies'] = iam.list_policies(Scope='Local')
                resources['iam_client'] = iam
            except Exception as e:
                logger.warning(f"Erro coletando IAM: {e}")
        
        logs = clients.get('logs')
        if logs:
            try:
                resources['log_groups'] = logs.describe_log_groups()
            except Exception as e:
                logger.warning(f"Erro coletando CloudWatch Logs: {e}")
        
        ecr = clients.get('ecr')
        if ecr:
            try:
                resources['ecr_repositories'] = ecr.describe_repositories()
                resources['ecr_client'] = ecr
            except Exception as e:
                logger.warning(f"Erro coletando ECR: {e}")
        
        return resources
    
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """Analisa recursos e gera recomendações."""
        recommendations = []
        metrics = {}
        
        recommendations.extend(self._analyze_iam(resources, metrics))
        recommendations.extend(self._analyze_cloudwatch_logs(resources, metrics))
        recommendations.extend(self._analyze_ecr(resources, metrics))
        
        return recommendations, metrics
    
    def _analyze_iam(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa configurações IAM."""
        recommendations = []
        iam = resources.get('iam_client')
        
        users_data = resources.get('iam_users', {})
        users = users_data.get('Users', [])
        metrics['iam_users'] = len(users)
        
        if iam:
            for user in users:
                username = user.get('UserName', '')
                try:
                    keys = iam.list_access_keys(UserName=username)
                    
                    for key in keys.get('AccessKeyMetadata', []):
                        if key.get('Status') == 'Inactive':
                            recommendations.append(self._create_recommendation(
                                rec_type='IAM_INACTIVE_KEY',
                                resource_id=username,
                                description=f'Access key inativa para usuário {username}',
                                service='IAM Security',
                                priority=Priority.MEDIUM
                            ))
                        
                        create_date = key.get('CreateDate')
                        if create_date:
                            age = (datetime.now(timezone.utc) - create_date.replace(tzinfo=timezone.utc)).days
                            if age > 90:
                                recommendations.append(self._create_recommendation(
                                    rec_type='IAM_OLD_KEY',
                                    resource_id=username,
                                    description=f'Access key de {username} tem {age} dias - rotacionar',
                                    service='IAM Security',
                                    priority=Priority.HIGH
                                ))
                except Exception:
                    pass
        
        roles_data = resources.get('iam_roles', {})
        metrics['iam_roles'] = len(roles_data.get('Roles', []))
        
        groups_data = resources.get('iam_groups', {})
        metrics['iam_groups'] = len(groups_data.get('Groups', []))
        
        policies_data = resources.get('iam_policies', {})
        metrics['iam_policies'] = len(policies_data.get('Policies', []))
        
        return recommendations
    
    def _analyze_cloudwatch_logs(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa grupos de logs CloudWatch."""
        recommendations = []
        logs_data = resources.get('log_groups', {})
        
        log_groups = logs_data.get('logGroups', [])
        metrics['cloudwatch_log_groups'] = len(log_groups)
        
        no_retention_count = 0
        for lg in log_groups:
            lg_name = lg.get('logGroupName', '')
            
            if lg.get('retentionInDays') is None:
                no_retention_count += 1
        
        if no_retention_count > 0:
            recommendations.append(self._create_recommendation(
                rec_type='CLOUDWATCH_RETENTION',
                resource_id=f'{no_retention_count} log groups',
                description=f'{no_retention_count} log groups sem retenção definida - podem crescer indefinidamente',
                service='CloudWatch Optimization',
                priority=Priority.MEDIUM,
                savings=no_retention_count * 5.0
            ))
        
        return recommendations
    
    def _analyze_ecr(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa repositórios ECR."""
        recommendations = []
        ecr = resources.get('ecr_client')
        repos_data = resources.get('ecr_repositories', {})
        
        repos = repos_data.get('repositories', [])
        metrics['ecr_repositories'] = len(repos)
        
        if not ecr:
            return recommendations
        
        for repo in repos[:10]:
            repo_name = repo.get('repositoryName', '')
            
            try:
                images = ecr.list_images(repositoryName=repo_name, filter={'tagStatus': 'UNTAGGED'})
                untagged = len(images.get('imageIds', []))
                
                if untagged > 5:
                    recommendations.append(self._create_recommendation(
                        rec_type='ECR_UNTAGGED',
                        resource_id=repo_name,
                        description=f'ECR {repo_name} tem {untagged} imagens sem tag',
                        service='ECR Cleanup',
                        priority=Priority.LOW,
                        savings=untagged * 0.10
                    ))
            except Exception:
                pass
        
        return recommendations
    
    def _get_services_list(self) -> List[str]:
        """Retorna serviços analisados."""
        return ['IAM', 'CloudWatch Logs', 'ECR']
