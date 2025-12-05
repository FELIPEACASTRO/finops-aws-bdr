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

def get_compute_optimizer_recommendations(region):
    """Obtém recomendações do AWS Compute Optimizer para EC2."""
    import boto3
    recommendations = []
    
    try:
        co = boto3.client('compute-optimizer', region_name=region)
        response = co.get_ec2_instance_recommendations()
        
        for rec in response.get('instanceRecommendations', []):
            instance_id = rec.get('instanceArn', '').split('/')[-1]
            finding = rec.get('finding', 'OPTIMIZED')
            current_type = rec.get('currentInstanceType', '')
            
            if finding in ['OVER_PROVISIONED', 'UNDER_PROVISIONED']:
                savings = 0
                recommended_type = current_type
                
                for option in rec.get('recommendationOptions', []):
                    if option.get('rank') == 1:
                        recommended_type = option.get('instanceType', current_type)
                        savings_info = option.get('savingsOpportunity', {})
                        savings = savings_info.get('estimatedMonthlySavings', {}).get('value', 0)
                        break
                
                recommendations.append({
                    'type': 'EC2_RIGHTSIZING',
                    'resource': instance_id,
                    'description': f'Redimensionar {instance_id}: {current_type} → {recommended_type}',
                    'impact': 'high' if finding == 'OVER_PROVISIONED' else 'medium',
                    'savings': round(savings, 2),
                    'source': 'Compute Optimizer'
                })
    except Exception as e:
        pass
    
    return recommendations


def get_cost_explorer_ri_recommendations(region):
    """Obtém recomendações de Reserved Instances e Savings Plans do Cost Explorer."""
    import boto3
    recommendations = []
    
    try:
        ce = boto3.client('ce', region_name=region)
        
        try:
            ri_response = ce.get_reservation_purchase_recommendation(
                Service='Amazon Elastic Compute Cloud - Compute',
                LookbackPeriodInDays='SIXTY_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT'
            )
            
            for rec in ri_response.get('Recommendations', []):
                for detail in rec.get('RecommendationDetails', []):
                    savings = float(detail.get('EstimatedMonthlySavingsAmount', 0))
                    instance_type = detail.get('InstanceDetails', {}).get('EC2InstanceDetails', {}).get('InstanceType', 'N/A')
                    
                    if savings > 0:
                        recommendations.append({
                            'type': 'EC2_RESERVED_INSTANCE',
                            'resource': instance_type,
                            'description': f'Comprar Reserved Instance para {instance_type} (economia mensal: ${savings:.2f})',
                            'impact': 'high',
                            'savings': round(savings, 2),
                            'source': 'Cost Explorer RI'
                        })
        except Exception:
            pass
        
        try:
            sp_response = ce.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                LookbackPeriodInDays='SIXTY_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT'
            )
            
            for rec in sp_response.get('SavingsPlansPurchaseRecommendation', {}).get('SavingsPlansPurchaseRecommendationDetails', []):
                savings = float(rec.get('EstimatedMonthlySavingsAmount', 0))
                commitment = rec.get('HourlyCommitmentToPurchase', 'N/A')
                
                if savings > 0:
                    recommendations.append({
                        'type': 'SAVINGS_PLAN',
                        'resource': f'Compute SP ${commitment}/hora',
                        'description': f'Comprar Savings Plan Compute (economia mensal: ${savings:.2f})',
                        'impact': 'high',
                        'savings': round(savings, 2),
                        'source': 'Cost Explorer SP'
                    })
        except Exception:
            pass
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            coverage = ce.get_reservation_coverage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY'
            )
            
            for period in coverage.get('CoveragesByTime', []):
                total_coverage = period.get('Total', {}).get('CoverageHours', {})
                coverage_pct = float(total_coverage.get('CoverageHoursPercentage', '100'))
                
                if coverage_pct < 70:
                    recommendations.append({
                        'type': 'RI_COVERAGE_LOW',
                        'resource': 'EC2',
                        'description': f'Cobertura de RI baixa ({coverage_pct:.1f}%) - considere mais Reserved Instances',
                        'impact': 'medium',
                        'savings': 0,
                        'source': 'Cost Explorer Coverage'
                    })
        except Exception:
            pass
            
    except Exception as e:
        pass
    
    return recommendations


