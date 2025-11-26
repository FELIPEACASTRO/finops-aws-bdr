"""
Secrets Manager FinOps Service - Análise de Custos de Secrets

FASE 2 - Prioridade 2: Security
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Secrets
- Análise de rotação e acesso
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class Secret:
    """Representa um Secret"""
    name: str
    arn: str
    description: str = ""
    kms_key_id: Optional[str] = None
    rotation_enabled: bool = False
    rotation_lambda_arn: Optional[str] = None
    last_accessed_date: Optional[datetime] = None
    last_changed_date: Optional[datetime] = None
    last_rotated_date: Optional[datetime] = None
    created_date: Optional[datetime] = None
    deleted_date: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'description': self.description,
            'rotation_enabled': self.rotation_enabled,
            'last_accessed_date': self.last_accessed_date.isoformat() if self.last_accessed_date else None,
            'last_rotated_date': self.last_rotated_date.isoformat() if self.last_rotated_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }


class SecretsManagerService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Secrets Manager
    """
    
    def __init__(
        self,
        secretsmanager_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._secretsmanager_client = secretsmanager_client
    
    @property
    def secretsmanager_client(self):
        if self._secretsmanager_client is None:
            import boto3
            self._secretsmanager_client = boto3.client('secretsmanager')
        return self._secretsmanager_client
    
    def get_service_name(self) -> str:
        return "AWS Secrets Manager"
    
    def health_check(self) -> bool:
        try:
            self.secretsmanager_client.list_secrets(MaxResults=1)
            return True
        except Exception:
            return False
    
    
    def get_secrets(self) -> List[Secret]:
        """Lista todos os Secrets"""
        secrets = []
        
        paginator = self.secretsmanager_client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page.get('SecretList', []):
                tags = {t['Key']: t['Value'] for t in secret.get('Tags', [])}
                
                s = Secret(
                    name=secret['Name'],
                    arn=secret['ARN'],
                    description=secret.get('Description', ''),
                    kms_key_id=secret.get('KmsKeyId'),
                    rotation_enabled=secret.get('RotationEnabled', False),
                    rotation_lambda_arn=secret.get('RotationLambdaARN'),
                    last_accessed_date=secret.get('LastAccessedDate'),
                    last_changed_date=secret.get('LastChangedDate'),
                    last_rotated_date=secret.get('LastRotatedDate'),
                    created_date=secret.get('CreatedDate'),
                    deleted_date=secret.get('DeletedDate'),
                    tags=tags
                )
                secrets.append(s)
        
        return secrets
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        secrets = self.get_secrets()
        return [s.to_dict() for s in secrets]
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Secrets Manager"""
        secrets = self.get_secrets()
        
        with_rotation = len([s for s in secrets if s.rotation_enabled])
        
        never_accessed = 0
        for s in secrets:
            if not s.last_accessed_date:
                never_accessed += 1
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(secrets),
            metrics={
                'total_secrets': len(secrets),
                'with_rotation': with_rotation,
                'without_rotation': len(secrets) - with_rotation,
                'never_accessed': never_accessed
            },
            period_days=30,
            collected_at=datetime.utcnow()
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Secrets Manager"""
        recommendations = []
        secrets = self.get_secrets()
        
        for secret in secrets:
            if not secret.rotation_enabled:
                recommendations.append(ServiceRecommendation(
                    resource_id=secret.name,
                    resource_type='Secret',
                    recommendation_type='NO_ROTATION',
                    title='Rotação automática não habilitada',
                    description=f'Secret {secret.name} não tem rotação automática. '
                               f'Considere habilitar para melhor segurança.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    action='Habilitar rotação automática'
                ))
            
            if not secret.last_accessed_date:
                recommendations.append(ServiceRecommendation(
                    resource_id=secret.name,
                    resource_type='Secret',
                    recommendation_type='NEVER_ACCESSED',
                    title='Secret nunca acessado',
                    description=f'Secret {secret.name} nunca foi acessado. '
                               f'Custo: $0.40/mês. Remova se não for necessário.',
                    estimated_savings=0.40,
                    priority='MEDIUM',
                    action='Remover secret não utilizado'
                ))
            elif secret.last_accessed_date:
                days_since_access = (datetime.utcnow() - secret.last_accessed_date.replace(tzinfo=None)).days
                if days_since_access > 90:
                    recommendations.append(ServiceRecommendation(
                        resource_id=secret.name,
                        resource_type='Secret',
                        recommendation_type='STALE_SECRET',
                        title=f'Secret não acessado há {days_since_access} dias',
                        description=f'Secret {secret.name} não é acessado há {days_since_access} dias. '
                                   f'Verifique se ainda é necessário.',
                        estimated_savings=0.40,
                        priority='LOW',
                        action='Avaliar necessidade do secret'
                    ))
        
        return recommendations
