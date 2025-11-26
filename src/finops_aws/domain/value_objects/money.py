"""
Value Object: Money
Implementa DDD com imutabilidade e validações de domínio
Complexidade: O(1) para todas as operações
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)  # Immutable Value Object
class Money:
    """
    Value Object para representar valores monetários
    
    DDD Principles:
    - Imutável
    - Sem identidade
    - Validações de domínio
    - Operações de negócio
    
    Complexidade: O(1) para todas as operações
    """
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        """
        Validações de domínio
        SOLID: Single Responsibility - apenas validação
        """
        if not isinstance(self.amount, Decimal):
            # Convert to Decimal for precision
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")
        
        # Round to 2 decimal places for currency precision
        rounded_amount = self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'amount', rounded_amount)
    
    def __add__(self, other: 'Money') -> 'Money':
        """
        Soma monetária com validação de moeda
        Complexidade: O(1)
        """
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: 'Money') -> 'Money':
        """
        Subtração monetária com validação
        Complexidade: O(1)
        """
        if not isinstance(other, Money):
            raise TypeError("Can only subtract Money from Money")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Result cannot be negative")
        
        return Money(result_amount, self.currency)
    
    def __mul__(self, factor: Union[int, float, Decimal]) -> 'Money':
        """
        Multiplicação por fator
        Complexidade: O(1)
        """
        if not isinstance(factor, (int, float, Decimal)):
            raise TypeError("Can only multiply Money by number")
        
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        
        return Money(self.amount * Decimal(str(factor)), self.currency)
    
    def __truediv__(self, divisor: Union[int, float, Decimal]) -> 'Money':
        """
        Divisão por fator
        Complexidade: O(1)
        """
        if not isinstance(divisor, (int, float, Decimal)):
            raise TypeError("Can only divide Money by number")
        
        if divisor <= 0:
            raise ValueError("Divisor must be positive")
        
        return Money(self.amount / Decimal(str(divisor)), self.currency)
    
    def __eq__(self, other) -> bool:
        """
        Igualdade baseada em valor (Value Object characteristic)
        Complexidade: O(1)
        """
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def __lt__(self, other: 'Money') -> bool:
        """
        Comparação menor que
        Complexidade: O(1)
        """
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money with Money")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        
        return self.amount < other.amount
    
    def __le__(self, other: 'Money') -> bool:
        """Complexidade: O(1)"""
        return self < other or self == other
    
    def __gt__(self, other: 'Money') -> bool:
        """Complexidade: O(1)"""
        return not self <= other
    
    def __ge__(self, other: 'Money') -> bool:
        """Complexidade: O(1)"""
        return not self < other
    
    def to_float(self) -> float:
        """
        Converte para float (para compatibilidade)
        Complexidade: O(1)
        """
        return float(self.amount)
    
    def format(self, include_currency: bool = True) -> str:
        """
        Formata valor monetário
        Complexidade: O(1)
        Clean Code: Nome descritivo e parâmetro opcional
        """
        formatted_amount = f"{self.amount:,.2f}"
        
        if include_currency:
            return f"{formatted_amount} {self.currency}"
        
        return formatted_amount
    
    @classmethod
    def zero(cls, currency: str = "USD") -> 'Money':
        """
        Factory method para valor zero
        Design Pattern: Factory Method
        Complexidade: O(1)
        """
        return cls(Decimal('0'), currency)
    
    @classmethod
    def from_float(cls, amount: float, currency: str = "USD") -> 'Money':
        """
        Factory method para criar Money a partir de float
        Design Pattern: Factory Method
        Complexidade: O(1)
        """
        return cls(Decimal(str(amount)), currency)
