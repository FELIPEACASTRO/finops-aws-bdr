"""
AWS Backup FinOps Service - Análise de Custos de Backup

FASE 2 - Prioridade 2: Storage
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Vaults, Plans, Jobs
- Análise de recovery points e retenção
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class BackupVault:
    """Representa um Backup Vault"""
    backup_vault_name: str
    backup_vault_arn: str
    creation_date: Optional[datetime]
    encryption_key_arn: Optional[str]
    number_of_recovery_points: int = 0
    locked: bool = False
    min_retention_days: Optional[int] = None
    max_retention_days: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backup_vault_name': self.backup_vault_name,
            'number_of_recovery_points': self.number_of_recovery_points,
            'locked': self.locked,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass
class BackupPlan:
    """Representa um Backup Plan"""
    backup_plan_id: str
    backup_plan_name: str
    backup_plan_arn: str
    version_id: str
    creation_date: Optional[datetime]
    last_execution_date: Optional[datetime]
    advanced_backup_settings: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backup_plan_id': self.backup_plan_id,
            'backup_plan_name': self.backup_plan_name,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_execution_date': self.last_execution_date.isoformat() if self.last_execution_date else None
        }


@dataclass
class BackupJob:
    """Representa um Backup Job"""
    backup_job_id: str
    backup_vault_name: str
    resource_arn: str
    resource_type: str
    state: str
    status_message: str = ""
    creation_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    backup_size_in_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backup_job_id': self.backup_job_id,
            'backup_vault_name': self.backup_vault_name,
            'resource_type': self.resource_type,
            'state': self.state,
            'backup_size_gb': round(self.backup_size_in_bytes / (1024**3), 2),
            'creation_date': self.creation_date.isoformat() if self.creation_date else None
        }


class BackupService(BaseAWSService):
    """
    Serviço FinOps para análise de custos AWS Backup
    """
    
    def __init__(
        self,
        backup_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._backup_client = backup_client
    
    @property
    def backup_client(self):
        if self._backup_client is None:
            import boto3
            self._backup_client = boto3.client('backup')
        return self._backup_client
    
    def get_service_name(self) -> str:
        return "AWS Backup"
    
    def health_check(self) -> bool:
        try:
            self.backup_client.list_backup_vaults(MaxResults=1)
            return True
        except Exception:
            return False
    
    
    def get_backup_vaults(self) -> List[BackupVault]:
        """Lista Backup Vaults"""
        vaults = []
        
        paginator = self.backup_client.get_paginator('list_backup_vaults')
        
        for page in paginator.paginate():
            for vault in page.get('BackupVaultList', []):
                backup_vault = BackupVault(
                    backup_vault_name=vault['BackupVaultName'],
                    backup_vault_arn=vault['BackupVaultArn'],
                    creation_date=vault.get('CreationDate'),
                    encryption_key_arn=vault.get('EncryptionKeyArn'),
                    number_of_recovery_points=vault.get('NumberOfRecoveryPoints', 0),
                    locked=vault.get('Locked', False),
                    min_retention_days=vault.get('MinRetentionDays'),
                    max_retention_days=vault.get('MaxRetentionDays')
                )
                vaults.append(backup_vault)
        
        return vaults
    
    
    def get_backup_plans(self) -> List[BackupPlan]:
        """Lista Backup Plans"""
        plans = []
        
        paginator = self.backup_client.get_paginator('list_backup_plans')
        
        for page in paginator.paginate():
            for plan in page.get('BackupPlansList', []):
                backup_plan = BackupPlan(
                    backup_plan_id=plan['BackupPlanId'],
                    backup_plan_name=plan['BackupPlanName'],
                    backup_plan_arn=plan['BackupPlanArn'],
                    version_id=plan['VersionId'],
                    creation_date=plan.get('CreationDate'),
                    last_execution_date=plan.get('LastExecutionDate'),
                    advanced_backup_settings=plan.get('AdvancedBackupSettings', [])
                )
                plans.append(backup_plan)
        
        return plans
    
    
    def get_backup_jobs(self, days: int = 7) -> List[BackupJob]:
        """Lista Backup Jobs recentes"""
        jobs = []
        
        created_after = datetime.now(timezone.utc) - timedelta(days=days)
        
        paginator = self.backup_client.get_paginator('list_backup_jobs')
        
        for page in paginator.paginate(ByCreatedAfter=created_after):
            for job in page.get('BackupJobs', []):
                backup_job = BackupJob(
                    backup_job_id=job['BackupJobId'],
                    backup_vault_name=job['BackupVaultName'],
                    resource_arn=job['ResourceArn'],
                    resource_type=job['ResourceType'],
                    state=job['State'],
                    status_message=job.get('StatusMessage', ''),
                    creation_date=job.get('CreationDate'),
                    completion_date=job.get('CompletionDate'),
                    backup_size_in_bytes=job.get('BackupSizeInBytes', 0)
                )
                jobs.append(backup_job)
        
        return jobs
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for vault in self.get_backup_vaults():
            res = vault.to_dict()
            res['resource_type'] = 'vault'
            resources.append(res)
        
        for plan in self.get_backup_plans():
            res = plan.to_dict()
            res['resource_type'] = 'plan'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de AWS Backup"""
        vaults = self.get_backup_vaults()
        plans = self.get_backup_plans()
        jobs = self.get_backup_jobs(days=7)
        
        total_recovery_points = sum(v.number_of_recovery_points for v in vaults)
        total_backup_size = sum(j.backup_size_in_bytes for j in jobs)
        failed_jobs = len([j for j in jobs if j.state == 'FAILED'])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(vaults) + len(plans),
            metrics={
                'backup_vaults': len(vaults),
                'backup_plans': len(plans),
                'total_recovery_points': total_recovery_points,
                'jobs_7d': len(jobs),
                'failed_jobs_7d': failed_jobs,
                'total_backup_size_gb': round(total_backup_size / (1024**3), 2),
                'period_days': 7,
                'collected_at': datetime.now(timezone.utc).isoformat()
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para AWS Backup"""
        recommendations = []
        vaults = self.get_backup_vaults()
        plans = self.get_backup_plans()
        jobs = self.get_backup_jobs(days=30)
        
        for vault in vaults:
            if vault.number_of_recovery_points == 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=vault.backup_vault_name,
                    resource_type='Backup Vault',
                    recommendation_type='EMPTY_VAULT',
                    title='Vault sem recovery points',
                    description=f'Backup Vault {vault.backup_vault_name} não tem recovery points. '
                               f'Considere remover se não for mais necessário.',
                    estimated_savings=0.0,
                    priority='LOW',
                    action='Remover vault vazio'
                ))
        
        for plan in plans:
            if not plan.last_execution_date:
                recommendations.append(ServiceRecommendation(
                    resource_id=plan.backup_plan_id,
                    resource_type='Backup Plan',
                    recommendation_type='NEVER_EXECUTED',
                    title='Backup Plan nunca executado',
                    description=f'Backup Plan {plan.backup_plan_name} nunca foi executado. '
                               f'Verifique se está configurado corretamente.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    action='Verificar configuração do plan'
                ))
        
        failed_jobs = [j for j in jobs if j.state == 'FAILED']
        if len(failed_jobs) > len(jobs) * 0.1 and len(jobs) > 10:
            recommendations.append(ServiceRecommendation(
                resource_id='backup-jobs',
                resource_type='Backup Jobs',
                recommendation_type='HIGH_FAILURE_RATE',
                title=f'Alta taxa de falhas em backups ({len(failed_jobs)}/{len(jobs)})',
                description=f'{len(failed_jobs)} jobs falharam nos últimos 30 dias. '
                           f'Investigue e corrija para garantir proteção de dados.',
                estimated_savings=0.0,
                priority='HIGH',
                action='Investigar falhas de backup'
            ))
        
        return recommendations
