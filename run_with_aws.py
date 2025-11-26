#!/usr/bin/env python3
"""
FinOps AWS - Execução Local com Conta AWS Real

Este script executa a análise FinOps conectando à sua conta AWS real.
Requer credenciais AWS configuradas.

Uso:
  1. Configure suas credenciais AWS (veja instruções abaixo)
  2. Execute: python run_with_aws.py

Configuração de Credenciais:
  Opção A - Variáveis de ambiente (recomendado para Replit):
    Adicione no painel de Secrets do Replit:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION (opcional, padrão: us-east-1)

  Opção B - AWS Profile:
    Configure ~/.aws/credentials com seu perfil

Permissões IAM Necessárias:
  - ce:GetCostAndUsage (Cost Explorer)
  - cloudwatch:GetMetricData
  - compute-optimizer:GetRecommendations
  - ec2:Describe* (instâncias, volumes, snapshots)
  - lambda:ListFunctions, lambda:GetFunction
  - s3:ListBuckets, s3:GetBucketLocation
  - rds:DescribeDBInstances
  - dynamodb:ListTables, dynamodb:DescribeTable
  - ecs:ListClusters, ecs:DescribeClusters
  - elasticache:DescribeCacheClusters
  - redshift:DescribeClusters
  - kafka:ListClustersV2, kafka:DescribeClusterV2 (MSK)
  - E outros serviços que você quiser analisar...

Para política IAM completa, veja: infrastructure/iam-policy.json
"""
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
from tabulate import tabulate

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def print_banner():
    print("=" * 80)
    print("  FinOps AWS - Análise de Custos e Otimização")
    print("  Execução Local com Conta AWS Real")
    print("=" * 80)
    print()


def check_aws_credentials() -> bool:
    """Verifica se as credenciais AWS estão configuradas"""
    print("Verificando credenciais AWS...")
    print()
    
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    profile = os.getenv('AWS_PROFILE')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if access_key and secret_key:
        print(f"  ✓ AWS_ACCESS_KEY_ID: {access_key[:4]}...{access_key[-4:]}")
        print(f"  ✓ AWS_SECRET_ACCESS_KEY: ****")
        print(f"  ✓ AWS_REGION: {region}")
        return True
    elif profile:
        print(f"  ✓ AWS_PROFILE: {profile}")
        return True
    elif os.path.exists(os.path.expanduser('~/.aws/credentials')):
        print("  ✓ Arquivo ~/.aws/credentials encontrado")
        return True
    else:
        print("  ✗ NENHUMA CREDENCIAL AWS ENCONTRADA!")
        print()
        print("  Configure suas credenciais:")
        print("    1. Adicione AWS_ACCESS_KEY_ID nos Secrets do Replit")
        print("    2. Adicione AWS_SECRET_ACCESS_KEY nos Secrets do Replit")
        print("    3. Opcionalmente, adicione AWS_REGION (padrão: us-east-1)")
        print()
        return False


def test_aws_connection() -> Dict[str, Any]:
    """Testa conexão com AWS e retorna informações da conta"""
    import boto3
    
    print("Testando conexão com AWS...")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"  ✓ Account ID: {identity['Account']}")
        print(f"  ✓ User ARN: {identity['Arn']}")
        print()
        return identity
    except Exception as e:
        print(f"  ✗ Erro de conexão: {e}")
        return None


def run_service_analysis(service_name: str, service_instance) -> Dict[str, Any]:
    """Executa análise de um serviço específico"""
    result = {
        'service': service_name,
        'success': False,
        'resources': 0,
        'recommendations': 0,
        'error': None
    }
    
    try:
        if service_instance.health_check():
            resources = service_instance.get_resources()
            recommendations = service_instance.get_recommendations()
            
            result['success'] = True
            result['resources'] = len(resources) if isinstance(resources, list) else 1
            result['recommendations'] = len(recommendations)
        else:
            result['error'] = "Health check failed"
    except Exception as e:
        result['error'] = str(e)[:50]
    
    return result


