"""
AWS Inspector FinOps Service

Análise de vulnerabilidades, findings e recomendações de segurança.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class InspectorFinding:
    """Representa um finding do Inspector"""
    finding_arn: str
    severity: str = 'MEDIUM'
    status: str = 'ACTIVE'
    type: str = 'PACKAGE_VULNERABILITY'
    title: str = ''
    description: str = ''
    remediation: str = ''
    aws_account_id: str = ''
    resource_type: str = ''
    resource_id: str = ''
    first_observed_at: Optional[datetime] = None
    last_observed_at: Optional[datetime] = None
    inspector_score: float = 0.0
    exploit_available: bool = False
    fix_available: bool = False
    
    @property
    def is_critical(self) -> bool:
        return self.severity == 'CRITICAL'
    
    @property
    def is_high(self) -> bool:
        return self.severity == 'HIGH'
    
    @property
    def is_medium(self) -> bool:
        return self.severity == 'MEDIUM'
    
    @property
    def is_low(self) -> bool:
        return self.severity == 'LOW'
    
    @property
    def is_active(self) -> bool:
        return self.status == 'ACTIVE'
    
    @property
    def is_exploitable(self) -> bool:
        return self.exploit_available
    
    @property
    def has_fix(self) -> bool:
        return self.fix_available
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'finding_arn': self.finding_arn,
            'severity': self.severity,
            'status': self.status,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'remediation': self.remediation,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'inspector_score': self.inspector_score,
            'is_critical': self.is_critical,
            'is_high': self.is_high,
            'is_exploitable': self.is_exploitable,
            'has_fix': self.has_fix,
            'is_active': self.is_active
        }


@dataclass
class CoverageStatistics:
    """Estatísticas de cobertura do Inspector"""
    total_resources: int = 0
    covered_resources: int = 0
    ec2_instances: int = 0
    ecr_repositories: int = 0
    lambda_functions: int = 0
    ec2_covered: int = 0
    ecr_covered: int = 0
    lambda_covered: int = 0
    
    @property
    def coverage_percentage(self) -> float:
        if self.total_resources == 0:
            return 0.0
        return (self.covered_resources / self.total_resources) * 100
    
    @property
    def ec2_coverage_percentage(self) -> float:
        if self.ec2_instances == 0:
            return 0.0
        return (self.ec2_covered / self.ec2_instances) * 100
    
    @property
    def has_full_coverage(self) -> bool:
        return self.coverage_percentage >= 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_resources': self.total_resources,
            'covered_resources': self.covered_resources,
            'coverage_percentage': round(self.coverage_percentage, 2),
            'ec2_instances': self.ec2_instances,
            'ec2_covered': self.ec2_covered,
            'ecr_repositories': self.ecr_repositories,
            'ecr_covered': self.ecr_covered,
            'lambda_functions': self.lambda_functions,
            'lambda_covered': self.lambda_covered,
            'has_full_coverage': self.has_full_coverage
        }


@dataclass
class AccountStatus:
    """Status do Inspector para uma conta"""
    account_id: str
    status: str = 'ENABLED'
    resource_status: Dict = field(default_factory=dict)
    
    @property
    def is_enabled(self) -> bool:
        return self.status == 'ENABLED'
    
    @property
    def ec2_scanning_enabled(self) -> bool:
        ec2 = self.resource_status.get('ec2', {})
        return ec2.get('status') == 'ENABLED'
    
    @property
    def ecr_scanning_enabled(self) -> bool:
        ecr = self.resource_status.get('ecr', {})
        return ecr.get('status') == 'ENABLED'
    
    @property
    def lambda_scanning_enabled(self) -> bool:
        lambda_status = self.resource_status.get('lambda', {})
        return lambda_status.get('status') == 'ENABLED'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'account_id': self.account_id,
            'status': self.status,
            'is_enabled': self.is_enabled,
            'ec2_scanning_enabled': self.ec2_scanning_enabled,
            'ecr_scanning_enabled': self.ecr_scanning_enabled,
            'lambda_scanning_enabled': self.lambda_scanning_enabled
        }


class InspectorService(BaseAWSService):
    """Serviço FinOps para AWS Inspector"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._inspector_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "inspector2"
    
    @property
    def inspector_client(self):
        if self._inspector_client is None:
            if self._client_factory:
                self._inspector_client = self._client_factory.get_client('inspector2')
            else:
                import boto3
                self._inspector_client = boto3.client('inspector2')
        return self._inspector_client
    
    def health_check(self) -> bool:
        try:
            self.inspector_client.batch_get_account_status(accountIds=[])
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_account_status(self) -> List[AccountStatus]:
        statuses = []
        try:
            response = self.inspector_client.batch_get_account_status(accountIds=[])
            
            for account in response.get('accounts', []):
                statuses.append(AccountStatus(
                    account_id=account.get('accountId', ''),
                    status=account.get('state', {}).get('status', 'DISABLED'),
                    resource_status=account.get('resourceState', {})
                ))
        except Exception as e:
            self.logger.error(f"Erro ao obter status das contas: {e}")
        
        return statuses
    
    def get_findings(self, max_results: int = 100) -> List[InspectorFinding]:
        findings = []
        try:
            paginator = self.inspector_client.get_paginator('list_findings')
            
            count = 0
            for page in paginator.paginate(
                filterCriteria={'findingStatus': [{'comparison': 'EQUALS', 'value': 'ACTIVE'}]},
                sortCriteria={'field': 'SEVERITY', 'sortOrder': 'DESC'}
            ):
                for finding in page.get('findings', []):
                    if count >= max_results:
                        break
                    
                    resources = finding.get('resources', [{}])
                    resource = resources[0] if resources else {}
                    remediation = finding.get('remediation', {})
                    
                    findings.append(InspectorFinding(
                        finding_arn=finding.get('findingArn', ''),
                        severity=finding.get('severity', 'MEDIUM'),
                        status=finding.get('status', 'ACTIVE'),
                        type=finding.get('type', ''),
                        title=finding.get('title', ''),
                        description=finding.get('description', ''),
                        remediation=remediation.get('recommendation', {}).get('text', ''),
                        aws_account_id=finding.get('awsAccountId', ''),
                        resource_type=resource.get('type', ''),
                        resource_id=resource.get('id', ''),
                        first_observed_at=finding.get('firstObservedAt'),
                        last_observed_at=finding.get('lastObservedAt'),
                        inspector_score=finding.get('inspectorScore', 0.0),
                        exploit_available=finding.get('exploitAvailable', 'NO') == 'YES',
                        fix_available=finding.get('fixAvailable', 'NO') == 'YES'
                    ))
                    count += 1
                
                if count >= max_results:
                    break
        except Exception as e:
            self.logger.error(f"Erro ao listar findings: {e}")
        
        return findings
    
    def get_coverage_statistics(self) -> CoverageStatistics:
        stats = CoverageStatistics()
        try:
            response = self.inspector_client.list_coverage_statistics(
                groupBy='RESOURCE_TYPE'
            )
            
            counts = response.get('countsByGroup', [])
            for group in counts:
                resource_type = group.get('groupKey', '')
                count = group.get('count', 0)
                
                if resource_type == 'AWS_EC2_INSTANCE':
                    stats.ec2_instances = count
                    stats.ec2_covered = count
                elif resource_type == 'AWS_ECR_REPOSITORY':
                    stats.ecr_repositories = count
                    stats.ecr_covered = count
                elif resource_type == 'AWS_LAMBDA_FUNCTION':
                    stats.lambda_functions = count
                    stats.lambda_covered = count
            
            stats.total_resources = stats.ec2_instances + stats.ecr_repositories + stats.lambda_functions
            stats.covered_resources = stats.ec2_covered + stats.ecr_covered + stats.lambda_covered
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas de cobertura: {e}")
        
        return stats
    
    def get_resources(self) -> Dict[str, Any]:
        account_statuses = self.get_account_status()
        findings = self.get_findings()
        coverage = self.get_coverage_statistics()
        
        return {
            'account_statuses': [a.to_dict() for a in account_statuses],
            'findings': [f.to_dict() for f in findings],
            'coverage': coverage.to_dict(),
            'summary': {
                'total_accounts': len(account_statuses),
                'enabled_accounts': sum(1 for a in account_statuses if a.is_enabled),
                'total_findings': len(findings),
                'critical_findings': sum(1 for f in findings if f.is_critical),
                'high_findings': sum(1 for f in findings if f.is_high),
                'exploitable_findings': sum(1 for f in findings if f.is_exploitable),
                'fixable_findings': sum(1 for f in findings if f.has_fix),
                'coverage_percentage': coverage.coverage_percentage
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        findings = self.get_findings()
        coverage = self.get_coverage_statistics()
        
        return {
            'total_findings': len(findings),
            'findings_by_severity': {
                'critical': sum(1 for f in findings if f.is_critical),
                'high': sum(1 for f in findings if f.is_high),
                'medium': sum(1 for f in findings if f.is_medium),
                'low': sum(1 for f in findings if f.is_low)
            },
            'exploitable_findings': sum(1 for f in findings if f.is_exploitable),
            'fixable_findings': sum(1 for f in findings if f.has_fix),
            'coverage': coverage.to_dict()
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        account_statuses = self.get_account_status()
        findings = self.get_findings()
        coverage = self.get_coverage_statistics()
        
        for status in account_statuses:
            if not status.is_enabled:
                recommendations.append({
                    'resource_id': status.account_id,
                    'resource_type': 'Inspector Account',
                    'title': 'Inspector desabilitado',
                    'description': f'Inspector não está habilitado para a conta {status.account_id}.',
                    'action': 'Habilitar Inspector para detecção de vulnerabilidades',
                    'estimated_savings': 'N/A',
                    'priority': 'CRITICAL'
                })
            else:
                if not status.ec2_scanning_enabled:
                    recommendations.append({
                        'resource_id': status.account_id,
                        'resource_type': 'Inspector Account',
                        'title': 'EC2 scanning desabilitado',
                        'description': f'Scanning de EC2 não está habilitado para a conta {status.account_id}.',
                        'action': 'Habilitar EC2 scanning para detectar vulnerabilidades',
                        'estimated_savings': 'N/A',
                        'priority': 'HIGH'
                    })
                
                if not status.lambda_scanning_enabled:
                    recommendations.append({
                        'resource_id': status.account_id,
                        'resource_type': 'Inspector Account',
                        'title': 'Lambda scanning desabilitado',
                        'description': f'Scanning de Lambda não está habilitado para a conta {status.account_id}.',
                        'action': 'Habilitar Lambda scanning para detectar vulnerabilidades',
                        'estimated_savings': 'N/A',
                        'priority': 'MEDIUM'
                    })
        
        critical_exploitable = [f for f in findings if f.is_critical and f.is_exploitable]
        if len(critical_exploitable) > 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'Inspector Findings',
                'title': f'{len(critical_exploitable)} vulnerabilidades críticas exploráveis',
                'description': f'Há {len(critical_exploitable)} vulnerabilidades críticas com exploits conhecidos.',
                'action': 'Remediar vulnerabilidades críticas exploráveis imediatamente',
                'estimated_savings': 'N/A',
                'priority': 'CRITICAL'
            })
        
        fixable = [f for f in findings if f.has_fix and (f.is_critical or f.is_high)]
        if len(fixable) > 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'Inspector Findings',
                'title': f'{len(fixable)} vulnerabilidades com fix disponível',
                'description': f'Há {len(fixable)} vulnerabilidades críticas/altas com correção disponível.',
                'action': 'Aplicar patches para vulnerabilidades com fix disponível',
                'estimated_savings': 'N/A',
                'priority': 'HIGH'
            })
        
        if coverage.coverage_percentage < 80:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'Inspector Coverage',
                'title': f'Cobertura de scanning baixa ({coverage.coverage_percentage:.1f}%)',
                'description': f'Apenas {coverage.coverage_percentage:.1f}% dos recursos estão cobertos pelo Inspector.',
                'action': 'Expandir cobertura do Inspector para todos os recursos',
                'estimated_savings': 'N/A',
                'priority': 'MEDIUM'
            })
        
        return recommendations
