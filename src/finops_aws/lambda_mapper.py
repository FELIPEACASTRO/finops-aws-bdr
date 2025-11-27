"""
FinOps AWS - Lambda Mapper
Divide os 252 servicos AWS em batches para processamento paralelo
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

from .utils.logger import setup_logger
from .core.factories import ServiceFactory

logger = setup_logger(__name__)

BATCH_SIZE = int(os.getenv('BATCH_SIZE', '20'))
S3_BUCKET = os.getenv('REPORTS_BUCKET_NAME', 'finops-aws-reports')
STATE_PREFIX = os.getenv('STATE_PREFIX', 'state/')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda Mapper - Inicializa execucao e divide servicos em batches
    
    Args:
        event: Evento do Step Functions contendo:
            - execution_id: ID da execucao do Step Functions
            - start_time: Hora de inicio
            - input: Parametros de entrada
        context: Contexto do Lambda
    
    Returns:
        Dict com batches para processamento paralelo
    """
    logger.info(f"Mapper iniciado: {json.dumps(event)}")
    
    try:
        execution_id = event.get('execution_id', context.aws_request_id)
        start_time = event.get('start_time', datetime.now().isoformat())
        input_params = event.get('input', {})
        
        all_services = _get_all_services()
        enabled_services = _filter_services(all_services, input_params)
        
        batches = _create_batches(enabled_services, BATCH_SIZE)
        
        execution_state = {
            'execution_id': execution_id,
            'start_time': start_time,
            'total_services': len(enabled_services),
            'total_batches': len(batches),
            'batch_size': BATCH_SIZE,
            'status': 'RUNNING',
            'input_params': input_params
        }
        
        _save_state(execution_id, execution_state)
        
        logger.info(f"Mapper concluido: {len(batches)} batches criados para {len(enabled_services)} servicos")
        
        return {
            'execution_id': execution_id,
            'start_time': start_time,
            'total_services': len(enabled_services),
            'total_batches': len(batches),
            'batches': batches
        }
        
    except Exception as e:
        logger.error(f"Erro no Mapper: {str(e)}")
        raise


def _get_all_services() -> List[Dict[str, Any]]:
    """
    Obtem lista de todos os 252 servicos AWS disponiveis
    
    Returns:
        Lista de servicos com metadados
    """
    try:
        factory = ServiceFactory()
        services_dict = factory.get_all_services()
        
        service_list = []
        for service_name in services_dict.keys():
            service_list.append({
                'name': service_name,
                'category': _get_service_category(service_name),
                'priority': _get_service_priority(service_name),
                'estimated_duration': 30,
                'requires_cost_explorer': service_name in ['cost_explorer', 'budgets', 'cur']
            })
        
        service_list.sort(key=lambda x: (x['priority'], x['name']))
        
        return service_list
        
    except Exception as e:
        logger.warning(f"Erro ao obter servicos da factory: {e}. Usando lista padrao.")
        return _get_default_services()


def _get_service_category(service_name: str) -> str:
    """Retorna categoria de um servico"""
    categories = {
        'compute': ['ec2', 'lambda', 'ecs', 'eks', 'fargate', 'batch', 'lightsail'],
        'storage': ['s3', 'ebs', 'efs', 'fsx', 'glacier', 'backup'],
        'database': ['rds', 'dynamodb', 'elasticache', 'redshift', 'neptune', 'documentdb'],
        'networking': ['vpc', 'cloudfront', 'route53', 'elb', 'api_gateway'],
        'security': ['iam', 'kms', 'secrets_manager', 'waf', 'guardduty', 'security_hub'],
        'analytics': ['athena', 'emr', 'kinesis', 'glue', 'quicksight', 'opensearch'],
        'ml': ['sagemaker', 'bedrock', 'rekognition', 'comprehend', 'polly', 'transcribe'],
        'management': ['cloudwatch', 'cloudtrail', 'config', 'systems_manager', 'organizations']
    }
    for category, services in categories.items():
        if service_name.lower() in services:
            return category
    return 'other'


def _get_service_priority(service_name: str) -> int:
    """Retorna prioridade de um servico (1-10)"""
    high_priority = ['ec2', 'rds', 's3', 'lambda', 'cloudwatch', 'iam']
    medium_priority = ['ecs', 'eks', 'dynamodb', 'elasticache', 'cloudfront']
    
    if service_name.lower() in high_priority:
        return 1
    elif service_name.lower() in medium_priority:
        return 3
    return 5


