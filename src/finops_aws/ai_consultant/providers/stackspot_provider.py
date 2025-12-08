"""
StackSpot AI Provider - Provedor StackSpot AI

Implementa o BaseAIProvider para StackSpot AI.
Usa API OAuth 2.0 Client Credentials para autenticacao.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import os
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .base_provider import (
    BaseAIProvider, 
    AIProviderConfig, 
    AIProviderType,
    AIResponse,
    PersonaType
)


class StackSpotProvider(BaseAIProvider):
    """
    Provedor StackSpot AI
    
    Usa API StackSpot para consultas IA com Knowledge Sources.
    Requer STACKSPOT_CLIENT_ID, STACKSPOT_CLIENT_SECRET e STACKSPOT_REALM.
    
    Vantagens:
    - Integracao com Knowledge Sources customizadas
    - Contexto corporativo personalizado
    - Agents especializados
    
    Authentication:
    - OAuth 2.0 Client Credentials Flow
    - Token automaticamente renovado
    
    Example:
        ```python
        config = AIProviderConfig.from_env(AIProviderType.STACKSPOT)
        provider = StackSpotProvider(config)
        
        response = provider.generate_report(costs, resources, PersonaType.EXECUTIVE)
        print(response.content)
        ```
    """
    
    _token_cache: Dict[str, Any] = {}
    
    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.STACKSPOT
    
    @property
    def available_models(self) -> List[str]:
        return [
            "stackspot-ai",
            "stackspot-agent"
        ]
    
    def _get_credentials(self) -> Dict[str, str]:
        """Obtem credenciais do ambiente"""
        client_id = self.config.extra_config.get('client_id') or os.environ.get('STACKSPOT_CLIENT_ID')
        client_secret = self.config.extra_config.get('client_secret') or os.environ.get('STACKSPOT_CLIENT_SECRET')
        realm = self.config.extra_config.get('realm') or os.environ.get('STACKSPOT_REALM')
        
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'realm': realm
        }
    
    def _get_access_token(self) -> str:
        """
        Obtem access token via OAuth 2.0 Client Credentials
        
        Returns:
            Access token JWT
        """
        creds = self._get_credentials()
        
        if not all([creds['client_id'], creds['client_secret'], creds['realm']]):
            raise ValueError("Credenciais StackSpot nao configuradas (CLIENT_ID, CLIENT_SECRET, REALM)")
        
        cache_key = f"{creds['realm']}_{creds['client_id']}"
        
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if datetime.utcnow() < cached['expires_at']:
                return cached['token']
        
        token_url = f"https://idm.stackspot.com/{creds['realm']}/oidc/oauth/token"
        
        response = requests.post(
            token_url,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                'grant_type': 'client_credentials',
                'client_id': creds['client_id'],
                'client_secret': creds['client_secret']
            },
            timeout=30
        )
        
        if response.status_code != 200:
            error_detail = response.text[:200] if response.text else "Unknown error"
            raise RuntimeError(f"Erro ao obter token StackSpot: {response.status_code} - {error_detail}")
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)
        
        self._token_cache[cache_key] = {
            'token': access_token,
            'expires_at': datetime.utcnow() + timedelta(seconds=expires_in - 60)
        }
        
        return access_token
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude da conexao com StackSpot
        
        Returns:
            Dict com status
        """
        status = {
            "healthy": False,
            "provider": "stackspot",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {}
        }
        
        creds = self._get_credentials()
        
        if not creds['client_id']:
            status["details"]["error"] = "STACKSPOT_CLIENT_ID nao configurado"
            return status
        
        if not creds['client_secret']:
            status["details"]["error"] = "STACKSPOT_CLIENT_SECRET nao configurado"
            return status
            
        if not creds['realm']:
            status["details"]["error"] = "STACKSPOT_REALM nao configurado"
            return status
        
        try:
            token = self._get_access_token()
            
            if token:
                status["healthy"] = True
                status["details"] = {
                    "realm": creds['realm'],
                    "authenticated": True,
                    "current_model": "stackspot-ai"
                }
            
        except requests.exceptions.Timeout:
            status["details"]["error"] = "Timeout na conexao"
        except requests.exceptions.ConnectionError:
            status["details"]["error"] = "Erro de conexao com StackSpot"
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                status["details"]["error"] = "Credenciais invalidas"
            elif "403" in error_msg or "Forbidden" in error_msg:
                status["details"]["error"] = "Acesso negado"
            else:
                status["details"]["error"] = error_msg[:100]
        
        return status
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Envia mensagem para StackSpot AI
        
        Args:
            message: Mensagem do usuario
            system_prompt: Prompt de sistema
            context: Contexto adicional
            
        Returns:
            AIResponse com resposta
        """
        token = self._get_access_token()
        
        full_message = ""
        if system_prompt:
            full_message = f"{system_prompt}\n\n"
        
        full_message += message
        
        if context:
            import json
            full_message += f"\n\n## Contexto\n```json\n{json.dumps(context, indent=2, default=str)}\n```"
        
        start_time = time.time()
        
        api_url = "https://genai-code-buddy-api.stackspot.com/v1/quick-commands/create-and-execute"
        
        response = requests.post(
            api_url,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                'input_data': full_message,
                'conversation_id': None
            },
            timeout=120
        )
        
        latency = int((time.time() - start_time) * 1000)
        
        if response.status_code not in [200, 201]:
            error_detail = response.text[:200] if response.text else "Unknown error"
            raise RuntimeError(f"Erro StackSpot API: {response.status_code} - {error_detail}")
        
        result = response.json()
        
        content = ""
        if isinstance(result, dict):
            content = result.get('result', result.get('answer', result.get('response', str(result))))
        else:
            content = str(result)
        
        return AIResponse(
            content=content,
            provider=self.provider_type,
            model="stackspot-ai",
            tokens_used=0,
            latency_ms=latency,
            metadata={
                "realm": self._get_credentials()['realm']
            }
        )
    
    def generate_report(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType = PersonaType.EXECUTIVE
    ) -> AIResponse:
        """
        Gera relatorio FinOps usando StackSpot AI
        
        Args:
            costs: Dados de custo AWS
            resources: Dados de recursos AWS
            persona: Tipo de persona
            
        Returns:
            AIResponse com relatorio
        """
        prompt = self._build_finops_prompt(costs, resources, persona)
        
        prompt += """

## Instrucoes OBRIGATORIAS

IMPORTANTE: Responda DIRETAMENTE com o relatorio completo em Markdown.
NAO diga "vou buscar" ou "deixe-me pesquisar" - va direto ao conteudo.

Gere um relatorio detalhado de FinOps AWS incluindo:
1. Resumo executivo com principais custos
2. Oportunidades de otimizacao ordenadas por impacto
3. Recomendacoes de Savings Plans e Reserved Instances
4. Proximos passos com prazos sugeridos"""
        
        system_prompt = """Voce e um consultor FinOps AWS senior especializado em otimizacao de custos.

REGRAS OBRIGATORIAS:
1. NUNCA diga "vou buscar" ou "deixe-me pesquisar" - responda DIRETAMENTE
2. Gere o relatorio COMPLETO imediatamente em Markdown
3. Inclua todas as recomendacoes de otimizacao
4. Responda em Portugues do Brasil
5. Formate com headers, tabelas e listas

Comece o relatorio com "# Relatorio" e va direto ao conteudo."""
        
        return self.chat(
            message=prompt,
            system_prompt=system_prompt
        )
