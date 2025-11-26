"""
Configuração de logging estruturado para FinOps AWS
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formatador JSON para logs estruturados"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Adiciona informações extras se disponíveis
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Configura logger com formatação JSON

    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Evita duplicação de handlers
    if logger.handlers:
        return logger

    # Define nível de log
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level.upper()))

    # Configura handler
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger


def log_api_call(logger: logging.Logger, service: str, operation: str,
                 params: Dict[str, Any] = None, duration: float = None):
    """
    Log estruturado para chamadas de API AWS

    Args:
        logger: Logger instance
        service: Nome do serviço AWS
        operation: Nome da operação
        params: Parâmetros da chamada
        duration: Duração da chamada em segundos
    """
    extra_data = {
        "aws_service": service,
        "aws_operation": operation,
        "api_call": True
    }

    if params:
        extra_data["parameters"] = params
    if duration is not None:
        extra_data["duration_seconds"] = duration

    logger.info(f"AWS API call: {service}.{operation}", extra={'extra_data': extra_data})


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """
    Log estruturado para erros

    Args:
        logger: Logger instance
        error: Exceção capturada
        context: Contexto adicional do erro
    """
    extra_data = {
        "error_type": type(error).__name__,
        "error_message": str(error)
    }

    if context:
        extra_data["context"] = context

    logger.error(f"Error occurred: {error}", extra={'extra_data': extra_data}, exc_info=True)
