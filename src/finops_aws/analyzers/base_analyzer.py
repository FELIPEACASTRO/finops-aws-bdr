"""
Base Analyzer - Classe base abstrata para todos os analyzers

Design Patterns:
- Template Method: Define algoritmo de análise com passos customizáveis
- Strategy: Permite diferentes estratégias de análise

SOLID:
- SRP: Define apenas a estrutura de análise
- OCP: Extensível via herança
- DIP: Depende de abstrações (Protocol)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Protocol, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Priority(str, Enum):
    """Prioridade de recomendação."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Impact(str, Enum):
    """Impacto financeiro."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Recommendation:
    """
    Representa uma recomendação de otimização.
    
    Pythonic: Usa dataclass para reduzir boilerplate
    """
    type: str
    resource_id: str
    title: str
    description: str
    service: str
    priority: Priority = Priority.MEDIUM
    impact: Impact = Impact.MEDIUM
    estimated_savings: float = 0.0
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'resource_id': self.resource_id,
            'resource': self.resource_id,
            'title': self.title,
            'description': self.description,
            'service': self.service,
            'source': self.service,
            'priority': self.priority.value,
            'impact': self.impact.value,
            'savings': self.estimated_savings,
            'action': self.action,
            'details': self.details
        }


@dataclass
class ResourceMetric:
    """Métrica de um recurso AWS."""
    resource_type: str
    count: int
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """
    Resultado da análise de um serviço/categoria.
    
    Aggregates recommendations e métricas de forma consistente.
    """
    analyzer_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recommendations: List[Recommendation] = field(default_factory=list)
    resources: Dict[str, int] = field(default_factory=dict)
    metrics: List[ResourceMetric] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    services_analyzed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analyzer': self.analyzer_name,
            'timestamp': self.timestamp.isoformat(),
            'recommendations': [r.to_dict() for r in self.recommendations],
            'resources': self.resources,
            'services_analyzed': self.services_analyzed,
            'errors_count': len(self.errors)
        }
    
    def merge(self, other: 'AnalysisResult') -> 'AnalysisResult':
        """Combina resultados de múltiplos analyzers."""
        return AnalysisResult(
            analyzer_name=f"{self.analyzer_name}+{other.analyzer_name}",
            recommendations=self.recommendations + other.recommendations,
            resources={**self.resources, **other.resources},
            metrics=self.metrics + other.metrics,
            errors=self.errors + other.errors,
            services_analyzed=self.services_analyzed + other.services_analyzed
        )


class AnalyzerProtocol(Protocol):
    """
    Protocol para analyzers - Duck typing tipado.
    
    Pythonic: Usa Protocol ao invés de ABC para maior flexibilidade
    """
    
    def analyze(self, region: str) -> AnalysisResult:
        """Executa análise na região especificada."""
        ...
    
    @property
    def name(self) -> str:
        """Nome do analyzer."""
        ...


class BaseAnalyzer(ABC):
    """
    Classe base abstrata para analyzers AWS.
    
    Design Pattern: Template Method
    - analyze() define o algoritmo geral
    - Métodos abstratos definem passos específicos
    
    Usage:
        class MyAnalyzer(BaseAnalyzer):
            name = "MyAnalyzer"
            
            def _get_client(self, region):
                return boto3.client('myservice', region_name=region)
                
            def _collect_resources(self, client):
                return client.list_resources()
                
            def _analyze_resources(self, resources, region):
                recommendations = []
                # análise específica
                return recommendations, metrics
    """
    
    name: str = "BaseAnalyzer"
    
    def __init__(self, client_factory: Optional[Callable] = None):
        """
        Args:
            client_factory: Função para criar clientes boto3 (DI)
        """
        self._client_factory = client_factory
        self._logger = logging.getLogger(f"finops.{self.name}")
    
    def analyze(self, region: str) -> AnalysisResult:
        """
        Template Method - define o algoritmo de análise.
        
        1. Cria cliente AWS
        2. Coleta recursos
        3. Analisa recursos
        4. Retorna resultado
        
        Args:
            region: Região AWS para análise
            
        Returns:
            AnalysisResult com recomendações e métricas
        """
        result = AnalysisResult(analyzer_name=self.name)
        
        try:
            clients = self._get_client(region)
            
            if clients is None:
                result.errors.append(f"Não foi possível criar cliente para {self.name}")
                return result
            
            resources = self._collect_resources(clients)
            
            recommendations, metrics = self._analyze_resources(resources, region)
            
            result.recommendations = recommendations
            result.resources = metrics
            result.services_analyzed = self._get_services_list()
            
            self._logger.info(
                f"Análise concluída: {len(recommendations)} recomendações, "
                f"{len(metrics)} recursos"
            )
            
        except Exception as e:
            error_msg = f"Erro em {self.name}: {str(e)[:200]}"
            result.errors.append(error_msg)
            self._logger.warning(error_msg)
        
        return result
    
    @abstractmethod
    def _get_client(self, region: str) -> Any:
        """
        Cria cliente AWS para o serviço.
        
        Args:
            region: Região AWS
            
        Returns:
            Cliente boto3
        """
        pass
    
    @abstractmethod
    def _collect_resources(self, clients: Any) -> Dict[str, Any]:
        """
        Coleta recursos do serviço.
        
        Args:
            clients: Cliente(s) boto3
            
        Returns:
            Dicionário com recursos coletados
        """
        pass
    
    @abstractmethod
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """
        Analisa recursos e gera recomendações.
        
        Args:
            resources: Recursos coletados
            region: Região AWS
            
        Returns:
            Tuple (recomendações, métricas)
        """
        pass
    
    def _get_services_list(self) -> List[str]:
        """Retorna lista de serviços analisados."""
        return [self.name]
    
    def _create_recommendation(
        self,
        rec_type: str,
        resource_id: str,
        description: str,
        service: str,
        priority: Priority = Priority.MEDIUM,
        savings: float = 0.0
    ) -> Recommendation:
        """
        Factory method para criar recomendações de forma consistente.
        """
        return Recommendation(
            type=rec_type,
            resource_id=resource_id,
            title=description,
            description=description,
            service=service,
            priority=priority,
            estimated_savings=savings
        )
