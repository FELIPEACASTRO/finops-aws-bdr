"""
DTOs for Cost Analysis
Implementa Clean Architecture - Application Layer
Complexidade: O(1) para criação, O(n) para serialização
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

from ...domain.value_objects.time_period import TimePeriod


@dataclass(frozen=True)
class CostAnalysisRequest:
    """
    DTO para requisição de análise de custos
    
    Clean Architecture: Isolamento de dados de entrada
    SOLID: Single Responsibility - apenas dados de entrada
    
    Complexidade: O(1) para criação
    """
    account_id: str
    periods: List[TimePeriod] = field(default_factory=lambda: [
        TimePeriod.last_7_days(),
        TimePeriod.last_15_days(),
        TimePeriod.last_30_days()
    ])
    include_trends: bool = True
    include_distribution: bool = True
    top_services_limit: int = 10
    
    def __post_init__(self):
        """
        Validações de entrada
        SOLID: Single Responsibility
        """
        if not self.account_id or len(self.account_id) != 12:
            raise ValueError("Account ID must be a 12-digit string")
        
        if not self.periods:
            raise ValueError("At least one period must be specified")
        
        if self.top_services_limit <= 0:
            raise ValueError("Top services limit must be positive")
        
        # Validate periods
        for period in self.periods:
            if not isinstance(period, TimePeriod):
                raise ValueError("All periods must be TimePeriod instances")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialização para dicionário
        
        Complexidade: O(n) onde n = número de períodos
        """
        return {
            "account_id": self.account_id,
            "periods": [
                {
                    "days": period.days,
                    "type": period.period_type.value
                }
                for period in self.periods
            ],
            "include_trends": self.include_trends,
            "include_distribution": self.include_distribution,
            "top_services_limit": self.top_services_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostAnalysisRequest':
        """
        Desserialização de dicionário
        
        Design Pattern: Factory Method
        Complexidade: O(n) onde n = número de períodos
        """
        periods = []
        for period_data in data.get("periods", []):
            periods.append(TimePeriod(
                days=period_data["days"]
            ))
        
        return cls(
            account_id=data["account_id"],
            periods=periods if periods else None,  # Use default if empty
            include_trends=data.get("include_trends", True),
            include_distribution=data.get("include_distribution", True),
            top_services_limit=data.get("top_services_limit", 10)
        )


@dataclass(frozen=True)
class CostAnalysisResponse:
    """
    DTO para resposta de análise de custos
    
    Clean Architecture: Isolamento de dados de saída
    Complexidade: O(1) para criação, O(n) para serialização
    """
    account_id: str
    analysis_date: datetime
    period_totals: Dict[str, Dict[str, Any]]
    detailed_analysis: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialização completa para dicionário
        
        Complexidade: O(n) onde n = tamanho dos dados de análise
        Clean Code: Método com responsabilidade única
        """
        return {
            "account_id": self.account_id,
            "generated_at": self.analysis_date.isoformat(),
            "period_totals": self.period_totals,
            "analysis": self.detailed_analysis,
            "metadata": self.metadata
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialização para JSON
        
        Complexidade: O(n) onde n = tamanho dos dados
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def get_total_cost_for_period(self, days: int) -> Optional[float]:
        """
        Obtém custo total para um período específico
        
        Complexidade: O(1)
        Clean Code: Nome descritivo e comportamento claro
        """
        period_key = f"total_{days}d"
        period_data = self.period_totals.get(period_key)
        
        if period_data:
            return period_data.get("amount")
        
        return None
    
    def get_top_services(self, days: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtém top serviços para um período
        
        Complexidade: O(n) onde n = número de serviços
        """
        analysis_key = f"top_services_{days}d"
        services = self.detailed_analysis.get(analysis_key, [])
        
        if limit:
            return services[:limit]
        
        return services
    
    def get_cost_trends(self) -> Dict[str, Any]:
        """
        Obtém tendências de custo
        
        Complexidade: O(1)
        """
        return self.detailed_analysis.get("cost_trends", {})
    
    def get_cost_distribution(self, days: int) -> Dict[str, float]:
        """
        Obtém distribuição de custos para um período
        
        Complexidade: O(1)
        """
        distribution_key = f"distribution_{days}d"
        return self.detailed_analysis.get(distribution_key, {})
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostAnalysisResponse':
        """
        Desserialização de dicionário
        
        Design Pattern: Factory Method
        Complexidade: O(1)
        """
        analysis_date = data.get("generated_at")
        if isinstance(analysis_date, str):
            analysis_date = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
        elif not isinstance(analysis_date, datetime):
            analysis_date = datetime.now()
        
        return cls(
            account_id=data["account_id"],
            analysis_date=analysis_date,
            period_totals=data.get("period_totals", {}),
            detailed_analysis=data.get("analysis", {}),
            metadata=data.get("metadata", {})
        )


@dataclass(frozen=True)
class CostSummaryDTO:
    """
    DTO para resumo de custos
    
    SOLID: Interface Segregation - DTO específico para resumos
    Complexidade: O(1) para todas as operações
    """
    total_cost_7d: float
    total_cost_15d: float
    total_cost_30d: float
    currency: str
    top_service: str
    top_service_cost: float
    cost_trend: str  # INCREASING, DECREASING, STABLE
    services_count: int
    
    def get_monthly_projection(self) -> float:
        """
        Projeta custo mensal baseado nos últimos 7 dias
        
        Complexidade: O(1)
        Domain Logic: Projeção simples
        """
        if self.total_cost_7d <= 0:
            return 0.0
        
        # Projeção simples: (custo_7d / 7) * 30
        daily_average = self.total_cost_7d / 7
        return daily_average * 30
    
    def get_cost_efficiency_score(self) -> float:
        """
        Calcula score de eficiência de custos (0-100)
        
        Complexidade: O(1)
        Business Logic: Score baseado em tendência e distribuição
        """
        base_score = 50.0  # Score neutro
        
        # Ajusta baseado na tendência
        if self.cost_trend == "DECREASING":
            base_score += 25.0
        elif self.cost_trend == "INCREASING":
            base_score -= 25.0
        
        # Ajusta baseado na concentração (diversificação é boa)
        if self.services_count > 10:
            base_score += 10.0
        elif self.services_count < 3:
            base_score -= 10.0
        
        # Ajusta baseado na proporção do top service
        if self.total_cost_30d > 0:
            top_service_percentage = (self.top_service_cost / self.total_cost_30d) * 100
            if top_service_percentage > 80:  # Muito concentrado
                base_score -= 15.0
            elif top_service_percentage < 30:  # Bem distribuído
                base_score += 10.0
        
        # Garante que o score está entre 0 e 100
        return max(0.0, min(100.0, base_score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialização para dicionário"""
        return {
            "costs": {
                "last_7_days": self.total_cost_7d,
                "last_15_days": self.total_cost_15d,
                "last_30_days": self.total_cost_30d,
                "currency": self.currency
            },
            "top_service": {
                "name": self.top_service,
                "cost": self.top_service_cost
            },
            "insights": {
                "trend": self.cost_trend,
                "services_count": self.services_count,
                "monthly_projection": self.get_monthly_projection(),
                "efficiency_score": self.get_cost_efficiency_score()
            }
        }