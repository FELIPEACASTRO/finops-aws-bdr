"""
Testes Unitários para FASE 2.6 - Serviços de Computação e Aplicação

Este módulo testa os novos serviços FinOps:
- BatchService: AWS Batch (computação em lote)
- StepFunctionsService: Step Functions (orquestração de workflows)
- APIGatewayService: API Gateway (REST, HTTP, WebSocket)
- TransferFamilyService: AWS Transfer Family (SFTP/FTPS/FTP)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.finops_aws.services.batch_service import (
    BatchService, BatchComputeEnvironment, BatchJobQueue, BatchJobDefinition
)
from src.finops_aws.services.stepfunctions_service import (
    StepFunctionsService, StateMachine, StateMachineExecution, Activity
)
from src.finops_aws.services.apigateway_service import (
    APIGatewayService, RestAPI, HttpAPI, APIStage, UsagePlan
)
from src.finops_aws.services.transfer_service import (
    TransferFamilyService, TransferServer, TransferUser, TransferConnector
)
from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory


class TestBatchComputeEnvironment:
    """Testes para dataclass BatchComputeEnvironment"""
    
    def test_create_compute_environment(self):
        """Testa criação de compute environment"""
        env = BatchComputeEnvironment(
            compute_environment_name='my-batch-env',
            compute_environment_arn='arn:aws:batch:us-east-1:123456789:compute-environment/my-batch-env',
            ecs_cluster_arn='arn:aws:ecs:us-east-1:123456789:cluster/batch-cluster',
            state='ENABLED',
            status='VALID',
            type='MANAGED',
            compute_resources={
                'type': 'SPOT',
                'minvCpus': 0,
                'maxvCpus': 256,
                'desiredvCpus': 0,
                'instanceTypes': ['optimal']
            }
        )
        
        assert env.compute_environment_name == 'my-batch-env'
        assert env.is_enabled == True
        assert env.is_managed == True
        assert env.is_spot == True
        assert env.is_fargate == False
        assert env.min_vcpus == 0
        assert env.max_vcpus == 256
    
    def test_fargate_environment(self):
        """Testa identificação de Fargate environment"""
        env = BatchComputeEnvironment(
            compute_environment_name='fargate-env',
            compute_environment_arn='arn',
            compute_resources={'type': 'FARGATE'}
        )
        
        assert env.is_fargate == True
        assert env.is_spot == False
    
    def test_compute_environment_to_dict(self):
        """Testa serialização de compute environment"""
        env = BatchComputeEnvironment(
            compute_environment_name='test-env',
            compute_environment_arn='arn'
        )
        
        data = env.to_dict()
        assert 'compute_environment_name' in data
        assert 'is_enabled' in data
        assert 'is_managed' in data
        assert 'is_spot' in data


class TestBatchJobQueue:
    """Testes para dataclass BatchJobQueue"""
    
    def test_create_job_queue(self):
        """Testa criação de job queue"""
        queue = BatchJobQueue(
            job_queue_name='my-queue',
            job_queue_arn='arn:aws:batch:us-east-1:123456789:job-queue/my-queue',
            state='ENABLED',
            priority=10,
            scheduling_policy_arn='arn:aws:batch:us-east-1:123456789:scheduling-policy/my-policy'
        )
        
        assert queue.job_queue_name == 'my-queue'
        assert queue.is_enabled == True
        assert queue.has_scheduling_policy == True
        assert queue.priority == 10
    
    def test_job_queue_to_dict(self):
        """Testa serialização de job queue"""
        queue = BatchJobQueue(
            job_queue_name='test-queue',
            job_queue_arn='arn'
        )
        
        data = queue.to_dict()
        assert 'job_queue_name' in data
        assert 'is_enabled' in data


class TestBatchJobDefinition:
    """Testes para dataclass BatchJobDefinition"""
    
    def test_create_job_definition(self):
        """Testa criação de job definition"""
        job_def = BatchJobDefinition(
            job_definition_name='my-job',
            job_definition_arn='arn:aws:batch:us-east-1:123456789:job-definition/my-job:1',
            revision=1,
            status='ACTIVE',
            container_properties={'vcpus': 2, 'memory': 4096},
            timeout={'attemptDurationSeconds': 3600},
            retry_strategy={'attempts': 3}
        )
        
        assert job_def.job_definition_name == 'my-job'
        assert job_def.is_active == True
        assert job_def.vcpus == 2.0
        assert job_def.memory_mb == 4096
        assert job_def.has_timeout == True
        assert job_def.timeout_seconds == 3600
        assert job_def.has_retry == True
        assert job_def.max_retries == 3


class TestBatchService:
    """Testes para BatchService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = BatchService(mock_client_factory)
        assert service.service_name == "AWS Batch"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_batch = Mock()
        mock_batch.describe_compute_environments.return_value = {'computeEnvironments': []}
        mock_client_factory.get_client.return_value = mock_batch
        
        service = BatchService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_compute_environments_empty(self, mock_client_factory):
        """Testa listagem sem compute environments"""
        mock_batch = Mock()
        mock_batch.get_paginator.return_value.paginate.return_value = [{'computeEnvironments': []}]
        mock_client_factory.get_client.return_value = mock_batch
        
        service = BatchService(mock_client_factory)
        envs = service.get_compute_environments()
        assert len(envs) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_batch = Mock()
        mock_batch.get_paginator.return_value.paginate.return_value = [
            {'computeEnvironments': [], 'jobQueues': [], 'jobDefinitions': []}
        ]
        mock_client_factory.get_client.return_value = mock_batch
        
        service = BatchService(mock_client_factory)
        resources = service.get_resources()
        assert 'compute_environments' in resources
        assert 'job_queues' in resources
        assert 'job_definitions' in resources
        assert 'summary' in resources


