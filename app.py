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

def get_all_services_analysis(region):
    """Analisa todos os principais serviços AWS para FinOps."""
    import boto3
    recommendations = []
    resources = {}
    
    try:
        ebs = boto3.client('ec2', region_name=region)
        volumes = ebs.describe_volumes()
        resources['ebs_volumes'] = len(volumes.get('Volumes', []))
        
        for vol in volumes.get('Volumes', []):
            vol_id = vol.get('VolumeId', '')
            state = vol.get('State', '')
            attachments = vol.get('Attachments', [])
            size = vol.get('Size', 0)
            
            if state == 'available' and not attachments:
                monthly_cost = size * 0.10
                recommendations.append({
                    'type': 'EBS_ORPHAN',
                    'resource': vol_id,
                    'description': f'Volume EBS órfão {vol_id} ({size}GB) - não está anexado',
                    'impact': 'high',
                    'savings': round(monthly_cost, 2),
                    'source': 'EBS Analysis'
                })
    except Exception:
        pass
    
    try:
        ec2 = boto3.client('ec2', region_name=region)
        eips = ec2.describe_addresses()
        resources['elastic_ips'] = len(eips.get('Addresses', []))
        
        for eip in eips.get('Addresses', []):
            allocation_id = eip.get('AllocationId', eip.get('PublicIp', ''))
            instance_id = eip.get('InstanceId')
            
            if not instance_id:
                recommendations.append({
                    'type': 'EIP_UNUSED',
                    'resource': allocation_id,
                    'description': f'Elastic IP {eip.get("PublicIp", allocation_id)} não está associado',
                    'impact': 'medium',
                    'savings': 3.60,
                    'source': 'EIP Analysis'
                })
    except Exception:
        pass
    
    try:
        ec2 = boto3.client('ec2', region_name=region)
        nat_gws = ec2.describe_nat_gateways(Filter=[{'Name': 'state', 'Values': ['available']}])
        resources['nat_gateways'] = len(nat_gws.get('NatGateways', []))
        
        for nat in nat_gws.get('NatGateways', []):
            nat_id = nat.get('NatGatewayId', '')
            recommendations.append({
                'type': 'NAT_GATEWAY_COST',
                'resource': nat_id,
                'description': f'NAT Gateway {nat_id} ativo - custo ~$32/mês + transferência',
                'impact': 'low',
                'savings': 0,
                'source': 'NAT Analysis'
            })
    except Exception:
        pass
    
    try:
        logs = boto3.client('logs', region_name=region)
        log_groups = logs.describe_log_groups()
        resources['log_groups'] = len(log_groups.get('logGroups', []))
        
        for lg in log_groups.get('logGroups', []):
            name = lg.get('logGroupName', '')
            retention = lg.get('retentionInDays')
            stored_bytes = lg.get('storedBytes', 0)
            stored_gb = stored_bytes / (1024**3)
            
            if retention is None and stored_gb > 1:
                recommendations.append({
                    'type': 'CLOUDWATCH_RETENTION',
                    'resource': name,
                    'description': f'Log group {name} sem retenção definida ({stored_gb:.1f}GB)',
                    'impact': 'medium',
                    'savings': round(stored_gb * 0.03, 2),
                    'source': 'CloudWatch Analysis'
                })
    except Exception:
        pass
    
    try:
        elb = boto3.client('elbv2', region_name=region)
        lbs = elb.describe_load_balancers()
        resources['load_balancers'] = len(lbs.get('LoadBalancers', []))
        
        for lb in lbs.get('LoadBalancers', []):
            lb_arn = lb.get('LoadBalancerArn', '')
            lb_name = lb.get('LoadBalancerName', '')
            lb_type = lb.get('Type', 'application')
            
            try:
                tgs = elb.describe_target_groups(LoadBalancerArn=lb_arn)
                has_targets = False
                for tg in tgs.get('TargetGroups', []):
                    health = elb.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
                    if health.get('TargetHealthDescriptions'):
                        has_targets = True
                        break
                
                if not has_targets:
                    cost = 16.20 if lb_type == 'application' else 22.50
                    recommendations.append({
                        'type': 'ELB_NO_TARGETS',
                        'resource': lb_name,
                        'description': f'Load Balancer {lb_name} sem targets registrados',
                        'impact': 'high',
                        'savings': cost,
                        'source': 'ELB Analysis'
                    })
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        dynamo = boto3.client('dynamodb', region_name=region)
        tables = dynamo.list_tables()
        resources['dynamodb_tables'] = len(tables.get('TableNames', []))
        
        for table_name in tables.get('TableNames', []):
            try:
                table = dynamo.describe_table(TableName=table_name)
                billing = table.get('Table', {}).get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
                
                if billing == 'PROVISIONED':
                    recommendations.append({
                        'type': 'DYNAMODB_BILLING',
                        'resource': table_name,
                        'description': f'DynamoDB {table_name} usa capacidade provisionada - considere on-demand',
                        'impact': 'low',
                        'savings': 0,
                        'source': 'DynamoDB Analysis'
                    })
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        elasticache = boto3.client('elasticache', region_name=region)
        clusters = elasticache.describe_cache_clusters()
        resources['elasticache_clusters'] = len(clusters.get('CacheClusters', []))
        
        for cluster in clusters.get('CacheClusters', []):
            cluster_id = cluster.get('CacheClusterId', '')
            node_type = cluster.get('CacheNodeType', '')
            engine = cluster.get('Engine', '')
            
            if 'large' in node_type or 'xlarge' in node_type:
                recommendations.append({
                    'type': 'ELASTICACHE_SIZE',
                    'resource': cluster_id,
                    'description': f'ElastiCache {cluster_id} ({node_type}) - verificar dimensionamento',
                    'impact': 'medium',
                    'savings': 0,
                    'source': 'ElastiCache Analysis'
                })
    except Exception:
        pass
    
    try:
        sns = boto3.client('sns', region_name=region)
        topics = sns.list_topics()
        resources['sns_topics'] = len(topics.get('Topics', []))
    except Exception:
        pass
    
    try:
        sqs = boto3.client('sqs', region_name=region)
        queues = sqs.list_queues()
        resources['sqs_queues'] = len(queues.get('QueueUrls', []))
    except Exception:
        pass
    
    try:
        apigw = boto3.client('apigateway', region_name=region)
        apis = apigw.get_rest_apis()
        resources['api_gateways'] = len(apis.get('items', []))
    except Exception:
        pass
    
    try:
        cf = boto3.client('cloudfront')
        distributions = cf.list_distributions()
        dist_list = distributions.get('DistributionList', {})
        resources['cloudfront_distributions'] = dist_list.get('Quantity', 0)
    except Exception:
        pass
    
    try:
        r53 = boto3.client('route53')
        zones = r53.list_hosted_zones()
        resources['route53_zones'] = len(zones.get('HostedZones', []))
    except Exception:
        pass
    
    try:
        sm = boto3.client('secretsmanager', region_name=region)
        secrets = sm.list_secrets()
        resources['secrets'] = len(secrets.get('SecretList', []))
    except Exception:
        pass
    
    try:
        kms = boto3.client('kms', region_name=region)
        keys = kms.list_keys()
        resources['kms_keys'] = len(keys.get('Keys', []))
    except Exception:
        pass
    
    try:
        iam = boto3.client('iam')
        users = iam.list_users()
        resources['iam_users'] = len(users.get('Users', []))
        
        for user in users.get('Users', []):
            username = user.get('UserName', '')
            try:
                keys = iam.list_access_keys(UserName=username)
                for key in keys.get('AccessKeyMetadata', []):
                    if key.get('Status') == 'Inactive':
                        recommendations.append({
                            'type': 'IAM_INACTIVE_KEY',
                            'resource': username,
                            'description': f'Access key inativa para usuário {username}',
                            'impact': 'medium',
                            'savings': 0,
                            'source': 'IAM Security'
                        })
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        ecs = boto3.client('ecs', region_name=region)
        clusters = ecs.list_clusters()
        resources['ecs_clusters'] = len(clusters.get('clusterArns', []))
    except Exception:
        pass
    
    try:
        eks = boto3.client('eks', region_name=region)
        clusters = eks.list_clusters()
        resources['eks_clusters'] = len(clusters.get('clusters', []))
    except Exception:
        pass
    
    try:
        ecr = boto3.client('ecr', region_name=region)
        repos = ecr.describe_repositories()
        resources['ecr_repositories'] = len(repos.get('repositories', []))
        
        for repo in repos.get('repositories', []):
            repo_name = repo.get('repositoryName', '')
            try:
                images = ecr.describe_images(repositoryName=repo_name)
                untagged = [img for img in images.get('imageDetails', []) if not img.get('imageTags')]
                if len(untagged) > 10:
                    recommendations.append({
                        'type': 'ECR_UNTAGGED',
                        'resource': repo_name,
                        'description': f'ECR {repo_name} tem {len(untagged)} imagens sem tag',
                        'impact': 'low',
                        'savings': 0,
                        'source': 'ECR Analysis'
                    })
            except Exception:
                pass
    except Exception:
        pass
    
    try:
        sfn = boto3.client('stepfunctions', region_name=region)
        machines = sfn.list_state_machines()
        resources['step_functions'] = len(machines.get('stateMachines', []))
    except Exception:
        pass
    
    try:
        events = boto3.client('events', region_name=region)
        rules = events.list_rules()
        resources['eventbridge_rules'] = len(rules.get('Rules', []))
    except Exception:
        pass
    
    try:
        glue = boto3.client('glue', region_name=region)
        jobs = glue.list_jobs()
        resources['glue_jobs'] = len(jobs.get('JobNames', []))
    except Exception:
        pass
    
    try:
        kinesis = boto3.client('kinesis', region_name=region)
        streams = kinesis.list_streams()
        resources['kinesis_streams'] = len(streams.get('StreamNames', []))
    except Exception:
        pass
    
    try:
        redshift = boto3.client('redshift', region_name=region)
        clusters = redshift.describe_clusters()
        resources['redshift_clusters'] = len(clusters.get('Clusters', []))
        
        for cluster in clusters.get('Clusters', []):
            cluster_id = cluster.get('ClusterIdentifier', '')
            node_type = cluster.get('NodeType', '')
            nodes = cluster.get('NumberOfNodes', 1)
            
            recommendations.append({
                'type': 'REDSHIFT_REVIEW',
                'resource': cluster_id,
                'description': f'Redshift {cluster_id} ({nodes}x {node_type}) - verificar utilização',
                'impact': 'high',
                'savings': 0,
                'source': 'Redshift Analysis'
            })
    except Exception:
        pass
    
    try:
        emr = boto3.client('emr', region_name=region)
        clusters = emr.list_clusters(ClusterStates=['RUNNING', 'WAITING'])
        resources['emr_clusters'] = len(clusters.get('Clusters', []))
        
        for cluster in clusters.get('Clusters', []):
            cluster_id = cluster.get('Id', '')
            name = cluster.get('Name', '')
            
            recommendations.append({
                'type': 'EMR_RUNNING',
                'resource': cluster_id,
                'description': f'EMR cluster {name} ativo - verificar se necessário',
                'impact': 'high',
                'savings': 0,
                'source': 'EMR Analysis'
            })
    except Exception:
        pass
    
    try:
        sm = boto3.client('sagemaker', region_name=region)
        notebooks = sm.list_notebook_instances()
        resources['sagemaker_notebooks'] = len(notebooks.get('NotebookInstances', []))
        
        for nb in notebooks.get('NotebookInstances', []):
            nb_name = nb.get('NotebookInstanceName', '')
            status = nb.get('NotebookInstanceStatus', '')
            instance_type = nb.get('InstanceType', '')
            
            if status == 'InService':
                recommendations.append({
                    'type': 'SAGEMAKER_NOTEBOOK',
                    'resource': nb_name,
                    'description': f'SageMaker notebook {nb_name} ({instance_type}) ativo',
                    'impact': 'medium',
                    'savings': 0,
                    'source': 'SageMaker Analysis'
                })
        
        endpoints = sm.list_endpoints()
        resources['sagemaker_endpoints'] = len(endpoints.get('Endpoints', []))
        
        for ep in endpoints.get('Endpoints', []):
            ep_name = ep.get('EndpointName', '')
            recommendations.append({
                'type': 'SAGEMAKER_ENDPOINT',
                'resource': ep_name,
                'description': f'SageMaker endpoint {ep_name} ativo - verificar uso',
                'impact': 'high',
                'savings': 0,
                'source': 'SageMaker Analysis'
            })
    except Exception:
        pass
    
    try:
        opensearch = boto3.client('opensearch', region_name=region)
        domains = opensearch.list_domain_names()
        resources['opensearch_domains'] = len(domains.get('DomainNames', []))
    except Exception:
        pass
    
    try:
        docdb = boto3.client('docdb', region_name=region)
        clusters = docdb.describe_db_clusters()
        resources['documentdb_clusters'] = len(clusters.get('DBClusters', []))
    except Exception:
        pass
    
    try:
        neptune = boto3.client('neptune', region_name=region)
        clusters = neptune.describe_db_clusters()
        resources['neptune_clusters'] = len(clusters.get('DBClusters', []))
    except Exception:
        pass
    
    try:
        codebuild = boto3.client('codebuild', region_name=region)
        projects = codebuild.list_projects()
        resources['codebuild_projects'] = len(projects.get('projects', []))
    except Exception:
        pass
    
    try:
        codepipeline = boto3.client('codepipeline', region_name=region)
        pipelines = codepipeline.list_pipelines()
        resources['codepipeline_pipelines'] = len(pipelines.get('pipelines', []))
    except Exception:
        pass
    
    try:
        backup = boto3.client('backup', region_name=region)
        vaults = backup.list_backup_vaults()
        resources['backup_vaults'] = len(vaults.get('BackupVaultList', []))
    except Exception:
        pass
    
    try:
        transfer = boto3.client('transfer', region_name=region)
        servers = transfer.list_servers()
        resources['transfer_servers'] = len(servers.get('Servers', []))
    except Exception:
        pass
    
    try:
        mq = boto3.client('mq', region_name=region)
        brokers = mq.list_brokers()
        resources['mq_brokers'] = len(brokers.get('BrokerSummaries', []))
    except Exception:
        pass
    
    try:
        msk = boto3.client('kafka', region_name=region)
        clusters = msk.list_clusters()
        resources['msk_clusters'] = len(clusters.get('ClusterInfoList', []))
    except Exception:
        pass
    
    try:
        appsync = boto3.client('appsync', region_name=region)
        apis = appsync.list_graphql_apis()
        resources['appsync_apis'] = len(apis.get('graphqlApis', []))
    except Exception:
        pass
    
    try:
        acm = boto3.client('acm', region_name=region)
        certs = acm.list_certificates()
        resources['acm_certificates'] = len(certs.get('CertificateSummaryList', []))
    except Exception:
        pass
    
    try:
        waf = boto3.client('wafv2', region_name=region)
        acls = waf.list_web_acls(Scope='REGIONAL')
        resources['waf_acls'] = len(acls.get('WebACLs', []))
    except Exception:
        pass
    
    try:
        athena = boto3.client('athena', region_name=region)
        workgroups = athena.list_work_groups()
        resources['athena_workgroups'] = len(workgroups.get('WorkGroups', []))
    except Exception:
        pass
    
    return recommendations, resources


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
            
            try:
                encryption = s3.get_bucket_encryption(Bucket=bucket_name)
            except Exception:
                result['recommendations'].append({
                    'type': 'S3_ENCRYPTION',
                    'resource': bucket_name,
                    'description': f'Habilitar criptografia no bucket {bucket_name}',
                    'impact': 'high',
                    'savings': 0,
                    'source': 'S3 Security'
                })
            
            try:
                public_access = s3.get_public_access_block(Bucket=bucket_name)
                config = public_access.get('PublicAccessBlockConfiguration', {})
                if not all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy'), 
                           config.get('IgnorePublicAcls'), config.get('RestrictPublicBuckets')]):
                    result['recommendations'].append({
                        'type': 'S3_PUBLIC_ACCESS',
                        'resource': bucket_name,
                        'description': f'Bloquear acesso público no bucket {bucket_name}',
                        'impact': 'high',
                        'savings': 0,
                        'source': 'S3 Security'
                    })
            except Exception:
                pass
        
        for reservation in instances.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance.get('InstanceId', '')
                instance_type = instance.get('InstanceType', '')
                state = instance.get('State', {}).get('Name', '')
                
                if state == 'stopped':
                    result['recommendations'].append({
                        'type': 'EC2_STOPPED',
                        'resource': instance_id,
                        'description': f'Instância EC2 {instance_id} está parada - considere terminar ou usar',
                        'impact': 'medium',
                        'savings': 5.0,
                        'source': 'EC2 Analysis'
                    })
                
                if state == 'running':
                    volumes = instance.get('BlockDeviceMappings', [])
                    for vol in volumes:
                        ebs = vol.get('Ebs', {})
                        if not ebs.get('DeleteOnTermination', True):
                            result['recommendations'].append({
                                'type': 'EBS_ORPHAN_RISK',
                                'resource': ebs.get('VolumeId', instance_id),
                                'description': f'Volume EBS não será deletado ao terminar {instance_id}',
                                'impact': 'low',
                                'savings': 0,
                                'source': 'EC2 Analysis'
                            })
        
        for db in db_instances.get('DBInstances', []):
            db_id = db.get('DBInstanceIdentifier', '')
            multi_az = db.get('MultiAZ', False)
            storage_encrypted = db.get('StorageEncrypted', False)
            backup_retention = db.get('BackupRetentionPeriod', 0)
            
            if not storage_encrypted:
                result['recommendations'].append({
                    'type': 'RDS_ENCRYPTION',
                    'resource': db_id,
                    'description': f'Habilitar criptografia no RDS {db_id}',
                    'impact': 'high',
                    'savings': 0,
                    'source': 'RDS Security'
                })
            
            if backup_retention < 7:
                result['recommendations'].append({
                    'type': 'RDS_BACKUP',
                    'resource': db_id,
                    'description': f'Aumentar retenção de backup do RDS {db_id} (atual: {backup_retention} dias)',
                    'impact': 'medium',
                    'savings': 0,
                    'source': 'RDS Best Practice'
                })
        
        for func in functions.get('Functions', []):
            func_name = func.get('FunctionName', '')
            memory = func.get('MemorySize', 128)
            timeout = func.get('Timeout', 3)
            
            if memory > 512:
                result['recommendations'].append({
                    'type': 'LAMBDA_MEMORY',
                    'resource': func_name,
                    'description': f'Avaliar redução de memória do Lambda {func_name} ({memory}MB)',
                    'impact': 'low',
                    'savings': 2.0,
                    'source': 'Lambda Optimization'
                })
                
    except Exception as e:
        result['resources'] = {'error': str(e)}
    
    all_services_recs, all_services_resources = get_all_services_analysis(region)
    if all_services_recs:
        result['recommendations'].extend(all_services_recs)
    if all_services_resources:
        result['resources'].update(all_services_resources)
        result['integrations']['all_services'] = True
    
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
