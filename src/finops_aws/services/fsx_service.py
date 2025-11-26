"""
FSx FinOps Service - Análise de Custos do Amazon FSx

FASE 2.5 - Serviços de Alto Custo de Armazenamento
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de file systems FSx (Lustre, Windows, NetApp ONTAP, OpenZFS)
- Análise de storage e throughput
- Métricas de utilização
- Recomendações de otimização de custos
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class FSxFileSystem:
    """Representa um file system FSx"""
    file_system_id: str
    file_system_type: str
    arn: str
    lifecycle: str
    storage_capacity: int
    storage_type: Optional[str] = None
    subnet_ids: List[str] = field(default_factory=list)
    vpc_id: Optional[str] = None
    dns_name: Optional[str] = None
    kms_key_id: Optional[str] = None
    owner_id: Optional[str] = None
    creation_time: Optional[datetime] = None
    throughput_capacity: Optional[int] = None
    deployment_type: Optional[str] = None
    automatic_backup_retention_days: int = 0
    copy_tags_to_backups: bool = False
    data_compression_type: Optional[str] = None
    weekly_maintenance_start_time: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_lustre(self) -> bool:
        return self.file_system_type == 'LUSTRE'
    
    @property
    def is_windows(self) -> bool:
        return self.file_system_type == 'WINDOWS'
    
    @property
    def is_ontap(self) -> bool:
        return self.file_system_type == 'ONTAP'
    
    @property
    def is_openzfs(self) -> bool:
        return self.file_system_type == 'OPENZFS'
    
    @property
    def is_encrypted(self) -> bool:
        return self.kms_key_id is not None
    
    @property
    def has_backups(self) -> bool:
        return self.automatic_backup_retention_days > 0
    
    @property
    def has_compression(self) -> bool:
        return self.data_compression_type is not None and self.data_compression_type != 'NONE'
    
    @property
    def storage_capacity_gb(self) -> int:
        return self.storage_capacity
    
    @property
    def storage_capacity_tb(self) -> float:
        return self.storage_capacity / 1024
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_system_id': self.file_system_id,
            'file_system_type': self.file_system_type,
            'arn': self.arn,
            'lifecycle': self.lifecycle,
            'storage_capacity': self.storage_capacity,
            'storage_type': self.storage_type,
            'subnet_ids': self.subnet_ids,
            'vpc_id': self.vpc_id,
            'dns_name': self.dns_name,
            'kms_key_id': self.kms_key_id,
            'throughput_capacity': self.throughput_capacity,
            'deployment_type': self.deployment_type,
            'automatic_backup_retention_days': self.automatic_backup_retention_days,
            'data_compression_type': self.data_compression_type,
            'is_encrypted': self.is_encrypted,
            'has_backups': self.has_backups,
            'has_compression': self.has_compression,
            'tags': self.tags,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class FSxVolume:
    """Representa um volume FSx (para ONTAP e OpenZFS)"""
    volume_id: str
    volume_type: str
    name: str
    lifecycle: str
    file_system_id: str
    storage_virtual_machine_id: Optional[str] = None
    creation_time: Optional[datetime] = None
    size_in_megabytes: int = 0
    storage_efficiency_enabled: bool = False
    tiering_policy: Optional[str] = None
    copy_tags_to_snapshots: bool = False
    snapshot_policy: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def size_in_gb(self) -> float:
        return self.size_in_megabytes / 1024
    
    @property
    def size_in_tb(self) -> float:
        return self.size_in_megabytes / (1024 * 1024)
    
    @property
    def has_tiering(self) -> bool:
        return self.tiering_policy is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'volume_id': self.volume_id,
            'volume_type': self.volume_type,
            'name': self.name,
            'lifecycle': self.lifecycle,
            'file_system_id': self.file_system_id,
            'storage_virtual_machine_id': self.storage_virtual_machine_id,
            'size_in_megabytes': self.size_in_megabytes,
            'size_in_gb': self.size_in_gb,
            'storage_efficiency_enabled': self.storage_efficiency_enabled,
            'tiering_policy': self.tiering_policy,
            'has_tiering': self.has_tiering,
            'tags': self.tags,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class FSxBackup:
    """Representa um backup FSx"""
    backup_id: str
    lifecycle: str
    file_system_id: str
    file_system_type: str
    type: str
    creation_time: Optional[datetime] = None
    progress_percent: int = 0
    kms_key_id: Optional[str] = None
    resource_arn: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_automatic(self) -> bool:
        return self.type == 'AUTOMATIC'
    
    @property
    def is_user_initiated(self) -> bool:
        return self.type == 'USER_INITIATED'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backup_id': self.backup_id,
            'lifecycle': self.lifecycle,
            'file_system_id': self.file_system_id,
            'file_system_type': self.file_system_type,
            'type': self.type,
            'progress_percent': self.progress_percent,
            'is_automatic': self.is_automatic,
            'is_user_initiated': self.is_user_initiated,
            'tags': self.tags,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


class FSxService(BaseAWSService):
    """
    Serviço FinOps para Amazon FSx
    
    Analisa file systems FSx (Lustre, Windows, NetApp ONTAP, OpenZFS)
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(self, client_factory):
        super().__init__()
        self.client_factory = client_factory
        self._fsx_client = None
        self._cloudwatch_client = None
    
    @property
    def fsx_client(self):
        if self._fsx_client is None:
            self._fsx_client = self.client_factory.get_client('fsx')
        return self._fsx_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            self._cloudwatch_client = self.client_factory.get_client('cloudwatch')
        return self._cloudwatch_client
    
    @property
    def service_name(self) -> str:
        return "Amazon FSx"
    
    def health_check(self) -> bool:
        """Verifica se o serviço FSx está acessível"""
        try:
            self.fsx_client.describe_file_systems(MaxResults=1)
            return True
        except Exception as e:
            logger.error(f"FSx health check failed: {e}")
            return False
    
    def get_file_systems(self) -> List[FSxFileSystem]:
        """Lista todos os file systems FSx"""
        file_systems = []
        try:
            paginator = self.fsx_client.get_paginator('describe_file_systems')
            for page in paginator.paginate():
                for fs in page.get('FileSystems', []):
                    file_system = FSxFileSystem(
                        file_system_id=fs['FileSystemId'],
                        file_system_type=fs['FileSystemType'],
                        arn=fs.get('ResourceARN', ''),
                        lifecycle=fs['Lifecycle'],
                        storage_capacity=fs['StorageCapacity'],
                        storage_type=fs.get('StorageType'),
                        subnet_ids=fs.get('SubnetIds', []),
                        vpc_id=fs.get('VpcId'),
                        dns_name=fs.get('DNSName'),
                        kms_key_id=fs.get('KmsKeyId'),
                        owner_id=fs.get('OwnerId'),
                        creation_time=fs.get('CreationTime'),
                        tags={t['Key']: t['Value'] for t in fs.get('Tags', [])}
                    )
                    
                    if fs['FileSystemType'] == 'LUSTRE':
                        lustre_config = fs.get('LustreConfiguration', {})
                        file_system.deployment_type = lustre_config.get('DeploymentType')
                        file_system.data_compression_type = lustre_config.get('DataCompressionType')
                        file_system.automatic_backup_retention_days = lustre_config.get('AutomaticBackupRetentionDays', 0)
                        file_system.weekly_maintenance_start_time = lustre_config.get('WeeklyMaintenanceStartTime')
                    
                    elif fs['FileSystemType'] == 'WINDOWS':
                        windows_config = fs.get('WindowsConfiguration', {})
                        file_system.throughput_capacity = windows_config.get('ThroughputCapacity')
                        file_system.deployment_type = windows_config.get('DeploymentType')
                        file_system.automatic_backup_retention_days = windows_config.get('AutomaticBackupRetentionDays', 0)
                        file_system.copy_tags_to_backups = windows_config.get('CopyTagsToBackups', False)
                        file_system.weekly_maintenance_start_time = windows_config.get('WeeklyMaintenanceStartTime')
                    
                    elif fs['FileSystemType'] == 'ONTAP':
                        ontap_config = fs.get('OntapConfiguration', {})
                        file_system.throughput_capacity = ontap_config.get('ThroughputCapacity')
                        file_system.deployment_type = ontap_config.get('DeploymentType')
                        file_system.automatic_backup_retention_days = ontap_config.get('AutomaticBackupRetentionDays', 0)
                        file_system.weekly_maintenance_start_time = ontap_config.get('WeeklyMaintenanceStartTime')
                    
                    elif fs['FileSystemType'] == 'OPENZFS':
                        openzfs_config = fs.get('OpenZFSConfiguration', {})
                        file_system.throughput_capacity = openzfs_config.get('ThroughputCapacity')
                        file_system.deployment_type = openzfs_config.get('DeploymentType')
                        file_system.automatic_backup_retention_days = openzfs_config.get('AutomaticBackupRetentionDays', 0)
                        file_system.copy_tags_to_backups = openzfs_config.get('CopyTagsToBackups', False)
                        file_system.weekly_maintenance_start_time = openzfs_config.get('WeeklyMaintenanceStartTime')
                    
                    file_systems.append(file_system)
            
            logger.info(f"Found {len(file_systems)} FSx file systems")
        except Exception as e:
            logger.error(f"Error listing FSx file systems: {e}")
        
        return file_systems
    
    def get_volumes(self) -> List[FSxVolume]:
        """Lista todos os volumes FSx (ONTAP e OpenZFS)"""
        volumes = []
        try:
            paginator = self.fsx_client.get_paginator('describe_volumes')
            for page in paginator.paginate():
                for vol in page.get('Volumes', []):
                    volume = FSxVolume(
                        volume_id=vol['VolumeId'],
                        volume_type=vol['VolumeType'],
                        name=vol.get('Name', ''),
                        lifecycle=vol['Lifecycle'],
                        file_system_id=vol.get('FileSystemId', ''),
                        creation_time=vol.get('CreationTime'),
                        tags={t['Key']: t['Value'] for t in vol.get('Tags', [])}
                    )
                    
                    if vol['VolumeType'] == 'ONTAP':
                        ontap_config = vol.get('OntapConfiguration', {})
                        volume.storage_virtual_machine_id = ontap_config.get('StorageVirtualMachineId')
                        volume.size_in_megabytes = ontap_config.get('SizeInMegabytes', 0)
                        volume.storage_efficiency_enabled = ontap_config.get('StorageEfficiencyEnabled', False)
                        tiering = ontap_config.get('TieringPolicy', {})
                        volume.tiering_policy = tiering.get('Name')
                        volume.copy_tags_to_snapshots = ontap_config.get('CopyTagsToSnapshots', False)
                        volume.snapshot_policy = ontap_config.get('SnapshotPolicy')
                    
                    elif vol['VolumeType'] == 'OPENZFS':
                        openzfs_config = vol.get('OpenZFSConfiguration', {})
                        volume.copy_tags_to_snapshots = openzfs_config.get('CopyTagsToSnapshots', False)
                        volume.storage_efficiency_enabled = openzfs_config.get('DataCompressionType', 'NONE') != 'NONE'
                    
                    volumes.append(volume)
            
            logger.info(f"Found {len(volumes)} FSx volumes")
        except Exception as e:
            logger.error(f"Error listing FSx volumes: {e}")
        
        return volumes
    
    def get_backups(self) -> List[FSxBackup]:
        """Lista todos os backups FSx"""
        backups = []
        try:
            paginator = self.fsx_client.get_paginator('describe_backups')
            for page in paginator.paginate():
                for backup in page.get('Backups', []):
                    fs_info = backup.get('FileSystem', {})
                    backups.append(FSxBackup(
                        backup_id=backup['BackupId'],
                        lifecycle=backup['Lifecycle'],
                        file_system_id=fs_info.get('FileSystemId', ''),
                        file_system_type=fs_info.get('FileSystemType', ''),
                        type=backup.get('Type', 'AUTOMATIC'),
                        creation_time=backup.get('CreationTime'),
                        progress_percent=backup.get('ProgressPercent', 0),
                        kms_key_id=backup.get('KmsKeyId'),
                        resource_arn=backup.get('ResourceARN'),
                        tags={t['Key']: t['Value'] for t in backup.get('Tags', [])}
                    ))
            
            logger.info(f"Found {len(backups)} FSx backups")
        except Exception as e:
            logger.error(f"Error listing FSx backups: {e}")
        
        return backups
    
    def get_resources(self) -> Dict[str, Any]:
        """Retorna todos os recursos FSx"""
        file_systems = self.get_file_systems()
        volumes = self.get_volumes()
        backups = self.get_backups()
        
        by_type = {}
        for fs in file_systems:
            fs_type = fs.file_system_type
            if fs_type not in by_type:
                by_type[fs_type] = []
            by_type[fs_type].append(fs.to_dict())
        
        return {
            'file_systems': [fs.to_dict() for fs in file_systems],
            'volumes': [vol.to_dict() for vol in volumes],
            'backups': [b.to_dict() for b in backups],
            'by_type': by_type,
            'summary': {
                'total_file_systems': len(file_systems),
                'total_volumes': len(volumes),
                'total_backups': len(backups),
                'lustre_count': len([fs for fs in file_systems if fs.is_lustre]),
                'windows_count': len([fs for fs in file_systems if fs.is_windows]),
                'ontap_count': len([fs for fs in file_systems if fs.is_ontap]),
                'openzfs_count': len([fs for fs in file_systems if fs.is_openzfs]),
                'total_storage_gb': sum(fs.storage_capacity for fs in file_systems),
                'encrypted_count': len([fs for fs in file_systems if fs.is_encrypted]),
                'with_backups_count': len([fs for fs in file_systems if fs.has_backups])
            }
        }
    
    def get_metrics(self, file_system_id: Optional[str] = None, period_hours: int = 24) -> Dict[str, Any]:
        """Obtém métricas de utilização do FSx"""
        metrics = {}
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=period_hours)
        
        file_systems = self.get_file_systems()
        if file_system_id:
            file_systems = [fs for fs in file_systems if fs.file_system_id == file_system_id]
        
        for fs in file_systems:
            try:
                fs_metrics = {}
                
                metric_names = []
                if fs.is_lustre:
                    metric_names = ['DataReadBytes', 'DataWriteBytes', 'MetadataOperations']
                elif fs.is_windows:
                    metric_names = ['DataReadBytes', 'DataWriteBytes', 'FreeStorageCapacity']
                elif fs.is_ontap or fs.is_openzfs:
                    metric_names = ['DataReadBytes', 'DataWriteBytes', 'StorageUsed']
                
                for metric_name in metric_names:
                    try:
                        response = self.cloudwatch_client.get_metric_statistics(
                            Namespace='AWS/FSx',
                            MetricName=metric_name,
                            Dimensions=[
                                {'Name': 'FileSystemId', 'Value': fs.file_system_id}
                            ],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,
                            Statistics=['Average', 'Maximum', 'Sum']
                        )
                        
                        datapoints = response.get('Datapoints', [])
                        if datapoints:
                            fs_metrics[metric_name] = {
                                'average': sum(d.get('Average', 0) for d in datapoints) / len(datapoints),
                                'maximum': max(d.get('Maximum', 0) for d in datapoints),
                                'sum': sum(d.get('Sum', 0) for d in datapoints)
                            }
                    except Exception as e:
                        logger.debug(f"Could not get metric {metric_name} for {fs.file_system_id}: {e}")
                
                metrics[fs.file_system_id] = fs_metrics
                
            except Exception as e:
                logger.error(f"Error getting metrics for {fs.file_system_id}: {e}")
        
        return metrics
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização de custos para FSx"""
        recommendations = []
        file_systems = self.get_file_systems()
        
        for fs in file_systems:
            if not fs.is_encrypted:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=fs.file_system_id,
                    recommendation_type='security',
                    title='FSx File System sem Criptografia',
                    description=f"File system '{fs.file_system_id}' ({fs.file_system_type}) não está criptografado",
                    action='Considere habilitar criptografia com KMS para dados sensíveis',
                    estimated_savings=0.0,
                    priority='high',
                    metadata={'file_system_type': fs.file_system_type}
                ))
            
            if not fs.has_backups:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=fs.file_system_id,
                    recommendation_type='reliability',
                    title='FSx File System sem Backup Automático',
                    description=f"File system '{fs.file_system_id}' não tem backup automático configurado",
                    action='Configure backup automático para proteção de dados',
                    estimated_savings=0.0,
                    priority='medium',
                    metadata={'file_system_type': fs.file_system_type}
                ))
            
            if fs.is_lustre and not fs.has_compression:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=fs.file_system_id,
                    recommendation_type='cost_optimization',
                    title='FSx Lustre sem Compressão de Dados',
                    description=f"File system Lustre '{fs.file_system_id}' não tem compressão habilitada",
                    action='Habilite compressão LZ4 para reduzir custos de armazenamento',
                    estimated_savings=fs.storage_capacity * 0.02,
                    priority='medium',
                    metadata={'storage_capacity_gb': fs.storage_capacity}
                ))
            
            if fs.storage_capacity > 10000:
                if fs.is_lustre and fs.deployment_type == 'PERSISTENT_1':
                    recommendations.append(ServiceRecommendation(
                        service_name=self.service_name,
                        resource_id=fs.file_system_id,
                        recommendation_type='cost_optimization',
                        title='FSx Lustre Grande - Considere PERSISTENT_2',
                        description=f"File system Lustre grande ({fs.storage_capacity_tb:.1f} TB) usando PERSISTENT_1",
                        action='Migre para PERSISTENT_2 para melhor custo-benefício em workloads de longa duração',
                        estimated_savings=fs.storage_capacity * 0.01,
                        priority='low',
                        metadata={'storage_tb': fs.storage_capacity_tb}
                    ))
            
            if fs.is_windows and fs.throughput_capacity and fs.throughput_capacity > 256:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=fs.file_system_id,
                    recommendation_type='rightsizing',
                    title='FSx Windows com Alto Throughput',
                    description=f"File system Windows '{fs.file_system_id}' com throughput de {fs.throughput_capacity} MB/s",
                    action='Avalie se o throughput configurado está sendo utilizado. Considere reduzir se subutilizado',
                    estimated_savings=50.0,
                    priority='medium',
                    metadata={'throughput_capacity': fs.throughput_capacity}
                ))
            
            if fs.lifecycle == 'FAILED':
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=fs.file_system_id,
                    recommendation_type='operational',
                    title='FSx File System em Estado de Falha',
                    description=f"File system '{fs.file_system_id}' está em estado FAILED",
                    action='Investigue e resolva o problema ou exclua o file system para evitar custos desnecessários',
                    estimated_savings=0.0,
                    priority='critical',
                    metadata={'lifecycle': fs.lifecycle}
                ))
        
        volumes = self.get_volumes()
        for vol in volumes:
            if vol.volume_type == 'ONTAP' and not vol.storage_efficiency_enabled:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=vol.volume_id,
                    recommendation_type='cost_optimization',
                    title='Volume ONTAP sem Storage Efficiency',
                    description=f"Volume ONTAP '{vol.volume_id}' não tem storage efficiency habilitado",
                    action='Habilite deduplicação e compressão para reduzir custos',
                    estimated_savings=vol.size_in_gb * 0.03,
                    priority='medium',
                    metadata={'size_gb': vol.size_in_gb}
                ))
            
            if vol.volume_type == 'ONTAP' and not vol.has_tiering:
                recommendations.append(ServiceRecommendation(
                    service_name=self.service_name,
                    resource_id=vol.volume_id,
                    recommendation_type='cost_optimization',
                    title='Volume ONTAP sem Tiering',
                    description=f"Volume ONTAP '{vol.volume_id}' não tem tiering configurado",
                    action='Configure tiering para mover dados frios para capacity pool automaticamente',
                    estimated_savings=vol.size_in_gb * 0.02,
                    priority='low',
                    metadata={'size_gb': vol.size_in_gb}
                ))
        
        logger.info(f"Generated {len(recommendations)} FSx recommendations")
        return recommendations