class TestStateMachine:
    """Testes para dataclass StateMachine"""
    
    def test_create_state_machine(self):
        """Testa criação de state machine"""
        sm = StateMachine(
            state_machine_arn='arn:aws:states:us-east-1:123456789:stateMachine:my-workflow',
            name='my-workflow',
            type='STANDARD',
            status='ACTIVE',
            logging_configuration={'level': 'ALL'},
            tracing_configuration={'enabled': True}
        )
        
        assert sm.name == 'my-workflow'
        assert sm.is_standard == True
        assert sm.is_express == False
        assert sm.is_active == True
        assert sm.has_logging == True
        assert sm.has_tracing == True
        assert sm.log_level == 'ALL'
    
    def test_express_state_machine(self):
        """Testa state machine Express"""
        sm = StateMachine(
            state_machine_arn='arn',
            name='express-workflow',
            type='EXPRESS'
        )
        
        assert sm.is_express == True
        assert sm.is_standard == False
    
    def test_state_machine_to_dict(self):
        """Testa serialização de state machine"""
        sm = StateMachine(
            state_machine_arn='arn',
            name='test-workflow'
        )
        
        data = sm.to_dict()
        assert 'name' in data
        assert 'is_standard' in data
        assert 'has_logging' in data


class TestStepFunctionsService:
    """Testes para StepFunctionsService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = StepFunctionsService(mock_client_factory)
        assert service.service_name == "AWS Step Functions"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_sfn = Mock()
        mock_sfn.list_state_machines.return_value = {'stateMachines': []}
        mock_client_factory.get_client.return_value = mock_sfn
        
        service = StepFunctionsService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_state_machines_empty(self, mock_client_factory):
        """Testa listagem sem state machines"""
        mock_sfn = Mock()
        mock_sfn.get_paginator.return_value.paginate.return_value = [{'stateMachines': []}]
        mock_client_factory.get_client.return_value = mock_sfn
        
        service = StepFunctionsService(mock_client_factory)
        machines = service.get_state_machines()
        assert len(machines) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_sfn = Mock()
        mock_sfn.get_paginator.return_value.paginate.return_value = [
            {'stateMachines': [], 'activities': []}
        ]
        mock_client_factory.get_client.return_value = mock_sfn
        
        service = StepFunctionsService(mock_client_factory)
        resources = service.get_resources()
        assert 'state_machines' in resources
        assert 'activities' in resources
        assert 'summary' in resources


class TestRestAPI:
    """Testes para dataclass RestAPI"""
    
    def test_create_rest_api(self):
        """Testa criação de REST API"""
        api = RestAPI(
            id='abc123',
            name='my-api',
            description='Test API',
            endpoint_configuration={'types': ['REGIONAL']}
        )
        
        assert api.id == 'abc123'
        assert api.name == 'my-api'
        assert api.is_regional == True
        assert api.is_edge == False
        assert api.is_private == False
    
    def test_edge_api(self):
        """Testa API Edge"""
        api = RestAPI(
            id='abc123',
            name='edge-api',
            endpoint_configuration={'types': ['EDGE']}
        )
        
        assert api.is_edge == True
    
    def test_rest_api_to_dict(self):
        """Testa serialização de REST API"""
        api = RestAPI(id='abc', name='test')
        
        data = api.to_dict()
        assert 'id' in data
        assert 'name' in data
        assert 'endpoint_type' in data


class TestHttpAPI:
    """Testes para dataclass HttpAPI"""
    
    def test_create_http_api(self):
        """Testa criação de HTTP API"""
        api = HttpAPI(
            api_id='xyz789',
            name='my-http-api',
            protocol_type='HTTP',
            cors_configuration={'AllowOrigins': ['*']}
        )
        
        assert api.api_id == 'xyz789'
        assert api.is_http == True
        assert api.is_websocket == False
        assert api.has_cors == True
    
    def test_websocket_api(self):
        """Testa WebSocket API"""
        api = HttpAPI(
            api_id='ws123',
            name='websocket-api',
            protocol_type='WEBSOCKET'
        )
        
        assert api.is_websocket == True
        assert api.is_http == False


class TestAPIGatewayService:
    """Testes para APIGatewayService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = APIGatewayService(mock_client_factory)
        assert service.service_name == "AWS API Gateway"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_apigw = Mock()
        mock_apigw.get_rest_apis.return_value = {'items': []}
        mock_client_factory.get_client.return_value = mock_apigw
        
        service = APIGatewayService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_rest_apis_empty(self, mock_client_factory):
        """Testa listagem sem REST APIs"""
        mock_apigw = Mock()
        mock_apigw.get_paginator.return_value.paginate.return_value = [{'items': []}]
        mock_client_factory.get_client.return_value = mock_apigw
        
        service = APIGatewayService(mock_client_factory)
        apis = service.get_rest_apis()
        assert len(apis) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_apigw = Mock()
        mock_apigw.get_paginator.return_value.paginate.return_value = [{'items': [], 'Items': []}]
        mock_apigwv2 = Mock()
        mock_apigwv2.get_paginator.return_value.paginate.return_value = [{'Items': []}]
        
        def get_client(service_name):
            if service_name == 'apigateway':
                return mock_apigw
            elif service_name == 'apigatewayv2':
                return mock_apigwv2
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = APIGatewayService(mock_client_factory)
        resources = service.get_resources()
        assert 'rest_apis' in resources
        assert 'http_apis' in resources
        assert 'summary' in resources


