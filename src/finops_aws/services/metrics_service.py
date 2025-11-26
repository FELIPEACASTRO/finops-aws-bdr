"""
Serviço para coleta de métricas de uso via AWS CloudWatch
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

from ..models.finops_models import EC2InstanceUsage, LambdaFunctionUsage
from ..utils.logger import setup_logger, log_api_call, log_error
from ..utils.aws_helpers import retry_with_backoff, safe_get_nested, get_aws_region

logger = setup_logger(__name__)

# Clientes globais para reutilização
_cloudwatch_client = None
_ec2_client = None
_lambda_client = None


def get_cloudwatch_client():
    """Obtém cliente CloudWatch (singleton)"""
    global _cloudwatch_client
    if _cloudwatch_client is None:
        _cloudwatch_client = boto3.client('cloudwatch', region_name=get_aws_region())
    return _cloudwatch_client


def get_ec2_client():
    """Obtém cliente EC2 (singleton)"""
    global _ec2_client
    if _ec2_client is None:
        _ec2_client = boto3.client('ec2', region_name=get_aws_region())
    return _ec2_client


def get_lambda_client():
    """Obtém cliente Lambda (singleton)"""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client('lambda', region_name=get_aws_region())
    return _lambda_client


class MetricsService:
    """Serviço para coleta de métricas de uso de recursos AWS"""

    def __init__(self):
        self.cloudwatch = get_cloudwatch_client()
        self.ec2 = get_ec2_client()
        self.lambda_client = get_lambda_client()

    @retry_with_backoff(max_retries=3)
    def get_ec2_instances(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de instâncias EC2 ativas

        Returns:
            Lista de instâncias EC2
        """
        try:
            start_time = datetime.now()
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )
            duration = (datetime.now() - start_time).total_seconds()

            log_api_call(logger, 'EC2', 'describe_instances', None, duration)

            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'InstanceId': instance.get('InstanceId'),
                        'InstanceType': instance.get('InstanceType'),
                        'State': instance.get('State', {}).get('Name'),
                        'AvailabilityZone': instance.get('Placement', {}).get('AvailabilityZone')
                    })

            logger.info(f"Found {len(instances)} EC2 instances")
            return instances

        except ClientError as e:
            log_error(logger, e, {'operation': 'describe_instances'})
            return []

    @retry_with_backoff(max_retries=3)
    def get_ec2_cpu_utilization(self, instance_id: str, days: int) -> Optional[float]:
        """
        Obtém utilização média de CPU para uma instância EC2

        Args:
            instance_id: ID da instância EC2
            days: Período de análise em dias

        Returns:
            Utilização média de CPU ou None se não disponível
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        params = {
            'Namespace': 'AWS/EC2',
            'MetricName': 'CPUUtilization',
            'Dimensions': [
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ],
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': 3600,  # 1 hora
            'Statistics': ['Average']
        }

        try:
            response = self.cloudwatch.get_metric_statistics(**params)

            datapoints = response.get('Datapoints', [])
            if not datapoints:
                logger.warning(f"No CPU metrics found for instance {instance_id}")
                return None

            # Calcula média dos datapoints
            avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
            return round(avg_cpu, 2)

        except ClientError as e:
            log_error(logger, e, {'instance_id': instance_id, 'days': days})
            return None

    def get_ec2_usage_data(self) -> List[EC2InstanceUsage]:
        """
        Obtém dados de uso para todas as instâncias EC2

        Returns:
            Lista de dados de uso de EC2
        """
        instances = self.get_ec2_instances()
        usage_data = []

        for instance in instances:
            instance_id = instance['InstanceId']

            # Só coleta métricas para instâncias em execução
            if instance['State'] != 'running':
                logger.info(f"Skipping metrics for {instance_id} (state: {instance['State']})")
                continue

            logger.info(f"Collecting CPU metrics for {instance_id}")

            usage = EC2InstanceUsage(
                instance_id=instance_id,
                instance_type=instance['InstanceType'],
                state=instance['State'],
                availability_zone=instance['AvailabilityZone']
            )

            # Coleta métricas para diferentes períodos
            for days, attr in [(7, 'avg_cpu_7d'), (15, 'avg_cpu_15d'), (30, 'avg_cpu_30d')]:
                cpu_avg = self.get_ec2_cpu_utilization(instance_id, days)
                setattr(usage, attr, cpu_avg)

            usage_data.append(usage)

        logger.info(f"Collected usage data for {len(usage_data)} EC2 instances")
        return usage_data

    @retry_with_backoff(max_retries=3)
    def get_lambda_functions(self) -> List[str]:
        """
        Obtém lista de funções Lambda

        Returns:
            Lista de nomes de funções Lambda
        """
        try:
            functions = []
            paginator = self.lambda_client.get_paginator('list_functions')

            for page in paginator.paginate():
                for function in page.get('Functions', []):
                    functions.append(function['FunctionName'])

            logger.info(f"Found {len(functions)} Lambda functions")
            return functions

        except ClientError as e:
            log_error(logger, e, {'operation': 'list_functions'})
            return []

    @retry_with_backoff(max_retries=3)
    def get_lambda_metrics(self, function_name: str, days: int = 7) -> Dict[str, Optional[float]]:
        """
        Obtém métricas de uma função Lambda

        Args:
            function_name: Nome da função Lambda
            days: Período de análise

        Returns:
            Dicionário com métricas da função
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        metrics = {
            'invocations': None,
            'duration': None,
            'errors': None,
            'throttles': None
        }

        metric_configs = [
            ('Invocations', 'Sum', 'invocations'),
            ('Duration', 'Average', 'duration'),
            ('Errors', 'Sum', 'errors'),
            ('Throttles', 'Sum', 'throttles')
        ]

        for metric_name, statistic, key in metric_configs:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'FunctionName',
                            'Value': function_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 1 dia
                    Statistics=[statistic]
                )

                datapoints = response.get('Datapoints', [])
                if datapoints:
                    if statistic == 'Sum':
                        metrics[key] = sum(dp[statistic] for dp in datapoints)
                    else:
                        metrics[key] = sum(dp[statistic] for dp in datapoints) / len(datapoints)

            except ClientError as e:
                logger.warning(f"Failed to get {metric_name} for {function_name}: {e}")
                continue

        return metrics

    def get_lambda_usage_data(self) -> List[LambdaFunctionUsage]:
        """
        Obtém dados de uso para todas as funções Lambda

        Returns:
            Lista de dados de uso de Lambda
        """
        functions = self.get_lambda_functions()
        usage_data = []

        for function_name in functions:
            logger.info(f"Collecting metrics for Lambda function {function_name}")

            metrics = self.get_lambda_metrics(function_name, days=7)

            usage = LambdaFunctionUsage(
                function_name=function_name,
                invocations_7d=int(metrics['invocations']) if metrics['invocations'] else None,
                avg_duration_7d=round(metrics['duration'], 2) if metrics['duration'] else None,
                errors_7d=int(metrics['errors']) if metrics['errors'] else None,
                throttles_7d=int(metrics['throttles']) if metrics['throttles'] else None
            )

            usage_data.append(usage)

        logger.info(f"Collected usage data for {len(usage_data)} Lambda functions")
        return usage_data

    def get_all_usage_data(self) -> Dict[str, List[Any]]:
        """
        Obtém dados de uso para todos os serviços suportados

        Returns:
            Dicionário com dados de uso por serviço
        """
        usage_data = {}

        try:
            usage_data['ec2'] = self.get_ec2_usage_data()
        except Exception as e:
            log_error(logger, e, {'service': 'ec2'})
            usage_data['ec2'] = []

        try:
            usage_data['lambda'] = self.get_lambda_usage_data()
        except Exception as e:
            log_error(logger, e, {'service': 'lambda'})
            usage_data['lambda'] = []

        return usage_data
