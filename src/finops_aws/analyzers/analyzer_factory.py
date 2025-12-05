"""
Analyzer Factory - Criação e registro de analyzers

Design Patterns:
- Factory Pattern: Cria analyzers apropriados
- Registry Pattern: Mantém registro de analyzers disponíveis
- Singleton: AnalyzerRegistry única

SOLID:
- SRP: Apenas criação de analyzers
- OCP: Novos analyzers via registro
"""
from typing import Dict, List, Type, Optional, Callable
from .base_analyzer import BaseAnalyzer, AnalysisResult
import logging

logger = logging.getLogger(__name__)


class AnalyzerRegistry:
    """
    Registry Pattern - mantém registro de analyzers disponíveis.
    
    Usage:
        registry = AnalyzerRegistry()
        registry.register('compute', ComputeAnalyzer)
        analyzer = registry.get('compute')
    """
    
    _instance: Optional['AnalyzerRegistry'] = None
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    
    def __new__(cls) -> 'AnalyzerRegistry':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._analyzers = {}
        return cls._instance
    
    def register(self, name: str, analyzer_class: Type[BaseAnalyzer]) -> None:
        """
        Registra um analyzer.
        
        Args:
            name: Nome identificador
            analyzer_class: Classe do analyzer
        """
        self._analyzers[name.lower()] = analyzer_class
        logger.debug(f"Analyzer registrado: {name}")
    
    def get(self, name: str) -> Optional[Type[BaseAnalyzer]]:
        """
        Obtém classe de analyzer pelo nome.
        
        Args:
            name: Nome do analyzer
            
        Returns:
            Classe do analyzer ou None
        """
        return self._analyzers.get(name.lower())
    
    def list_all(self) -> List[str]:
        """Lista todos os analyzers registrados."""
        return list(self._analyzers.keys())
    
    def clear(self) -> None:
        """Limpa registro (útil para testes)."""
        self._analyzers.clear()


class AnalyzerFactory:
    """
    Factory para criar e executar analyzers.
    
    Design Pattern: Factory Pattern
    
    Usage:
        factory = AnalyzerFactory()
        result = factory.analyze_all(region='us-east-1')
    """
    
    def __init__(self, client_factory: Optional[Callable] = None):
        """
        Args:
            client_factory: Função para criar clientes boto3 (DI)
        """
        self._client_factory = client_factory
        self._registry = AnalyzerRegistry()
        self._register_default_analyzers()
    
    def _register_default_analyzers(self) -> None:
        """Registra analyzers padrão."""
        from .compute_analyzer import ComputeAnalyzer
        from .storage_analyzer import StorageAnalyzer
        from .database_analyzer import DatabaseAnalyzer
        from .network_analyzer import NetworkAnalyzer
        from .security_analyzer import SecurityAnalyzer
        from .analytics_analyzer import AnalyticsAnalyzer
        
        self._registry.register('compute', ComputeAnalyzer)
        self._registry.register('storage', StorageAnalyzer)
        self._registry.register('database', DatabaseAnalyzer)
        self._registry.register('network', NetworkAnalyzer)
        self._registry.register('security', SecurityAnalyzer)
        self._registry.register('analytics', AnalyticsAnalyzer)
    
    def create(self, analyzer_name: str) -> Optional[BaseAnalyzer]:
        """
        Cria instância de analyzer.
        
        Args:
            analyzer_name: Nome do analyzer
            
        Returns:
            Instância do analyzer ou None
        """
        analyzer_class = self._registry.get(analyzer_name)
        if analyzer_class:
            return analyzer_class(self._client_factory)
        return None
    
    def get_analyzer(self, analyzer_name: str) -> Optional[BaseAnalyzer]:
        """
        Alias para create() - obtém instância de analyzer.
        
        Args:
            analyzer_name: Nome do analyzer
            
        Returns:
            Instância do analyzer ou None
        """
        return self.create(analyzer_name)
    
    def analyze(self, analyzer_name: str, region: str) -> AnalysisResult:
        """
        Executa um analyzer específico.
        
        Args:
            analyzer_name: Nome do analyzer
            region: Região AWS
            
        Returns:
            Resultado da análise
        """
        analyzer = self.create(analyzer_name)
        if analyzer:
            return analyzer.analyze(region)
        return AnalysisResult(analyzer_name=analyzer_name, errors=[f"Analyzer '{analyzer_name}' não encontrado"])
    
    def analyze_all(self, region: str) -> AnalysisResult:
        """
        Executa todos os analyzers registrados.
        
        Args:
            region: Região AWS
            
        Returns:
            Resultado combinado de todos os analyzers
        """
        combined = AnalysisResult(analyzer_name="AllAnalyzers")
        
        for name in self._registry.list_all():
            result = self.analyze(name, region)
            combined = combined.merge(result)
        
        return combined
    
    def analyze_categories(
        self, 
        categories: List[str], 
        region: str
    ) -> AnalysisResult:
        """
        Executa analyzers de categorias específicas.
        
        Args:
            categories: Lista de categorias ('compute', 'storage', etc.)
            region: Região AWS
            
        Returns:
            Resultado combinado
        """
        combined = AnalysisResult(analyzer_name="SelectedAnalyzers")
        
        for category in categories:
            result = self.analyze(category, region)
            combined = combined.merge(result)
        
        return combined
