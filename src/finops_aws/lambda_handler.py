"""
AWS Lambda Handler para FinOps AWS
Função principal que orquestra a coleta de custos, métricas e recomendações
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

from .services.cost_service import CostService
from .services.metrics_service import MetricsService
from .services.optimizer_service import OptimizerService
from .models.finops_models import FinOpsReport
from .utils.logger import setup_logger, log_error
from .utils.aws_helpers import get_aws_account_id
from .core.cleanup_manager import cleanup_after_execution

# Configuração de logging
logger = setup_logger(__name__, os.getenv('LOG_LEVEL', 'INFO'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal da função Lambda

    Args:
        event: Evento da Lambda
        context: Contexto da Lambda

    Returns:
        Relatório FinOps consolidado
    """
    start_time = datetime.now()
    logger.info("Starting FinOps AWS analysis", extra={
        'extra_data': {
            'request_id': context.aws_request_id if context else 'local',
            'function_name': context.function_name if context else 'local'
        }
    })

    try:
        # Obtém ID da conta AWS
        account_id = get_aws_account_id()
        logger.info(f"Analyzing AWS account: {account_id}")

        # Inicializa serviços
        cost_service = CostService()
        metrics_service = MetricsService()
        optimizer_service = OptimizerService()

        # Coleta dados de custo
        logger.info("Collecting cost data...")
        costs = cost_service.get_all_period_costs()

        # Coleta dados de uso
        logger.info("Collecting usage metrics...")
        usage = metrics_service.get_all_usage_data()

        # Coleta recomendações de otimização
        logger.info("Collecting optimization recommendations...")
        optimizer_recommendations = optimizer_service.get_all_recommendations()

        # Cria relatório consolidado
        report = FinOpsReport(
            account_id=account_id,
            generated_at=datetime.now(),
            costs=costs,
            usage=usage,
            optimizer=optimizer_recommendations
        )

        # Calcula métricas adicionais
        total_savings_potential = optimizer_service.calculate_total_savings_potential(
            optimizer_recommendations
        )

        # Converte para dicionário
        result = report.to_dict()

        # Adiciona métricas de resumo
        result['summary'] = generate_summary(costs, usage, optimizer_recommendations, total_savings_potential)

        # Executa limpeza automática de arquivos temporários (via helper do core)
        cleanup_enabled = os.getenv('CLEANUP_ENABLED', 'true').lower() == 'true'
        if cleanup_enabled:
            try:
                logger.info("Starting automatic cleanup...")
                result = cleanup_after_execution(result)
                logger.info("Cleanup completed", extra={
                    'extra_data': result.get('cleanup_metrics', {})
                })
            except Exception as cleanup_error:
                logger.warning(f"Cleanup failed (non-fatal): {cleanup_error}")
                result['cleanup_metrics'] = {'error': str(cleanup_error)}

        # Log de conclusão
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("FinOps analysis completed successfully", extra={
            'extra_data': {
                'duration_seconds': duration,
                'total_services_with_costs': len([s for period in costs.values() for s in period.keys()]),
                'total_ec2_instances': len(usage.get('ec2', [])),
                'total_lambda_functions': len(usage.get('lambda', [])),
                'total_recommendations': sum(len(recs) for recs in optimizer_recommendations.values()),
                'estimated_monthly_savings': total_savings_potential
            }
        })

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': context.aws_request_id if context else 'local'
            },
            'body': json.dumps(result, default=str, indent=2)
        }

    except Exception as e:
        log_error(logger, e, {
            'request_id': context.aws_request_id if context else 'local',
            'duration_seconds': (datetime.now() - start_time).total_seconds()
        })

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e),
                'request_id': context.aws_request_id if context else 'local'
            })
        }


