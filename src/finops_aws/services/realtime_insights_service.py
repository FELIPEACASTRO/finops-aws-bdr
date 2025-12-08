"""
FinOps AWS - Real-Time Insights Service
Serviço de Insights em Tempo Real para FinOps

Este serviço implementa:
- Pipeline de insights com latência <5 min
- Streaming de métricas de custo
- Alertas em tempo real
- Dashboard data streaming

Design Patterns:
- Observer: Notificação de mudanças
- Publisher-Subscriber: Streaming de eventos
- Singleton: Cache compartilhado
"""
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import json
import threading
import time

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class InsightType(Enum):
    """Tipos de insight"""
    COST_SPIKE = "cost_spike"
    ANOMALY = "anomaly"
    BUDGET_ALERT = "budget_alert"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    COMMITMENT_EXPIRY = "commitment_expiry"
    RESOURCE_IDLE = "resource_idle"
    TAG_VIOLATION = "tag_violation"


class InsightSeverity(Enum):
    """Severidade de insight"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class RealTimeInsight:
    """Insight em tempo real"""
    insight_id: str
    insight_type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    detected_at: datetime
    resource_id: str = ""
    resource_type: str = ""
    service: str = ""
    region: str = ""
    impact_amount: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: str = ""
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'insight_id': self.insight_id,
            'insight_type': self.insight_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'detected_at': self.detected_at.isoformat(),
            'resource': {
                'id': self.resource_id,
                'type': self.resource_type,
                'service': self.service,
                'region': self.region
            },
            'impact_amount': round(self.impact_amount, 2),
            'metadata': self.metadata,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


@dataclass
class CostSnapshot:
    """Snapshot de custos em tempo real"""
    timestamp: datetime
    total_cost_today: float
    total_cost_mtd: float
    projected_monthly: float
    top_services: Dict[str, float]
    hourly_rate: float
    vs_yesterday: float
    vs_last_week: float
    active_alerts: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'costs': {
                'today': round(self.total_cost_today, 2),
                'mtd': round(self.total_cost_mtd, 2),
                'projected_monthly': round(self.projected_monthly, 2),
                'hourly_rate': round(self.hourly_rate, 4)
            },
            'top_services': {k: round(v, 2) for k, v in self.top_services.items()},
            'comparisons': {
                'vs_yesterday_percent': round(self.vs_yesterday, 2),
                'vs_last_week_percent': round(self.vs_last_week, 2)
            },
            'active_alerts': self.active_alerts
        }


@dataclass
class StreamConfig:
    """Configuração de streaming"""
    enabled: bool = True
    refresh_interval_seconds: int = 300
    max_insights_retained: int = 100
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=list)


class RealTimeInsightsService(BaseAWSService):
    """
    Serviço de Insights em Tempo Real
    
    Funcionalidades:
    - Coleta métricas de custo em intervalos curtos
    - Detecta anomalias e spikes em tempo real
    - Gera alertas baseados em thresholds
    - Fornece dados para dashboard em tempo real
    
    AWS APIs utilizadas:
    - ce:GetCostAndUsage (com granularidade horária)
    - cloudwatch:GetMetricData
    - budgets:DescribeBudgets
    - ce:GetAnomalies
    """
    
    DEFAULT_REFRESH_INTERVAL = 300
    MAX_INSIGHTS = 100
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "realtime_insights"
        self._cache = FinOpsCache(default_ttl=60)
        self._insights: List[RealTimeInsight] = []
        self._subscribers: List[Callable[[RealTimeInsight], None]] = []
        self._config = StreamConfig(
            alert_thresholds={
                'daily_spend_increase': 20.0,
                'hourly_rate_spike': 50.0,
                'budget_utilization': 80.0
            },
            notification_channels=['dashboard', 'email']
        )
        self._last_snapshot: Optional[CostSnapshot] = None
        self._running = False
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce', region_name='us-east-1')
        return boto3.client('ce', region_name='us-east-1')
    
    def _get_budgets_client(self):
        """Obtém cliente boto3 para Budgets"""
        if self._client_factory:
            return self._client_factory.get_client('budgets', region_name='us-east-1')
        return boto3.client('budgets', region_name='us-east-1')
    
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
        """Retorna configuração do serviço"""
        return {
            'config': {
                'enabled': self._config.enabled,
                'refresh_interval': self._config.refresh_interval_seconds,
                'thresholds': self._config.alert_thresholds
            },
            'insights_count': len(self._insights),
            'subscribers_count': len(self._subscribers),
            'running': self._running
        }
    
    def subscribe(self, callback: Callable[[RealTimeInsight], None]):
        """Registra subscriber para novos insights"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[RealTimeInsight], None]):
        """Remove subscriber"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self, insight: RealTimeInsight):
        """Notifica todos os subscribers"""
        for subscriber in self._subscribers:
            try:
                subscriber(insight)
            except Exception as e:
                self.logger.error(f"Erro ao notificar subscriber: {e}")
    
    def get_current_snapshot(self, force_refresh: bool = False) -> CostSnapshot:
        """
        Obtém snapshot atual de custos
        
        Args:
            force_refresh: Se True, ignora cache
            
        Returns:
            CostSnapshot com métricas atuais
        """
        cache_key = "current_snapshot"
        
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached:
                return cached
        
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        today_cost = self._get_cost_for_period(today_start, now)
        mtd_cost = self._get_cost_for_period(month_start, now)
        
        days_in_month = 30
        days_elapsed = (now - month_start).days + 1
        if days_elapsed > 0:
            projected = (mtd_cost / days_elapsed) * days_in_month
        else:
            projected = mtd_cost * days_in_month
        
        hours_today = max(1, (now - today_start).seconds / 3600)
        hourly_rate = today_cost / hours_today
        
        top_services = self._get_top_services(today_start, now)
        
        yesterday_start = today_start - timedelta(days=1)
        yesterday_cost = self._get_cost_for_period(yesterday_start, today_start)
        vs_yesterday = 0.0
        if yesterday_cost > 0:
            vs_yesterday = ((today_cost - yesterday_cost) / yesterday_cost) * 100
        
        week_ago_start = today_start - timedelta(days=7)
        week_ago_end = today_start - timedelta(days=6)
        week_ago_cost = self._get_cost_for_period(week_ago_start, week_ago_end)
        vs_last_week = 0.0
        if week_ago_cost > 0:
            vs_last_week = ((today_cost - week_ago_cost) / week_ago_cost) * 100
        
        active_alerts = len([i for i in self._insights if not i.acknowledged])
        
        snapshot = CostSnapshot(
            timestamp=now,
            total_cost_today=today_cost,
            total_cost_mtd=mtd_cost,
            projected_monthly=projected,
            top_services=top_services,
            hourly_rate=hourly_rate,
            vs_yesterday=vs_yesterday,
            vs_last_week=vs_last_week,
            active_alerts=active_alerts
        )
        
        self._cache.set(cache_key, snapshot, ttl=60)
        self._last_snapshot = snapshot
        
        self._check_for_alerts(snapshot)
        
        return snapshot
    
    def _get_cost_for_period(
        self,
        start: datetime,
        end: datetime
    ) -> float:
        """Obtém custo para período específico"""
        try:
            client = self._get_ce_client()
            
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            
            if start_str == end_str:
                end_str = (end + timedelta(days=1)).strftime('%Y-%m-%d')
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            total = 0.0
            for result in response.get('ResultsByTime', []):
                total += float(result.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0))
            
            return total
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custo: {e}")
            return 0.0
    
    def _get_top_services(
        self,
        start: datetime,
        end: datetime,
        limit: int = 5
    ) -> Dict[str, float]:
        """Obtém top serviços por custo"""
        try:
            client = self._get_ce_client()
            
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            
            if start_str == end_str:
                end_str = (end + timedelta(days=1)).strftime('%Y-%m-%d')
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            by_service: Dict[str, float] = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_service[service] = by_service.get(service, 0) + cost
            
            sorted_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_services[:limit])
            
        except Exception as e:
            self.logger.error(f"Erro ao obter top serviços: {e}")
            return {}
    
    def _check_for_alerts(self, snapshot: CostSnapshot):
        """Verifica thresholds e gera alertas"""
        if snapshot.vs_yesterday > self._config.alert_thresholds.get('daily_spend_increase', 20):
            self._create_insight(
                InsightType.COST_SPIKE,
                InsightSeverity.WARNING,
                f"Aumento de {snapshot.vs_yesterday:.1f}% nos custos hoje",
                f"Custos de hoje (${snapshot.total_cost_today:.2f}) são {snapshot.vs_yesterday:.1f}% maiores que ontem",
                impact_amount=snapshot.total_cost_today - (snapshot.total_cost_today / (1 + snapshot.vs_yesterday/100))
            )
        
        if self._last_snapshot:
            prev_rate = self._last_snapshot.hourly_rate
            if prev_rate > 0:
                rate_change = ((snapshot.hourly_rate - prev_rate) / prev_rate) * 100
                if rate_change > self._config.alert_thresholds.get('hourly_rate_spike', 50):
                    self._create_insight(
                        InsightType.COST_SPIKE,
                        InsightSeverity.CRITICAL,
                        f"Spike de {rate_change:.1f}% na taxa horária",
                        f"Taxa horária subiu de ${prev_rate:.4f} para ${snapshot.hourly_rate:.4f}",
                        impact_amount=snapshot.hourly_rate - prev_rate
                    )
    
    def _create_insight(
        self,
        insight_type: InsightType,
        severity: InsightSeverity,
        title: str,
        description: str,
        resource_id: str = "",
        impact_amount: float = 0.0,
        metadata: Dict[str, Any] = None
    ):
        """Cria novo insight"""
        insight = RealTimeInsight(
            insight_id=f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self._insights)}",
            insight_type=insight_type,
            severity=severity,
            title=title,
            description=description,
            detected_at=datetime.utcnow(),
            resource_id=resource_id,
            impact_amount=impact_amount,
            metadata=metadata or {}
        )
        
        self._insights.insert(0, insight)
        
        if len(self._insights) > self.MAX_INSIGHTS:
            self._insights = self._insights[:self.MAX_INSIGHTS]
        
        self._notify_subscribers(insight)
        self.logger.info(f"Insight criado: {title}")
    
    def detect_anomalies(self) -> List[RealTimeInsight]:
        """Detecta anomalias de custo via AWS API"""
        try:
            client = self._get_ce_client()
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            response = client.get_anomalies(
                DateInterval={
                    'StartDate': start_date.strftime('%Y-%m-%d'),
                    'EndDate': end_date.strftime('%Y-%m-%d')
                },
                MaxResults=10
            )
            
            new_insights = []
            for anomaly in response.get('Anomalies', []):
                impact = anomaly.get('Impact', {})
                total_impact = float(impact.get('TotalImpact', 0))
                
                if total_impact > 10:
                    root_causes = anomaly.get('RootCauses', [])
                    service = root_causes[0].get('Service', 'Unknown') if root_causes else 'Unknown'
                    
                    insight = RealTimeInsight(
                        insight_id=anomaly.get('AnomalyId', ''),
                        insight_type=InsightType.ANOMALY,
                        severity=InsightSeverity.WARNING if total_impact < 100 else InsightSeverity.CRITICAL,
                        title=f"Anomalia detectada: ${total_impact:.2f}",
                        description=f"Anomalia de custo detectada em {service}",
                        detected_at=datetime.utcnow(),
                        service=service,
                        impact_amount=total_impact
                    )
                    
                    if insight.insight_id not in [i.insight_id for i in self._insights]:
                        self._insights.insert(0, insight)
                        new_insights.append(insight)
            
            return new_insights
            
        except ClientError as e:
            if 'AccessDenied' not in str(e):
                self.logger.error(f"Erro ao detectar anomalias: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao detectar anomalias: {e}")
            return []
    
    def get_insights(
        self,
        limit: int = 20,
        severity_filter: Optional[InsightSeverity] = None,
        unacknowledged_only: bool = False
    ) -> List[RealTimeInsight]:
        """
        Obtém lista de insights
        
        Args:
            limit: Número máximo de insights
            severity_filter: Filtrar por severidade
            unacknowledged_only: Apenas não reconhecidos
            
        Returns:
            Lista de insights
        """
        insights = self._insights
        
        if severity_filter:
            insights = [i for i in insights if i.severity == severity_filter]
        
        if unacknowledged_only:
            insights = [i for i in insights if not i.acknowledged]
        
        return insights[:limit]
    
    def acknowledge_insight(self, insight_id: str, user: str) -> bool:
        """Reconhece um insight"""
        for insight in self._insights:
            if insight.insight_id == insight_id:
                insight.acknowledged = True
                insight.acknowledged_by = user
                insight.acknowledged_at = datetime.utcnow()
                return True
        return False
    
    def get_streaming_data(self) -> Dict[str, Any]:
        """
        Obtém dados formatados para streaming/websocket
        
        Returns:
            Dicionário com snapshot e insights recentes
        """
        snapshot = self.get_current_snapshot()
        recent_insights = self.get_insights(limit=10, unacknowledged_only=True)
        
        return {
            'snapshot': snapshot.to_dict(),
            'insights': [i.to_dict() for i in recent_insights],
            'last_updated': datetime.utcnow().isoformat(),
            'refresh_interval_ms': self._config.refresh_interval_seconds * 1000
        }
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        snapshot = self.get_current_snapshot()
        return {
            'service': 'realtime_insights',
            'period_days': period_days,
            'total_cost': snapshot.total_cost_mtd,
            'today_cost': snapshot.total_cost_today,
            'projected_monthly': snapshot.projected_monthly,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        snapshot = self.get_current_snapshot()
        return {
            'service': 'realtime_insights',
            'hourly_rate': snapshot.hourly_rate,
            'vs_yesterday': snapshot.vs_yesterday,
            'active_alerts': snapshot.active_alerts,
            'total_insights': len(self._insights)
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações baseadas em insights"""
        recommendations = []
        
        critical_count = len([i for i in self._insights 
                            if i.severity == InsightSeverity.CRITICAL and not i.acknowledged])
        if critical_count > 0:
            recommendations.append({
                'type': 'CRITICAL_ALERTS',
                'priority': 'HIGH',
                'title': f'{critical_count} alertas críticos não reconhecidos',
                'description': 'Alertas críticos requerem atenção imediata',
                'action': 'Revisar e reconhecer alertas críticos'
            })
        
        snapshot = self.get_current_snapshot()
        if snapshot.vs_yesterday > 30:
            recommendations.append({
                'type': 'COST_INCREASE',
                'priority': 'MEDIUM',
                'title': f'Custos {snapshot.vs_yesterday:.1f}% maiores que ontem',
                'description': 'Investigue a causa do aumento de custos',
                'action': 'Analisar top serviços e recursos recém-criados'
            })
        
        return recommendations
