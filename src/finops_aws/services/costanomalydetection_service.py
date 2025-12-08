"""
FinOps AWS - Cost Anomaly Detection Service
Análise de anomalias de custos usando AWS Cost Anomaly Detection

Integração REAL com AWS Cost Anomaly Detection API:
- Lista monitores de anomalias
- Obtém anomalias detectadas
- Analisa severidade e impacto
- Gera recomendações de investigação

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Template Method: Fluxo padrão de análise
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger


class AnomalySeverity(Enum):
    """Níveis de severidade de anomalia"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class CostAnomaly:
    """Representa uma anomalia de custo detectada"""
    anomaly_id: str
    anomaly_start_date: Optional[datetime] = None
    anomaly_end_date: Optional[datetime] = None
    dimension_value: str = ""
    root_cause_service: str = ""
    root_cause_region: str = ""
    root_cause_linked_account: str = ""
    root_cause_usage_type: str = ""
    expected_spend: float = 0.0
    actual_spend: float = 0.0
    total_impact: float = 0.0
    impact_percentage: float = 0.0
    severity: str = "MEDIUM"
    status: str = "OPEN"
    feedback: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_start_date': self.anomaly_start_date.isoformat() if self.anomaly_start_date else None,
            'anomaly_end_date': self.anomaly_end_date.isoformat() if self.anomaly_end_date else None,
            'dimension_value': self.dimension_value,
            'root_cause': {
                'service': self.root_cause_service,
                'region': self.root_cause_region,
                'linked_account': self.root_cause_linked_account,
                'usage_type': self.root_cause_usage_type
            },
            'expected_spend': self.expected_spend,
            'actual_spend': self.actual_spend,
            'total_impact': self.total_impact,
            'impact_percentage': self.impact_percentage,
            'severity': self.severity,
            'status': self.status,
            'feedback': self.feedback
        }


@dataclass
class AnomalyMonitor:
    """Representa um monitor de anomalias"""
    monitor_arn: str
    monitor_name: str
    monitor_type: str
    monitor_dimension: str = ""
    creation_date: Optional[datetime] = None
    last_evaluated_date: Optional[datetime] = None
    last_updated_date: Optional[datetime] = None
    status: str = "ACTIVE"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'monitor_arn': self.monitor_arn,
            'monitor_name': self.monitor_name,
            'monitor_type': self.monitor_type,
            'monitor_dimension': self.monitor_dimension,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_evaluated_date': self.last_evaluated_date.isoformat() if self.last_evaluated_date else None,
            'status': self.status
        }


