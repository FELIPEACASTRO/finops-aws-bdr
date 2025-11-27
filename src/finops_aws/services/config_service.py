"""
AWS Config FinOps Service

Análise de conformidade, regras e recomendações de configuração.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ConfigRule:
    """Representa uma regra do AWS Config"""
    rule_name: str
    rule_id: Optional[str] = None
    rule_arn: Optional[str] = None
    description: Optional[str] = None
    source_identifier: str = ''
    source_owner: str = 'AWS'
    config_rule_state: str = 'ACTIVE'
    compliance_status: str = 'NOT_APPLICABLE'
    compliant_count: int = 0
    non_compliant_count: int = 0
    
    @property
    def is_active(self) -> bool:
        return self.config_rule_state == 'ACTIVE'
    
    @property
    def is_aws_managed(self) -> bool:
        return self.source_owner == 'AWS'
    
    @property
    def is_custom(self) -> bool:
        return self.source_owner == 'CUSTOM_LAMBDA'
    
    @property
    def is_compliant(self) -> bool:
        return self.compliance_status == 'COMPLIANT'
    
    @property
    def is_non_compliant(self) -> bool:
        return self.compliance_status == 'NON_COMPLIANT'
    
    @property
    def total_evaluated(self) -> int:
        return self.compliant_count + self.non_compliant_count
    
    @property
    def compliance_percentage(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return (self.compliant_count / self.total_evaluated) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_name': self.rule_name,
            'rule_id': self.rule_id,
            'rule_arn': self.rule_arn,
            'description': self.description,
            'source_identifier': self.source_identifier,
            'source_owner': self.source_owner,
            'config_rule_state': self.config_rule_state,
            'compliance_status': self.compliance_status,
            'compliant_count': self.compliant_count,
            'non_compliant_count': self.non_compliant_count,
            'is_active': self.is_active,
            'is_aws_managed': self.is_aws_managed,
            'is_compliant': self.is_compliant,
            'compliance_percentage': round(self.compliance_percentage, 2)
        }


@dataclass
class ConfigurationRecorder:
    """Representa um configuration recorder"""
    name: str
    role_arn: Optional[str] = None
    recording_group: Dict = field(default_factory=dict)
    status: str = 'STOPPED'
    last_status_change_time: Optional[datetime] = None
    last_start_time: Optional[datetime] = None
    last_stop_time: Optional[datetime] = None
    
    @property
    def is_recording(self) -> bool:
        return self.status == 'SUCCESS' or self.status == 'PENDING'
    
    @property
    def records_all_resources(self) -> bool:
        return self.recording_group.get('allSupported', False)
    
    @property
    def includes_global_resources(self) -> bool:
        return self.recording_group.get('includeGlobalResourceTypes', False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'role_arn': self.role_arn,
            'status': self.status,
            'is_recording': self.is_recording,
            'records_all_resources': self.records_all_resources,
            'includes_global_resources': self.includes_global_resources
        }


@dataclass
class DeliveryChannel:
    """Representa um delivery channel"""
    name: str
    s3_bucket_name: Optional[str] = None
    s3_key_prefix: Optional[str] = None
    sns_topic_arn: Optional[str] = None
    config_snapshot_delivery_properties: Dict = field(default_factory=dict)
    
    @property
    def has_s3_bucket(self) -> bool:
        return self.s3_bucket_name is not None
    
    @property
    def has_sns_topic(self) -> bool:
        return self.sns_topic_arn is not None
    
    @property
    def delivery_frequency(self) -> str:
        return self.config_snapshot_delivery_properties.get('deliveryFrequency', 'TwentyFour_Hours')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            's3_bucket_name': self.s3_bucket_name,
            's3_key_prefix': self.s3_key_prefix,
            'sns_topic_arn': self.sns_topic_arn,
            'has_s3_bucket': self.has_s3_bucket,
            'has_sns_topic': self.has_sns_topic,
            'delivery_frequency': self.delivery_frequency
        }


@dataclass
class ConformancePack:
    """Representa um conformance pack"""
    name: str
    conformance_pack_arn: Optional[str] = None
    conformance_pack_id: Optional[str] = None
    delivery_s3_bucket: Optional[str] = None
    conformance_pack_state: str = 'CREATE_COMPLETE'
    
    @property
    def is_complete(self) -> bool:
        return self.conformance_pack_state == 'CREATE_COMPLETE'
    
    @property
    def is_failed(self) -> bool:
        return 'FAILED' in self.conformance_pack_state
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'conformance_pack_arn': self.conformance_pack_arn,
            'conformance_pack_id': self.conformance_pack_id,
            'delivery_s3_bucket': self.delivery_s3_bucket,
            'conformance_pack_state': self.conformance_pack_state,
            'is_complete': self.is_complete,
            'is_failed': self.is_failed
        }


class ConfigService(BaseAWSService):
    """Serviço FinOps para AWS Config"""
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._config_client = None
        self.logger = logger
    
    @property
    def service_name(self) -> str:
        return "config"
    
    @property
    def config_client(self):
        if self._config_client is None:
            if self._client_factory:
                self._config_client = self._client_factory.get_client('config')
            else:
                import boto3
                self._config_client = boto3.client('config')
        return self._config_client
    
    def health_check(self) -> bool:
        try:
            self.config_client.describe_configuration_recorders()
            return True
        except Exception:
            return False
    
    def get_config_rules(self) -> List[ConfigRule]:
        rules = []
        try:
            paginator = self.config_client.get_paginator('describe_config_rules')
            
            for page in paginator.paginate():
                for rule in page.get('ConfigRules', []):
                    source = rule.get('Source', {})
                    rules.append(ConfigRule(
                        rule_name=rule.get('ConfigRuleName', ''),
                        rule_id=rule.get('ConfigRuleId'),
                        rule_arn=rule.get('ConfigRuleArn'),
                        description=rule.get('Description'),
                        source_identifier=source.get('SourceIdentifier', ''),
                        source_owner=source.get('Owner', 'AWS'),
                        config_rule_state=rule.get('ConfigRuleState', 'ACTIVE')
                    ))
            
            for rule in rules:
                try:
                    compliance = self.config_client.describe_compliance_by_config_rule(
                        ConfigRuleNames=[rule.rule_name]
                    )
                    for comp in compliance.get('ComplianceByConfigRules', []):
                        rule.compliance_status = comp.get('Compliance', {}).get('ComplianceType', 'NOT_APPLICABLE')
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Erro ao listar regras Config: {e}")
        
        return rules
    
    def get_configuration_recorders(self) -> List[ConfigurationRecorder]:
        recorders = []
        try:
            response = self.config_client.describe_configuration_recorders()
            status_response = self.config_client.describe_configuration_recorder_status()
            
            status_map = {}
            for status in status_response.get('ConfigurationRecordersStatus', []):
                status_map[status.get('name', '')] = status
            
            for recorder in response.get('ConfigurationRecorders', []):
                name = recorder.get('name', '')
                status = status_map.get(name, {})
                
                recorders.append(ConfigurationRecorder(
                    name=name,
                    role_arn=recorder.get('roleARN'),
                    recording_group=recorder.get('recordingGroup', {}),
                    status='SUCCESS' if status.get('recording', False) else 'STOPPED',
                    last_status_change_time=status.get('lastStatusChangeTime'),
                    last_start_time=status.get('lastStartTime'),
                    last_stop_time=status.get('lastStopTime')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar configuration recorders: {e}")
        
        return recorders
    
    def get_delivery_channels(self) -> List[DeliveryChannel]:
        channels = []
        try:
            response = self.config_client.describe_delivery_channels()
            
            for channel in response.get('DeliveryChannels', []):
                channels.append(DeliveryChannel(
                    name=channel.get('name', ''),
                    s3_bucket_name=channel.get('s3BucketName'),
                    s3_key_prefix=channel.get('s3KeyPrefix'),
                    sns_topic_arn=channel.get('snsTopicARN'),
                    config_snapshot_delivery_properties=channel.get('configSnapshotDeliveryProperties', {})
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar delivery channels: {e}")
        
        return channels
    
    def get_conformance_packs(self) -> List[ConformancePack]:
        packs = []
        try:
            paginator = self.config_client.get_paginator('describe_conformance_packs')
            
            for page in paginator.paginate():
                for pack in page.get('ConformancePackDetails', []):
                    packs.append(ConformancePack(
                        name=pack.get('ConformancePackName', ''),
                        conformance_pack_arn=pack.get('ConformancePackArn'),
                        conformance_pack_id=pack.get('ConformancePackId'),
                        delivery_s3_bucket=pack.get('DeliveryS3Bucket')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar conformance packs: {e}")
        
        return packs
    
    def get_resources(self) -> Dict[str, Any]:
        rules = self.get_config_rules()
        recorders = self.get_configuration_recorders()
        channels = self.get_delivery_channels()
        packs = self.get_conformance_packs()
        
        return {
            'config_rules': [r.to_dict() for r in rules],
            'configuration_recorders': [r.to_dict() for r in recorders],
            'delivery_channels': [c.to_dict() for c in channels],
            'conformance_packs': [p.to_dict() for p in packs],
            'summary': {
                'total_rules': len(rules),
                'active_rules': sum(1 for r in rules if r.is_active),
                'aws_managed_rules': sum(1 for r in rules if r.is_aws_managed),
                'custom_rules': sum(1 for r in rules if r.is_custom),
                'compliant_rules': sum(1 for r in rules if r.is_compliant),
                'non_compliant_rules': sum(1 for r in rules if r.is_non_compliant),
                'total_recorders': len(recorders),
                'recording_recorders': sum(1 for r in recorders if r.is_recording),
                'total_conformance_packs': len(packs)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        rules = self.get_config_rules()
        recorders = self.get_configuration_recorders()
        
        return {
            'total_rules': len(rules),
            'rule_compliance': {
                'compliant': sum(1 for r in rules if r.is_compliant),
                'non_compliant': sum(1 for r in rules if r.is_non_compliant),
                'not_applicable': sum(1 for r in rules if not r.is_compliant and not r.is_non_compliant)
            },
            'rule_ownership': {
                'aws_managed': sum(1 for r in rules if r.is_aws_managed),
                'custom': sum(1 for r in rules if r.is_custom)
            },
            'recording_status': {
                'total': len(recorders),
                'recording': sum(1 for r in recorders if r.is_recording)
            }
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        rules = self.get_config_rules()
        recorders = self.get_configuration_recorders()
        channels = self.get_delivery_channels()
        
        if len(recorders) == 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'AWS Config',
                'title': 'Nenhum configuration recorder configurado',
                'description': 'AWS Config não tem configuration recorder configurado. Mudanças de recursos não estão sendo rastreadas.',
                'action': 'Criar configuration recorder para rastrear mudanças de recursos',
                'estimated_savings': 'N/A',
                'priority': 'CRITICAL'
            })
        else:
            for recorder in recorders:
                if not recorder.is_recording:
                    recommendations.append({
                        'resource_id': recorder.name,
                        'resource_type': 'Configuration Recorder',
                        'title': 'Recorder não está gravando',
                        'description': f'Configuration recorder {recorder.name} não está gravando.',
                        'action': 'Iniciar configuration recorder para rastrear mudanças',
                        'estimated_savings': 'N/A',
                        'priority': 'HIGH'
                    })
                
                if not recorder.records_all_resources:
                    recommendations.append({
                        'resource_id': recorder.name,
                        'resource_type': 'Configuration Recorder',
                        'title': 'Recorder não cobre todos os recursos',
                        'description': f'Configuration recorder {recorder.name} não está configurado para todos os recursos.',
                        'action': 'Habilitar recording para todos os tipos de recursos',
                        'estimated_savings': 'N/A',
                        'priority': 'MEDIUM'
                    })
        
        if len(channels) == 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'AWS Config',
                'title': 'Nenhum delivery channel configurado',
                'description': 'AWS Config não tem delivery channel configurado.',
                'action': 'Criar delivery channel para armazenar snapshots de configuração',
                'estimated_savings': 'N/A',
                'priority': 'HIGH'
            })
        
        non_compliant_rules = [r for r in rules if r.is_non_compliant]
        if len(non_compliant_rules) > 0:
            recommendations.append({
                'resource_id': 'ALL',
                'resource_type': 'Config Rules',
                'title': f'{len(non_compliant_rules)} regras com recursos não conformes',
                'description': f'Há {len(non_compliant_rules)} regras com recursos não conformes.',
                'action': 'Revisar e remediar recursos não conformes',
                'estimated_savings': 'N/A',
                'priority': 'HIGH'
            })
        
        return recommendations
