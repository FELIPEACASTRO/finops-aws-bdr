"""
AWS ACM FinOps Service

Análise de certificados SSL/TLS e recomendações.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Certificate:
    """Representa um certificado ACM"""
    certificate_arn: str
    domain_name: str = ''
    subject_alternative_names: List[str] = field(default_factory=list)
    status: str = 'ISSUED'
    type: str = 'AMAZON_ISSUED'
    key_algorithm: str = 'RSA_2048'
    issuer: Optional[str] = None
    created_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    renewal_eligibility: str = 'ELIGIBLE'
    renewal_status: Optional[str] = None
    in_use_by: List[str] = field(default_factory=list)
    failure_reason: Optional[str] = None
    
    @property
    def is_issued(self) -> bool:
        return self.status == 'ISSUED'
    
    @property
    def is_pending_validation(self) -> bool:
        return self.status == 'PENDING_VALIDATION'
    
    @property
    def is_expired(self) -> bool:
        return self.status == 'EXPIRED'
    
    @property
    def is_failed(self) -> bool:
        return self.status == 'FAILED'
    
    @property
    def is_amazon_issued(self) -> bool:
        return self.type == 'AMAZON_ISSUED'
    
    @property
    def is_imported(self) -> bool:
        return self.type == 'IMPORTED'
    
    @property
    def is_in_use(self) -> bool:
        return len(self.in_use_by) > 0
    
    @property
    def days_until_expiry(self) -> int:
        if self.not_after:
            now = datetime.now(timezone.utc)
            if self.not_after.tzinfo is None:
                not_after = self.not_after.replace(tzinfo=timezone.utc)
            else:
                not_after = self.not_after
            delta = not_after - now
            return max(0, delta.days)
        return 0
    
    @property
    def is_expiring_soon(self) -> bool:
        return self.is_issued and self.days_until_expiry <= 30
    
    @property
    def is_renewable(self) -> bool:
        return self.renewal_eligibility == 'ELIGIBLE'
    
    @property
    def san_count(self) -> int:
        return len(self.subject_alternative_names)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'certificate_arn': self.certificate_arn,
            'domain_name': self.domain_name,
            'san_count': self.san_count,
            'status': self.status,
            'type': self.type,
            'key_algorithm': self.key_algorithm,
            'issuer': self.issuer,
            'days_until_expiry': self.days_until_expiry,
            'is_issued': self.is_issued,
            'is_pending_validation': self.is_pending_validation,
            'is_expired': self.is_expired,
            'is_amazon_issued': self.is_amazon_issued,
            'is_imported': self.is_imported,
            'is_in_use': self.is_in_use,
            'is_expiring_soon': self.is_expiring_soon,
            'is_renewable': self.is_renewable,
            'in_use_count': len(self.in_use_by),
            'failure_reason': self.failure_reason
        }


class ACMService(BaseAWSService):
    """Serviço FinOps para AWS ACM"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._acm_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "acm"
    
    @property
    def acm_client(self):
        if self._acm_client is None:
            if self._client_factory:
                self._acm_client = self._client_factory.get_client('acm')
            else:
                import boto3
                self._acm_client = boto3.client('acm')
        return self._acm_client
    
    def health_check(self) -> bool:
        try:
            self.acm_client.list_certificates(MaxItems=1)
            return True
        except Exception:
            return False
    
    def get_certificates(self) -> List[Certificate]:
        certificates = []
        try:
            paginator = self.acm_client.get_paginator('list_certificates')
            
            for page in paginator.paginate(Includes={'keyTypes': ['RSA_1024', 'RSA_2048', 'RSA_3072', 'RSA_4096', 'EC_prime256v1', 'EC_secp384r1', 'EC_secp521r1']}):
                for cert_summary in page.get('CertificateSummaryList', []):
                    cert_arn = cert_summary.get('CertificateArn', '')
                    
                    try:
                        response = self.acm_client.describe_certificate(CertificateArn=cert_arn)
                        cert = response.get('Certificate', {})
                        
                        certificates.append(Certificate(
                            certificate_arn=cert_arn,
                            domain_name=cert.get('DomainName', ''),
                            subject_alternative_names=cert.get('SubjectAlternativeNames', []),
                            status=cert.get('Status', 'ISSUED'),
                            type=cert.get('Type', 'AMAZON_ISSUED'),
                            key_algorithm=cert.get('KeyAlgorithm', 'RSA_2048'),
                            issuer=cert.get('Issuer'),
                            created_at=cert.get('CreatedAt'),
                            issued_at=cert.get('IssuedAt'),
                            not_before=cert.get('NotBefore'),
                            not_after=cert.get('NotAfter'),
                            renewal_eligibility=cert.get('RenewalEligibility', 'ELIGIBLE'),
                            renewal_status=cert.get('RenewalSummary', {}).get('RenewalStatus'),
                            in_use_by=cert.get('InUseBy', []),
                            failure_reason=cert.get('FailureReason')
                        ))
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter detalhes do certificado {cert_arn}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar certificados: {e}")
        
        return certificates
    
    def get_resources(self) -> Dict[str, Any]:
        certificates = self.get_certificates()
        
        return {
            'certificates': [c.to_dict() for c in certificates],
            'summary': {
                'total_certificates': len(certificates),
                'issued_certificates': sum(1 for c in certificates if c.is_issued),
                'pending_validation': sum(1 for c in certificates if c.is_pending_validation),
                'expired_certificates': sum(1 for c in certificates if c.is_expired),
                'failed_certificates': sum(1 for c in certificates if c.is_failed),
                'amazon_issued': sum(1 for c in certificates if c.is_amazon_issued),
                'imported': sum(1 for c in certificates if c.is_imported),
                'in_use': sum(1 for c in certificates if c.is_in_use),
                'unused': sum(1 for c in certificates if not c.is_in_use and c.is_issued),
                'expiring_soon': sum(1 for c in certificates if c.is_expiring_soon)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        certificates = self.get_certificates()
        
        return {
            'total_certificates': len(certificates),
            'certificate_status': {
                'issued': sum(1 for c in certificates if c.is_issued),
                'pending_validation': sum(1 for c in certificates if c.is_pending_validation),
                'expired': sum(1 for c in certificates if c.is_expired),
                'failed': sum(1 for c in certificates if c.is_failed)
            },
            'certificate_types': {
                'amazon_issued': sum(1 for c in certificates if c.is_amazon_issued),
                'imported': sum(1 for c in certificates if c.is_imported)
            },
            'usage': {
                'in_use': sum(1 for c in certificates if c.is_in_use),
                'unused': sum(1 for c in certificates if not c.is_in_use and c.is_issued)
            },
            'expiration': {
                'expiring_30_days': sum(1 for c in certificates if c.is_expiring_soon),
                'expiring_90_days': sum(1 for c in certificates if c.is_issued and c.days_until_expiry <= 90)
            }
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        certificates = self.get_certificates()
        
        for cert in certificates:
            if cert.is_expiring_soon and cert.is_issued:
                recommendations.append({
                    'resource_id': cert.certificate_arn,
                    'resource_type': 'ACM Certificate',
                    'title': f'Certificado expirando em {cert.days_until_expiry} dias',
                    'description': f'Certificado {cert.domain_name} expira em {cert.days_until_expiry} dias.',
                    'action': 'Renovar certificado antes da expiração' if cert.is_imported else 'Verificar renovação automática',
                    'estimated_savings': 'N/A',
                    'priority': 'CRITICAL' if cert.days_until_expiry <= 7 else 'HIGH'
                })
            
            if cert.is_issued and not cert.is_in_use:
                recommendations.append({
                    'resource_id': cert.certificate_arn,
                    'resource_type': 'ACM Certificate',
                    'title': 'Certificado não está em uso',
                    'description': f'Certificado {cert.domain_name} não está associado a nenhum recurso.',
                    'action': 'Remover certificado não utilizado ou associar a um recurso',
                    'estimated_savings': 'Baixo',
                    'priority': 'LOW'
                })
            
            if cert.is_pending_validation:
                recommendations.append({
                    'resource_id': cert.certificate_arn,
                    'resource_type': 'ACM Certificate',
                    'title': 'Validação pendente',
                    'description': f'Certificado {cert.domain_name} está aguardando validação.',
                    'action': 'Completar validação DNS ou email para emitir certificado',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
            
            if cert.is_failed:
                recommendations.append({
                    'resource_id': cert.certificate_arn,
                    'resource_type': 'ACM Certificate',
                    'title': 'Certificado falhou',
                    'description': f'Certificado {cert.domain_name} falhou. Motivo: {cert.failure_reason}',
                    'action': 'Verificar motivo da falha e recriar certificado',
                    'estimated_savings': 'N/A',
                    'priority': 'HIGH'
                })
            
            if cert.is_imported and cert.is_in_use:
                recommendations.append({
                    'resource_id': cert.certificate_arn,
                    'resource_type': 'ACM Certificate',
                    'title': 'Certificado importado em uso',
                    'description': f'Certificado {cert.domain_name} foi importado e requer renovação manual.',
                    'action': 'Considerar migrar para certificado gerenciado pela AWS para renovação automática',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
        
        return recommendations
