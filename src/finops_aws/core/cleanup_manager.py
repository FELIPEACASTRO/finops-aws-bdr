"""
CleanupManager - Sistema de Limpeza Automática de Arquivos Temporários

FASE 1.1 do Roadmap FinOps AWS
Objetivo: Implementar limpeza automática de arquivos internos (.bkp, .tmp, cache)

Autor: FinOps AWS Team
Data: Novembro 2025
"""
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import json
import boto3
from botocore.exceptions import ClientError

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class CleanupConfig:
    """
    Configuração para o sistema de limpeza
    
    Attributes:
        file_extensions: Extensões de arquivos a serem limpos
        max_file_age_hours: Idade máxima de arquivos em horas
        max_file_size_mb: Tamanho máximo de arquivo em MB (0 = sem limite)
        max_total_size_mb: Tamanho máximo total em MB (0 = sem limite)
        cleanup_directories: Diretórios a serem limpos
        s3_cleanup_enabled: Habilitar limpeza de arquivos no S3
        s3_max_age_days: Idade máxima de arquivos no S3 em dias
        dry_run: Se True, apenas simula a limpeza sem deletar
    """
    file_extensions: Set[str] = field(default_factory=lambda: {'.bkp', '.tmp', '.cache', '.log', '.pyc', '.pyo'})
    max_file_age_hours: int = 24
    max_file_size_mb: float = 100.0
    max_total_size_mb: float = 500.0
    cleanup_directories: List[str] = field(default_factory=lambda: ['/tmp', tempfile.gettempdir()])
    s3_cleanup_enabled: bool = True
    s3_max_age_days: int = 7
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário"""
        return {
            'file_extensions': list(self.file_extensions),
            'max_file_age_hours': self.max_file_age_hours,
            'max_file_size_mb': self.max_file_size_mb,
            'max_total_size_mb': self.max_total_size_mb,
            'cleanup_directories': self.cleanup_directories,
            's3_cleanup_enabled': self.s3_cleanup_enabled,
            's3_max_age_days': self.s3_max_age_days,
            'dry_run': self.dry_run
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CleanupConfig':
        """Cria configuração a partir de dicionário"""
        return cls(
            file_extensions=set(data.get('file_extensions', ['.bkp', '.tmp', '.cache'])),
            max_file_age_hours=data.get('max_file_age_hours', 24),
            max_file_size_mb=data.get('max_file_size_mb', 100.0),
            max_total_size_mb=data.get('max_total_size_mb', 500.0),
            cleanup_directories=data.get('cleanup_directories', ['/tmp']),
            s3_cleanup_enabled=data.get('s3_cleanup_enabled', True),
            s3_max_age_days=data.get('s3_max_age_days', 7),
            dry_run=data.get('dry_run', False)
        )

    @classmethod
    def from_env(cls) -> 'CleanupConfig':
        """Cria configuração a partir de variáveis de ambiente"""
        extensions_str = os.getenv('CLEANUP_FILE_EXTENSIONS', '.bkp,.tmp,.cache,.log,.pyc,.pyo')
        directories_str = os.getenv('CLEANUP_DIRECTORIES', '/tmp')
        
        return cls(
            file_extensions=set(extensions_str.split(',')),
            max_file_age_hours=int(os.getenv('CLEANUP_MAX_FILE_AGE_HOURS', '24')),
            max_file_size_mb=float(os.getenv('CLEANUP_MAX_FILE_SIZE_MB', '100')),
            max_total_size_mb=float(os.getenv('CLEANUP_MAX_TOTAL_SIZE_MB', '500')),
            cleanup_directories=directories_str.split(','),
            s3_cleanup_enabled=os.getenv('CLEANUP_S3_ENABLED', 'true').lower() == 'true',
            s3_max_age_days=int(os.getenv('CLEANUP_S3_MAX_AGE_DAYS', '7')),
            dry_run=os.getenv('CLEANUP_DRY_RUN', 'false').lower() == 'true'
        )


@dataclass
class CleanupResult:
    """
    Resultado da operação de limpeza
    
    Attributes:
        files_deleted: Número de arquivos deletados
        files_failed: Número de arquivos que falharam
        bytes_freed: Bytes liberados
        s3_objects_deleted: Objetos S3 deletados
        s3_bytes_freed: Bytes liberados no S3
        execution_time_seconds: Tempo de execução em segundos
        errors: Lista de erros encontrados
        deleted_files: Lista de arquivos deletados
    """
    files_deleted: int = 0
    files_failed: int = 0
    bytes_freed: int = 0
    s3_objects_deleted: int = 0
    s3_bytes_freed: int = 0
    execution_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte resultado para dicionário"""
        return {
            'files_deleted': self.files_deleted,
            'files_failed': self.files_failed,
            'bytes_freed': self.bytes_freed,
            'bytes_freed_mb': round(self.bytes_freed / (1024 * 1024), 2),
            's3_objects_deleted': self.s3_objects_deleted,
            's3_bytes_freed': self.s3_bytes_freed,
            's3_bytes_freed_mb': round(self.s3_bytes_freed / (1024 * 1024), 2),
            'total_bytes_freed': self.bytes_freed + self.s3_bytes_freed,
            'total_bytes_freed_mb': round((self.bytes_freed + self.s3_bytes_freed) / (1024 * 1024), 2),
            'execution_time_seconds': round(self.execution_time_seconds, 3),
            'errors_count': len(self.errors),
            'errors': self.errors[:10],  # Limita a 10 erros no relatório
            'success_rate': round(
                (self.files_deleted / (self.files_deleted + self.files_failed) * 100)
                if (self.files_deleted + self.files_failed) > 0 else 100.0, 2
            )
        }

    def merge(self, other: 'CleanupResult') -> 'CleanupResult':
        """Mescla dois resultados de limpeza"""
        return CleanupResult(
            files_deleted=self.files_deleted + other.files_deleted,
            files_failed=self.files_failed + other.files_failed,
            bytes_freed=self.bytes_freed + other.bytes_freed,
            s3_objects_deleted=self.s3_objects_deleted + other.s3_objects_deleted,
            s3_bytes_freed=self.s3_bytes_freed + other.s3_bytes_freed,
            execution_time_seconds=self.execution_time_seconds + other.execution_time_seconds,
            errors=self.errors + other.errors,
            deleted_files=self.deleted_files + other.deleted_files,
            skipped_files=self.skipped_files + other.skipped_files
        )


