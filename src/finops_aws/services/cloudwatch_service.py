"""
CloudWatch FinOps Service

Análise de custos e otimização para Amazon CloudWatch:
- Log Groups e retenção
- Métricas customizadas
- Alarmes e dashboards
- Insights queries
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class LogGroup:
    """Representa um Log Group do CloudWatch"""
    log_group_name: str
    arn: Optional[str] = None
    creation_time: Optional[datetime] = None
    retention_in_days: Optional[int] = None
    stored_bytes: int = 0
    metric_filter_count: int = 0
    kms_key_id: Optional[str] = None
    data_protection_status: Optional[str] = None
    
    @property
    def has_retention_policy(self) -> bool:
        return self.retention_in_days is not None
    
    @property
    def is_encrypted(self) -> bool:
        return self.kms_key_id is not None
    
    @property
    def stored_gb(self) -> float:
        return self.stored_bytes / (1024 ** 3)
    
    @property
    def has_metric_filters(self) -> bool:
        return self.metric_filter_count > 0
    
    @property
    def retention_cost_risk(self) -> str:
        if self.retention_in_days is None:
            return 'HIGH'
        elif self.retention_in_days > 365:
            return 'MEDIUM'
        return 'LOW'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_group_name': self.log_group_name,
            'arn': self.arn,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'retention_in_days': self.retention_in_days,
            'stored_bytes': self.stored_bytes,
            'stored_gb': round(self.stored_gb, 2),
            'metric_filter_count': self.metric_filter_count,
            'kms_key_id': self.kms_key_id,
            'has_retention_policy': self.has_retention_policy,
            'is_encrypted': self.is_encrypted,
            'retention_cost_risk': self.retention_cost_risk
        }


@dataclass
class CloudWatchAlarm:
    """Representa um Alarme do CloudWatch"""
    alarm_name: str
    alarm_arn: Optional[str] = None
    state_value: str = 'OK'
    metric_name: Optional[str] = None
    namespace: Optional[str] = None
    statistic: Optional[str] = None
    period: int = 300
    evaluation_periods: int = 1
    threshold: Optional[float] = None
    comparison_operator: Optional[str] = None
    actions_enabled: bool = True
    alarm_actions: List[str] = field(default_factory=list)
    ok_actions: List[str] = field(default_factory=list)
    insufficient_data_actions: List[str] = field(default_factory=list)
    
    @property
    def is_in_alarm(self) -> bool:
        return self.state_value == 'ALARM'
    
    @property
    def has_actions(self) -> bool:
        return len(self.alarm_actions) > 0 or len(self.ok_actions) > 0
    
    @property
    def is_high_resolution(self) -> bool:
        return self.period < 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alarm_name': self.alarm_name,
            'alarm_arn': self.alarm_arn,
            'state_value': self.state_value,
            'metric_name': self.metric_name,
            'namespace': self.namespace,
            'period': self.period,
            'evaluation_periods': self.evaluation_periods,
            'threshold': self.threshold,
            'actions_enabled': self.actions_enabled,
            'is_in_alarm': self.is_in_alarm,
            'has_actions': self.has_actions,
            'is_high_resolution': self.is_high_resolution
        }


@dataclass
class CloudWatchDashboard:
    """Representa um Dashboard do CloudWatch"""
    dashboard_name: str
    dashboard_arn: Optional[str] = None
    size: int = 0
    last_modified: Optional[datetime] = None
    
    @property
    def size_kb(self) -> float:
        return self.size / 1024
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dashboard_name': self.dashboard_name,
            'dashboard_arn': self.dashboard_arn,
            'size': self.size,
            'size_kb': round(self.size_kb, 2),
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        }


@dataclass  
class MetricStream:
    """Representa um Metric Stream do CloudWatch"""
    name: str
    arn: Optional[str] = None
    firehose_arn: Optional[str] = None
    state: str = 'running'
    creation_date: Optional[datetime] = None
    output_format: str = 'json'
    include_filters: List[Dict] = field(default_factory=list)
    exclude_filters: List[Dict] = field(default_factory=list)
    
    @property
    def is_running(self) -> bool:
        return self.state.lower() == 'running'
    
    @property
    def has_filters(self) -> bool:
        return len(self.include_filters) > 0 or len(self.exclude_filters) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'firehose_arn': self.firehose_arn,
            'state': self.state,
            'is_running': self.is_running,
            'output_format': self.output_format,
            'has_filters': self.has_filters
        }


class CloudWatchService(BaseAWSService):
    """
    Serviço FinOps para análise de custos CloudWatch
    
    Analisa Log Groups, Alarmes, Dashboards, Metric Streams
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._logs_client = None
        self._cloudwatch_client = None
    
    @property
    def logs_client(self):
        if self._logs_client is None:
            if self._client_factory:
                self._logs_client = self._client_factory.get_client('logs')
            else:
                import boto3
                self._logs_client = boto3.client('logs')
        return self._logs_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            if self._client_factory:
                self._cloudwatch_client = self._client_factory.get_client('cloudwatch')
            else:
                import boto3
                self._cloudwatch_client = boto3.client('cloudwatch')
        return self._cloudwatch_client
    
    @property
    def service_name(self) -> str:
        return "Amazon CloudWatch"
    
    def health_check(self) -> bool:
        try:
            self.logs_client.describe_log_groups(limit=1)
            return True
        except Exception:
            return False
    
    def get_log_groups(self) -> List[LogGroup]:
        log_groups = []
        try:
            paginator = self.logs_client.get_paginator('describe_log_groups')
            for page in paginator.paginate():
                for lg in page.get('logGroups', []):
                    log_groups.append(LogGroup(
                        log_group_name=lg.get('logGroupName', ''),
                        arn=lg.get('arn'),
                        creation_time=datetime.fromtimestamp(lg['creationTime'] / 1000) if lg.get('creationTime') else None,
                        retention_in_days=lg.get('retentionInDays'),
                        stored_bytes=lg.get('storedBytes', 0),
                        metric_filter_count=lg.get('metricFilterCount', 0),
                        kms_key_id=lg.get('kmsKeyId'),
                        data_protection_status=lg.get('dataProtectionStatus')
                    ))
        except Exception:
            pass
        return log_groups
    
    def get_alarms(self) -> List[CloudWatchAlarm]:
        alarms = []
        try:
            paginator = self.cloudwatch_client.get_paginator('describe_alarms')
            for page in paginator.paginate():
                for alarm in page.get('MetricAlarms', []):
                    alarms.append(CloudWatchAlarm(
                        alarm_name=alarm.get('AlarmName', ''),
                        alarm_arn=alarm.get('AlarmArn'),
                        state_value=alarm.get('StateValue', 'OK'),
                        metric_name=alarm.get('MetricName'),
                        namespace=alarm.get('Namespace'),
                        statistic=alarm.get('Statistic'),
                        period=alarm.get('Period', 300),
                        evaluation_periods=alarm.get('EvaluationPeriods', 1),
                        threshold=alarm.get('Threshold'),
                        comparison_operator=alarm.get('ComparisonOperator'),
                        actions_enabled=alarm.get('ActionsEnabled', True),
                        alarm_actions=alarm.get('AlarmActions', []),
                        ok_actions=alarm.get('OKActions', []),
                        insufficient_data_actions=alarm.get('InsufficientDataActions', [])
                    ))
        except Exception:
            pass
        return alarms
    
    def get_dashboards(self) -> List[CloudWatchDashboard]:
        dashboards = []
        try:
            paginator = self.cloudwatch_client.get_paginator('list_dashboards')
            for page in paginator.paginate():
                for db in page.get('DashboardEntries', []):
                    dashboards.append(CloudWatchDashboard(
                        dashboard_name=db.get('DashboardName', ''),
                        dashboard_arn=db.get('DashboardArn'),
                        size=db.get('Size', 0),
                        last_modified=db.get('LastModified')
                    ))
        except Exception:
            pass
        return dashboards
    
    def get_metric_streams(self) -> List[MetricStream]:
        streams = []
        try:
            paginator = self.cloudwatch_client.get_paginator('list_metric_streams')
            for page in paginator.paginate():
                for stream in page.get('Entries', []):
                    streams.append(MetricStream(
                        name=stream.get('Name', ''),
                        arn=stream.get('Arn'),
                        firehose_arn=stream.get('FirehoseArn'),
                        state=stream.get('State', 'running'),
                        creation_date=stream.get('CreationDate'),
                        output_format=stream.get('OutputFormat', 'json')
                    ))
        except Exception:
            pass
        return streams
    
    def get_resources(self) -> Dict[str, Any]:
        log_groups = self.get_log_groups()
        alarms = self.get_alarms()
        dashboards = self.get_dashboards()
        metric_streams = self.get_metric_streams()
        
        total_stored_bytes = sum(lg.stored_bytes for lg in log_groups)
        no_retention_count = sum(1 for lg in log_groups if not lg.has_retention_policy)
        alarms_in_alarm = sum(1 for a in alarms if a.is_in_alarm)
        
        return {
            'log_groups': [lg.to_dict() for lg in log_groups],
            'alarms': [a.to_dict() for a in alarms],
            'dashboards': [d.to_dict() for d in dashboards],
            'metric_streams': [s.to_dict() for s in metric_streams],
            'summary': {
                'total_log_groups': len(log_groups),
                'total_stored_gb': round(total_stored_bytes / (1024 ** 3), 2),
                'log_groups_without_retention': no_retention_count,
                'total_alarms': len(alarms),
                'alarms_in_alarm_state': alarms_in_alarm,
                'total_dashboards': len(dashboards),
                'total_metric_streams': len(metric_streams)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        return {
            'service': self.service_name,
            'log_groups_count': resources['summary']['total_log_groups'],
            'total_stored_gb': resources['summary']['total_stored_gb'],
            'alarms_count': resources['summary']['total_alarms'],
            'dashboards_count': resources['summary']['total_dashboards']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        log_groups = self.get_log_groups()
        alarms = self.get_alarms()
        
        for lg in log_groups:
            if not lg.has_retention_policy:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=lg.log_group_name,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Configure Log Retention Policy',
                    description=f'Log group {lg.log_group_name} has no retention policy. Logs are stored indefinitely, incurring ongoing storage costs.',
                    action=f'Set retention policy (e.g., 30, 90, or 365 days) for log group {lg.log_group_name}',
                    estimated_savings=lg.stored_gb * 0.03,
                    priority='HIGH',
                    impact='HIGH'
                ))
            
            if lg.stored_gb > 100 and not lg.is_encrypted:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=lg.log_group_name,
                    recommendation_type='SECURITY',
                    title='Enable Log Group Encryption',
                    description=f'Large log group {lg.log_group_name} ({lg.stored_gb:.1f} GB) is not encrypted with KMS.',
                    action='Enable KMS encryption for sensitive log data',
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
        
        for alarm in alarms:
            if not alarm.has_actions:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=alarm.alarm_name,
                    recommendation_type='OPERATIONAL',
                    title='Add Alarm Actions',
                    description=f'Alarm {alarm.alarm_name} has no actions configured. Alerts will not trigger notifications.',
                    action='Configure SNS topic or other actions for alarm notifications',
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
            
            if alarm.is_high_resolution:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=alarm.alarm_name,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Review High-Resolution Alarm',
                    description=f'Alarm {alarm.alarm_name} uses high-resolution metrics (period < 60s), which costs 3x more.',
                    action='Consider if standard resolution (60s+) would meet requirements',
                    estimated_savings=0.30,
                    priority='LOW',
                    impact='LOW'
                ))
        
        return recommendations
