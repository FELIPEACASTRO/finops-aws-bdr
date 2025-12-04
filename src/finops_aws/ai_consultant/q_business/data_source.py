"""
Amazon Q Business Data Source Manager

Gerencia fontes de dados S3 para o Amazon Q Business,
incluindo sync, upload e indexação de documentos.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError

from .config import QBusinessConfig
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DocumentMetadata:
    """Metadados de documento para indexação"""
    document_id: str
    title: str
    source_uri: str
    content_type: str
    created_at: str
    updated_at: str
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "source_uri": self.source_uri,
            "content_type": self.content_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "attributes": self.attributes
        }


class QBusinessDataSource:
    """
    Gerenciador de Data Sources para Amazon Q Business
    
    Responsável por:
    - Preparar dados de custo para indexação
    - Gerenciar documentos de conhecimento
    - Sincronizar com S3
    - Monitorar status de indexação
    
    Example:
        ```python
        data_source = QBusinessDataSource()
        
        # Preparar dados de custo para Q
        data_source.prepare_cost_data(cost_report)
        
        # Sincronizar com Q Business
        data_source.trigger_sync()
        ```
    """
    
    def __init__(
        self,
        config: Optional[QBusinessConfig] = None,
        s3_client: Optional[Any] = None,
        q_client: Optional[Any] = None
    ):
        """
        Inicializa gerenciador de data source
        
        Args:
            config: Configuração Q Business
            s3_client: Cliente S3 injetado
            q_client: Cliente Q Business injetado
        """
        self.config = config or QBusinessConfig.from_env()
        self._s3_client = s3_client
        self._q_client = q_client
    
    @property
    def s3_client(self):
        """Lazy loading do cliente S3"""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                region_name=self.config.region
            )
        return self._s3_client
    
    @property
    def q_client(self):
        """Lazy loading do cliente Q Business"""
        if self._q_client is None:
            self._q_client = boto3.client(
                'qbusiness',
                region_name=self.config.region
            )
        return self._q_client
    
    def prepare_cost_data(
        self,
        cost_report: Dict[str, Any],
        report_date: Optional[str] = None
    ) -> str:
        """
        Prepara dados de custo para indexação no Q Business
        
        Args:
            cost_report: Relatório de custos do FinOps
            report_date: Data do relatório (default: hoje)
            
        Returns:
            S3 key do arquivo criado
        """
        if not self.config.s3_bucket:
            raise ValueError("S3 bucket não configurado")
        
        report_date = report_date or datetime.utcnow().strftime("%Y-%m-%d")
        
        structured_data = self._structure_cost_data(cost_report, report_date)
        
        s3_key = f"processed/cost_summary_{report_date}.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key,
                Body=json.dumps(structured_data, indent=2, default=str),
                ContentType='application/json',
                Metadata={
                    'report-date': report_date,
                    'data-type': 'cost-summary',
                    'generated-by': 'finops-aws'
                }
            )
            
            logger.info(f"Dados de custo preparados: s3://{self.config.s3_bucket}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Erro ao salvar dados de custo: {e}")
            raise
    
    def _structure_cost_data(
        self,
        cost_report: Dict[str, Any],
        report_date: str
    ) -> Dict[str, Any]:
        """Estrutura dados de custo para consumo pelo Q Business"""
        
        services = cost_report.get('services', [])
        top_services = sorted(
            services,
            key=lambda x: x.get('cost', 0),
            reverse=True
        )[:10] if isinstance(services, list) else []
        
        recommendations = cost_report.get('recommendations', [])
        anomalies = cost_report.get('anomalies', [])
        
        return {
            "metadata": {
                "report_date": report_date,
                "generated_at": datetime.utcnow().isoformat(),
                "data_version": "1.0"
            },
            "summary": {
                "total_cost": cost_report.get('total_cost', 0),
                "period": cost_report.get('period', {}),
                "currency": "USD",
                "service_count": len(services) if isinstance(services, list) else 0,
                "change_from_previous": cost_report.get('change_percentage', 0)
            },
            "top_services": [
                {
                    "name": svc.get('name', svc.get('service_name', 'Unknown')),
                    "cost": svc.get('cost', svc.get('total_cost', 0)),
                    "percentage_of_total": svc.get('percentage', 0),
                    "trend": svc.get('trend', 'STABLE'),
                    "resource_count": svc.get('resource_count', 0)
                }
                for svc in top_services
            ],
            "recommendations": [
                {
                    "type": rec.get('recommendation_type', rec.get('type', '')),
                    "description": rec.get('description', ''),
                    "estimated_savings": rec.get('estimated_savings', 0),
                    "priority": rec.get('priority', 'MEDIUM'),
                    "effort": rec.get('implementation_effort', 'MEDIUM')
                }
                for rec in recommendations[:20]
            ],
            "anomalies": [
                {
                    "service": an.get('service', ''),
                    "type": an.get('anomaly_type', an.get('type', '')),
                    "description": an.get('description', ''),
                    "impact": an.get('impact', 0),
                    "detected_at": an.get('detected_at', '')
                }
                for an in anomalies[:10]
            ],
            "trends": cost_report.get('trends', {}),
            "forecasts": cost_report.get('forecasts', {})
        }
    
    def upload_knowledge_document(
        self,
        document_id: str,
        title: str,
        content: str,
        category: str = "best-practices",
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Upload documento de conhecimento para S3
        
        Args:
            document_id: ID único do documento
            title: Título do documento
            content: Conteúdo em Markdown
            category: Categoria do documento
            tags: Tags para busca
            
        Returns:
            S3 key do documento
        """
        if not self.config.s3_bucket:
            raise ValueError("S3 bucket não configurado")
        
        s3_key = f"knowledge/{category}/{document_id}.md"
        
        metadata = {
            'document-id': document_id,
            'title': title,
            'category': category,
            'tags': ','.join(tags or []),
            'uploaded-at': datetime.utcnow().isoformat()
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown',
                Metadata=metadata
            )
            
            logger.info(f"Documento de conhecimento enviado: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Erro ao enviar documento: {e}")
            raise
    
    def trigger_sync(self) -> Dict[str, Any]:
        """
        Dispara sincronização do data source com Q Business
        
        Returns:
            Dict com status do sync
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
            
            return {
                "status": "STARTED",
                "execution_id": response.get("executionId"),
                "started_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_msg = str(e)
            if "already in progress" in error_msg.lower():
                return {"status": "ALREADY_IN_PROGRESS"}
            raise
    
    def get_sync_history(
        self,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtém histórico de sincronizações
        
        Args:
            max_results: Número máximo de resultados
            
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
            
            return [
                {
                    "execution_id": job.get("executionId"),
                    "status": job.get("status"),
                    "started_at": job.get("startTime"),
                    "ended_at": job.get("endTime"),
                    "documents_added": job.get("metrics", {}).get("documentsAdded", 0),
                    "documents_modified": job.get("metrics", {}).get("documentsModified", 0),
                    "documents_deleted": job.get("metrics", {}).get("documentsDeleted", 0),
                    "documents_failed": job.get("metrics", {}).get("documentsFailed", 0)
                }
                for job in response.get("history", [])
            ]
            
        except ClientError as e:
            logger.error(f"Erro ao obter histórico de sync: {e}")
            return []
    
    def list_indexed_documents(
        self,
        prefix: str = "processed/"
    ) -> List[DocumentMetadata]:
        """
        Lista documentos indexados no S3
        
        Args:
            prefix: Prefixo S3 para filtrar
            
        Returns:
            Lista de metadados de documentos
        """
        documents = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(
                Bucket=self.config.s3_bucket,
                Prefix=prefix
            ):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    
                    head = self.s3_client.head_object(
                        Bucket=self.config.s3_bucket,
                        Key=key
                    )
                    
                    metadata = head.get('Metadata', {})
                    
                    documents.append(DocumentMetadata(
                        document_id=metadata.get('document-id', key),
                        title=metadata.get('title', key.split('/')[-1]),
                        source_uri=f"s3://{self.config.s3_bucket}/{key}",
                        content_type=head.get('ContentType', 'application/octet-stream'),
                        created_at=metadata.get('uploaded-at', ''),
                        updated_at=obj['LastModified'].isoformat(),
                        attributes=metadata
                    ))
            
            return documents
            
        except ClientError as e:
            logger.error(f"Erro ao listar documentos: {e}")
            return []
    
    def delete_document(self, s3_key: str) -> bool:
        """
        Remove documento do S3
        
        Args:
            s3_key: Key do objeto no S3
            
        Returns:
            True se removido com sucesso
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key
            )
            logger.info(f"Documento removido: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Erro ao remover documento: {e}")
            return False
    
    def prepare_batch_upload(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepara lote de documentos para upload
        
        Args:
            documents: Lista de documentos com id, title, content
            
        Returns:
            Dict com status do batch upload
        """
        results = {
            "total": len(documents),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for doc in documents:
            try:
                self.upload_knowledge_document(
                    document_id=doc['id'],
                    title=doc['title'],
                    content=doc['content'],
                    category=doc.get('category', 'general'),
                    tags=doc.get('tags', [])
                )
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "document_id": doc['id'],
                    "error": str(e)
                })
        
        return results
