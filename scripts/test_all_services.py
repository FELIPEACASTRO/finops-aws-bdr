#!/usr/bin/env python3
"""
FinOps AWS - Teste de Todos os 252 Serviços AWS

Este script testa todos os serviços implementados de forma fácil.
Pode ser executado localmente (com mocks) ou contra AWS real.

Uso:
    python scripts/test_all_services.py              # Teste com mocks
    python scripts/test_all_services.py --aws        # Teste com AWS real
    python scripts/test_all_services.py --category compute  # Apenas categoria
    python scripts/test_all_services.py --service ec2       # Apenas um serviço
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_category(text: str):
    print(f"\n{'─' * 50}")
    print(f"  {text}")
    print(f"{'─' * 50}")


def test_service(service_name: str, service_instance: Any) -> Dict[str, Any]:
    """Testa um serviço individual"""
    result = {
        'name': service_name,
        'success': False,
        'health_check': False,
        'resources': 0,
        'recommendations': 0,
        'metrics': {},
        'duration_ms': 0,
        'error': None
    }
    
    start_time = time.time()
    
    try:
        if hasattr(service_instance, 'health_check'):
            result['health_check'] = service_instance.health_check()
        else:
            result['health_check'] = True
        
        if hasattr(service_instance, 'get_resources'):
            resources = service_instance.get_resources()
            result['resources'] = len(resources) if isinstance(resources, list) else 1
        
        if hasattr(service_instance, 'get_recommendations'):
            recs = service_instance.get_recommendations()
            result['recommendations'] = len(recs) if isinstance(recs, list) else 0
        
        if hasattr(service_instance, 'get_metrics'):
            metrics = service_instance.get_metrics()
            if hasattr(metrics, 'metrics'):
                result['metrics'] = metrics.metrics
            elif isinstance(metrics, dict):
                result['metrics'] = metrics
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)[:100]
    
    result['duration_ms'] = int((time.time() - start_time) * 1000)
    return result


def get_all_services(use_aws: bool = False) -> Dict[str, Any]:
    """Obtém todos os serviços da factory"""
    if not use_aws:
        os.environ['MOTO_ALLOW_NONEXISTENT_REGION'] = 'true'
        import moto
        
    from finops_aws.core.factories import ServiceFactory, AWSClientFactory
    
    AWSClientFactory.reset_instance()
    ServiceFactory.reset_instance()
    
    factory = ServiceFactory()
    return factory.get_all_services()


def get_service_categories() -> Dict[str, List[str]]:
    """Define categorias de serviços"""
    return {
        'compute': ['ec2', 'lambda', 'ecs', 'eks', 'fargate', 'batch', 'lightsail', 'apprunner', 'elasticbeanstalk'],
        'storage': ['s3', 'ebs', 'efs', 'fsx', 'glacier', 'storagegateway', 'backup'],
        'database': ['rds', 'aurora', 'dynamodb', 'elasticache', 'redshift', 'neptune', 'documentdb', 'timestream', 'memorydb'],
        'networking': ['vpc', 'cloudfront', 'route53', 'elb', 'apigateway', 'directconnect', 'globalaccelerator', 'transitgateway'],
        'security': ['iam', 'kms', 'secretsmanager', 'guardduty', 'securityhub', 'macie', 'inspector', 'waf', 'shield'],
        'analytics': ['athena', 'emr', 'kinesis', 'glue', 'quicksight', 'opensearch', 'msk', 'lakeformation'],
        'ai_ml': ['sagemaker', 'bedrock', 'comprehend', 'rekognition', 'textract', 'polly', 'transcribe', 'translate'],
        'management': ['cloudwatch', 'cloudtrail', 'config', 'organizations', 'controltower', 'ssm', 'servicecatalog'],
        'cost': ['costexplorer', 'budgets', 'cur', 'computeoptimizer', 'savingsplans'],
        'messaging': ['sns', 'sqs', 'eventbridge', 'mq', 'ses'],
        'developer': ['codecommit', 'codebuild', 'codepipeline', 'codedeploy', 'codeartifact', 'cloud9'],
        'iot': ['iot', 'iotanalytics', 'greengrass', 'iotevents', 'iotsitewise'],
        'media': ['mediaconvert', 'medialive', 'mediapackage', 'ivs', 'elementalmediaconnect'],
        'enduser': ['workspaces', 'appstream', 'workdocs', 'chime', 'connect']
    }


def run_tests(
    use_aws: bool = False,
    category: Optional[str] = None,
    service_filter: Optional[str] = None,
    parallel: bool = True,
    max_workers: int = 10
) -> Dict[str, Any]:
    """Executa testes em todos os serviços"""
    
    print_header(f"FinOps AWS - Teste de Serviços ({'AWS Real' if use_aws else 'Mocks'})")
    
    if use_aws:
        import boto3
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"  Account: {identity['Account']}")
            print(f"  User: {identity['Arn']}")
        except Exception as e:
            print(f"  ERRO: Não foi possível conectar à AWS: {e}")
            return {'error': str(e)}
    
    print("\nCarregando serviços...")
    
    if not use_aws:
        from moto import mock_aws
        mock = mock_aws()
        mock.start()
    
    try:
        all_services = get_all_services(use_aws)
        categories = get_service_categories()
        
        services_to_test = {}
        
        if service_filter:
            for name, instance in all_services.items():
                if service_filter.lower() in name.lower():
                    services_to_test[name] = instance
        elif category:
            category_services = categories.get(category.lower(), [])
            for name, instance in all_services.items():
                service_key = name.lower().replace('_service', '').replace('service', '')
                if any(cat_svc in service_key for cat_svc in category_services):
                    services_to_test[name] = instance
        else:
            services_to_test = all_services
        
        print(f"  Total de serviços a testar: {len(services_to_test)}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'aws' if use_aws else 'mock',
            'total_services': len(services_to_test),
            'successful': 0,
            'failed': 0,
            'services': [],
            'by_category': {},
            'duration_seconds': 0
        }
        
        start_time = time.time()
        
        if parallel and len(services_to_test) > 5:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(test_service, name, instance): name
                    for name, instance in services_to_test.items()
                }
                
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        result = future.result()
                        results['services'].append(result)
                        
                        if result['success']:
                            results['successful'] += 1
                            status = "✓"
                        else:
                            results['failed'] += 1
                            status = "✗"
                        
                        print(f"  {status} {name}: {result.get('resources', 0)} recursos, "
                              f"{result.get('recommendations', 0)} recs, "
                              f"{result['duration_ms']}ms")
                    except Exception as e:
                        print(f"  ✗ {name}: ERRO - {e}")
                        results['failed'] += 1
        else:
            for name, instance in services_to_test.items():
                result = test_service(name, instance)
                results['services'].append(result)
                
                if result['success']:
                    results['successful'] += 1
                    status = "✓"
                else:
                    results['failed'] += 1
                    status = "✗"
                
                print(f"  {status} {name}: {result.get('resources', 0)} recursos, "
                      f"{result.get('recommendations', 0)} recs, "
                      f"{result['duration_ms']}ms")
        
        results['duration_seconds'] = round(time.time() - start_time, 2)
        
        for cat_name, cat_services in categories.items():
            cat_results = [
                r for r in results['services']
                if any(cs in r['name'].lower() for cs in cat_services)
            ]
            if cat_results:
                results['by_category'][cat_name] = {
                    'total': len(cat_results),
                    'successful': sum(1 for r in cat_results if r['success']),
                    'failed': sum(1 for r in cat_results if not r['success'])
                }
        
        return results
        
    finally:
        if not use_aws:
            mock.stop()


def print_summary(results: Dict[str, Any]):
    """Imprime resumo dos resultados"""
    print_header("RESUMO DOS TESTES")
    
    total = results['total_services']
    success = results['successful']
    failed = results['failed']
    success_rate = (success / total * 100) if total > 0 else 0
    
    print(f"  Modo: {'AWS Real' if results['mode'] == 'aws' else 'Mocks'}")
    print(f"  Total de Serviços: {total}")
    print(f"  Sucessos: {success} ({success_rate:.1f}%)")
    print(f"  Falhas: {failed}")
    print(f"  Duração: {results['duration_seconds']}s")
    
    if results.get('by_category'):
        print("\n  Por Categoria:")
        for cat, stats in sorted(results['by_category'].items()):
            rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"    {cat}: {stats['successful']}/{stats['total']} ({rate:.0f}%)")
    
    if failed > 0:
        print("\n  Serviços com Falha:")
        for svc in results['services']:
            if not svc['success']:
                print(f"    ✗ {svc['name']}: {svc.get('error', 'Unknown error')[:60]}")


def main():
    parser = argparse.ArgumentParser(
        description='Teste todos os 252 serviços AWS do FinOps'
    )
    parser.add_argument(
        '--aws', action='store_true',
        help='Usar AWS real ao invés de mocks'
    )
    parser.add_argument(
        '--category', type=str,
        help='Testar apenas uma categoria (compute, storage, database, etc)'
    )
    parser.add_argument(
        '--service', type=str,
        help='Testar apenas serviços que contenham este nome'
    )
    parser.add_argument(
        '--sequential', action='store_true',
        help='Executar testes sequencialmente (não em paralelo)'
    )
    parser.add_argument(
        '--workers', type=int, default=10,
        help='Número de workers paralelos (padrão: 10)'
    )
    parser.add_argument(
        '--output', type=str,
        help='Salvar resultados em arquivo JSON'
    )
    
    args = parser.parse_args()
    
    results = run_tests(
        use_aws=args.aws,
        category=args.category,
        service_filter=args.service,
        parallel=not args.sequential,
        max_workers=args.workers
    )
    
    if 'error' not in results:
        print_summary(results)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n  Resultados salvos em: {args.output}")
    
    sys.exit(0 if results.get('failed', 0) == 0 else 1)


if __name__ == '__main__':
    main()