class TestTransferServer:
    """Testes para dataclass TransferServer"""
    
    def test_create_transfer_server(self):
        """Testa criação de servidor Transfer"""
        server = TransferServer(
            server_id='s-12345678',
            arn='arn:aws:transfer:us-east-1:123456789:server/s-12345678',
            domain='S3',
            endpoint_type='PUBLIC',
            protocols=['SFTP', 'FTPS'],
            state='ONLINE',
            user_count=5,
            logging_role='arn:aws:iam::123456789:role/transfer-logging'
        )
        
        assert server.server_id == 's-12345678'
        assert server.is_online == True
        assert server.is_public == True
        assert server.supports_sftp == True
        assert server.supports_ftps == True
        assert server.supports_ftp == False
        assert server.uses_s3 == True
        assert server.has_logging == True
    
    def test_vpc_server(self):
        """Testa servidor VPC"""
        server = TransferServer(
            server_id='s-vpc',
            arn='arn',
            endpoint_type='VPC'
        )
        
        assert server.is_vpc == True
        assert server.is_public == False
    
    def test_transfer_server_to_dict(self):
        """Testa serialização de servidor"""
        server = TransferServer(server_id='s-test', arn='arn')
        
        data = server.to_dict()
        assert 'server_id' in data
        assert 'is_online' in data
        assert 'supports_sftp' in data


