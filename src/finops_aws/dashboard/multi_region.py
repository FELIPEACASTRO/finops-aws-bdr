"""
Multi-Region Analysis for FinOps Dashboard

Análise de custos e recursos em múltiplas regiões AWS.
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1',
    'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
    'ap-southeast-1', 'ap-southeast-2',
    'ap-south-1',
    'sa-east-1',
    'ca-central-1',
    'me-south-1',
    'af-south-1'
]


def get_enabled_regions() -> List[str]:
    """
    Obtém lista de regiões habilitadas na conta AWS.
    
    Returns:
        Lista de regiões habilitadas
    """
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        response = ec2.describe_regions(
            Filters=[{'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}]
        )
        return [r['RegionName'] for r in response.get('Regions', [])]
    except ClientError as e:
        logger.error(f"Erro ao obter regiões: {e}")
        return AWS_REGIONS[:4]


def analyze_region(region: str) -> Tuple[str, Dict[str, Any]]:
    """
    Analisa recursos e custos em uma região específica.
    
    Args:
        region: Código da região AWS
        
    Returns:
        Tupla com (região, dados da análise)
    """
    result = {
        'region': region,
        'resources': {},
        'recommendations': [],
        'costs': 0,
        'status': 'success'
    }
    
    try:
        ec2 = boto3.client('ec2', region_name=region)
        instances = ec2.describe_instances()
        all_instances = []
        for res in instances.get('Reservations', []):
            all_instances.extend(res.get('Instances', []))
        result['resources']['ec2_instances'] = len(all_instances)
        
        running = sum(1 for i in all_instances if i.get('State', {}).get('Name') == 'running')
        stopped = sum(1 for i in all_instances if i.get('State', {}).get('Name') == 'stopped')
        
        if stopped > 0:
            result['recommendations'].append({
                'type': 'EC2_STOPPED',
                'resource_id': f'{region}-ec2',
                'title': f'{stopped} instâncias EC2 paradas em {region}',
                'description': f'Considere terminar {stopped} instâncias paradas na região {region}',
                'priority': 'MEDIUM',
                'savings': stopped * 5,
                'service': 'EC2 Analysis'
            })
        
        volumes = ec2.describe_volumes()
        result['resources']['ebs_volumes'] = len(volumes.get('Volumes', []))
        
        orphan_volumes = [v for v in volumes.get('Volumes', []) 
                        if v.get('State') == 'available' and not v.get('Attachments')]
        
        if orphan_volumes:
            total_size = sum(v.get('Size', 0) for v in orphan_volumes)
            savings = total_size * 0.10
            result['recommendations'].append({
                'type': 'EBS_ORPHAN',
                'resource_id': f'{region}-ebs',
                'title': f'{len(orphan_volumes)} volumes EBS órfãos em {region}',
                'description': f'{len(orphan_volumes)} volumes ({total_size}GB) não anexados na região {region}',
                'priority': 'HIGH',
                'savings': round(savings, 2),
                'service': 'EBS Analysis'
            })
        
        try:
            rds = boto3.client('rds', region_name=region)
            db_instances = rds.describe_db_instances()
            result['resources']['rds_instances'] = len(db_instances.get('DBInstances', []))
            
            for db in db_instances.get('DBInstances', []):
                if not db.get('MultiAZ', False) and db.get('Engine') not in ['aurora', 'aurora-mysql', 'aurora-postgresql']:
                    result['recommendations'].append({
                        'type': 'RDS_SINGLE_AZ',
                        'resource_id': db.get('DBInstanceIdentifier'),
                        'title': f"RDS {db.get('DBInstanceIdentifier')} sem Multi-AZ",
                        'description': f"RDS {db.get('DBInstanceIdentifier')} em {region} não tem Multi-AZ habilitado",
                        'priority': 'LOW',
                        'savings': 0,
                        'service': 'RDS Analysis'
                    })
        except ClientError:
            pass
        
        try:
            lambda_client = boto3.client('lambda', region_name=region)
            functions = lambda_client.list_functions()
            result['resources']['lambda_functions'] = len(functions.get('Functions', []))
        except ClientError:
            pass
        
        try:
            s3 = boto3.client('s3')
            buckets = s3.list_buckets()
            result['resources']['s3_buckets'] = len(buckets.get('Buckets', []))
        except ClientError:
            pass
            
    except ClientError as e:
        result['status'] = 'error'
        result['error'] = str(e)
        logger.error(f"Erro ao analisar região {region}: {e}")
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        logger.error(f"Erro inesperado na região {region}: {e}")
    
    return region, result


def get_all_regions_analysis(max_workers: int = 5) -> Dict[str, Any]:
    """
    Analisa todas as regiões AWS em paralelo.
    
    Args:
        max_workers: Número máximo de workers paralelos
        
    Returns:
        Dicionário com análise consolidada de todas as regiões
    """
    enabled_regions = get_enabled_regions()
    
    results = {
        'regions': {},
        'summary': {
            'total_regions': len(enabled_regions),
            'regions_with_resources': 0,
            'total_recommendations': 0,
            'total_potential_savings': 0
        },
        'consolidated_recommendations': []
    }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_region, region): region for region in enabled_regions}
        
        for future in as_completed(futures):
            region = futures[future]
            try:
                region_name, region_data = future.result()
                results['regions'][region_name] = region_data
                
                if region_data.get('resources'):
                    has_resources = any(
                        isinstance(v, (int, float)) and v > 0 
                        for k, v in region_data['resources'].items()
                    )
                    if has_resources:
                        results['summary']['regions_with_resources'] += 1
                
                for rec in region_data.get('recommendations', []):
                    results['summary']['total_recommendations'] += 1
                    results['summary']['total_potential_savings'] += rec.get('savings', 0)
                    results['consolidated_recommendations'].append(rec)
                    
            except Exception as e:
                logger.error(f"Erro ao processar região {region}: {e}")
                results['regions'][region] = {'status': 'error', 'error': str(e)}
    
    results['consolidated_recommendations'].sort(
        key=lambda x: x.get('savings', 0), 
        reverse=True
    )
    
    return results


def get_region_costs() -> Dict[str, float]:
    """
    Obtém custos por região usando Cost Explorer.
    
    Returns:
        Dicionário com custo por região
    """
    from datetime import datetime, timedelta
    
    costs_by_region = {}
    
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'REGION'}]
        )
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                region = group.get('Keys', ['Unknown'])[0]
                cost = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', 0))
                costs_by_region[region] = costs_by_region.get(region, 0) + cost
                
    except ClientError as e:
        logger.error(f"Erro ao obter custos por região: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao obter custos: {e}")
    
    return costs_by_region
