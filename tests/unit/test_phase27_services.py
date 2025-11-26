"""
Testes Unitários para FASE 2.7 - Serviços de Monitoramento e Segurança

Este módulo testa os novos serviços FinOps:
- CloudWatchService: Logs, métricas, alarmes, dashboards
- WAFService: Web ACLs, rule groups, IP sets
- CognitoService: User pools, identity pools
- EventBridgeService: Event buses, rules, archives, pipes
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.finops_aws.services.cloudwatch_service import (
    CloudWatchService, LogGroup, CloudWatchAlarm, CloudWatchDashboard, MetricStream
)
from src.finops_aws.services.waf_service import (
    WAFService, WebACL, RuleGroup, IPSet, RegexPatternSet
)
from src.finops_aws.services.cognito_service import (
    CognitoService, UserPool, UserPoolClient, IdentityPool, ResourceServer
)
from src.finops_aws.services.eventbridge_service import (
    EventBridgeService, EventBus, EventRule, EventArchive, EventPipe, SchemaRegistry
)
from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory


class TestLogGroup:
    """Testes para dataclass LogGroup"""
    
    def test_create_log_group(self):
        """Testa criação de log group"""
        lg = LogGroup(
            log_group_name='/aws/lambda/my-function',
            arn='arn:aws:logs:us-east-1:123456789:log-group:/aws/lambda/my-function',
            retention_in_days=30,
            stored_bytes=1024 * 1024 * 500,
            metric_filter_count=2,
            kms_key_id='arn:aws:kms:us-east-1:123456789:key/abc'
        )
        
        assert lg.log_group_name == '/aws/lambda/my-function'
        assert lg.has_retention_policy == True
        assert lg.is_encrypted == True
        assert lg.has_metric_filters == True
        assert lg.retention_cost_risk == 'LOW'
    
    def test_log_group_no_retention(self):
        """Testa log group sem retention"""
        lg = LogGroup(
            log_group_name='/test/logs',
            retention_in_days=None
        )
        
        assert lg.has_retention_policy == False
        assert lg.retention_cost_risk == 'HIGH'
    
    def test_log_group_to_dict(self):
        """Testa serialização de log group"""
        lg = LogGroup(log_group_name='/test')
        
        data = lg.to_dict()
        assert 'log_group_name' in data
        assert 'has_retention_policy' in data
        assert 'retention_cost_risk' in data


class TestCloudWatchAlarm:
    """Testes para dataclass CloudWatchAlarm"""
    
    def test_create_alarm(self):
        """Testa criação de alarme"""
        alarm = CloudWatchAlarm(
            alarm_name='high-cpu',
            state_value='OK',
            metric_name='CPUUtilization',
            period=300,
            alarm_actions=['arn:aws:sns:us-east-1:123456789:alerts']
        )
        
        assert alarm.alarm_name == 'high-cpu'
        assert alarm.is_in_alarm == False
        assert alarm.has_actions == True
        assert alarm.is_high_resolution == False
    
    def test_high_resolution_alarm(self):
        """Testa alarme de alta resolução"""
        alarm = CloudWatchAlarm(
            alarm_name='fast-alarm',
            period=10
        )
        
        assert alarm.is_high_resolution == True


class TestCloudWatchDashboard:
    """Testes para dataclass CloudWatchDashboard"""
    
    def test_create_dashboard(self):
        """Testa criação de dashboard"""
        db = CloudWatchDashboard(
            dashboard_name='my-dashboard',
            size=5120
        )
        
        assert db.dashboard_name == 'my-dashboard'
        assert db.size_kb == 5.0


class TestMetricStream:
    """Testes para dataclass MetricStream"""
    
    def test_create_metric_stream(self):
        """Testa criação de metric stream"""
        stream = MetricStream(
            name='my-stream',
            state='running',
            output_format='json',
            include_filters=[{'Namespace': 'AWS/EC2'}]
        )
        
        assert stream.name == 'my-stream'
        assert stream.is_running == True
        assert stream.has_filters == True


class TestCloudWatchService:
    """Testes para CloudWatchService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = CloudWatchService(mock_client_factory)
        assert service.service_name == "Amazon CloudWatch"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_logs = Mock()
        mock_logs.describe_log_groups.return_value = {'logGroups': []}
        mock_client_factory.get_client.return_value = mock_logs
        
        service = CloudWatchService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_log_groups_empty(self, mock_client_factory):
        """Testa listagem sem log groups"""
        mock_logs = Mock()
        mock_logs.get_paginator.return_value.paginate.return_value = [{'logGroups': []}]
        mock_client_factory.get_client.return_value = mock_logs
        
        service = CloudWatchService(mock_client_factory)
        groups = service.get_log_groups()
        assert len(groups) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_logs = Mock()
        mock_logs.get_paginator.return_value.paginate.return_value = [{'logGroups': []}]
        mock_cw = Mock()
        mock_cw.get_paginator.return_value.paginate.return_value = [
            {'MetricAlarms': [], 'DashboardEntries': [], 'Entries': []}
        ]
        
        def get_client(service_name):
            if service_name == 'logs':
                return mock_logs
            return mock_cw
        
        mock_client_factory.get_client = get_client
        
        service = CloudWatchService(mock_client_factory)
        resources = service.get_resources()
        assert 'log_groups' in resources
        assert 'alarms' in resources
        assert 'dashboards' in resources
        assert 'summary' in resources


