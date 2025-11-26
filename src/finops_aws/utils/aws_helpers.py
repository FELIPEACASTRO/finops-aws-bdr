"""
Utilitários para interação com AWS
"""
import time
from functools import wraps
from typing import Any, Callable, Dict, List
import boto3
from botocore.exceptions import ClientError
from .logger import setup_logger, log_error

logger = setup_logger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator para retry com backoff exponencial

    Args:
        max_retries: Número máximo de tentativas
        base_delay: Delay base em segundos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    if attempt == max_retries:
                        log_error(logger, e, {"function": func.__name__, "attempt": attempt + 1})
                        raise

                    # Verifica se é um erro que vale a pena tentar novamente
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code not in ['ThrottlingException', 'RequestLimitExceeded', 'ServiceUnavailable', 'Throttling']:
                        raise

                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retrying {func.__name__} in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)

            return None
        return wrapper
    return decorator


def paginate_aws_call(client: Any, operation: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Executa paginação automática para chamadas AWS

    Args:
        client: Cliente boto3
        operation: Nome da operação
        **kwargs: Parâmetros da operação

    Returns:
        Lista com todos os resultados paginados
    """
    results = []
    paginator = client.get_paginator(operation)

    try:
        for page in paginator.paginate(**kwargs):
            results.append(page)
    except Exception as e:
        log_error(logger, e, {"operation": operation, "params": kwargs})
        raise

    return results


def get_aws_account_id() -> str:
    """
    Obtém o ID da conta AWS atual

    Returns:
        ID da conta AWS
    """
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        return response['Account']
    except Exception as e:
        log_error(logger, e, {"operation": "get_caller_identity"})
        raise


def get_aws_regions() -> List[str]:
    """
    Obtém lista de regiões AWS disponíveis

    Returns:
        Lista de códigos de região
    """
    try:
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        response = ec2_client.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except Exception as e:
        log_error(logger, e, {"operation": "describe_regions"})
        return ['us-east-1']  # Fallback para região padrão


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Obtém valor aninhado de dicionário de forma segura

    Args:
        data: Dicionário de dados
        keys: Lista de chaves para navegar
        default: Valor padrão se não encontrado

    Returns:
        Valor encontrado ou default
    """
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default
