"""
AWS Integrations for FinOps Dashboard

Integração com serviços AWS para recomendações de otimização:
- AWS Compute Optimizer
- Cost Explorer (Reserved Instances e Savings Plans)
- AWS Trusted Advisor
- Amazon Q Business
- AWS Budgets
- Cost Anomaly Detection
- Savings Plans Analysis
- Reserved Instances Analysis
- Tag Governance
- KPIs Calculator

Design Patterns:
- Facade: Simplifica acesso às integrações
- Strategy: Provedores de IA intercambiáveis
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
    from ..ai_consultant.providers import AIProviderFactory
    from ..ai_consultant.providers.base_provider import PersonaType
    
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


def get_budgets_analysis() -> Dict[str, Any]:
    """
    Obtém análise completa de AWS Budgets.
    
    Returns:
        Dict com budgets, métricas e recomendações
    """
    try:
        from ..services.budgets_service import BudgetsService
        
        service = BudgetsService()
        if not service.health_check():
            return {'error': 'Budgets service not available', 'budgets': [], 'recommendations': []}
        
        budgets = service.get_resources()
        metrics = service.get_metrics()
        recommendations = service.get_recommendations()
        
        return {
            'budgets': budgets,
            'metrics': metrics.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
            'costs': service.get_costs().to_dict()
        }
    except Exception as e:
        logger.error(f"Erro ao obter análise de Budgets: {e}")
        return {'error': str(e), 'budgets': [], 'recommendations': []}


def get_anomaly_detection_analysis(days_back: int = 90) -> Dict[str, Any]:
    """
    Obtém análise de anomalias de custo.
    
    Args:
        days_back: Dias para análise histórica
        
    Returns:
        Dict com anomalias, métricas e recomendações
    """
    try:
        from ..services.costanomalydetection_service import CostAnomalyDetectionService
        
        service = CostAnomalyDetectionService()
        if not service.health_check():
            return {'error': 'Cost Anomaly Detection not available', 'anomalies': [], 'recommendations': []}
        
        anomalies = service.get_anomalies(days_back=days_back)
        monitors = service.get_anomaly_monitors()
        metrics = service.get_metrics()
        recommendations = service.get_recommendations()
        
        return {
            'anomalies': [a.to_dict() for a in anomalies],
            'monitors': [m.to_dict() for m in monitors],
            'metrics': metrics.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
            'costs': service.get_costs().to_dict()
        }
    except Exception as e:
        logger.error(f"Erro ao obter análise de anomalias: {e}")
        return {'error': str(e), 'anomalies': [], 'recommendations': []}


def get_savings_plans_analysis() -> Dict[str, Any]:
    """
    Obtém análise completa de Savings Plans.
    
    Returns:
        Dict com SP, utilização, cobertura e recomendações
    """
    try:
        from ..services.savingsplans_service import SavingsPlansService
        
        service = SavingsPlansService()
        if not service.health_check():
            return {'error': 'Savings Plans service not available', 'savings_plans': [], 'recommendations': []}
        
        savings_plans = service.get_savings_plans(states=['active'])
        utilization = service.get_utilization()
        coverage = service.get_coverage()
        metrics = service.get_metrics()
        recommendations = service.get_recommendations()
        purchase_recs = service.get_purchase_recommendations()
        
        return {
            'savings_plans': [sp.to_dict() for sp in savings_plans],
            'utilization': utilization.to_dict(),
            'coverage': coverage.to_dict(),
            'metrics': metrics.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
            'purchase_recommendations': purchase_recs,
            'costs': service.get_costs().to_dict()
        }
    except Exception as e:
        logger.error(f"Erro ao obter análise de Savings Plans: {e}")
        return {'error': str(e), 'savings_plans': [], 'recommendations': []}


def get_reserved_instances_analysis() -> Dict[str, Any]:
    """
    Obtém análise completa de Reserved Instances.
    
    Returns:
        Dict com RIs, utilização, cobertura e recomendações
    """
    try:
        from ..services.reservedinstances_service import ReservedInstancesService
        
        service = ReservedInstancesService()
        if not service.health_check():
            return {'error': 'Reserved Instances service not available', 'reserved_instances': [], 'recommendations': []}
        
        ris = service.get_all_reserved_instances()
        utilization = service.get_utilization()
        coverage = service.get_coverage()
        metrics = service.get_metrics()
        recommendations = service.get_recommendations()
        purchase_recs = service.get_purchase_recommendations()
        
        return {
            'reserved_instances': [ri.to_dict() for ri in ris],
            'utilization': utilization.to_dict(),
            'coverage': coverage.to_dict(),
            'metrics': metrics.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
            'purchase_recommendations': purchase_recs,
            'costs': service.get_costs().to_dict()
        }
    except Exception as e:
        logger.error(f"Erro ao obter análise de Reserved Instances: {e}")
        return {'error': str(e), 'reserved_instances': [], 'recommendations': []}


def get_tag_governance_analysis(required_tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Obtém análise de governança de tags.
    
    Args:
        required_tags: Lista de tags obrigatórias (opcional)
        
    Returns:
        Dict com cobertura, compliance e recomendações
    """
    try:
        from ..services.tag_governance_service import TagGovernanceService
        
        service = TagGovernanceService(required_tags=required_tags)
        if not service.health_check():
            return {'error': 'Tag Governance service not available', 'coverage': {}, 'recommendations': []}
        
        coverage = service.analyze_tag_coverage()
        tags_in_use = service.get_all_tags_in_use()
        metrics = service.get_metrics()
        recommendations = service.get_recommendations()
        
        return {
            'coverage': coverage.to_dict(),
            'tags_in_use': tags_in_use,
            'metrics': metrics.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
            'policy': service.get_tag_policy().to_dict(),
            'costs': service.get_costs().to_dict()
        }
    except Exception as e:
        logger.error(f"Erro ao obter análise de Tag Governance: {e}")
        return {'error': str(e), 'coverage': {}, 'recommendations': []}


