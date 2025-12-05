"""
Google Gemini Provider - Provedor Gemini

Implementa o BaseAIProvider para Google Gemini.
Suporta Gemini Pro e Flash.

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


class GeminiProvider(BaseAIProvider):
    """
    Provedor Google Gemini
    
    Usa API Gemini para chat e analise FinOps.
    Requer GEMINI_API_KEY configurado.
    
    Modelos suportados:
    - gemini-2.5-pro (recomendado para analises complexas)
    - gemini-2.5-flash (rapido e economico)
    - gemini-1.5-pro
    
    Example:
        ```python
        config = AIProviderConfig.from_env(AIProviderType.GEMINI)
        provider = GeminiProvider(config)
        
        response = provider.generate_report(costs, resources, PersonaType.ANALYST)
        print(response.content)
        ```
    """
    
    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.GEMINI
    
    @property
    def available_models(self) -> List[str]:
        return [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
    
    @property
    def client(self):
        """Lazy loading do cliente Gemini"""
        if self._client is None:
            try:
                import google.generativeai as genai
                
                api_key = self.config.api_key or os.environ.get('GEMINI_API_KEY')
                
                if not api_key:
                    raise ValueError("GEMINI_API_KEY nao configurado")
                
                genai.configure(api_key=api_key)
                
                model_name = self.config.model or "gemini-2.5-flash"
                self._client = genai.GenerativeModel(model_name)
                
            except ImportError:
                raise ImportError(
                    "Pacote google-generativeai nao instalado. "
                    "Execute: pip install google-generativeai"
                )
        
        return self._client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude da conexao com Gemini
        
        Returns:
            Dict com status
        """
        status = {
            "healthy": False,
            "provider": self.provider_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {}
        }
        
        api_key = self.config.api_key or os.environ.get('GEMINI_API_KEY')
        
        if not api_key:
            status["details"]["error"] = "GEMINI_API_KEY nao configurado"
            return status
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            models = genai.list_models()
            gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
            
            status["healthy"] = True
            status["details"] = {
                "models_available": len(gemini_models),
                "current_model": self.config.model or "gemini-2.5-flash"
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
        Envia mensagem para Gemini
        
        Args:
            message: Mensagem do usuario
            system_prompt: Prompt de sistema
            context: Contexto adicional
            
        Returns:
            AIResponse com resposta
        """
        full_prompt = ""
        
        if system_prompt:
            full_prompt = f"## Instrucoes do Sistema\n\n{system_prompt}\n\n"
        
        full_prompt += f"## Solicitacao\n\n{message}"
        
        if context:
            import json
            full_prompt += f"\n\n## Contexto\n```json\n{json.dumps(context, indent=2, default=str)}\n```"
        
        start_time = time.time()
        
        try:
            generation_config = {
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens
            }
            
            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            latency = int((time.time() - start_time) * 1000)
            
            tokens_used = 0
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                tokens_used = getattr(usage, 'total_token_count', 0)
            
            return AIResponse(
                content=response.text,
                provider=self.provider_type,
                model=self.config.model or "gemini-2.5-flash",
                tokens_used=tokens_used,
                latency_ms=latency,
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Erro Gemini: {str(e)}")
    
    def generate_report(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType = PersonaType.EXECUTIVE
    ) -> AIResponse:
        """
        Gera relatorio FinOps usando Gemini
        
        Args:
            costs: Dados de custo AWS
            resources: Dados de recursos AWS
            persona: Tipo de persona
            
        Returns:
            AIResponse com relatorio
        """
        prompt = self._build_finops_prompt(costs, resources, persona)
        
        system_prompt = """Voce e um consultor FinOps AWS senior com expertise em:
- Cloud Financial Management
- AWS Cost Optimization
- Reserved Instances e Savings Plans
- Analise de recursos e rightsizing

Regras:
- Responda SEMPRE em Portugues do Brasil
- Use formatacao Markdown
- Priorize recomendacoes por impacto financeiro
- Seja preciso com valores monetarios"""
        
        return self.chat(
            message=prompt,
            system_prompt=system_prompt
        )
