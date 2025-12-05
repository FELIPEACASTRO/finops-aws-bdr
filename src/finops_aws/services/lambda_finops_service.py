"""
Lambda FinOps Service - Análise de Custos e Otimização de Funções Lambda

FASE 2 - Prioridade 1: Serverless Compute
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de funções Lambda com configurações
- Análise de memória e duração de execução
- Detecção de funções ociosas ou superprovisionadas
- Recomendações de rightsizing de memória
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class LambdaFunction:
    """Representa uma função Lambda"""
    function_name: str
    function_arn: str
    runtime: str
    memory_size: int
    timeout: int
    code_size: int
    handler: str
    last_modified: str
    description: str = ""
    role: str = ""
    vpc_config: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    layers: List[str] = field(default_factory=list)
    architectures: List[str] = field(default_factory=lambda: ["x86_64"])
    ephemeral_storage: int = 512
    package_type: str = "Zip"
    state: str = "Active"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'function_name': self.function_name,
            'function_arn': self.function_arn,
            'runtime': self.runtime,
            'memory_size': self.memory_size,
            'timeout': self.timeout,
            'code_size': self.code_size,
            'handler': self.handler,
            'last_modified': self.last_modified,
            'architectures': self.architectures,
            'ephemeral_storage': self.ephemeral_storage,
            'state': self.state
        }


@dataclass
class LambdaMetricsData:
    """Métricas de uma função Lambda"""
    function_name: str
    invocations: int = 0
    errors: int = 0
    throttles: int = 0
    duration_avg_ms: float = 0.0
    duration_max_ms: float = 0.0
    concurrent_executions_max: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'function_name': self.function_name,
            'invocations': self.invocations,
            'errors': self.errors,
            'throttles': self.throttles,
            'duration_avg_ms': self.duration_avg_ms,
            'duration_max_ms': self.duration_max_ms,
            'concurrent_executions_max': self.concurrent_executions_max,
            'error_rate': round((self.errors / self.invocations * 100) if self.invocations > 0 else 0, 2)
        }


class LambdaFinOpsService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Lambda
    
    Analisa funções Lambda, invocações, duração e fornece
    recomendações de otimização de memória e custos.
    """
    
    def __init__(
        self,
        lambda_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._lambda_client = lambda_client
    
    @property
    def lambda_client(self):
        if self._lambda_client is None:
            import boto3
            self._lambda_client = boto3.client('lambda')
        return self._lambda_client
    
    def get_service_name(self) -> str:
        return "AWS Lambda"
    
    def health_check(self) -> bool:
        try:
            self.lambda_client.list_functions(MaxItems=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    
    def get_functions(self) -> List[LambdaFunction]:
        """Lista todas as funções Lambda"""
        functions = []
        
        paginator = self.lambda_client.get_paginator('list_functions')
        
        for page in paginator.paginate():
            for func in page.get('Functions', []):
                function = LambdaFunction(
                    function_name=func['FunctionName'],
                    function_arn=func['FunctionArn'],
                    runtime=func.get('Runtime', 'unknown'),
                    memory_size=func['MemorySize'],
                    timeout=func['Timeout'],
                    code_size=func['CodeSize'],
                    handler=func.get('Handler', ''),
                    last_modified=func['LastModified'],
                    description=func.get('Description', ''),
                    role=func['Role'],
                    vpc_config=func.get('VpcConfig', {}),
                    environment=func.get('Environment', {}).get('Variables', {}),
                    layers=[l['Arn'] for l in func.get('Layers', [])],
                    architectures=func.get('Architectures', ['x86_64']),
                    ephemeral_storage=func.get('EphemeralStorage', {}).get('Size', 512),
                    package_type=func.get('PackageType', 'Zip'),
                    state=func.get('State', 'Active')
                )
                functions.append(function)
        
        return functions
    
    
    def get_function_metrics(self, function_name: str, days: int = 7) -> LambdaMetricsData:
        """
        Obtém métricas de uma função Lambda
        
        Args:
            function_name: Nome da função
            days: Período de análise
        
        Returns:
            LambdaMetricsData com métricas agregadas
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        metrics_data = LambdaMetricsData(function_name=function_name)
        
        invocations = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400 * days,
            Statistics=['Sum']
        )
        if invocations.get('Datapoints'):
            metrics_data.invocations = int(sum(d['Sum'] for d in invocations['Datapoints']))
        
        errors = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400 * days,
            Statistics=['Sum']
        )
        if errors.get('Datapoints'):
            metrics_data.errors = int(sum(d['Sum'] for d in errors['Datapoints']))
        
        throttles = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Throttles',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400 * days,
            Statistics=['Sum']
        )
        if throttles.get('Datapoints'):
            metrics_data.throttles = int(sum(d['Sum'] for d in throttles['Datapoints']))
        
        duration = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400 * days,
            Statistics=['Average', 'Maximum']
        )
        if duration.get('Datapoints'):
            metrics_data.duration_avg_ms = round(
                sum(d['Average'] for d in duration['Datapoints']) / len(duration['Datapoints']), 2
            )
            metrics_data.duration_max_ms = round(
                max(d['Maximum'] for d in duration['Datapoints']), 2
            )
        
        concurrent = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='ConcurrentExecutions',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400 * days,
            Statistics=['Maximum']
        )
        if concurrent.get('Datapoints'):
            metrics_data.concurrent_executions_max = int(
                max(d['Maximum'] for d in concurrent['Datapoints'])
            )
        
        return metrics_data
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        functions = self.get_functions()
        return [func.to_dict() for func in functions]
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Lambda"""
        functions = self.get_functions()
        
        total_invocations = 0
        total_errors = 0
        total_throttles = 0
        runtimes = {}
        memory_distribution = {'small': 0, 'medium': 0, 'large': 0}
        
        for func in functions:
            if func.runtime:
                runtimes[func.runtime] = runtimes.get(func.runtime, 0) + 1
            
            if func.memory_size <= 512:
                memory_distribution['small'] += 1
            elif func.memory_size <= 1024:
                memory_distribution['medium'] += 1
            else:
                memory_distribution['large'] += 1
            
            try:
                metrics = self.get_function_metrics(func.function_name, days=7)
                total_invocations += metrics.invocations
                total_errors += metrics.errors
                total_throttles += metrics.throttles
            except Exception as e:  # noqa: E722
                pass
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(functions),
            metrics={
                'total_functions': len(functions),
                'total_invocations_7d': total_invocations,
                'total_errors_7d': total_errors,
                'total_throttles_7d': total_throttles,
                'error_rate': round((total_errors / total_invocations * 100) if total_invocations > 0 else 0, 2),
                'runtimes': runtimes,
                'memory_distribution': memory_distribution,
                'period_days': 7,
                'collected_at': datetime.now(timezone.utc).isoformat()
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Lambda"""
        recommendations = []
        functions = self.get_functions()
        
        for func in functions:
            try:
                metrics = self.get_function_metrics(func.function_name, days=30)
                
                if metrics.invocations == 0:
                    recommendations.append(ServiceRecommendation(
                        resource_id=func.function_name,
                        resource_type='Lambda Function',
                        recommendation_type='UNUSED_FUNCTION',
                        title=f'Função sem invocações nos últimos 30 dias',
                        description=f'Função {func.function_name} não foi invocada nos últimos 30 dias. '
                                   f'Considere removê-la ou verificar se está configurada corretamente.',
                        estimated_savings=5.0,
                        priority='MEDIUM',
                        action='Remover função não utilizada'
                    ))
                    continue
                
                if metrics.duration_max_ms > 0 and func.timeout * 1000 > metrics.duration_max_ms * 3:
                    new_timeout = int(metrics.duration_max_ms * 2 / 1000) + 1
                    recommendations.append(ServiceRecommendation(
                        resource_id=func.function_name,
                        resource_type='Lambda Function',
                        recommendation_type='TIMEOUT_OPTIMIZATION',
                        title=f'Timeout superdimensionado',
                        description=f'Função {func.function_name} tem timeout de {func.timeout}s mas '
                                   f'duração máxima de {metrics.duration_max_ms/1000:.1f}s. '
                                   f'Considere reduzir para {new_timeout}s.',
                        estimated_savings=0.0,
                        priority='LOW',
                        action=f'Reduzir timeout para {new_timeout}s'
                    ))
                
                if func.memory_size >= 1024 and metrics.duration_avg_ms < 1000:
                    recommendations.append(ServiceRecommendation(
                        resource_id=func.function_name,
                        resource_type='Lambda Function',
                        recommendation_type='MEMORY_OVERSIZED',
                        title=f'Memória potencialmente superdimensionada',
                        description=f'Função {func.function_name} tem {func.memory_size}MB mas '
                                   f'executa rapidamente (média {metrics.duration_avg_ms:.0f}ms). '
                                   f'Use Power Tuning para otimizar memória.',
                        estimated_savings=10.0,
                        priority='MEDIUM',
                        action='Executar AWS Lambda Power Tuning'
                    ))
                
                if metrics.throttles > 0:
                    throttle_rate = (metrics.throttles / metrics.invocations * 100) if metrics.invocations > 0 else 0
                    if throttle_rate > 1:
                        recommendations.append(ServiceRecommendation(
                            resource_id=func.function_name,
                            resource_type='Lambda Function',
                            recommendation_type='THROTTLING',
                            title=f'Taxa de throttling elevada ({throttle_rate:.1f}%)',
                            description=f'Função {func.function_name} teve {metrics.throttles} throttles '
                                       f'({throttle_rate:.1f}%). Considere aumentar concorrência reservada.',
                            estimated_savings=0.0,
                            priority='HIGH',
                            action='Aumentar reserved concurrency'
                        ))
                
                error_rate = (metrics.errors / metrics.invocations * 100) if metrics.invocations > 0 else 0
                if error_rate > 5:
                    recommendations.append(ServiceRecommendation(
                        resource_id=func.function_name,
                        resource_type='Lambda Function',
                        recommendation_type='HIGH_ERROR_RATE',
                        title=f'Taxa de erros elevada ({error_rate:.1f}%)',
                        description=f'Função {func.function_name} teve {metrics.errors} erros '
                                   f'({error_rate:.1f}%). Investigue e corrija problemas.',
                        estimated_savings=0.0,
                        priority='HIGH',
                        action='Investigar logs de erros'
                    ))
                
            except Exception as e:  # noqa: E722
                pass
        
        deprecated_runtimes = ['python2.7', 'python3.6', 'nodejs10.x', 'nodejs12.x', 'ruby2.5', 'dotnetcore2.1']
        for func in functions:
            if func.runtime in deprecated_runtimes:
                recommendations.append(ServiceRecommendation(
                    resource_id=func.function_name,
                    resource_type='Lambda Function',
                    recommendation_type='DEPRECATED_RUNTIME',
                    title=f'Runtime depreciado: {func.runtime}',
                    description=f'Função {func.function_name} usa runtime {func.runtime} que está '
                               f'depreciado ou será em breve. Atualize para versão mais recente.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Atualizar runtime'
                ))
        
        for func in functions:
            if 'x86_64' in func.architectures and 'arm64' not in func.architectures:
                recommendations.append(ServiceRecommendation(
                    resource_id=func.function_name,
                    resource_type='Lambda Function',
                    recommendation_type='ARM_MIGRATION',
                    title=f'Candidata a migração para ARM (Graviton2)',
                    description=f'Função {func.function_name} usa x86_64. Migrar para arm64 '
                               f'pode reduzir custos em até 34% com performance similar ou melhor.',
                    estimated_savings=func.memory_size * 0.00001667 * 0.34 * 30,
                    priority='MEDIUM',
                    action='Migrar para arquitetura arm64'
                ))
        
        return recommendations
