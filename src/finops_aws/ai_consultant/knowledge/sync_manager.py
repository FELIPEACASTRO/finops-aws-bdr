"""
Sync Manager

Gerenciador de sincronização entre S3 e Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from ..q_business.config import QBusinessConfig
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class SyncStatus(Enum):
    """Status de sincronização"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class SyncManager:
    """
    Gerenciador de sincronização Q Business
    
    Controla sincronização entre S3 e índice do Q Business,
    monitora progresso e gerencia erros.
    
    Example:
        ```python
        sync = SyncManager()
        
        # Iniciar sync
        job = sync.start_sync()
        
        # Aguardar conclusão
        result = sync.wait_for_completion(job['execution_id'])
        ```
    """
    
    def __init__(
        self,
        config: Optional[QBusinessConfig] = None,
        q_client: Optional[Any] = None
    ):
        """
        Inicializa gerenciador de sync
        
        Args:
            config: Configuração Q Business
            q_client: Cliente Q Business injetado
        """
        self.config = config or QBusinessConfig.from_env()
        self._q_client = q_client
    
    @property
    def q_client(self):
        """Lazy loading do cliente Q Business"""
        if self._q_client is None:
            self._q_client = boto3.client(
                'qbusiness',
                region_name=self.config.region
            )
        return self._q_client
    
    def start_sync(self) -> Dict[str, Any]:
        """
        Inicia sincronização do data source
        
        Returns:
            Dict com informações do sync job
        """
        if not all([
            self.config.application_id,
            self.config.index_id,
            self.config.data_source_id
        ]):
            raise ValueError(
                "application_id, index_id e data_source_id são obrigatórios"
            )
        
        try:
            response = self.q_client.start_data_source_sync_job(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                dataSourceId=self.config.data_source_id
            )
            
            execution_id = response.get("executionId")
            
            logger.info(f"Sync iniciado: {execution_id}")
            
            return {
                "execution_id": execution_id,
                "status": SyncStatus.IN_PROGRESS.value,
                "started_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_msg = str(e)
            
            if "already in progress" in error_msg.lower():
                logger.info("Sync já em andamento")
                return {
                    "status": SyncStatus.IN_PROGRESS.value,
                    "message": "Sync already in progress"
                }
            
            logger.error(f"Erro ao iniciar sync: {e}")
            raise
    
    def get_sync_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Verifica status de um sync job
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Dict com status do sync
        """
        try:
            response = self.q_client.list_data_source_sync_jobs(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                dataSourceId=self.config.data_source_id,
                maxResults=20
            )
            
            for job in response.get("history", []):
                if job.get("executionId") == execution_id:
                    metrics = job.get("metrics", {})
                    
                    return {
                        "execution_id": execution_id,
                        "status": job.get("status"),
                        "started_at": job.get("startTime"),
                        "ended_at": job.get("endTime"),
                        "error": job.get("error"),
                        "metrics": {
                            "documents_added": metrics.get("documentsAdded", 0),
                            "documents_modified": metrics.get("documentsModified", 0),
                            "documents_deleted": metrics.get("documentsDeleted", 0),
                            "documents_failed": metrics.get("documentsFailed", 0)
                        }
                    }
            
            return {
                "execution_id": execution_id,
                "status": "NOT_FOUND"
            }
            
        except ClientError as e:
            logger.error(f"Erro ao verificar status: {e}")
            return {
                "execution_id": execution_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    def wait_for_completion(
        self,
        execution_id: str,
        timeout_seconds: int = 300,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Aguarda conclusão de sync job
        
        Args:
            execution_id: ID da execução
            timeout_seconds: Timeout em segundos
            poll_interval: Intervalo de polling em segundos
            
        Returns:
            Dict com resultado final
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                return {
                    "execution_id": execution_id,
                    "status": "TIMEOUT",
                    "elapsed_seconds": elapsed
                }
            
            status = self.get_sync_status(execution_id)
            current_status = status.get("status")
            
            if current_status in [
                SyncStatus.SUCCEEDED.value,
                "SUCCEEDED",
                "COMPLETE"
            ]:
                logger.info(f"Sync concluído com sucesso: {execution_id}")
                return status
            
            if current_status in [
                SyncStatus.FAILED.value,
                "FAILED",
                "ERROR"
            ]:
                logger.error(f"Sync falhou: {execution_id}")
                return status
            
            if current_status in [
                SyncStatus.STOPPED.value,
                "STOPPED",
                "CANCELLED"
            ]:
                logger.warning(f"Sync interrompido: {execution_id}")
                return status
            
            logger.debug(f"Sync em andamento: {current_status}")
            time.sleep(poll_interval)
    
    def stop_sync(self, execution_id: str) -> Dict[str, Any]:
        """
        Interrompe sync job em andamento
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Dict com resultado da interrupção
        """
        try:
            self.q_client.stop_data_source_sync_job(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                dataSourceId=self.config.data_source_id
            )
            
            logger.info(f"Sync interrompido: {execution_id}")
            
            return {
                "execution_id": execution_id,
                "status": SyncStatus.STOPPING.value
            }
            
        except ClientError as e:
            logger.error(f"Erro ao interromper sync: {e}")
            return {
                "execution_id": execution_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    def get_sync_history(
        self,
        max_results: int = 10,
        include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtém histórico de sincronizações
        
        Args:
            max_results: Número máximo de resultados
            include_metrics: Incluir métricas detalhadas
            
        Returns:
            Lista de sync jobs
        """
        try:
            response = self.q_client.list_data_source_sync_jobs(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                dataSourceId=self.config.data_source_id,
                maxResults=max_results
            )
            
            history = []
            for job in response.get("history", []):
                job_info = {
                    "execution_id": job.get("executionId"),
                    "status": job.get("status"),
                    "started_at": job.get("startTime"),
                    "ended_at": job.get("endTime")
                }
                
                if include_metrics:
                    metrics = job.get("metrics", {})
                    job_info["metrics"] = {
                        "documents_added": metrics.get("documentsAdded", 0),
                        "documents_modified": metrics.get("documentsModified", 0),
                        "documents_deleted": metrics.get("documentsDeleted", 0),
                        "documents_failed": metrics.get("documentsFailed", 0)
                    }
                
                if job.get("error"):
                    job_info["error"] = job["error"]
                
                history.append(job_info)
            
            return history
            
        except ClientError as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def get_last_successful_sync(self) -> Optional[Dict[str, Any]]:
        """
        Obtém último sync bem-sucedido
        
        Returns:
            Dict com informações do último sync ou None
        """
        history = self.get_sync_history(max_results=20)
        
        for job in history:
            if job.get("status") in ["SUCCEEDED", "COMPLETE"]:
                return job
        
        return None
    
    def is_sync_needed(
        self,
        hours_threshold: int = 24
    ) -> bool:
        """
        Verifica se sincronização é necessária
        
        Args:
            hours_threshold: Horas desde último sync
            
        Returns:
            True se sync é necessário
        """
        last_sync = self.get_last_successful_sync()
        
        if not last_sync:
            return True
        
        ended_at = last_sync.get("ended_at")
        if not ended_at:
            return True
        
        if isinstance(ended_at, str):
            from datetime import datetime
            try:
                ended_at = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
            except ValueError:
                return True
        
        now = datetime.utcnow()
        if hasattr(ended_at, 'replace'):
            ended_at = ended_at.replace(tzinfo=None)
        
        hours_since = (now - ended_at).total_seconds() / 3600
        
        return hours_since > hours_threshold
