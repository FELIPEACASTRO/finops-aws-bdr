"""
Logger Interface
Implementa SOLID - Dependency Inversion Principle
Complexidade: O(1) para todas as operações
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """
    Enum para níveis de log
    
    SOLID: Open/Closed - fácil de estender
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ILogger(ABC):
    """
    Interface para logging
    
    SOLID Principles:
    - Dependency Inversion: Interface abstrata
    - Interface Segregation: Métodos específicos
    - Single Responsibility: Apenas logging
    
    Design Pattern: Strategy Pattern (para diferentes implementações)
    Complexidade: O(1) para todas as operações
    """
    
    @abstractmethod
    async def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log de debug
        
        Args:
            message: Mensagem de log
            extra: Dados adicionais
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    async def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log de informação
        
        Args:
            message: Mensagem de log
            extra: Dados adicionais
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    async def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log de aviso
        
        Args:
            message: Mensagem de log
            extra: Dados adicionais
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    async def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None) -> None:
        """
        Log de erro
        
        Args:
            message: Mensagem de log
            extra: Dados adicionais
            exception: Exceção associada
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    async def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None) -> None:
        """
        Log crítico
        
        Args:
            message: Mensagem de log
            extra: Dados adicionais
            exception: Exceção associada
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """
        Define nível de log
        
        Args:
            level: Nível de log
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    def get_level(self) -> LogLevel:
        """
        Obtém nível de log atual
        
        Returns:
            Nível de log
            
        Complexidade: O(1)
        """
        pass


class IMetricsLogger(ABC):
    """
    Interface específica para logging de métricas
    
    SOLID: Interface Segregation - separada do logger básico
    Microservices Pattern: Observability
    """
    
    @abstractmethod
    async def log_performance_metric(self, operation: str, duration_seconds: float, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log de métrica de performance
        
        Args:
            operation: Nome da operação
            duration_seconds: Duração em segundos
            extra: Dados adicionais
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    async def log_business_metric(self, metric_name: str, value: float, unit: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log de métrica de negócio
        
        Args:
            metric_name: Nome da métrica
            value: Valor da métrica
            unit: Unidade de medida
            extra: Dados adicionais
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    async def log_api_call(self, service: str, operation: str, duration_seconds: float, success: bool, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log de chamada de API
        
        Args:
            service: Nome do serviço
            operation: Nome da operação
            duration_seconds: Duração da chamada
            success: Se a chamada foi bem-sucedida
            extra: Dados adicionais
            
        Complexidade: O(1)
        """
        pass


class IStructuredLogger(ILogger, IMetricsLogger):
    """
    Interface combinada para logging estruturado
    
    SOLID: Interface Segregation - combina interfaces relacionadas
    Design Pattern: Composite Interface
    """
    
    @abstractmethod
    async def log_with_context(self, level: LogLevel, message: str, context: Dict[str, Any]) -> None:
        """
        Log com contexto estruturado
        
        Args:
            level: Nível de log
            message: Mensagem
            context: Contexto estruturado
            
        Complexidade: O(1)
        """
        pass
    
    @abstractmethod
    def create_child_logger(self, context: Dict[str, Any]) -> 'IStructuredLogger':
        """
        Cria logger filho com contexto adicional
        
        Args:
            context: Contexto adicional
            
        Returns:
            Logger filho
            
        Design Pattern: Factory Method
        Complexidade: O(1)
        """
        pass
