"""
AWS Integrations for FinOps Dashboard

Integração com serviços AWS para recomendações de otimização:
- AWS Compute Optimizer
- Cost Explorer (Reserved Instances e Savings Plans)
- AWS Trusted Advisor
- Amazon Q Business
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_compute_optimizer_recommendations(region: str) -> List[Dict[str, Any]]:
    """
    Obtém recomendações do AWS Compute Optimizer para EC2.
    
    Args:
        region: Região AWS para análise
        
    Returns:
        Lista de recomendações de right-sizing
    """
    recommendations = []
    
    try:
        co = boto3.client('compute-optimizer', region_name=region)
        
        ec2_recs = co.get_ec2_instance_recommendations()
        for rec in ec2_recs.get('instanceRecommendations', []):
            instance_id = rec.get('instanceArn', '').split('/')[-1]
            finding = rec.get('finding', '')
            
            if finding in ['OVER_PROVISIONED', 'UNDER_PROVISIONED']:
                current_type = rec.get('currentInstanceType', '')
                rec_options = rec.get('recommendationOptions', [])
                
                if rec_options:
                    best_option = rec_options[0]
                    recommended_type = best_option.get('instanceType', '')
                    savings = best_option.get('estimatedMonthlySavings', {}).get('value', 0)
                    
                    recommendations.append({
                        'type': 'COMPUTE_OPTIMIZER_EC2',
                        'resource_id': instance_id,
                        'title': f'Right-size EC2: {current_type} → {recommended_type}',
                        'description': f'EC2 {instance_id}: {current_type} → {recommended_type} ({finding})',
                        'priority': 'HIGH',
                        'savings': round(savings, 2),
                        'service': 'AWS Compute Optimizer'
                    })
                    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'OptInRequiredException':
            logger.warning("Compute Optimizer não está habilitado nesta conta")
        else:
            logger.error(f"Erro ao acessar Compute Optimizer: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado no Compute Optimizer: {e}")
    
    return recommendations


def get_cost_explorer_ri_recommendations(region: str) -> List[Dict[str, Any]]:
    """
    Obtém recomendações de Reserved Instances e Savings Plans.
    
    Args:
        region: Região AWS (Cost Explorer usa us-east-1)
        
    Returns:
        Lista de recomendações de RI e Savings Plans
    """
    recommendations = []
    
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        ri_response = ce.get_reservation_purchase_recommendation(
            Service='Amazon Elastic Compute Cloud - Compute',
            LookbackPeriodInDays='SIXTY_DAYS',
            TermInYears='ONE_YEAR',
            PaymentOption='NO_UPFRONT'
        )
        
        for rec in ri_response.get('Recommendations', []):
            for detail in rec.get('RecommendationDetails', []):
                instance_details = detail.get('InstanceDetails', {}).get('EC2InstanceDetails', {})
                instance_type = instance_details.get('InstanceType', 'Unknown')
                savings = float(detail.get('EstimatedMonthlySavingsAmount', 0))
                
                if savings > 0:
                    recommendations.append({
                        'type': 'RESERVED_INSTANCE',
                        'resource_id': instance_type,
                        'title': f'Reserved Instance para {instance_type}',
                        'description': f'Comprar Reserved Instance para {instance_type}',
                        'priority': 'HIGH',
                        'savings': round(savings, 2),
                        'service': 'Cost Explorer RI'
                    })
        
        sp_response = ce.get_savings_plans_purchase_recommendation(
            SavingsPlansType='COMPUTE_SP',
            LookbackPeriodInDays='SIXTY_DAYS',
            TermInYears='ONE_YEAR',
            PaymentOption='NO_UPFRONT'
        )
        
        sp_rec = sp_response.get('SavingsPlansPurchaseRecommendation', {})
        details = sp_rec.get('SavingsPlansPurchaseRecommendationDetails', [])
        
        for detail in details:
            savings = float(detail.get('EstimatedMonthlySavingsAmount', 0))
            commitment = float(detail.get('HourlyCommitmentToPurchase', 0))
            
            if savings > 0:
                recommendations.append({
                    'type': 'SAVINGS_PLAN',
                    'resource_id': 'Compute Savings Plan',
                    'title': f'Savings Plan: ${commitment:.2f}/hora',
                    'description': f'Savings Plan: ${commitment:.2f}/hora para economia de ${savings:.2f}/mês',
                    'priority': 'HIGH',
                    'savings': round(savings, 2),
                    'service': 'Cost Explorer SP'
                })
                
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'DataUnavailableException':
            logger.warning("Dados insuficientes para recomendações de RI/SP")
        else:
            logger.error(f"Erro ao acessar Cost Explorer: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado no Cost Explorer: {e}")
    
    return recommendations


def get_trusted_advisor_recommendations() -> List[Dict[str, Any]]:
    """
    Obtém recomendações do AWS Trusted Advisor.
    
    Requer AWS Business ou Enterprise Support.
    
    Returns:
        Lista de recomendações do Trusted Advisor
    """
    recommendations = []
    
    try:
        support = boto3.client('support', region_name='us-east-1')
        
        checks = support.describe_trusted_advisor_checks(language='en')
        
        cost_checks = [c for c in checks.get('checks', []) if c.get('category') == 'cost_optimizing']
        
        for check in cost_checks[:10]:
            check_id = check.get('id')
            check_name = check.get('name')
            
            try:
                result = support.describe_trusted_advisor_check_result(checkId=check_id, language='en')
                status = result.get('result', {}).get('status', '')
                
                if status in ['warning', 'error']:
                    flagged = result.get('result', {}).get('flaggedResources', [])
                    
                    for resource in flagged[:5]:
                        metadata = resource.get('metadata', [])
                        
                        recommendations.append({
                            'type': 'TRUSTED_ADVISOR',
                            'resource_id': metadata[0] if metadata else 'N/A',
                            'title': check_name,
                            'description': f'{check_name}',
                            'priority': 'HIGH' if status == 'error' else 'MEDIUM',
                            'savings': 0,
                            'service': 'AWS Trusted Advisor'
                        })
            except ClientError:
                continue
                
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'SubscriptionRequiredException':
            recommendations.append({
                'type': 'TRUSTED_ADVISOR_UNAVAILABLE',
                'resource_id': 'N/A',
                'title': 'Trusted Advisor indisponível',
                'description': 'Trusted Advisor requer AWS Business ou Enterprise Support',
                'priority': 'LOW',
                'savings': 0,
                'service': 'Info'
            })
        else:
            logger.error(f"Erro ao acessar Trusted Advisor: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado no Trusted Advisor: {e}")
    
    return recommendations


def get_ai_insights(
    costs: Dict[str, Any], 
    resources: Dict[str, Any],
    persona: str = 'EXECUTIVE',
    provider: str = 'auto'
) -> List[Dict[str, Any]]:
    """
    Obtém insights de IA para análise FinOps usando múltiplos provedores.
    
    Provedores suportados:
    - amazon_q: Amazon Q Business (AWS nativo)
    - openai: ChatGPT (GPT-4o)
    - gemini: Google Gemini
    - perplexity: Perplexity AI (com busca online)
    - auto: Seleciona automaticamente o primeiro disponível
    
    Args:
        costs: Dados de custos consolidados
        resources: Dados de recursos AWS
        persona: Persona para o relatório (EXECUTIVE, CTO, DEVOPS, ANALYST)
        provider: Provedor de IA a usar (ou 'auto')
        
    Returns:
        Lista de insights gerados pela IA
    """
    from ..ai_consultant.providers import AIProviderFactory, PersonaType
    
    insights = []
    
    persona_map = {
        'EXECUTIVE': PersonaType.EXECUTIVE,
        'CTO': PersonaType.CTO,
        'DEVOPS': PersonaType.DEVOPS,
        'ANALYST': PersonaType.ANALYST
    }
    persona_type = persona_map.get(persona.upper(), PersonaType.EXECUTIVE)
    
    ai_provider = None
    
    if provider == 'auto':
        available = AIProviderFactory.create_all_available()
        if available:
            provider_name = list(available.keys())[0]
            ai_provider = available[provider_name]
    else:
        ai_provider = AIProviderFactory.create(provider)
    
    if not ai_provider:
        return insights
    
    try:
        response = ai_provider.generate_report(costs, resources, persona_type)
        
        if response and response.content:
            insights.append({
                'type': f'{response.provider.value.upper()}_INSIGHT',
                'resource_id': 'AI Analysis',
                'title': f'Análise Inteligente FinOps ({response.provider.value})',
                'description': response.content,
                'priority': 'HIGH',
                'savings': 0,
                'service': response.provider.value.replace('_', ' ').title(),
                'full_response': response.content,
                'model': response.model,
                'tokens_used': response.tokens_used,
                'latency_ms': response.latency_ms,
                'sources': response.sources
            })
            
    except Exception as e:
        logger.error(f"Erro ao obter insights de IA ({provider}): {e}")
    
    return insights


def get_amazon_q_insights(
    costs: Dict[str, Any], 
    resources: Dict[str, Any],
    persona: str = 'EXECUTIVE'
) -> List[Dict[str, Any]]:
    """
    Obtém insights do Amazon Q Business para análise FinOps.
    
    DEPRECATED: Use get_ai_insights() com provider='amazon_q'
    
    Args:
        costs: Dados de custos consolidados
        resources: Dados de recursos AWS
        persona: Persona para o relatório (EXECUTIVE, CTO, DEVOPS, ANALYST)
        
    Returns:
        Lista de insights gerados pela IA
    """
    return get_ai_insights(costs, resources, persona, provider='amazon_q')


def list_available_ai_providers() -> Dict[str, Any]:
    """
    Lista provedores de IA disponíveis e configurados.
    
    Returns:
        Dict com provedores e status
    """
    from ..ai_consultant.providers import AIProviderFactory
    
    result = {
        'available': [],
        'configured': [],
        'providers': {}
    }
    
    for name in ['amazon_q', 'openai', 'gemini', 'perplexity']:
        info = AIProviderFactory.get_provider_info(name)
        result['providers'][name] = info
        result['available'].append(name)
        
        try:
            provider = AIProviderFactory.create(name)
            if provider:
                health = provider.health_check()
                if health.get('healthy'):
                    result['configured'].append(name)
                    result['providers'][name]['status'] = 'configured'
                else:
                    result['providers'][name]['status'] = 'not_configured'
                    result['providers'][name]['error'] = health.get('details', {}).get('error')
        except Exception as e:
            result['providers'][name]['status'] = 'error'
            result['providers'][name]['error'] = str(e)
    
    return result


def _build_finops_prompt(
    costs: Dict[str, Any], 
    resources: Dict[str, Any],
    persona: str = 'EXECUTIVE'
) -> str:
    """
    Constrói prompt otimizado para análise FinOps.
    
    Args:
        costs: Dados de custos
        resources: Dados de recursos
        persona: Persona alvo
        
    Returns:
        Prompt estruturado para Amazon Q
    """
    total_cost = costs.get('total', 0)
    by_service = costs.get('by_service', {})
    
    top_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:10]
    top_services_text = "\n".join([f"  - {svc}: ${cost:.2f}" for svc, cost in top_services])
    
    resource_summary = []
    for key, value in list(resources.items())[:20]:
        if not key.startswith('_') and isinstance(value, (int, float)):
            resource_summary.append(f"  - {key}: {value}")
    resource_text = "\n".join(resource_summary) if resource_summary else "  Nenhum recurso identificado"
    
    persona_instructions = {
        'EXECUTIVE': """
