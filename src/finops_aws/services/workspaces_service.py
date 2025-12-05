"""
WorkSpaces FinOps Service - Análise de Custos do Amazon WorkSpaces

FASE 2.4 - Serviços Não-Serverless de Alto Custo
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de WorkSpaces
- Análise de bundles e billing modes
- Métricas de utilização
- Recomendações de otimização de custos
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class WorkSpacesDirectory:
    """Representa um diretório WorkSpaces"""
    directory_id: str
    alias: Optional[str] = None
    directory_name: Optional[str] = None
    registration_code: Optional[str] = None
    directory_type: str = "SIMPLE_AD"
    state: str = "REGISTERED"
    workspace_creation_properties: Dict[str, Any] = field(default_factory=dict)
    workspace_access_properties: Dict[str, Any] = field(default_factory=dict)
    subnet_ids: List[str] = field(default_factory=list)
    ip_group_ids: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_registered(self) -> bool:
        return self.state == "REGISTERED"
    
    @property
    def enables_internet_access(self) -> bool:
        return self.workspace_creation_properties.get('EnableInternetAccess', False)
    
    @property
    def default_ou(self) -> Optional[str]:
        return self.workspace_creation_properties.get('DefaultOu')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'directory_id': self.directory_id,
            'alias': self.alias,
            'directory_name': self.directory_name,
            'directory_type': self.directory_type,
            'state': self.state,
            'is_registered': self.is_registered,
            'enables_internet_access': self.enables_internet_access,
            'subnet_ids': self.subnet_ids,
            'tags': self.tags
        }


@dataclass
class WorkSpace:
    """Representa um WorkSpace"""
    workspace_id: str
    directory_id: str
    user_name: str
    state: str
    bundle_id: str
    ip_address: Optional[str] = None
    computer_name: Optional[str] = None
    subnet_id: Optional[str] = None
    volume_encryption_key: Optional[str] = None
    user_volume_encryption_enabled: bool = False
    root_volume_encryption_enabled: bool = False
    workspace_properties: Dict[str, Any] = field(default_factory=dict)
    modification_states: List[Dict[str, str]] = field(default_factory=list)
    bundle_name: Optional[str] = None
    compute_type: str = "VALUE"
    running_mode: str = "AUTO_STOP"
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_running(self) -> bool:
        return self.state in ['AVAILABLE', 'IMPAIRED', 'UNHEALTHY']
    
    @property
    def is_stopped(self) -> bool:
        return self.state in ['STOPPED', 'STOPPING']
    
    @property
    def is_auto_stop(self) -> bool:
        return self.running_mode == "AUTO_STOP"
    
    @property
    def is_always_on(self) -> bool:
        return self.running_mode == "ALWAYS_ON"
    
    @property
    def running_mode_auto_stop_timeout(self) -> int:
        return self.workspace_properties.get('RunningModeAutoStopTimeoutInMinutes', 60)
    
    @property
    def root_volume_size_gb(self) -> int:
        return self.workspace_properties.get('RootVolumeSizeGib', 80)
    
    @property
    def user_volume_size_gb(self) -> int:
        return self.workspace_properties.get('UserVolumeSizeGib', 50)
    
    @property
    def compute_type_name(self) -> str:
        return self.workspace_properties.get('ComputeTypeName', self.compute_type)
    
    @property
    def total_storage_gb(self) -> int:
        return self.root_volume_size_gb + self.user_volume_size_gb
    
    @property
    def has_encryption(self) -> bool:
        return self.user_volume_encryption_enabled or self.root_volume_encryption_enabled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'workspace_id': self.workspace_id,
            'directory_id': self.directory_id,
            'user_name': self.user_name,
            'state': self.state,
            'bundle_id': self.bundle_id,
            'bundle_name': self.bundle_name,
            'ip_address': self.ip_address,
            'computer_name': self.computer_name,
            'running_mode': self.running_mode,
            'compute_type': self.compute_type_name,
            'is_running': self.is_running,
            'is_auto_stop': self.is_auto_stop,
            'is_always_on': self.is_always_on,
            'auto_stop_timeout_minutes': self.running_mode_auto_stop_timeout,
            'root_volume_size_gb': self.root_volume_size_gb,
            'user_volume_size_gb': self.user_volume_size_gb,
            'total_storage_gb': self.total_storage_gb,
            'has_encryption': self.has_encryption,
            'tags': self.tags
        }


@dataclass
class WorkSpacesBundle:
    """Representa um bundle de WorkSpaces"""
    bundle_id: str
    name: str
    owner: str
    description: Optional[str] = None
    image_id: Optional[str] = None
    root_storage: Dict[str, int] = field(default_factory=dict)
    user_storage: Dict[str, int] = field(default_factory=dict)
    compute_type: Dict[str, str] = field(default_factory=dict)
    bundle_type: str = "REGULAR"
    state: str = "AVAILABLE"
    
    @property
    def compute_type_name(self) -> str:
        return self.compute_type.get('Name', 'VALUE')
    
    @property
    def root_volume_size_gb(self) -> int:
        return self.root_storage.get('Capacity', 80)
    
    @property
    def user_volume_size_gb(self) -> int:
        return self.user_storage.get('Capacity', 50)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bundle_id': self.bundle_id,
            'name': self.name,
            'owner': self.owner,
            'description': self.description,
            'compute_type': self.compute_type_name,
            'root_volume_size_gb': self.root_volume_size_gb,
            'user_volume_size_gb': self.user_volume_size_gb,
            'bundle_type': self.bundle_type,
            'state': self.state
        }


class WorkSpacesService(BaseAWSService):
    """
    Serviço FinOps para Amazon WorkSpaces
    
    Analisa WorkSpaces, bundles e diretórios e fornece
    recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._workspaces_client = None
        self._cloudwatch_client = None
    
    @property
    def workspaces_client(self):
        if self._workspaces_client is None:
            from ..core.factories import AWSServiceType
            self._workspaces_client = self.client_factory.get_client(AWSServiceType.WORKSPACES)
        return self._workspaces_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            from ..core.factories import AWSServiceType
            self._cloudwatch_client = self.client_factory.get_client(AWSServiceType.CLOUDWATCH)
        return self._cloudwatch_client
    
    def get_service_name(self) -> str:
        return "WorkSpaces"
    
    def health_check(self) -> bool:
        try:
            self.workspaces_client.describe_workspaces(Limit=1)
            return True
        except Exception as e:
            logger.error(f"WorkSpaces health check failed: {e}")
            return False
    
    def get_workspaces(self) -> List[WorkSpace]:
        """Lista todos os WorkSpaces"""
        workspaces = []
        bundles = {b.bundle_id: b for b in self.get_bundles()}
        
        try:
            paginator = self.workspaces_client.get_paginator('describe_workspaces')
            
            for page in paginator.paginate():
                for ws_data in page.get('Workspaces', []):
                    workspace = self._parse_workspace(ws_data)
                    if workspace:
                        if workspace.bundle_id in bundles:
                            workspace.bundle_name = bundles[workspace.bundle_id].name
                        workspaces.append(workspace)
            
            logger.info(f"Found {len(workspaces)} WorkSpaces")
            
        except Exception as e:
            logger.error(f"Error listing WorkSpaces: {e}")
        
        return workspaces
    
    def _parse_workspace(self, data: Dict[str, Any]) -> Optional[WorkSpace]:
        """Parse dados do WorkSpace"""
        try:
            props = data.get('WorkspaceProperties', {})
            return WorkSpace(
                workspace_id=data.get('WorkspaceId', ''),
                directory_id=data.get('DirectoryId', ''),
                user_name=data.get('UserName', ''),
                state=data.get('State', ''),
                bundle_id=data.get('BundleId', ''),
                ip_address=data.get('IpAddress'),
                computer_name=data.get('ComputerName'),
                subnet_id=data.get('SubnetId'),
                volume_encryption_key=data.get('VolumeEncryptionKey'),
                user_volume_encryption_enabled=data.get('UserVolumeEncryptionEnabled', False),
                root_volume_encryption_enabled=data.get('RootVolumeEncryptionEnabled', False),
                workspace_properties=props,
                modification_states=data.get('ModificationStates', []),
                compute_type=props.get('ComputeTypeName', 'VALUE'),
                running_mode=props.get('RunningMode', 'AUTO_STOP')
            )
        except Exception as e:
            logger.error(f"Error parsing workspace: {e}")
            return None
    
    def get_directories(self) -> List[WorkSpacesDirectory]:
        """Lista diretórios registrados"""
        directories = []
        
        try:
            paginator = self.workspaces_client.get_paginator('describe_workspace_directories')
            
            for page in paginator.paginate():
                for dir_data in page.get('Directories', []):
                    directory = self._parse_directory(dir_data)
                    if directory:
                        directories.append(directory)
            
            logger.info(f"Found {len(directories)} WorkSpaces directories")
            
        except Exception as e:
            logger.error(f"Error listing directories: {e}")
        
        return directories
    
    def _parse_directory(self, data: Dict[str, Any]) -> Optional[WorkSpacesDirectory]:
        """Parse dados do diretório"""
        try:
            return WorkSpacesDirectory(
                directory_id=data.get('DirectoryId', ''),
                alias=data.get('Alias'),
                directory_name=data.get('DirectoryName'),
                registration_code=data.get('RegistrationCode'),
                directory_type=data.get('DirectoryType', 'SIMPLE_AD'),
                state=data.get('State', 'REGISTERED'),
                workspace_creation_properties=data.get('WorkspaceCreationProperties', {}),
                workspace_access_properties=data.get('WorkspaceAccessProperties', {}),
                subnet_ids=data.get('SubnetIds', []),
                ip_group_ids=data.get('ipGroupIds', [])
            )
        except Exception as e:
            logger.error(f"Error parsing directory: {e}")
            return None
    
    def get_bundles(self) -> List[WorkSpacesBundle]:
        """Lista bundles disponíveis"""
        bundles = []
        
        try:
            paginator = self.workspaces_client.get_paginator('describe_workspace_bundles')
            
            for page in paginator.paginate():
                for bundle_data in page.get('Bundles', []):
                    bundle = self._parse_bundle(bundle_data)
                    if bundle:
                        bundles.append(bundle)
            
        except Exception as e:
            logger.error(f"Error listing bundles: {e}")
        
        return bundles
    
    def _parse_bundle(self, data: Dict[str, Any]) -> Optional[WorkSpacesBundle]:
        """Parse dados do bundle"""
        try:
            return WorkSpacesBundle(
                bundle_id=data.get('BundleId', ''),
                name=data.get('Name', ''),
                owner=data.get('Owner', ''),
                description=data.get('Description'),
                image_id=data.get('ImageId'),
                root_storage=data.get('RootStorage', {}),
                user_storage=data.get('UserStorage', {}),
                compute_type=data.get('ComputeType', {}),
                bundle_type=data.get('BundleType', 'REGULAR'),
                state=data.get('State', 'AVAILABLE')
            )
        except Exception as e:
            logger.error(f"Error parsing bundle: {e}")
            return None
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos WorkSpaces"""
        workspaces = self.get_workspaces()
        directories = self.get_directories()
        
        running = [w for w in workspaces if w.is_running]
        stopped = [w for w in workspaces if w.is_stopped]
        auto_stop = [w for w in workspaces if w.is_auto_stop]
        always_on = [w for w in workspaces if w.is_always_on]
        
        return {
            'workspaces': [w.to_dict() for w in workspaces],
            'directories': [d.to_dict() for d in directories],
            'summary': {
                'total_workspaces': len(workspaces),
                'running': len(running),
                'stopped': len(stopped),
                'auto_stop_mode': len(auto_stop),
                'always_on_mode': len(always_on),
                'encrypted': len([w for w in workspaces if w.has_encryption]),
                'total_directories': len(directories),
                'registered_directories': len([d for d in directories if d.is_registered])
            }
        }
    
    def get_costs(self) -> List[ServiceCost]:
        """Retorna estimativas de custo para WorkSpaces"""
        costs = []
        workspaces = self.get_workspaces()
        
        for workspace in workspaces:
            monthly_cost = 0.0
            
            if workspace.is_always_on:
                monthly_cost = self._get_always_on_monthly_rate(workspace.compute_type_name)
            else:
                base_cost = self._get_auto_stop_monthly_rate(workspace.compute_type_name)
                hourly_cost = self._get_hourly_rate(workspace.compute_type_name)
                avg_hours = 160
                monthly_cost = base_cost + (hourly_cost * avg_hours)
            
            storage_cost = (workspace.root_volume_size_gb + workspace.user_volume_size_gb) * 0.10
            monthly_cost += storage_cost
            
            costs.append(ServiceCost(
                service_name='WorkSpaces',
                resource_id=workspace.workspace_id,
                cost=monthly_cost,
                period='monthly_estimate',
                currency='USD',
                metadata={
                    'user_name': workspace.user_name,
                    'running_mode': workspace.running_mode,
                    'compute_type': workspace.compute_type_name,
                    'state': workspace.state
                }
            ))
        
        return costs
    
    def _get_always_on_monthly_rate(self, compute_type: str) -> float:
        """Taxa mensal para Always-On"""
        rates = {
            'VALUE': 25.0,
            'STANDARD': 35.0,
            'PERFORMANCE': 60.0,
            'POWER': 80.0,
            'POWERPRO': 124.0,
            'GRAPHICS': 225.0,
            'GRAPHICSPRO': 382.0,
        }
        return rates.get(compute_type, 35.0)
    
    def _get_auto_stop_monthly_rate(self, compute_type: str) -> float:
        """Taxa base mensal para AutoStop"""
        rates = {
            'VALUE': 9.75,
            'STANDARD': 12.0,
            'PERFORMANCE': 17.0,
            'POWER': 22.0,
            'POWERPRO': 34.0,
            'GRAPHICS': 40.0,
            'GRAPHICSPRO': 72.0,
        }
        return rates.get(compute_type, 12.0)
    
    def _get_hourly_rate(self, compute_type: str) -> float:
        """Taxa horária para AutoStop"""
        rates = {
            'VALUE': 0.17,
            'STANDARD': 0.26,
            'PERFORMANCE': 0.47,
            'POWER': 0.63,
            'POWERPRO': 0.98,
            'GRAPHICS': 1.31,
            'GRAPHICSPRO': 2.14,
        }
        return rates.get(compute_type, 0.26)
    
    def get_metrics(self) -> List[ServiceMetrics]:
        """Retorna métricas dos WorkSpaces"""
        metrics = []
        workspaces = self.get_workspaces()
        
        for workspace in workspaces:
            try:
                available = self._get_workspace_metric(workspace.workspace_id, 'Available')
                unhealthy = self._get_workspace_metric(workspace.workspace_id, 'Unhealthy')
                
                metrics.append(ServiceMetrics(
                    service_name='WorkSpaces',
                    resource_id=workspace.workspace_id,
                    metric_name='HealthStatus',
                    value=1.0 if workspace.is_running else 0.0,
                    unit='Count',
                    period='current',
                    metadata={
                        'user_name': workspace.user_name,
                        'state': workspace.state
                    }
                ))
                
            except Exception as e:
                logger.debug(f"Error getting metrics for {workspace.workspace_id}: {e}")
        
        return metrics
    
    def _get_workspace_metric(self, workspace_id: str, metric_name: str) -> Optional[float]:
        """Obtém métrica do CloudWatch"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/WorkSpaces',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'WorkspaceId', 'Value': workspace_id}
                ],
                StartTime=datetime.now(timezone.utc) - timedelta(hours=1),
                EndTime=datetime.now(timezone.utc),
                Period=3600,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                return datapoints[-1].get('Average')
            return None
            
        except Exception as e:  # noqa: E722
            return None
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para WorkSpaces"""
        recommendations = []
        workspaces = self.get_workspaces()
        
        always_on_workspaces = [w for w in workspaces if w.is_always_on]
        for workspace in always_on_workspaces:
            auto_stop_cost = self._get_auto_stop_monthly_rate(workspace.compute_type_name) + (self._get_hourly_rate(workspace.compute_type_name) * 160)
            always_on_cost = self._get_always_on_monthly_rate(workspace.compute_type_name)
            
            if auto_stop_cost < always_on_cost:
                savings = always_on_cost - auto_stop_cost
                recommendations.append(ServiceRecommendation(
                    resource_id=workspace.workspace_id,
                    resource_type='WorkSpace',
                    recommendation_type='COST_OPTIMIZATION',
                    title='Considerar modo AutoStop',
                    description=f'WorkSpace {workspace.workspace_id} ({workspace.user_name}) usa AlwaysOn. '
                               f'AutoStop pode economizar se uso < 8h/dia.',
                    action='Alterar running mode para AutoStop',
                    estimated_savings=savings,
                    priority='MEDIUM',
                    metadata={
                        'user_name': workspace.user_name,
                        'compute_type': workspace.compute_type_name,
                        'current_mode': 'ALWAYS_ON'
                    }
                ))
        
        auto_stop_workspaces = [w for w in workspaces if w.is_auto_stop]
        for workspace in auto_stop_workspaces:
            if workspace.running_mode_auto_stop_timeout > 60:
                recommendations.append(ServiceRecommendation(
                    resource_id=workspace.workspace_id,
                    resource_type='WorkSpace',
                    recommendation_type='COST_OPTIMIZATION',
                    title='Reduzir timeout de AutoStop',
                    description=f'WorkSpace {workspace.workspace_id} tem timeout de '
                               f'{workspace.running_mode_auto_stop_timeout} min. Reduza para 60 min.',
                    action='Reduzir RunningModeAutoStopTimeoutInMinutes para 60',
                    estimated_savings=0.0,
                    priority='LOW',
                    metadata={
                        'user_name': workspace.user_name,
                        'current_timeout': workspace.running_mode_auto_stop_timeout
                    }
                ))
        
        for workspace in workspaces:
            if not workspace.has_encryption:
                recommendations.append(ServiceRecommendation(
                    resource_id=workspace.workspace_id,
                    resource_type='WorkSpace',
                    recommendation_type='SECURITY',
                    title='Habilitar criptografia de volumes',
                    description=f'WorkSpace {workspace.workspace_id} ({workspace.user_name}) não tem volumes criptografados. '
                               f'Habilite para proteção de dados.',
                    action='Recriar WorkSpace com encryption habilitado',
                    estimated_savings=0.0,
                    priority='HIGH',
                    metadata={
                        'user_name': workspace.user_name
                    }
                ))
        
        stopped_workspaces = [w for w in workspaces if w.is_stopped]
        for workspace in stopped_workspaces:
            base_cost = self._get_auto_stop_monthly_rate(workspace.compute_type_name)
            storage_cost = workspace.total_storage_gb * 0.10
            
            recommendations.append(ServiceRecommendation(
                resource_id=workspace.workspace_id,
                resource_type='WorkSpace',
                recommendation_type='COST_OPTIMIZATION',
                title='Avaliar WorkSpace parado',
                description=f'WorkSpace {workspace.workspace_id} ({workspace.user_name}) está parado. '
                           f'Considere remover se não for mais utilizado.',
                action='Verificar se usuário ainda precisa do WorkSpace',
                estimated_savings=base_cost + storage_cost,
                priority='MEDIUM',
                metadata={
                    'user_name': workspace.user_name,
                    'state': workspace.state
                }
            ))
        
        logger.info(f"Generated {len(recommendations)} WorkSpaces recommendations")
        return recommendations
