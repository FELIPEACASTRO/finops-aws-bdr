"""
Serviço para coleta de recomendações de otimização via AWS Compute Optimizer
"""
import boto3
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

from ..models.finops_models import OptimizationRecommendation
from ..utils.logger import setup_logger, log_api_call, log_error
from ..utils.aws_helpers import retry_with_backoff, safe_get_nested, get_aws_region

logger = setup_logger(__name__)

# Cliente global para reutilização
_compute_optimizer_client = None


def get_compute_optimizer_client():
    """Obtém cliente Compute Optimizer (singleton)"""
    global _compute_optimizer_client
    if _compute_optimizer_client is None:
        _compute_optimizer_client = boto3.client('compute-optimizer', region_name=get_aws_region())
    return _compute_optimizer_client


class OptimizerService:
    """Serviço para coleta de recomendações de otimização AWS"""

    def __init__(self):
        self.client = get_compute_optimizer_client()
        self._optimizer_enabled = None

    def is_compute_optimizer_enabled(self) -> bool:
        """
        Verifica se o Compute Optimizer está habilitado

        Returns:
            True se habilitado, False caso contrário
        """
        if self._optimizer_enabled is not None:
            return self._optimizer_enabled

        try:
            # Tenta fazer uma chamada simples para verificar se está habilitado
            self.client.get_enrollment_status()
            self._optimizer_enabled = True
            logger.info("Compute Optimizer is enabled")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['OptInRequiredException', 'AccessDeniedException']:
                logger.warning("Compute Optimizer is not enabled or accessible")
                self._optimizer_enabled = False
                return False
            else:
                log_error(logger, e, {'operation': 'get_enrollment_status'})
                self._optimizer_enabled = False
                return False

    @retry_with_backoff(max_retries=3)
    def get_ec2_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Obtém recomendações de otimização para instâncias EC2

        Returns:
            Lista de recomendações de EC2
        """
        if not self.is_compute_optimizer_enabled():
            logger.info("Skipping EC2 recommendations - Compute Optimizer not enabled")
            return []

        recommendations = []

        try:
            # Usa paginação para obter todas as recomendações
            paginator = self.client.get_paginator('get_ec2_instance_recommendations')

            for page in paginator.paginate():
                for rec in page.get('instanceRecommendations', []):
                    recommendation = self._process_ec2_recommendation(rec)
                    if recommendation:
                        recommendations.append(recommendation)

            logger.info(f"Retrieved {len(recommendations)} EC2 recommendations")
            return recommendations

        except ClientError as e:
            log_error(logger, e, {'operation': 'get_ec2_instance_recommendations'})
            return []

    def _process_ec2_recommendation(self, rec: Dict) -> Optional[OptimizationRecommendation]:
        """
        Processa uma recomendação de EC2 do Compute Optimizer

        Args:
            rec: Recomendação bruta da API

        Returns:
            Recomendação processada ou None se inválida
        """
        try:
            instance_arn = rec.get('instanceArn', '')
            instance_id = instance_arn.split('/')[-1] if instance_arn else 'unknown'

            current_type = rec.get('currentInstanceType', 'unknown')
            finding = rec.get('finding', 'UNKNOWN')

            # Extrai tipos recomendados
            recommended_types = []
            for option in rec.get('recommendationOptions', []):
                instance_type = option.get('instanceType')
                if instance_type:
                    recommended_types.append(instance_type)

            # Calcula economia estimada (pega a primeira opção)
            estimated_savings = None
            if rec.get('recommendationOptions'):
                first_option = rec['recommendationOptions'][0]
                savings_data = first_option.get('estimatedMonthlySavings', {})
                if savings_data and savings_data.get('value'):
                    estimated_savings = float(savings_data['value'])

            # Extrai métricas de utilização
            utilization_metrics = {}
            for metric in rec.get('utilizationMetrics', []):
                metric_name = metric.get('name', '').lower()
                metric_value = safe_get_nested(metric, ['statistic', 'maximum'], 0)
                if metric_name and metric_value:
                    utilization_metrics[metric_name] = float(metric_value)

            return OptimizationRecommendation(
                resource_id=instance_id,
                resource_type='EC2',
                current_configuration=current_type,
                recommended_configurations=recommended_types,
                estimated_monthly_savings=estimated_savings,
                finding=finding,
                utilization_metrics=utilization_metrics
            )

        except Exception as e:
            log_error(logger, e, {'recommendation_data': rec})
            return None

    @retry_with_backoff(max_retries=3)
    def get_lambda_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Obtém recomendações de otimização para funções Lambda

        Returns:
            Lista de recomendações de Lambda
        """
        if not self.is_compute_optimizer_enabled():
            logger.info("Skipping Lambda recommendations - Compute Optimizer not enabled")
            return []

        recommendations = []

        try:
            paginator = self.client.get_paginator('get_lambda_function_recommendations')

            for page in paginator.paginate():
                for rec in page.get('lambdaFunctionRecommendations', []):
                    recommendation = self._process_lambda_recommendation(rec)
                    if recommendation:
                        recommendations.append(recommendation)

            logger.info(f"Retrieved {len(recommendations)} Lambda recommendations")
            return recommendations

        except ClientError as e:
            # Lambda recommendations podem não estar disponíveis em todas as regiões
            if e.response.get('Error', {}).get('Code') == 'InvalidParameterValueException':
                logger.info("Lambda recommendations not available in this region")
            else:
                log_error(logger, e, {'operation': 'get_lambda_function_recommendations'})
            return []

    def _process_lambda_recommendation(self, rec: Dict) -> Optional[OptimizationRecommendation]:
        """
        Processa uma recomendação de Lambda do Compute Optimizer

        Args:
            rec: Recomendação bruta da API

        Returns:
            Recomendação processada ou None se inválida
        """
        try:
            function_arn = rec.get('functionArn', '')
            function_name = function_arn.split(':')[-1] if function_arn else 'unknown'

            current_memory = rec.get('currentMemorySize', 0)
            finding = rec.get('finding', 'UNKNOWN')

            # Extrai configurações recomendadas
            recommended_configs = []
            estimated_savings = None

            for option in rec.get('memorySizeRecommendationOptions', []):
                memory_size = option.get('memorySize')
                if memory_size:
                    recommended_configs.append(f"{memory_size}MB")

                # Pega economia da primeira opção
                if estimated_savings is None:
                    savings_data = option.get('estimatedMonthlySavings', {})
                    if savings_data and savings_data.get('value'):
                        estimated_savings = float(savings_data['value'])

            # Extrai métricas de utilização
            utilization_metrics = {}
            for metric in rec.get('utilizationMetrics', []):
                metric_name = metric.get('name', '').lower()
                metric_value = safe_get_nested(metric, ['statistic', 'maximum'], 0)
                if metric_name and metric_value:
                    utilization_metrics[metric_name] = float(metric_value)

            return OptimizationRecommendation(
                resource_id=function_name,
                resource_type='Lambda',
                current_configuration=f"{current_memory}MB",
                recommended_configurations=recommended_configs,
                estimated_monthly_savings=estimated_savings,
                finding=finding,
                utilization_metrics=utilization_metrics
            )

        except Exception as e:
            log_error(logger, e, {'recommendation_data': rec})
            return None

    def get_all_recommendations(self) -> Dict[str, List[OptimizationRecommendation]]:
        """
        Obtém todas as recomendações de otimização disponíveis

        Returns:
            Dicionário com recomendações por tipo de recurso
        """
        recommendations = {}

        try:
            recommendations['ec2_recommendations'] = self.get_ec2_recommendations()
        except Exception as e:
            log_error(logger, e, {'service': 'ec2_recommendations'})
            recommendations['ec2_recommendations'] = []

        try:
            recommendations['lambda_recommendations'] = self.get_lambda_recommendations()
        except Exception as e:
            log_error(logger, e, {'service': 'lambda_recommendations'})
            recommendations['lambda_recommendations'] = []

        total_recommendations = sum(len(recs) for recs in recommendations.values())
        logger.info(f"Retrieved {total_recommendations} total optimization recommendations")

        return recommendations

    def calculate_total_savings_potential(self, recommendations: Dict[str, List[OptimizationRecommendation]]) -> float:
        """
        Calcula o potencial total de economia

        Args:
            recommendations: Dicionário com recomendações

        Returns:
            Economia total estimada mensal
        """
        total_savings = 0.0

        for rec_list in recommendations.values():
            for rec in rec_list:
                if rec.estimated_monthly_savings:
                    total_savings += rec.estimated_monthly_savings

        return round(total_savings, 2)
