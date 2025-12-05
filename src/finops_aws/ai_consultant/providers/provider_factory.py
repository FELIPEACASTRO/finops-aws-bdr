"""
AI Provider Factory - Factory e Registry para Provedores de IA

Implementa os patterns Factory e Registry do GoF para
criar e gerenciar provedores de IA de forma dinamica.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from typing import Dict, Type, Optional, List
from .base_provider import BaseAIProvider, AIProviderConfig, AIProviderType


class AIProviderRegistry:
    """
    Registry Singleton para Provedores de IA
    
    Mantem catalogo central de todos os provedores disponiveis.
    Permite registro dinamico de novos provedores.
    
    Example:
        ```python
        registry = AIProviderRegistry()
        registry.register("custom", CustomProvider)
        
        provider_class = registry.get("openai")
        ```
    """
    
    _instance = None
    _providers: Dict[str, Type[BaseAIProvider]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._providers = {}
        return cls._instance
    
    def register(self, name: str, provider_class: Type[BaseAIProvider]) -> None:
        """
        Registra um provedor no catalogo
        
        Args:
            name: Nome identificador do provedor
            provider_class: Classe do provedor
        """
        self._providers[name.lower()] = provider_class
    
    def get(self, name: str) -> Optional[Type[BaseAIProvider]]:
        """
        Obtem classe do provedor pelo nome
        
        Args:
            name: Nome do provedor
            
        Returns:
            Classe do provedor ou None
        """
        return self._providers.get(name.lower())
    
    def list_all(self) -> List[str]:
        """
        Lista todos os provedores registrados
        
        Returns:
            Lista de nomes de provedores
        """
        return list(self._providers.keys())
    
    def is_registered(self, name: str) -> bool:
        """
        Verifica se provedor esta registrado
        
        Args:
            name: Nome do provedor
            
        Returns:
            True se registrado
        """
        return name.lower() in self._providers


class AIProviderFactory:
    """
    Factory para criar Provedores de IA
    
    Usa o Registry para criar instancias de provedores
    de forma desacoplada.
    
    Example:
        ```python
        # Criar provedor especifico
        provider = AIProviderFactory.create("openai")
        
        # Criar com configuracao customizada
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            model="gpt-4o",
            temperature=0.5
        )
        provider = AIProviderFactory.create("openai", config)
        
        # Listar provedores disponiveis
        providers = AIProviderFactory.list_providers()
        ```
    """
    
    _registry = None
    _initialized = False
    
    @classmethod
    def _ensure_initialized(cls):
        """Garante que os provedores padrao estao registrados"""
        if cls._initialized:
            return
            
        cls._registry = AIProviderRegistry()
        
        from .amazon_q_provider import AmazonQProvider
        from .openai_provider import OpenAIProvider
        from .gemini_provider import GeminiProvider
        from .perplexity_provider import PerplexityProvider
        
        cls._registry.register("amazon_q", AmazonQProvider)
        cls._registry.register("amazonq", AmazonQProvider)
        cls._registry.register("q_business", AmazonQProvider)
        
        cls._registry.register("openai", OpenAIProvider)
        cls._registry.register("chatgpt", OpenAIProvider)
        cls._registry.register("gpt", OpenAIProvider)
        
        cls._registry.register("gemini", GeminiProvider)
        cls._registry.register("google", GeminiProvider)
        
        cls._registry.register("perplexity", PerplexityProvider)
        
        cls._initialized = True
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        config: Optional[AIProviderConfig] = None
    ) -> Optional[BaseAIProvider]:
        """
        Cria instancia de um provedor de IA
        
        Args:
            provider_name: Nome do provedor (openai, gemini, etc)
            config: Configuracao opcional
            
        Returns:
            Instancia do provedor ou None
            
        Example:
            ```python
            # Criar OpenAI com config default
            openai = AIProviderFactory.create("openai")
            
            # Criar Gemini com modelo especifico
            config = AIProviderConfig(
                provider_type=AIProviderType.GEMINI,
                model="gemini-2.5-pro"
            )
            gemini = AIProviderFactory.create("gemini", config)
            ```
        """
        cls._ensure_initialized()
        
        provider_class = cls._registry.get(provider_name)
        
        if provider_class is None:
            return None
        
        if config is None:
            provider_type = cls._get_provider_type(provider_name)
            config = AIProviderConfig.from_env(provider_type)
        
        return provider_class(config)
    
    @classmethod
    def create_all_available(cls) -> Dict[str, BaseAIProvider]:
        """
        Cria instancias de todos os provedores configurados
        
        Returns:
            Dict com provedores ativos
            
        Example:
            ```python
            providers = AIProviderFactory.create_all_available()
            for name, provider in providers.items():
                print(f"{name}: {provider.health_check()}")
            ```
        """
        cls._ensure_initialized()
        
        available = {}
        
        for name in ["amazon_q", "openai", "gemini", "perplexity"]:
            try:
                provider = cls.create(name)
                if provider:
                    health = provider.health_check()
                    if health.get("healthy", False):
                        available[name] = provider
            except Exception:
                pass
        
        return available
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """
        Lista todos os provedores registrados
        
        Returns:
            Lista de nomes de provedores
        """
        cls._ensure_initialized()
        return cls._registry.list_all()
    
    @classmethod
    def get_provider_info(cls, provider_name: str) -> Dict[str, any]:
        """
        Obtem informacoes sobre um provedor
        
        Args:
            provider_name: Nome do provedor
            
        Returns:
            Dict com informacoes do provedor
        """
        cls._ensure_initialized()
        
        info = {
            "amazon_q": {
                "name": "Amazon Q Business",
                "vendor": "AWS",
                "requires_api_key": False,
                "requires_aws_credentials": True,
                "models": ["q-business"],
                "features": ["RAG", "Knowledge Base", "Chat"],
                "pricing": "Por uso AWS"
            },
            "openai": {
                "name": "OpenAI ChatGPT",
                "vendor": "OpenAI",
                "requires_api_key": True,
                "requires_aws_credentials": False,
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "features": ["Chat", "Function Calling", "Vision"],
                "pricing": "Por token"
            },
            "gemini": {
                "name": "Google Gemini",
                "vendor": "Google",
                "requires_api_key": True,
                "requires_aws_credentials": False,
                "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro"],
                "features": ["Chat", "Multimodal", "Long Context"],
                "pricing": "Por token"
            },
            "perplexity": {
                "name": "Perplexity AI",
                "vendor": "Perplexity",
                "requires_api_key": True,
                "requires_aws_credentials": False,
                "models": ["sonar", "sonar-pro", "sonar-reasoning"],
                "features": ["Chat", "Web Search", "Citations"],
                "pricing": "Por requisicao"
            }
        }
        
        return info.get(provider_name.lower(), {})
    
    @classmethod
    def _get_provider_type(cls, name: str) -> AIProviderType:
        """Mapeia nome para tipo de provedor"""
        mapping = {
            "amazon_q": AIProviderType.AMAZON_Q,
            "amazonq": AIProviderType.AMAZON_Q,
            "q_business": AIProviderType.AMAZON_Q,
            "openai": AIProviderType.OPENAI,
            "chatgpt": AIProviderType.OPENAI,
            "gpt": AIProviderType.OPENAI,
            "gemini": AIProviderType.GEMINI,
            "google": AIProviderType.GEMINI,
            "perplexity": AIProviderType.PERPLEXITY
        }
        return mapping.get(name.lower(), AIProviderType.OPENAI)
