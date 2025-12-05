"""
Storage Analyzer - Análise de serviços de armazenamento AWS

Serviços cobertos:
- S3 (buckets, versioning, encryption, lifecycle)
- EFS
- FSx
- Storage Gateway
- Backup

Design Pattern: Strategy
"""
from typing import Dict, List, Any
from datetime import datetime
import logging

from .base_analyzer import (
    BaseAnalyzer,
    Recommendation,
    Priority,
    Impact
)

logger = logging.getLogger(__name__)


class StorageAnalyzer(BaseAnalyzer):
    """Analyzer para serviços de armazenamento AWS."""
    
    name = "StorageAnalyzer"
    
    def _get_client(self, region: str) -> Any:
        """Retorna clientes boto3 para armazenamento."""
        import boto3
        return {
            's3': boto3.client('s3'),
            'efs': boto3.client('efs', region_name=region),
        }
    
    def _collect_resources(self, clients: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta recursos de armazenamento."""
        resources = {}
        
        s3 = clients.get('s3')
        if s3:
            try:
                resources['buckets'] = s3.list_buckets()
                resources['s3_client'] = s3
            except Exception as e:
                logger.warning(f"Erro coletando S3: {e}")
        
        efs = clients.get('efs')
        if efs:
            try:
                resources['filesystems'] = efs.describe_file_systems()
            except Exception as e:
                logger.warning(f"Erro coletando EFS: {e}")
        
        return resources
    
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """Analisa recursos e gera recomendações."""
        recommendations = []
        metrics = {}
        
        recommendations.extend(self._analyze_s3_buckets(resources, metrics))
        recommendations.extend(self._analyze_efs(resources, metrics))
        
        return recommendations, metrics
    
    def _analyze_s3_buckets(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa buckets S3."""
        recommendations = []
        buckets_data = resources.get('buckets', {})
        s3 = resources.get('s3_client')
        
        buckets = buckets_data.get('Buckets', [])
        metrics['s3_buckets'] = len(buckets)
        
        if not s3:
            return recommendations
        
        for bucket in buckets:
            bucket_name = bucket.get('Name', '')
            
            try:
                versioning = s3.get_bucket_versioning(Bucket=bucket_name)
                if versioning.get('Status') != 'Enabled':
                    recommendations.append(self._create_recommendation(
                        rec_type='S3_VERSIONING',
                        resource_id=bucket_name,
                        description=f'Habilitar versionamento no bucket {bucket_name}',
                        service='S3 Analysis',
                        priority=Priority.MEDIUM
                    ))
            except Exception:
                pass
            
            try:
                s3.get_bucket_encryption(Bucket=bucket_name)
            except Exception:
                recommendations.append(self._create_recommendation(
                    rec_type='S3_ENCRYPTION',
                    resource_id=bucket_name,
                    description=f'Habilitar criptografia no bucket {bucket_name}',
                    service='S3 Security',
                    priority=Priority.HIGH
                ))
            
            try:
                s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            except Exception:
                recommendations.append(self._create_recommendation(
                    rec_type='S3_LIFECYCLE',
                    resource_id=bucket_name,
                    description=f'Configurar lifecycle rules no bucket {bucket_name}',
                    service='S3 Optimization',
                    priority=Priority.MEDIUM
                ))
        
        return recommendations
    
    def _analyze_efs(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa sistemas de arquivos EFS."""
        recommendations = []
        filesystems_data = resources.get('filesystems', {})
        
        filesystems = filesystems_data.get('FileSystems', [])
        metrics['efs_filesystems'] = len(filesystems)
        
        for fs in filesystems:
            fs_id = fs.get('FileSystemId', '')
            size_bytes = fs.get('SizeInBytes', {}).get('Value', 0)
            size_gb = size_bytes / (1024**3)
            throughput_mode = fs.get('ThroughputMode', '')
            
            if throughput_mode == 'provisioned' and size_gb < 100:
                recommendations.append(self._create_recommendation(
                    rec_type='EFS_THROUGHPUT_MODE',
                    resource_id=fs_id,
                    description=f'EFS {fs_id} ({size_gb:.1f}GB) pode usar bursting ao invés de provisioned',
                    service='EFS Optimization',
                    priority=Priority.MEDIUM,
                    savings=50.0
                ))
        
        return recommendations
    
    def _get_services_list(self) -> List[str]:
        """Retorna serviços analisados."""
        return ['S3', 'EFS']
