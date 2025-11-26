"""
Value Object: Time Period
Representa períodos de tempo para análise de custos
Complexidade: O(1) para todas as operações
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Tuple


class PeriodType(Enum):
    """
    Enum para tipos de período
    SOLID: Open/Closed - fácil de estender
    """
    DAYS_7 = "7_days"
    DAYS_15 = "15_days"
    DAYS_30 = "30_days"
    CUSTOM = "custom"


@dataclass(frozen=True)  # Immutable Value Object
class TimePeriod:
    """
    Value Object para períodos de tempo
    
    DDD Principles:
    - Imutável
    - Validações de domínio
    - Comportamentos específicos do domínio
    
    Complexidade: O(1) para todas as operações
    """
    days: int
    period_type: PeriodType = PeriodType.CUSTOM
    
    def __post_init__(self):
        """
        Validações de domínio
        SOLID: Single Responsibility
        """
        if self.days <= 0:
            raise ValueError("Period days must be positive")
        
        if self.days > 365:
            raise ValueError("Period cannot exceed 365 days")
        
        # Auto-detect standard periods
        if self.period_type == PeriodType.CUSTOM:
            if self.days == 7:
                object.__setattr__(self, 'period_type', PeriodType.DAYS_7)
            elif self.days == 15:
                object.__setattr__(self, 'period_type', PeriodType.DAYS_15)
            elif self.days == 30:
                object.__setattr__(self, 'period_type', PeriodType.DAYS_30)
    
    def get_date_range(self, end_date: datetime = None) -> Tuple[datetime, datetime]:
        """
        Calcula range de datas para o período
        
        Complexidade: O(1)
        Clean Code: Nome descritivo, comportamento claro
        """
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=self.days)
        
        return start_date, end_date
    
    def get_api_format(self, end_date: datetime = None) -> Tuple[str, str]:
        """
        Retorna datas no formato para APIs AWS
        
        Complexidade: O(1)
        SOLID: Interface Segregation - método específico para API
        """
        start_date, end_date = self.get_date_range(end_date)
        
        return (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
    
    def __str__(self) -> str:
        """
        Representação string amigável
        Complexidade: O(1)
        """
        if self.period_type == PeriodType.DAYS_7:
            return "Last 7 days"
        elif self.period_type == PeriodType.DAYS_15:
            return "Last 15 days"
        elif self.period_type == PeriodType.DAYS_30:
            return "Last 30 days"
        else:
            return f"Last {self.days} days"
    
    def __hash__(self) -> int:
        """
        Hash para usar como chave em dicionários
        Complexidade: O(1)
        """
        return hash((self.days, self.period_type))
    
    def __eq__(self, other) -> bool:
        """
        Igualdade baseada em valor
        Complexidade: O(1)
        """
        if not isinstance(other, TimePeriod):
            return False
        return self.days == other.days and self.period_type == other.period_type
    
    def __lt__(self, other: 'TimePeriod') -> bool:
        """
        Comparação para ordenação
        Complexidade: O(1)
        """
        if not isinstance(other, TimePeriod):
            raise TypeError("Can only compare TimePeriod with TimePeriod")
        return self.days < other.days
    
    @classmethod
    def last_7_days(cls) -> 'TimePeriod':
        """
        Factory method para período de 7 dias
        Design Pattern: Factory Method
        Complexidade: O(1)
        """
        return cls(7, PeriodType.DAYS_7)
    
    @classmethod
    def last_15_days(cls) -> 'TimePeriod':
        """Factory method para período de 15 dias"""
        return cls(15, PeriodType.DAYS_15)
    
    @classmethod
    def last_30_days(cls) -> 'TimePeriod':
        """Factory method para período de 30 dias"""
        return cls(30, PeriodType.DAYS_30)
    
    @classmethod
    def custom_days(cls, days: int) -> 'TimePeriod':
        """Factory method para período customizado"""
        return cls(days, PeriodType.CUSTOM)