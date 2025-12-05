"""
FinOps AWS - Analyzers Module

Design Patterns aplicados:
- Strategy Pattern: Cada analyzer implementa sua estratégia de análise
- Factory Pattern: ServiceAnalyzerFactory cria analyzers apropriados
- Template Method: BaseAnalyzer define estrutura comum

SOLID:
- SRP: Cada analyzer tem responsabilidade única (um serviço ou categoria)
- OCP: Novos analyzers podem ser adicionados sem modificar existentes
- DIP: Dependem de abstrações (Protocol)
"""

from .base_analyzer import (
    BaseAnalyzer,
    AnalyzerProtocol,
    AnalysisResult,
    Recommendation,
    ResourceMetric
)
from .analyzer_factory import (
    AnalyzerFactory,
    AnalyzerRegistry
)
from .compute_analyzer import ComputeAnalyzer
from .storage_analyzer import StorageAnalyzer
from .database_analyzer import DatabaseAnalyzer
from .network_analyzer import NetworkAnalyzer
from .security_analyzer import SecurityAnalyzer
from .analytics_analyzer import AnalyticsAnalyzer

__all__ = [
    'BaseAnalyzer',
    'AnalyzerProtocol',
    'AnalysisResult',
    'Recommendation',
    'ResourceMetric',
    'AnalyzerFactory',
    'AnalyzerRegistry',
    'ComputeAnalyzer',
    'StorageAnalyzer',
    'DatabaseAnalyzer',
    'NetworkAnalyzer',
    'SecurityAnalyzer',
    'AnalyticsAnalyzer',
]
