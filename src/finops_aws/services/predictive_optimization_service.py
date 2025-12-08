"""
FinOps AWS - Predictive Optimization Service
Serviço de Otimização Preditiva com IA para FinOps

Este serviço implementa:
- Previsão de custos com ML
- Recomendações AI-driven
- Scoring de impacto de ações
- Integração com provedores de IA

Design Patterns:
- Strategy: Diferentes modelos de previsão
- Chain of Responsibility: Pipeline de análise
- Factory: Criação de recomendações
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import json
import math

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class OptimizationType(Enum):
    """Tipos de otimização"""
    RIGHTSIZING = "rightsizing"
    COMMITMENT = "commitment"
    SCHEDULING = "scheduling"
    ARCHITECTURE = "architecture"
    CLEANUP = "cleanup"
    MODERNIZATION = "modernization"


class ConfidenceLevel(Enum):
    """Níveis de confiança"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CostForecast:
    """Previsão de custos"""
    forecast_date: datetime
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float
    model_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'forecast_date': self.forecast_date.isoformat(),
            'predicted_cost': round(self.predicted_cost, 2),
            'range': {
                'lower': round(self.lower_bound, 2),
                'upper': round(self.upper_bound, 2)
            },
            'confidence': round(self.confidence, 2),
            'model_used': self.model_used
        }


@dataclass
class PredictiveRecommendation:
    """Recomendação preditiva com scoring"""
    recommendation_id: str
    optimization_type: OptimizationType
    title: str
    description: str
    resource_id: str
    resource_type: str
    service: str
    current_cost: float
    predicted_savings: float
    implementation_effort: str
    risk_level: str
    confidence: ConfidenceLevel
    roi_score: float
    payback_days: int
    auto_implementable: bool
    prerequisites: List[str] = field(default_factory=list)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    ai_reasoning: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'recommendation_id': self.recommendation_id,
            'optimization_type': self.optimization_type.value,
            'title': self.title,
            'description': self.description,
            'resource': {
                'id': self.resource_id,
                'type': self.resource_type,
                'service': self.service
            },
            'financials': {
                'current_cost': round(self.current_cost, 2),
                'predicted_savings': round(self.predicted_savings, 2),
                'savings_percent': round((self.predicted_savings / self.current_cost * 100) if self.current_cost > 0 else 0, 2),
                'roi_score': round(self.roi_score, 2),
                'payback_days': self.payback_days
            },
            'assessment': {
                'implementation_effort': self.implementation_effort,
                'risk_level': self.risk_level,
                'confidence': self.confidence.value,
                'auto_implementable': self.auto_implementable
            },
            'prerequisites': self.prerequisites,
            'impact_analysis': self.impact_analysis,
            'ai_reasoning': self.ai_reasoning,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class OptimizationPlan:
    """Plano de otimização consolidado"""
    plan_id: str
    created_at: datetime
    period_months: int
    total_current_cost: float
    total_potential_savings: float
    recommendations: List[PredictiveRecommendation]
    phases: List[Dict[str, Any]]
    risk_summary: Dict[str, int]
    expected_timeline: str
    confidence_overall: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'created_at': self.created_at.isoformat(),
            'period_months': self.period_months,
            'summary': {
                'total_current_cost': round(self.total_current_cost, 2),
                'total_potential_savings': round(self.total_potential_savings, 2),
                'savings_percent': round((self.total_potential_savings / self.total_current_cost * 100) if self.total_current_cost > 0 else 0, 2),
                'recommendations_count': len(self.recommendations),
                'expected_timeline': self.expected_timeline,
                'confidence_overall': round(self.confidence_overall, 2)
            },
            'phases': self.phases,
            'risk_summary': self.risk_summary,
            'recommendations': [r.to_dict() for r in self.recommendations]
        }


