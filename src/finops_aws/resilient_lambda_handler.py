"""
Lambda Handler Resiliente para FinOps AWS
Implementa recuperação de falhas, retry automático e execução incremental
"""
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from .core.state_manager import StateManager, TaskType
from .core.resilient_executor import ResilientExecutor
from .services.cost_service import CostService
from .services.metrics_service import MetricsService
from .services.optimizer_service import OptimizerService
from .models.finops_models import FinOpsReport
from .utils.logger import setup_logger, log_error
from .utils.aws_helpers import get_aws_account_id

# Configuração de logging
logger = setup_logger(__name__, os.getenv('LOG_LEVEL', 'INFO'))


class FinOpsResilientHandler:
    """
    Handler resiliente para execução de análises FinOps
    Implementa recuperação de estado e execução incremental
    """
    
    def __init__(self):
        self.state_manager = StateManager()
        self.executor = ResilientExecutor(self.state_manager)
        self.cost_service = CostService()
        self.metrics_service = MetricsService()
        self.optimizer_service = OptimizerService()

    async def handle_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Processa requisição com recuperação de estado
        
        Args:
            event: Evento da Lambda
            context: Contexto da Lambda
            
        Returns:
            Resposta da análise FinOps
        """
        start_time = datetime.now()
        request_id = context.aws_request_id if context else 'local'
        
        logger.info("Starting resilient FinOps AWS analysis", extra={
            'extra_data': {
                'request_id': request_id,
                'function_name': context.function_name if context else 'local'
            }
        })

        try:
            # Obtém ID da conta AWS
            account_id = get_aws_account_id()
            logger.info(f"Analyzing AWS account: {account_id}")

            # Cria ou recupera execução
            execution = self.state_manager.create_execution(
                account_id=account_id,
                metadata={
                    'request_id': request_id,
                    'lambda_function': context.function_name if context else 'local',
                    'event_source': event.get('source', 'unknown')
                }
            )

            logger.info(f"Using execution: {execution.execution_id}")

            # Define funções para cada tipo de tarefa
            task_functions = {
                TaskType.COST_ANALYSIS: self._analyze_costs,
                TaskType.EC2_METRICS: self._collect_ec2_metrics,
                TaskType.LAMBDA_METRICS: self._collect_lambda_metrics,
                TaskType.RDS_METRICS: self._collect_rds_metrics,
                TaskType.S3_METRICS: self._collect_s3_metrics,
                TaskType.EC2_RECOMMENDATIONS: self._get_ec2_recommendations,
                TaskType.LAMBDA_RECOMMENDATIONS: self._get_lambda_recommendations,
                TaskType.RDS_RECOMMENDATIONS: self._get_rds_recommendations,
                TaskType.REPORT_GENERATION: self._generate_report
            }

            # Executa tarefas com dependências
            max_concurrent = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))
            timeout_per_task = float(os.getenv('TASK_TIMEOUT_SECONDS', '300'))  # 5 minutos
            
            logger.info(f"Executing tasks with max_concurrent={max_concurrent}, timeout={timeout_per_task}s")
            
            results = await self.executor.execute_with_dependencies(
                task_functions=task_functions,
                max_concurrent=max_concurrent,
                timeout_per_task=timeout_per_task
            )

            # Verifica se a execução está completa
            if self.state_manager.is_execution_complete():
                self.state_manager.complete_execution()
                logger.info("Execution completed successfully")
            else:
                logger.warning("Execution incomplete, some tasks failed or were skipped")

            # Gera resposta final
            response = await self._build_response(results, start_time, request_id)
            
            # Log de conclusão
            duration = (datetime.now() - start_time).total_seconds()
            progress = self.executor.get_execution_progress()
            
            logger.info("FinOps analysis completed", extra={
                'extra_data': {
                    'duration_seconds': duration,
                    'execution_id': execution.execution_id,
                    'completion_percentage': progress.get('completion_percentage', 0),
                    'completed_tasks': progress.get('completed_tasks', 0),
                    'failed_tasks': progress.get('failed_tasks', 0)
                }
            })

            return response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            log_error(logger, e, {
                'request_id': request_id,
                'duration_seconds': duration,
                'execution_id': getattr(self.state_manager.current_execution, 'execution_id', None)
            })

            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'X-Request-ID': request_id
                },
                'body': json.dumps({
                    'error': 'Internal server error',
                    'message': str(e),
                    'request_id': request_id,
                    'execution_id': getattr(self.state_manager.current_execution, 'execution_id', None),
                    'progress': self.executor.get_execution_progress()
                })
            }

    async def _analyze_costs(self) -> Dict[str, Any]:
        """Executa análise de custos"""
        logger.info("Analyzing costs...")
        
        # Coleta custos para diferentes períodos
        costs = {}
        periods = [7, 15, 30]
        
        for days in periods:
            try:
                period_costs = self.cost_service.get_costs_by_service(days)
                costs[f"last_{days}_days"] = period_costs
                logger.info(f"Collected costs for {days} days: {len(period_costs)} services")
            except Exception as e:
                logger.error(f"Failed to collect costs for {days} days: {e}")
                costs[f"last_{days}_days"] = {}
        
        return costs

    async def _collect_ec2_metrics(self) -> Any:
        """Coleta métricas do EC2"""
        logger.info("Collecting EC2 metrics...")
        
        try:
            ec2_data = self.metrics_service.get_ec2_usage_data()
            logger.info(f"Collected metrics for {len(ec2_data)} EC2 instances")
            return ec2_data
        except Exception as e:
            logger.error(f"Failed to collect EC2 metrics: {e}")
            return []

    async def _collect_lambda_metrics(self) -> Any:
        """Coleta métricas do Lambda"""
        logger.info("Collecting Lambda metrics...")
        
        try:
            lambda_data = self.metrics_service.get_lambda_usage_data()
            logger.info(f"Collected metrics for {len(lambda_data)} Lambda functions")
            return lambda_data
        except Exception as e:
            logger.error(f"Failed to collect Lambda metrics: {e}")
            return []

    async def _collect_rds_metrics(self) -> Any:
        """Coleta métricas do RDS"""
        logger.info("Collecting RDS metrics...")
        
        try:
            logger.info("RDS metrics collection not implemented yet")
            return []
        except Exception as e:
            logger.error(f"Failed to collect RDS metrics: {e}")
            return []

    async def _collect_s3_metrics(self) -> Any:
        """Coleta métricas do S3"""
        logger.info("Collecting S3 metrics...")
        
        try:
            logger.info("S3 metrics collection not implemented yet")
            return []
        except Exception as e:
            logger.error(f"Failed to collect S3 metrics: {e}")
            return []

    async def _get_ec2_recommendations(self) -> Any:
        """Obtém recomendações do EC2"""
        logger.info("Getting EC2 recommendations...")
        
        try:
            recommendations = self.optimizer_service.get_ec2_recommendations()
            logger.info(f"Got {len(recommendations)} EC2 recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Failed to get EC2 recommendations: {e}")
            return []

    async def _get_lambda_recommendations(self) -> Any:
        """Obtém recomendações do Lambda"""
        logger.info("Getting Lambda recommendations...")
        
        try:
            recommendations = self.optimizer_service.get_lambda_recommendations()
            logger.info(f"Got {len(recommendations)} Lambda recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Failed to get Lambda recommendations: {e}")
            return []

    async def _get_rds_recommendations(self) -> Any:
        """Obtém recomendações do RDS"""
        logger.info("Getting RDS recommendations...")
        
        try:
            logger.info("RDS recommendations not implemented yet")
            return []
        except Exception as e:
            logger.error(f"Failed to get RDS recommendations: {e}")
            return []

    async def _generate_report(self) -> Dict[str, Any]:
        """Gera relatório consolidado"""
        logger.info("Generating consolidated report...")
        
        try:
            # Coleta resultados das tarefas concluídas
            completed_tasks = self.state_manager.get_completed_tasks()
            
            costs = {}
            usage = {}
            recommendations = {}
            
            for task in completed_tasks:
                if not task.result_data:
                    continue
                    
                if task.task_type == TaskType.COST_ANALYSIS:
                    costs = task.result_data
                elif task.task_type == TaskType.EC2_METRICS:
                    usage['ec2'] = task.result_data
                elif task.task_type == TaskType.LAMBDA_METRICS:
                    usage['lambda'] = task.result_data
                elif task.task_type == TaskType.RDS_METRICS:
                    usage['rds'] = task.result_data
                elif task.task_type == TaskType.S3_METRICS:
                    usage['s3'] = task.result_data
                elif task.task_type == TaskType.EC2_RECOMMENDATIONS:
                    recommendations['ec2_recommendations'] = task.result_data
                elif task.task_type == TaskType.LAMBDA_RECOMMENDATIONS:
                    recommendations['lambda_recommendations'] = task.result_data
                elif task.task_type == TaskType.RDS_RECOMMENDATIONS:
                    recommendations['rds_recommendations'] = task.result_data

            # Cria relatório consolidado
            current_exec = self.state_manager.current_execution
            account_id = current_exec.account_id if current_exec else 'unknown'
            report = FinOpsReport(
                account_id=account_id,
                generated_at=datetime.now(),
                costs=costs,
                usage=usage,
                optimizer=recommendations
            )

            # Calcula economia total
            total_savings = self.optimizer_service.calculate_total_savings_potential(recommendations)
            
            # Gera resumo
            summary = self._generate_summary(costs, usage, recommendations, total_savings)
            
            result = report.to_dict()
            result['summary'] = summary
            result['execution_metadata'] = self.executor.get_execution_progress()
            
            logger.info("Report generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

    def _generate_summary(
        self,
        costs: Dict[str, Dict[str, float]],
        usage: Dict[str, Any],
        recommendations: Dict[str, Any],
        total_savings: float
    ) -> Dict[str, Any]:
        """Gera resumo executivo"""
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

            summary['usage_insights']['ec2'] = {
                'total_instances': len(ec2_instances),
                'running_instances': len(running_instances),
                'low_utilization_instances': len(low_cpu_instances),
                'avg_cpu_utilization_30d': round(
                    sum(i.avg_cpu_30d for i in running_instances if hasattr(i, 'avg_cpu_30d') and i.avg_cpu_30d) /
                    len([i for i in running_instances if hasattr(i, 'avg_cpu_30d') and i.avg_cpu_30d]),
                    2
                ) if running_instances else 0
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
            if isinstance(rec_list, list):
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

    async def _build_response(
        self,
        results: Dict[str, Any],
        start_time: datetime,
        request_id: str
    ) -> Dict[str, Any]:
        """Constrói resposta final"""
        
        # Obtém resultado do relatório
        report_task_id = None
        for task_id, result in results.items():
            if 'report_generation' in task_id:
                report_task_id = task_id
                break

        if report_task_id and results.get(report_task_id):
            # Sucesso - retorna relatório completo
            report_data = results[report_task_id]
            report_data['partial'] = False
            report_data['execution_status'] = 'complete'
            status_code = 200
        else:
            # Falha parcial - retorna progresso e dados disponíveis com status 200
            completed_tasks = self.state_manager.get_completed_tasks()
            partial_data = {}
            
            for task in completed_tasks:
                if task.result_data:
                    partial_data[task.task_type.value] = task.result_data
            
            report_data = {
                'partial_results': partial_data,
                'partial': True,
                'execution_status': 'incomplete',
                'progress': self.executor.get_execution_progress(),
                'message': 'Analysis completed with some failures. Partial results available.'
            }
            status_code = 200  # Sempre retorna 200, usa campo 'partial' para indicar estado

        # Adiciona metadados de execução
        duration = (datetime.now() - start_time).total_seconds()
        current_exec = self.state_manager.current_execution
        execution_id = current_exec.execution_id if current_exec else 'unknown'
        report_data['execution_metadata'] = {
            'duration_seconds': duration,
            'execution_id': execution_id,
            'request_id': request_id,
            'completed_at': datetime.now().isoformat()
        }

        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': request_id,
                'X-Execution-ID': execution_id
            },
            'body': json.dumps(report_data, default=str, indent=2)
        }


# Instância global do handler
_handler_instance = None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Entry point para AWS Lambda
    Usa handler resiliente com recuperação de estado
    """
    global _handler_instance
    
    # Cria instância única do handler (reutilização entre invocações)
    if _handler_instance is None:
        _handler_instance = FinOpsResilientHandler()
    
    # Executa de forma assíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            _handler_instance.handle_request(event, context)
        )
    finally:
        loop.close()


# Função para execução local/teste
def main():
    """Função principal para execução local"""
    import sys

    # Simula contexto da Lambda para teste local
    class MockContext:
        aws_request_id = 'local-test-request'
        function_name = 'finops-aws-resilient'

    try:
        result = lambda_handler({}, MockContext())
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    exit(main())