class TestTransferUser:
    """Testes para dataclass TransferUser"""
    
    def test_create_transfer_user(self):
        """Testa criação de usuário Transfer"""
        user = TransferUser(
            user_name='my-user',
            server_id='s-12345678',
            home_directory='/bucket/home',
            home_directory_type='PATH',
            ssh_public_key_count=2
        )
        
        assert user.user_name == 'my-user'
        assert user.uses_logical_directory == False
        assert user.has_ssh_keys == True
    
    def test_logical_directory_user(self):
        """Testa usuário com diretório lógico"""
        user = TransferUser(
            user_name='logical-user',
            server_id='s-123',
            home_directory_type='LOGICAL'
        )
        
        assert user.uses_logical_directory == True


class TestTransferFamilyService:
    """Testes para TransferFamilyService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = TransferFamilyService(mock_client_factory)
        assert service.service_name == "AWS Transfer Family"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_transfer = Mock()
        mock_transfer.list_servers.return_value = {'Servers': []}
        mock_client_factory.get_client.return_value = mock_transfer
        
        service = TransferFamilyService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_servers_empty(self, mock_client_factory):
        """Testa listagem sem servidores"""
        mock_transfer = Mock()
        mock_transfer.get_paginator.return_value.paginate.return_value = [{'Servers': []}]
        mock_client_factory.get_client.return_value = mock_transfer
        
        service = TransferFamilyService(mock_client_factory)
        servers = service.get_servers()
        assert len(servers) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_transfer = Mock()
        mock_transfer.get_paginator.return_value.paginate.return_value = [
            {'Servers': [], 'Users': [], 'Connectors': []}
        ]
        mock_client_factory.get_client.return_value = mock_transfer
        
        service = TransferFamilyService(mock_client_factory)
        resources = service.get_resources()
        assert 'servers' in resources
        assert 'users' in resources
        assert 'connectors' in resources
        assert 'summary' in resources


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_get_all_services_includes_new_services(self, mock_client_factory):
        """Testa que get_all_services inclui os novos serviços"""
        ServiceFactory._instance = None
        
        service_factory = ServiceFactory(client_factory=mock_client_factory)
        all_services = service_factory.get_all_services()
        
        assert 'batch' in all_services
        assert 'stepfunctions' in all_services
        assert 'apigateway' in all_services
        assert 'transfer' in all_services
        
        ServiceFactory._instance = None
    
    def test_services_are_cached(self, mock_client_factory):
        """Testa que serviços são cacheados"""
        ServiceFactory._instance = None
        
        service_factory = ServiceFactory(client_factory=mock_client_factory)
        
        batch1 = service_factory.get_batch_service()
        batch2 = service_factory.get_batch_service()
        assert batch1 is batch2
        
        sfn1 = service_factory.get_stepfunctions_service()
        sfn2 = service_factory.get_stepfunctions_service()
        assert sfn1 is sfn2
        
        ServiceFactory._instance = None


class TestRecommendations:
    """Testes para recomendações dos serviços"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_batch_recommendations_empty(self, mock_client_factory):
        """Testa recomendações Batch sem recursos"""
        mock_batch = Mock()
        mock_batch.get_paginator.return_value.paginate.return_value = [
            {'computeEnvironments': [], 'jobDefinitions': []}
        ]
        mock_client_factory.get_client.return_value = mock_batch
        
        service = BatchService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_stepfunctions_recommendations_empty(self, mock_client_factory):
        """Testa recomendações Step Functions sem recursos"""
        mock_sfn = Mock()
        mock_sfn.get_paginator.return_value.paginate.return_value = [{'stateMachines': []}]
        mock_client_factory.get_client.return_value = mock_sfn
        
        service = StepFunctionsService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_apigateway_recommendations_empty(self, mock_client_factory):
        """Testa recomendações API Gateway sem recursos"""
        mock_apigw = Mock()
        mock_apigw.get_paginator.return_value.paginate.return_value = [{'items': []}]
        mock_apigwv2 = Mock()
        mock_apigwv2.get_paginator.return_value.paginate.return_value = [{'Items': []}]
        
        def get_client(service_name):
            if service_name == 'apigateway':
                return mock_apigw
            elif service_name == 'apigatewayv2':
                return mock_apigwv2
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = APIGatewayService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_transfer_recommendations_empty(self, mock_client_factory):
        """Testa recomendações Transfer sem recursos"""
        mock_transfer = Mock()
        mock_transfer.get_paginator.return_value.paginate.return_value = [{'Servers': []}]
        mock_client_factory.get_client.return_value = mock_transfer
        
        service = TransferFamilyService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestStateMachineExecution:
    """Testes para dataclass StateMachineExecution"""
    
    def test_create_execution(self):
        """Testa criação de execução"""
        now = datetime.now()
        execution = StateMachineExecution(
            execution_arn='arn:aws:states:us-east-1:123456789:execution:my-workflow:exec-1',
            state_machine_arn='arn:aws:states:us-east-1:123456789:stateMachine:my-workflow',
            name='exec-1',
            status='SUCCEEDED',
            start_date=now - timedelta(minutes=5),
            stop_date=now
        )
        
        assert execution.name == 'exec-1'
        assert execution.is_succeeded == True
        assert execution.is_running == False
        assert execution.duration_seconds is not None
        assert execution.duration_seconds >= 300  # 5 minutes