def _get_default_services() -> List[Dict[str, Any]]:
    """
    Retorna lista padrao de servicos quando factory nao esta disponivel
    """
    categories = {
        'compute': ['ec2', 'lambda', 'ecs', 'eks', 'fargate', 'batch', 'lightsail', 'elasticbeanstalk'],
        'storage': ['s3', 'ebs', 'efs', 'fsx', 'glacier', 'storage_gateway', 'backup'],
        'database': ['rds', 'dynamodb', 'elasticache', 'redshift', 'neptune', 'documentdb', 'aurora'],
        'networking': ['vpc', 'cloudfront', 'route53', 'elb', 'api_gateway', 'direct_connect', 'transit_gateway'],
        'analytics': ['athena', 'emr', 'kinesis', 'glue', 'quicksight', 'opensearch', 'msk'],
        'ml': ['sagemaker', 'rekognition', 'comprehend', 'polly', 'transcribe', 'lex', 'bedrock'],
        'security': ['iam', 'kms', 'secrets_manager', 'waf', 'shield', 'guardduty', 'security_hub'],
        'management': ['cloudwatch', 'cloudtrail', 'config', 'systems_manager', 'organizations', 'control_tower']
    }
    
    services = []
    priority = 1
    for category, service_names in categories.items():
        for name in service_names:
            services.append({
                'name': name,
                'category': category,
                'priority': priority,
                'estimated_duration': 30,
                'requires_cost_explorer': name in ['cost_explorer', 'budgets', 'cur']
            })
        priority += 1
    
    return services


def _filter_services(services: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filtra servicos baseado nos parametros de entrada
    
    Args:
        services: Lista completa de servicos
        params: Parametros de filtragem
    
    Returns:
        Lista filtrada de servicos
    """
    enabled = params.get('enabled_services', [])
    excluded = params.get('excluded_services', [])
    categories = params.get('categories', [])
    
    filtered = services
    
    if enabled:
        enabled_set = set(enabled)
        filtered = [s for s in filtered if s['name'] in enabled_set]
    
    if excluded:
        excluded_set = set(excluded)
        filtered = [s for s in filtered if s['name'] not in excluded_set]
    
    if categories:
        categories_set = set(categories)
        filtered = [s for s in filtered if s['category'] in categories_set]
    
    return filtered


def _create_batches(services: List[Dict[str, Any]], batch_size: int) -> List[Dict[str, Any]]:
    """
    Cria batches de servicos para processamento paralelo
    Agrupa servicos que requerem Cost Explorer para otimizar rate limiting
    
    Args:
        services: Lista de servicos
        batch_size: Tamanho de cada batch
    
    Returns:
        Lista de batches
    """
    ce_services = [s for s in services if s.get('requires_cost_explorer', False)]
    other_services = [s for s in services if not s.get('requires_cost_explorer', False)]
    
    batches = []
    batch_index = 0
    
    for i in range(0, len(ce_services), batch_size // 2):
        batch_services = ce_services[i:i + batch_size // 2]
        batches.append({
            'batch_id': f"batch-ce-{batch_index}",
            'batch_index': batch_index,
            'services': batch_services,
            'service_count': len(batch_services),
            'batch_type': 'cost_explorer',
            'rate_limited': True
        })
        batch_index += 1
    
    for i in range(0, len(other_services), batch_size):
        batch_services = other_services[i:i + batch_size]
        batches.append({
            'batch_id': f"batch-{batch_index}",
            'batch_index': batch_index,
            'services': batch_services,
            'service_count': len(batch_services),
            'batch_type': 'standard',
            'rate_limited': False
        })
        batch_index += 1
    
    return batches


def _save_state(execution_id: str, state: Dict[str, Any]) -> None:
    """
    Salva estado da execucao no S3
    
    Args:
        execution_id: ID da execucao
        state: Estado a ser salvo
    """
    try:
        s3 = boto3.client('s3')
        key = f"{STATE_PREFIX}executions/{execution_id}/state.json"
        
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(state, default=str, indent=2),
            ContentType='application/json'
        )
        
        logger.debug(f"Estado salvo: s3://{S3_BUCKET}/{key}")
        
    except ClientError as e:
        logger.error(f"Erro ao salvar estado: {e}")
        raise
