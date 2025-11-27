#!/usr/bin/env python3
"""
FinOps AWS - Teste Rápido
Executa um teste rápido do sistema para validar funcionamento.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

from moto import mock_aws

@mock_aws
def run_tests():
    """Executa todos os testes dentro do mock AWS"""
    from finops_aws.core.factories import ServiceFactory, AWSClientFactory
    from finops_aws.lambda_mapper import lambda_handler as mapper_handler
    from finops_aws.lambda_aggregator import _aggregate_results
    
    import boto3
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='finops-aws-reports')
    
    print("1. Testando imports...")
    print("   ✓ Todos os imports OK")
    
    print()
    print("2. Testando ServiceFactory...")
    AWSClientFactory.reset_instance()
    ServiceFactory.reset_instance()
    factory = ServiceFactory()
    services = factory.get_all_services()
    print(f"   ✓ {len(services)} serviços registrados")
    
    print()
    print("3. Testando Lambda Mapper...")
    class FakeContext:
        aws_request_id = "test-123"
    
    event = {"input": {}}
    result = mapper_handler(event, FakeContext())
    print(f"   ✓ Mapper retornou {result.get('total_batches', 0)} batches")
    print(f"   ✓ Total de {result.get('total_services', 0)} serviços")
    
    print()
    print("4. Testando Lambda Aggregator...")
    batch_results = [
        {
            "services": {"ec2": {"status": "ok"}},
            "costs": {"by_service": {"ec2": 100.0}},
            "recommendations": [{"service": "ec2", "savings": 10}],
            "savings_potential": {"by_service": {"ec2": 10.0}},
            "metrics": {"resources_analyzed": 5}
        }
    ]
    
    aggregated = _aggregate_results(batch_results)
    print(f"   ✓ Aggregator processou {len(aggregated.get('services', {}))} serviços")
    print(f"   ✓ Custo total: ${aggregated['costs']['total']:.2f}")
    
    print()
    print("5. Testando serviços principais...")
    main_services = ['ec2', 's3', 'rds', 'lambda', 'dynamodb']
    for svc_name in main_services:
        svc_key = f"{svc_name}_service"
        if svc_key in services:
            svc = services[svc_key]
            if hasattr(svc, 'health_check'):
                print(f"   ✓ {svc_name.upper()}: health_check disponível")
            else:
                print(f"   ✓ {svc_name.upper()}: serviço disponível")
    
    return 0


def main():
    print("=" * 60)
    print("  FinOps AWS - Teste Rápido (com Mocks)")
    print("=" * 60)
    print()
    
    try:
        result = run_tests()
        
        print()
        print("=" * 60)
        print("  TESTE RÁPIDO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print()
        print("  Próximos passos:")
        print("    1. Deploy: ./scripts/deploy_and_test.sh")
        print("    2. Teste completo: python scripts/test_all_services.py")
        print("    3. Teste com AWS: python scripts/test_all_services.py --aws")
        print()
        
        return result
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