def generate_summary(costs: Dict[str, Dict[str, float]],
                    usage: Dict[str, Any],
                    recommendations: Dict[str, Any],
                    total_savings: float) -> Dict[str, Any]:
    """
    Gera resumo executivo dos dados coletados

    Args:
        costs: Dados de custo
        usage: Dados de uso
        recommendations: Recomendações
        total_savings: Economia total estimada

    Returns:
        Resumo executivo
    """
    summary = {
        'total_estimated_monthly_savings': total_savings,
        'cost_analysis': {},
        'usage_insights': {},
        'optimization_opportunities': []
    }

    # Análise de custos
    if costs.get('last_30_days'):
        cost_30d = costs['last_30_days']
        total_cost_30d = sum(cost_30d.values())

        # Top 5 serviços mais caros
        top_services = sorted(cost_30d.items(), key=lambda x: x[1], reverse=True)[:5]

        summary['cost_analysis'] = {
            'total_cost_last_30_days': round(total_cost_30d, 2),
            'top_5_services': [
                {
                    'service': service,
                    'cost': round(cost, 2),
                    'percentage': round((cost / total_cost_30d) * 100, 1) if total_cost_30d > 0 else 0
                }
                for service, cost in top_services
            ]
        }

    # Insights de uso
    ec2_instances = usage.get('ec2', [])
    lambda_functions = usage.get('lambda', [])

    # Análise de EC2
    if ec2_instances:
        running_instances = [i for i in ec2_instances if hasattr(i, 'state') and i.state == 'running']
        low_cpu_instances = [
            i for i in running_instances
            if hasattr(i, 'avg_cpu_30d') and i.avg_cpu_30d and i.avg_cpu_30d < 20
        ]

        instances_with_cpu = [i for i in running_instances if hasattr(i, 'avg_cpu_30d') and i.avg_cpu_30d]
        avg_cpu = 0
        if instances_with_cpu:
            avg_cpu = round(
                sum(i.avg_cpu_30d for i in instances_with_cpu) / len(instances_with_cpu),
                2
            )
        
        summary['usage_insights']['ec2'] = {
            'total_instances': len(ec2_instances),
            'running_instances': len(running_instances),
            'low_utilization_instances': len(low_cpu_instances),
            'avg_cpu_utilization_30d': avg_cpu
        }

    # Análise de Lambda
    if lambda_functions:
        active_functions = [f for f in lambda_functions if hasattr(f, 'invocations_7d') and f.invocations_7d and f.invocations_7d > 0]

        summary['usage_insights']['lambda'] = {
            'total_functions': len(lambda_functions),
            'active_functions_7d': len(active_functions),
            'total_invocations_7d': sum(f.invocations_7d for f in active_functions if hasattr(f, 'invocations_7d') and f.invocations_7d),
            'total_errors_7d': sum(f.errors_7d for f in active_functions if hasattr(f, 'errors_7d') and f.errors_7d)
        }

    # Oportunidades de otimização
    all_recommendations = []
    for rec_type, rec_list in recommendations.items():
        all_recommendations.extend(rec_list)

    # Agrupa por tipo de finding
    findings_summary = {}
    for rec in all_recommendations:
        if hasattr(rec, 'finding') and rec.finding:
            if rec.finding not in findings_summary:
                findings_summary[rec.finding] = {'count': 0, 'potential_savings': 0}
            findings_summary[rec.finding]['count'] += 1
            if hasattr(rec, 'estimated_monthly_savings') and rec.estimated_monthly_savings:
                findings_summary[rec.finding]['potential_savings'] += rec.estimated_monthly_savings

    summary['optimization_opportunities'] = [
        {
            'finding': finding,
            'resource_count': data['count'],
            'estimated_monthly_savings': round(data['potential_savings'], 2)
        }
        for finding, data in findings_summary.items()
    ]

    return summary


# Função para execução local/teste
def main():
    """Função principal para execução local"""
    import sys

    # Simula contexto da Lambda para teste local
    class MockContext:
        aws_request_id = 'local-test-request'
        function_name = 'finops-aws-local'

    try:
        result = lambda_handler({}, MockContext())
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    exit(main())
