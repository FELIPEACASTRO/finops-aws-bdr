"""
OpenAI Provider - Provedor ChatGPT

Implementa o BaseAIProvider para OpenAI GPT.
Suporta GPT-4o, GPT-4 Turbo e GPT-3.5.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_provider import (
    BaseAIProvider, 
    AIProviderConfig, 
    AIProviderType,
    AIResponse,
    PersonaType
)


class OpenAIProvider(BaseAIProvider):
    """
    Provedor OpenAI ChatGPT
    
    Usa API OpenAI para chat e analise FinOps.
    Requer OPENAI_API_KEY configurado.
    
    Modelos suportados:
    - gpt-4o (recomendado)
    - gpt-4o-mini
    - gpt-4-turbo
    - gpt-3.5-turbo
    
    Example:
        ```python
        config = AIProviderConfig.from_env(AIProviderType.OPENAI)
        provider = OpenAIProvider(config)
        
        response = provider.generate_report(costs, resources, PersonaType.CTO)
        print(response.content)
        ```
    """
    
    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.OPENAI
    
    @property
    def available_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
    
    @property
    def client(self):
        """Lazy loading do cliente OpenAI"""
        if self._client is None:
            try:
                from openai import OpenAI
                
                api_key = self.config.api_key or os.environ.get('OPENAI_API_KEY')
                
                if not api_key:
                    raise ValueError("OPENAI_API_KEY nao configurado")
                
                self._client = OpenAI(api_key=api_key)
                
            except ImportError:
                raise ImportError(
                    "Pacote openai nao instalado. "
                    "Execute: pip install openai"
                )
        
        return self._client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude da conexao com OpenAI
        
        Returns:
            Dict com status
        """
        status = {
            "healthy": False,
            "provider": self.provider_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {}
        }
        
        api_key = self.config.api_key or os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            status["details"]["error"] = "OPENAI_API_KEY nao configurado"
            return status
        
        try:
            models = self.client.models.list()
            
            available = [m.id for m in models.data if 'gpt' in m.id.lower()]
            
            status["healthy"] = True
            status["details"] = {
                "models_available": len(available),
                "current_model": self.config.model or "gpt-4o"
            }
            
        except Exception as e:
            status["details"]["error"] = str(e)
        
        return status
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Envia mensagem para OpenAI
        
        Args:
            message: Mensagem do usuario
            system_prompt: Prompt de sistema
            context: Contexto adicional
            
        Returns:
            AIResponse com resposta
        """
        model = self.config.model or "gpt-4o"
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        user_content = message
        if context:
            import json
            user_content += f"\n\n## Contexto\n```json\n{json.dumps(context, indent=2, default=str)}\n```"
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            latency = int((time.time() - start_time) * 1000)
            
            choice = response.choices[0]
            usage = response.usage
            
            return AIResponse(
                content=choice.message.content,
                provider=self.provider_type,
                model=model,
                tokens_used=usage.total_tokens if usage else 0,
                latency_ms=latency,
                metadata={
                    "finish_reason": choice.finish_reason,
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Erro OpenAI: {str(e)}")
    
    def generate_report(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType = PersonaType.EXECUTIVE
    ) -> AIResponse:
        """
        Gera relatorio FinOps usando ChatGPT
        
        Args:
            costs: Dados de custo AWS
            resources: Dados de recursos AWS
            persona: Tipo de persona
            
        Returns:
            AIResponse com relatorio
        """
        prompt = self._build_finops_prompt(costs, resources, persona)
        
        system_prompt = """Voce e um consultor FinOps AWS senior especializado em:
- Otimizacao de custos cloud
- AWS Well-Architected Framework
- Reserved Instances e Savings Plans
- Rightsizing e automacao

Responda sempre em Portugues do Brasil.
Use Markdown para formatacao.
Priorize recomendacoes por impacto financeiro."""
        
        return self.chat(
            message=prompt,
            system_prompt=system_prompt
        )
