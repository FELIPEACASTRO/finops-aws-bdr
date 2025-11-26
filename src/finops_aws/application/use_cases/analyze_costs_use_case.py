"""
Use Case: Analyze Costs
Implementa Clean Architecture + SOLID + Strategy Pattern
Complexidade: O(n*m) onde n = serviços, m = períodos
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Protocol
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

from ...domain.entities.cost_entity import CostEntity
from ...domain.repositories.cost_repository import ICostRepository, CostRetrievalError
from ...domain.value_objects.time_period import TimePeriod
from ...domain.value_objects.service_name import ServiceName
from ...domain.value_objects.money import Money
from ..dto.cost_analysis_dto import CostAnalysisRequest, CostAnalysisResponse
from ..interfaces.logger_interface import ILogger


class IAnalysisStrategy(Protocol):
    """
    Strategy Interface para diferentes tipos de análise
    
    Design Pattern: Strategy Pattern
    SOLID: Interface Segregation
    """
    
    async def analyze(self, cost_entity: CostEntity, periods: List[TimePeriod]) -> Dict[str, any]:
        """Executa análise específica"""
        pass


class TopServicesAnalysisStrategy:
    """
    Strategy para análise de top serviços
    
    Complexidade: O(n log n) devido ao sorting
    """
    
    def __init__(self, limit: int = 10):
        self.limit = limit
    
    async def analyze(self, cost_entity: CostEntity, periods: List[TimePeriod]) -> Dict[str, any]:
        """
        Analisa os serviços com maior custo
        
        Complexidade: O(n log n) para cada período
        """
        analysis = {}
        
        for period in periods:
            top_services = cost_entity.get_top_services_by_cost(period, self.limit)
            
            analysis[f"top_services_{period.days}d"] = [
                {
                    "service": str(service),
                    "cost": cost.to_float(),
                    "currency": cost.currency,
                    "category": service.get_service_category()
                }
                for service, cost in top_services
            ]
        
        return analysis


class CostTrendAnalysisStrategy:
    """
    Strategy para análise de tendências
    
    Complexidade: O(n) onde n = número de serviços
    """
    
    async def analyze(self, cost_entity: CostEntity, periods: List[TimePeriod]) -> Dict[str, any]:
        """
        Analisa tendências de custo
        
        Complexidade: O(n) onde n = número de serviços
        """
        trends = {}
        
        for service_name in cost_entity.service_costs.keys():
            trend = cost_entity.calculate_cost_trend(service_name)
            if trend and trend != "INSUFFICIENT_DATA":
                trends[str(service_name)] = {
                    "trend": trend,
                    "category": service_name.get_service_category()
                }
        
        return {"cost_trends": trends}


class CostDistributionAnalysisStrategy:
    """
    Strategy para análise de distribuição
    
    Complexidade: O(n) onde n = número de serviços
    """
    
    async def analyze(self, cost_entity: CostEntity, periods: List[TimePeriod]) -> Dict[str, any]:
        """
        Analisa distribuição de custos
        
        Complexidade: O(n) para cada período
        """
        distributions = {}
        
        for period in periods:
            distribution = cost_entity.get_cost_distribution(period)
            distributions[f"distribution_{period.days}d"] = distribution
        
        return distributions


@dataclass(frozen=True)
class AnalyzeCostsUseCase:
    """
    Use Case para análise de custos
    
    Clean Architecture:
    - Independente de frameworks
    - Regras de negócio centralizadas
    - Inversão de dependências
    
    SOLID:
    - Single Responsibility: Apenas análise de custos
    - Open/Closed: Extensível via strategies
    - Dependency Inversion: Depende de abstrações
    
    Complexidade: O(n*m*s) onde n = serviços, m = períodos, s = strategies
    """
    
    cost_repository: ICostRepository
    logger: ILogger
    analysis_strategies: List[IAnalysisStrategy]
    
    async def execute(self, request: CostAnalysisRequest) -> CostAnalysisResponse:
        """
        Executa análise de custos
        
        Args:
            request: Dados da requisição
            
        Returns:
            Resposta com análise completa
            
        Raises:
            CostAnalysisError: Erro durante análise
            
        Complexidade: O(n*m*s) onde n = serviços, m = períodos, s = strategies
        """
        try:
            await self.logger.info(
                "Starting cost analysis",
                extra={
                    "account_id": request.account_id,
                    "periods": [p.days for p in request.periods],
                    "strategies_count": len(self.analysis_strategies)
                }
            )
            
            # Obter entidade de custo - O(n*m)
            cost_entity = await self.cost_repository.get_cost_entity(
                request.account_id,
                request.periods
            )
            
            # Executar strategies em paralelo - O(s) paralelo
            analysis_tasks = [
                strategy.analyze(cost_entity, request.periods)
                for strategy in self.analysis_strategies
            ]
            
            strategy_results = await asyncio.gather(*analysis_tasks)
            
            # Consolidar resultados - O(s)
            consolidated_analysis = {}
            for result in strategy_results:
                consolidated_analysis.update(result)
            
            # Calcular totais por período - O(m)
            period_totals = {}
            for period in request.periods:
                total = cost_entity.get_total_cost_for_period(period)
                period_totals[f"total_{period.days}d"] = {
                    "amount": total.to_float(),
                    "currency": total.currency
                }
            
            response = CostAnalysisResponse(
                account_id=request.account_id,
                analysis_date=datetime.now(),
                period_totals=period_totals,
                detailed_analysis=consolidated_analysis,
                metadata={
                    "strategies_used": [type(s).__name__ for s in self.analysis_strategies],
                    "periods_analyzed": [str(p) for p in request.periods],
                    "services_count": len(cost_entity.service_costs)
                }
            )
            
            await self.logger.info(
                "Cost analysis completed successfully",
                extra={
                    "account_id": request.account_id,
                    "services_analyzed": len(cost_entity.service_costs),
                    "total_cost_30d": period_totals.get("total_30d", {}).get("amount", 0)
                }
            )
            
            return response
            
        except CostRetrievalError as e:
            await self.logger.error(
                f"Cost retrieval failed: {e}",
                extra={
                    "account_id": request.account_id,
                    "error_type": type(e).__name__
                }
            )
            raise CostAnalysisError(f"Failed to retrieve costs: {e}") from e
            
        except Exception as e:
            await self.logger.error(
                f"Unexpected error during cost analysis: {e}",
                extra={
                    "account_id": request.account_id,
                    "error_type": type(e).__name__
                }
            )
            raise CostAnalysisError(f"Analysis failed: {e}") from e


class CostAnalysisError(Exception):
    """
    Exceção específica para erros de análise de custos
    
    Clean Code: Exceções específicas e descritivas
    """
    pass


class CostAnalysisFactory:
    """
    Factory para criar use case com strategies padrão
    
    Design Pattern: Factory Pattern
    SOLID: Single Responsibility - criação de objetos
    """
    
    @staticmethod
    def create_standard_analysis(
        cost_repository: ICostRepository,
        logger: ILogger,
        top_services_limit: int = 10
    ) -> AnalyzeCostsUseCase:
        """
        Cria análise padrão com strategies comuns
        
        Complexidade: O(1)
        """
        strategies = [
            TopServicesAnalysisStrategy(limit=top_services_limit),
            CostTrendAnalysisStrategy(),
            CostDistributionAnalysisStrategy()
        ]
        
        return AnalyzeCostsUseCase(
            cost_repository=cost_repository,
            logger=logger,
            analysis_strategies=strategies
        )
    
    @staticmethod
    def create_custom_analysis(
        cost_repository: ICostRepository,
        logger: ILogger,
        strategies: List[IAnalysisStrategy]
    ) -> AnalyzeCostsUseCase:
        """
        Cria análise customizada
        
        Complexidade: O(1)
        """
        return AnalyzeCostsUseCase(
            cost_repository=cost_repository,
            logger=logger,
            analysis_strategies=strategies
        )