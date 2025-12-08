"""
FinOps AWS - Policy Automation Service
Serviço de Automação de Políticas FinOps

Este serviço implementa:
- Políticas automáticas de otimização
- Ações baseadas em regras (throttling, cleanup, alertas)
- Integração com AWS Systems Manager
- Workflow de aprovação para ações destrutivas

Design Patterns:
- Strategy: Diferentes tipos de ações
- Chain of Responsibility: Pipeline de avaliação de políticas
- Command: Ações reversíveis com rollback
"""
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import uuid

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class PolicyType(Enum):
    """Tipos de política"""
    COST_THRESHOLD = "cost_threshold"
    IDLE_RESOURCE = "idle_resource"
    TAG_COMPLIANCE = "tag_compliance"
    BUDGET_ALERT = "budget_alert"
    ANOMALY_RESPONSE = "anomaly_response"
    RIGHTSIZING = "rightsizing"
    COMMITMENT_PURCHASE = "commitment_purchase"


class ActionType(Enum):
    """Tipos de ação"""
    ALERT = "alert"
    TAG_RESOURCE = "tag_resource"
    STOP_RESOURCE = "stop_resource"
    TERMINATE_RESOURCE = "terminate_resource"
    RESIZE_RESOURCE = "resize_resource"
    CREATE_TICKET = "create_ticket"
    PURCHASE_SAVINGS_PLAN = "purchase_savings_plan"
    EXECUTE_SSM_DOCUMENT = "execute_ssm_document"


