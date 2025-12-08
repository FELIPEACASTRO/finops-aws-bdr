"""
Main Analysis Module for FinOps Dashboard

Módulo principal de análise que consolida todas as fontes de dados.

Design Patterns:
- Facade: Simplifica acesso à análise complexa
- Strategy: Usa analyzers modulares

SOLID:
- SRP: Coordena análise, não implementa
- OCP: Extensível via novos analyzers
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional

import boto3
from botocore.exceptions import ClientError

from .integrations import (
    get_compute_optimizer_recommendations,
    get_cost_explorer_ri_recommendations,
    get_trusted_advisor_recommendations,
    get_amazon_q_insights,
    get_budgets_analysis,
    get_anomaly_detection_analysis,
    get_savings_plans_analysis,
    get_reserved_instances_analysis,
    get_tag_governance_analysis,
    get_finops_kpis,
    get_commitments_summary,
)

logger = logging.getLogger(__name__)


def get_analyzers_analysis(region: str) -> tuple[List[Dict], Dict[str, Any]]:
    """
    Executa análise usando os analyzers modulares (Strategy Pattern).
    
    Usa AnalyzerFactory para criar e executar todos os analyzers:
    - ComputeAnalyzer
    - StorageAnalyzer
    - DatabaseAnalyzer
    - NetworkAnalyzer
    - SecurityAnalyzer
    - AnalyticsAnalyzer
    
    Args:
        region: Região AWS para análise
        
    Returns:
        Tuple (recommendations, resources)
    """
    try:
        from ..analyzers import AnalyzerFactory
        
        factory = AnalyzerFactory()
        result = factory.analyze_all(region)
        
        recommendations = [rec.to_dict() for rec in result.recommendations]
        resources: Dict[str, Any] = dict(result.resources)
        resources['_services_analyzed_list'] = result.services_analyzed
        resources['_services_analyzed_count'] = len(result.services_analyzed)
        
        logger.info(
            f"Analyzers executados: {len(result.services_analyzed)} serviços, "
            f"{len(recommendations)} recomendações"
        )
        
        return recommendations, resources
        
    except ImportError as e:
        logger.warning(f"Analyzers não disponíveis: {e}")
        return [], {}
    except Exception as e:
        logger.error(f"Erro nos analyzers: {e}")
        return [], {}


def get_dashboard_analysis(
    all_services_func: Optional[Callable] = None,
    include_multi_region: bool = False
) -> Dict[str, Any]:
    """
    Executa análise completa de custos e recursos AWS para o dashboard.
    
    Esta função é chamada pelos endpoints da API quando precisam de análise
    completa. Ela não importa de app.py para evitar dependência circular.
    
    Args:
        all_services_func: Função opcional para análise de todos os serviços.
                          Quando None, usa apenas as integrações.
        include_multi_region: Se True, analisa todas as regiões
        
    Returns:
        Dicionário com análise completa
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    result = {
        'costs': {},
        'resources': {},
        'recommendations': [],
        'integrations': {
            'analyzers': False,
            'all_services': False,
            'compute_optimizer': False,
            'cost_explorer_ri': False,
            'trusted_advisor': False,
            'amazon_q': False,
            'multi_region': False,
            'budgets': False,
            'anomalies': False,
            'savings_plans': False,
            'reserved_instances': False,
            'tag_governance': False,
            'kpis': False
        },
        'finops': {
            'budgets': {},
            'anomalies': {},
            'savings_plans': {},
            'reserved_instances': {},
            'commitments': {},
            'tag_governance': {},
            'kpis': {}
        },
        'account_id': 'Unknown',
        'region': region,
        'generated_at': datetime.utcnow().isoformat()
    }
    
    result['costs'] = _get_cost_data()
    
    try:
        sts = boto3.client('sts')
        result['account_id'] = sts.get_caller_identity()['Account']
    except ClientError:
        pass
    
    analyzer_recs, analyzer_resources = get_analyzers_analysis(region)
    if analyzer_recs:
        result['recommendations'].extend(_normalize_recommendations(analyzer_recs))
        result['integrations']['analyzers'] = True
    if analyzer_resources:
        result['resources'].update(analyzer_resources)
    
    if all_services_func:
        try:
            all_services_recs, all_services_resources = all_services_func(region)
            if all_services_recs:
                result['recommendations'].extend(_normalize_recommendations(all_services_recs))
                result['integrations']['all_services'] = True
            if all_services_resources:
                result['resources'].update(all_services_resources)
        except Exception as e:
            logger.error(f"Erro na análise de serviços: {e}")
    
    try:
        co_recs = get_compute_optimizer_recommendations(region)
        if co_recs:
            result['recommendations'].extend(co_recs)
            result['integrations']['compute_optimizer'] = True
    except Exception as e:
        logger.error(f"Erro no Compute Optimizer: {e}")
    
    try:
        ri_recs = get_cost_explorer_ri_recommendations(region)
        if ri_recs:
            result['recommendations'].extend(ri_recs)
            result['integrations']['cost_explorer_ri'] = True
    except Exception as e:
        logger.error(f"Erro no Cost Explorer RI: {e}")
    
    try:
        ta_recs = get_trusted_advisor_recommendations()
        if ta_recs:
            result['recommendations'].extend(ta_recs)
            result['integrations']['trusted_advisor'] = True
    except Exception as e:
        logger.error(f"Erro no Trusted Advisor: {e}")
    
    try:
        q_insights = get_amazon_q_insights(result.get('costs', {}), result.get('resources', {}))
        if q_insights:
            result['recommendations'].extend(q_insights)
            result['integrations']['amazon_q'] = True
    except Exception as e:
        logger.error(f"Erro no Amazon Q: {e}")
    
    if include_multi_region:
        try:
            from .multi_region import get_all_regions_analysis
            multi_region_data = get_all_regions_analysis(max_workers=3)
            result['multi_region'] = multi_region_data
            result['integrations']['multi_region'] = True
            
            for rec in multi_region_data.get('consolidated_recommendations', []):
                result['recommendations'].append(rec)
        except Exception as e:
            logger.error(f"Erro na análise multi-region: {e}")
    
    try:
        budgets_data = get_budgets_analysis()
        if budgets_data and 'error' not in budgets_data:
            result['finops']['budgets'] = budgets_data
            result['integrations']['budgets'] = True
            for rec in budgets_data.get('recommendations', []):
                result['recommendations'].append(rec)
    except Exception as e:
        logger.error(f"Erro na análise de Budgets: {e}")
    
    try:
        anomalies_data = get_anomaly_detection_analysis(days_back=90)
        if anomalies_data and 'error' not in anomalies_data:
            result['finops']['anomalies'] = anomalies_data
            result['integrations']['anomalies'] = True
            for rec in anomalies_data.get('recommendations', []):
                result['recommendations'].append(rec)
    except Exception as e:
        logger.error(f"Erro na análise de Anomalias: {e}")
    
    sp_data = None
    ri_data = None
    
    try:
        sp_data = get_savings_plans_analysis()
        if sp_data and 'error' not in sp_data:
            result['finops']['savings_plans'] = sp_data
            result['integrations']['savings_plans'] = True
            for rec in sp_data.get('recommendations', []):
                result['recommendations'].append(rec)
    except Exception as e:
        logger.error(f"Erro na análise de Savings Plans: {e}")
    
    try:
        ri_data = get_reserved_instances_analysis()
        if ri_data and 'error' not in ri_data:
            result['finops']['reserved_instances'] = ri_data
            result['integrations']['reserved_instances'] = True
            for rec in ri_data.get('recommendations', []):
                result['recommendations'].append(rec)
    except Exception as e:
        logger.error(f"Erro na análise de Reserved Instances: {e}")
    
    try:
        commitments_data = get_commitments_summary(sp_data=sp_data, ri_data=ri_data)
        if commitments_data:
            result['finops']['commitments'] = commitments_data.get('summary', {})
    except Exception as e:
        logger.error(f"Erro no resumo de Commitments: {e}")
    
    tag_data: Optional[Dict[str, Any]] = None
    try:
        tag_data = get_tag_governance_analysis()
        if tag_data and 'error' not in tag_data:
            result['finops']['tag_governance'] = tag_data
            result['integrations']['tag_governance'] = True
            for rec in tag_data.get('recommendations', []):
                result['recommendations'].append(rec)
    except Exception as e:
        logger.error(f"Erro na análise de Tag Governance: {e}")
    
    try:
        idle_cost = sum(
            r.get('savings', 0) for r in result['recommendations'] 
            if 'idle' in r.get('type', '').lower() or 'unused' in r.get('type', '').lower()
        )
        shadow_cost = tag_data.get('costs', {}).get('total_cost', 0) if tag_data else 0
        savings_potential = sum(r.get('savings', 0) for r in result['recommendations'])
        
        tag_coverage_percent = 0.0
        if tag_data and 'coverage' in tag_data:
            tag_coverage_percent = tag_data['coverage'].get('compliance_percent', 0.0)
        
        kpis_data = get_finops_kpis(
            idle_cost=idle_cost,
            shadow_cost=shadow_cost,
            savings_potential=savings_potential,
            tag_coverage_percent=tag_coverage_percent
        )
        if kpis_data and 'error' not in kpis_data:
            result['finops']['kpis'] = kpis_data
            result['integrations']['kpis'] = True
    except Exception as e:
        logger.error(f"Erro no cálculo de KPIs: {e}")
    
    result['recommendations'] = _deduplicate_recommendations(result['recommendations'])
    result['recommendations'].sort(key=lambda x: x.get('savings', 0), reverse=True)
    
    result['summary'] = _generate_summary(result)
    
    return result


