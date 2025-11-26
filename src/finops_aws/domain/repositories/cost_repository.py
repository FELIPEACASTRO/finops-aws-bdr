"""
Domain Repository Interface: Cost Repository
Implementa DDD + SOLID (Dependency Inversion Principle)
Complexidade: O(1) para interfaces, O(n) para implementações
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from ..entities.cost_entity import CostEntity
from ..value_objects.service_name import ServiceName
from ..value_objects.time_period import TimePeriod
from ..value_objects.money import Money


class ICostRepository(ABC):
    """
    Interface do repositório de custos
    
    SOLID Principles:
    - Dependency Inversion: Interface abstrata
    - Interface Segregation: Métodos específicos
    - Single Responsibility: Apenas operações de custo
    
    Design Pattern: Repository Pattern
    Complexidade: Interfaces O(1), implementações variam
    """
    
    @abstractmethod
    async def get_costs_by_service(self, account_id: str, period: TimePeriod) -> Dict[ServiceName, Money]:
        """
        Obtém custos por serviço para um período
        
        Args:
            account_id: ID da conta AWS
            period: Período de análise
            
        Returns:
            Dicionário com custos por serviço
            
        Raises:
            CostRetrievalError: Erro ao obter custos
            
        Complexidade: O(n) onde n = número de serviços
        """
        pass
    
    @abstractmethod
    async def get_cost_entity(self, account_id: str, periods: List[TimePeriod]) -> CostEntity:
        """
        Obtém entidade de custo completa
        
        Args:
            account_id: ID da conta AWS
            periods: Lista de períodos para análise
            
        Returns:
            Entidade de custo com todos os dados
            
        Complexidade: O(n*m) onde n = serviços, m = períodos
        """
        pass
    
    @abstractmethod
    async def get_cost_trend(self, account_id: str, service: ServiceName, periods: List[TimePeriod]) -> List[tuple[TimePeriod, Money]]:
        """
        Obtém tendência de custo para um serviço
        
        Args:
            account_id: ID da conta AWS
            service: Nome do serviço
            periods: Períodos para análise de tendência
            
        Returns:
            Lista de tuplas (período, custo)
            
        Complexidade: O(m) onde m = número de períodos
        """
        pass
    
    @abstractmethod
    async def get_account_total_cost(self, account_id: str, period: TimePeriod) -> Money:
        """
        Obtém custo total da conta para um período
        
        Args:
            account_id: ID da conta AWS
            period: Período de análise
            
        Returns:
            Custo total
            
        Complexidade: O(n) onde n = número de serviços
        """
        pass


class CostRetrievalError(Exception):
    """
    Exceção específica do domínio para erros de obtenção de custos
    
    DDD: Exceções específicas do domínio
    Clean Code: Nome descritivo e específico
    """
    
    def __init__(self, message: str, account_id: str = None, period: TimePeriod = None, cause: Exception = None):
        super().__init__(message)
        self.account_id = account_id
        self.period = period
        self.cause = cause
        
    def __str__(self) -> str:
        base_message = super().__str__()
        
        if self.account_id:
            base_message += f" (Account: {self.account_id})"
        
        if self.period:
            base_message += f" (Period: {self.period})"
        
        if self.cause:
            base_message += f" (Caused by: {self.cause})"
        
        return base_message