class TestWebACL:
    """Testes para dataclass WebACL"""
    
    def test_create_web_acl(self):
        """Testa criação de Web ACL"""
        acl = WebACL(
            name='my-acl',
            id='abc123',
            scope='REGIONAL',
            default_action='ALLOW',
            rules=[{'Name': 'rule1'}],
            visibility_config={'cloudWatchMetricsEnabled': True, 'sampledRequestsEnabled': True},
            capacity=500
        )
        
        assert acl.name == 'my-acl'
        assert acl.is_regional == True
        assert acl.is_cloudfront == False
        assert acl.has_logging == True
        assert acl.has_sampled_requests == True
        assert acl.rule_count == 1
        assert acl.blocks_by_default == False
    
    def test_web_acl_to_dict(self):
        """Testa serialização de Web ACL"""
        acl = WebACL(name='test', id='123')
        
        data = acl.to_dict()
        assert 'name' in data
        assert 'is_regional' in data
        assert 'has_logging' in data


class TestRuleGroup:
    """Testes para dataclass RuleGroup"""
    
    def test_create_rule_group(self):
        """Testa criação de rule group"""
        rg = RuleGroup(
            name='my-rules',
            id='rg123',
            capacity=100,
            rules=[{'Name': 'r1'}, {'Name': 'r2'}],
            visibility_config={'cloudWatchMetricsEnabled': True}
        )
        
        assert rg.name == 'my-rules'
        assert rg.rule_count == 2
        assert rg.has_metrics == True


class TestIPSet:
    """Testes para dataclass IPSet"""
    
    def test_create_ip_set(self):
        """Testa criação de IP Set"""
        ip_set = IPSet(
            name='blocked-ips',
            id='ip123',
            ip_address_version='IPV4',
            addresses=['1.2.3.4/32', '5.6.7.8/32']
        )
        
        assert ip_set.name == 'blocked-ips'
        assert ip_set.address_count == 2
        assert ip_set.is_ipv6 == False


