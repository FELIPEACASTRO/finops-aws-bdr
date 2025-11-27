"""
AWS CodeCommit FinOps Service

Análise de repositórios, branches e recomendações de otimização.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Repository:
    """Representa um repositório CodeCommit"""
    name: str
    repository_id: Optional[str] = None
    arn: Optional[str] = None
    description: Optional[str] = None
    clone_url_http: Optional[str] = None
    clone_url_ssh: Optional[str] = None
    default_branch: str = 'main'
    creation_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    kms_key_id: Optional[str] = None
    
    @property
    def has_encryption(self) -> bool:
        return self.kms_key_id is not None
    
    @property
    def has_description(self) -> bool:
        return bool(self.description)
    
    @property
    def days_since_modified(self) -> int:
        if self.last_modified_date:
            delta = datetime.now(self.last_modified_date.tzinfo) - self.last_modified_date
            return delta.days
        return 0
    
    @property
    def is_stale(self) -> bool:
        return self.days_since_modified > 180
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'repository_id': self.repository_id,
            'arn': self.arn,
            'description': self.description,
            'default_branch': self.default_branch,
            'has_encryption': self.has_encryption,
            'has_description': self.has_description,
            'days_since_modified': self.days_since_modified,
            'is_stale': self.is_stale
        }


@dataclass
class Branch:
    """Representa uma branch de repositório"""
    name: str
    repository_name: str
    commit_id: Optional[str] = None
    
    @property
    def is_main_branch(self) -> bool:
        return self.name in ['main', 'master']
    
    @property
    def is_develop_branch(self) -> bool:
        return self.name in ['develop', 'development', 'dev']
    
    @property
    def is_feature_branch(self) -> bool:
        return self.name.startswith('feature/')
    
    @property
    def is_release_branch(self) -> bool:
        return self.name.startswith('release/')
    
    @property
    def is_hotfix_branch(self) -> bool:
        return self.name.startswith('hotfix/')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'repository_name': self.repository_name,
            'commit_id': self.commit_id,
            'is_main_branch': self.is_main_branch,
            'is_develop_branch': self.is_develop_branch,
            'is_feature_branch': self.is_feature_branch,
            'is_release_branch': self.is_release_branch,
            'is_hotfix_branch': self.is_hotfix_branch
        }


@dataclass
class PullRequest:
    """Representa um pull request"""
    pull_request_id: str
    title: str
    repository_name: str
    author_arn: Optional[str] = None
    status: str = 'OPEN'
    creation_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    source_branch: str = ''
    destination_branch: str = ''
    merge_metadata: Dict = field(default_factory=dict)
    
    @property
    def is_open(self) -> bool:
        return self.status == 'OPEN'
    
    @property
    def is_closed(self) -> bool:
        return self.status == 'CLOSED'
    
    @property
    def is_merged(self) -> bool:
        return self.merge_metadata.get('isMerged', False)
    
    @property
    def days_open(self) -> int:
        if self.creation_date and self.is_open:
            delta = datetime.now(self.creation_date.tzinfo) - self.creation_date
            return delta.days
        return 0
    
    @property
    def is_stale_pr(self) -> bool:
        return self.is_open and self.days_open > 30
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pull_request_id': self.pull_request_id,
            'title': self.title,
            'repository_name': self.repository_name,
            'status': self.status,
            'source_branch': self.source_branch,
            'destination_branch': self.destination_branch,
            'is_open': self.is_open,
            'is_closed': self.is_closed,
            'is_merged': self.is_merged,
            'days_open': self.days_open,
            'is_stale_pr': self.is_stale_pr
        }


@dataclass 
class ApprovalRule:
    """Representa uma regra de aprovação"""
    name: str
    rule_content: Dict = field(default_factory=dict)
    creation_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    
    @property
    def approvers_required(self) -> int:
        return self.rule_content.get('minApprovalsCount', 0)
    
    @property
    def has_pool_members(self) -> bool:
        return len(self.rule_content.get('approvalPoolMembers', [])) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'approvers_required': self.approvers_required,
            'has_pool_members': self.has_pool_members
        }


class CodeCommitService(BaseAWSService):
    """Serviço FinOps para AWS CodeCommit"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._codecommit_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "codecommit"
    
    @property
    def codecommit_client(self):
        if self._codecommit_client is None:
            if self._client_factory:
                self._codecommit_client = self._client_factory.get_client('codecommit')
            else:
                import boto3
                self._codecommit_client = boto3.client('codecommit')
        return self._codecommit_client
    
    def health_check(self) -> bool:
        try:
            self.codecommit_client.list_repositories(maxResults=1)
            return True
        except Exception:
            return False
    
    def get_repositories(self) -> List[Repository]:
        repositories = []
        try:
            paginator = self.codecommit_client.get_paginator('list_repositories')
            
            for page in paginator.paginate():
                for repo_summary in page.get('repositories', []):
                    repo_name = repo_summary.get('repositoryName', '')
                    
                    try:
                        response = self.codecommit_client.get_repository(repositoryName=repo_name)
                        repo = response.get('repositoryMetadata', {})
                        
                        repositories.append(Repository(
                            name=repo.get('repositoryName', repo_name),
                            repository_id=repo.get('repositoryId'),
                            arn=repo.get('Arn'),
                            description=repo.get('repositoryDescription'),
                            clone_url_http=repo.get('cloneUrlHttp'),
                            clone_url_ssh=repo.get('cloneUrlSsh'),
                            default_branch=repo.get('defaultBranch', 'main'),
                            creation_date=repo.get('creationDate'),
                            last_modified_date=repo.get('lastModifiedDate'),
                            kms_key_id=repo.get('kmsKeyId')
                        ))
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter detalhes do repositório {repo_name}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar repositórios: {e}")
        
        return repositories
    
    def get_branches(self, repository_name: str) -> List[Branch]:
        branches = []
        try:
            paginator = self.codecommit_client.get_paginator('list_branches')
            
            for page in paginator.paginate(repositoryName=repository_name):
                for branch_name in page.get('branches', []):
                    try:
                        response = self.codecommit_client.get_branch(
                            repositoryName=repository_name,
                            branchName=branch_name
                        )
                        branch = response.get('branch', {})
                        
                        branches.append(Branch(
                            name=branch.get('branchName', branch_name),
                            repository_name=repository_name,
                            commit_id=branch.get('commitId')
                        ))
                    except Exception:
                        branches.append(Branch(
                            name=branch_name,
                            repository_name=repository_name
                        ))
        except Exception as e:
            self.logger.error(f"Erro ao listar branches para {repository_name}: {e}")
        
        return branches
    
    def get_pull_requests(self, repository_name: str, status: str = 'OPEN') -> List[PullRequest]:
        pull_requests = []
        try:
            paginator = self.codecommit_client.get_paginator('list_pull_requests')
            
            for page in paginator.paginate(repositoryName=repository_name, pullRequestStatus=status):
                for pr_id in page.get('pullRequestIds', []):
                    try:
                        response = self.codecommit_client.get_pull_request(pullRequestId=pr_id)
                        pr = response.get('pullRequest', {})
                        
                        targets = pr.get('pullRequestTargets', [{}])
                        target = targets[0] if targets else {}
                        
                        pull_requests.append(PullRequest(
                            pull_request_id=pr.get('pullRequestId', pr_id),
                            title=pr.get('title', ''),
                            repository_name=target.get('repositoryName', repository_name),
                            author_arn=pr.get('authorArn'),
                            status=pr.get('pullRequestStatus', 'OPEN'),
                            creation_date=pr.get('creationDate'),
                            last_activity_date=pr.get('lastActivityDate'),
                            source_branch=target.get('sourceReference', ''),
                            destination_branch=target.get('destinationReference', ''),
                            merge_metadata=target.get('mergeMetadata', {})
                        ))
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter PR {pr_id}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar PRs para {repository_name}: {e}")
        
        return pull_requests
    
    def get_approval_rule_templates(self) -> List[ApprovalRule]:
        templates = []
        try:
            response = self.codecommit_client.list_approval_rule_templates()
            
            for template_name in response.get('approvalRuleTemplateNames', []):
                try:
                    details = self.codecommit_client.get_approval_rule_template(
                        approvalRuleTemplateName=template_name
                    )
                    template = details.get('approvalRuleTemplate', {})
                    
                    import json
                    rule_content = {}
                    try:
                        rule_content = json.loads(template.get('approvalRuleTemplateContent', '{}'))
                    except json.JSONDecodeError:
                        pass
                    
                    templates.append(ApprovalRule(
                        name=template.get('approvalRuleTemplateName', template_name),
                        rule_content=rule_content,
                        creation_date=template.get('creationDate'),
                        last_modified_date=template.get('lastModifiedDate')
                    ))
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Erro ao listar approval rule templates: {e}")
        
        return templates
    
    def get_resources(self) -> Dict[str, Any]:
        repositories = self.get_repositories()
        all_branches = []
        all_open_prs = []
        
        for repo in repositories[:20]:
            branches = self.get_branches(repo.name)
            all_branches.extend(branches)
            
            prs = self.get_pull_requests(repo.name, status='OPEN')
            all_open_prs.extend(prs)
        
        approval_templates = self.get_approval_rule_templates()
        
        return {
            'repositories': [r.to_dict() for r in repositories],
            'branches': [b.to_dict() for b in all_branches],
            'open_pull_requests': [p.to_dict() for p in all_open_prs],
            'approval_templates': [a.to_dict() for a in approval_templates],
            'summary': {
                'total_repositories': len(repositories),
                'total_branches': len(all_branches),
                'open_pull_requests': len(all_open_prs),
                'stale_prs': sum(1 for p in all_open_prs if p.is_stale_pr),
                'repositories_with_encryption': sum(1 for r in repositories if r.has_encryption),
                'stale_repositories': sum(1 for r in repositories if r.is_stale),
                'approval_templates': len(approval_templates)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        repositories = self.get_repositories()
        
        metrics = {
            'total_repositories': len(repositories),
            'repositories_with_encryption': sum(1 for r in repositories if r.has_encryption),
            'repositories_with_description': sum(1 for r in repositories if r.has_description),
            'stale_repositories': sum(1 for r in repositories if r.is_stale),
            'active_repositories': sum(1 for r in repositories if not r.is_stale)
        }
        
        return metrics
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        repositories = self.get_repositories()
        
        for repo in repositories:
            if not repo.has_encryption:
                recommendations.append({
                    'resource_id': repo.name,
                    'resource_type': 'CodeCommit Repository',
                    'title': 'Habilitar criptografia KMS',
                    'description': f'Repositório {repo.name} não usa criptografia KMS personalizada.',
                    'action': 'Configurar KMS key para criptografia do repositório',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
            
            if repo.is_stale:
                recommendations.append({
                    'resource_id': repo.name,
                    'resource_type': 'CodeCommit Repository',
                    'title': 'Repositório inativo',
                    'description': f'Repositório {repo.name} não foi modificado há {repo.days_since_modified} dias.',
                    'action': 'Verificar se repositório ainda é necessário ou arquivar',
                    'estimated_savings': 'Baixo',
                    'priority': 'LOW'
                })
            
            prs = self.get_pull_requests(repo.name, status='OPEN')
            stale_prs = [p for p in prs if p.is_stale_pr]
            
            for pr in stale_prs:
                recommendations.append({
                    'resource_id': f"{repo.name}/PR-{pr.pull_request_id}",
                    'resource_type': 'CodeCommit Pull Request',
                    'title': 'Pull Request aberto há muito tempo',
                    'description': f'PR "{pr.title}" está aberto há {pr.days_open} dias.',
                    'action': 'Revisar e fechar ou mesclar o PR',
                    'estimated_savings': 'N/A',
                    'priority': 'LOW'
                })
        
        approval_templates = self.get_approval_rule_templates()
        if len(approval_templates) == 0 and len(repositories) > 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'CodeCommit',
                'title': 'Sem templates de aprovação configurados',
                'description': 'Nenhum template de regras de aprovação configurado para PRs.',
                'action': 'Criar templates de aprovação para garantir revisão de código',
                'estimated_savings': 'N/A',
                'priority': 'MEDIUM'
            })
        
        return recommendations
