"""
API Gateway Handler para FinOps AWS
REST API para invocar análises e consultar relatórios
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Lazy loading - clients criados sob demanda
_s3_client = None
_stepfunctions_client = None

def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return _s3_client

def get_stepfunctions_client():
    global _stepfunctions_client
    if _stepfunctions_client is None:
        _stepfunctions_client = boto3.client('stepfunctions', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return _stepfunctions_client

sfn_arn = os.environ.get('STEPFUNCTIONS_ARN', '')
reports_bucket = os.environ.get('REPORTS_BUCKET_NAME', 'finops-aws-reports')


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Formata resposta HTTP padrão"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler para API Gateway"""
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        logger.info(f"API request: {http_method} {path}")
        
        # Roteamento
        if path == '/v1/analysis' and http_method == 'POST':
            return handle_start_analysis(event)
        
        elif path == '/v1/analysis/status' and http_method == 'GET':
            return handle_get_status(event)
        
        elif path == '/v1/reports/latest' and http_method == 'GET':
            return handle_get_latest_report(event)
        
        elif path == '/v1/reports' and http_method == 'GET':
            return handle_list_reports(event)
        
        elif path == '/v1/health' and http_method == 'GET':
            return response(200, {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
        
        else:
            return response(404, {'error': 'Endpoint not found'})
    
    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)
        return response(500, {'error': str(e)})


def handle_start_analysis(event: Dict[str, Any]) -> Dict[str, Any]:
    """Inicia nova análise via Step Functions"""
    try:
        body = json.loads(event.get('body', '{}'))
        analysis_type = body.get('analysis_type', 'full')
        regions = body.get('regions', ['us-east-1'])
        
        if not sfn_arn:
            return response(400, {'error': 'Step Functions not configured'})
        
        # Inicia execução
        exec_response = get_stepfunctions_client().start_execution(
            stateMachineArn=sfn_arn,
            input=json.dumps({
                'source': 'api',
                'analysis_type': analysis_type,
                'regions': regions,
                'initiated_at': datetime.utcnow().isoformat()
            })
        )
        
        return response(202, {
            'status': 'accepted',
            'execution_arn': exec_response['executionArn'],
            'execution_id': exec_response['executionArn'].split(':')[-1],
            'message': 'Analysis started'
        })
    
    except ClientError as e:
        return response(500, {'error': f"Failed to start execution: {str(e)}"})


def handle_get_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Obtém status de uma execução"""
    try:
        query_params = event.get('queryStringParameters', {})
        execution_id = query_params.get('execution_id') if query_params else None
        
        if not execution_id:
            return response(400, {'error': 'execution_id required'})
        
        try:
            exec_arn = f"arn:aws:states:*:*:execution:*:{execution_id}"
            # Try to get from S3 state
            key = f"state/executions/{execution_id}/state.json"
            s3_response = get_s3_client().get_object(Bucket=reports_bucket, Key=key)
            state = json.loads(s3_response['Body'].read())
            
            return response(200, {
                'execution_id': execution_id,
                'status': state.get('status', 'UNKNOWN'),
                'state': state
            })
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NoSuchKey':
                return response(404, {'error': 'Execution not found'})
            return response(500, {'error': str(e)})
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_get_latest_report(event: Dict[str, Any]) -> Dict[str, Any]:
    """Obtém relatório mais recente"""
    try:
        key = 'reports/latest/report.json'
        s3_response = get_s3_client().get_object(Bucket=reports_bucket, Key=key)
        report = json.loads(s3_response['Body'].read())
        
        return response(200, {
            'status': 'success',
            'report': report
        })
    
    except ClientError as e:
        if e.response.get('Error', {}).get('Code') == 'NoSuchKey':
            return response(404, {'error': 'No reports available yet'})
        return response(500, {'error': str(e)})
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_list_reports(event: Dict[str, Any]) -> Dict[str, Any]:
    """Lista relatórios disponíveis"""
    try:
        query_params = event.get('queryStringParameters', {})
        prefix = query_params.get('prefix', 'reports/') if query_params else 'reports/'
        
        list_response = get_s3_client().list_objects_v2(
            Bucket=reports_bucket,
            Prefix=prefix,
            MaxKeys=100
        )
        
        reports = []
        for obj in list_response.get('Contents', []):
            if obj['Key'].endswith('report.json'):
                reports.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
        
        return response(200, {
            'status': 'success',
            'report_count': len(reports),
            'reports': sorted(reports, key=lambda x: x['last_modified'], reverse=True)
        })
    
    except Exception as e:
        return response(500, {'error': str(e)})
