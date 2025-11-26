"""
Testes Unitários - Fase 2.4 Services
Serviços Não-Serverless de Alto Custo

Cobertura:
- EKSService: Kubernetes gerenciado
- AuroraService: Database gerenciado
- OpenSearchService: Elasticsearch gerenciado  
- WorkSpacesService: Desktop virtual
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

import sys
sys.path.insert(0, 'src')


class TestEKSCluster:
    """Testes para dataclass EKSCluster"""
    
    def test_create_cluster(self):
        from finops_aws.services.eks_service import EKSCluster
        
        cluster = EKSCluster(
            name='test-cluster',
            arn='arn:aws:eks:us-east-1:123456789012:cluster/test-cluster',
            status='ACTIVE',
            version='1.28'
        )
        
        assert cluster.name == 'test-cluster'
        assert cluster.status == 'ACTIVE'
        assert cluster.version == '1.28'
        assert cluster.is_active == True
    
    def test_cluster_to_dict(self):
        from finops_aws.services.eks_service import EKSCluster
        
        cluster = EKSCluster(
            name='prod-cluster',
            arn='arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster',
            status='ACTIVE',
            version='1.29',
            tags={'Environment': 'production'}
        )
        
        d = cluster.to_dict()
        assert d['name'] == 'prod-cluster'
        assert d['status'] == 'ACTIVE'
        assert d['version'] == '1.29'
        assert d['tags']['Environment'] == 'production'
    
    def test_cluster_properties(self):
        from finops_aws.services.eks_service import EKSCluster
        
        cluster = EKSCluster(
            name='test',
            arn='arn:test',
            status='ACTIVE',
            version='1.28',
            resources_vpc_config={
                'endpointPublicAccess': True,
                'endpointPrivateAccess': False,
                'vpcId': 'vpc-123'
            },
            encryption_config=[{'provider': {'keyArn': 'arn:kms'}}]
        )
        
        assert cluster.is_public == True
        assert cluster.is_private == False
        assert cluster.vpc_id == 'vpc-123'
        assert cluster.has_encryption == True


class TestEKSNodeGroup:
    """Testes para dataclass EKSNodeGroup"""
    
    def test_create_node_group(self):
        from finops_aws.services.eks_service import EKSNodeGroup
        
        ng = EKSNodeGroup(
            nodegroup_name='workers',
            nodegroup_arn='arn:aws:eks:us-east-1:123456789012:nodegroup/test/workers/123',
            cluster_name='test-cluster',
            status='ACTIVE',
            capacity_type='SPOT',
            scaling_config={'minSize': 1, 'maxSize': 10, 'desiredSize': 3},
            instance_types=['t3.medium', 't3.large']
        )
        
        assert ng.nodegroup_name == 'workers'
        assert ng.is_spot == True
        assert ng.is_on_demand == False
        assert ng.min_size == 1
        assert ng.max_size == 10
        assert ng.desired_size == 3
        assert ng.primary_instance_type == 't3.medium'
    
    def test_node_group_to_dict(self):
        from finops_aws.services.eks_service import EKSNodeGroup
        
        ng = EKSNodeGroup(
            nodegroup_name='workers',
            nodegroup_arn='arn:test',
            cluster_name='cluster',
            status='ACTIVE'
        )
        
        d = ng.to_dict()
        assert 'nodegroup_name' in d
        assert 'is_spot' in d


class TestEKSService:
    """Testes para EKSService"""
    
    @mock_aws
    def test_service_name(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_eks_service()
        
        assert service.get_service_name() == "EKS"
    
    @mock_aws
    def test_health_check(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_eks_service()
        
        result = service.health_check()
        assert result == True
    
    @mock_aws
    def test_get_clusters_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_eks_service()
        
        clusters = service.get_clusters()
        assert clusters == []
    
    @mock_aws
    def test_get_resources(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_eks_service()
        
        resources = service.get_resources()
        assert 'clusters' in resources
        assert 'summary' in resources
        assert resources['summary']['total_clusters'] == 0


class TestAuroraCluster:
    """Testes para dataclass AuroraCluster"""
    
    def test_create_cluster(self):
        from finops_aws.services.aurora_service import AuroraCluster
        
        cluster = AuroraCluster(
            db_cluster_identifier='prod-aurora',
            db_cluster_arn='arn:aws:rds:us-east-1:123456789012:cluster:prod-aurora',
            engine='aurora-mysql',
            engine_version='8.0.mysql_aurora.3.04.0',
            engine_mode='provisioned',
            status='available'
        )
        
        assert cluster.db_cluster_identifier == 'prod-aurora'
        assert cluster.is_mysql == True
        assert cluster.is_postgresql == False
        assert cluster.is_provisioned == True
        assert cluster.is_serverless == False
    
    def test_serverless_v2_cluster(self):
        from finops_aws.services.aurora_service import AuroraCluster
        
        cluster = AuroraCluster(
            db_cluster_identifier='serverless-aurora',
            db_cluster_arn='arn:test',
            engine='aurora-postgresql',
            engine_version='15.4',
            engine_mode='provisioned',
            status='available',
            serverless_v2_scaling_configuration={
                'MinCapacity': 0.5,
                'MaxCapacity': 16
            }
        )
        
        assert cluster.is_serverless_v2 == True
        assert cluster.is_serverless == True
        assert cluster.min_capacity == 0.5
        assert cluster.max_capacity == 16
    
    def test_cluster_to_dict(self):
        from finops_aws.services.aurora_service import AuroraCluster
        
        cluster = AuroraCluster(
            db_cluster_identifier='test',
            db_cluster_arn='arn:test',
            engine='aurora-mysql',
            engine_version='8.0',
            engine_mode='provisioned',
            status='available'
        )
        
        d = cluster.to_dict()
        assert 'db_cluster_identifier' in d
        assert 'is_serverless' in d
        assert 'is_mysql' not in d  # Property, not in to_dict


class TestAuroraService:
    """Testes para AuroraService"""
    
    @mock_aws
    def test_service_name(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_aurora_service()
        
        assert service.get_service_name() == "Aurora"
    
    @mock_aws
    def test_health_check(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_aurora_service()
        
        result = service.health_check()
        assert result == True
    
    @mock_aws
    def test_get_clusters_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_aurora_service()
        
        clusters = service.get_clusters()
        assert clusters == []


class TestOpenSearchDomain:
    """Testes para dataclass OpenSearchDomain"""
    
    def test_create_domain(self):
        from finops_aws.services.opensearch_service import OpenSearchDomain
        
        domain = OpenSearchDomain(
            domain_name='logs-prod',
            domain_id='123456789012/logs-prod',
            arn='arn:aws:es:us-east-1:123456789012:domain/logs-prod',
            engine_version='OpenSearch_2.11',
            cluster_config={
                'InstanceType': 'm6g.large.search',
                'InstanceCount': 3,
                'DedicatedMasterEnabled': True,
                'DedicatedMasterType': 'm6g.large.search',
                'DedicatedMasterCount': 3,
                'ZoneAwarenessEnabled': True
            },
            ebs_options={
                'EBSEnabled': True,
                'VolumeType': 'gp3',
                'VolumeSize': 100
            }
        )
        
        assert domain.domain_name == 'logs-prod'
        assert domain.instance_type == 'm6g.large.search'
        assert domain.instance_count == 3
        assert domain.dedicated_master_enabled == True
        assert domain.volume_size_gb == 100
        assert domain.total_storage_gb == 300
    
    def test_domain_security_properties(self):
        from finops_aws.services.opensearch_service import OpenSearchDomain
        
        domain = OpenSearchDomain(
            domain_name='secure-domain',
            domain_id='123',
            arn='arn:test',
            engine_version='OpenSearch_2.11',
            encryption_at_rest_options={'Enabled': True},
            node_to_node_encryption_options={'Enabled': True},
            vpc_options={'VPCId': 'vpc-123'}
        )
        
        assert domain.has_encryption_at_rest == True
        assert domain.has_node_to_node_encryption == True
        assert domain.is_vpc == True
        assert domain.vpc_id == 'vpc-123'
    
    def test_domain_to_dict(self):
        from finops_aws.services.opensearch_service import OpenSearchDomain
        
        domain = OpenSearchDomain(
            domain_name='test',
            domain_id='123',
            arn='arn:test',
            engine_version='OpenSearch_2.11'
        )
        
        d = domain.to_dict()
        assert 'domain_name' in d
        assert 'has_encryption_at_rest' in d


class TestOpenSearchService:
    """Testes para OpenSearchService"""
    
    @mock_aws
    def test_service_name(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_opensearch_service()
        
        assert service.get_service_name() == "OpenSearch"
    
    @mock_aws
    def test_health_check(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_opensearch_service()
        
        result = service.health_check()
        assert result == True
    
    @mock_aws
    def test_get_domains_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_opensearch_service()
        
        domains = service.get_domains()
        assert domains == []


class TestWorkSpace:
    """Testes para dataclass WorkSpace"""
    
    def test_create_workspace(self):
        from finops_aws.services.workspaces_service import WorkSpace
        
        ws = WorkSpace(
            workspace_id='ws-abc123',
            directory_id='d-123456789',
            user_name='john.doe',
            state='AVAILABLE',
            bundle_id='wsb-123',
            running_mode='AUTO_STOP',
            compute_type='STANDARD',
            workspace_properties={
                'RunningMode': 'AUTO_STOP',
                'RunningModeAutoStopTimeoutInMinutes': 60,
                'RootVolumeSizeGib': 80,
                'UserVolumeSizeGib': 50,
                'ComputeTypeName': 'STANDARD'
            }
        )
        
        assert ws.workspace_id == 'ws-abc123'
        assert ws.user_name == 'john.doe'
        assert ws.is_running == True
        assert ws.is_auto_stop == True
        assert ws.is_always_on == False
        assert ws.root_volume_size_gb == 80
        assert ws.user_volume_size_gb == 50
        assert ws.total_storage_gb == 130
    
    def test_workspace_always_on(self):
        from finops_aws.services.workspaces_service import WorkSpace
        
        ws = WorkSpace(
            workspace_id='ws-123',
            directory_id='d-123',
            user_name='test',
            state='AVAILABLE',
            bundle_id='wsb-123',
            running_mode='ALWAYS_ON'
        )
        
        assert ws.is_always_on == True
        assert ws.is_auto_stop == False
    
    def test_workspace_to_dict(self):
        from finops_aws.services.workspaces_service import WorkSpace
        
        ws = WorkSpace(
            workspace_id='ws-123',
            directory_id='d-123',
            user_name='test',
            state='STOPPED',
            bundle_id='wsb-123'
        )
        
        d = ws.to_dict()
        assert 'workspace_id' in d
        assert 'is_running' in d
        assert 'is_auto_stop' in d


class TestWorkSpacesService:
    """Testes para WorkSpacesService"""
    
    @mock_aws
    def test_service_name(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_workspaces_service()
        
        assert service.get_service_name() == "WorkSpaces"
    
    @mock_aws
    def test_health_check(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_workspaces_service()
        
        result = service.health_check()
        assert result == True
    
    @mock_aws
    def test_get_workspaces_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_workspaces_service()
        
        workspaces = service.get_workspaces()
        assert workspaces == []
    
    @mock_aws
    def test_get_resources(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_workspaces_service()
        
        resources = service.get_resources()
        assert 'workspaces' in resources
        assert 'directories' in resources
        assert 'summary' in resources


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory"""
    
    @mock_aws
    def test_get_all_services_includes_new_services(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        services = factory.get_all_services()
        
        assert 'eks' in services
        assert 'aurora' in services
        assert 'opensearch' in services
        assert 'workspaces' in services
    
    @mock_aws
    def test_services_are_cached(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        
        eks1 = factory.get_eks_service()
        eks2 = factory.get_eks_service()
        
        assert eks1 is eks2


class TestRecommendations:
    """Testes para recomendações dos novos serviços"""
    
    @mock_aws
    def test_eks_recommendations_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_eks_service()
        
        recommendations = service.get_recommendations()
        assert recommendations == []
    
    @mock_aws
    def test_aurora_recommendations_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_aurora_service()
        
        recommendations = service.get_recommendations()
        assert recommendations == []
    
    @mock_aws
    def test_opensearch_recommendations_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_opensearch_service()
        
        recommendations = service.get_recommendations()
        assert recommendations == []
    
    @mock_aws
    def test_workspaces_recommendations_empty(self):
        from finops_aws.core.factories import AWSClientFactory, ServiceFactory
        AWSClientFactory.reset_instance()
        ServiceFactory.reset_instance()
        
        factory = ServiceFactory()
        service = factory.get_workspaces_service()
        
        recommendations = service.get_recommendations()
        assert recommendations == []
