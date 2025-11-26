"""
EventBridge FinOps Service

Análise de custos e otimização para Amazon EventBridge:
- Event Buses
- Rules
- Archives
- Pipes
- Schemas
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class EventBus:
    """Representa um Event Bus do EventBridge"""
    name: str
    arn: Optional[str] = None
    policy: Optional[str] = None
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    
    @property
    def is_default(self) -> bool:
        return self.name == 'default'
    
    @property
    def is_custom(self) -> bool:
        return not self.is_default and not self.name.startswith('aws.')
    
    @property
    def has_policy(self) -> bool:
        return self.policy is not None and len(self.policy) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'is_default': self.is_default,
            'is_custom': self.is_custom,
            'has_policy': self.has_policy,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class EventRule:
    """Representa uma Rule do EventBridge"""
    name: str
    arn: Optional[str] = None
    event_bus_name: str = 'default'
    event_pattern: Optional[str] = None
    schedule_expression: Optional[str] = None
    state: str = 'ENABLED'
    description: Optional[str] = None
    managed_by: Optional[str] = None
    targets_count: int = 0
    
    @property
    def is_enabled(self) -> bool:
        return self.state == 'ENABLED'
    
    @property
    def is_scheduled(self) -> bool:
        return self.schedule_expression is not None
    
    @property
    def is_event_pattern(self) -> bool:
        return self.event_pattern is not None
    
    @property
    def is_managed(self) -> bool:
        return self.managed_by is not None
    
    @property
    def has_targets(self) -> bool:
        return self.targets_count > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'event_bus_name': self.event_bus_name,
            'state': self.state,
            'is_enabled': self.is_enabled,
            'is_scheduled': self.is_scheduled,
            'is_event_pattern': self.is_event_pattern,
            'is_managed': self.is_managed,
            'has_targets': self.has_targets,
            'targets_count': self.targets_count,
            'schedule_expression': self.schedule_expression,
            'description': self.description
        }


@dataclass
class EventArchive:
    """Representa um Archive do EventBridge"""
    archive_name: str
    event_source_arn: Optional[str] = None
    state: str = 'ENABLED'
    state_reason: Optional[str] = None
    retention_days: int = 0
    size_bytes: int = 0
    event_count: int = 0
    creation_time: Optional[datetime] = None
    
    @property
    def is_enabled(self) -> bool:
        return self.state == 'ENABLED'
    
    @property
    def has_retention(self) -> bool:
        return self.retention_days > 0
    
    @property
    def is_unlimited_retention(self) -> bool:
        return self.retention_days == 0
    
    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 ** 2)
    
    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'archive_name': self.archive_name,
            'event_source_arn': self.event_source_arn,
            'state': self.state,
            'is_enabled': self.is_enabled,
            'retention_days': self.retention_days,
            'has_retention': self.has_retention,
            'is_unlimited_retention': self.is_unlimited_retention,
            'size_bytes': self.size_bytes,
            'size_mb': round(self.size_mb, 2),
            'event_count': self.event_count,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class EventPipe:
    """Representa um Pipe do EventBridge"""
    name: str
    arn: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None
    desired_state: str = 'RUNNING'
    current_state: str = 'RUNNING'
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    enrichment: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        return self.current_state == 'RUNNING'
    
    @property
    def is_stopped(self) -> bool:
        return self.current_state == 'STOPPED'
    
    @property
    def has_enrichment(self) -> bool:
        return self.enrichment is not None
    
    @property
    def state_mismatch(self) -> bool:
        return self.desired_state != self.current_state
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'arn': self.arn,
            'source': self.source,
            'target': self.target,
            'desired_state': self.desired_state,
            'current_state': self.current_state,
            'is_running': self.is_running,
            'has_enrichment': self.has_enrichment,
            'state_mismatch': self.state_mismatch,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class SchemaRegistry:
    """Representa um Schema Registry do EventBridge"""
    registry_name: str
    registry_arn: Optional[str] = None
    description: Optional[str] = None
    schema_count: int = 0
    
    @property
    def is_discovered(self) -> bool:
        return self.registry_name.startswith('aws.events')
    
    @property
    def is_custom(self) -> bool:
        return not self.is_discovered
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'registry_name': self.registry_name,
            'registry_arn': self.registry_arn,
            'description': self.description,
            'schema_count': self.schema_count,
            'is_discovered': self.is_discovered,
            'is_custom': self.is_custom
        }


class EventBridgeService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Amazon EventBridge
    
    Analisa Event Buses, Rules, Archives, Pipes
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self._events_client = None
        self._pipes_client = None
        self._schemas_client = None
    
    @property
    def events_client(self):
        if self._events_client is None:
            if self._client_factory:
                self._events_client = self._client_factory.get_client('events')
            else:
                import boto3
                self._events_client = boto3.client('events')
        return self._events_client
    
    @property
    def pipes_client(self):
        if self._pipes_client is None:
            if self._client_factory:
                self._pipes_client = self._client_factory.get_client('pipes')
            else:
                import boto3
                self._pipes_client = boto3.client('pipes')
        return self._pipes_client
    
    @property
    def schemas_client(self):
        if self._schemas_client is None:
            if self._client_factory:
                self._schemas_client = self._client_factory.get_client('schemas')
            else:
                import boto3
                self._schemas_client = boto3.client('schemas')
        return self._schemas_client
    
    @property
    def service_name(self) -> str:
        return "Amazon EventBridge"
    
    def health_check(self) -> bool:
        try:
            self.events_client.list_event_buses(Limit=1)
            return True
        except Exception:
            return False
    
    def get_event_buses(self) -> List[EventBus]:
        event_buses = []
        try:
            response = self.events_client.list_event_buses(Limit=100)
            for bus in response.get('EventBuses', []):
                event_buses.append(EventBus(
                    name=bus.get('Name', ''),
                    arn=bus.get('Arn'),
                    policy=bus.get('Policy')
                ))
        except Exception:
            pass
        return event_buses
    
    def get_rules(self, event_bus_name: str = 'default') -> List[EventRule]:
        rules = []
        try:
            paginator = self.events_client.get_paginator('list_rules')
            for page in paginator.paginate(EventBusName=event_bus_name):
                for rule in page.get('Rules', []):
                    targets_count = 0
                    try:
                        targets_response = self.events_client.list_targets_by_rule(
                            Rule=rule['Name'],
                            EventBusName=event_bus_name
                        )
                        targets_count = len(targets_response.get('Targets', []))
                    except Exception:
                        pass
                    
                    rules.append(EventRule(
                        name=rule.get('Name', ''),
                        arn=rule.get('Arn'),
                        event_bus_name=event_bus_name,
                        event_pattern=rule.get('EventPattern'),
                        schedule_expression=rule.get('ScheduleExpression'),
                        state=rule.get('State', 'ENABLED'),
                        description=rule.get('Description'),
                        managed_by=rule.get('ManagedBy'),
                        targets_count=targets_count
                    ))
        except Exception:
            pass
        return rules
    
    def get_archives(self) -> List[EventArchive]:
        archives = []
        try:
            response = self.events_client.list_archives(Limit=100)
            for archive in response.get('Archives', []):
                archives.append(EventArchive(
                    archive_name=archive.get('ArchiveName', ''),
                    event_source_arn=archive.get('EventSourceArn'),
                    state=archive.get('State', 'ENABLED'),
                    state_reason=archive.get('StateReason'),
                    retention_days=archive.get('RetentionDays', 0),
                    size_bytes=archive.get('SizeBytes', 0),
                    event_count=archive.get('EventCount', 0),
                    creation_time=archive.get('CreationTime')
                ))
        except Exception:
            pass
        return archives
    
    def get_pipes(self) -> List[EventPipe]:
        pipes = []
        try:
            paginator = self.pipes_client.get_paginator('list_pipes')
            for page in paginator.paginate():
                for pipe in page.get('Pipes', []):
                    pipes.append(EventPipe(
                        name=pipe.get('Name', ''),
                        arn=pipe.get('Arn'),
                        source=pipe.get('Source'),
                        target=pipe.get('Target'),
                        desired_state=pipe.get('DesiredState', 'RUNNING'),
                        current_state=pipe.get('CurrentState', 'RUNNING'),
                        creation_time=pipe.get('CreationTime'),
                        last_modified_time=pipe.get('LastModifiedTime'),
                        enrichment=pipe.get('Enrichment')
                    ))
        except Exception:
            pass
        return pipes
    
    def get_schema_registries(self) -> List[SchemaRegistry]:
        registries = []
        try:
            paginator = self.schemas_client.get_paginator('list_registries')
            for page in paginator.paginate():
                for registry in page.get('Registries', []):
                    registries.append(SchemaRegistry(
                        registry_name=registry.get('RegistryName', ''),
                        registry_arn=registry.get('RegistryArn')
                    ))
        except Exception:
            pass
        return registries
    
    def get_resources(self) -> Dict[str, Any]:
        event_buses = self.get_event_buses()
        archives = self.get_archives()
        pipes = self.get_pipes()
        registries = self.get_schema_registries()
        
        all_rules = []
        for bus in event_buses:
            rules = self.get_rules(bus.name)
            all_rules.extend(rules)
        
        total_archive_size = sum(a.size_bytes for a in archives)
        disabled_rules = sum(1 for r in all_rules if not r.is_enabled)
        rules_without_targets = sum(1 for r in all_rules if not r.has_targets)
        unlimited_retention_archives = sum(1 for a in archives if a.is_unlimited_retention)
        
        return {
            'event_buses': [b.to_dict() for b in event_buses],
            'rules': [r.to_dict() for r in all_rules],
            'archives': [a.to_dict() for a in archives],
            'pipes': [p.to_dict() for p in pipes],
            'schema_registries': [r.to_dict() for r in registries],
            'summary': {
                'total_event_buses': len(event_buses),
                'total_rules': len(all_rules),
                'disabled_rules': disabled_rules,
                'rules_without_targets': rules_without_targets,
                'total_archives': len(archives),
                'total_archive_size_gb': round(total_archive_size / (1024 ** 3), 2),
                'unlimited_retention_archives': unlimited_retention_archives,
                'total_pipes': len(pipes),
                'total_schema_registries': len(registries)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        return {
            'service': self.service_name,
            'event_buses_count': resources['summary']['total_event_buses'],
            'rules_count': resources['summary']['total_rules'],
            'archives_count': resources['summary']['total_archives'],
            'pipes_count': resources['summary']['total_pipes']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        event_buses = self.get_event_buses()
        archives = self.get_archives()
        pipes = self.get_pipes()
        
        for bus in event_buses:
            rules = self.get_rules(bus.name)
            for rule in rules:
                if rule.is_enabled and not rule.has_targets:
                    recommendations.append(ServiceRecommendation(
                        service=self.service_name,
                        resource_id=rule.name,
                        recommendation_type='COST_OPTIMIZATION',
                        title='Rule Has No Targets',
                        description=f'Rule {rule.name} on bus {bus.name} is enabled but has no targets. Events are processed but not delivered.',
                        action='Add targets or disable/delete the rule',
                        priority='MEDIUM',
                        impact='LOW'
                    ))
                
                if not rule.is_enabled and not rule.is_managed:
                    recommendations.append(ServiceRecommendation(
                        service=self.service_name,
                        resource_id=rule.name,
                        recommendation_type='COST_OPTIMIZATION',
                        title='Review Disabled Rule',
                        description=f'Rule {rule.name} is disabled. Consider deleting if no longer needed.',
                        action='Delete unused rule or document why it is disabled',
                        priority='LOW',
                        impact='LOW'
                    ))
        
        for archive in archives:
            if archive.is_unlimited_retention:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=archive.archive_name,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Configure Archive Retention',
                    description=f'Archive {archive.archive_name} has unlimited retention ({archive.size_mb:.1f} MB). Storage costs grow indefinitely.',
                    action='Set retention period based on compliance requirements',
                    estimated_savings=archive.size_gb * 0.023,
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
            
            if archive.size_gb > 10 and not archive.is_enabled:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=archive.archive_name,
                    recommendation_type='COST_OPTIMIZATION',
                    title='Large Disabled Archive',
                    description=f'Archive {archive.archive_name} is disabled but still storing {archive.size_gb:.1f} GB.',
                    action='Delete archive if events are no longer needed',
                    estimated_savings=archive.size_gb * 0.023,
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
        
        for pipe in pipes:
            if pipe.is_stopped:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pipe.name,
                    recommendation_type='OPERATIONAL',
                    title='Stopped Pipe',
                    description=f'Pipe {pipe.name} is stopped. Events are not being processed.',
                    action='Start pipe or delete if no longer needed',
                    priority='MEDIUM',
                    impact='MEDIUM'
                ))
            
            if pipe.state_mismatch:
                recommendations.append(ServiceRecommendation(
                    service=self.service_name,
                    resource_id=pipe.name,
                    recommendation_type='OPERATIONAL',
                    title='Pipe State Mismatch',
                    description=f'Pipe {pipe.name} desired state ({pipe.desired_state}) differs from current ({pipe.current_state}).',
                    action='Investigate why pipe is not in desired state',
                    priority='HIGH',
                    impact='HIGH'
                ))
        
        return recommendations
