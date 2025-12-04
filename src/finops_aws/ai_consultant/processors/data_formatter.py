"""
Data Formatter

Formata dados de custo FinOps para consumo pelo Amazon Q Business.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class FormattedCostData:
    """Dados de custo formatados para Q Business"""
    period: Dict[str, str]
    summary: Dict[str, Any]
    services: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    trends: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "summary": self.summary,
            "services": self.services,
            "recommendations": self.recommendations,
            "anomalies": self.anomalies,
            "trends": self.trends,
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str, ensure_ascii=False)


class DataFormatter:
    """
    Formatador de dados para Amazon Q Business
    
    Transforma dados brutos do FinOps em formato estruturado
    otimizado para consumo pelo Q Business.
    
    Example:
        ```python
        formatter = DataFormatter()
        
        formatted = formatter.format_cost_report(raw_report)
        prompt_data = formatted.to_json()
        ```
    """
    
    def __init__(self, currency: str = "USD", language: str = "pt-BR"):
        """
        Inicializa formatador
        
        Args:
            currency: Moeda para valores
            language: Idioma para formatação
        """
        self.currency = currency
        self.language = language
    
    def format_cost_report(
        self,
        report: Dict[str, Any],
        period_days: int = 30,
        top_services: int = 10,
        max_recommendations: int = 20
    ) -> FormattedCostData:
        """
        Formata relatório de custo completo
        
        Args:
            report: Relatório bruto do FinOps
            period_days: Dias do período
            top_services: Número de top serviços
            max_recommendations: Máximo de recomendações
            
        Returns:
            FormattedCostData estruturado
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=period_days)
        
        period = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days": period_days,
            "description": f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
        }
        
        summary = self._format_summary(report)
        services = self._format_services(report, top_services)
        recommendations = self._format_recommendations(report, max_recommendations)
        anomalies = self._format_anomalies(report)
        trends = self._format_trends(report)
        
        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "currency": self.currency,
            "language": self.language,
            "data_version": "2.0",
            "source": "finops-aws"
        }
        
        return FormattedCostData(
            period=period,
            summary=summary,
            services=services,
            recommendations=recommendations,
            anomalies=anomalies,
            trends=trends,
            metadata=metadata
        )
    
    def _format_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Formata resumo de custos"""
        total_cost = report.get('total_cost', 0)
        if isinstance(total_cost, dict):
            total_cost = total_cost.get('amount', 0)
        
        previous_cost = report.get('previous_period_cost', total_cost)
        change = ((total_cost - previous_cost) / previous_cost * 100) if previous_cost > 0 else 0
        
        services = report.get('services', [])
        if isinstance(services, list):
            service_count = len(services)
        elif isinstance(services, dict):
            service_count = len(services.get('items', services.get('list', [])))
        else:
            service_count = 0
        
        resources = report.get('resources', {})
        if isinstance(resources, dict):
            resource_count = resources.get('total', 0)
        elif isinstance(resources, list):
            resource_count = len(resources)
        else:
            resource_count = 0
        
        return {
            "total_cost": round(float(total_cost), 2),
            "previous_period_cost": round(float(previous_cost), 2),
            "change_amount": round(float(total_cost - previous_cost), 2),
            "change_percentage": round(float(change), 2),
            "currency": self.currency,
            "service_count": service_count,
            "resource_count": resource_count,
            "daily_average": round(float(total_cost) / 30, 2) if total_cost else 0,
            "trend": "INCREASING" if change > 5 else ("DECREASING" if change < -5 else "STABLE")
        }
    
    def _format_services(
        self,
        report: Dict[str, Any],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Formata lista de serviços"""
        services = report.get('services', [])
        
        if isinstance(services, dict):
            services = services.get('items', services.get('list', []))
        
        if not isinstance(services, list):
            return []
        
        formatted = []
        for svc in services:
            if isinstance(svc, dict):
                cost = svc.get('cost', svc.get('total_cost', 0))
                if isinstance(cost, dict):
                    cost = cost.get('amount', 0)
                
                formatted.append({
                    "name": svc.get('name', svc.get('service_name', 'Unknown')),
                    "cost": round(float(cost), 2),
                    "percentage": svc.get('percentage', 0),
                    "resource_count": svc.get('resource_count', 0),
                    "trend": svc.get('trend', 'STABLE'),
                    "utilization": svc.get('utilization', None),
                    "region": svc.get('region', 'global')
                })
        
        formatted.sort(key=lambda x: x['cost'], reverse=True)
        
        total = sum(s['cost'] for s in formatted)
        for s in formatted:
            s['percentage'] = round((s['cost'] / total * 100) if total > 0 else 0, 2)
        
        return formatted[:top_n]
    
    def _format_recommendations(
        self,
        report: Dict[str, Any],
        max_n: int
    ) -> List[Dict[str, Any]]:
        """Formata recomendações de otimização"""
        recommendations = report.get('recommendations', [])
        
        if isinstance(recommendations, dict):
            recommendations = recommendations.get('items', [])
        
        if not isinstance(recommendations, list):
            return []
        
        formatted = []
        for rec in recommendations[:max_n]:
            if isinstance(rec, dict):
                savings = rec.get('estimated_savings', rec.get('savings', 0))
                if isinstance(savings, dict):
                    savings = savings.get('amount', 0)
                
                formatted.append({
                    "type": rec.get('recommendation_type', rec.get('type', 'GENERAL')),
                    "title": rec.get('title', rec.get('description', '')[:50]),
                    "description": rec.get('description', ''),
                    "estimated_savings_monthly": round(float(savings), 2),
                    "estimated_savings_annual": round(float(savings) * 12, 2),
                    "priority": rec.get('priority', 'MEDIUM'),
                    "effort": rec.get('implementation_effort', rec.get('effort', 'MEDIUM')),
                    "resource_id": rec.get('resource_id', ''),
                    "resource_type": rec.get('resource_type', ''),
                    "action": rec.get('action', '')
                })
        
        formatted.sort(key=lambda x: x['estimated_savings_monthly'], reverse=True)
        
        return formatted
    
    def _format_anomalies(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Formata anomalias detectadas"""
        anomalies = report.get('anomalies', [])
        
        if isinstance(anomalies, dict):
            anomalies = anomalies.get('items', [])
        
        if not isinstance(anomalies, list):
            return []
        
        formatted = []
        for anomaly in anomalies[:10]:
            if isinstance(anomaly, dict):
                formatted.append({
                    "type": anomaly.get('anomaly_type', anomaly.get('type', 'COST_SPIKE')),
                    "service": anomaly.get('service', ''),
                    "description": anomaly.get('description', ''),
                    "impact": anomaly.get('impact', 0),
                    "detected_at": anomaly.get('detected_at', ''),
                    "severity": anomaly.get('severity', 'MEDIUM'),
                    "root_cause": anomaly.get('root_cause', ''),
                    "status": anomaly.get('status', 'OPEN')
                })
        
        return formatted
    
    def _format_trends(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Formata tendências de custo"""
        trends = report.get('trends', {})
        forecasts = report.get('forecasts', {})
        
        daily_costs = trends.get('daily_costs', [])
        if isinstance(daily_costs, list) and daily_costs:
            weekly_trend = self._calculate_trend(daily_costs[-7:]) if len(daily_costs) >= 7 else 0
            monthly_trend = self._calculate_trend(daily_costs) if len(daily_costs) >= 14 else 0
        else:
            weekly_trend = 0
            monthly_trend = 0
        
        return {
            "weekly_change_percentage": round(weekly_trend, 2),
            "monthly_change_percentage": round(monthly_trend, 2),
            "direction": "UP" if monthly_trend > 0 else ("DOWN" if monthly_trend < 0 else "STABLE"),
            "forecast_next_month": forecasts.get('next_month', 0),
            "forecast_confidence": forecasts.get('confidence', 'MEDIUM'),
            "seasonality": trends.get('seasonality', 'NONE'),
            "daily_costs": daily_costs[-30:] if isinstance(daily_costs, list) else []
        }
    
    def _calculate_trend(self, costs: List[Any]) -> float:
        """Calcula tendência de uma série de custos"""
        if not costs or len(costs) < 2:
            return 0
        
        values = []
        for c in costs:
            if isinstance(c, dict):
                values.append(float(c.get('cost', c.get('amount', 0))))
            else:
                values.append(float(c))
        
        if not values or len(values) < 2:
            return 0
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if first_half == 0:
            return 0
        
        return ((second_half - first_half) / first_half) * 100
    
    def format_for_comparison(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Formata dados para comparação entre períodos
        
        Args:
            current: Dados do período atual
            previous: Dados do período anterior
            
        Returns:
            Dict com dados formatados para comparação
        """
        current_formatted = self.format_cost_report(current)
        previous_formatted = self.format_cost_report(previous)
        
        current_services = {s['name']: s for s in current_formatted.services}
        previous_services = {s['name']: s for s in previous_formatted.services}
        
        all_services = set(current_services.keys()) | set(previous_services.keys())
        
        comparison = []
        for name in all_services:
            curr = current_services.get(name, {'cost': 0})
            prev = previous_services.get(name, {'cost': 0})
            
            delta = curr['cost'] - prev['cost']
            delta_pct = ((delta / prev['cost']) * 100) if prev['cost'] > 0 else 0
            
            comparison.append({
                "service": name,
                "current_cost": curr['cost'],
                "previous_cost": prev['cost'],
                "delta_amount": round(delta, 2),
                "delta_percentage": round(delta_pct, 2)
            })
        
        comparison.sort(key=lambda x: abs(x['delta_amount']), reverse=True)
        
        return {
            "current_period": current_formatted.to_dict(),
            "previous_period": previous_formatted.to_dict(),
            "service_comparison": comparison[:20],
            "total_delta": round(
                current_formatted.summary['total_cost'] - 
                previous_formatted.summary['total_cost'], 
                2
            )
        }