class CostAnomalyDetectionService(BaseAWSService):
    """
    Serviço FinOps para AWS Cost Anomaly Detection
    
    Funcionalidades:
    - Lista monitores de anomalias
    - Obtém anomalias recentes
    - Analisa severidade e impacto
    - Identifica root causes
    - Gera recomendações de investigação
    
    AWS APIs utilizadas:
    - ce:GetAnomalies
    - ce:GetAnomalyMonitors
    - ce:GetAnomalySubscriptions
    """
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "costanomalydetection"
    
    def _get_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce')
        return boto3.client('ce', region_name='us-east-1')
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        try:
            client = self._get_client()
            client.get_anomaly_monitors(MaxResults=1)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão para acessar Cost Anomaly Detection")
            return False
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            return False
    
    def get_anomaly_monitors(self) -> List[AnomalyMonitor]:
        """Obtém todos os monitores de anomalias"""
        monitors = []
        try:
            client = self._get_client()
            
            next_token = None
            while True:
                params = {'MaxResults': 100}
                if next_token:
                    params['NextPageToken'] = next_token
                
                response = client.get_anomaly_monitors(**params)
                
                for monitor in response.get('AnomalyMonitors', []):
                    parsed = self._parse_monitor(monitor)
                    monitors.append(parsed)
                
                next_token = response.get('NextPageToken')
                if not next_token:
                    break
            
            self.logger.info(f"Encontrados {len(monitors)} monitores de anomalias")
            return monitors
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: ce:GetAnomalyMonitors")
            else:
                self.logger.error(f"Erro ao listar monitores: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter monitores: {e}")
            return []
    
    def _parse_monitor(self, monitor: Dict) -> AnomalyMonitor:
        """Parse de um monitor de anomalias"""
        creation_date = None
        last_evaluated = None
        last_updated = None
        
        if 'CreationDate' in monitor:
            try:
                creation_date = datetime.fromisoformat(str(monitor['CreationDate']).replace('Z', '+00:00'))
            except Exception:
                pass
        
        if 'LastEvaluatedDate' in monitor:
            try:
                last_evaluated = datetime.fromisoformat(str(monitor['LastEvaluatedDate']).replace('Z', '+00:00'))
            except Exception:
                pass
        
        if 'LastUpdatedDate' in monitor:
            try:
                last_updated = datetime.fromisoformat(str(monitor['LastUpdatedDate']).replace('Z', '+00:00'))
            except Exception:
                pass
        
        spec = monitor.get('MonitorSpecification', {})
        dimension = ""
        if 'Dimensions' in spec:
            dimension = spec['Dimensions'].get('Key', '')
        
        return AnomalyMonitor(
            monitor_arn=monitor.get('MonitorArn', ''),
            monitor_name=monitor.get('MonitorName', ''),
            monitor_type=monitor.get('MonitorType', ''),
            monitor_dimension=dimension,
            creation_date=creation_date,
            last_evaluated_date=last_evaluated,
            last_updated_date=last_updated,
            status='ACTIVE'
        )
    
    def get_anomalies(self, days_back: int = 90) -> List[CostAnomaly]:
        """Obtém anomalias detectadas nos últimos N dias"""
        anomalies = []
        try:
            client = self._get_client()
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            next_token = None
            while True:
                params = {
                    'DateInterval': {
                        'StartDate': start_date,
                        'EndDate': end_date
                    },
                    'MaxResults': 100
                }
                if next_token:
                    params['NextPageToken'] = next_token
                
                response = client.get_anomalies(**params)
                
                for anomaly in response.get('Anomalies', []):
                    parsed = self._parse_anomaly(anomaly)
                    anomalies.append(parsed)
                
                next_token = response.get('NextPageToken')
                if not next_token:
                    break
            
            self.logger.info(f"Encontradas {len(anomalies)} anomalias nos últimos {days_back} dias")
            return anomalies
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.logger.warning("Sem permissão: ce:GetAnomalies")
            else:
                self.logger.error(f"Erro ao obter anomalias: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter anomalias: {e}")
            return []
    
    def _parse_anomaly(self, anomaly: Dict) -> CostAnomaly:
        """Parse de uma anomalia"""
        anomaly_id = anomaly.get('AnomalyId', '')
        
        start_date = None
        end_date = None
        if 'AnomalyStartDate' in anomaly:
            try:
                start_date = datetime.fromisoformat(str(anomaly['AnomalyStartDate']).replace('Z', '+00:00'))
            except Exception:
                pass
        if 'AnomalyEndDate' in anomaly:
            try:
                end_date = datetime.fromisoformat(str(anomaly['AnomalyEndDate']).replace('Z', '+00:00'))
            except Exception:
                pass
        
        impact = anomaly.get('Impact', {})
        max_impact = float(impact.get('MaxImpact', 0))
        total_impact = float(impact.get('TotalImpact', max_impact))
        total_actual = float(impact.get('TotalActualSpend', 0))
        total_expected = float(impact.get('TotalExpectedSpend', 0))
        impact_pct = float(impact.get('TotalImpactPercentage', 0))
        
        root_causes = anomaly.get('RootCauses', [])
        root_service = ""
        root_region = ""
        root_account = ""
        root_usage = ""
        
        if root_causes:
            rc = root_causes[0]
            root_service = rc.get('Service', '')
            root_region = rc.get('Region', '')
            root_account = rc.get('LinkedAccount', '')
            root_usage = rc.get('UsageType', '')
        
        if total_impact >= 1000:
            severity = "CRITICAL"
        elif total_impact >= 500:
            severity = "HIGH"
        elif total_impact >= 100:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        dimension_value = anomaly.get('DimensionValue', '')
        feedback = anomaly.get('Feedback', '')
        status = "OPEN" if not feedback else "REVIEWED"
        
        return CostAnomaly(
            anomaly_id=anomaly_id,
            anomaly_start_date=start_date,
            anomaly_end_date=end_date,
            dimension_value=dimension_value,
            root_cause_service=root_service,
            root_cause_region=root_region,
            root_cause_linked_account=root_account,
            root_cause_usage_type=root_usage,
            expected_spend=total_expected,
            actual_spend=total_actual,
            total_impact=total_impact,
            impact_percentage=impact_pct,
            severity=severity,
            status=status,
            feedback=feedback
        )
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Obtém anomalias como recursos"""
        anomalies = self.get_anomalies(days_back=90)
        return [a.to_dict() for a in anomalies]
    
    def get_costs(self, period_days: int = 30) -> ServiceCost:
        """Obtém resumo de impacto das anomalias"""
        anomalies = self.get_anomalies(days_back=period_days)
        
        total_impact = sum(a.total_impact for a in anomalies)
        critical_count = len([a for a in anomalies if a.severity == 'CRITICAL'])
        
        cost_by_resource: Dict[str, float] = {}
        for a in anomalies:
            if a.root_cause_service:
                cost_by_resource[a.root_cause_service] = cost_by_resource.get(a.root_cause_service, 0) + a.total_impact
        
        trend = "INCREASING" if critical_count > 0 else "STABLE"
        
        return ServiceCost(
            service_name='costanomalydetection',
            total_cost=round(total_impact, 2),
            period_days=period_days,
            cost_by_resource={k: round(v, 2) for k, v in sorted(cost_by_resource.items(), key=lambda x: -x[1])[:10]},
            trend=trend,
            currency='USD'
        )
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de anomalias"""
        monitors = self.get_anomaly_monitors()
        anomalies = self.get_anomalies(days_back=90)
        
        severity_counts = {
            'CRITICAL': len([a for a in anomalies if a.severity == 'CRITICAL']),
            'HIGH': len([a for a in anomalies if a.severity == 'HIGH']),
            'MEDIUM': len([a for a in anomalies if a.severity == 'MEDIUM']),
            'LOW': len([a for a in anomalies if a.severity == 'LOW'])
        }
        
        open_count = len([a for a in anomalies if a.status == 'OPEN'])
        reviewed_count = len([a for a in anomalies if a.status == 'REVIEWED'])
        
        return ServiceMetrics(
            service_name='costanomalydetection',
            resource_count=len(anomalies),
            metrics={
                'monitor_count': len(monitors),
                'anomaly_count_90d': len(anomalies),
                'open_anomalies': open_count,
                'reviewed_anomalies': reviewed_count,
                'by_severity': severity_counts,
                'avg_impact': round(sum(a.total_impact for a in anomalies) / len(anomalies), 2) if anomalies else 0
            },
            utilization=None
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações baseadas em anomalias detectadas"""
        recommendations: List[ServiceRecommendation] = []
        monitors = self.get_anomaly_monitors()
        anomalies = self.get_anomalies(days_back=30)
        
        if not monitors:
            recommendations.append(ServiceRecommendation(
                resource_id='account',
                resource_type='anomaly',
                recommendation_type='NO_MONITORS',
                description=(
                    'A conta AWS não possui monitores de anomalias configurados. '
                    'Cost Anomaly Detection é gratuito e essencial para detectar '
                    'picos de custo inesperados. Configure pelo menos um monitor '
                    'para SERVICE_DIMENSION ou LINKED_ACCOUNT.'
                ),
                estimated_savings=0,
                priority='HIGH',
                title='Nenhum monitor de anomalias configurado',
                action='Criar monitor de anomalias no Console AWS ou via API'
            ))
        
        critical_anomalies = [a for a in anomalies if a.severity == 'CRITICAL']
        for anomaly in critical_anomalies:
            recommendations.append(ServiceRecommendation(
                resource_id=anomaly.anomaly_id,
                resource_type='anomaly',
                recommendation_type='CRITICAL_ANOMALY',
                description=(
                    f'Anomalia crítica detectada com impacto de ${anomaly.total_impact:,.2f}. '
                    f'Serviço: {anomaly.root_cause_service or "N/A"}, '
                    f'Região: {anomaly.root_cause_region or "N/A"}. '
                    f'Esperado: ${anomaly.expected_spend:,.2f}, '
                    f'Real: ${anomaly.actual_spend:,.2f} (+{anomaly.impact_percentage:.1f}%). '
                    f'Investigação imediata necessária.'
                ),
                estimated_savings=anomaly.total_impact,
                priority='CRITICAL',
                title=f'Anomalia CRÍTICA: ${anomaly.total_impact:,.2f} de impacto',
                action=f'Investigar serviço {anomaly.root_cause_service} na região {anomaly.root_cause_region}'
            ))
        
        high_anomalies = [a for a in anomalies if a.severity == 'HIGH']
        for anomaly in high_anomalies[:5]:
            recommendations.append(ServiceRecommendation(
                resource_id=anomaly.anomaly_id,
                resource_type='anomaly',
                recommendation_type='HIGH_ANOMALY',
                description=(
                    f'Anomalia de alta severidade com impacto de ${anomaly.total_impact:,.2f}. '
                    f'Serviço: {anomaly.root_cause_service or "N/A"}. '
                    f'Aumento de {anomaly.impact_percentage:.1f}% sobre o esperado.'
                ),
                estimated_savings=anomaly.total_impact,
                priority='HIGH',
                title=f'Anomalia ALTA: ${anomaly.total_impact:,.2f} de impacto',
                action=f'Revisar uso do serviço {anomaly.root_cause_service}'
            ))
        
        service_impacts: Dict[str, float] = {}
        for a in anomalies:
            if a.root_cause_service:
                service_impacts[a.root_cause_service] = service_impacts.get(a.root_cause_service, 0) + a.total_impact
        
        for service, impact in sorted(service_impacts.items(), key=lambda x: -x[1])[:3]:
            if impact > 100:
                recommendations.append(ServiceRecommendation(
                    resource_id=service,
                    resource_type='anomaly',
                    recommendation_type='SERVICE_ANOMALY_PATTERN',
                    description=(
                        f'O serviço {service} apresenta padrão recorrente de anomalias '
                        f'com impacto total de ${impact:,.2f} nos últimos 30 dias. '
                        f'Considere revisar configurações e uso deste serviço.'
                    ),
                    estimated_savings=impact,
                    priority='MEDIUM',
                    title=f'Padrão de anomalias em {service}',
                    action=f'Analisar padrões de uso e configuração de {service}'
                ))
        
        return recommendations
    
    def analyze_usage(self) -> Dict[str, Any]:
        """Analisa padrões de anomalias"""
        monitors = self.get_anomaly_monitors()
        anomalies = self.get_anomalies(days_back=90)
        costs = self.get_costs(period_days=30)
        recommendations = self.get_recommendations()
        
        by_service: Dict[str, int] = {}
        by_region: Dict[str, int] = {}
        for a in anomalies:
            if a.root_cause_service:
                by_service[a.root_cause_service] = by_service.get(a.root_cause_service, 0) + 1
            if a.root_cause_region:
                by_region[a.root_cause_region] = by_region.get(a.root_cause_region, 0) + 1
        
        return {
            'service': 'costanomalydetection',
            'summary': {
                'monitor_count': len(monitors),
                'anomaly_count_90d': len(anomalies),
                'total_impact_30d': costs.cost_by_resource.get('total_anomaly_impact', 0),
                'critical_count': costs.cost_by_resource.get('critical_anomalies', 0),
                'high_count': costs.cost_by_resource.get('high_anomalies', 0)
            },
            'anomalies_by_service': dict(sorted(by_service.items(), key=lambda x: -x[1])[:10]),
            'anomalies_by_region': dict(sorted(by_region.items(), key=lambda x: -x[1])[:10]),
            'recommendations_count': len(recommendations),
            'optimization_opportunities': [r.title for r in recommendations[:5]]
        }
