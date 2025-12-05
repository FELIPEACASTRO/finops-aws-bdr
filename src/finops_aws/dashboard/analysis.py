"""
Main Analysis Module for FinOps Dashboard

Módulo principal de análise que consolida todas as fontes de dados.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

import boto3
from botocore.exceptions import ClientError

from .integrations import (
    get_compute_optimizer_recommendations,
    get_cost_explorer_ri_recommendations,
    get_trusted_advisor_recommendations,
    get_amazon_q_insights,
)

logger = logging.getLogger(__name__)


def get_aws_analysis(include_multi_region: bool = False) -> Dict[str, Any]:
    """
    Executa análise completa de custos e recursos AWS.
    
    Args:
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
            'all_services': False,
            'compute_optimizer': False,
            'cost_explorer_ri': False,
            'trusted_advisor': False,
            'amazon_q': False,
            'multi_region': False
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
    
    from app import get_all_services_analysis
    all_services_recs, all_services_resources = get_all_services_analysis(region)
    if all_services_recs:
        result['recommendations'].extend(all_services_recs)
        result['integrations']['all_services'] = True
    if all_services_resources:
        result['resources'].update(all_services_resources)
    
    co_recs = get_compute_optimizer_recommendations(region)
    if co_recs:
        result['recommendations'].extend(co_recs)
        result['integrations']['compute_optimizer'] = True
    
    ri_recs = get_cost_explorer_ri_recommendations(region)
    if ri_recs:
        result['recommendations'].extend(ri_recs)
        result['integrations']['cost_explorer_ri'] = True
    
    ta_recs = get_trusted_advisor_recommendations()
    if ta_recs:
        result['recommendations'].extend(ta_recs)
        result['integrations']['trusted_advisor'] = True
    
    q_insights = get_amazon_q_insights(result.get('costs', {}), result.get('resources', {}))
    if q_insights:
        result['recommendations'].extend(q_insights)
        result['integrations']['amazon_q'] = True
    
    if include_multi_region:
        from .multi_region import get_all_regions_analysis
        multi_region_data = get_all_regions_analysis()
        result['multi_region'] = multi_region_data
        result['integrations']['multi_region'] = True
        
        for rec in multi_region_data.get('consolidated_recommendations', []):
            result['recommendations'].append(rec)
    
    result['recommendations'] = _deduplicate_recommendations(result['recommendations'])
    result['recommendations'].sort(key=lambda x: x.get('savings', 0), reverse=True)
    
    result['summary'] = _generate_summary(result)
    
    return result


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
        costs = {'error': str(e)}
    except Exception as e:
        logger.error(f"Erro inesperado ao obter custos: {e}")
        costs = {'error': str(e)}
    
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
        key = f"{rec.get('type', '')}:{rec.get('resource_id', rec.get('resource', ''))}"
        
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
    
    return {
        'total_cost': costs.get('total', 0),
        'total_potential_savings': round(total_savings, 2),
        'savings_percentage': round((total_savings / costs.get('total', 1)) * 100, 1) if costs.get('total', 0) > 0 else 0,
        'recommendations_count': len(recommendations),
        'high_priority_count': high_priority,
        'medium_priority_count': medium_priority,
        'low_priority_count': low_priority,
        'integrations_active': integrations_active,
        'top_opportunity': recommendations[0] if recommendations else None
    }
