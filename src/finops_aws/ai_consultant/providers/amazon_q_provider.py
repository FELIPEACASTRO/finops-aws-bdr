"""
Amazon Q Business Provider - Provedor AWS Nativo

Implementa o BaseAIProvider para Amazon Q Business.
Usa a base de conhecimento AWS para respostas contextualizadas.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from .base_provider import (
    BaseAIProvider, 
    AIProviderConfig, 
    AIProviderType,
    AIResponse,
    PersonaType
)


class AmazonQProvider(BaseAIProvider):
    """
    Provedor Amazon Q Business
    
    Usa AWS Q Business para chat e analise FinOps.
    Requer Q_BUSINESS_APPLICATION_ID configurado.
    
    Vantagens:
    - Integracao nativa AWS
    - RAG com base de conhecimento
    - Seguranca IAM integrada
    
    Example:
        ```python
        config = AIProviderConfig.from_env(AIProviderType.AMAZON_Q)
        provider = AmazonQProvider(config)
        
        response = provider.generate_report(costs, resources, PersonaType.EXECUTIVE)
        print(response.content)
        ```
    """
    
    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.AMAZON_Q
    
    @property
    def available_models(self) -> List[str]:
        return ["amazon-q-business"]
    
    @property
    def client(self):
        """Lazy loading do cliente Q Business"""
        if self._client is None:
            self._client = boto3.client(
                'qbusiness',
                region_name=self.config.region
            )
        return self._client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude da conexao com Q Business
        
        Returns:
            Dict com status
        """
        status = {
            "healthy": False,
            "provider": self.provider_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {}
        }
        
        application_id = self.config.extra_config.get('application_id')
        
        if not application_id:
            status["details"]["error"] = "Q_BUSINESS_APPLICATION_ID nao configurado"
            return status
        
        try:
            response = self.client.get_application(
                applicationId=application_id
            )
            
            status["healthy"] = response.get("status") == "ACTIVE"
            status["details"] = {
                "application_id": application_id,
                "name": response.get("displayName"),
                "status": response.get("status")
            }
            
        except ClientError as e:
            status["details"]["error"] = str(e)
        except BotoCoreError as e:
            status["details"]["error"] = str(e)
        
        return status
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Envia mensagem para Amazon Q Business
        
        Args:
            message: Mensagem do usuario
            system_prompt: Prompt de sistema (prefixado)
            context: Contexto adicional
            
        Returns:
            AIResponse com resposta
        """
        import random
        
        application_id = self.config.extra_config.get('application_id')
        
        if not application_id:
            raise ValueError("Q_BUSINESS_APPLICATION_ID nao configurado")
        
        full_message = ""
        if system_prompt:
            full_message = f"{system_prompt}\n\n"
        full_message += message
        
        if context:
            import json
            full_message += f"\n\n## Contexto\n```json\n{json.dumps(context, indent=2, default=str)}\n```"
        
        start_time = time.time()
        
        try:
            response = self.client.chat_sync(
                applicationId=application_id,
                userMessage=full_message,
                clientToken=str(random.randint(0, 1000000))
            )
            
            latency = int((time.time() - start_time) * 1000)
            
            sources = []
            for attr in response.get("sourceAttributions", []):
                sources.append({
                    "title": attr.get("title"),
                    "url": attr.get("url"),
                    "snippet": attr.get("snippet")
                })
            
            return AIResponse(
                content=response.get("systemMessage", ""),
                provider=self.provider_type,
                model="amazon-q-business",
                latency_ms=latency,
                sources=sources,
                metadata={
                    "conversation_id": response.get("conversationId"),
                    "message_id": response.get("systemMessageId")
                }
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_msg = e.response.get('Error', {}).get('Message', '')
            
            raise RuntimeError(f"Erro Q Business [{error_code}]: {error_msg}")
    
    def generate_report(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType = PersonaType.EXECUTIVE
    ) -> AIResponse:
        """
        Gera relatorio FinOps usando Q Business
        
        Args:
            costs: Dados de custo AWS
            resources: Dados de recursos AWS
            persona: Tipo de persona
            
        Returns:
            AIResponse com relatorio
        """
        prompt = self._build_finops_prompt(costs, resources, persona)
        
        return self.chat(
            message=prompt,
            system_prompt="Voce e um consultor FinOps AWS especializado."
        )
