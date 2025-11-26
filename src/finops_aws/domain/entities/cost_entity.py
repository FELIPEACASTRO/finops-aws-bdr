"""
Domain Entity: Cost Analysis
Implementa DDD com entidade rica em comportamento
Complexidade: O(1) para operações básicas, O(n) para agregações
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional
from decimal import Decimal

from ..value_objects.money import Money
from ..value_objects.time_period import TimePeriod
from ..value_objects.service_name import ServiceName


@dataclass(frozen=True)  # Immutability (DDD principle)
class CostEntity:
    """
    Entidade de domínio para análise de custos
    
    Seguindo DDD:
    - Rica em comportamento
    - Imutável
    - Validações de domínio
    - Linguagem ubíqua
    
    Complexidade: O(1) para criação, O(n) para agregações
    """
    account_id: str
    service_costs: Dict[ServiceName, Dict[TimePeriod, Money]] = field(default_factory=dict)
    analysis_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validações de domínio - SOLID: Single Responsibility"""
        if not self.account_id or len(self.account_id) != 12:
            raise ValueError("Account ID must be a 12-digit string")
    
    def get_total_cost_for_period(self, period: TimePeriod) -> Money:
        """
        Calcula custo total para um período
        
        Complexidade: O(n) onde n = número de serviços
        Design Pattern: Strategy implícito para diferentes períodos
        """
        total = Decimal('0')
        currency = 'USD'  # Default
        
        for service_name, periods in self.service_costs.items():
            if period in periods:
                cost = periods[period]
                total += cost.amount
                currency = cost.currency  # Assume mesma moeda
        
        return Money(total, currency)
    
    def get_top_services_by_cost(self, period: TimePeriod, limit: int = 5) -> List[tuple[ServiceName, Money]]:
        """
        Obtém serviços com maior custo
        
        Complexidade: O(n log n) devido ao sorting
        SOLID: Open/Closed - extensível para diferentes critérios
        """
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        service_costs = []
        for service_name, periods in self.service_costs.items():
            if period in periods:
                service_costs.append((service_name, periods[period]))
        
        # Sort by amount descending - O(n log n)
        service_costs.sort(key=lambda x: x[1].amount, reverse=True)
        
        return service_costs[:limit]
    
    def calculate_cost_trend(self, service: ServiceName) -> Optional[str]:
        """
        Calcula tendência de custo para um serviço
        
        Complexidade: O(1) - comparação de 3 períodos
        Domain Logic: Regras de negócio para tendências
        """
        if service not in self.service_costs:
            return None
        
        periods = self.service_costs[service]
        
        # Precisa ter pelo menos 2 períodos para calcular tendência
        if len(periods) < 2:
            return "INSUFFICIENT_DATA"
        
        # Ordena períodos por duração (7, 15, 30 dias)
        sorted_periods = sorted(periods.items(), key=lambda x: x[0].days)
        
        if len(sorted_periods) >= 3:
            # Compara últimos 3 períodos
            cost_7d = sorted_periods[0][1].amount
            cost_15d = sorted_periods[1][1].amount
            cost_30d = sorted_periods[2][1].amount
            
            # Calcula tendência baseada na média dos últimos períodos
            recent_avg = (cost_7d + cost_15d) / 2
            older_cost = cost_30d
            
            if recent_avg > older_cost * Decimal('1.1'):  # 10% de aumento
                return "INCREASING"
            elif recent_avg < older_cost * Decimal('0.9'):  # 10% de redução
                return "DECREASING"
            else:
                return "STABLE"
        
        return "UNKNOWN"
    
    def add_service_cost(self, service: ServiceName, period: TimePeriod, cost: Money) -> 'CostEntity':
        """
        Adiciona custo de serviço (retorna nova instância - imutabilidade)
        
        Complexidade: O(1)
        SOLID: Liskov Substitution - mantém contrato
        """
        new_service_costs = self.service_costs.copy()
        
        if service not in new_service_costs:
            new_service_costs[service] = {}
        
        new_service_costs[service] = new_service_costs[service].copy()
        new_service_costs[service][period] = cost
        
        return CostEntity(
            account_id=self.account_id,
            service_costs=new_service_costs,
            analysis_date=self.analysis_date
        )
    
    def get_cost_distribution(self, period: TimePeriod) -> Dict[ServiceName, float]:
        """
        Calcula distribuição percentual de custos
        
        Complexidade: O(n) onde n = número de serviços
        Clean Code: Nome descritivo, função única
        """
        total_cost = self.get_total_cost_for_period(period)
        
        if total_cost.amount == 0:
            return {}
        
        distribution = {}
        for service_name, periods in self.service_costs.items():
            if period in periods:
                service_cost = periods[period]
                percentage = float(service_cost.amount / total_cost.amount * 100)
                distribution[service_name] = round(percentage, 2)
        
        return distribution