"""
Amazon Q Business Client

Cliente principal para interação com Amazon Q Business API.
Gerencia aplicações, índices, data sources e chat.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
import json
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from .config import QBusinessConfig, QBusinessIndexType, QBusinessRetrieverType
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ChatResponse:
    """Resposta do chat Amazon Q Business"""
    message: str
    source_attributions: List[Dict[str, Any]]
    conversation_id: Optional[str]
    system_message_id: Optional[str]
    action_review: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "source_attributions": self.source_attributions,
            "conversation_id": self.conversation_id,
            "system_message_id": self.system_message_id,
            "action_review": self.action_review
        }


class QBusinessClient:
    """
    Cliente para Amazon Q Business
    
    Fornece interface unificada para:
    - Gerenciamento de aplicações
    - Criação e gestão de índices
    - Configuração de data sources
    - Chat síncrono (chat_sync)
    - Busca de conteúdo relevante
    
    Example:
        ```python
        config = QBusinessConfig.from_env()
        client = QBusinessClient(config)
        
        response = client.chat("Analise os custos de EC2")
        print(response.message)
        ```
    """
    
    def __init__(
        self,
        config: Optional[QBusinessConfig] = None,
        boto_client: Optional[Any] = None
    ):
        """
        Inicializa cliente Q Business
        
        Args:
            config: Configuração do Q Business
            boto_client: Cliente boto3 injetado (para testes)
        """
        self.config = config or QBusinessConfig.from_env()
        self._client = boto_client
        self._sts_client = None
        self._s3_client = None
    
    @property
    def client(self):
        """Lazy loading do cliente Q Business"""
        if self._client is None:
            self._client = boto3.client(
                'qbusiness',
                region_name=self.config.region
            )
        return self._client
    
    @property
    def sts_client(self):
        """Lazy loading do cliente STS"""
        if self._sts_client is None:
            self._sts_client = boto3.client(
                'sts',
                region_name=self.config.region
            )
        return self._sts_client
    
    @property
    def s3_client(self):
        """Lazy loading do cliente S3"""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                region_name=self.config.region
            )
        return self._s3_client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde da integração Q Business
        
        Returns:
            Dict com status de cada componente
        """
        status = {
            "healthy": True,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        try:
            if self.config.application_id:
                app = self.get_application()
                status["components"]["application"] = {
                    "status": "OK",
                    "name": app.get("displayName"),
                    "status_detail": app.get("status")
                }
            else:
                status["components"]["application"] = {
                    "status": "NOT_CONFIGURED"
                }
                status["healthy"] = False
        except Exception as e:
            status["components"]["application"] = {
                "status": "ERROR",
                "error": str(e)
            }
            status["healthy"] = False
        
        try:
            if self.config.index_id and self.config.application_id:
                index = self.get_index()
                status["components"]["index"] = {
                    "status": "OK",
                    "name": index.get("displayName"),
                    "status_detail": index.get("status")
                }
            else:
                status["components"]["index"] = {
                    "status": "NOT_CONFIGURED"
                }
        except Exception as e:
            status["components"]["index"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        try:
            if self.config.s3_bucket:
                self.s3_client.head_bucket(Bucket=self.config.s3_bucket)
                status["components"]["s3_bucket"] = {
                    "status": "OK",
                    "bucket": self.config.s3_bucket
                }
            else:
                status["components"]["s3_bucket"] = {
                    "status": "NOT_CONFIGURED"
                }
        except Exception as e:
            status["components"]["s3_bucket"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        return status
    
    def get_application(self) -> Dict[str, Any]:
        """
        Obtém detalhes da aplicação Q Business
        
        Returns:
            Dict com informações da aplicação
        """
        if not self.config.application_id:
            raise ValueError("application_id não configurado")
        
        try:
            response = self.client.get_application(
                applicationId=self.config.application_id
            )
            return {
                "applicationId": response.get("applicationId"),
                "displayName": response.get("displayName"),
                "description": response.get("description"),
                "status": response.get("status"),
                "createdAt": response.get("createdAt"),
                "updatedAt": response.get("updatedAt"),
                "roleArn": response.get("roleArn")
            }
        except ClientError as e:
            logger.error(f"Erro ao obter aplicação Q Business: {e}")
            raise
    
    def get_index(self) -> Dict[str, Any]:
        """
        Obtém detalhes do índice
        
        Returns:
            Dict com informações do índice
        """
        if not self.config.application_id or not self.config.index_id:
            raise ValueError("application_id e index_id são obrigatórios")
        
        try:
            response = self.client.get_index(
                applicationId=self.config.application_id,
                indexId=self.config.index_id
            )
            return {
                "indexId": response.get("indexId"),
                "displayName": response.get("displayName"),
                "status": response.get("status"),
                "type": response.get("type"),
                "documentCount": response.get("documentAttributeConfigurations", [])
            }
        except ClientError as e:
            logger.error(f"Erro ao obter índice Q Business: {e}")
            raise
    
    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        attribute_filter: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Envia mensagem para Amazon Q Business (chat_sync)
        
        Args:
            message: Mensagem do usuário
            conversation_id: ID da conversa (para continuidade)
            attachments: Anexos (arquivos)
            attribute_filter: Filtros de atributos
            
        Returns:
            ChatResponse com resposta do Q Business
        """
        if not self.config.application_id:
            raise ValueError("application_id não configurado")
        
        try:
            params = {
                "applicationId": self.config.application_id,
                "userMessage": message,
                "clientToken": str(random.randint(0, 1000000))
            }
            
            if conversation_id:
                params["conversationId"] = conversation_id
            
            if attachments:
                params["attachments"] = attachments
            
            if attribute_filter:
                params["attributeFilter"] = attribute_filter
            
            logger.info(f"Enviando mensagem para Q Business: {message[:100]}...")
            
            response = self.client.chat_sync(**params)
            
            return ChatResponse(
                message=response.get("systemMessage", ""),
                source_attributions=response.get("sourceAttributions", []),
                conversation_id=response.get("conversationId"),
                system_message_id=response.get("systemMessageId"),
                action_review=response.get("actionReview")
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', '')
            
            logger.error(f"Erro Q Business chat_sync: {error_code} - {error_message}")
            
            if error_code == 'AccessDeniedException':
                raise PermissionError(
                    "Acesso negado. Verifique credenciais identity-aware "
                    "e permissões IAM Identity Center."
                )
            elif error_code == 'ValidationException':
                raise ValueError(f"Validação falhou: {error_message}")
            elif error_code == 'ThrottlingException':
                raise RuntimeError("Rate limit excedido. Tente novamente.")
            else:
                raise
    
    def chat_with_context(
        self,
        message: str,
        context_data: Dict[str, Any],
        persona: str = "executive"
    ) -> ChatResponse:
        """
        Chat com contexto de dados FinOps
        
        Args:
            message: Mensagem/pergunta
            context_data: Dados de contexto (custos, métricas)
            persona: Tipo de persona para resposta
            
        Returns:
            ChatResponse com análise contextualizada
        """
        context_json = json.dumps(context_data, indent=2, default=str)
        
        enriched_message = f"""
## Contexto de Dados FinOps

```json
{context_json}
```

## Pergunta/Solicitação

{message}

## Instruções

Responda considerando o contexto de dados acima. 
Persona: {persona}
"""
        
        return self.chat(enriched_message)
    
    def search_relevant_content(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca conteúdo relevante no índice
        
        Args:
            query: Texto de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes
        """
        if not self.config.application_id or not self.config.retriever_id:
            raise ValueError("application_id e retriever_id são obrigatórios")
        
        try:
            response = self.client.search_relevant_content(
                applicationId=self.config.application_id,
                retrieverId=self.config.retriever_id,
                queryText=query
            )
            
            results = []
            for item in response.get("relevantContent", [])[:max_results]:
                results.append({
                    "content": item.get("content", {}).get("text", ""),
                    "document_id": item.get("documentId"),
                    "document_title": item.get("documentTitle"),
                    "score_attributes": item.get("scoreAttributes")
                })
            
            return results
            
        except ClientError as e:
            logger.error(f"Erro ao buscar conteúdo: {e}")
            raise
    
    def start_data_source_sync(self) -> Dict[str, Any]:
        """
        Inicia sincronização do data source S3
        
        Returns:
            Dict com status do sync job
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
            response = self.client.start_data_source_sync_job(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                dataSourceId=self.config.data_source_id
            )
            
            logger.info(f"Sync iniciado: {response.get('executionId')}")
            
            return {
                "execution_id": response.get("executionId"),
                "status": "SYNCING"
            }
            
        except ClientError as e:
            if "already in progress" in str(e).lower():
                logger.info("Sync já em progresso")
                return {"status": "ALREADY_SYNCING"}
            raise
    
    def get_sync_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Verifica status de um sync job
        
        Args:
            execution_id: ID da execução do sync
            
        Returns:
            Dict com status do sync
        """
        try:
            response = self.client.list_data_source_sync_jobs(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                dataSourceId=self.config.data_source_id,
                maxResults=10
            )
            
            for job in response.get("history", []):
                if job.get("executionId") == execution_id:
                    return {
                        "execution_id": execution_id,
                        "status": job.get("status"),
                        "started_at": job.get("startTime"),
                        "ended_at": job.get("endTime"),
                        "metrics": job.get("metrics", {})
                    }
            
            return {"status": "NOT_FOUND"}
            
        except ClientError as e:
            logger.error(f"Erro ao verificar sync: {e}")
            raise
    
    def upload_document(
        self,
        document_id: str,
        title: str,
        content: str,
        content_type: str = "PLAIN_TEXT",
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload de documento para o índice
        
        Args:
            document_id: ID único do documento
            title: Título do documento
            content: Conteúdo do documento
            content_type: Tipo de conteúdo (PLAIN_TEXT, HTML)
            attributes: Atributos adicionais
            
        Returns:
            Dict com resultado do upload
        """
        if not self.config.application_id or not self.config.index_id:
            raise ValueError("application_id e index_id são obrigatórios")
        
        try:
            document = {
                "id": document_id,
                "title": title,
                "content": {
                    "blob": content.encode('utf-8'),
                    "type": content_type
                }
            }
            
            if attributes:
                document["attributes"] = attributes
            
            response = self.client.batch_put_document(
                applicationId=self.config.application_id,
                indexId=self.config.index_id,
                documents=[document]
            )
            
            failed = response.get("failedDocuments", [])
            
            if failed:
                logger.warning(f"Documentos falharam: {failed}")
                return {
                    "status": "PARTIAL",
                    "failed": failed
                }
            
            logger.info(f"Documento {document_id} indexado com sucesso")
            return {"status": "SUCCESS", "document_id": document_id}
            
        except ClientError as e:
            logger.error(f"Erro ao indexar documento: {e}")
            raise
    
    def list_conversations(
        self,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista conversas recentes
        
        Args:
            max_results: Número máximo de conversas
            
        Returns:
            Lista de conversas
        """
        try:
            response = self.client.list_conversations(
                applicationId=self.config.application_id,
                maxResults=max_results
            )
            
            return [
                {
                    "conversation_id": conv.get("conversationId"),
                    "title": conv.get("title"),
                    "start_time": conv.get("startTime")
                }
                for conv in response.get("conversations", [])
            ]
            
        except ClientError as e:
            logger.error(f"Erro ao listar conversas: {e}")
            return []