class TestWAFService:
    """Testes para WAFService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = WAFService(mock_client_factory)
        assert service.service_name == "AWS WAF"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_waf = Mock()
        mock_waf.list_web_acls.return_value = {'WebACLs': []}
        mock_client_factory.get_client.return_value = mock_waf
        
        service = WAFService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_web_acls_empty(self, mock_client_factory):
        """Testa listagem sem Web ACLs"""
        mock_waf = Mock()
        mock_waf.list_web_acls.return_value = {'WebACLs': []}
        mock_client_factory.get_client.return_value = mock_waf
        
        service = WAFService(mock_client_factory)
        acls = service.get_web_acls()
        assert len(acls) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_waf = Mock()
        mock_waf.list_web_acls.return_value = {'WebACLs': []}
        mock_waf.list_rule_groups.return_value = {'RuleGroups': []}
        mock_waf.list_ip_sets.return_value = {'IPSets': []}
        mock_waf.list_regex_pattern_sets.return_value = {'RegexPatternSets': []}
        mock_client_factory.get_client.return_value = mock_waf
        
        service = WAFService(mock_client_factory)
        resources = service.get_resources()
        assert 'web_acls' in resources
        assert 'rule_groups' in resources
        assert 'ip_sets' in resources
        assert 'summary' in resources


class TestUserPool:
    """Testes para dataclass UserPool"""
    
    def test_create_user_pool(self):
        """Testa criação de User Pool"""
        pool = UserPool(
            id='us-east-1_ABC123',
            name='my-app-users',
            mfa_configuration='ON',
            estimated_number_of_users=10000,
            deletion_protection='ACTIVE',
            sms_configuration={'SnsCallerArn': 'arn'}
        )
        
        assert pool.id == 'us-east-1_ABC123'
        assert pool.has_mfa == True
        assert pool.mfa_required == True
        assert pool.has_sms_config == True
        assert pool.has_deletion_protection == True
        assert pool.user_tier == 'GROWTH'
    
    def test_user_pool_no_mfa(self):
        """Testa User Pool sem MFA"""
        pool = UserPool(
            id='pool1',
            name='test',
            mfa_configuration='OFF'
        )
        
        assert pool.has_mfa == False
        assert pool.mfa_required == False
    
    def test_user_pool_to_dict(self):
        """Testa serialização de User Pool"""
        pool = UserPool(id='p1', name='test')
        
        data = pool.to_dict()
        assert 'id' in data
        assert 'has_mfa' in data
        assert 'user_tier' in data


class TestIdentityPool:
    """Testes para dataclass IdentityPool"""
    
    def test_create_identity_pool(self):
        """Testa criação de Identity Pool"""
        pool = IdentityPool(
            identity_pool_id='us-east-1:abc123',
            identity_pool_name='my-identity-pool',
            allow_unauthenticated_identities=True,
            cognito_identity_providers=[{'ProviderName': 'test'}],
            supported_login_providers={'accounts.google.com': 'client_id'}
        )
        
        assert pool.identity_pool_name == 'my-identity-pool'
        assert pool.allows_guest_access == True
        assert pool.has_cognito_user_pool == True
        assert pool.has_social_providers == True
        assert pool.provider_count == 2


class TestUserPoolClient:
    """Testes para dataclass UserPoolClient"""
    
    def test_create_client(self):
        """Testa criação de App Client"""
        client = UserPoolClient(
            client_id='abc123',
            user_pool_id='pool1',
            client_name='my-app',
            client_secret='secret',
            allowed_oauth_flows=['code'],
            supported_identity_providers=['COGNITO', 'Google']
        )
        
        assert client.has_secret == True
        assert client.uses_oauth == True
        assert client.has_social_providers == True


class TestCognitoService:
    """Testes para CognitoService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = CognitoService(mock_client_factory)
        assert service.service_name == "Amazon Cognito"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_cognito = Mock()
        mock_cognito.list_user_pools.return_value = {'UserPools': []}
        mock_client_factory.get_client.return_value = mock_cognito
        
        service = CognitoService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_user_pools_empty(self, mock_client_factory):
        """Testa listagem sem User Pools"""
        mock_cognito = Mock()
        mock_cognito.get_paginator.return_value.paginate.return_value = [{'UserPools': []}]
        mock_client_factory.get_client.return_value = mock_cognito
        
        service = CognitoService(mock_client_factory)
        pools = service.get_user_pools()
        assert len(pools) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_idp = Mock()
        mock_idp.get_paginator.return_value.paginate.return_value = [{'UserPools': []}]
        mock_identity = Mock()
        mock_identity.get_paginator.return_value.paginate.return_value = [{'IdentityPools': []}]
        
        def get_client(service_name):
            if service_name == 'cognito-idp':
                return mock_idp
            elif service_name == 'cognito-identity':
                return mock_identity
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = CognitoService(mock_client_factory)
        resources = service.get_resources()
        assert 'user_pools' in resources
        assert 'identity_pools' in resources
        assert 'summary' in resources


class TestEventBus:
    """Testes para dataclass EventBus"""
    
    def test_create_event_bus(self):
        """Testa criação de Event Bus"""
        bus = EventBus(
            name='default',
            arn='arn:aws:events:us-east-1:123456789:event-bus/default',
            policy='{"Version": "2012-10-17"}'
        )
        
        assert bus.name == 'default'
        assert bus.is_default == True
        assert bus.is_custom == False
        assert bus.has_policy == True
    
    def test_custom_event_bus(self):
        """Testa Event Bus customizado"""
        bus = EventBus(name='my-custom-bus')
        
        assert bus.is_default == False
        assert bus.is_custom == True


