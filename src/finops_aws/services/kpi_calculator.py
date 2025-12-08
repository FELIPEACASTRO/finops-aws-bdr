"""
FinOps AWS - KPI Calculator
Calculador de KPIs oficiais FinOps

Implementa os 12+ KPIs do framework FinOps:
- Total Spend
- Waste %
- Idle Cost
- Shadow Cost
- Commitment Loss
- Cost per Customer
- Cost per Transaction
- Margin
- Forecast 7/30/90
- RI/SP Coverage & Utilization
- MoM/YoY Growth
- Economic Health Index
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

import boto3
from botocore.exceptions import ClientError

from ..utils.logger import setup_logger
from ..models.finops_models import FinOpsKPIs


@dataclass
class KPIResult:
    """Resultado de cálculo de KPIs"""
    kpis: FinOpsKPIs
    calculated_at: datetime
    period_start: datetime
    period_end: datetime
    data_sources: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = self.kpis.to_dict()
        result['metadata'] = {
            'calculated_at': self.calculated_at.isoformat(),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'data_sources': self.data_sources,
            'warnings': self.warnings
        }
        return result


class KPICalculator:
    """
    Calculador de KPIs FinOps
    
    Calcula métricas oficiais usando dados de:
    - Cost Explorer (custos, forecasts)
    - Savings Plans Service (utilização, cobertura)
    - Reserved Instances Service (utilização, cobertura)
    - Tag Governance Service (shadow cost)
    - Analyzers (idle cost, savings potential)
    """
    
    def __init__(self, client_factory=None):
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce')
        return boto3.client('ce', region_name='us-east-1')
    
    def get_total_spend(self, days_back: int = 30) -> float:
        """Obtém custo total do período"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            total = 0.0
            for result in response.get('ResultsByTime', []):
                amount = result.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0')
                total += float(amount)
            
            return round(total, 2)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter total spend: {e}")
            return 0.0
    
    def get_cost_forecast(self, days_forward: int = 30) -> float:
        """Obtém previsão de custos"""
        try:
            client = self._get_ce_client()
            
            start_date = datetime.utcnow().strftime('%Y-%m-%d')
            end_date = (datetime.utcnow() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
            
            response = client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
            
            total_forecast = float(response.get('Total', {}).get('Amount', 0))
            return round(total_forecast, 2)
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'DataUnavailableException':
                self.logger.info("Dados insuficientes para forecast")
            else:
                self.logger.error(f"Erro ao obter forecast: {e}")
            return 0.0
        except Exception as e:
            self.logger.error(f"Erro ao obter forecast: {e}")
            return 0.0
    
    def get_cost_by_period(self, months_back: int) -> float:
        """Obtém custo de N meses atrás"""
        try:
            client = self._get_ce_client()
            
            end_date = (datetime.utcnow().replace(day=1) - timedelta(days=1))
            end_date = end_date.replace(day=1) - timedelta(days=30 * (months_back - 1))
            start_date = end_date - timedelta(days=30)
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            total = 0.0
            for result in response.get('ResultsByTime', []):
                amount = result.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0')
                total += float(amount)
            
            return round(total, 2)
            
        except Exception as e:
            self.logger.debug(f"Erro ao obter custo histórico: {e}")
            return 0.0
    
    def get_ri_utilization_and_coverage(self) -> Dict[str, float]:
        """Obtém utilização e cobertura de RIs"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            utilization = 0.0
            try:
                util_response = client.get_reservation_utilization(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY'
                )
                utilization = float(util_response.get('Total', {}).get('UtilizationPercentage', 0))
            except Exception:
                pass
            
            coverage = 0.0
            try:
                cov_response = client.get_reservation_coverage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY'
                )
                coverage = float(cov_response.get('Total', {}).get('CoverageHours', {}).get('CoverageHoursPercentage', 0))
            except Exception:
                pass
            
            return {
                'utilization': round(utilization, 2),
                'coverage': round(coverage, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter RI metrics: {e}")
            return {'utilization': 0.0, 'coverage': 0.0}
    
    def get_sp_utilization_and_coverage(self) -> Dict[str, float]:
        """Obtém utilização e cobertura de Savings Plans"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            utilization = 0.0
            unused = 0.0
            try:
                util_response = client.get_savings_plans_utilization(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY'
                )
                total = util_response.get('Total', {}).get('Utilization', {})
                utilization = float(total.get('UtilizationPercentage', 0))
                unused = float(total.get('UnusedCommitment', 0))
            except Exception:
                pass
            
            coverage = 0.0
            try:
                cov_response = client.get_savings_plans_coverage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY'
                )
                coverage = float(cov_response.get('Total', {}).get('Coverage', {}).get('CoveragePercentage', 0))
            except Exception:
                pass
            
            return {
                'utilization': round(utilization, 2),
                'coverage': round(coverage, 2),
                'unused_commitment': round(unused, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter SP metrics: {e}")
            return {'utilization': 0.0, 'coverage': 0.0, 'unused_commitment': 0.0}
    
    def calculate_all_kpis(
        self,
        idle_cost: float = 0.0,
        shadow_cost: float = 0.0,
        savings_potential: float = 0.0,
        savings_captured: float = 0.0,
        transactions_count: int = 0,
        customers_count: int = 0,
        revenue: float = 0.0,
        tag_coverage_percent: float = 0.0
    ) -> KPIResult:
        """
        Calcula todos os KPIs FinOps
        
        Args:
            idle_cost: Custo de recursos ociosos (de analyzers)
            shadow_cost: Custo de recursos sem tags (de tag governance)
            savings_potential: Economia potencial identificada
            savings_captured: Economia já capturada
            transactions_count: Número de transações (para unit economics)
            customers_count: Número de clientes (para unit economics)
            revenue: Receita do período (para margem)
        """
        warnings = []
        data_sources = []
        
        total_spend = self.get_total_spend(30)
        if total_spend > 0:
            data_sources.append('Cost Explorer')
        else:
            warnings.append('Dados de Cost Explorer não disponíveis')
        
        forecast_7d = self.get_cost_forecast(7)
        forecast_30d = self.get_cost_forecast(30)
        forecast_90d = self.get_cost_forecast(90)
        if forecast_30d > 0:
            data_sources.append('Cost Forecast')
        
        ri_metrics = self.get_ri_utilization_and_coverage()
        sp_metrics = self.get_sp_utilization_and_coverage()
        
        if ri_metrics['utilization'] > 0 or sp_metrics['utilization'] > 0:
            data_sources.append('Commitment Metrics')
        
        commitment_loss = sp_metrics.get('unused_commitment', 0)
        
        waste_cost = idle_cost + commitment_loss + shadow_cost
        waste_percent = (waste_cost / total_spend * 100) if total_spend > 0 else 0
        
        cost_per_transaction = total_spend / transactions_count if transactions_count > 0 else 0
        cost_per_customer = total_spend / customers_count if customers_count > 0 else 0
        
        margin = ((revenue - total_spend) / revenue * 100) if revenue > 0 else 0
        
        current_month_cost = self.get_total_spend(30)
        last_month_cost = self.get_cost_by_period(1)
        last_year_cost = self.get_cost_by_period(12)
        
        cost_growth_mom = ((current_month_cost - last_month_cost) / last_month_cost * 100) if last_month_cost > 0 else 0
        cost_growth_yoy = ((current_month_cost - last_year_cost) / last_year_cost * 100) if last_year_cost > 0 else 0
        
        health_factors = []
        
        if waste_percent <= 5:
            health_factors.append(25)
        elif waste_percent <= 10:
            health_factors.append(20)
        elif waste_percent <= 20:
            health_factors.append(10)
        else:
            health_factors.append(0)
        
        avg_commitment = (ri_metrics['utilization'] + sp_metrics['utilization']) / 2 if (ri_metrics['utilization'] > 0 or sp_metrics['utilization'] > 0) else 0
        if avg_commitment >= 80:
            health_factors.append(25)
        elif avg_commitment >= 60:
            health_factors.append(20)
        elif avg_commitment >= 40:
            health_factors.append(10)
        else:
            health_factors.append(5)
        
        avg_coverage = (ri_metrics['coverage'] + sp_metrics['coverage']) / 2 if (ri_metrics['coverage'] > 0 or sp_metrics['coverage'] > 0) else 0
        if avg_coverage >= 70:
            health_factors.append(25)
        elif avg_coverage >= 50:
            health_factors.append(20)
        elif avg_coverage >= 30:
            health_factors.append(10)
        else:
            health_factors.append(5)
        
        if cost_growth_mom <= 5:
            health_factors.append(25)
        elif cost_growth_mom <= 15:
            health_factors.append(20)
        elif cost_growth_mom <= 30:
            health_factors.append(10)
        else:
            health_factors.append(0)
        
        economic_health_index = sum(health_factors)
        
        kpis = FinOpsKPIs(
            total_spend=total_spend,
            waste_percent=waste_percent,
            idle_cost=idle_cost,
            shadow_cost=shadow_cost,
            commitment_loss=commitment_loss,
            cost_per_customer=round(cost_per_customer, 4),
            cost_per_transaction=round(cost_per_transaction, 6),
            margin=round(margin, 2),
            forecast_7d=forecast_7d,
            forecast_30d=forecast_30d,
            forecast_90d=forecast_90d,
            ri_coverage_percent=ri_metrics['coverage'],
            ri_utilization_percent=ri_metrics['utilization'],
            sp_coverage_percent=sp_metrics['coverage'],
            sp_utilization_percent=sp_metrics['utilization'],
            cost_growth_mom=round(cost_growth_mom, 2),
            cost_growth_yoy=round(cost_growth_yoy, 2),
            economic_health_index=economic_health_index,
            tag_coverage_percent=tag_coverage_percent,
            savings_captured=savings_captured,
            savings_potential=savings_potential
        )
        
        return KPIResult(
            kpis=kpis,
            calculated_at=datetime.utcnow(),
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            data_sources=data_sources,
            warnings=warnings
        )
    
    def get_kpis_summary(self) -> Dict[str, Any]:
        """Obtém resumo rápido de KPIs principais"""
        result = self.calculate_all_kpis()
        kpis = result.kpis
        
        return {
            'total_spend': kpis.total_spend,
            'waste_percent': kpis.waste_percent,
            'economic_health_index': kpis.economic_health_index,
            'ri_utilization': kpis.ri_utilization_percent,
            'sp_utilization': kpis.sp_utilization_percent,
            'forecast_30d': kpis.forecast_30d,
            'cost_growth_mom': kpis.cost_growth_mom,
            'calculated_at': result.calculated_at.isoformat()
        }