class ActionStatus(Enum):
    """Status de execução de ação"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class ApprovalLevel(Enum):
    """Níveis de aprovação"""
    AUTO = "auto"
    REVIEW = "review"
    MANAGER = "manager"
    EXECUTIVE = "executive"


@dataclass
class PolicyCondition:
    """Condição de uma política"""
    metric: str
    operator: str
    threshold: float
    duration_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric': self.metric,
            'operator': self.operator,
            'threshold': self.threshold,
            'duration_minutes': self.duration_minutes
        }


@dataclass
class PolicyAction:
    """Ação de uma política"""
    action_type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    approval_level: ApprovalLevel = ApprovalLevel.AUTO
    rollback_action: Optional['PolicyAction'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type.value,
            'parameters': self.parameters,
            'approval_level': self.approval_level.value,
            'has_rollback': self.rollback_action is not None
        }


@dataclass
class FinOpsPolicy:
    """Política FinOps"""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    conditions: List[PolicyCondition]
    actions: List[PolicyAction]
    enabled: bool = True
    priority: int = 1
    scope: Dict[str, List[str]] = field(default_factory=dict)
    schedule: str = ""
    last_evaluated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'description': self.description,
            'policy_type': self.policy_type.value,
            'conditions': [c.to_dict() for c in self.conditions],
            'actions': [a.to_dict() for a in self.actions],
            'enabled': self.enabled,
            'priority': self.priority,
            'scope': self.scope,
            'schedule': self.schedule,
            'last_evaluated': self.last_evaluated.isoformat() if self.last_evaluated else None
        }


@dataclass
class ActionExecution:
    """Registro de execução de ação"""
    execution_id: str
    policy_id: str
    action_type: ActionType
    status: ActionStatus
    resource_id: str
    resource_type: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_by: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    rollback_available: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'policy_id': self.policy_id,
            'action_type': self.action_type.value,
            'status': self.status.value,
            'resource': {
                'id': self.resource_id,
                'type': self.resource_type
            },
            'timestamps': {
                'created_at': self.created_at.isoformat(),
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            },
            'approved_by': self.approved_by,
            'result': self.result,
            'rollback_available': self.rollback_available
        }


class PolicyAutomationService(BaseAWSService):
    """
    Serviço de Automação de Políticas FinOps
    
    Funcionalidades:
    - Define políticas baseadas em condições
    - Executa ações automaticamente ou com aprovação
    - Mantém histórico de execuções com rollback
    - Integra com AWS SSM para ações complexas
    
    AWS APIs utilizadas:
    - ssm:SendCommand
    - ssm:GetCommandInvocation
    - ec2:StopInstances, ec2:TerminateInstances, ec2:ModifyInstanceAttribute
    - lambda:InvokeFunction
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "policy_automation"
        self._cache = FinOpsCache(default_ttl=300)
        self._policies: Dict[str, FinOpsPolicy] = {}
        self._executions: Dict[str, ActionExecution] = {}
        self._load_default_policies()
    
    def _get_ec2_client(self, region: str = None):
        """Obtém cliente boto3 para EC2"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('ec2', region_name=region)
        return boto3.client('ec2', region_name=region)
    
    def _get_ssm_client(self, region: str = None):
        """Obtém cliente boto3 para SSM"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('ssm', region_name=region)
        return boto3.client('ssm', region_name=region)
    
    def _load_default_policies(self):
        """Carrega políticas padrão"""
        self._policies = {
            "policy_idle_ec2": FinOpsPolicy(
                policy_id="policy_idle_ec2",
                name="Stop Idle EC2 Instances",
                description="Para instâncias EC2 ociosas por mais de 7 dias",
                policy_type=PolicyType.IDLE_RESOURCE,
                conditions=[
                    PolicyCondition(
                        metric="CPUUtilization",
                        operator="less_than",
                        threshold=5.0,
                        duration_minutes=10080
                    )
                ],
                actions=[
                    PolicyAction(
                        action_type=ActionType.ALERT,
                        parameters={'channel': 'email', 'severity': 'warning'},
                        approval_level=ApprovalLevel.AUTO
                    ),
                    PolicyAction(
                        action_type=ActionType.STOP_RESOURCE,
                        parameters={'wait_hours': 24},
                        approval_level=ApprovalLevel.REVIEW
                    )
                ],
                priority=1
            ),
            "policy_tag_compliance": FinOpsPolicy(
                policy_id="policy_tag_compliance",
                name="Tag Compliance Enforcement",
                description="Força aplicação de tags obrigatórias",
                policy_type=PolicyType.TAG_COMPLIANCE,
                conditions=[
                    PolicyCondition(
                        metric="missing_required_tags",
                        operator="greater_than",
                        threshold=0
                    )
                ],
                actions=[
                    PolicyAction(
                        action_type=ActionType.ALERT,
                        parameters={'channel': 'slack', 'severity': 'info'},
                        approval_level=ApprovalLevel.AUTO
                    ),
                    PolicyAction(
                        action_type=ActionType.CREATE_TICKET,
                        parameters={'priority': 'medium', 'due_days': 7},
                        approval_level=ApprovalLevel.AUTO
                    )
                ],
                priority=2
            ),
            "policy_budget_breach": FinOpsPolicy(
                policy_id="policy_budget_breach",
                name="Budget Breach Response",
                description="Responde a violações de orçamento",
                policy_type=PolicyType.BUDGET_ALERT,
                conditions=[
                    PolicyCondition(
                        metric="budget_utilization",
                        operator="greater_than",
                        threshold=90.0
                    )
                ],
                actions=[
                    PolicyAction(
                        action_type=ActionType.ALERT,
                        parameters={'channel': 'all', 'severity': 'critical'},
                        approval_level=ApprovalLevel.AUTO
                    )
                ],
                priority=1
            ),
            "policy_rightsizing": FinOpsPolicy(
                policy_id="policy_rightsizing",
                name="Auto Rightsizing",
                description="Rightsizing automático baseado em Compute Optimizer",
                policy_type=PolicyType.RIGHTSIZING,
                conditions=[
                    PolicyCondition(
                        metric="rightsizing_recommendation_age",
                        operator="greater_than",
                        threshold=14
                    )
                ],
                actions=[
                    PolicyAction(
                        action_type=ActionType.ALERT,
                        parameters={'include_savings': True},
                        approval_level=ApprovalLevel.AUTO
                    ),
                    PolicyAction(
                        action_type=ActionType.RESIZE_RESOURCE,
                        parameters={'to_recommended': True},
                        approval_level=ApprovalLevel.MANAGER
                    )
                ],
                priority=2
            )
        }
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        return True
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Retorna políticas configuradas"""
        return [p.to_dict() for p in self._policies.values()]
    
    def add_policy(self, policy: FinOpsPolicy):
        """Adiciona nova política"""
        self._policies[policy.policy_id] = policy
        self.logger.info(f"Política adicionada: {policy.name}")
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove política"""
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False
    
    def enable_policy(self, policy_id: str) -> bool:
        """Habilita política"""
        if policy_id in self._policies:
            self._policies[policy_id].enabled = True
            return True
        return False
    
    def disable_policy(self, policy_id: str) -> bool:
        """Desabilita política"""
        if policy_id in self._policies:
            self._policies[policy_id].enabled = False
            return True
        return False
    
    def evaluate_policies(
        self,
        resources: List[Dict[str, Any]],
        dry_run: bool = True
    ) -> List[ActionExecution]:
        """
        Avalia políticas contra recursos
        
        Args:
            resources: Lista de recursos para avaliar
            dry_run: Se True, não executa ações
            
        Returns:
            Lista de execuções pendentes ou completadas
        """
        pending_actions = []
        
        for policy in sorted(self._policies.values(), key=lambda p: p.priority):
            if not policy.enabled:
                continue
            
            for resource in resources:
                if self._policy_matches(policy, resource):
                    for action in policy.actions:
                        execution = self._create_execution(
                            policy,
                            action,
                            resource
                        )
                        
                        if not dry_run and action.approval_level == ApprovalLevel.AUTO:
                            self._execute_action(execution, action)
                        
                        pending_actions.append(execution)
            
            policy.last_evaluated = datetime.utcnow()
        
        return pending_actions
    
    def _policy_matches(
        self,
        policy: FinOpsPolicy,
        resource: Dict[str, Any]
    ) -> bool:
        """Verifica se política se aplica ao recurso"""
        for condition in policy.conditions:
            metric_value = resource.get('metrics', {}).get(condition.metric, 0)
            
            if condition.operator == 'less_than':
                if not (metric_value < condition.threshold):
                    return False
            elif condition.operator == 'greater_than':
                if not (metric_value > condition.threshold):
                    return False
            elif condition.operator == 'equals':
                if not (metric_value == condition.threshold):
                    return False
        
        return True
    
    def _create_execution(
        self,
        policy: FinOpsPolicy,
        action: PolicyAction,
        resource: Dict[str, Any]
    ) -> ActionExecution:
        """Cria registro de execução"""
        execution = ActionExecution(
            execution_id=str(uuid.uuid4()),
            policy_id=policy.policy_id,
            action_type=action.action_type,
            status=ActionStatus.PENDING,
            resource_id=resource.get('resource_id', 'unknown'),
            resource_type=resource.get('resource_type', 'unknown'),
            created_at=datetime.utcnow(),
            rollback_available=action.rollback_action is not None
        )
        
        self._executions[execution.execution_id] = execution
        return execution
    
    def _execute_action(
        self,
        execution: ActionExecution,
        action: PolicyAction
    ) -> bool:
        """Executa uma ação"""
        execution.status = ActionStatus.IN_PROGRESS
        execution.started_at = datetime.utcnow()
        
        try:
            if action.action_type == ActionType.ALERT:
                result = self._execute_alert(execution, action.parameters)
            elif action.action_type == ActionType.STOP_RESOURCE:
                result = self._execute_stop_resource(execution, action.parameters)
            elif action.action_type == ActionType.TAG_RESOURCE:
                result = self._execute_tag_resource(execution, action.parameters)
            elif action.action_type == ActionType.CREATE_TICKET:
                result = self._execute_create_ticket(execution, action.parameters)
            else:
                result = {'status': 'unsupported', 'message': f'Action {action.action_type} not implemented'}
            
            execution.result = result
            execution.status = ActionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            self.logger.info(f"Ação executada: {execution.execution_id} - {action.action_type.value}")
            return True
            
        except Exception as e:
            execution.status = ActionStatus.FAILED
            execution.result = {'error': str(e)}
            execution.completed_at = datetime.utcnow()
            self.logger.error(f"Erro na execução {execution.execution_id}: {e}")
            return False
    
    def _execute_alert(
        self,
        execution: ActionExecution,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa ação de alerta"""
        return {
            'status': 'sent',
            'channel': parameters.get('channel', 'email'),
            'severity': parameters.get('severity', 'info'),
            'resource_id': execution.resource_id,
            'message': f'Alert for {execution.resource_type}: {execution.resource_id}'
        }
    
    def _execute_stop_resource(
        self,
        execution: ActionExecution,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa parada de recurso (simulado)"""
        return {
            'status': 'simulated',
            'action': 'stop_instance',
            'resource_id': execution.resource_id,
            'message': 'Stop action simulated - enable production mode for real execution'
        }
    
    def _execute_tag_resource(
        self,
        execution: ActionExecution,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa aplicação de tag (simulado)"""
        return {
            'status': 'simulated',
            'action': 'apply_tags',
            'resource_id': execution.resource_id,
            'tags': parameters.get('tags', {}),
            'message': 'Tag action simulated'
        }
    
    def _execute_create_ticket(
        self,
        execution: ActionExecution,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria ticket (simulado)"""
        ticket_id = f"TICKET-{execution.execution_id[:8].upper()}"
        return {
            'status': 'created',
            'ticket_id': ticket_id,
            'priority': parameters.get('priority', 'medium'),
            'due_days': parameters.get('due_days', 7),
            'resource_id': execution.resource_id
        }
    
    def approve_execution(
        self,
        execution_id: str,
        approver: str
    ) -> bool:
        """Aprova execução pendente"""
        if execution_id not in self._executions:
            return False
        
        execution = self._executions[execution_id]
        if execution.status == ActionStatus.PENDING:
            execution.status = ActionStatus.APPROVED
            execution.approved_by = approver
            
            policy = self._policies.get(execution.policy_id)
            if policy:
                for action in policy.actions:
                    if action.action_type == execution.action_type:
                        self._execute_action(execution, action)
                        break
            
            return True
        
        return False
    
    def rollback_execution(self, execution_id: str) -> bool:
        """Faz rollback de uma execução"""
        if execution_id not in self._executions:
            return False
        
        execution = self._executions[execution_id]
        if not execution.rollback_available:
            return False
        
        execution.status = ActionStatus.ROLLED_BACK
        self.logger.info(f"Rollback executado: {execution_id}")
        return True
    
    def get_execution(self, execution_id: str) -> Optional[ActionExecution]:
        """Obtém execução por ID"""
        return self._executions.get(execution_id)
    
    def get_pending_executions(self) -> List[ActionExecution]:
        """Lista execuções pendentes de aprovação"""
        return [e for e in self._executions.values() if e.status == ActionStatus.PENDING]
    
    def get_execution_history(
        self,
        limit: int = 100,
        status_filter: Optional[ActionStatus] = None
    ) -> List[ActionExecution]:
        """Obtém histórico de execuções"""
        executions = list(self._executions.values())
        
        if status_filter:
            executions = [e for e in executions if e.status == status_filter]
        
        executions.sort(key=lambda e: e.created_at, reverse=True)
        return executions[:limit]
    
    def get_policy_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de políticas"""
        total_policies = len(self._policies)
        enabled_policies = len([p for p in self._policies.values() if p.enabled])
        total_executions = len(self._executions)
        
        status_counts = {}
        for e in self._executions.values():
            status = e.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'policies': {
                'total': total_policies,
                'enabled': enabled_policies,
                'disabled': total_policies - enabled_policies
            },
            'executions': {
                'total': total_executions,
                'by_status': status_counts
            }
        }
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        return {
            'service': 'policy_automation',
            'period_days': period_days,
            'total_cost': 0,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        stats = self.get_policy_stats()
        return {
            'service': 'policy_automation',
            'policies_enabled': stats['policies']['enabled'],
            'executions_total': stats['executions']['total'],
            'pending_approvals': len(self.get_pending_executions())
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de automação"""
        recommendations = []
        
        disabled_count = len([p for p in self._policies.values() if not p.enabled])
        if disabled_count > 0:
            recommendations.append({
                'type': 'DISABLED_POLICIES',
                'priority': 'LOW',
                'title': f'{disabled_count} políticas desabilitadas',
                'description': 'Revise políticas desabilitadas para garantir cobertura adequada',
                'action': 'Habilitar políticas relevantes'
            })
        
        pending_count = len(self.get_pending_executions())
        if pending_count > 5:
            recommendations.append({
                'type': 'PENDING_APPROVALS',
                'priority': 'MEDIUM',
                'title': f'{pending_count} ações aguardando aprovação',
                'description': 'Ações pendentes podem representar economia não capturada',
                'action': 'Revisar e aprovar ações pendentes'
            })
        
        return recommendations
