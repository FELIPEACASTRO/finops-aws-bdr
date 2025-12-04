"""
Knowledge Base Module

Gerenciamento de base de conhecimento para Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from .indexer import KnowledgeIndexer
from .sync_manager import SyncManager

__all__ = [
    'KnowledgeIndexer',
    'SyncManager'
]
