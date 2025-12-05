"""
FinOps AWS - Hierarquia de Exceções

Design Pattern: Exception Hierarchy
SOLID: Single Responsibility - cada exceção tem propósito específico
Pythonic: Exceções específicas ao invés de genéricas
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class FinOpsError(Exception):
    """
    Exceção base para todos os erros FinOps AWS.
    
    Attributes:
        message: Mensagem descritiva do erro
        code: Código do erro para identificação
        details: Detalhes adicionais do erro
    """
    message: str
    code: str = "FINOPS_ERROR"
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


@dataclass
class AWSServiceError(FinOpsError):
    """Erro ao interagir com serviço AWS."""
    service_name: str = ""
    region: str = ""
    code: str = "AWS_SERVICE_ERROR"
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.service_name} ({self.region}): {self.message}"


@dataclass 
class AWSClientError(AWSServiceError):
    """Erro de cliente AWS (credenciais, permissões)."""
    code: str = "AWS_CLIENT_ERROR"


@dataclass
class AWSThrottlingError(AWSServiceError):
    """Rate limiting da AWS."""
    retry_after: float = 0.0
    code: str = "AWS_THROTTLING"


@dataclass
class AWSResourceNotFoundError(AWSServiceError):
    """Recurso AWS não encontrado."""
    resource_id: str = ""
    code: str = "AWS_RESOURCE_NOT_FOUND"


@dataclass
class AnalysisError(FinOpsError):
    """Erro durante análise de custos/recursos."""
    analyzer_name: str = ""
    code: str = "ANALYSIS_ERROR"


@dataclass
class ValidationError(FinOpsError):
    """Erro de validação de dados."""
    field_name: str = ""
    expected: str = ""
    received: str = ""
    code: str = "VALIDATION_ERROR"
    
    def __str__(self) -> str:
        return f"[{self.code}] Campo '{self.field_name}': esperado {self.expected}, recebido {self.received}"


@dataclass
class ConfigurationError(FinOpsError):
    """Erro de configuração."""
    config_key: str = ""
    code: str = "CONFIG_ERROR"


@dataclass
class ExportError(FinOpsError):
    """Erro ao exportar relatório."""
    format: str = ""
    code: str = "EXPORT_ERROR"


@dataclass
class IntegrationError(FinOpsError):
    """Erro de integração externa."""
    integration_name: str = ""
    code: str = "INTEGRATION_ERROR"


@dataclass
class CostExplorerError(AWSServiceError):
    """Erro específico do Cost Explorer."""
    code: str = "COST_EXPLORER_ERROR"


@dataclass
class ComputeOptimizerError(AWSServiceError):
    """Erro específico do Compute Optimizer."""
    code: str = "COMPUTE_OPTIMIZER_ERROR"


@dataclass
class TrustedAdvisorError(AWSServiceError):
    """Erro específico do Trusted Advisor."""
    requires_support_plan: bool = False
    code: str = "TRUSTED_ADVISOR_ERROR"


@dataclass
class AmazonQError(IntegrationError):
    """Erro específico do Amazon Q Business."""
    application_id: str = ""
    code: str = "AMAZON_Q_ERROR"


def handle_boto3_error(error: Exception, service_name: str, region: str = "") -> AWSServiceError:
    """
    Converte exceção boto3 em exceção FinOps tipada.
    
    Args:
        error: Exceção original do boto3
        service_name: Nome do serviço AWS
        region: Região AWS
        
    Returns:
        Exceção FinOps apropriada
    """
    error_str = str(error)
    error_code = getattr(error, 'response', {}).get('Error', {}).get('Code', '')
    
    if 'AccessDenied' in error_str or error_code == 'AccessDenied':
        return AWSClientError(
            message=f"Acesso negado ao serviço {service_name}",
            service_name=service_name,
            region=region,
            details={"original_error": error_str}
        )
    
    if 'Throttling' in error_str or error_code == 'Throttling':
        return AWSThrottlingError(
            message=f"Rate limit excedido para {service_name}",
            service_name=service_name,
            region=region,
            retry_after=1.0,
            details={"original_error": error_str}
        )
    
    if 'NotFound' in error_str or 'NoSuch' in error_str:
        return AWSResourceNotFoundError(
            message=f"Recurso não encontrado em {service_name}",
            service_name=service_name,
            region=region,
            details={"original_error": error_str}
        )
    
    if 'SubscriptionRequiredException' in error_str:
        return TrustedAdvisorError(
            message="Trusted Advisor requer AWS Business ou Enterprise Support",
            service_name=service_name,
            region=region,
            requires_support_plan=True,
            details={"original_error": error_str}
        )
    
    return AWSServiceError(
        message=f"Erro no serviço {service_name}: {error_str[:200]}",
        service_name=service_name,
        region=region,
        details={"original_error": error_str}
    )
