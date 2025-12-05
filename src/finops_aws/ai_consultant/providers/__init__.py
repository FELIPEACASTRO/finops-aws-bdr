"""
AI Providers - Modulo de Provedores de IA para FinOps AWS

Este modulo implementa o Strategy Pattern para suportar multiplas IAs:
- Amazon Q Business (AWS nativo)
- OpenAI (ChatGPT)
- Google Gemini
- Perplexity

Cada provedor implementa a mesma interface, permitindo troca transparente.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from .base_provider import BaseAIProvider, AIProviderConfig, AIResponse
from .provider_factory import AIProviderFactory, AIProviderRegistry
from .amazon_q_provider import AmazonQProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .perplexity_provider import PerplexityProvider

__all__ = [
    'BaseAIProvider',
    'AIProviderConfig',
    'AIResponse',
    'AIProviderFactory',
    'AIProviderRegistry',
    'AmazonQProvider',
    'OpenAIProvider',
    'GeminiProvider',
    'PerplexityProvider'
]

__version__ = "1.0.0"
