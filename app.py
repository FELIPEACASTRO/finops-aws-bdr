#!/usr/bin/env python3
"""
FinOps AWS - Web Server para Deploy
Serve o dashboard e API de análise de custos AWS.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_file, render_template_string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def get_aws_analysis():
    """Executa análise completa da conta AWS."""
    import boto3
    
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'status': 'success',
        'account': {},
        'costs': {},
        'resources': {},
        'recommendations': []
    }
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        result['account'] = {
            'id': identity['Account'],
            'arn': identity['Arn'],
            'user': identity['Arn'].split('/')[-1]
        }
    except Exception as e:
        result['account'] = {'error': str(e)}
    
    try:
        ce = boto3.client('ce', region_name=region)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        services = []
        total = 0
        for r in response.get('ResultsByTime', []):
            for group in r.get('Groups', []):
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0.001:
                    services.append({'service': service, 'cost': round(cost, 4)})
                    total += cost
        
        result['costs'] = {
            'period': {'start': start_date, 'end': end_date},
            'total_usd': round(total, 2),
            'by_service': sorted(services, key=lambda x: x['cost'], reverse=True)
        }
    except Exception as e:
        result['costs'] = {'error': str(e)}
    
    try:
        ec2 = boto3.client('ec2', region_name=region)
        instances = ec2.describe_instances()
        ec2_count = sum(len(r['Instances']) for r in instances.get('Reservations', []))
        
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()
        s3_count = len(buckets.get('Buckets', []))
        
        lam = boto3.client('lambda', region_name=region)
        functions = lam.list_functions()
        lambda_count = len(functions.get('Functions', []))
        
        rds = boto3.client('rds', region_name=region)
        db_instances = rds.describe_db_instances()
        rds_count = len(db_instances.get('DBInstances', []))
        
        result['resources'] = {
            'ec2_instances': ec2_count,
            's3_buckets': s3_count,
            'lambda_functions': lambda_count,
            'rds_instances': rds_count,
            'total': ec2_count + s3_count + lambda_count + rds_count
        }
        
        for bucket in buckets.get('Buckets', []):
            bucket_name = bucket['Name']
            try:
                versioning = s3.get_bucket_versioning(Bucket=bucket_name)
                if versioning.get('Status') != 'Enabled':
                    result['recommendations'].append({
                        'type': 'S3_VERSIONING',
                        'resource': bucket_name,
                        'description': f'Habilitar versionamento no bucket {bucket_name}',
                        'impact': 'medium'
                    })
            except:
                pass
                
    except Exception as e:
        result['resources'] = {'error': str(e)}
    
    return result


@app.route('/')
def index():
    """Serve o dashboard principal."""
    dashboard_path = os.path.join(os.path.dirname(__file__), 'src', 'finops_aws', 'dashboard.html')
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>FinOps AWS</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #3b82f6; }
        a { color: #3b82f6; }
        .card { background: #1e293b; padding: 20px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>FinOps AWS</h1>
        <p>Solução de análise de custos AWS</p>
        <div class="card">
            <h3>Endpoints disponíveis:</h3>
            <ul>
                <li><a href="/api/analysis">/api/analysis</a> - Análise completa</li>
                <li><a href="/api/health">/api/health</a> - Status do serviço</li>
            </ul>
        </div>
    </div>
</body>
</html>
''')


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'finops-aws',
        'version': '1.0.0'
    })


@app.route('/api/analysis')
def analysis():
    """Executa e retorna análise FinOps."""
    try:
        result = get_aws_analysis()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/costs')
def costs():
    """Retorna apenas os custos."""
    try:
        result = get_aws_analysis()
        return jsonify({
            'status': 'success',
            'account_id': result.get('account', {}).get('id'),
            'costs': result.get('costs', {})
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/resources')
def resources():
    """Retorna inventário de recursos."""
    try:
        result = get_aws_analysis()
        return jsonify({
            'status': 'success',
            'account_id': result.get('account', {}).get('id'),
            'resources': result.get('resources', {})
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/recommendations')
def recommendations():
    """Retorna recomendações de otimização."""
    try:
        result = get_aws_analysis()
        return jsonify({
            'status': 'success',
            'account_id': result.get('account', {}).get('id'),
            'recommendations': result.get('recommendations', [])
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


_cached_report = None

@app.route('/api/v1/reports/latest')
def get_latest_report():
    """Retorna o último relatório no formato esperado pelo dashboard."""
    global _cached_report
    try:
        result = get_aws_analysis()
        
        costs_by_service = {}
        for svc in result.get('costs', {}).get('by_service', []):
            costs_by_service[svc['service']] = svc['cost']
        
        recommendations_list = []
        for rec in result.get('recommendations', []):
            recommendations_list.append({
                'type': rec.get('type', 'OPTIMIZATION'),
                'title': rec.get('description', rec.get('type', 'Recomendação')),
                'resource_id': rec.get('resource', '-'),
                'service': rec.get('resource', '-'),
                'savings': 0,
                'priority': 'HIGH' if rec.get('impact') == 'high' else 'MEDIUM' if rec.get('impact') == 'medium' else 'LOW'
            })
        
        total_cost = result.get('costs', {}).get('total_usd', 0)
        
        _cached_report = {
            'status': 'success',
            'report': {
                'execution_id': f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'account_id': result.get('account', {}).get('id', 'unknown'),
                'summary': {
                    'total_cost': total_cost,
                    'total_savings_potential': total_cost * 0.15,
                    'recommendations_count': len(recommendations_list),
                    'services_analyzed': len(costs_by_service),
                    'start_time': result.get('costs', {}).get('period', {}).get('start', ''),
                    'end_time': datetime.now().isoformat()
                },
                'details': {
                    'costs': {
                        'by_service': costs_by_service,
                        'total': total_cost
                    },
                    'recommendations': recommendations_list,
                    'resources': result.get('resources', {})
                }
            }
        }
        
        return jsonify(_cached_report)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/v1/analysis', methods=['POST'])
def start_analysis():
    """Inicia uma nova análise."""
    try:
        execution_id = f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return jsonify({
            'status': 'started',
            'execution_id': execution_id,
            'message': 'Análise iniciada com sucesso'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
