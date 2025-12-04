"""
Knowledge Indexer

Indexador de documentos de conhecimento para Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from ..q_business.config import QBusinessConfig
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeIndexer:
    """
    Indexador de documentos de conhecimento
    
    Gerencia upload e indexação de documentos para
    a base de conhecimento do Amazon Q Business.
    
    Example:
        ```python
        indexer = KnowledgeIndexer()
        
        # Indexar todos os documentos locais
        indexer.index_all_documents()
        
        # Indexar documento específico
        indexer.index_document("best_practices.md")
        ```
    """
    
    KNOWLEDGE_DIR = Path(__file__).parent / "documents"
    
    DOCUMENT_CATEGORIES = {
        "aws_best_practices": "Melhores práticas AWS",
        "finops_framework": "Framework FinOps",
        "pricing_guides": "Guias de precificação",
        "optimization_patterns": "Padrões de otimização",
        "case_studies": "Casos de estudo"
    }
    
    def __init__(
        self,
        config: Optional[QBusinessConfig] = None,
        s3_client: Optional[Any] = None
    ):
        """
        Inicializa indexador
        
        Args:
            config: Configuração Q Business
            s3_client: Cliente S3 injetado
        """
        self.config = config or QBusinessConfig.from_env()
        self._s3_client = s3_client
    
    @property
    def s3_client(self):
        """Lazy loading do cliente S3"""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                region_name=self.config.region
            )
        return self._s3_client
    
    def index_all_documents(self) -> Dict[str, Any]:
        """
        Indexa todos os documentos de conhecimento
        
        Returns:
            Dict com resultado da indexação
        """
        if not self.config.s3_bucket:
            raise ValueError("S3 bucket não configurado")
        
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "documents": []
        }
        
        for category in self.DOCUMENT_CATEGORIES.keys():
            category_path = self.KNOWLEDGE_DIR / category
            
            if category_path.exists():
                for doc_file in category_path.glob("*.md"):
                    results["total"] += 1
                    
                    try:
                        s3_key = self.index_document(
                            doc_file,
                            category=category
                        )
                        results["success"] += 1
                        results["documents"].append({
                            "file": doc_file.name,
                            "category": category,
                            "s3_key": s3_key,
                            "status": "SUCCESS"
                        })
                    except Exception as e:
                        results["failed"] += 1
                        results["documents"].append({
                            "file": doc_file.name,
                            "category": category,
                            "status": "FAILED",
                            "error": str(e)
                        })
        
        logger.info(
            f"Indexação completa: {results['success']}/{results['total']} documentos"
        )
        
        return results
    
    def index_document(
        self,
        file_path: Path,
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Indexa documento individual
        
        Args:
            file_path: Caminho do arquivo
            category: Categoria do documento
            tags: Tags para busca
            
        Returns:
            S3 key do documento indexado
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        content = file_path.read_text(encoding='utf-8')
        
        document_id = f"{category}_{file_path.stem}"
        title = self._extract_title(content) or file_path.stem.replace('_', ' ').title()
        
        s3_key = f"knowledge/{category}/{file_path.name}"
        
        metadata = {
            'document-id': document_id,
            'title': title[:256],
            'category': category,
            'tags': ','.join(tags or []),
            'source': 'finops-aws-knowledge',
            'indexed-at': datetime.utcnow().isoformat()
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown',
                Metadata=metadata
            )
            
            logger.info(f"Documento indexado: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Erro ao indexar documento: {e}")
            raise
    
    def index_from_string(
        self,
        document_id: str,
        title: str,
        content: str,
        category: str = "dynamic",
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Indexa documento a partir de string
        
        Args:
            document_id: ID único do documento
            title: Título do documento
            content: Conteúdo em Markdown
            category: Categoria
            tags: Tags para busca
            
        Returns:
            S3 key do documento
        """
        s3_key = f"knowledge/{category}/{document_id}.md"
        
        metadata = {
            'document-id': document_id,
            'title': title[:256],
            'category': category,
            'tags': ','.join(tags or []),
            'source': 'finops-aws-dynamic',
            'indexed-at': datetime.utcnow().isoformat()
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown',
                Metadata=metadata
            )
            
            return s3_key
            
        except ClientError as e:
            logger.error(f"Erro ao indexar documento: {e}")
            raise
    
    def delete_document(self, s3_key: str) -> bool:
        """
        Remove documento do índice
        
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
    
    def list_indexed_documents(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista documentos indexados
        
        Args:
            category: Filtrar por categoria
            
        Returns:
            Lista de documentos
        """
        prefix = f"knowledge/{category}/" if category else "knowledge/"
        
        documents = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(
                Bucket=self.config.s3_bucket,
                Prefix=prefix
            ):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    
                    try:
                        head = self.s3_client.head_object(
                            Bucket=self.config.s3_bucket,
                            Key=key
                        )
                        metadata = head.get('Metadata', {})
                        
                        documents.append({
                            "s3_key": key,
                            "document_id": metadata.get('document-id', key),
                            "title": metadata.get('title', ''),
                            "category": metadata.get('category', ''),
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat()
                        })
                    except ClientError:
                        documents.append({
                            "s3_key": key,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat()
                        })
            
            return documents
            
        except ClientError as e:
            logger.error(f"Erro ao listar documentos: {e}")
            return []
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extrai título do documento Markdown"""
        for line in content.split('\n')[:10]:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None
    
    def get_document_content(self, s3_key: str) -> Optional[str]:
        """
        Obtém conteúdo de documento indexado
        
        Args:
            s3_key: Key do objeto no S3
            
        Returns:
            Conteúdo do documento ou None
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key
            )
            return response['Body'].read().decode('utf-8')
            
        except ClientError:
            return None