class TestActivity:
    """Testes para dataclass Activity"""
    
    def test_create_activity(self):
        """Testa criação de atividade"""
        activity = Activity(
            activity_arn='arn:aws:states:us-east-1:123456789:activity:my-activity',
            name='my-activity',
            creation_date=datetime.now()
        )
        
        assert activity.name == 'my-activity'
        data = activity.to_dict()
        assert 'activity_arn' in data
        assert 'name' in data


class TestAPIStage:
    """Testes para dataclass APIStage"""
    
    def test_create_stage(self):
        """Testa criação de stage"""
        stage = APIStage(
            stage_name='prod',
            api_id='abc123',
            cache_cluster_enabled=True,
            cache_cluster_size='0.5',
            throttling_burst_limit=1000,
            throttling_rate_limit=500.0,
            tracing_enabled=True
        )
        
        assert stage.stage_name == 'prod'
        assert stage.has_caching == True
        assert stage.has_throttling == True
        assert stage.has_tracing == True
    
    def test_stage_without_features(self):
        """Testa stage sem features"""
        stage = APIStage(
            stage_name='dev',
            api_id='abc123'
        )
        
        assert stage.has_caching == False
        assert stage.has_throttling == False
        assert stage.has_tracing == False


class TestUsagePlan:
    """Testes para dataclass UsagePlan"""
    
    def test_create_usage_plan(self):
        """Testa criação de usage plan"""
        plan = UsagePlan(
            id='plan-123',
            name='basic-plan',
            throttle={'burstLimit': 100, 'rateLimit': 50.0},
            quota={'limit': 1000, 'period': 'MONTH'}
        )
        
        assert plan.name == 'basic-plan'
        assert plan.has_throttle == True
        assert plan.has_quota == True
        assert plan.throttle_burst_limit == 100
        assert plan.quota_limit == 1000
        assert plan.quota_period == 'MONTH'


class TestTransferConnector:
    """Testes para dataclass TransferConnector"""
    
    def test_create_connector(self):
        """Testa criação de conector"""
        connector = TransferConnector(
            connector_id='c-12345678',
            arn='arn:aws:transfer:us-east-1:123456789:connector/c-12345678',
            url='sftp://partner.example.com',
            logging_role='arn:aws:iam::123456789:role/connector-logging'
        )
        
        assert connector.connector_id == 'c-12345678'
        assert connector.has_logging == True
    
    def test_connector_to_dict(self):
        """Testa serialização de conector"""
        connector = TransferConnector(
            connector_id='c-test',
            arn='arn'
        )
        
        data = connector.to_dict()
        assert 'connector_id' in data
        assert 'has_logging' in data