def get_finops_kpis(
    idle_cost: float = 0.0,
    shadow_cost: float = 0.0,
    savings_potential: float = 0.0,
    savings_captured: float = 0.0,
    transactions_count: int = 0,
    customers_count: int = 0,
    revenue: float = 0.0
) -> Dict[str, Any]:
    """
    Calcula todos os KPIs FinOps.
    
    Args:
        idle_cost: Custo de recursos ociosos
        shadow_cost: Custo de recursos sem tags
        savings_potential: Economia potencial identificada
        savings_captured: Economia já capturada
        transactions_count: Número de transações (para unit economics)
        customers_count: Número de clientes (para unit economics)
        revenue: Receita do período (para margem)
        
    Returns:
        Dict com todos os KPIs calculados
    """
    try:
        from ..services.kpi_calculator import KPICalculator
        
        calculator = KPICalculator()
        result = calculator.calculate_all_kpis(
            idle_cost=idle_cost,
            shadow_cost=shadow_cost,
            savings_potential=savings_potential,
            savings_captured=savings_captured,
            transactions_count=transactions_count,
            customers_count=customers_count,
            revenue=revenue
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Erro ao calcular KPIs: {e}")
        return {'error': str(e), 'kpis': {}}


def get_commitments_summary() -> Dict[str, Any]:
    """
    Obtém resumo consolidado de commitments (RI + SP).
    
    Returns:
        Dict com resumo de todos os commitments
    """
    sp_analysis = get_savings_plans_analysis()
    ri_analysis = get_reserved_instances_analysis()
    
    total_sp = len(sp_analysis.get('savings_plans', []))
    total_ri = len(ri_analysis.get('reserved_instances', []))
    
    sp_utilization = sp_analysis.get('utilization', {}).get('utilization_percentage', 0)
    ri_utilization = ri_analysis.get('utilization', {}).get('utilization_percentage', 0)
    
    sp_coverage = sp_analysis.get('coverage', {}).get('coverage_percentage', 0)
    ri_coverage = ri_analysis.get('coverage', {}).get('coverage_percentage', 0)
    
    all_recommendations = []
    all_recommendations.extend(sp_analysis.get('recommendations', []))
    all_recommendations.extend(ri_analysis.get('recommendations', []))
    
    return {
        'summary': {
            'total_savings_plans': total_sp,
            'total_reserved_instances': total_ri,
            'sp_utilization_percent': sp_utilization,
            'ri_utilization_percent': ri_utilization,
            'sp_coverage_percent': sp_coverage,
            'ri_coverage_percent': ri_coverage,
            'avg_utilization': (sp_utilization + ri_utilization) / 2 if (sp_utilization + ri_utilization) > 0 else 0,
            'avg_coverage': (sp_coverage + ri_coverage) / 2 if (sp_coverage + ri_coverage) > 0 else 0
        },
        'savings_plans': sp_analysis,
        'reserved_instances': ri_analysis,
        'recommendations': all_recommendations
    }
