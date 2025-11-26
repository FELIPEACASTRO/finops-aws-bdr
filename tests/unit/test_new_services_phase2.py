"""
Testes unitários para novos serviços AWS (FASE 2 - Parte 2)

Testa EFSService, ElastiCacheService e ECSContainerService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.finops_aws.services.efs_service import EFSService, EFSFileSystem
from src.finops_aws.services.elasticache_service import (
    ElastiCacheService, 
    ElastiCacheCluster, 
    ElastiCacheReplicationGroup
)
from src.finops_aws.services.ecs_service import (
    ECSContainerService, 
    ECSCluster, 
    ECSService as ECSServiceModel,
    ECSTask
)


class TestEFSFileSystem:
    """Testes para EFSFileSystem dataclass"""
    
    def test_create_file_system(self):
        """Testa criação de EFSFileSystem"""
        fs = EFSFileSystem(
            file_system_id="fs-12345678",
            name="my-efs",
            lifecycle_state="available"
        )
        
        assert fs.file_system_id == "fs-12345678"
        assert fs.name == "my-efs"
        assert fs.lifecycle_state == "available"
        assert fs.performance_mode == "generalPurpose"


class TestEFSService:
    """Testes para EFSService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_efs = Mock()
        self.mock_cloudwatch = Mock()
        self.mock_cost = Mock()
        
        self.service = EFSService(
            efs_client=self.mock_efs,
            cloudwatch_client=self.mock_cloudwatch,
            cost_client=self.mock_cost
        )
    
    def test_service_name(self):
        """Testa nome do serviço"""
        assert self.service.get_service_name() == "Amazon EFS"
    
    def test_health_check_success(self):
        """Testa health check com sucesso"""
        self.mock_efs.describe_file_systems.return_value = {'FileSystems': []}
        
        result = self.service.health_check()
        
        assert result is True
    
    def test_health_check_failure(self):
        """Testa health check com falha"""
        self.mock_efs.describe_file_systems.side_effect = Exception("Access denied")
        
        result = self.service.health_check()
        
        assert result is False
    
    def test_get_file_systems(self):
        """Testa obtenção de file systems"""
        self.mock_efs.describe_file_systems.return_value = {
            'FileSystems': [
                {
                    'FileSystemId': 'fs-123',
                    'Name': 'test-efs',
                    'LifeCycleState': 'available',
                    'SizeInBytes': {'Value': 1024000},
                    'PerformanceMode': 'generalPurpose',
                    'ThroughputMode': 'bursting',
                    'Encrypted': True,
                    'NumberOfMountTargets': 2
                }
            ]
        }
        self.mock_efs.describe_lifecycle_configuration.return_value = {
            'LifecyclePolicies': [{'TransitionToIA': 'AFTER_30_DAYS'}]
        }
        
        file_systems = self.service.get_file_systems()
        
        assert len(file_systems) == 1
        assert file_systems[0].file_system_id == 'fs-123'
        assert file_systems[0].encrypted is True
    
    def test_get_metrics(self):
        """Testa obtenção de métricas agregadas"""
        self.mock_efs.describe_file_systems.return_value = {
            'FileSystems': [
                {
                    'FileSystemId': 'fs-123',
                    'LifeCycleState': 'available',
                    'SizeInBytes': {'Value': 1024000},
                    'PerformanceMode': 'generalPurpose',
                    'ThroughputMode': 'elastic',
                    'Encrypted': True,
                    'NumberOfMountTargets': 2
                }
            ]
        }
        self.mock_efs.describe_lifecycle_configuration.side_effect = Exception()
        
        metrics = self.service.get_metrics()
        
        assert metrics.service_name == "Amazon EFS"
        assert metrics.resource_count == 1
    
    def test_get_recommendations_no_lifecycle(self):
        """Testa recomendação para FS sem lifecycle"""
        self.mock_efs.describe_file_systems.return_value = {
            'FileSystems': [
                {
                    'FileSystemId': 'fs-no-lifecycle',
                    'LifeCycleState': 'available',
                    'SizeInBytes': {'Value': 10240000000},
                    'PerformanceMode': 'generalPurpose',
                    'ThroughputMode': 'bursting',
                    'Encrypted': True,
                    'NumberOfMountTargets': 2
                }
            ]
        }
        self.mock_efs.describe_lifecycle_configuration.side_effect = Exception()
        self.mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
        
        recommendations = self.service.get_recommendations()
        
        lifecycle_recs = [r for r in recommendations if r.recommendation_type == 'ENABLE_LIFECYCLE']
        assert len(lifecycle_recs) >= 1


