"""
AI Consultant - Modulo de Consultoria Financeira Automatizada

Este modulo integra o FinOps AWS com multiplos provedores de IA:
- Amazon Q Business (AWS nativo)
- OpenAI ChatGPT
- Google Gemini
- Perplexity AI

Componentes:
- providers: Provedores de IA (Strategy Pattern)
- q_business: Cliente e servicos Amazon Q Business
- prompts: Templates e builders de prompts
- processors: Formatacao e parsing de dados
- knowledge: Base de conhecimento e documentos
- delivery: Canais de entrega (email, Slack, PDF)

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from .q_business import QBusinessClient, QBusinessConfig, QBusinessChat
from .prompts import PromptBuilder, PromptPersona
from .processors import DataFormatter, ResponseParser, ReportStructurer

from .providers import (
    BaseAIProvider,
    AIProviderConfig,
    AIResponse,
    AIProviderFactory,
    AIProviderRegistry,
    AmazonQProvider,
    OpenAIProvider,
    GeminiProvider,
    PerplexityProvider
)

__all__ = [
    'QBusinessClient',
    'QBusinessConfig', 
    'QBusinessChat',
    'PromptBuilder',
    'PromptPersona',
    'DataFormatter',
    'ResponseParser',
    'ReportStructurer',
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

__version__ = "2.0.0"