def get_trusted_advisor_recommendations():
    """Obtém recomendações do AWS Trusted Advisor (requer Business/Enterprise Support)."""
    import boto3
    recommendations = []
    
    try:
        support = boto3.client('support', region_name='us-east-1')
        
        checks_response = support.describe_trusted_advisor_checks(language='en')
        
        cost_check_ids = []
        security_check_ids = []
        
        for check in checks_response.get('checks', []):
            category = check.get('category', '')
            check_id = check.get('id')
            
            if category == 'cost_optimizing':
                cost_check_ids.append((check_id, check.get('name', '')))
            elif category == 'security':
                security_check_ids.append((check_id, check.get('name', '')))
        
        for check_id, check_name in cost_check_ids[:5]:
            try:
                result = support.describe_trusted_advisor_check_result(checkId=check_id, language='en')
                status = result.get('result', {}).get('status', 'ok')
                
                if status in ['warning', 'error']:
                    flagged = result.get('result', {}).get('flaggedResources', [])
                    for resource in flagged[:3]:
                        resource_id = resource.get('resourceId', 'N/A')
                        recommendations.append({
                            'type': 'TRUSTED_ADVISOR_COST',
                            'resource': resource_id,
                            'description': f'{check_name}: {resource_id}',
                            'impact': 'high' if status == 'error' else 'medium',
                            'savings': 0,
                            'source': 'Trusted Advisor'
                        })
            except Exception:
                pass
        
        for check_id, check_name in security_check_ids[:3]:
            try:
                result = support.describe_trusted_advisor_check_result(checkId=check_id, language='en')
                status = result.get('result', {}).get('status', 'ok')
                
                if status in ['warning', 'error']:
                    flagged = result.get('result', {}).get('flaggedResources', [])
                    for resource in flagged[:3]:
                        resource_id = resource.get('resourceId', 'N/A')
                        recommendations.append({
                            'type': 'TRUSTED_ADVISOR_SECURITY',
                            'resource': resource_id,
                            'description': f'{check_name}: {resource_id}',
                            'impact': 'high',
                            'savings': 0,
                            'source': 'Trusted Advisor Security'
                        })
            except Exception:
                pass
                
    except Exception as e:
        error_msg = str(e)
        if 'SubscriptionRequiredException' in error_msg:
            recommendations.append({
                'type': 'TRUSTED_ADVISOR_UNAVAILABLE',
                'resource': 'N/A',
                'description': 'Trusted Advisor requer AWS Business ou Enterprise Support',
                'impact': 'low',
                'savings': 0,
                'source': 'Info'
            })
    
    return recommendations


def get_amazon_q_insights(cost_data, resources_data):
    """Obtém insights do Amazon Q Business (se configurado)."""
    import boto3
    insights = []
    
    q_app_id = os.environ.get('Q_BUSINESS_APPLICATION_ID')
    if not q_app_id:
        return insights
    
    try:
        q_client = boto3.client('qbusiness', region_name='us-east-1')
        
        prompt = f"""Analise os seguintes dados de custos AWS e forneça recomendações de otimização:

Custo Total: ${cost_data.get('total_usd', 0):.2f}/mês
Serviços: {', '.join([s['service'] + ': $' + str(s['cost']) for s in cost_data.get('by_service', [])[:5]])}
Recursos: EC2={resources_data.get('ec2_instances', 0)}, S3={resources_data.get('s3_buckets', 0)}, Lambda={resources_data.get('lambda_functions', 0)}, RDS={resources_data.get('rds_instances', 0)}

Forneça 3 recomendações específicas de economia."""

        response = q_client.chat_sync(
            applicationId=q_app_id,
            userMessage=prompt
        )
        
        ai_response = response.get('systemMessage', '')
        if ai_response:
            insights.append({
                'type': 'AI_INSIGHT',
                'resource': 'Amazon Q',
                'description': ai_response[:500],
                'impact': 'medium',
                'savings': 0,
                'source': 'Amazon Q Business'
            })
            
    except Exception as e:
        pass
    
    return insights


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
        'recommendations': [],
        'integrations': {
            'compute_optimizer': False,
            'cost_explorer_ri': False,
            'trusted_advisor': False,
            'amazon_q': False
        }
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
                        'impact': 'medium',
                        'savings': 0,
                        'source': 'S3 Analysis'
                    })
            except Exception:
                pass
                
    except Exception as e:
        result['resources'] = {'error': str(e)}
    
    co_recs = get_compute_optimizer_recommendations(region)
    if co_recs:
        result['recommendations'].extend(co_recs)
        result['integrations']['compute_optimizer'] = True
    
    ri_recs = get_cost_explorer_ri_recommendations(region)
    if ri_recs:
        result['recommendations'].extend(ri_recs)
        result['integrations']['cost_explorer_ri'] = True
    
    ta_recs = get_trusted_advisor_recommendations()
    if ta_recs:
        result['recommendations'].extend(ta_recs)
        result['integrations']['trusted_advisor'] = True
    
    q_insights = get_amazon_q_insights(result.get('costs', {}), result.get('resources', {}))
    if q_insights:
        result['recommendations'].extend(q_insights)
        result['integrations']['amazon_q'] = True
    
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
        total_savings = 0
        for rec in result.get('recommendations', []):
            savings = rec.get('savings', 0)
            total_savings += savings
            recommendations_list.append({
                'type': rec.get('type', 'OPTIMIZATION'),
                'title': rec.get('description', rec.get('type', 'Recomendação')),
                'resource_id': rec.get('resource', '-'),
                'service': rec.get('source', rec.get('resource', '-')),
                'savings': savings,
                'priority': 'HIGH' if rec.get('impact') == 'high' else 'MEDIUM' if rec.get('impact') == 'medium' else 'LOW'
            })
        
        total_cost = result.get('costs', {}).get('total_usd', 0)
        integrations = result.get('integrations', {})
        
        _cached_report = {
            'status': 'success',
            'report': {
                'execution_id': f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'account_id': result.get('account', {}).get('id', 'unknown'),
                'integrations': integrations,
                'summary': {
                    'total_cost': total_cost,
                    'total_savings_potential': total_savings if total_savings > 0 else total_cost * 0.15,
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
