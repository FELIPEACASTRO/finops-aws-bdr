"""
FinOps AWS - FinOps Maturity Assessment Service
Serviço de Avaliação de Maturidade FinOps

Este serviço implementa:
- Avaliação dos 4 níveis de maturidade FinOps
- Scorecards por capability
- Roadmap de melhoria
- Culture artifacts e OKRs

Design Patterns:
- Strategy: Diferentes avaliadores por capability
- Builder: Construção de assessments
- Observer: Notificação de mudanças em maturidade
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class MaturityLevel(Enum):
    """Níveis de maturidade FinOps"""
    CRAWL = "crawl"
    WALK = "walk"
    RUN = "run"
    FLY = "fly"


class CapabilityDomain(Enum):
    """Domínios de capability FinOps"""
    UNDERSTAND = "understand"
    QUANTIFY = "quantify"
    OPTIMIZE = "optimize"
    OPERATE = "operate"


@dataclass
class CapabilityAssessment:
    """Avaliação de uma capability"""
    capability_id: str
    capability_name: str
    domain: CapabilityDomain
    current_level: MaturityLevel
    target_level: MaturityLevel
    score: float
    max_score: float
    evidence: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'capability_id': self.capability_id,
            'capability_name': self.capability_name,
            'domain': self.domain.value,
            'current_level': self.current_level.value,
            'target_level': self.target_level.value,
            'score': round(self.score, 2),
            'max_score': self.max_score,
            'percentage': round((self.score / self.max_score * 100) if self.max_score > 0 else 0, 2),
            'evidence': self.evidence,
            'gaps': self.gaps,
            'recommendations': self.recommendations
        }


@dataclass
class DomainScore:
    """Score agregado por domínio"""
    domain: CapabilityDomain
    total_score: float
    max_score: float
    capabilities_count: int
    maturity_level: MaturityLevel
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'domain': self.domain.value,
            'total_score': round(self.total_score, 2),
            'max_score': self.max_score,
            'percentage': round((self.total_score / self.max_score * 100) if self.max_score > 0 else 0, 2),
            'capabilities_count': self.capabilities_count,
            'maturity_level': self.maturity_level.value
        }


@dataclass
class MaturityAssessment:
    """Avaliação completa de maturidade"""
    assessment_id: str
    assessed_at: datetime
    overall_score: float
    max_score: float
    overall_level: MaturityLevel
    level_percentages: Dict[str, float]
    domain_scores: List[DomainScore]
    capabilities: List[CapabilityAssessment]
    top_gaps: List[Dict[str, Any]]
    roadmap: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'assessment_id': self.assessment_id,
            'assessed_at': self.assessed_at.isoformat(),
            'overall': {
                'score': round(self.overall_score, 2),
                'max_score': self.max_score,
                'percentage': round((self.overall_score / self.max_score * 100) if self.max_score > 0 else 0, 2),
                'level': self.overall_level.value
            },
            'level_percentages': {k: round(v, 2) for k, v in self.level_percentages.items()},
            'domain_scores': [d.to_dict() for d in self.domain_scores],
            'capabilities': [c.to_dict() for c in self.capabilities],
            'top_gaps': self.top_gaps,
            'roadmap': self.roadmap
        }


@dataclass
class FinOpsOKR:
    """OKR FinOps"""
    okr_id: str
    objective: str
    key_results: List[Dict[str, Any]]
    owner: str
    quarter: str
    status: str
    progress: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'okr_id': self.okr_id,
            'objective': self.objective,
            'key_results': self.key_results,
            'owner': self.owner,
            'quarter': self.quarter,
            'status': self.status,
            'progress': round(self.progress, 2)
        }


class FinOpsMaturityService(BaseAWSService):
    """
    Serviço de Avaliação de Maturidade FinOps
    
    Funcionalidades:
    - Avalia maturidade em 4 níveis (Crawl, Walk, Run, Fly)
    - Analisa capabilities por domínio
    - Gera roadmap de melhoria
    - Gerencia OKRs e scorecards
    
    Capabilities avaliadas:
    - Cost Allocation
    - Showback/Chargeback
    - Budgets & Forecasting
    - Anomaly Detection
    - Commitments (RI/SP)
    - Rightsizing
    - Automation
    - Unit Economics
    """
    
    FINOPS_CAPABILITIES = [
        ("cost_visibility", "Cost Visibility", CapabilityDomain.UNDERSTAND),
        ("cost_allocation", "Cost Allocation", CapabilityDomain.QUANTIFY),
        ("showback", "Showback/Chargeback", CapabilityDomain.QUANTIFY),
        ("budgets", "Budgets & Forecasting", CapabilityDomain.QUANTIFY),
        ("anomaly_detection", "Anomaly Detection", CapabilityDomain.UNDERSTAND),
        ("tag_governance", "Tag Governance", CapabilityDomain.OPERATE),
        ("commitments", "Commitments (RI/SP)", CapabilityDomain.OPTIMIZE),
        ("rightsizing", "Rightsizing", CapabilityDomain.OPTIMIZE),
        ("idle_resources", "Idle Resource Management", CapabilityDomain.OPTIMIZE),
        ("automation", "Policy Automation", CapabilityDomain.OPERATE),
        ("unit_economics", "Unit Economics", CapabilityDomain.QUANTIFY),
        ("realtime_insights", "Real-Time Insights", CapabilityDomain.UNDERSTAND),
        ("predictive_optimization", "Predictive Optimization", CapabilityDomain.OPTIMIZE),
        ("finops_culture", "FinOps Culture & Training", CapabilityDomain.OPERATE)
    ]
    
    LEVEL_THRESHOLDS = {
        MaturityLevel.CRAWL: 25,
        MaturityLevel.WALK: 50,
        MaturityLevel.RUN: 75,
        MaturityLevel.FLY: 90
    }
    
    def __init__(self, client_factory=None, services_status: Dict[str, bool] = None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "finops_maturity"
        self._cache = FinOpsCache(default_ttl=3600)
        self._services_status = services_status or {}
        self._okrs: List[FinOpsOKR] = []
        self._load_default_okrs()
    
    def _load_default_okrs(self):
        """Carrega OKRs padrão"""
        current_quarter = f"Q{((datetime.utcnow().month - 1) // 3) + 1} {datetime.utcnow().year}"
        
        self._okrs = [
            FinOpsOKR(
                okr_id="okr_cost_visibility",
                objective="Atingir visibilidade completa de custos AWS",
                key_results=[
                    {"kr": "100% dos recursos com tags obrigatórias", "target": 100, "current": 0, "unit": "%"},
                    {"kr": "Dashboard atualizado em tempo real (<5min)", "target": 5, "current": 300, "unit": "min"},
                    {"kr": "Relatórios automáticos semanais", "target": 4, "current": 0, "unit": "reports/month"}
                ],
                owner="FinOps Team",
                quarter=current_quarter,
                status="in_progress",
                progress=0
            ),
            FinOpsOKR(
                okr_id="okr_cost_optimization",
                objective="Reduzir custos AWS em 20% YoY",
                key_results=[
                    {"kr": "Implementar Savings Plans com 80% coverage", "target": 80, "current": 0, "unit": "%"},
                    {"kr": "Eliminar recursos ociosos", "target": 0, "current": 0, "unit": "resources"},
                    {"kr": "Rightsizing em 100% das recomendações", "target": 100, "current": 0, "unit": "%"}
                ],
                owner="Cloud Team",
                quarter=current_quarter,
                status="in_progress",
                progress=0
            ),
            FinOpsOKR(
                okr_id="okr_automation",
                objective="Automatizar 80% das ações de otimização",
                key_results=[
                    {"kr": "Políticas de automação ativas", "target": 10, "current": 4, "unit": "policies"},
                    {"kr": "Ações automáticas por mês", "target": 50, "current": 0, "unit": "actions"},
                    {"kr": "Tempo de resposta a anomalias", "target": 15, "current": 60, "unit": "min"}
                ],
                owner="Platform Team",
                quarter=current_quarter,
                status="in_progress",
                progress=40
            )
        ]
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço"""
        return True
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Retorna capabilities e OKRs"""
        return {
            'capabilities_count': len(self.FINOPS_CAPABILITIES),
            'okrs': [okr.to_dict() for okr in self._okrs]
        }
    
    def set_services_status(self, status: Dict[str, bool]):
        """Define status dos serviços para avaliação"""
        self._services_status = status
    
    def assess_maturity(self) -> MaturityAssessment:
        """
        Realiza avaliação completa de maturidade FinOps
        
        Returns:
            MaturityAssessment com scores e roadmap
        """
        cache_key = "maturity_assessment"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        capabilities = []
        for cap_id, cap_name, domain in self.FINOPS_CAPABILITIES:
            assessment = self._assess_capability(cap_id, cap_name, domain)
            capabilities.append(assessment)
        
        domain_scores = self._calculate_domain_scores(capabilities)
        
        overall_score = sum(c.score for c in capabilities)
        max_score = sum(c.max_score for c in capabilities)
        overall_percentage = (overall_score / max_score * 100) if max_score > 0 else 0
        
        overall_level = self._determine_level(overall_percentage)
        
        level_percentages = {
            'crawl': min(100, overall_percentage / 25 * 100),
            'walk': min(100, max(0, (overall_percentage - 25) / 25 * 100)),
            'run': min(100, max(0, (overall_percentage - 50) / 25 * 100)),
            'fly': min(100, max(0, (overall_percentage - 75) / 25 * 100))
        }
        
        top_gaps = self._identify_top_gaps(capabilities)
        roadmap = self._generate_roadmap(capabilities, overall_level)
        
        assessment = MaturityAssessment(
            assessment_id=f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            assessed_at=datetime.utcnow(),
            overall_score=overall_score,
            max_score=max_score,
            overall_level=overall_level,
            level_percentages=level_percentages,
            domain_scores=domain_scores,
            capabilities=capabilities,
            top_gaps=top_gaps,
            roadmap=roadmap
        )
        
        self._cache.set(cache_key, assessment, ttl=3600)
        return assessment
    
    def _assess_capability(
        self,
        cap_id: str,
        cap_name: str,
        domain: CapabilityDomain
    ) -> CapabilityAssessment:
        """Avalia uma capability específica"""
        max_score = 100
        score = 0
        evidence = []
        gaps = []
        recommendations = []
        
        if cap_id == "cost_visibility":
            if self._services_status.get('cost_explorer', True):
                score += 30
                evidence.append("Cost Explorer integrado")
            else:
                gaps.append("Cost Explorer não configurado")
                recommendations.append("Configurar integração com Cost Explorer")
            
            if self._services_status.get('cur_ingestion', False):
                score += 40
                evidence.append("CUR ingestion configurado")
            else:
                gaps.append("CUR não configurado")
                recommendations.append("Implementar ingestão de CUR via S3/Athena")
            
            if self._services_status.get('realtime_insights', False):
                score += 30
                evidence.append("Insights em tempo real ativos")
            else:
                gaps.append("Sem insights em tempo real")
                recommendations.append("Habilitar Real-Time Insights Service")
        
        elif cap_id == "cost_allocation":
            if self._services_status.get('tag_governance', True):
                score += 40
                evidence.append("Tag Governance implementado")
            else:
                gaps.append("Sem governança de tags")
            
            if self._services_status.get('cost_allocation', False):
                score += 60
                evidence.append("Cost Allocation Engine ativo")
            else:
                gaps.append("Sem engine de alocação")
                recommendations.append("Implementar Cost Allocation Service")
        
        elif cap_id == "showback":
            if self._services_status.get('showback', False):
                score += 100
                evidence.append("Showback/Chargeback implementado")
            else:
                gaps.append("Sem showback/chargeback")
                recommendations.append("Implementar Showback/Chargeback Service")
        
        elif cap_id == "budgets":
            if self._services_status.get('budgets', True):
                score += 50
                evidence.append("AWS Budgets configurado")
            
            if self._services_status.get('forecasting', True):
                score += 50
                evidence.append("Forecasting implementado")
            else:
                gaps.append("Forecasting limitado")
        
        elif cap_id == "anomaly_detection":
            if self._services_status.get('anomaly_detection', True):
                score += 100
                evidence.append("Cost Anomaly Detection ativo")
            else:
                gaps.append("Sem detecção de anomalias")
        
        elif cap_id == "tag_governance":
            if self._services_status.get('tag_governance', True):
                score += 100
                evidence.append("Tag Governance Service implementado")
            else:
                gaps.append("Sem governança de tags")
        
        elif cap_id == "commitments":
            if self._services_status.get('savings_plans', True):
                score += 50
                evidence.append("Savings Plans monitorado")
            if self._services_status.get('reserved_instances', True):
                score += 50
                evidence.append("Reserved Instances monitorado")
        
        elif cap_id == "rightsizing":
            if self._services_status.get('compute_optimizer', True):
                score += 100
                evidence.append("Compute Optimizer integrado")
            else:
                gaps.append("Compute Optimizer não habilitado")
        
        elif cap_id == "idle_resources":
            if self._services_status.get('idle_detection', True):
                score += 100
                evidence.append("Detecção de recursos ociosos ativa")
            else:
                gaps.append("Sem detecção de recursos ociosos")
        
        elif cap_id == "automation":
            if self._services_status.get('policy_automation', False):
                score += 100
                evidence.append("Policy Automation Service ativo")
            else:
                gaps.append("Sem automação de políticas")
                recommendations.append("Implementar Policy Automation Service")
        
        elif cap_id == "unit_economics":
            if self._services_status.get('unit_economics', False):
                score += 100
                evidence.append("Unit Economics Service implementado")
            else:
                gaps.append("Sem unit economics")
                recommendations.append("Implementar Unit Economics Service")
        
        elif cap_id == "realtime_insights":
            if self._services_status.get('realtime_insights', False):
                score += 100
                evidence.append("Real-Time Insights ativo")
            else:
                gaps.append("Sem insights em tempo real")
                recommendations.append("Implementar Real-Time Insights Service")
        
        elif cap_id == "predictive_optimization":
            if self._services_status.get('predictive_optimization', False):
                score += 100
                evidence.append("Predictive Optimization ativo")
            else:
                gaps.append("Sem otimização preditiva")
                recommendations.append("Implementar Predictive Optimization Service")
        
        elif cap_id == "finops_culture":
            if len(self._okrs) > 0:
                score += 50
                evidence.append("OKRs FinOps definidos")
            
            if self._services_status.get('training', False):
                score += 50
                evidence.append("Programa de treinamento ativo")
            else:
                gaps.append("Sem programa de treinamento")
                recommendations.append("Estabelecer programa de treinamento FinOps")
        
        current_level = self._determine_level((score / max_score) * 100)
        target_level = MaturityLevel.FLY
        
        return CapabilityAssessment(
            capability_id=cap_id,
            capability_name=cap_name,
            domain=domain,
            current_level=current_level,
            target_level=target_level,
            score=score,
            max_score=max_score,
            evidence=evidence,
            gaps=gaps,
            recommendations=recommendations
        )
    
    def _determine_level(self, percentage: float) -> MaturityLevel:
        """Determina nível de maturidade baseado em porcentagem"""
        if percentage >= 90:
            return MaturityLevel.FLY
        elif percentage >= 75:
            return MaturityLevel.RUN
        elif percentage >= 50:
            return MaturityLevel.WALK
        else:
            return MaturityLevel.CRAWL
    
    def _calculate_domain_scores(
        self,
        capabilities: List[CapabilityAssessment]
    ) -> List[DomainScore]:
        """Calcula scores por domínio"""
        domain_data: Dict[CapabilityDomain, Tuple[float, float, int]] = {}
        
        for cap in capabilities:
            if cap.domain not in domain_data:
                domain_data[cap.domain] = (0, 0, 0)
            
            current = domain_data[cap.domain]
            domain_data[cap.domain] = (
                current[0] + cap.score,
                current[1] + cap.max_score,
                current[2] + 1
            )
        
        scores = []
        for domain, (total, max_score, count) in domain_data.items():
            percentage = (total / max_score * 100) if max_score > 0 else 0
            level = self._determine_level(percentage)
            
            scores.append(DomainScore(
                domain=domain,
                total_score=total,
                max_score=max_score,
                capabilities_count=count,
                maturity_level=level
            ))
        
        return scores
    
    def _identify_top_gaps(
        self,
        capabilities: List[CapabilityAssessment]
    ) -> List[Dict[str, Any]]:
        """Identifica principais gaps"""
        gaps = []
        
        for cap in capabilities:
            percentage = (cap.score / cap.max_score * 100) if cap.max_score > 0 else 0
            gap_size = 100 - percentage
            
            if gap_size > 0:
                gaps.append({
                    'capability': cap.capability_name,
                    'current_percentage': percentage,
                    'gap_percentage': gap_size,
                    'gaps': cap.gaps,
                    'recommendations': cap.recommendations
                })
        
        gaps.sort(key=lambda g: g['gap_percentage'], reverse=True)
        return gaps[:5]
    
    def _generate_roadmap(
        self,
        capabilities: List[CapabilityAssessment],
        current_level: MaturityLevel
    ) -> List[Dict[str, Any]]:
        """Gera roadmap de melhoria"""
        roadmap = []
        
        quick_wins = []
        for cap in capabilities:
            if cap.gaps and cap.score < 50:
                quick_wins.append({
                    'capability': cap.capability_name,
                    'action': cap.recommendations[0] if cap.recommendations else f"Melhorar {cap.capability_name}",
                    'impact': 'high' if cap.score < 25 else 'medium'
                })
        
        if quick_wins:
            roadmap.append({
                'phase': 1,
                'name': 'Quick Wins (Semanas 1-2)',
                'focus': 'Implementar melhorias rápidas de alto impacto',
                'items': quick_wins[:3]
            })
        
        roadmap.append({
            'phase': 2,
            'name': 'Core Capabilities (Semanas 3-6)',
            'focus': 'Fortalecer capabilities fundamentais',
            'items': [
                {'action': 'Implementar CUR ingestion completo', 'impact': 'high'},
                {'action': 'Configurar Cost Allocation Engine', 'impact': 'high'},
                {'action': 'Estabelecer Showback/Chargeback', 'impact': 'medium'}
            ]
        })
        
        roadmap.append({
            'phase': 3,
            'name': 'Advanced Optimization (Semanas 7-10)',
            'focus': 'Implementar automação e otimização avançada',
            'items': [
                {'action': 'Ativar Policy Automation', 'impact': 'high'},
                {'action': 'Implementar Unit Economics', 'impact': 'medium'},
                {'action': 'Configurar Real-Time Insights', 'impact': 'medium'}
            ]
        })
        
        roadmap.append({
            'phase': 4,
            'name': 'Excellence & Culture (Semanas 11-12)',
            'focus': 'Atingir excelência e estabelecer cultura FinOps',
            'items': [
                {'action': 'Implementar Predictive Optimization', 'impact': 'high'},
                {'action': 'Estabelecer programa de treinamento', 'impact': 'medium'},
                {'action': 'Criar scorecards e OKRs FinOps', 'impact': 'medium'}
            ]
        })
        
        return roadmap
    
    def get_okrs(self) -> List[FinOpsOKR]:
        """Retorna OKRs configurados"""
        return self._okrs
    
    def update_okr_progress(
        self,
        okr_id: str,
        kr_index: int,
        current_value: float
    ) -> bool:
        """Atualiza progresso de um Key Result"""
        for okr in self._okrs:
            if okr.okr_id == okr_id:
                if 0 <= kr_index < len(okr.key_results):
                    okr.key_results[kr_index]['current'] = current_value
                    
                    total_progress = 0
                    for kr in okr.key_results:
                        target = kr.get('target', 1)
                        current = kr.get('current', 0)
                        if target != 0:
                            total_progress += min(100, (current / target) * 100)
                    
                    okr.progress = total_progress / len(okr.key_results)
                    return True
        
        return False
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        return {
            'service': 'finops_maturity',
            'period_days': period_days,
            'total_cost': 0,
            'currency': 'USD'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        assessment = self.assess_maturity()
        return {
            'service': 'finops_maturity',
            'overall_score': assessment.overall_score,
            'overall_level': assessment.overall_level.value,
            'capabilities_assessed': len(assessment.capabilities),
            'gaps_identified': sum(len(c.gaps) for c in assessment.capabilities)
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de maturidade"""
        assessment = self.assess_maturity()
        
        recommendations = []
        for gap in assessment.top_gaps[:5]:
            recommendations.append({
                'type': 'MATURITY_GAP',
                'priority': 'HIGH' if gap['gap_percentage'] > 50 else 'MEDIUM',
                'title': f"Melhorar {gap['capability']}",
                'description': f"Capability está em {gap['current_percentage']:.0f}% - gap de {gap['gap_percentage']:.0f}%",
                'action': gap['recommendations'][0] if gap['recommendations'] else 'Revisar e implementar melhorias'
            })
        
        return recommendations
