"""
AWS GuardDuty FinOps Service

Análise de detecção de ameaças, findings e recomendações de segurança.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Detector:
    """Representa um detector GuardDuty"""
    detector_id: str
    status: str = 'ENABLED'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    finding_publishing_frequency: str = 'SIX_HOURS'
    service_role: Optional[str] = None
    data_sources: Dict = field(default_factory=dict)
    features: List[Dict] = field(default_factory=list)
    
    @property
    def is_enabled(self) -> bool:
        return self.status == 'ENABLED'
    
    @property
    def has_s3_protection(self) -> bool:
        s3_logs = self.data_sources.get('s3Logs', {})
        return s3_logs.get('status') == 'ENABLED'
    
    @property
    def has_kubernetes_protection(self) -> bool:
        k8s = self.data_sources.get('kubernetes', {})
        audit_logs = k8s.get('auditLogs', {})
        return audit_logs.get('status') == 'ENABLED'
    
    @property
    def has_malware_protection(self) -> bool:
        malware = self.data_sources.get('malwareProtection', {})
        return malware.get('status') == 'ENABLED'
    
    @property
    def has_runtime_monitoring(self) -> bool:
        for feature in self.features:
            if feature.get('name') == 'RUNTIME_MONITORING' and feature.get('status') == 'ENABLED':
                return True
        return False
    
    @property
    def publishes_frequently(self) -> bool:
        return self.finding_publishing_frequency == 'FIFTEEN_MINUTES'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detector_id': self.detector_id,
            'status': self.status,
            'finding_publishing_frequency': self.finding_publishing_frequency,
            'is_enabled': self.is_enabled,
            'has_s3_protection': self.has_s3_protection,
            'has_kubernetes_protection': self.has_kubernetes_protection,
            'has_malware_protection': self.has_malware_protection,
            'has_runtime_monitoring': self.has_runtime_monitoring,
            'publishes_frequently': self.publishes_frequently
        }


@dataclass
class Finding:
    """Representa um finding do GuardDuty"""
    finding_id: str
    detector_id: str
    account_id: str
    severity: float = 0.0
    type: str = ''
    title: str = ''
    description: str = ''
    region: str = ''
    resource_type: str = ''
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def severity_level(self) -> str:
        if self.severity >= 7.0:
            return 'HIGH'
        elif self.severity >= 4.0:
            return 'MEDIUM'
        return 'LOW'
    
    @property
    def is_high_severity(self) -> bool:
        return self.severity >= 7.0
    
    @property
    def is_medium_severity(self) -> bool:
        return 4.0 <= self.severity < 7.0
    
    @property
    def is_low_severity(self) -> bool:
        return self.severity < 4.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'finding_id': self.finding_id,
            'detector_id': self.detector_id,
            'account_id': self.account_id,
            'severity': self.severity,
            'severity_level': self.severity_level,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'region': self.region,
            'resource_type': self.resource_type,
            'is_high_severity': self.is_high_severity,
            'is_medium_severity': self.is_medium_severity,
            'is_low_severity': self.is_low_severity
        }


@dataclass
class Member:
    """Representa uma conta membro GuardDuty"""
    account_id: str
    detector_id: str
    email: str = ''
    relationship_status: str = 'ENABLED'
    invited_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        return self.relationship_status == 'ENABLED'
    
    @property
    def is_pending(self) -> bool:
        return self.relationship_status == 'INVITED'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'account_id': self.account_id,
            'detector_id': self.detector_id,
            'email': self.email,
            'relationship_status': self.relationship_status,
            'is_active': self.is_active,
            'is_pending': self.is_pending
        }


class GuardDutyService(BaseAWSService):
    """Serviço FinOps para AWS GuardDuty"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._guardduty_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "guardduty"
    
    @property
    def guardduty_client(self):
        if self._guardduty_client is None:
            if self._client_factory:
                self._guardduty_client = self._client_factory.get_client('guardduty')
            else:
                import boto3
                self._guardduty_client = boto3.client('guardduty')
        return self._guardduty_client
    
    def health_check(self) -> bool:
        try:
            self.guardduty_client.list_detectors(MaxResults=1)
            return True
        except Exception:
            return False
    
    def get_detectors(self) -> List[Detector]:
        detectors = []
        try:
            paginator = self.guardduty_client.get_paginator('list_detectors')
            
            for page in paginator.paginate():
                for detector_id in page.get('DetectorIds', []):
                    try:
                        response = self.guardduty_client.get_detector(DetectorId=detector_id)
                        
                        detectors.append(Detector(
                            detector_id=detector_id,
                            status=response.get('Status', 'ENABLED'),
                            created_at=response.get('CreatedAt'),
                            updated_at=response.get('UpdatedAt'),
                            finding_publishing_frequency=response.get('FindingPublishingFrequency', 'SIX_HOURS'),
                            service_role=response.get('ServiceRole'),
                            data_sources=response.get('DataSources', {}),
                            features=response.get('Features', [])
                        ))
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter detector {detector_id}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao listar detectors: {e}")
        
        return detectors
    
    def get_findings(self, detector_id: str, max_results: int = 50) -> List[Finding]:
        findings = []
        try:
            response = self.guardduty_client.list_findings(
                DetectorId=detector_id,
                MaxResults=max_results,
                SortCriteria={'AttributeName': 'severity', 'OrderBy': 'DESC'}
            )
            
            finding_ids = response.get('FindingIds', [])
            
            if finding_ids:
                details = self.guardduty_client.get_findings(
                    DetectorId=detector_id,
                    FindingIds=finding_ids
                )
                
                for finding in details.get('Findings', []):
                    resource = finding.get('Resource', {})
                    findings.append(Finding(
                        finding_id=finding.get('Id', ''),
                        detector_id=detector_id,
                        account_id=finding.get('AccountId', ''),
                        severity=finding.get('Severity', 0.0),
                        type=finding.get('Type', ''),
                        title=finding.get('Title', ''),
                        description=finding.get('Description', ''),
                        region=finding.get('Region', ''),
                        resource_type=resource.get('ResourceType', ''),
                        created_at=finding.get('CreatedAt'),
                        updated_at=finding.get('UpdatedAt')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar findings: {e}")
        
        return findings
    
    def get_members(self, detector_id: str) -> List[Member]:
        members = []
        try:
            paginator = self.guardduty_client.get_paginator('list_members')
            
            for page in paginator.paginate(DetectorId=detector_id):
                for member in page.get('Members', []):
                    members.append(Member(
                        account_id=member.get('AccountId', ''),
                        detector_id=detector_id,
                        email=member.get('Email', ''),
                        relationship_status=member.get('RelationshipStatus', ''),
                        invited_at=member.get('InvitedAt'),
                        updated_at=member.get('UpdatedAt')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar membros: {e}")
        
        return members
    
    def get_resources(self) -> Dict[str, Any]:
        detectors = self.get_detectors()
        all_findings = []
        all_members = []
        
        for detector in detectors:
            findings = self.get_findings(detector.detector_id)
            all_findings.extend(findings)
            
            members = self.get_members(detector.detector_id)
            all_members.extend(members)
        
        return {
            'detectors': [d.to_dict() for d in detectors],
            'findings': [f.to_dict() for f in all_findings],
            'members': [m.to_dict() for m in all_members],
            'summary': {
                'total_detectors': len(detectors),
                'enabled_detectors': sum(1 for d in detectors if d.is_enabled),
                'total_findings': len(all_findings),
                'high_severity_findings': sum(1 for f in all_findings if f.is_high_severity),
                'medium_severity_findings': sum(1 for f in all_findings if f.is_medium_severity),
                'low_severity_findings': sum(1 for f in all_findings if f.is_low_severity),
                'total_members': len(all_members),
                'active_members': sum(1 for m in all_members if m.is_active)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        detectors = self.get_detectors()
        all_findings = []
        
        for detector in detectors:
            findings = self.get_findings(detector.detector_id)
            all_findings.extend(findings)
        
        return {
            'total_detectors': len(detectors),
            'enabled_detectors': sum(1 for d in detectors if d.is_enabled),
            'findings_by_severity': {
                'high': sum(1 for f in all_findings if f.is_high_severity),
                'medium': sum(1 for f in all_findings if f.is_medium_severity),
                'low': sum(1 for f in all_findings if f.is_low_severity)
            },
            'protection_coverage': {
                's3_protection': sum(1 for d in detectors if d.has_s3_protection),
                'kubernetes_protection': sum(1 for d in detectors if d.has_kubernetes_protection),
                'malware_protection': sum(1 for d in detectors if d.has_malware_protection),
                'runtime_monitoring': sum(1 for d in detectors if d.has_runtime_monitoring)
            }
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        detectors = self.get_detectors()
        
        for detector in detectors:
            if not detector.is_enabled:
                recommendations.append({
                    'resource_id': detector.detector_id,
                    'resource_type': 'GuardDuty Detector',
                    'title': 'Detector desabilitado',
                    'description': f'Detector {detector.detector_id} está desabilitado. Ameaças não estão sendo monitoradas.',
                    'action': 'Habilitar detector para monitoramento de segurança',
                    'estimated_savings': 'N/A',
                    'priority': 'CRITICAL'
                })
            
            if not detector.has_s3_protection:
                recommendations.append({
                    'resource_id': detector.detector_id,
                    'resource_type': 'GuardDuty Detector',
                    'title': 'Proteção S3 não habilitada',
                    'description': f'Detector {detector.detector_id} não tem proteção S3 habilitada.',
                    'action': 'Habilitar S3 Protection para detectar ameaças em buckets S3',
                    'estimated_savings': 'N/A',
                    'priority': 'HIGH'
                })
            
            if not detector.has_malware_protection:
                recommendations.append({
                    'resource_id': detector.detector_id,
                    'resource_type': 'GuardDuty Detector',
                    'title': 'Proteção Malware não habilitada',
                    'description': f'Detector {detector.detector_id} não tem proteção contra malware.',
                    'action': 'Habilitar Malware Protection para detectar malware em workloads',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
            
            findings = self.get_findings(detector.detector_id)
            high_severity = [f for f in findings if f.is_high_severity]
            
            if len(high_severity) > 0:
                recommendations.append({
                    'resource_id': detector.detector_id,
                    'resource_type': 'GuardDuty Detector',
                    'title': f'{len(high_severity)} findings de alta severidade',
                    'description': f'Detector tem {len(high_severity)} findings de alta severidade pendentes.',
                    'action': 'Investigar e remediar findings de alta severidade imediatamente',
                    'estimated_savings': 'N/A',
                    'priority': 'CRITICAL'
                })
        
        return recommendations
