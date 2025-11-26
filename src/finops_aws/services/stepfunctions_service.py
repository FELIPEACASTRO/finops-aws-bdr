"""
AWS Step Functions FinOps Service

Análise de custos e otimização para AWS Step Functions:
- State machines (Standard e Express)
- Execuções e métricas
- Atividades
- Recomendações de otimização (Express vs Standard)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService, ServiceRecommendation


@dataclass
class StateMachine:
    """Representa uma State Machine do Step Functions"""
    state_machine_arn: str
    name: str
    type: str = 'STANDARD'
    status: str = 'ACTIVE'
    definition: str = ''
    role_arn: str = ''
    creation_date: Optional[datetime] = None
    logging_configuration: Dict[str, Any] = field(default_factory=dict)
    tracing_configuration: Dict[str, Any] = field(default_factory=dict)
    label: str = ''
    revision_id: str = ''
    
    @property
    def is_standard(self) -> bool:
        return self.type == 'STANDARD'
    
    @property
    def is_express(self) -> bool:
        return self.type == 'EXPRESS'
    
    @property
    def is_active(self) -> bool:
        return self.status == 'ACTIVE'
    
    @property
    def has_logging(self) -> bool:
        level = self.logging_configuration.get('level', 'OFF')
        return level != 'OFF'
    
    @property
    def has_tracing(self) -> bool:
        return self.tracing_configuration.get('enabled', False)
    
    @property
    def log_level(self) -> str:
        return self.logging_configuration.get('level', 'OFF')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state_machine_arn': self.state_machine_arn,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'is_standard': self.is_standard,
            'is_express': self.is_express,
            'is_active': self.is_active,
            'has_logging': self.has_logging,
            'has_tracing': self.has_tracing,
            'log_level': self.log_level,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'label': self.label
        }


@dataclass
class StateMachineExecution:
    """Representa uma execução de State Machine"""
    execution_arn: str
    state_machine_arn: str
    name: str
    status: str = 'RUNNING'
    start_date: Optional[datetime] = None
    stop_date: Optional[datetime] = None
    
    @property
    def is_running(self) -> bool:
        return self.status == 'RUNNING'
    
    @property
    def is_succeeded(self) -> bool:
        return self.status == 'SUCCEEDED'
    
    @property
    def is_failed(self) -> bool:
        return self.status == 'FAILED'
    
    @property
    def is_timed_out(self) -> bool:
        return self.status == 'TIMED_OUT'
    
    @property
    def is_aborted(self) -> bool:
        return self.status == 'ABORTED'
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_date and self.stop_date:
            return (self.stop_date - self.start_date).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_arn': self.execution_arn,
            'state_machine_arn': self.state_machine_arn,
            'name': self.name,
            'status': self.status,
            'is_running': self.is_running,
            'is_succeeded': self.is_succeeded,
            'is_failed': self.is_failed,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'stop_date': self.stop_date.isoformat() if self.stop_date else None,
            'duration_seconds': self.duration_seconds
        }


@dataclass
class Activity:
    """Representa uma Activity do Step Functions"""
    activity_arn: str
    name: str
    creation_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'activity_arn': self.activity_arn,
            'name': self.name,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None
        }


class StepFunctionsService(BaseAWSService):
    """Serviço FinOps para análise de AWS Step Functions"""
    
    def __init__(self, client_factory):
        self.client_factory = client_factory
        self._sfn_client = None
    
    @property
    def sfn_client(self):
        if self._sfn_client is None:
            self._sfn_client = self.client_factory.get_client('stepfunctions')
        return self._sfn_client
    
    @property
    def service_name(self) -> str:
        return "AWS Step Functions"
    
    def health_check(self) -> bool:
        try:
            self.sfn_client.list_state_machines(maxResults=1)
            return True
        except Exception:
            return False
    
    def get_state_machines(self) -> List[StateMachine]:
        machines = []
        try:
            paginator = self.sfn_client.get_paginator('list_state_machines')
            for page in paginator.paginate():
                for sm in page.get('stateMachines', []):
                    try:
                        details = self.sfn_client.describe_state_machine(
                            stateMachineArn=sm.get('stateMachineArn', '')
                        )
                        machines.append(StateMachine(
                            state_machine_arn=details.get('stateMachineArn', ''),
                            name=details.get('name', ''),
                            type=details.get('type', 'STANDARD'),
                            status=details.get('status', 'ACTIVE'),
                            definition=details.get('definition', ''),
                            role_arn=details.get('roleArn', ''),
                            creation_date=details.get('creationDate'),
                            logging_configuration=details.get('loggingConfiguration', {}),
                            tracing_configuration=details.get('tracingConfiguration', {}),
                            label=details.get('label', ''),
                            revision_id=details.get('revisionId', '')
                        ))
                    except Exception:
                        machines.append(StateMachine(
                            state_machine_arn=sm.get('stateMachineArn', ''),
                            name=sm.get('name', ''),
                            type=sm.get('type', 'STANDARD'),
                            creation_date=sm.get('creationDate')
                        ))
        except Exception:
            pass
        return machines
    
    def get_executions(self, state_machine_arn: str, max_results: int = 100) -> List[StateMachineExecution]:
        executions = []
        try:
            paginator = self.sfn_client.get_paginator('list_executions')
            count = 0
            for page in paginator.paginate(stateMachineArn=state_machine_arn):
                for exec_item in page.get('executions', []):
                    if count >= max_results:
                        break
                    executions.append(StateMachineExecution(
                        execution_arn=exec_item.get('executionArn', ''),
                        state_machine_arn=exec_item.get('stateMachineArn', ''),
                        name=exec_item.get('name', ''),
                        status=exec_item.get('status', 'RUNNING'),
                        start_date=exec_item.get('startDate'),
                        stop_date=exec_item.get('stopDate')
                    ))
                    count += 1
                if count >= max_results:
                    break
        except Exception:
            pass
        return executions
    
    def get_activities(self) -> List[Activity]:
        activities = []
        try:
            paginator = self.sfn_client.get_paginator('list_activities')
            for page in paginator.paginate():
                for activity in page.get('activities', []):
                    activities.append(Activity(
                        activity_arn=activity.get('activityArn', ''),
                        name=activity.get('name', ''),
                        creation_date=activity.get('creationDate')
                    ))
        except Exception:
            pass
        return activities
    
    def get_resources(self) -> Dict[str, Any]:
        state_machines = self.get_state_machines()
        activities = self.get_activities()
        
        return {
            'state_machines': [sm.to_dict() for sm in state_machines],
            'activities': [a.to_dict() for a in activities],
            'summary': {
                'total_state_machines': len(state_machines),
                'standard_machines': sum(1 for sm in state_machines if sm.is_standard),
                'express_machines': sum(1 for sm in state_machines if sm.is_express),
                'active_machines': sum(1 for sm in state_machines if sm.is_active),
                'machines_with_logging': sum(1 for sm in state_machines if sm.has_logging),
                'machines_with_tracing': sum(1 for sm in state_machines if sm.has_tracing),
                'total_activities': len(activities)
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        resources = self.get_resources()
        total = max(resources['summary']['total_state_machines'], 1)
        
        return {
            'state_machine_count': resources['summary']['total_state_machines'],
            'standard_ratio': resources['summary']['standard_machines'] / total,
            'express_ratio': resources['summary']['express_machines'] / total,
            'logging_enabled_ratio': resources['summary']['machines_with_logging'] / total,
            'tracing_enabled_ratio': resources['summary']['machines_with_tracing'] / total,
            'activity_count': resources['summary']['total_activities']
        }
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        recommendations = []
        state_machines = self.get_state_machines()
        
        for sm in state_machines:
            if sm.is_standard and not sm.has_logging:
                recommendations.append(ServiceRecommendation(
                    resource_id=sm.name,
                    resource_type='StateMachine',
                    title='Habilitar logging para auditoria',
                    recommendation=f'State machine {sm.name} não tem logging habilitado. '
                                 f'Habilite para auditoria e debugging.',
                    action='Configurar loggingConfiguration com level ALL ou ERROR',
                    estimated_savings=None,
                    priority='low',
                    category='operational_excellence'
                ))
            
            if sm.is_standard:
                recommendations.append(ServiceRecommendation(
                    resource_id=sm.name,
                    resource_type='StateMachine',
                    title='Avaliar migração para Express Workflow',
                    recommendation=f'State machine {sm.name} é do tipo STANDARD. '
                                 f'Se as execuções duram menos de 5 minutos e não precisam de '
                                 f'exatamente-uma-vez, considere Express para economia de até 80%.',
                    action='Avaliar migração para Express Workflow',
                    estimated_savings=None,
                    priority='medium',
                    category='cost_optimization'
                ))
        
        return recommendations
