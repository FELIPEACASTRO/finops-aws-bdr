"""
Utilitários para interação com AWS
"""
import time
import os
from functools import wraps
from typing import Any, Callable, Dict, List
import boto3
from botocore.exceptions import ClientError
from .logger import setup_logger, log_error

logger = setup_logger(__name__)


def get_aws_region() -> str:
    """
    Obtém a região AWS configurada

    Returns:
        Região AWS (padrão: us-east-1)
    """
    # Tenta obter região de várias fontes
    region = (
        os.getenv('AWS_DEFAULT_REGION') or
        os.getenv('AWS_REGION') or
        'us-east-1'  # Fallback padrão
    )
    return region


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
        sts_client = boto3.client('sts', region_name=get_aws_region())
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
        ec2_client = boto3.client('ec2', region_name=get_aws_region())
        response = ec2_client.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except Exception as e:
        log_error(logger, e, {"operation": "describe_regions"})
        return [get_aws_region()]  # Fallback para região configurada


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


def handle_aws_error(error: Exception, operation: str, raise_exception: bool = False) -> None:
    """
    Handler centralizado para erros AWS
    
    Args:
        error: Exceção capturada
        operation: Nome da operação que falhou
        raise_exception: Se deve relançar a exceção
    """
    error_details = {"operation": operation}
    
    if isinstance(error, ClientError):
        error_code = error.response.get('Error', {}).get('Code', 'Unknown')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        error_details.update({
            'error_code': error_code,
            'error_message': error_message
        })
        
        if error_code in ['AccessDeniedException', 'UnauthorizedAccess']:
            logger.warning(f"Access denied for operation: {operation}")
        elif error_code in ['ThrottlingException', 'RequestLimitExceeded']:
            logger.warning(f"Rate limit exceeded for operation: {operation}")
        else:
            log_error(logger, error, error_details)
    else:
        log_error(logger, error, error_details)
    
    if raise_exception:
        raise error
