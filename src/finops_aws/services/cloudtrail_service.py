"""
AWS CloudTrail FinOps Service

Análise de trails, eventos e recomendações de auditoria.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Trail:
    """Representa um trail do CloudTrail"""
    name: str
    trail_arn: Optional[str] = None
    home_region: str = ''
    s3_bucket_name: Optional[str] = None
    s3_key_prefix: Optional[str] = None
    sns_topic_name: Optional[str] = None
    sns_topic_arn: Optional[str] = None
    include_global_service_events: bool = True
    is_multi_region_trail: bool = False
    is_organization_trail: bool = False
    has_custom_event_selectors: bool = False
    has_insight_selectors: bool = False
    kms_key_id: Optional[str] = None
    log_file_validation_enabled: bool = False
    cloud_watch_logs_log_group_arn: Optional[str] = None
    cloud_watch_logs_role_arn: Optional[str] = None
    is_logging: bool = False
    
    @property
    def is_encrypted(self) -> bool:
        return self.kms_key_id is not None
    
    @property
    def has_log_validation(self) -> bool:
        return self.log_file_validation_enabled
    
    @property
    def has_cloudwatch_logs(self) -> bool:
        return self.cloud_watch_logs_log_group_arn is not None
    
    @property
    def has_sns_notifications(self) -> bool:
        return self.sns_topic_arn is not None or self.sns_topic_name is not None
    
    @property
    def is_global_trail(self) -> bool:
        return self.include_global_service_events and self.is_multi_region_trail
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'trail_arn': self.trail_arn,
            'home_region': self.home_region,
            's3_bucket_name': self.s3_bucket_name,
            'is_multi_region_trail': self.is_multi_region_trail,
            'is_organization_trail': self.is_organization_trail,
            'is_logging': self.is_logging,
            'is_encrypted': self.is_encrypted,
            'has_log_validation': self.has_log_validation,
            'has_cloudwatch_logs': self.has_cloudwatch_logs,
            'has_sns_notifications': self.has_sns_notifications,
            'is_global_trail': self.is_global_trail,
            'has_insight_selectors': self.has_insight_selectors
        }


@dataclass
class EventDataStore:
    """Representa um Event Data Store do CloudTrail Lake"""
    name: str
    event_data_store_arn: Optional[str] = None
    status: str = 'ENABLED'
    retention_period: int = 2557
    multi_region_enabled: bool = True
    organization_enabled: bool = False
    termination_protection_enabled: bool = True
    kms_key_id: Optional[str] = None
    created_timestamp: Optional[datetime] = None
    updated_timestamp: Optional[datetime] = None
    
    @property
    def is_enabled(self) -> bool:
        return self.status == 'ENABLED'
    
    @property
    def is_encrypted(self) -> bool:
        return self.kms_key_id is not None
    
    @property
    def has_termination_protection(self) -> bool:
        return self.termination_protection_enabled
    
    @property
    def retention_years(self) -> float:
        return self.retention_period / 365
    
    @property
    def is_long_retention(self) -> bool:
        return self.retention_period > 365 * 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'event_data_store_arn': self.event_data_store_arn,
            'status': self.status,
            'retention_period': self.retention_period,
            'retention_years': round(self.retention_years, 1),
            'multi_region_enabled': self.multi_region_enabled,
            'organization_enabled': self.organization_enabled,
            'is_enabled': self.is_enabled,
            'is_encrypted': self.is_encrypted,
            'has_termination_protection': self.has_termination_protection,
            'is_long_retention': self.is_long_retention
        }


@dataclass
class Channel:
    """Representa um channel do CloudTrail"""
    channel_arn: str
    name: str = ''
    source: str = ''
    destinations: List[Dict] = field(default_factory=list)
    
    @property
    def destination_count(self) -> int:
        return len(self.destinations)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'channel_arn': self.channel_arn,
            'name': self.name,
            'source': self.source,
            'destination_count': self.destination_count
        }


class CloudTrailService(BaseAWSService):
    """Serviço FinOps para AWS CloudTrail"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._cloudtrail_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "cloudtrail"
    
    @property
    def cloudtrail_client(self):
        if self._cloudtrail_client is None:
            if self._client_factory:
                self._cloudtrail_client = self._client_factory.get_client('cloudtrail')
            else:
                import boto3
                self._cloudtrail_client = boto3.client('cloudtrail')
        return self._cloudtrail_client
    
    def health_check(self) -> bool:
        try:
            self.cloudtrail_client.describe_trails()
            return True
        except Exception:
            return False
    
    def get_trails(self) -> List[Trail]:
        trails = []
        try:
            response = self.cloudtrail_client.describe_trails(includeShadowTrails=False)
            
            for trail_data in response.get('trailList', []):
                trail = Trail(
                    name=trail_data.get('Name', ''),
                    trail_arn=trail_data.get('TrailARN'),
                    home_region=trail_data.get('HomeRegion', ''),
                    s3_bucket_name=trail_data.get('S3BucketName'),
                    s3_key_prefix=trail_data.get('S3KeyPrefix'),
                    sns_topic_name=trail_data.get('SnsTopicName'),
                    sns_topic_arn=trail_data.get('SnsTopicARN'),
                    include_global_service_events=trail_data.get('IncludeGlobalServiceEvents', True),
                    is_multi_region_trail=trail_data.get('IsMultiRegionTrail', False),
                    is_organization_trail=trail_data.get('IsOrganizationTrail', False),
                    has_custom_event_selectors=trail_data.get('HasCustomEventSelectors', False),
                    has_insight_selectors=trail_data.get('HasInsightSelectors', False),
                    kms_key_id=trail_data.get('KMSKeyId'),
                    log_file_validation_enabled=trail_data.get('LogFileValidationEnabled', False),
                    cloud_watch_logs_log_group_arn=trail_data.get('CloudWatchLogsLogGroupArn'),
                    cloud_watch_logs_role_arn=trail_data.get('CloudWatchLogsRoleArn')
                )
                
                try:
                    status = self.cloudtrail_client.get_trail_status(Name=trail.name)
                    trail.is_logging = status.get('IsLogging', False)
                except Exception:
                    pass
                
                trails.append(trail)
        except Exception as e:
            self.logger.error(f"Erro ao listar trails: {e}")
        
        return trails
    
    def get_event_data_stores(self) -> List[EventDataStore]:
        data_stores = []
        try:
            paginator = self.cloudtrail_client.get_paginator('list_event_data_stores')
            
            for page in paginator.paginate():
                for store in page.get('EventDataStores', []):
                    data_stores.append(EventDataStore(
                        name=store.get('Name', ''),
                        event_data_store_arn=store.get('EventDataStoreArn'),
                        status=store.get('Status', 'ENABLED'),
                        retention_period=store.get('RetentionPeriod', 2557),
                        multi_region_enabled=store.get('MultiRegionEnabled', True),
                        organization_enabled=store.get('OrganizationEnabled', False),
                        termination_protection_enabled=store.get('TerminationProtectionEnabled', True),
                        created_timestamp=store.get('CreatedTimestamp'),
                        updated_timestamp=store.get('UpdatedTimestamp')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar event data stores: {e}")
        
        return data_stores
    
    def get_channels(self) -> List[Channel]:
        channels = []
        try:
            paginator = self.cloudtrail_client.get_paginator('list_channels')
            
            for page in paginator.paginate():
                for channel in page.get('Channels', []):
                    channels.append(Channel(
                        channel_arn=channel.get('ChannelArn', ''),
                        name=channel.get('Name', ''),
                        source=channel.get('Source', ''),
                        destinations=channel.get('Destinations', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar channels: {e}")
        
        return channels
    
    def get_resources(self) -> Dict[str, Any]:
        trails = self.get_trails()
        data_stores = self.get_event_data_stores()
        channels = self.get_channels()
        
        return {
            'trails': [t.to_dict() for t in trails],
            'event_data_stores': [d.to_dict() for d in data_stores],
            'channels': [c.to_dict() for c in channels],
            'summary': {
                'total_trails': len(trails),
                'logging_trails': sum(1 for t in trails if t.is_logging),
                'encrypted_trails': sum(1 for t in trails if t.is_encrypted),
                'multi_region_trails': sum(1 for t in trails if t.is_multi_region_trail),
                'organization_trails': sum(1 for t in trails if t.is_organization_trail),
                'total_data_stores': len(data_stores),
                'enabled_data_stores': sum(1 for d in data_stores if d.is_enabled),
                'total_channels': len(channels)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        trails = self.get_trails()
        data_stores = self.get_event_data_stores()
        
        return {
            'total_trails': len(trails),
            'trail_status': {
                'logging': sum(1 for t in trails if t.is_logging),
                'not_logging': sum(1 for t in trails if not t.is_logging)
            },
            'trail_features': {
                'encrypted': sum(1 for t in trails if t.is_encrypted),
                'log_validation': sum(1 for t in trails if t.has_log_validation),
                'cloudwatch_logs': sum(1 for t in trails if t.has_cloudwatch_logs),
                'multi_region': sum(1 for t in trails if t.is_multi_region_trail)
            },
            'event_data_stores': {
                'total': len(data_stores),
                'enabled': sum(1 for d in data_stores if d.is_enabled),
                'long_retention': sum(1 for d in data_stores if d.is_long_retention)
            }
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        trails = self.get_trails()
        data_stores = self.get_event_data_stores()
        
        if len(trails) == 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'CloudTrail',
                'title': 'Nenhum trail configurado',
                'description': 'CloudTrail não tem nenhum trail configurado. Atividades de API não estão sendo rastreadas.',
                'action': 'Criar trail para auditoria de atividades de API',
                'estimated_savings': 'N/A',
                'priority': 'CRITICAL'
            })
        
        for trail in trails:
            if not trail.is_logging:
                recommendations.append({
                    'resource_id': trail.name,
                    'resource_type': 'CloudTrail Trail',
                    'title': 'Trail não está logando',
                    'description': f'Trail {trail.name} não está gravando logs.',
                    'action': 'Iniciar logging no trail para auditoria',
                    'estimated_savings': 'N/A',
                    'priority': 'CRITICAL'
                })
            
            if not trail.is_encrypted:
                recommendations.append({
                    'resource_id': trail.name,
                    'resource_type': 'CloudTrail Trail',
                    'title': 'Trail sem criptografia KMS',
                    'description': f'Trail {trail.name} não usa criptografia KMS.',
                    'action': 'Habilitar criptografia KMS para logs do trail',
                    'estimated_savings': 'N/A',
                    'priority': 'HIGH'
                })
            
            if not trail.has_log_validation:
                recommendations.append({
                    'resource_id': trail.name,
                    'resource_type': 'CloudTrail Trail',
                    'title': 'Validação de logs não habilitada',
                    'description': f'Trail {trail.name} não tem validação de integridade de logs.',
                    'action': 'Habilitar log file validation para detectar alterações',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
            
            if not trail.is_multi_region_trail:
                recommendations.append({
                    'resource_id': trail.name,
                    'resource_type': 'CloudTrail Trail',
                    'title': 'Trail não é multi-região',
                    'description': f'Trail {trail.name} captura eventos apenas de uma região.',
                    'action': 'Converter para multi-region trail para cobertura completa',
                    'estimated_savings': 'N/A',
                    'priority': 'MEDIUM'
                })
        
        for data_store in data_stores:
            if data_store.is_long_retention:
                recommendations.append({
                    'resource_id': data_store.name,
                    'resource_type': 'Event Data Store',
                    'title': f'Retenção longa ({data_store.retention_years:.1f} anos)',
                    'description': f'Event Data Store {data_store.name} tem retenção de {data_store.retention_years:.1f} anos.',
                    'action': 'Revisar período de retenção para otimizar custos de armazenamento',
                    'estimated_savings': 'Médio',
                    'priority': 'LOW'
                })
        
        return recommendations