def run_full_analysis():
    """Executa análise completa de todos os serviços"""
    from finops_aws.core.factories import ServiceFactory, AWSClientFactory
    
    print("=" * 80)
    print("Iniciando Análise FinOps Completa...")
    print("=" * 80)
    print()
    
    AWSClientFactory.reset_instance()
    ServiceFactory.reset_instance()
    
    factory = ServiceFactory()
    
    services_to_analyze = [
        ('S3', 'get_s3_service'),
        ('EC2', 'get_ec2_finops_service'),
        ('Lambda', 'get_lambda_finops_service'),
        ('RDS', 'get_rds_service'),
        ('DynamoDB', 'get_dynamodb_service'),
        ('EBS', 'get_ebs_service'),
        ('EFS', 'get_efs_service'),
        ('ElastiCache', 'get_elasticache_service'),
        ('ECS', 'get_ecs_service'),
        ('Redshift', 'get_redshift_service'),
        ('CloudFront', 'get_cloudfront_service'),
        ('ELB', 'get_elb_service'),
        ('EMR', 'get_emr_service'),
        ('VPC/NAT', 'get_vpc_network_service'),
        ('Kinesis', 'get_kinesis_service'),
        ('Glue', 'get_glue_service'),
        ('SageMaker', 'get_sagemaker_service'),
        ('Route53', 'get_route53_service'),
        ('Backup', 'get_backup_service'),
        ('SNS/SQS', 'get_sns_sqs_service'),
        ('Secrets Manager', 'get_secrets_manager_service'),
        ('MSK (Kafka)', 'get_msk_service'),
    ]
    
    results = []
    total_resources = 0
    total_recommendations = 0
    
    for service_name, getter_name in services_to_analyze:
        print(f"  Analisando {service_name}...", end=" ", flush=True)
        
        try:
            service = getattr(factory, getter_name)()
            result = run_service_analysis(service_name, service)
            results.append(result)
            
            if result['success']:
                total_resources += result['resources']
                total_recommendations += result['recommendations']
                print(f"✓ {result['resources']} recursos, {result['recommendations']} recomendações")
            else:
                print(f"⚠ {result['error']}")
        except Exception as e:
            print(f"✗ {str(e)[:40]}")
            results.append({
                'service': service_name,
                'success': False,
                'resources': 0,
                'recommendations': 0,
                'error': str(e)[:50]
            })
    
    print()
    print("=" * 80)
    print("RESUMO DA ANÁLISE")
    print("=" * 80)
    print()
    
    table_data = []
    for r in results:
        status = "✓" if r['success'] else "✗"
        table_data.append([
            r['service'],
            status,
            r['resources'],
            r['recommendations'],
            r['error'] or '-'
        ])
    
    print(tabulate(
        table_data,
        headers=['Serviço', 'Status', 'Recursos', 'Recomendações', 'Erro'],
        tablefmt='simple'
    ))
    
    print()
    print("-" * 80)
    print(f"Total de Recursos Encontrados: {total_resources}")
    print(f"Total de Recomendações: {total_recommendations}")
    print(f"Serviços Analisados: {len([r for r in results if r['success']])}/{len(results)}")
    print("-" * 80)
    
    return results


def run_cost_analysis():
    """Executa análise de custos via Cost Explorer"""
    from finops_aws.services.cost_service import CostService
    
    print("=" * 80)
    print("Análise de Custos (últimos 30 dias)")
    print("=" * 80)
    print()
    
    try:
        cost_service = CostService()
        costs = cost_service.get_all_period_costs()
        
        if costs and 'last_30_days' in costs:
            last_30 = costs['last_30_days']
            
            table_data = []
            total = 0
            
            sorted_services = sorted(last_30.items(), key=lambda x: x[1], reverse=True)
            
            for service, cost in sorted_services[:15]:
                table_data.append([service, f"${cost:.2f}"])
                total += cost
            
            print(tabulate(
                table_data,
                headers=['Serviço AWS', 'Custo (USD)'],
                tablefmt='simple'
            ))
            
            print()
            print(f"TOTAL (últimos 30 dias): ${total:.2f}")
            
        return costs
    except Exception as e:
        print(f"Erro ao obter custos: {e}")
        print()
        print("Nota: Cost Explorer requer permissão ce:GetCostAndUsage")
        print("      e a conta precisa ter Cost Explorer ativado.")
        return None