class TestElastiCacheCluster:
    """Testes para ElastiCacheCluster dataclass"""
    
    def test_create_cluster(self):
        """Testa criação de ElastiCacheCluster"""
        cluster = ElastiCacheCluster(
            cluster_id="my-cache",
            engine="redis",
            engine_version="6.2",
            cache_node_type="cache.t3.micro",
            num_cache_nodes=1,
            status="available"
        )
        
        assert cluster.cluster_id == "my-cache"
        assert cluster.engine == "redis"
        assert cluster.status == "available"


class TestElastiCacheService:
    """Testes para ElastiCacheService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_elasticache = Mock()
        self.mock_cloudwatch = Mock()
        self.mock_cost = Mock()
        
        self.service = ElastiCacheService(
            elasticache_client=self.mock_elasticache,
            cloudwatch_client=self.mock_cloudwatch,
            cost_client=self.mock_cost
        )
    
    def test_service_name(self):
        """Testa nome do serviço"""
        assert self.service.get_service_name() == "Amazon ElastiCache"
    
    def test_health_check_success(self):
        """Testa health check com sucesso"""
        self.mock_elasticache.describe_cache_clusters.return_value = {'CacheClusters': []}
        
        result = self.service.health_check()
        
        assert result is True
    
    def test_health_check_failure(self):
        """Testa health check com falha"""
        self.mock_elasticache.describe_cache_clusters.side_effect = Exception("Access denied")
        
        result = self.service.health_check()
        
        assert result is False
    
    def test_get_clusters(self):
        """Testa obtenção de clusters"""
        self.mock_elasticache.describe_cache_clusters.return_value = {
            'CacheClusters': [
                {
                    'CacheClusterId': 'cache-1',
                    'Engine': 'redis',
                    'EngineVersion': '6.2',
                    'CacheNodeType': 'cache.t3.micro',
                    'NumCacheNodes': 1,
                    'CacheClusterStatus': 'available',
                    'AtRestEncryptionEnabled': True,
                    'TransitEncryptionEnabled': True
                }
            ]
        }
        
        clusters = self.service.get_clusters()
        
        assert len(clusters) == 1
        assert clusters[0].cluster_id == 'cache-1'
        assert clusters[0].engine == 'redis'
    
    def test_get_replication_groups(self):
        """Testa obtenção de replication groups"""
        self.mock_elasticache.describe_replication_groups.return_value = {
            'ReplicationGroups': [
                {
                    'ReplicationGroupId': 'rg-1',
                    'Description': 'Test RG',
                    'Status': 'available',
                    'NodeGroups': [
                        {'NodeGroupMembers': [{'CacheNodeId': 'node-1'}]}
                    ],
                    'AutomaticFailover': 'enabled',
                    'MultiAZ': 'enabled'
                }
            ]
        }
        
        groups = self.service.get_replication_groups()
        
        assert len(groups) == 1
        assert groups[0].replication_group_id == 'rg-1'
    
    def test_get_metrics(self):
        """Testa obtenção de métricas agregadas"""
        self.mock_elasticache.describe_cache_clusters.return_value = {
            'CacheClusters': [
                {
                    'CacheClusterId': 'cache-1',
                    'Engine': 'redis',
                    'EngineVersion': '6.2',
                    'CacheNodeType': 'cache.t3.micro',
                    'NumCacheNodes': 1,
                    'CacheClusterStatus': 'available'
                }
            ]
        }
        self.mock_elasticache.describe_replication_groups.return_value = {
            'ReplicationGroups': []
        }
        
        metrics = self.service.get_metrics()
        
        assert metrics.service_name == "Amazon ElastiCache"
        assert metrics.resource_count >= 1
    
    def test_get_recommendations_no_encryption(self):
        """Testa recomendação para cluster sem criptografia"""
        self.mock_elasticache.describe_cache_clusters.return_value = {
            'CacheClusters': [
                {
                    'CacheClusterId': 'no-encrypt',
                    'Engine': 'redis',
                    'EngineVersion': '6.2',
                    'CacheNodeType': 'cache.t3.micro',
                    'NumCacheNodes': 1,
                    'CacheClusterStatus': 'available',
                    'AtRestEncryptionEnabled': False
                }
            ]
        }
        self.mock_elasticache.describe_replication_groups.return_value = {
            'ReplicationGroups': []
        }
        self.mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
        
        recommendations = self.service.get_recommendations()
        
        security_recs = [r for r in recommendations if r.recommendation_type == 'SECURITY']
        assert len(security_recs) >= 1


class TestECSCluster:
    """Testes para ECSCluster dataclass"""
    
    def test_create_cluster(self):
        """Testa criação de ECSCluster"""
        cluster = ECSCluster(
            cluster_arn="arn:aws:ecs:us-east-1:123456789:cluster/my-cluster",
            cluster_name="my-cluster",
            status="ACTIVE"
        )
        
        assert cluster.cluster_name == "my-cluster"
        assert cluster.status == "ACTIVE"


class TestECSContainerService:
    """Testes para ECSContainerService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_ecs = Mock()
        self.mock_cloudwatch = Mock()
        self.mock_cost = Mock()
        
        self.service = ECSContainerService(
            ecs_client=self.mock_ecs,
            cloudwatch_client=self.mock_cloudwatch,
            cost_client=self.mock_cost
        )
    
    def test_service_name(self):
        """Testa nome do serviço"""
        assert self.service.get_service_name() == "Amazon ECS"
    
    def test_health_check_success(self):
        """Testa health check com sucesso"""
        self.mock_ecs.list_clusters.return_value = {'clusterArns': []}
        
        result = self.service.health_check()
        
        assert result is True
    
    def test_health_check_failure(self):
        """Testa health check com falha"""
        self.mock_ecs.list_clusters.side_effect = Exception("Access denied")
        
        result = self.service.health_check()
        
        assert result is False
    
    def test_get_clusters(self):
        """Testa obtenção de clusters"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {'clusterArns': ['arn:aws:ecs:us-east-1:123:cluster/test']}
        ]
        self.mock_ecs.get_paginator.return_value = paginator
        
        self.mock_ecs.describe_clusters.return_value = {
            'clusters': [
                {
                    'clusterArn': 'arn:aws:ecs:us-east-1:123:cluster/test',
                    'clusterName': 'test',
                    'status': 'ACTIVE',
                    'registeredContainerInstancesCount': 2,
                    'runningTasksCount': 5,
                    'pendingTasksCount': 0,
                    'activeServicesCount': 3,
                    'capacityProviders': ['FARGATE']
                }
            ]
        }
        
        clusters = self.service.get_clusters()
        
        assert len(clusters) == 1
        assert clusters[0].cluster_name == 'test'
        assert clusters[0].running_tasks == 5
    
    def test_get_metrics(self):
        """Testa obtenção de métricas agregadas"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {'clusterArns': ['arn:aws:ecs:us-east-1:123:cluster/test']}
        ]
        self.mock_ecs.get_paginator.return_value = paginator
        
        self.mock_ecs.describe_clusters.return_value = {
            'clusters': [
                {
                    'clusterArn': 'arn:aws:ecs:us-east-1:123:cluster/test',
                    'clusterName': 'test',
                    'status': 'ACTIVE',
                    'registeredContainerInstancesCount': 2,
                    'runningTasksCount': 5,
                    'pendingTasksCount': 0,
                    'activeServicesCount': 3,
                    'capacityProviders': ['FARGATE']
                }
            ]
        }
        
        metrics = self.service.get_metrics()
        
        assert metrics.service_name == "Amazon ECS"
        assert metrics.resource_count == 1
    
    def test_get_recommendations_unused_cluster(self):
        """Testa recomendação para cluster sem uso"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {'clusterArns': ['arn:aws:ecs:us-east-1:123:cluster/unused']}
        ]
        self.mock_ecs.get_paginator.return_value = paginator
        
        self.mock_ecs.describe_clusters.return_value = {
            'clusters': [
                {
                    'clusterArn': 'arn:aws:ecs:us-east-1:123:cluster/unused',
                    'clusterName': 'unused',
                    'status': 'ACTIVE',
                    'registeredContainerInstancesCount': 0,
                    'runningTasksCount': 0,
                    'pendingTasksCount': 0,
                    'activeServicesCount': 0,
                    'capacityProviders': []
                }
            ]
        }
        
        recommendations = self.service.get_recommendations()
        
        unused_recs = [r for r in recommendations if r.recommendation_type == 'UNUSED_RESOURCE']
        assert len(unused_recs) >= 1
    
    def test_get_services(self):
        """Testa obtenção de serviços de um cluster"""
        paginator = Mock()
        paginator.paginate.return_value = [
            {'serviceArns': ['arn:aws:ecs:us-east-1:123:service/test/my-svc']}
        ]
        self.mock_ecs.get_paginator.return_value = paginator
        
        self.mock_ecs.describe_services.return_value = {
            'services': [
                {
                    'serviceArn': 'arn:aws:ecs:us-east-1:123:service/test/my-svc',
                    'serviceName': 'my-svc',
                    'clusterArn': 'arn:aws:ecs:us-east-1:123:cluster/test',
                    'status': 'ACTIVE',
                    'desiredCount': 2,
                    'runningCount': 2,
                    'pendingCount': 0,
                    'launchType': 'FARGATE'
                }
            ]
        }
        
        services = self.service.get_services('arn:aws:ecs:us-east-1:123:cluster/test')
        
        assert len(services) == 1
        assert services[0].service_name == 'my-svc'
        assert services[0].launch_type == 'FARGATE'


class TestECSTask:
    """Testes para ECSTask dataclass"""
    
    def test_create_task(self):
        """Testa criação de ECSTask"""
        task = ECSTask(
            task_arn="arn:aws:ecs:us-east-1:123:task/test/abc123",
            task_definition_arn="arn:aws:ecs:us-east-1:123:task-definition/my-task:1",
            cluster_arn="arn:aws:ecs:us-east-1:123:cluster/test",
            last_status="RUNNING",
            desired_status="RUNNING",
            launch_type="FARGATE",
            cpu="256",
            memory="512"
        )
        
        assert task.last_status == "RUNNING"
        assert task.launch_type == "FARGATE"
        assert task.cpu == "256"


class TestElastiCacheReplicationGroup:
    """Testes para ElastiCacheReplicationGroup dataclass"""
    
    def test_create_replication_group(self):
        """Testa criação de ElastiCacheReplicationGroup"""
        rg = ElastiCacheReplicationGroup(
            replication_group_id="my-rg",
            description="Test RG",
            status="available",
            automatic_failover="enabled",
            multi_az="enabled"
        )
        
        assert rg.replication_group_id == "my-rg"
        assert rg.automatic_failover == "enabled"
        assert rg.multi_az == "enabled"