Produza um relatório executivo com:
1. RESUMO EXECUTIVO (2 parágrafos)
2. TOP 3 OPORTUNIDADES DE ECONOMIA com valores em USD
3. RISCOS IDENTIFICADOS
4. PRÓXIMOS PASSOS (3 ações prioritárias)

Tom: Executivo, foco em ROI e impacto no negócio.""",
        
        'CTO': """
Produza um relatório técnico com:
1. ANÁLISE DE ARQUITETURA (eficiência e custos)
2. OPORTUNIDADES DE MODERNIZAÇÃO
3. TRADE-OFFS técnicos identificados
4. ROADMAP de otimização (30-60-90 dias)

Tom: Técnico-estratégico, foco em arquitetura.""",
        
        'DEVOPS': """
Produza um relatório operacional com:
1. AÇÕES IMEDIATAS (quick wins)
2. COMANDOS AWS CLI para cada ação
3. SCRIPTS de automação sugeridos
4. MÉTRICAS para monitorar

Tom: Prático e técnico, foco em implementação.""",
        
        'ANALYST': """
Produza uma análise detalhada com:
1. BREAKDOWN completo por serviço
2. TENDÊNCIAS identificadas
3. ANOMALIAS de custo
4. BENCHMARKS de mercado
5. PROJEÇÕES para próximos 3 meses

Tom: Analítico e detalhado, foco em dados."""
    }
    
    instructions = persona_instructions.get(persona, persona_instructions['EXECUTIVE'])
    
    prompt = f"""Você é um especialista FinOps analisando custos AWS.

## Dados de Custo

**Custo Total (últimos 30 dias):** ${total_cost:.2f}

**Top Serviços por Custo:**
{top_services_text}

## Recursos AWS Ativos

{resource_text}

## Instruções

{instructions}

## Formato

- Use Markdown
- Valores em USD
- Seja específico com números
- Priorize por impacto financeiro
- Idioma: Português do Brasil
"""
    
    return prompt