class TestEventRule:
    """Testes para dataclass EventRule"""
    
    def test_create_scheduled_rule(self):
        """Testa criação de regra agendada"""
        rule = EventRule(
            name='daily-task',
            schedule_expression='rate(1 day)',
            state='ENABLED',
            targets_count=1
        )
        
        assert rule.is_scheduled == True
        assert rule.is_event_pattern == False
        assert rule.is_enabled == True
        assert rule.has_targets == True
    
    def test_event_pattern_rule(self):
        """Testa regra com event pattern"""
        rule = EventRule(
            name='ec2-events',
            event_pattern='{"source": ["aws.ec2"]}'
        )
        
        assert rule.is_scheduled == False
        assert rule.is_event_pattern == True


class TestEventArchive:
    """Testes para dataclass EventArchive"""
    
    def test_create_archive(self):
        """Testa criação de archive"""
        archive = EventArchive(
            archive_name='my-archive',
            retention_days=90,
            size_bytes=1024 * 1024 * 1024,
            event_count=100000
        )
        
        assert archive.has_retention == True
        assert archive.is_unlimited_retention == False
        assert archive.size_gb == 1.0
    
    def test_unlimited_retention(self):
        """Testa archive com retenção ilimitada"""
        archive = EventArchive(
            archive_name='unlimited',
            retention_days=0
        )
        
        assert archive.is_unlimited_retention == True


class TestEventPipe:
    """Testes para dataclass EventPipe"""
    
    def test_create_pipe(self):
        """Testa criação de pipe"""
        pipe = EventPipe(
            name='sqs-to-lambda',
            source='arn:aws:sqs:us-east-1:123456789:queue',
            target='arn:aws:lambda:us-east-1:123456789:function:process',
            current_state='RUNNING',
            enrichment='arn:aws:lambda:us-east-1:123456789:function:enrich'
        )
        
        assert pipe.is_running == True
        assert pipe.is_stopped == False
        assert pipe.has_enrichment == True
        assert pipe.state_mismatch == False
    
    def test_stopped_pipe(self):
        """Testa pipe parado"""
        pipe = EventPipe(
            name='stopped-pipe',
            desired_state='RUNNING',
            current_state='STOPPED'
        )
        
        assert pipe.is_stopped == True
        assert pipe.state_mismatch == True


