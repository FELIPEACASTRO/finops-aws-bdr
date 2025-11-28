"""
FinOps AWS - Lambda Aggregator
Consolida resultados de todos os batches e gera relatorio final
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError

from .utils.logger import setup_logger

logger = setup_logger(__name__)

S3_BUCKET = os.getenv('REPORTS_BUCKET_NAME', 'finops-aws-reports')
STATE_PREFIX = os.getenv('STATE_PREFIX', 'state/')
REPORTS_PREFIX = os.getenv('REPORTS_PREFIX', 'reports/')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda Aggregator - Consolida resultados e gera relatorio final
    
    Args:
        event: Evento do Step Functions contendo:
            - execution_id: ID da execucao
            - batch_results: Resultados de cada batch
            - start_time: Hora de inicio
        context: Contexto do Lambda
    
    Returns:
        Dict com resumo da execucao e localizacao do relatorio
    """
    logger.info(f"Aggregator iniciado: execution_id={event.get('execution_id')}")
    
    try:
        execution_id: str = event.get('execution_id', context.aws_request_id)
        batch_results = event.get('batch_results', [])
        start_time: str = event.get('start_time', datetime.now().isoformat())
        
        aggregated = _aggregate_results(batch_results)
        
        end_time = datetime.now().isoformat()
        duration = _calculate_duration(start_time, end_time)
        
        summary = _create_execution_summary(
            execution_id=execution_id,
            aggregated=aggregated,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        
        report_path = _save_report(execution_id, summary, aggregated)
        
        _update_execution_state(execution_id, 'COMPLETED', summary)
        
        if SNS_TOPIC_ARN:
            _send_notification(summary, report_path)
        
        logger.info(f"Aggregator concluido: {summary['total_services_analyzed']} servicos analisados")
        
        return {
            'status': 'SUCCESS',
            'execution_id': execution_id,
            'summary': summary,
            'report_path': report_path,
            'duration_seconds': duration
        }
        
    except Exception as e:
        logger.error(f"Erro no Aggregator: {str(e)}")
        
        if 'execution_id' in event:
            _update_execution_state(event['execution_id'], 'FAILED', {'error': str(e)})
        
        raise


def _aggregate_results(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrega resultados de todos os batches
    
    Args:
        batch_results: Lista de resultados de cada batch
    
    Returns:
        Dados agregados
    """
    aggregated = {
        'services': {},
        'costs': {
            'total': 0.0,
            'by_service': {},
            'by_category': {}
        },
        'recommendations': [],
        'savings_potential': {
            'total': 0.0,
            'by_service': {},
            'by_category': {}
        },
        'metrics': {
            'resources_analyzed': 0,
            'anomalies_detected': 0,
            'optimizations_found': 0
        },
        'errors': []
    }
    
    for batch_result in batch_results:
        if batch_result is None:
            continue
            
        if isinstance(batch_result, dict) and 'error' in batch_result:
            aggregated['errors'].append(batch_result['error'])
            continue
        
        if isinstance(batch_result, dict):
            _merge_batch_result(aggregated, batch_result)
    
    aggregated['costs']['total'] = sum(aggregated['costs']['by_service'].values())
    aggregated['savings_potential']['total'] = sum(aggregated['savings_potential']['by_service'].values())
    
    aggregated['recommendations'].sort(key=lambda x: x.get('savings', 0), reverse=True)
    aggregated['recommendations'] = aggregated['recommendations'][:100]
    
    return aggregated


def _merge_batch_result(aggregated: Dict[str, Any], batch: Dict[str, Any]) -> None:
    """
    Mescla resultado de um batch no agregado
    """
    if 'services' in batch:
        aggregated['services'].update(batch['services'])
    
    if 'costs' in batch:
        batch_costs = batch['costs']
        if 'by_service' in batch_costs:
            for service, cost in batch_costs['by_service'].items():
                aggregated['costs']['by_service'][service] = \
                    aggregated['costs']['by_service'].get(service, 0) + cost
        if 'by_category' in batch_costs:
            for category, cost in batch_costs['by_category'].items():
                aggregated['costs']['by_category'][category] = \
                    aggregated['costs']['by_category'].get(category, 0) + cost
    
    if 'recommendations' in batch:
        aggregated['recommendations'].extend(batch['recommendations'])
    
    if 'savings_potential' in batch:
        batch_savings = batch['savings_potential']
        if 'by_service' in batch_savings:
            for service, savings in batch_savings['by_service'].items():
                aggregated['savings_potential']['by_service'][service] = \
                    aggregated['savings_potential']['by_service'].get(service, 0) + savings
        if 'by_category' in batch_savings:
            for category, savings in batch_savings['by_category'].items():
                aggregated['savings_potential']['by_category'][category] = \
                    aggregated['savings_potential']['by_category'].get(category, 0) + savings
    
    if 'metrics' in batch:
        batch_metrics = batch['metrics']
        aggregated['metrics']['resources_analyzed'] += batch_metrics.get('resources_analyzed', 0)
        aggregated['metrics']['anomalies_detected'] += batch_metrics.get('anomalies_detected', 0)
        aggregated['metrics']['optimizations_found'] += batch_metrics.get('optimizations_found', 0)


def _calculate_duration(start_time: str, end_time: str) -> float:
    """
    Calcula duracao da execucao em segundos
    """
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        return (end - start).total_seconds()
    except Exception:
        return 0.0


def _create_execution_summary(
    execution_id: str,
    aggregated: Dict[str, Any],
    start_time: str,
    end_time: str,
    duration: float
) -> Dict[str, Any]:
    """
    Cria resumo da execucao
    """
    return {
        'execution_id': execution_id,
        'status': 'SUCCESS' if not aggregated['errors'] else 'PARTIAL',
        'start_time': start_time,
        'end_time': end_time,
        'duration_seconds': duration,
        'total_services_analyzed': len(aggregated['services']),
        'total_cost': aggregated['costs']['total'],
        'total_savings_potential': aggregated['savings_potential']['total'],
        'recommendations_count': len(aggregated['recommendations']),
        'resources_analyzed': aggregated['metrics']['resources_analyzed'],
        'anomalies_detected': aggregated['metrics']['anomalies_detected'],
        'optimizations_found': aggregated['metrics']['optimizations_found'],
        'errors_count': len(aggregated['errors']),
        'top_cost_services': _get_top_items(aggregated['costs']['by_service'], 10),
        'top_savings_opportunities': _get_top_items(aggregated['savings_potential']['by_service'], 10)
    }


def _get_top_items(data: Dict[str, float], limit: int) -> List[Dict[str, Any]]:
    """
    Retorna top N items ordenados por valor
    """
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    return [{'name': k, 'value': v} for k, v in sorted_items[:limit]]


def _save_report(execution_id: str, summary: Dict[str, Any], aggregated: Dict[str, Any]) -> str:
    """
    Salva relatorio no S3
    
    Returns:
        Path do relatorio no S3
    """
    try:
        s3 = boto3.client('s3')
        
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        
        report = {
            'summary': summary,
            'details': aggregated,
            'generated_at': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        report_key = f"{REPORTS_PREFIX}{date_prefix}/{execution_id}/report.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=report_key,
            Body=json.dumps(report, default=str, indent=2),
            ContentType='application/json'
        )
        
        summary_key = f"{REPORTS_PREFIX}{date_prefix}/{execution_id}/summary.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=summary_key,
            Body=json.dumps(summary, default=str, indent=2),
            ContentType='application/json'
        )
        
        latest_key = f"{REPORTS_PREFIX}latest/report.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=latest_key,
            Body=json.dumps(report, default=str, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Relatorio salvo: s3://{S3_BUCKET}/{report_key}")
        
        return f"s3://{S3_BUCKET}/{report_key}"
        
    except ClientError as e:
        logger.error(f"Erro ao salvar relatorio: {e}")
        raise


def _update_execution_state(execution_id: str, status: str, data: Dict[str, Any]) -> None:
    """
    Atualiza estado da execucao no S3
    """
    try:
        s3 = boto3.client('s3')
        
        key = f"{STATE_PREFIX}executions/{execution_id}/state.json"
        
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=key)
            state = json.loads(response['Body'].read())
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NoSuchKey':
                state = {}
            else:
                state = {}
        except Exception:
            state = {}
        
        state.update({
            'status': status,
            'updated_at': datetime.now().isoformat(),
            **data
        })
        
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(state, default=str, indent=2),
            ContentType='application/json'
        )
        
    except ClientError as e:
        logger.error(f"Erro ao atualizar estado: {e}")


def _send_notification(summary: Dict[str, Any], report_path: str) -> None:
    """
    Envia notificacao SNS com resumo da execucao
    """
    try:
        sns = boto3.client('sns')
        
        message = {
            'default': json.dumps(summary, default=str),
            'email': _format_email_message(summary, report_path),
            'sms': f"FinOps: {summary['total_services_analyzed']} servicos analisados. Economia potencial: ${summary['total_savings_potential']:.2f}"
        }
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            MessageStructure='json',
            Subject=f"FinOps AWS - Analise Concluida ({summary['status']})"
        )
        
        logger.info("Notificacao enviada com sucesso")
        
    except ClientError as e:
        logger.warning(f"Erro ao enviar notificacao: {e}")


def _format_email_message(summary: Dict[str, Any], report_path: str) -> str:
    """
    Formata mensagem de email
    """
    return f"""
FinOps AWS - Relatorio de Analise de Custos
============================================

Status: {summary['status']}
Duracao: {summary['duration_seconds']:.1f} segundos

RESUMO
------
- Servicos Analisados: {summary['total_services_analyzed']}
- Recursos Analisados: {summary['resources_analyzed']}
- Custo Total: ${summary['total_cost']:,.2f}
- Economia Potencial: ${summary['total_savings_potential']:,.2f}

INSIGHTS
--------
- Recomendacoes Geradas: {summary['recommendations_count']}
- Anomalias Detectadas: {summary['anomalies_detected']}
- Otimizacoes Encontradas: {summary['optimizations_found']}

TOP 5 SERVICOS POR CUSTO
------------------------
{_format_top_items(summary['top_cost_services'][:5])}

TOP 5 OPORTUNIDADES DE ECONOMIA
-------------------------------
{_format_top_items(summary['top_savings_opportunities'][:5])}

Relatorio Completo: {report_path}

---
FinOps AWS - Otimizacao Inteligente de Custos
"""


def _format_top_items(items: List[Dict[str, Any]]) -> str:
    """
    Formata lista de top items para exibicao
    """
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item['name']}: ${item['value']:,.2f}")
    return '\n'.join(lines) if lines else 'Nenhum item encontrado'