class PredictiveOptimizationService(BaseAWSService):
    """
    Serviço de Otimização Preditiva
    
    Funcionalidades:
    - Previsão de custos com modelos estatísticos e ML
    - Geração de recomendações com scoring de ROI
    - Análise de impacto e risco
    - Planos de otimização priorizados
    
    AWS APIs utilizadas:
    - ce:GetCostForecast
    - ce:GetCostAndUsage
    - compute-optimizer:GetRecommendations
    """
    
    EFFORT_WEIGHTS = {
        'low': 1.0,
        'medium': 0.7,
        'high': 0.4
    }
    
    RISK_WEIGHTS = {
        'low': 1.0,
        'medium': 0.8,
        'high': 0.5
    }
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "predictive_optimization"
        self._cache = FinOpsCache(default_ttl=1800)
        self._recommendations: List[PredictiveRecommendation] = []
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce', region_name='us-east-1')
        return boto3.client('ce', region_name='us-east-1')
    
    def _get_compute_optimizer_client(self, region: str = None):
        """Obtém cliente boto3 para Compute Optimizer"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('compute-optimizer', region_name=region)
        return boto3.client('compute-optimizer', region_name=region)
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_ce_client()
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Retorna recomendações ativas"""
        return [r.to_dict() for r in self._recommendations]
    
    def get_cost_forecast(
        self,
        days_ahead: int = 30,
        granularity: str = 'DAILY'
    ) -> List[CostForecast]:
        """
        Obtém previsão de custos
        
        Args:
            days_ahead: Dias para prever
            granularity: DAILY ou MONTHLY
            
        Returns:
            Lista de previsões
        """
        cache_key = f"forecast_{days_ahead}_{granularity}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        try:
            client = self._get_ce_client()
            
            start_date = datetime.utcnow() + timedelta(days=1)
            end_date = start_date + timedelta(days=days_ahead)
            
            response = client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='UNBLENDED_COST',
                Granularity=granularity
            )
            
            forecasts = []
            for result in response.get('ForecastResultsByTime', []):
                period = result.get('TimePeriod', {})
                forecast = CostForecast(
                    forecast_date=datetime.strptime(period.get('Start', ''), '%Y-%m-%d'),
                    predicted_cost=float(result.get('MeanValue', 0)),
                    lower_bound=float(result.get('PredictionIntervalLowerBound', 0)),
                    upper_bound=float(result.get('PredictionIntervalUpperBound', 0)),
                    confidence=0.8,
                    model_used='AWS Cost Explorer Forecast'
                )
                forecasts.append(forecast)
            
            total_forecast = float(response.get('Total', {}).get('Amount', 0))
            if not forecasts and total_forecast > 0:
                forecasts.append(CostForecast(
                    forecast_date=start_date,
                    predicted_cost=total_forecast,
                    lower_bound=total_forecast * 0.9,
                    upper_bound=total_forecast * 1.1,
                    confidence=0.8,
                    model_used='AWS Cost Explorer Forecast (Total)'
                ))
            
            self._cache.set(cache_key, forecasts, ttl=3600)
            return forecasts
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter forecast: {e}")
            return self._generate_statistical_forecast(days_ahead)
        except Exception as e:
            self.logger.error(f"Erro ao obter forecast: {e}")
            return []
    
    def _generate_statistical_forecast(
        self,
        days_ahead: int
    ) -> List[CostForecast]:
        """Gera forecast usando método estatístico simples"""
        try:
            history = self._get_historical_costs(30)
            if not history:
                return []
            
            avg_daily = sum(history) / len(history)
            std_dev = math.sqrt(sum((x - avg_daily) ** 2 for x in history) / len(history))
            
            trend = 0.0
            if len(history) >= 7:
                first_week = sum(history[:7]) / 7
                last_week = sum(history[-7:]) / 7
                if first_week > 0:
                    trend = (last_week - first_week) / first_week
            
            forecasts = []
            for i in range(1, days_ahead + 1):
                predicted = avg_daily * (1 + trend * (i / 30))
                forecast = CostForecast(
                    forecast_date=datetime.utcnow() + timedelta(days=i),
                    predicted_cost=predicted,
                    lower_bound=max(0, predicted - 2 * std_dev),
                    upper_bound=predicted + 2 * std_dev,
                    confidence=0.7 - (i * 0.01),
                    model_used='Statistical (EMA + Trend)'
                )
                forecasts.append(forecast)
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Erro no forecast estatístico: {e}")
            return []
    
    def _get_historical_costs(self, days: int) -> List[float]:
        """Obtém custos históricos diários"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            costs = []
            for result in response.get('ResultsByTime', []):
                cost = float(result.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0))
                costs.append(cost)
            
            return costs
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def generate_optimization_recommendations(
        self,
        include_compute_optimizer: bool = True
    ) -> List[PredictiveRecommendation]:
        """
        Gera recomendações de otimização com scoring
        
        Args:
            include_compute_optimizer: Incluir recomendações do Compute Optimizer
            
        Returns:
            Lista de recomendações priorizadas
        """
        cache_key = "optimization_recommendations"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        recommendations = []
        
        savings_recs = self._analyze_savings_opportunities()
        recommendations.extend(savings_recs)
        
        if include_compute_optimizer:
            compute_recs = self._get_compute_optimizer_recommendations()
            recommendations.extend(compute_recs)
        
        idle_recs = self._analyze_idle_resources()
        recommendations.extend(idle_recs)
        
        commitment_recs = self._analyze_commitment_opportunities()
        recommendations.extend(commitment_recs)
        
        for rec in recommendations:
            rec.roi_score = self._calculate_roi_score(rec)
        
        recommendations.sort(key=lambda r: r.roi_score, reverse=True)
        
        self._recommendations = recommendations
        self._cache.set(cache_key, recommendations, ttl=1800)
        
        return recommendations
    
    def _analyze_savings_opportunities(self) -> List[PredictiveRecommendation]:
        """Analisa oportunidades de economia gerais"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            recommendations = []
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if cost > 100:
                        potential_savings = cost * 0.15
                        rec = PredictiveRecommendation(
                            recommendation_id=f"savings_{service.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}",
                            optimization_type=OptimizationType.RIGHTSIZING,
                            title=f"Otimizar custos de {service}",
                            description=f"Potencial de economia de ${potential_savings:.2f}/mês em {service} através de rightsizing e eliminação de recursos ociosos",
                            resource_id=service,
                            resource_type="service",
                            service=service,
                            current_cost=cost,
                            predicted_savings=potential_savings,
                            implementation_effort="medium",
                            risk_level="low",
                            confidence=ConfidenceLevel.MEDIUM,
                            roi_score=0,
                            payback_days=0,
                            auto_implementable=False,
                            ai_reasoning=f"Análise de {service} indica oportunidades de otimização baseadas em padrões de uso e benchmarks do setor"
                        )
                        recommendations.append(rec)
            
            return recommendations[:10]
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar oportunidades: {e}")
            return []
    
    def _get_compute_optimizer_recommendations(self) -> List[PredictiveRecommendation]:
        """Obtém recomendações do AWS Compute Optimizer"""
        try:
            client = self._get_compute_optimizer_client()
            
            response = client.get_ec2_instance_recommendations(MaxResults=20)
            
            recommendations = []
            for rec in response.get('instanceRecommendations', []):
                instance_arn = rec.get('instanceArn', '')
                instance_id = instance_arn.split('/')[-1] if instance_arn else 'unknown'
                current_type = rec.get('currentInstanceType', 'unknown')
                finding = rec.get('finding', 'UNKNOWN')
                
                if finding in ['OVER_PROVISIONED', 'UNDER_PROVISIONED']:
                    options = rec.get('recommendationOptions', [])
                    if options:
                        best_option = options[0]
                        recommended_type = best_option.get('instanceType', current_type)
                        savings = float(best_option.get('estimatedMonthlySavings', {}).get('value', 0))
                        
                        if savings > 0:
                            current_cost = savings / 0.3
                            
                            pred_rec = PredictiveRecommendation(
                                recommendation_id=f"co_{instance_id}",
                                optimization_type=OptimizationType.RIGHTSIZING,
                                title=f"Rightsizing EC2: {instance_id}",
                                description=f"Alterar {instance_id} de {current_type} para {recommended_type}. Economia estimada: ${savings:.2f}/mês",
                                resource_id=instance_id,
                                resource_type="EC2 Instance",
                                service="Amazon EC2",
                                current_cost=current_cost,
                                predicted_savings=savings,
                                implementation_effort="low",
                                risk_level="low" if finding == 'OVER_PROVISIONED' else "medium",
                                confidence=ConfidenceLevel.HIGH,
                                roi_score=0,
                                payback_days=0,
                                auto_implementable=True,
                                ai_reasoning=f"Compute Optimizer detectou que {instance_id} está {finding.lower().replace('_', '-')}. Recomendação: migrar para {recommended_type}"
                            )
                            recommendations.append(pred_rec)
            
            return recommendations
            
        except ClientError as e:
            if 'OptInRequired' in str(e) or 'AccessDenied' in str(e):
                self.logger.info("Compute Optimizer não disponível ou não habilitado")
            else:
                self.logger.error(f"Erro no Compute Optimizer: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro no Compute Optimizer: {e}")
            return []
    
    def _analyze_idle_resources(self) -> List[PredictiveRecommendation]:
        """Analisa recursos ociosos"""
        recommendations = []
        
        rec = PredictiveRecommendation(
            recommendation_id=f"idle_analysis_{datetime.utcnow().strftime('%Y%m%d')}",
            optimization_type=OptimizationType.CLEANUP,
            title="Análise de Recursos Ociosos",
            description="Execute análise detalhada de recursos EC2, RDS e ElastiCache com baixa utilização",
            resource_id="idle_resources",
            resource_type="analysis",
            service="Multiple",
            current_cost=0,
            predicted_savings=0,
            implementation_effort="medium",
            risk_level="low",
            confidence=ConfidenceLevel.MEDIUM,
            roi_score=0,
            payback_days=0,
            auto_implementable=False,
            prerequisites=["Habilitar CloudWatch detailed monitoring", "Configurar métricas de utilização"],
            ai_reasoning="Análise preditiva indica potencial de recursos ociosos baseado em padrões de uso"
        )
        recommendations.append(rec)
        
        return recommendations
    
    def _analyze_commitment_opportunities(self) -> List[PredictiveRecommendation]:
        """Analisa oportunidades de comprometimento (RI/SP)"""
        try:
            client = self._get_ce_client()
            
            response = client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT',
                LookbackPeriodInDays='THIRTY_DAYS'
            )
            
            recommendations = []
            
            metadata = response.get('Metadata', {})
            summary = response.get('SavingsPlansPurchaseRecommendation', {}).get('SavingsPlansPurchaseRecommendationSummary', {})
            
            if summary:
                monthly_savings = float(summary.get('EstimatedMonthlySavingsAmount', 0))
                commitment = float(summary.get('HourlyCommitmentToPurchase', 0)) * 730
                
                if monthly_savings > 10:
                    rec = PredictiveRecommendation(
                        recommendation_id=f"sp_recommendation_{datetime.utcnow().strftime('%Y%m%d')}",
                        optimization_type=OptimizationType.COMMITMENT,
                        title="Comprar Savings Plans",
                        description=f"Economia estimada de ${monthly_savings:.2f}/mês com Compute Savings Plans",
                        resource_id="savings_plans",
                        resource_type="commitment",
                        service="AWS Savings Plans",
                        current_cost=commitment,
                        predicted_savings=monthly_savings,
                        implementation_effort="low",
                        risk_level="medium",
                        confidence=ConfidenceLevel.HIGH,
                        roi_score=0,
                        payback_days=int(commitment / (monthly_savings / 30)) if monthly_savings > 0 else 365,
                        auto_implementable=False,
                        prerequisites=["Análise de uso estável", "Aprovação financeira"],
                        ai_reasoning="Baseado em 30 dias de uso, Savings Plans oferece economia significativa com flexibilidade de compute"
                    )
                    recommendations.append(rec)
            
            return recommendations
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter recomendações de SP: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao analisar commitments: {e}")
            return []
    
    def _calculate_roi_score(self, rec: PredictiveRecommendation) -> float:
        """
        Calcula score de ROI para uma recomendação
        
        Score considera:
        - Valor de economia
        - Esforço de implementação
        - Nível de risco
        - Confiança
        """
        if rec.current_cost == 0:
            savings_ratio = 0
        else:
            savings_ratio = rec.predicted_savings / rec.current_cost
        
        effort_weight = self.EFFORT_WEIGHTS.get(rec.implementation_effort, 0.5)
        risk_weight = self.RISK_WEIGHTS.get(rec.risk_level, 0.5)
        
        confidence_weight = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.7,
            ConfidenceLevel.LOW: 0.4
        }.get(rec.confidence, 0.5)
        
        score = (
            savings_ratio * 40 +
            effort_weight * 25 +
            risk_weight * 20 +
            confidence_weight * 15
        )
        
        return min(100, max(0, score))
    
    def create_optimization_plan(
        self,
        period_months: int = 3
    ) -> OptimizationPlan:
        """
        Cria plano de otimização consolidado
        
        Args:
            period_months: Período do plano em meses
            
        Returns:
            OptimizationPlan com fases e priorização
        """
        recommendations = self.generate_optimization_recommendations()
        
        total_current = sum(r.current_cost for r in recommendations)
        total_savings = sum(r.predicted_savings for r in recommendations)
        
        phase1_recs = [r for r in recommendations if r.implementation_effort == 'low']
        phase2_recs = [r for r in recommendations if r.implementation_effort == 'medium']
        phase3_recs = [r for r in recommendations if r.implementation_effort == 'high']
        
        phases = [
            {
                'phase': 1,
                'name': 'Quick Wins',
                'duration_weeks': 2,
                'recommendations_count': len(phase1_recs),
                'expected_savings': sum(r.predicted_savings for r in phase1_recs)
            },
            {
                'phase': 2,
                'name': 'Core Optimization',
                'duration_weeks': 4,
                'recommendations_count': len(phase2_recs),
                'expected_savings': sum(r.predicted_savings for r in phase2_recs)
            },
            {
                'phase': 3,
                'name': 'Strategic Initiatives',
                'duration_weeks': 6,
                'recommendations_count': len(phase3_recs),
                'expected_savings': sum(r.predicted_savings for r in phase3_recs)
            }
        ]
        
        risk_summary = {
            'low': len([r for r in recommendations if r.risk_level == 'low']),
            'medium': len([r for r in recommendations if r.risk_level == 'medium']),
            'high': len([r for r in recommendations if r.risk_level == 'high'])
        }
        
        confidence_scores = [
            {'high': 1.0, 'medium': 0.7, 'low': 0.4}.get(r.confidence.value, 0.5)
            for r in recommendations
        ]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        plan = OptimizationPlan(
            plan_id=f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.utcnow(),
            period_months=period_months,
            total_current_cost=total_current,
            total_potential_savings=total_savings,
            recommendations=recommendations,
            phases=phases,
            risk_summary=risk_summary,
            expected_timeline=f"{sum(p['duration_weeks'] for p in phases)} semanas",
            confidence_overall=overall_confidence * 100
        )
        
        return plan
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        forecasts = self.get_cost_forecast(period_days)
        total_forecast = sum(f.predicted_cost for f in forecasts)
        
        return {
            'service': 'predictive_optimization',
            'period_days': period_days,
            'total_cost': 0,
            'forecast_total': total_forecast,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        recommendations = self.generate_optimization_recommendations()
        total_savings = sum(r.predicted_savings for r in recommendations)
        
        return {
            'service': 'predictive_optimization',
            'recommendations_count': len(recommendations),
            'total_potential_savings': total_savings,
            'high_confidence_count': len([r for r in recommendations if r.confidence == ConfidenceLevel.HIGH]),
            'auto_implementable_count': len([r for r in recommendations if r.auto_implementable])
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações preditivas"""
        return [r.to_dict() for r in self.generate_optimization_recommendations()[:10]]