class TestEventBridgeService:
    """Testes para EventBridgeService"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_service_name(self, mock_client_factory):
        """Testa nome do serviço"""
        service = EventBridgeService(mock_client_factory)
        assert service.service_name == "Amazon EventBridge"
    
    def test_health_check(self, mock_client_factory):
        """Testa health check do serviço"""
        mock_events = Mock()
        mock_events.list_event_buses.return_value = {'EventBuses': []}
        mock_client_factory.get_client.return_value = mock_events
        
        service = EventBridgeService(mock_client_factory)
        assert service.health_check() == True
    
    def test_get_event_buses_empty(self, mock_client_factory):
        """Testa listagem sem event buses"""
        mock_events = Mock()
        mock_events.list_event_buses.return_value = {'EventBuses': []}
        mock_client_factory.get_client.return_value = mock_events
        
        service = EventBridgeService(mock_client_factory)
        buses = service.get_event_buses()
        assert len(buses) == 0
    
    def test_get_resources(self, mock_client_factory):
        """Testa get_resources"""
        mock_events = Mock()
        mock_events.list_event_buses.return_value = {'EventBuses': []}
        mock_events.get_paginator.return_value.paginate.return_value = [{'Rules': []}]
        mock_events.list_archives.return_value = {'Archives': []}
        mock_pipes = Mock()
        mock_pipes.get_paginator.return_value.paginate.return_value = [{'Pipes': []}]
        mock_schemas = Mock()
        mock_schemas.get_paginator.return_value.paginate.return_value = [{'Registries': []}]
        
        def get_client(service_name):
            if service_name == 'events':
                return mock_events
            elif service_name == 'pipes':
                return mock_pipes
            elif service_name == 'schemas':
                return mock_schemas
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = EventBridgeService(mock_client_factory)
        resources = service.get_resources()
        assert 'event_buses' in resources
        assert 'rules' in resources
        assert 'archives' in resources
        assert 'pipes' in resources
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
        
        assert 'cloudwatch_logs' in all_services
        assert 'waf' in all_services
        assert 'cognito' in all_services
        assert 'eventbridge' in all_services
        
        ServiceFactory._instance = None
    
    def test_services_are_cached(self, mock_client_factory):
        """Testa que serviços são cacheados"""
        ServiceFactory._instance = None
        
        service_factory = ServiceFactory(client_factory=mock_client_factory)
        
        cw1 = service_factory.get_cloudwatch_logs_service()
        cw2 = service_factory.get_cloudwatch_logs_service()
        assert cw1 is cw2
        
        waf1 = service_factory.get_waf_service()
        waf2 = service_factory.get_waf_service()
        assert waf1 is waf2
        
        cognito1 = service_factory.get_cognito_service()
        cognito2 = service_factory.get_cognito_service()
        assert cognito1 is cognito2
        
        eb1 = service_factory.get_eventbridge_service()
        eb2 = service_factory.get_eventbridge_service()
        assert eb1 is eb2
        
        ServiceFactory._instance = None


class TestRecommendations:
    """Testes para recomendações dos serviços"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = Mock(spec=AWSClientFactory)
        factory.get_client = Mock(return_value=Mock())
        return factory
    
    def test_cloudwatch_recommendations_empty(self, mock_client_factory):
        """Testa recomendações CloudWatch sem recursos"""
        mock_logs = Mock()
        mock_logs.get_paginator.return_value.paginate.return_value = [{'logGroups': []}]
        mock_cw = Mock()
        mock_cw.get_paginator.return_value.paginate.return_value = [{'MetricAlarms': []}]
        
        def get_client(service_name):
            if service_name == 'logs':
                return mock_logs
            return mock_cw
        
        mock_client_factory.get_client = get_client
        
        service = CloudWatchService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_waf_recommendations_empty(self, mock_client_factory):
        """Testa recomendações WAF sem recursos"""
        mock_waf = Mock()
        mock_waf.list_web_acls.return_value = {'WebACLs': []}
        mock_client_factory.get_client.return_value = mock_waf
        
        service = WAFService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_cognito_recommendations_empty(self, mock_client_factory):
        """Testa recomendações Cognito sem recursos"""
        mock_idp = Mock()
        mock_idp.get_paginator.return_value.paginate.return_value = [{'UserPools': []}]
        mock_identity = Mock()
        mock_identity.get_paginator.return_value.paginate.return_value = [{'IdentityPools': []}]
        
        def get_client(service_name):
            if service_name == 'cognito-idp':
                return mock_idp
            elif service_name == 'cognito-identity':
                return mock_identity
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = CognitoService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)
    
    def test_eventbridge_recommendations_empty(self, mock_client_factory):
        """Testa recomendações EventBridge sem recursos"""
        mock_events = Mock()
        mock_events.list_event_buses.return_value = {'EventBuses': []}
        mock_events.list_archives.return_value = {'Archives': []}
        mock_pipes = Mock()
        mock_pipes.get_paginator.return_value.paginate.return_value = [{'Pipes': []}]
        
        def get_client(service_name):
            if service_name == 'events':
                return mock_events
            elif service_name == 'pipes':
                return mock_pipes
            return Mock()
        
        mock_client_factory.get_client = get_client
        
        service = EventBridgeService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestSchemaRegistry:
    """Testes para dataclass SchemaRegistry"""
    
    def test_create_registry(self):
        """Testa criação de registry"""
        registry = SchemaRegistry(
            registry_name='my-registry',
            registry_arn='arn:aws:schemas:us-east-1:123456789:registry/my-registry',
            schema_count=5
        )
        
        assert registry.registry_name == 'my-registry'
        assert registry.is_custom == True
        assert registry.is_discovered == False
    
    def test_discovered_registry(self):
        """Testa registry descoberto"""
        registry = SchemaRegistry(
            registry_name='aws.events'
        )
        
        assert registry.is_discovered == True
        assert registry.is_custom == False


class TestResourceServer:
    """Testes para dataclass ResourceServer"""
    
    def test_create_resource_server(self):
        """Testa criação de resource server"""
        server = ResourceServer(
            identifier='https://api.example.com',
            name='My API',
            user_pool_id='pool1',
            scopes=[{'ScopeName': 'read'}, {'ScopeName': 'write'}]
        )
        
        assert server.name == 'My API'
        assert server.scope_count == 2
        
        data = server.to_dict()
        assert 'scopes' in data
        assert len(data['scopes']) == 2
