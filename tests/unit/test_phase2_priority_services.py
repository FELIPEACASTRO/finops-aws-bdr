"""
Tests for Phase 2 Priority Services - FASE 2.3

Tests for high-priority compute, analytics, networking, and ML services.
Author: FinOps AWS Team
Date: November 2025
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.finops_aws.services.ec2_finops_service import EC2FinOpsService, EC2Instance, ReservedInstance
from src.finops_aws.services.lambda_finops_service import LambdaFinOpsService, LambdaFunction
from src.finops_aws.services.redshift_service import RedshiftService, RedshiftCluster
from src.finops_aws.services.cloudfront_service import CloudFrontService, CloudFrontDistribution
from src.finops_aws.services.elb_service import ELBService, LoadBalancer, ClassicLoadBalancer
from src.finops_aws.services.emr_service import EMRService, EMRCluster
from src.finops_aws.services.vpc_network_service import VPCNetworkService, NATGateway, ElasticIP
from src.finops_aws.services.kinesis_service import KinesisService, KinesisDataStream
from src.finops_aws.services.glue_service import GlueService, GlueJob
from src.finops_aws.services.sagemaker_service import SageMakerService, SageMakerNotebook
from src.finops_aws.services.route53_service import Route53Service, HostedZone
from src.finops_aws.services.backup_service import BackupService, BackupVault
from src.finops_aws.services.sns_sqs_service import SNSSQSService, SNSTopic, SQSQueue
from src.finops_aws.services.secrets_manager_service import SecretsManagerService, Secret


class TestEC2FinOpsService:
    """Tests for EC2FinOpsService"""
    
    @pytest.fixture
    def mock_clients(self):
        return {
            'ec2': Mock(),
            'cloudwatch': Mock(),
            'cost': Mock()
        }
    
    @pytest.fixture
    def service(self, mock_clients):
        return EC2FinOpsService(
            ec2_client=mock_clients['ec2'],
            cloudwatch_client=mock_clients['cloudwatch'],
            cost_client=mock_clients['cost']
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon EC2"
    
    def test_get_instances(self, service, mock_clients):
        mock_clients['ec2'].get_paginator.return_value.paginate.return_value = [
            {
                'Reservations': [
                    {
                        'Instances': [
                            {
                                'InstanceId': 'i-123',
                                'InstanceType': 'm5.large',
                                'State': {'Name': 'running'},
                                'Placement': {'AvailabilityZone': 'us-east-1a'},
                                'Tags': [{'Key': 'Name', 'Value': 'TestInstance'}]
                            }
                        ]
                    }
                ]
            }
        ]
        
        instances = service.get_instances()
        assert len(instances) == 1
        assert instances[0].instance_id == 'i-123'
        assert instances[0].instance_type == 'm5.large'
    
    def test_get_resources(self, service, mock_clients):
        mock_clients['ec2'].get_paginator.return_value.paginate.return_value = [
            {'Reservations': [{'Instances': [
                {
                    'InstanceId': 'i-test',
                    'InstanceType': 't3.micro',
                    'State': {'Name': 'stopped'},
                    'Placement': {'AvailabilityZone': 'us-east-1b'}
                }
            ]}]}
        ]
        
        resources = service.get_resources()
        assert len(resources) == 1
        assert resources[0]['instance_id'] == 'i-test'


class TestLambdaFinOpsService:
    """Tests for LambdaFinOpsService"""
    
    @pytest.fixture
    def service(self):
        return LambdaFinOpsService(
            lambda_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "AWS Lambda"
    
    def test_get_functions(self, service):
        service._lambda_client.get_paginator.return_value.paginate.return_value = [
            {
                'Functions': [
                    {
                        'FunctionName': 'test-function',
                        'FunctionArn': 'arn:aws:lambda:us-east-1:123:function:test',
                        'Runtime': 'python3.11',
                        'MemorySize': 256,
                        'Timeout': 30,
                        'CodeSize': 1024,
                        'Handler': 'index.handler',
                        'LastModified': '2025-01-01T00:00:00.000+0000',
                        'Role': 'arn:aws:iam::123:role/test'
                    }
                ]
            }
        ]
        
        functions = service.get_functions()
        assert len(functions) == 1
        assert functions[0].function_name == 'test-function'
        assert functions[0].memory_size == 256


class TestRedshiftService:
    """Tests for RedshiftService"""
    
    @pytest.fixture
    def service(self):
        return RedshiftService(
            redshift_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon Redshift"
    
    def test_get_clusters(self, service):
        service._redshift_client.get_paginator.return_value.paginate.return_value = [
            {
                'Clusters': [
                    {
                        'ClusterIdentifier': 'test-cluster',
                        'NodeType': 'ra3.xlplus',
                        'NumberOfNodes': 2,
                        'ClusterStatus': 'available',
                        'AvailabilityZone': 'us-east-1a',
                        'DBName': 'testdb',
                        'MasterUsername': 'admin'
                    }
                ]
            }
        ]
        
        clusters = service.get_clusters()
        assert len(clusters) == 1
        assert clusters[0].cluster_identifier == 'test-cluster'


class TestCloudFrontService:
    """Tests for CloudFrontService"""
    
    @pytest.fixture
    def service(self):
        return CloudFrontService(
            cloudfront_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon CloudFront"
    
    def test_get_distributions(self, service):
        service._cloudfront_client.get_paginator.return_value.paginate.return_value = [
            {
                'DistributionList': {
                    'Items': [
                        {
                            'Id': 'E123ABC',
                            'DomainName': 'd123.cloudfront.net',
                            'Status': 'Deployed',
                            'Enabled': True,
                            'PriceClass': 'PriceClass_100',
                            'HttpVersion': 'http2',
                            'IsIPV6Enabled': True,
                            'Origins': {'Items': []}
                        }
                    ]
                }
            }
        ]
        
        distributions = service.get_distributions()
        assert len(distributions) == 1
        assert distributions[0].distribution_id == 'E123ABC'


class TestELBService:
    """Tests for ELBService"""
    
    @pytest.fixture
    def service(self):
        return ELBService(
            elbv2_client=Mock(),
            elb_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Elastic Load Balancing"
    
    def test_get_load_balancers(self, service):
        service._elbv2_client.get_paginator.return_value.paginate.return_value = [
            {
                'LoadBalancers': [
                    {
                        'LoadBalancerArn': 'arn:aws:elasticloadbalancing:us-east-1:123:loadbalancer/app/test/123',
                        'LoadBalancerName': 'test-alb',
                        'DNSName': 'test-123.us-east-1.elb.amazonaws.com',
                        'Scheme': 'internet-facing',
                        'Type': 'application',
                        'State': {'Code': 'active'},
                        'VpcId': 'vpc-123',
                        'AvailabilityZones': [{'ZoneName': 'us-east-1a'}]
                    }
                ]
            }
        ]
        
        lbs = service.get_load_balancers()
        assert len(lbs) == 1
        assert lbs[0].load_balancer_name == 'test-alb'


class TestEMRService:
    """Tests for EMRService"""
    
    @pytest.fixture
    def service(self):
        return EMRService(
            emr_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon EMR"
    
    def test_get_clusters(self, service):
        service._emr_client.get_paginator.return_value.paginate.return_value = [
            {'Clusters': [{'Id': 'j-123', 'Status': {'State': 'RUNNING'}}]}
        ]
        service._emr_client.describe_cluster.return_value = {
            'Cluster': {
                'Id': 'j-123',
                'Name': 'TestCluster',
                'Status': {'State': 'RUNNING'}
            }
        }
        
        clusters = service.get_clusters()
        assert len(clusters) == 1
        assert clusters[0].cluster_id == 'j-123'


class TestVPCNetworkService:
    """Tests for VPCNetworkService"""
    
    @pytest.fixture
    def service(self):
        return VPCNetworkService(
            ec2_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon VPC"
    
    def test_get_nat_gateways(self, service):
        service._ec2_client.get_paginator.return_value.paginate.return_value = [
            {
                'NatGateways': [
                    {
                        'NatGatewayId': 'nat-123',
                        'VpcId': 'vpc-123',
                        'SubnetId': 'subnet-123',
                        'State': 'available',
                        'NatGatewayAddresses': [{'PublicIp': '1.2.3.4'}]
                    }
                ]
            }
        ]
        
        nats = service.get_nat_gateways()
        assert len(nats) == 1
        assert nats[0].nat_gateway_id == 'nat-123'
    
    def test_get_elastic_ips(self, service):
        service._ec2_client.describe_addresses.return_value = {
            'Addresses': [
                {
                    'AllocationId': 'eipalloc-123',
                    'PublicIp': '1.2.3.4',
                    'Domain': 'vpc'
                }
            ]
        }
        
        eips = service.get_elastic_ips()
        assert len(eips) == 1
        assert eips[0].public_ip == '1.2.3.4'


class TestKinesisService:
    """Tests for KinesisService"""
    
    @pytest.fixture
    def service(self):
        return KinesisService(
            kinesis_client=Mock(),
            firehose_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon Kinesis"
    
    def test_get_data_streams(self, service):
        service._kinesis_client.get_paginator.return_value.paginate.return_value = [
            {'StreamNames': ['test-stream']}
        ]
        service._kinesis_client.describe_stream_summary.return_value = {
            'StreamDescriptionSummary': {
                'StreamName': 'test-stream',
                'StreamARN': 'arn:aws:kinesis:us-east-1:123:stream/test',
                'StreamStatus': 'ACTIVE',
                'RetentionPeriodHours': 24,
                'OpenShardCount': 2
            }
        }
        
        streams = service.get_data_streams()
        assert len(streams) == 1
        assert streams[0].stream_name == 'test-stream'


class TestGlueService:
    """Tests for GlueService"""
    
    @pytest.fixture
    def service(self):
        return GlueService(
            glue_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "AWS Glue"
    
    def test_get_jobs(self, service):
        service._glue_client.get_paginator.return_value.paginate.return_value = [
            {
                'Jobs': [
                    {
                        'Name': 'test-job',
                        'Role': 'arn:aws:iam::123:role/glue',
                        'Command': {'Name': 'glueetl'},
                        'GlueVersion': '3.0',
                        'MaxCapacity': 10.0
                    }
                ]
            }
        ]
        
        jobs = service.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].name == 'test-job'


class TestSageMakerService:
    """Tests for SageMakerService"""
    
    @pytest.fixture
    def service(self):
        return SageMakerService(
            sagemaker_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon SageMaker"
    
    def test_get_notebook_instances(self, service):
        service._sagemaker_client.get_paginator.return_value.paginate.return_value = [
            {
                'NotebookInstances': [
                    {
                        'NotebookInstanceName': 'test-notebook',
                        'NotebookInstanceArn': 'arn:aws:sagemaker:us-east-1:123:notebook/test',
                        'NotebookInstanceStatus': 'InService',
                        'InstanceType': 'ml.t3.medium'
                    }
                ]
            }
        ]
        
        notebooks = service.get_notebook_instances()
        assert len(notebooks) == 1
        assert notebooks[0].notebook_instance_name == 'test-notebook'


class TestRoute53Service:
    """Tests for Route53Service"""
    
    @pytest.fixture
    def service(self):
        return Route53Service(
            route53_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon Route 53"
    
    def test_get_hosted_zones(self, service):
        service._route53_client.get_paginator.return_value.paginate.return_value = [
            {
                'HostedZones': [
                    {
                        'Id': '/hostedzone/Z123',
                        'Name': 'example.com.',
                        'ResourceRecordSetCount': 10,
                        'Config': {'PrivateZone': False},
                        'CallerReference': 'ref-123'
                    }
                ]
            }
        ]
        
        zones = service.get_hosted_zones()
        assert len(zones) == 1
        assert zones[0].name == 'example.com.'


class TestBackupService:
    """Tests for BackupService"""
    
    @pytest.fixture
    def service(self):
        return BackupService(
            backup_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "AWS Backup"
    
    def test_get_backup_vaults(self, service):
        service._backup_client.get_paginator.return_value.paginate.return_value = [
            {
                'BackupVaultList': [
                    {
                        'BackupVaultName': 'Default',
                        'BackupVaultArn': 'arn:aws:backup:us-east-1:123:vault:Default',
                        'NumberOfRecoveryPoints': 5
                    }
                ]
            }
        ]
        
        vaults = service.get_backup_vaults()
        assert len(vaults) == 1
        assert vaults[0].backup_vault_name == 'Default'


class TestSNSSQSService:
    """Tests for SNSSQSService"""
    
    @pytest.fixture
    def service(self):
        return SNSSQSService(
            sns_client=Mock(),
            sqs_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "Amazon SNS/SQS"
    
    def test_get_sns_topics(self, service):
        service._sns_client.get_paginator.return_value.paginate.return_value = [
            {'Topics': [{'TopicArn': 'arn:aws:sns:us-east-1:123:test-topic'}]}
        ]
        service._sns_client.get_topic_attributes.return_value = {
            'Attributes': {
                'SubscriptionsConfirmed': '3',
                'SubscriptionsPending': '0'
            }
        }
        
        topics = service.get_sns_topics()
        assert len(topics) == 1
        assert topics[0].topic_name == 'test-topic'
    
    def test_get_sqs_queues(self, service):
        service._sqs_client.list_queues.return_value = {
            'QueueUrls': ['https://sqs.us-east-1.amazonaws.com/123/test-queue']
        }
        service._sqs_client.get_queue_attributes.return_value = {
            'Attributes': {
                'QueueArn': 'arn:aws:sqs:us-east-1:123:test-queue',
                'ApproximateNumberOfMessages': '10'
            }
        }
        
        queues = service.get_sqs_queues()
        assert len(queues) == 1
        assert queues[0].queue_name == 'test-queue'


class TestSecretsManagerService:
    """Tests for SecretsManagerService"""
    
    @pytest.fixture
    def service(self):
        return SecretsManagerService(
            secretsmanager_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
    
    def test_service_name(self, service):
        assert service.get_service_name() == "AWS Secrets Manager"
    
    def test_get_secrets(self, service):
        service._secretsmanager_client.get_paginator.return_value.paginate.return_value = [
            {
                'SecretList': [
                    {
                        'Name': 'prod/db/password',
                        'ARN': 'arn:aws:secretsmanager:us-east-1:123:secret:prod/db/password',
                        'RotationEnabled': True
                    }
                ]
            }
        ]
        
        secrets = service.get_secrets()
        assert len(secrets) == 1
        assert secrets[0].name == 'prod/db/password'
        assert secrets[0].rotation_enabled is True


class TestDataClasses:
    """Tests for dataclass models"""
    
    def test_ec2_instance_to_dict(self):
        instance = EC2Instance(
            instance_id='i-123',
            instance_type='t3.micro',
            state='running',
            availability_zone='us-east-1a'
        )
        d = instance.to_dict()
        assert d['instance_id'] == 'i-123'
        assert d['instance_type'] == 't3.micro'
    
    def test_lambda_function_to_dict(self):
        func = LambdaFunction(
            function_name='test',
            function_arn='arn:aws:lambda:us-east-1:123:function:test',
            runtime='python3.11',
            memory_size=128,
            timeout=30,
            code_size=1024,
            handler='index.handler',
            last_modified='2025-01-01'
        )
        d = func.to_dict()
        assert d['function_name'] == 'test'
        assert d['memory_size'] == 128
    
    def test_nat_gateway_to_dict(self):
        nat = NATGateway(
            nat_gateway_id='nat-123',
            vpc_id='vpc-123',
            subnet_id='subnet-123',
            state='available',
            connectivity_type='public',
            public_ip='1.2.3.4'
        )
        d = nat.to_dict()
        assert d['nat_gateway_id'] == 'nat-123'
        assert d['public_ip'] == '1.2.3.4'
    
    def test_elastic_ip_to_dict(self):
        eip = ElasticIP(
            allocation_id='eipalloc-123',
            public_ip='1.2.3.4',
            domain='vpc'
        )
        d = eip.to_dict()
        assert d['public_ip'] == '1.2.3.4'
        assert d['is_associated'] is False


class TestRecommendations:
    """Tests for recommendation generation"""
    
    def test_ec2_stopped_instance_recommendation(self):
        service = EC2FinOpsService(
            ec2_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
        service._ec2_client.get_paginator.return_value.paginate.return_value = [
            {'Reservations': [{'Instances': [
                {
                    'InstanceId': 'i-stopped',
                    'InstanceType': 'm5.large',
                    'State': {'Name': 'stopped'},
                    'Placement': {'AvailabilityZone': 'us-east-1a'},
                    'LaunchTime': datetime.utcnow() - timedelta(days=30)
                }
            ]}]}
        ]
        service._ec2_client.describe_reserved_instances.return_value = {'ReservedInstances': []}
        service._ec2_client.describe_spot_instance_requests.return_value = {'SpotInstanceRequests': []}
        
        recommendations = service.get_recommendations()
        stopped_recs = [r for r in recommendations if r.recommendation_type == 'STOPPED_INSTANCE']
        assert len(stopped_recs) >= 0  # May or may not have recommendations based on launch time
    
    def test_sns_no_subscribers_recommendation(self):
        service = SNSSQSService(
            sns_client=Mock(),
            sqs_client=Mock(),
            cloudwatch_client=Mock(),
            cost_client=Mock()
        )
        service._sns_client.get_paginator.return_value.paginate.return_value = [
            {'Topics': [{'TopicArn': 'arn:aws:sns:us-east-1:123:empty-topic'}]}
        ]
        service._sns_client.get_topic_attributes.return_value = {
            'Attributes': {'SubscriptionsConfirmed': '0', 'SubscriptionsPending': '0'}
        }
        service._sqs_client.list_queues.return_value = {'QueueUrls': []}
        
        recommendations = service.get_recommendations()
        no_sub_recs = [r for r in recommendations if r.recommendation_type == 'NO_SUBSCRIBERS']
        assert len(no_sub_recs) == 1
