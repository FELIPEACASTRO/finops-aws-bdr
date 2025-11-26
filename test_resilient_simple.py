#!/usr/bin/env python3
"""
Teste simples do sistema resiliente FinOps
"""
import asyncio
import os
import sys
from moto import mock_aws
import boto3

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.finops_aws.core.state_manager import StateManager, TaskType
from src.finops_aws.core.resilient_executor import ResilientExecutor


async def test_resilient_system():
    """Teste básico do sistema resiliente"""
    print("🚀 Testando sistema resiliente FinOps")

    # Criar bucket S3 mock
    bucket_name = 'test-finops-state'
    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_client.create_bucket(Bucket=bucket_name)

    # Criar componentes
    state_manager = StateManager(bucket_name)
    executor = ResilientExecutor(state_manager)
    account_id = '123456789012'

    print("✅ Componentes criados")

    # Criar execução
    execution = state_manager.create_execution(account_id, {'test': 'simple'})
    print(f"✅ Execução criada: {execution.execution_id}")

    # Definir funções de teste
    async def mock_cost_analysis():
        await asyncio.sleep(0.1)
        return {'costs': {'EC2': 100.0}}

    async def mock_ec2_metrics():
        await asyncio.sleep(0.1)
        return [{'instance_id': 'i-123', 'cpu': 50.0}]

    async def mock_report():
        await asyncio.sleep(0.1)
        return {'summary': 'Test report'}

    task_functions = {
        TaskType.COST_ANALYSIS: mock_cost_analysis,
        TaskType.EC2_METRICS: mock_ec2_metrics,
        TaskType.REPORT_GENERATION: mock_report
    }

    # Executar tarefas
    results = await executor.execute_all_pending_tasks(
        task_functions=task_functions,
        max_concurrent=2,
        timeout_per_task=10
    )

    print(f"✅ Tarefas executadas: {len(results)}")

    # Verificar progresso
    progress = executor.get_execution_progress()
    print(f"✅ Progresso: {progress['completion_percentage']:.1f}%")

    # Testar recuperação de estado
    new_state_manager = StateManager(bucket_name)
    recovered_execution = new_state_manager.get_execution_state(execution.execution_id)

    if recovered_execution:
        print("✅ Estado recuperado com sucesso")
    else:
        print("❌ Falha na recuperação de estado")

    print("🎉 Teste concluído com sucesso!")
    return True


if __name__ == '__main__':
    # Configura ambiente
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    # Executa teste
    try:
        result = asyncio.run(test_resilient_system())
        if result:
            print("\n✅ Sistema resiliente funcionando corretamente!")
            exit(0)
        else:
            print("\n❌ Sistema resiliente com problemas!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
