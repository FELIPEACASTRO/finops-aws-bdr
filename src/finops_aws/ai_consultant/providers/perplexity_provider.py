"""
Perplexity Provider - Provedor Perplexity AI

Implementa o BaseAIProvider para Perplexity.
Suporta modelos Sonar com busca online integrada.

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


class PerplexityProvider(BaseAIProvider):
    """
    Provedor Perplexity AI
    
    Usa API Perplexity para chat com busca online integrada.
    Requer PERPLEXITY_API_KEY configurado.
    
    Vantagens:
    - Busca online em tempo real
    - Citacoes de fontes
    - Informacoes atualizadas de precos AWS
    
    Modelos suportados:
    - llama-3.1-sonar-large-128k-online (recomendado)
    - llama-3.1-sonar-small-128k-online
    - llama-3.1-sonar-huge-128k-online
    
    Example:
        ```python
        config = AIProviderConfig.from_env(AIProviderType.PERPLEXITY)
        provider = PerplexityProvider(config)
        
        response = provider.generate_report(costs, resources, PersonaType.DEVOPS)
        print(response.content)
        print("Fontes:", response.sources)
        ```
    """
    
    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.PERPLEXITY
    
    @property
    def available_models(self) -> List[str]:
        return [
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-huge-128k-online"
        ]
    
    @property
    def client(self):
        """Lazy loading do cliente Perplexity (usa API compativel OpenAI)"""
        if self._client is None:
            try:
                from openai import OpenAI
                
                api_key = self.config.api_key or os.environ.get('PERPLEXITY_API_KEY')
                
                if not api_key:
                    raise ValueError("PERPLEXITY_API_KEY nao configurado")
                
                self._client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.perplexity.ai"
                )
                
            except ImportError:
                raise ImportError(
                    "Pacote openai nao instalado. "
                    "Execute: pip install openai"
                )
        
        return self._client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude da conexao com Perplexity
        
        Returns:
            Dict com status
        """
        status = {
            "healthy": False,
            "provider": self.provider_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {}
        }
        
        api_key = self.config.api_key or os.environ.get('PERPLEXITY_API_KEY')
        
        if not api_key:
            status["details"]["error"] = "PERPLEXITY_API_KEY nao configurado"
            return status
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            status["healthy"] = True
            status["details"] = {
                "current_model": self.config.model or "llama-3.1-sonar-large-128k-online",
                "online_search": True
            }
            
        except Exception as e:
            if "Invalid API Key" in str(e):
                status["details"]["error"] = "API Key invalida"
            else:
                status["details"]["error"] = str(e)
        
        return status
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Envia mensagem para Perplexity
        
        Args:
            message: Mensagem do usuario
            system_prompt: Prompt de sistema
            context: Contexto adicional
            
        Returns:
            AIResponse com resposta e citacoes
        """
        model = self.config.model or "llama-3.1-sonar-large-128k-online"
        
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
            
            sources = []
            if hasattr(response, 'citations') and response.citations:
                for citation in response.citations:
                    sources.append({
                        "title": citation.get("title", ""),
                        "url": citation.get("url", ""),
                        "snippet": citation.get("snippet", "")
                    })
            
            return AIResponse(
                content=choice.message.content,
                provider=self.provider_type,
                model=model,
                tokens_used=usage.total_tokens if usage else 0,
                latency_ms=latency,
                sources=sources,
                metadata={
                    "finish_reason": choice.finish_reason,
                    "online_search": True
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Erro Perplexity: {str(e)}")
    
    def generate_report(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType = PersonaType.EXECUTIVE
    ) -> AIResponse:
        """
        Gera relatorio FinOps usando Perplexity
        
        Vantagem: busca online por precos atualizados AWS
        
        Args:
            costs: Dados de custo AWS
            resources: Dados de recursos AWS
            persona: Tipo de persona
            
        Returns:
            AIResponse com relatorio e fontes
        """
        prompt = self._build_finops_prompt(costs, resources, persona)
        
        prompt += """

## Instrucoes Adicionais para Perplexity

Por favor, busque online:
1. Precos atualizados dos servicos AWS mencionados
2. Comparativo com alternativas (Reserved Instances, Savings Plans)
3. Artigos recentes sobre otimizacao AWS
4. Best practices atualizadas do AWS Well-Architected

Cite todas as fontes consultadas."""
        
        system_prompt = """Voce e um consultor FinOps AWS com acesso a informacoes em tempo real.

Use sua capacidade de busca online para:
- Verificar precos AWS atualizados
- Encontrar best practices recentes
- Citar fontes confiaveis (AWS docs, blogs oficiais)

Responda em Portugues do Brasil.
Use Markdown para formatacao.
Sempre cite as fontes consultadas."""
        
        return self.chat(
            message=prompt,
            system_prompt=system_prompt
        )
    
    def search_aws_pricing(self, service: str, region: str = "us-east-1") -> AIResponse:
        """
        Busca precos atualizados de um servico AWS
        
        Args:
            service: Nome do servico (ec2, rds, etc)
            region: Regiao AWS
            
        Returns:
            AIResponse com precos atualizados
        """
        prompt = f"""Busque os precos atualizados do AWS {service.upper()} na regiao {region}.

Inclua:
1. Precos On-Demand por tipo de instancia
2. Precos Reserved Instances (1 ano, 3 anos)
3. Precos Savings Plans
4. Comparativo de economia

Formate como tabela Markdown.
Cite a fonte (AWS Pricing Calculator ou documentacao oficial)."""
        
        return self.chat(
            message=prompt,
            system_prompt="Voce e um especialista em precos AWS. Busque apenas em fontes oficiais AWS."
        )