def _normalize_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normaliza o formato das recomendações para consistência.
    
    Converte campos antigos para o novo padrão:
    - resource -> resource_id
    - impact -> priority
    - source -> service
    
    Args:
        recommendations: Lista de recomendações em formato antigo ou novo
        
    Returns:
        Lista de recomendações normalizadas
    """
    normalized = []
    
    priority_map = {
        'high': 'HIGH',
        'medium': 'MEDIUM',
        'low': 'LOW',
        'HIGH': 'HIGH',
        'MEDIUM': 'MEDIUM',
        'LOW': 'LOW'
    }
    
    for rec in recommendations:
        normalized_rec = {
            'type': rec.get('type', 'UNKNOWN'),
            'resource_id': rec.get('resource_id', rec.get('resource', 'N/A')),
            'title': rec.get('title', rec.get('description', '')),
            'description': rec.get('description', rec.get('title', '')),
            'priority': priority_map.get(rec.get('priority', rec.get('impact', 'MEDIUM')), 'MEDIUM'),
            'savings': rec.get('savings', 0),
            'service': rec.get('service', rec.get('source', 'Analysis'))
        }
        normalized.append(normalized_rec)
    
    return normalized


def _get_cost_data() -> Dict[str, Any]:
    """
    Obtém dados de custo do Cost Explorer.
    
    Returns:
        Dicionário com custos por serviço
    """
    costs = {}
    
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cost_response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        total_cost = 0
        cost_by_service = {}
        
        for result_item in cost_response.get('ResultsByTime', []):
            for group in result_item.get('Groups', []):
                service_name = group.get('Keys', ['Unknown'])[0]
                cost = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', 0))
                cost_by_service[service_name] = cost_by_service.get(service_name, 0) + cost
                total_cost += cost
        
        costs = {
            'total': round(total_cost, 2),
            'by_service': {k: round(v, 4) for k, v in sorted(
                cost_by_service.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20]},
            'period': {
                'start': start_date,
                'end': end_date
            }
        }
        
    except ClientError as e:
        logger.error(f"Erro ao obter custos: {e}")
        costs = {'error': str(e), 'total': 0, 'by_service': {}}
    except Exception as e:
        logger.error(f"Erro inesperado ao obter custos: {e}")
        costs = {'error': str(e), 'total': 0, 'by_service': {}}
    
    return costs


def _deduplicate_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove recomendações duplicadas mantendo a de maior economia.
    
    Args:
        recommendations: Lista de recomendações
        
    Returns:
        Lista de recomendações sem duplicatas
    """
    seen = {}
    
    for rec in recommendations:
        resource_id = rec.get('resource_id', rec.get('resource', ''))
        key = f"{rec.get('type', '')}:{resource_id}"
        
        if key not in seen or rec.get('savings', 0) > seen[key].get('savings', 0):
            seen[key] = rec
    
    return list(seen.values())


def _generate_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera resumo executivo da análise.
    
    Args:
        result: Resultado completo da análise
        
    Returns:
        Dicionário com resumo
    """
    recommendations = result.get('recommendations', [])
    costs = result.get('costs', {})
    
    total_savings = sum(r.get('savings', 0) for r in recommendations)
    
    high_priority = sum(1 for r in recommendations if r.get('priority') == 'HIGH')
    medium_priority = sum(1 for r in recommendations if r.get('priority') == 'MEDIUM')
    low_priority = sum(1 for r in recommendations if r.get('priority') == 'LOW')
    
    integrations_active = sum(1 for v in result.get('integrations', {}).values() if v)
    
    total_cost = costs.get('total', 0)
    if total_cost > 0:
        savings_pct = round((total_savings / total_cost) * 100, 1)
    else:
        savings_pct = 0
    
    return {
        'total_cost': total_cost,
        'total_potential_savings': round(total_savings, 2),
        'savings_percentage': savings_pct,
        'recommendations_count': len(recommendations),
        'high_priority_count': high_priority,
        'medium_priority_count': medium_priority,
        'low_priority_count': low_priority,
        'integrations_active': integrations_active,
        'top_opportunity': recommendations[0] if recommendations else None
    }