def run_single_service(service_name: str):
    """Executa análise de um único serviço"""
    from finops_aws.core.factories import ServiceFactory, AWSClientFactory
    
    AWSClientFactory.reset_instance()
    ServiceFactory.reset_instance()
    
    factory = ServiceFactory()
    
    service_map = {
        's3': 'get_s3_service',
        'ec2': 'get_ec2_finops_service',
        'lambda': 'get_lambda_finops_service',
        'rds': 'get_rds_service',
        'dynamodb': 'get_dynamodb_service',
        'msk': 'get_msk_service',
        'kafka': 'get_msk_service',
        'ecs': 'get_ecs_service',
        'redshift': 'get_redshift_service',
    }
    
    getter = service_map.get(service_name.lower())
    if not getter:
        print(f"Serviço '{service_name}' não encontrado.")
        print(f"Serviços disponíveis: {', '.join(service_map.keys())}")
        return
    
    print(f"Analisando serviço: {service_name.upper()}")
    print("=" * 80)
    
    service = getattr(factory, getter)()
    
    print("\nRecursos:")
    resources = service.get_resources()
    print(json.dumps(resources[:5] if len(resources) > 5 else resources, indent=2, default=str))
    
    if len(resources) > 5:
        print(f"... e mais {len(resources) - 5} recursos")
    
    print("\nRecomendações:")
    recommendations = service.get_recommendations()
    for rec in recommendations[:5]:
        print(f"  - [{rec.recommendation_type}] {rec.title or rec.description[:50]}")
        if rec.estimated_savings > 0:
            print(f"    Economia estimada: ${rec.estimated_savings:.2f}/mês")
    
    if len(recommendations) > 5:
        print(f"  ... e mais {len(recommendations) - 5} recomendações")


def main():
    print_banner()
    
    if not check_aws_credentials():
        print()
        print("Configure as credenciais AWS e tente novamente.")
        return 1
    
    print()
    identity = test_aws_connection()
    
    if not identity:
        return 1
    
    print("Escolha uma opção:")
    print("  1. Análise completa de todos os serviços")
    print("  2. Análise de custos (Cost Explorer)")
    print("  3. Análise de serviço específico")
    print("  4. Executar Lambda Handler completo")
    print()
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Opção (1-4) [padrão: 1]: ").strip() or "1"
    
    print()
    
    if choice == "1":
        run_full_analysis()
    elif choice == "2":
        run_cost_analysis()
    elif choice == "3":
        if len(sys.argv) > 2:
            service = sys.argv[2]
        else:
            service = input("Nome do serviço (s3, ec2, msk, lambda, etc): ").strip()
        run_single_service(service)
    elif choice == "4":
        from finops_aws.lambda_handler import lambda_handler
        
        class RealContext:
            aws_request_id = f'local-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            function_name = 'finops-aws-local'
            invoked_function_arn = f'arn:aws:lambda:us-east-1:{identity["Account"]}:function:finops-aws'
            memory_limit_in_mb = '1024'
        
        event = {
            'source': 'local.execution',
            'detail-type': 'Manual Analysis',
            'time': datetime.now().isoformat()
        }
        
        result = lambda_handler(event, RealContext())
        print(json.dumps(json.loads(result['body']), indent=2, default=str))
    else:
        print(f"Opção inválida: {choice}")
        return 1
    
    print()
    print("=" * 80)
    print("Análise concluída!")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