class CleanupManager:
    """
    Gerenciador de Limpeza de Arquivos Temporários
    
    Implementa limpeza automática de:
    - Arquivos locais (.bkp, .tmp, .cache, etc.)
    - Diretórios de cache
    - Objetos S3 antigos (execuções expiradas)
    - Arquivos __pycache__ e bytecode Python
    
    Padrões de Design:
    - Strategy Pattern para diferentes tipos de limpeza
    - Observer Pattern para notificações de limpeza
    
    Uso:
        manager = CleanupManager()
        result = manager.cleanup_all()
        print(result.to_dict())
    """

    def __init__(self, config: Optional[CleanupConfig] = None, s3_bucket: Optional[str] = None):
        """
        Inicializa o CleanupManager
        
        Args:
            config: Configuração de limpeza (usa padrão se não fornecida)
            s3_bucket: Nome do bucket S3 para limpeza (usa env var se não fornecido)
        """
        self.config = config or CleanupConfig.from_env()
        self.s3_bucket = s3_bucket or os.getenv('FINOPS_STATE_BUCKET', 'finops-aws-state')
        self._s3_client = None
        
        logger.info("CleanupManager initialized", extra={
            'extra_data': {
                'config': self.config.to_dict(),
                's3_bucket': self.s3_bucket
            }
        })

    @property
    def s3_client(self):
        """Lazy initialization do cliente S3"""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3')
        return self._s3_client

    def cleanup_all(self) -> CleanupResult:
        """
        Executa limpeza completa (local + S3)
        
        Returns:
            CleanupResult com métricas da limpeza
        """
        start_time = datetime.now()
        
        logger.info("Starting full cleanup process")
        
        # Limpeza local
        local_result = self.cleanup_local_files()
        
        # Limpeza S3
        s3_result = CleanupResult()
        if self.config.s3_cleanup_enabled:
            s3_result = self.cleanup_s3_objects()
        
        # Limpeza de __pycache__
        pycache_result = self.cleanup_pycache()
        
        # Mescla resultados
        final_result = local_result.merge(s3_result).merge(pycache_result)
        final_result.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info("Cleanup process completed", extra={
            'extra_data': final_result.to_dict()
        })
        
        return final_result

    def cleanup_local_files(self) -> CleanupResult:
        """
        Limpa arquivos locais baseado na configuração
        
        Returns:
            CleanupResult com métricas da limpeza local
        """
        result = CleanupResult()
        cutoff_time = datetime.now() - timedelta(hours=self.config.max_file_age_hours)
        
        for directory in self.config.cleanup_directories:
            if not os.path.exists(directory):
                continue
                
            try:
                for root, dirs, files in os.walk(directory):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        file_result = self._process_file(filepath, cutoff_time)
                        result = result.merge(file_result)
                        
            except PermissionError as e:
                result.errors.append(f"Permission denied: {directory}")
                logger.warning(f"Permission denied accessing directory: {directory}")
            except Exception as e:
                result.errors.append(f"Error processing {directory}: {str(e)}")
                logger.error(f"Error processing directory {directory}: {e}")
        
        return result

    def _process_file(self, filepath: str, cutoff_time: datetime) -> CleanupResult:
        """
        Processa um arquivo individual para limpeza
        
        Args:
            filepath: Caminho do arquivo
            cutoff_time: Data/hora de corte para arquivos antigos
            
        Returns:
            CleanupResult para o arquivo
        """
        result = CleanupResult()
        
        try:
            # Verifica se o arquivo existe
            if not os.path.isfile(filepath):
                return result
            
            # Obtém extensão do arquivo
            _, ext = os.path.splitext(filepath)
            
            # Verifica se a extensão está na lista de limpeza
            if ext.lower() not in self.config.file_extensions:
                return result
            
            # Obtém estatísticas do arquivo
            stat = os.stat(filepath)
            file_size = stat.st_size
            file_mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # Verifica se o arquivo é antigo o suficiente
            if file_mtime > cutoff_time:
                result.skipped_files.append(filepath)
                return result
            
            # Verifica tamanho máximo
            if self.config.max_file_size_mb > 0:
                if file_size > (self.config.max_file_size_mb * 1024 * 1024):
                    logger.warning(f"File exceeds max size, skipping: {filepath}")
                    result.skipped_files.append(filepath)
                    return result
            
            # Executa a deleção (ou simula em dry_run)
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Would delete: {filepath}")
                result.deleted_files.append(filepath)
                result.files_deleted += 1
                result.bytes_freed += file_size
            else:
                os.remove(filepath)
                result.deleted_files.append(filepath)
                result.files_deleted += 1
                result.bytes_freed += file_size
                logger.debug(f"Deleted file: {filepath} ({file_size} bytes)")
                
        except PermissionError:
            result.files_failed += 1
            result.errors.append(f"Permission denied: {filepath}")
        except FileNotFoundError:
            pass  # Arquivo já foi deletado
        except Exception as e:
            result.files_failed += 1
            result.errors.append(f"Error deleting {filepath}: {str(e)}")
            logger.error(f"Error deleting file {filepath}: {e}")
        
        return result

    def cleanup_s3_objects(self, prefix: str = "executions/") -> CleanupResult:
        """
        Limpa objetos antigos do S3
        
        Args:
            prefix: Prefixo S3 para buscar objetos
            
        Returns:
            CleanupResult com métricas da limpeza S3
        """
        result = CleanupResult()
        cutoff_date = datetime.now() - timedelta(days=self.config.s3_max_age_days)
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            objects_to_delete = []
            
            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    last_modified = obj['LastModified'].replace(tzinfo=None)
                    size = obj['Size']
                    
                    if last_modified < cutoff_date:
                        objects_to_delete.append({
                            'Key': key,
                            'Size': size
                        })
            
            # Deleta objetos em lotes de 1000 (limite da API)
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i + 1000]
                
                if self.config.dry_run:
                    for obj in batch:
                        logger.info(f"[DRY RUN] Would delete S3: {obj['Key']}")
                        result.s3_objects_deleted += 1
                        result.s3_bytes_freed += obj['Size']
                else:
                    delete_request = {
                        'Objects': [{'Key': obj['Key']} for obj in batch],
                        'Quiet': True
                    }
                    
                    self.s3_client.delete_objects(
                        Bucket=self.s3_bucket,
                        Delete=delete_request
                    )
                    
                    for obj in batch:
                        result.s3_objects_deleted += 1
                        result.s3_bytes_freed += obj['Size']
                    
                    logger.info(f"Deleted {len(batch)} S3 objects")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                logger.warning(f"S3 bucket not found: {self.s3_bucket}")
            else:
                result.errors.append(f"S3 error: {str(e)}")
                logger.error(f"S3 cleanup error: {e}")
        except Exception as e:
            result.errors.append(f"S3 cleanup error: {str(e)}")
            logger.error(f"S3 cleanup error: {e}")
        
        return result

    def cleanup_pycache(self, base_path: Optional[str] = None) -> CleanupResult:
        """
        Limpa diretórios __pycache__ e arquivos .pyc/.pyo
        
        Args:
            base_path: Diretório base para busca (usa diretório do projeto se não fornecido)
            
        Returns:
            CleanupResult com métricas da limpeza
        """
        result = CleanupResult()
        
        if base_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            for root, dirs, files in os.walk(base_path):
                # Remove __pycache__ directories
                if '__pycache__' in dirs:
                    pycache_path = os.path.join(root, '__pycache__')
                    try:
                        if self.config.dry_run:
                            logger.info(f"[DRY RUN] Would delete: {pycache_path}")
                        else:
                            # Calcula tamanho antes de deletar
                            for pycache_root, _, pycache_files in os.walk(pycache_path):
                                for f in pycache_files:
                                    try:
                                        result.bytes_freed += os.path.getsize(os.path.join(pycache_root, f))
                                    except OSError:
                                        pass
                            
                            shutil.rmtree(pycache_path)
                            result.files_deleted += 1
                            result.deleted_files.append(pycache_path)
                            
                    except Exception as e:
                        result.files_failed += 1
                        result.errors.append(f"Error removing {pycache_path}: {str(e)}")
                
                # Remove arquivos .pyc e .pyo individuais
                for filename in files:
                    if filename.endswith(('.pyc', '.pyo')):
                        filepath = os.path.join(root, filename)
                        try:
                            if self.config.dry_run:
                                logger.info(f"[DRY RUN] Would delete: {filepath}")
                            else:
                                file_size = os.path.getsize(filepath)
                                os.remove(filepath)
                                result.files_deleted += 1
                                result.bytes_freed += file_size
                                result.deleted_files.append(filepath)
                        except Exception as e:
                            result.files_failed += 1
                            result.errors.append(f"Error removing {filepath}: {str(e)}")
                            
        except Exception as e:
            result.errors.append(f"Error in pycache cleanup: {str(e)}")
            logger.error(f"Error in pycache cleanup: {e}")
        
        return result

    def cleanup_temp_directory(self) -> CleanupResult:
        """
        Limpa diretório temporário do sistema
        
        Returns:
            CleanupResult com métricas da limpeza
        """
        result = CleanupResult()
        temp_dir = tempfile.gettempdir()
        
        # Adiciona prefixo específico do FinOps para evitar deletar arquivos de outros processos
        finops_pattern = 'finops_'
        
        try:
            for filename in os.listdir(temp_dir):
                if filename.startswith(finops_pattern):
                    filepath = os.path.join(temp_dir, filename)
                    try:
                        if os.path.isfile(filepath):
                            file_size = os.path.getsize(filepath)
                            if self.config.dry_run:
                                logger.info(f"[DRY RUN] Would delete: {filepath}")
                            else:
                                os.remove(filepath)
                            result.files_deleted += 1
                            result.bytes_freed += file_size
                            result.deleted_files.append(filepath)
                        elif os.path.isdir(filepath):
                            if self.config.dry_run:
                                logger.info(f"[DRY RUN] Would delete directory: {filepath}")
                            else:
                                shutil.rmtree(filepath)
                            result.files_deleted += 1
                            result.deleted_files.append(filepath)
                    except Exception as e:
                        result.files_failed += 1
                        result.errors.append(f"Error removing {filepath}: {str(e)}")
                        
        except Exception as e:
            result.errors.append(f"Error cleaning temp directory: {str(e)}")
            logger.error(f"Error cleaning temp directory: {e}")
        
        return result

    def get_cleanup_status(self) -> Dict[str, Any]:
        """
        Obtém status atual dos arquivos que seriam limpos
        
        Returns:
            Dicionário com estatísticas de arquivos candidatos à limpeza
        """
        status = {
            'local_files': {
                'count': 0,
                'total_size_bytes': 0,
                'by_extension': {}
            },
            's3_objects': {
                'count': 0,
                'total_size_bytes': 0
            },
            'pycache': {
                'count': 0,
                'total_size_bytes': 0
            }
        }
        
        cutoff_time = datetime.now() - timedelta(hours=self.config.max_file_age_hours)
        
        # Conta arquivos locais
        for directory in self.config.cleanup_directories:
            if not os.path.exists(directory):
                continue
            try:
                for root, dirs, files in os.walk(directory):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        _, ext = os.path.splitext(filepath)
                        
                        if ext.lower() in self.config.file_extensions:
                            try:
                                stat = os.stat(filepath)
                                file_mtime = datetime.fromtimestamp(stat.st_mtime)
                                
                                if file_mtime < cutoff_time:
                                    status['local_files']['count'] += 1
                                    status['local_files']['total_size_bytes'] += stat.st_size
                                    
                                    if ext not in status['local_files']['by_extension']:
                                        status['local_files']['by_extension'][ext] = {'count': 0, 'size': 0}
                                    status['local_files']['by_extension'][ext]['count'] += 1
                                    status['local_files']['by_extension'][ext]['size'] += stat.st_size
                            except OSError:
                                pass
            except PermissionError:
                pass
        
        # Conta objetos S3
        if self.config.s3_cleanup_enabled:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.config.s3_max_age_days)
                paginator = self.s3_client.get_paginator('list_objects_v2')
                
                for page in paginator.paginate(Bucket=self.s3_bucket, Prefix="executions/"):
                    for obj in page.get('Contents', []):
                        last_modified = obj['LastModified'].replace(tzinfo=None)
                        if last_modified < cutoff_date:
                            status['s3_objects']['count'] += 1
                            status['s3_objects']['total_size_bytes'] += obj['Size']
            except Exception:
                pass
        
        return status


def cleanup_after_execution(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função helper para executar limpeza após uma execução do FinOps
    e adicionar métricas ao resultado
    
    Args:
        result_dict: Dicionário com resultado da execução FinOps
        
    Returns:
        Dicionário atualizado com métricas de limpeza
    """
    manager = CleanupManager()
    cleanup_result = manager.cleanup_all()
    
    result_dict['cleanup_metrics'] = cleanup_result.to_dict()
    
    return result_dict
