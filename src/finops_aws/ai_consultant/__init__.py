"""
AI Consultant - Módulo de Consultoria Financeira Automatizada com Amazon Q

Este módulo integra o FinOps AWS com Amazon Q Business para gerar
relatórios inteligentes de otimização de custos AWS.

Componentes:
- q_business: Cliente e serviços Amazon Q Business
- prompts: Templates e builders de prompts
- processors: Formatação e parsing de dados
- knowledge: Base de conhecimento e documentos
- delivery: Canais de entrega (email, Slack, PDF)

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from .q_business import QBusinessClient, QBusinessConfig
from .prompts import PromptBuilder, PromptPersona
from .processors import DataFormatter, ResponseParser, ReportStructurer

__all__ = [
    'QBusinessClient',
    'QBusinessConfig', 
    'PromptBuilder',
    'PromptPersona',
    'DataFormatter',
    'ResponseParser',
    'ReportStructurer'
]

__version__ = "1.0.0"
