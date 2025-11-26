#!/usr/bin/env python3
"""
Script de teste para o sistema resiliente FinOps
Testa recuperação de falhas, retry e circuit breaker
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from moto import mock_aws
import boto3

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.finops_aws.core.state_manager import StateManager, TaskType
from src.finops_aws.core.resilient_executor import ResilientExecutor
from src.finops_aws.utils.logger import setup_logger

logger = setup_logger(__name__)


class TestFinOpsResilientSystem:
    """Classe de teste para o sistema resiliente"""

    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or 'finops-test-state'
        self.state_manager = StateManager(self.bucket_name)
        self.executor = ResilientExecutor(self.state_manager)
        self.account_id = '123456789012'

    async def test_basic_execution(self):
        """Testa execução básica sem falhas"""
        print("\n=== Teste 1: Execução Básica ===")

        # Cria execução
        execution = self.state_manager.create_execution(
            self.account_id,
            {'test': 'basic_execution'}
        )
        print(f"Criada execução: {execution.execution_id}")

        # Define funções de teste simples
        task_functions = {
            TaskType.COST_ANALYSIS: self._mock_cost_analysis,
            TaskType.EC2_METRICS: self._mock_ec2_metrics,
            TaskType.LAMBDA_METRICS: self._mock_lambda_metrics,
            TaskType.EC2_RECOMMENDATIONS: self._mock_ec2_recommendations,
            TaskType.REPORT_GENERATION: self._mock_report_generation
        }

        # Executa tarefas
        results = await self.executor.execute_with_dependencies(
            task_functions=task_functions,
            max_concurrent=2,
            timeout_per_task=30
        )

        print(f"Resultados: {len(results)} tarefas executadas")

        # Verifica se execução está completa
        if self.state_manager.is_execution_complete():
            self.state_manager.complete_execution()
            print("✅ Execução concluída com sucesso")
        else:
            print("❌ Execução incompleta")

        return results

    async def test_execution_with_failures(self):
        """Testa execução com falhas e retry"""
        print("\n=== Teste 2: Execução com Falhas e Retry ===")

        # Cria execução
        execution = self.state_manager.create_execution(
            self.account_id,
            {'test': 'execution_with_failures'}
        )
        print(f"Criada execução: {execution.execution_id}")

        # Define funções com falhas simuladas
        task_functions = {
            TaskType.COST_ANALYSIS: self._mock_cost_analysis_with_retry,
            TaskType.EC2_METRICS: self._mock_failing_task,
            TaskType.LAMBDA_METRICS: self._mock_lambda_metrics,
            TaskType.EC2_RECOMMENDATIONS: self._mock_ec2_recommendations,
            TaskType.REPORT_GENERATION: self._mock_report_generation
        }

        # Executa tarefas
        results = await self.executor.execute_with_dependencies(
            task_functions=task_functions,
            max_concurrent=2,
            timeout_per_task=30
        )

        print(f"Resultados: {len(results)} tarefas executadas")

        # Mostra progresso
        progress = self.executor.get_execution_progress()
        print(f"Progresso: {progress['completion_percentage']:.1f}%")
        print(f"Tarefas concluídas: {progress['completed_tasks']}")
        print(f"Tarefas falhadas: {progress['failed_tasks']}")

        return results

    async def test_execution_recovery(self):
        """Testa recuperação de execução interrompida"""
        print("\n=== Teste 3: Recuperação de Execução ===")

        # Cria execução inicial
        execution1 = self.state_manager.create_execution(
            self.account_id,
            {'test': 'execution_recovery'}
        )
        print(f"Criada execução inicial: {execution1.execution_id}")

        # Executa apenas algumas tarefas
        task_functions = {
            TaskType.COST_ANALYSIS: self._mock_cost_analysis,
            TaskType.EC2_METRICS: self._mock_ec2_metrics
        }

        await self.executor.execute_all_pending_tasks(
            task_functions=task_functions,
            max_concurrent=1
        )

        print("Execução parcial concluída")

        # Simula nova instância (recuperação)
        new_state_manager = StateManager(self.bucket_name)
        new_executor = ResilientExecutor(new_state_manager)

        # Recupera execução
        recovered_execution = new_state_manager.create_execution(self.account_id)
        print(f"Recuperada execução: {recovered_execution.execution_id}")

        if recovered_execution.execution_id == execution1.execution_id:
            print("✅ Execução recuperada com sucesso")

            # Continua execução
            remaining_functions = {
                TaskType.LAMBDA_METRICS: self._mock_lambda_metrics,
                TaskType.EC2_RECOMMENDATIONS: self._mock_ec2_recommendations,
                TaskType.REPORT_GENERATION: self._mock_report_generation
            }

            results = await new_executor.execute_all_pending_tasks(
                task_functions=remaining_functions,
                max_concurrent=2
            )

            print(f"Execução continuada: {len(results)} tarefas adicionais")
        else:
            print("❌ Nova execução criada ao invés de recuperar")

    async def test_circuit_breaker(self):
        """Testa circuit breaker"""
        print("\n=== Teste 4: Circuit Breaker ===")

        # Cria execução
        execution = self.state_manager.create_execution(
            self.account_id,
            {'test': 'circuit_breaker'}
        )
        print(f"Criada execução: {execution.execution_id}")

        # Função que sempre falha para disparar circuit breaker
        async def always_fails():
            raise Exception("Simulated failure for circuit breaker test")

        # Tenta executar tarefa que sempre falha
        task_id = f"{TaskType.COST_ANALYSIS.value}_{execution.execution_id}"

        try:
            await self.executor.execute_task(
                task_id, always_fails, TaskType.COST_ANALYSIS
            )
        except Exception as e:
            print(f"Tarefa falhou como esperado: {e}")

        # Verifica estado do circuit breaker
        progress = self.executor.get_execution_progress()
        cb_status = progress.get('circuit_breakers', {})
        cost_analysis_cb = cb_status.get(TaskType.COST_ANALYSIS.value, {})

        print(f"Circuit Breaker Status: {cost_analysis_cb}")

        # Tenta executar novamente (deve ser rejeitado se circuit breaker abriu)
        try:
            await self.executor.execute_task(
                f"{TaskType.COST_ANALYSIS.value}_2_{execution.execution_id}",
                always_fails, TaskType.COST_ANALYSIS
            )
        except Exception as e:
            if "Circuit breaker open" in str(e):
                print("✅ Circuit breaker funcionando corretamente")
            else:
                print(f"❌ Erro inesperado: {e}")

    async def test_timeout_handling(self):
        """Testa tratamento de timeout"""
        print("\n=== Teste 5: Tratamento de Timeout ===")

        # Cria execução
        execution = self.state_manager.create_execution(
            self.account_id,
            {'test': 'timeout_handling'}
        )
        print(f"Criada execução: {execution.execution_id}")

        # Função que demora muito
        async def slow_task():
            await asyncio.sleep(10)  # 10 segundos
            return {'data': 'slow'}

        task_id = f"{TaskType.COST_ANALYSIS.value}_{execution.execution_id}"

        try:
            await self.executor.execute_task(
                task_id, slow_task, TaskType.COST_ANALYSIS, timeout=2  # 2 segundos
            )
        except asyncio.TimeoutError:
            print("✅ Timeout tratado corretamente")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

    # Funções mock para simular tarefas
    async def _mock_cost_analysis(self):
        """Mock da análise de custos"""
        await asyncio.sleep(0.1)  # Simula processamento
        return {
            'last_30_days': {
                'Amazon EC2': 100.50,
                'Amazon S3': 25.30,
                'AWS Lambda': 5.20
            }
        }

    async def _mock_cost_analysis_with_retry(self):
        """Mock que falha na primeira tentativa"""
        if not hasattr(self, '_cost_analysis_attempts'):
            self._cost_analysis_attempts = 0

        self._cost_analysis_attempts += 1

        if self._cost_analysis_attempts == 1:
            raise Exception("First attempt fails")

        await asyncio.sleep(0.1)
        return await self._mock_cost_analysis()

    async def _mock_ec2_metrics(self):
        """Mock das métricas EC2"""
        await asyncio.sleep(0.1)
        return [
            {
                'instance_id': 'i-1234567890abcdef0',
                'instance_type': 't3.medium',
                'state': 'running',
                'avg_cpu_30d': 45.2
            }
        ]

    async def _mock_lambda_metrics(self):
        """Mock das métricas Lambda"""
        await asyncio.sleep(0.1)
        return [
            {
                'function_name': 'test-function',
                'invocations_7d': 1000,
                'avg_duration_7d': 150.5,
                'errors_7d': 2
            }
        ]

    async def _mock_ec2_recommendations(self):
        """Mock das recomendações EC2"""
        await asyncio.sleep(0.1)
        return [
            {
                'resource_id': 'i-1234567890abcdef0',
                'finding': 'OVER_PROVISIONED',
                'recommended_instance_type': 't3.small',
                'estimated_monthly_savings': 25.50
            }
        ]

    async def _mock_failing_task(self):
        """Mock de tarefa que sempre falha"""
        raise Exception("This task always fails for testing")

    async def _mock_report_generation(self):
        """Mock da geração de relatório"""
        await asyncio.sleep(0.1)
        return {
            'summary': {
                'total_estimated_monthly_savings': 25.50,
                'total_cost_last_30_days': 130.00
            }
        }

    def print_execution_summary(self):
        """Imprime resumo da execução atual"""
        if not self.state_manager.current_execution:
            print("Nenhuma execução ativa")
            return

        summary = self.state_manager.get_execution_summary()

        print(f"\n=== Resumo da Execução ===")
        print(f"ID: {summary['execution_id']}")
        print(f"Status: {summary['status']}")
        print(f"Progresso: {summary['completion_percentage']:.1f}%")
        print(f"Tarefas: {summary['completed_tasks']}/{summary['total_tasks']}")
        print(f"Falhas: {summary['failed_tasks']}")


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do sistema resiliente FinOps")

    # Usa bucket de teste (pode não existir - será criado se necessário)
    test_system = TestFinOpsResilientSystem('finops-test-state-local')

    try:
        # Teste 1: Execução básica
        await test_system.test_basic_execution()
        test_system.print_execution_summary()

        # Teste 2: Execução com falhas
        await test_system.test_execution_with_failures()
        test_system.print_execution_summary()

        # Teste 3: Recuperação de execução
        await test_system.test_execution_recovery()

        # Teste 4: Circuit breaker
        await test_system.test_circuit_breaker()

        # Teste 5: Timeout
        await test_system.test_timeout_handling()

        print("\n✅ Todos os testes concluídos!")

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    # Configura variáveis de ambiente para teste
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    # Executa testes
    exit(asyncio.run(main()))
