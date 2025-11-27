"""
Testes Unitários FASE 2.9 - Security & Compliance Services

Testa os 6 serviços de Segurança e Conformidade:
- GuardDutyService
- InspectorService
- ConfigService
- CloudTrailService
- KMSService
- ACMService
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

from src.finops_aws.services.guardduty_service import (
    GuardDutyService, Detector, Finding, Member
)
from src.finops_aws.services.inspector_service import (
    InspectorService, InspectorFinding, CoverageStatistics, AccountStatus
)
from src.finops_aws.services.config_service import (
    ConfigService, ConfigRule, ConfigurationRecorder, DeliveryChannel, ConformancePack
)
from src.finops_aws.services.cloudtrail_service import (
    CloudTrailService, Trail, EventDataStore, Channel
)
from src.finops_aws.services.kms_service import (
    KMSService, KMSKey, KeyAlias, Grant
)
from src.finops_aws.services.acm_service import (
    ACMService, Certificate
)
from src.finops_aws.core.factories import ServiceFactory


class TestDetectorDataclass:
    """Testes para dataclass Detector"""
    
    def test_detector_creation(self):
        detector = Detector(
            detector_id='test-detector',
            status='ENABLED',
            finding_publishing_frequency='FIFTEEN_MINUTES'
        )
        assert detector.detector_id == 'test-detector'
        assert detector.is_enabled is True
        assert detector.publishes_frequently is True
    
    def test_detector_disabled(self):
        detector = Detector(
            detector_id='test-detector',
            status='DISABLED'
        )
        assert detector.is_enabled is False
    
    def test_detector_data_sources(self):
        detector = Detector(
            detector_id='test-detector',
            data_sources={
                's3Logs': {'status': 'ENABLED'},
                'kubernetes': {'auditLogs': {'status': 'ENABLED'}},
                'malwareProtection': {'status': 'ENABLED'}
            }
        )
        assert detector.has_s3_protection is True
        assert detector.has_kubernetes_protection is True
        assert detector.has_malware_protection is True
    
    def test_detector_runtime_monitoring(self):
        detector = Detector(
            detector_id='test-detector',
            features=[{'name': 'RUNTIME_MONITORING', 'status': 'ENABLED'}]
        )
        assert detector.has_runtime_monitoring is True
    
    def test_detector_to_dict(self):
        detector = Detector(detector_id='test-detector')
        result = detector.to_dict()
        assert 'detector_id' in result
        assert 'is_enabled' in result


class TestFindingDataclass:
    """Testes para dataclass Finding"""
    
    def test_finding_creation(self):
        finding = Finding(
            finding_id='test-finding',
            detector_id='test-detector',
            account_id='123456789012',
            severity=8.0
        )
        assert finding.finding_id == 'test-finding'
        assert finding.severity_level == 'HIGH'
        assert finding.is_high_severity is True
    
    def test_finding_severity_levels(self):
        high = Finding(finding_id='high', detector_id='d', account_id='a', severity=7.5)
        medium = Finding(finding_id='medium', detector_id='d', account_id='a', severity=5.0)
        low = Finding(finding_id='low', detector_id='d', account_id='a', severity=2.0)
        
        assert high.is_high_severity is True
        assert medium.is_medium_severity is True
        assert low.is_low_severity is True
    
    def test_finding_to_dict(self):
        finding = Finding(finding_id='test', detector_id='d', account_id='a')
        result = finding.to_dict()
        assert 'finding_id' in result
        assert 'severity_level' in result


class TestMemberDataclass:
    """Testes para dataclass Member"""
    
    def test_member_creation(self):
        member = Member(
            account_id='123456789012',
            detector_id='test-detector',
            relationship_status='ENABLED'
        )
        assert member.account_id == '123456789012'
        assert member.is_active is True
    
    def test_member_pending(self):
        member = Member(
            account_id='123456789012',
            detector_id='test-detector',
            relationship_status='INVITED'
        )
        assert member.is_pending is True


class TestGuardDutyService:
    """Testes para GuardDutyService"""
    
    def test_service_creation(self):
        service = GuardDutyService()
        assert service.service_name == 'guardduty'
    
    def test_service_with_factory(self):
        mock_factory = MagicMock()
        service = GuardDutyService(client_factory=mock_factory)
        assert service._client_factory == mock_factory
    
    def test_health_check_success(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        mock_client.list_detectors.return_value = {'DetectorIds': []}
        
        service = GuardDutyService(client_factory=mock_factory)
        assert service.health_check() is True


class TestInspectorFindingDataclass:
    """Testes para dataclass InspectorFinding"""
    
    def test_finding_creation(self):
        finding = InspectorFinding(
            finding_arn='arn:aws:inspector2:us-east-1:123456789012:finding/test',
            severity='CRITICAL'
        )
        assert finding.is_critical is True
    
    def test_finding_severity_levels(self):
        critical = InspectorFinding(finding_arn='crit', severity='CRITICAL')
        high = InspectorFinding(finding_arn='high', severity='HIGH')
        medium = InspectorFinding(finding_arn='med', severity='MEDIUM')
        low = InspectorFinding(finding_arn='low', severity='LOW')
        
        assert critical.is_critical is True
        assert high.is_high is True
        assert medium.is_medium is True
        assert low.is_low is True
    
    def test_finding_exploitable(self):
        finding = InspectorFinding(
            finding_arn='test',
            exploit_available=True,
            fix_available=True
        )
        assert finding.is_exploitable is True
        assert finding.has_fix is True


class TestCoverageStatistics:
    """Testes para dataclass CoverageStatistics"""
    
    def test_coverage_creation(self):
        stats = CoverageStatistics(
            total_resources=100,
            covered_resources=80,
            ec2_instances=50,
            ec2_covered=40
        )
        assert stats.coverage_percentage == 80.0
        assert stats.has_full_coverage is False
    
    def test_full_coverage(self):
        stats = CoverageStatistics(
            total_resources=100,
            covered_resources=100
        )
        assert stats.has_full_coverage is True


class TestAccountStatus:
    """Testes para dataclass AccountStatus"""
    
    def test_account_enabled(self):
        status = AccountStatus(
            account_id='123456789012',
            status='ENABLED',
            resource_status={
                'ec2': {'status': 'ENABLED'},
                'ecr': {'status': 'ENABLED'},
                'lambda': {'status': 'ENABLED'}
            }
        )
        assert status.is_enabled is True
        assert status.ec2_scanning_enabled is True
        assert status.ecr_scanning_enabled is True
        assert status.lambda_scanning_enabled is True


class TestInspectorService:
    """Testes para InspectorService"""
    
    def test_service_creation(self):
        service = InspectorService()
        assert service.service_name == 'inspector2'
    
    def test_health_check_success(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        mock_client.batch_get_account_status.return_value = {'accounts': []}
        
        service = InspectorService(client_factory=mock_factory)
        assert service.health_check() is True


class TestConfigRuleDataclass:
    """Testes para dataclass ConfigRule"""
    
    def test_rule_creation(self):
        rule = ConfigRule(
            rule_name='test-rule',
            source_owner='AWS',
            config_rule_state='ACTIVE'
        )
        assert rule.is_active is True
        assert rule.is_aws_managed is True
    
    def test_rule_compliance(self):
        compliant = ConfigRule(rule_name='comp', compliance_status='COMPLIANT')
        non_compliant = ConfigRule(rule_name='non', compliance_status='NON_COMPLIANT')
        
        assert compliant.is_compliant is True
        assert non_compliant.is_non_compliant is True
    
    def test_rule_compliance_percentage(self):
        rule = ConfigRule(
            rule_name='test',
            compliant_count=80,
            non_compliant_count=20
        )
        assert rule.compliance_percentage == 80.0


class TestConfigurationRecorder:
    """Testes para dataclass ConfigurationRecorder"""
    
    def test_recorder_creation(self):
        recorder = ConfigurationRecorder(
            name='test-recorder',
            status='SUCCESS',
            recording_group={'allSupported': True, 'includeGlobalResourceTypes': True}
        )
        assert recorder.is_recording is True
        assert recorder.records_all_resources is True
        assert recorder.includes_global_resources is True


class TestDeliveryChannel:
    """Testes para dataclass DeliveryChannel"""
    
    def test_channel_creation(self):
        channel = DeliveryChannel(
            name='test-channel',
            s3_bucket_name='my-bucket',
            sns_topic_arn='arn:aws:sns:us-east-1:123456789012:my-topic'
        )
        assert channel.has_s3_bucket is True
        assert channel.has_sns_topic is True


class TestConformancePack:
    """Testes para dataclass ConformancePack"""
    
    def test_pack_creation(self):
        pack = ConformancePack(
            name='test-pack',
            conformance_pack_state='CREATE_COMPLETE'
        )
        assert pack.is_complete is True
        assert pack.is_failed is False


class TestConfigService:
    """Testes para ConfigService"""
    
    def test_service_creation(self):
        service = ConfigService()
        assert service.service_name == 'config'
    
    def test_health_check_success(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        mock_client.describe_configuration_recorders.return_value = {'ConfigurationRecorders': []}
        
        service = ConfigService(client_factory=mock_factory)
        assert service.health_check() is True


class TestTrailDataclass:
    """Testes para dataclass Trail"""
    
    def test_trail_creation(self):
        trail = Trail(
            name='test-trail',
            is_multi_region_trail=True,
            include_global_service_events=True,
            kms_key_id='arn:aws:kms:us-east-1:123456789012:key/test',
            log_file_validation_enabled=True
        )
        assert trail.is_global_trail is True
        assert trail.is_encrypted is True
        assert trail.has_log_validation is True
    
    def test_trail_cloudwatch_logs(self):
        trail = Trail(
            name='test-trail',
            cloud_watch_logs_log_group_arn='arn:aws:logs:us-east-1:123456789012:log-group:test'
        )
        assert trail.has_cloudwatch_logs is True
    
    def test_trail_sns_notifications(self):
        trail = Trail(
            name='test-trail',
            sns_topic_arn='arn:aws:sns:us-east-1:123456789012:topic'
        )
        assert trail.has_sns_notifications is True


class TestEventDataStore:
    """Testes para dataclass EventDataStore"""
    
    def test_data_store_creation(self):
        store = EventDataStore(
            name='test-store',
            status='ENABLED',
            retention_period=2557
        )
        assert store.is_enabled is True
        assert store.retention_years == 2557 / 365
        assert store.is_long_retention is True
    
    def test_data_store_encryption(self):
        store = EventDataStore(
            name='test-store',
            kms_key_id='arn:aws:kms:us-east-1:123456789012:key/test'
        )
        assert store.is_encrypted is True


class TestCloudTrailService:
    """Testes para CloudTrailService"""
    
    def test_service_creation(self):
        service = CloudTrailService()
        assert service.service_name == 'cloudtrail'
    
    def test_health_check_success(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        mock_client.describe_trails.return_value = {'trailList': []}
        
        service = CloudTrailService(client_factory=mock_factory)
        assert service.health_check() is True


class TestKMSKeyDataclass:
    """Testes para dataclass KMSKey"""
    
    def test_key_creation(self):
        key = KMSKey(
            key_id='test-key',
            key_state='Enabled',
            key_manager='CUSTOMER',
            enabled=True
        )
        assert key.is_enabled is True
        assert key.is_customer_managed is True
    
    def test_key_aws_managed(self):
        key = KMSKey(
            key_id='test-key',
            key_manager='AWS'
        )
        assert key.is_aws_managed is True
    
    def test_key_symmetric_asymmetric(self):
        symmetric = KMSKey(key_id='sym', key_spec='SYMMETRIC_DEFAULT')
        asymmetric = KMSKey(key_id='asym', key_spec='RSA_2048')
        
        assert symmetric.is_symmetric is True
        assert asymmetric.is_asymmetric is True
    
    def test_key_imported(self):
        key = KMSKey(
            key_id='test-key',
            origin='EXTERNAL'
        )
        assert key.is_imported is True
    
    def test_key_pending_deletion(self):
        key = KMSKey(
            key_id='test-key',
            key_state='PendingDeletion'
        )
        assert key.is_pending_deletion is True
    
    def test_key_aliases(self):
        key = KMSKey(
            key_id='test-key',
            aliases=['alias/my-key']
        )
        assert key.has_alias is True


class TestKeyAlias:
    """Testes para dataclass KeyAlias"""
    
    def test_alias_creation(self):
        alias = KeyAlias(
            alias_name='alias/my-key',
            target_key_id='test-key'
        )
        assert alias.is_custom_alias is True
    
    def test_aws_alias(self):
        alias = KeyAlias(
            alias_name='alias/aws/s3'
        )
        assert alias.is_aws_alias is True
        assert alias.is_custom_alias is False


class TestGrant:
    """Testes para dataclass Grant"""
    
    def test_grant_creation(self):
        grant = Grant(
            key_id='test-key',
            grant_id='test-grant',
            operations=['Decrypt', 'Encrypt', 'GenerateDataKey']
        )
        assert grant.operation_count == 3
        assert grant.allows_decrypt is True
        assert grant.allows_encrypt is True


class TestKMSService:
    """Testes para KMSService"""
    
    def test_service_creation(self):
        service = KMSService()
        assert service.service_name == 'kms'
    
    def test_health_check_success(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        mock_client.list_keys.return_value = {'Keys': []}
        
        service = KMSService(client_factory=mock_factory)
        assert service.health_check() is True


class TestCertificateDataclass:
    """Testes para dataclass Certificate"""
    
    def test_certificate_creation(self):
        cert = Certificate(
            certificate_arn='arn:aws:acm:us-east-1:123456789012:certificate/test',
            domain_name='example.com',
            status='ISSUED',
            type='AMAZON_ISSUED'
        )
        assert cert.is_issued is True
        assert cert.is_amazon_issued is True
    
    def test_certificate_imported(self):
        cert = Certificate(
            certificate_arn='arn:aws:acm:us-east-1:123456789012:certificate/test',
            type='IMPORTED'
        )
        assert cert.is_imported is True
    
    def test_certificate_pending_validation(self):
        cert = Certificate(
            certificate_arn='test',
            status='PENDING_VALIDATION'
        )
        assert cert.is_pending_validation is True
    
    def test_certificate_expired(self):
        cert = Certificate(
            certificate_arn='test',
            status='EXPIRED'
        )
        assert cert.is_expired is True
    
    def test_certificate_in_use(self):
        cert = Certificate(
            certificate_arn='test',
            in_use_by=['arn:aws:elasticloadbalancing:...']
        )
        assert cert.is_in_use is True
    
    def test_certificate_expiry_calculation(self):
        future = datetime.now(timezone.utc) + timedelta(days=15)
        cert = Certificate(
            certificate_arn='test',
            status='ISSUED',
            not_after=future
        )
        assert cert.days_until_expiry <= 15
        assert cert.is_expiring_soon is True
    
    def test_certificate_san_count(self):
        cert = Certificate(
            certificate_arn='test',
            subject_alternative_names=['example.com', '*.example.com', 'api.example.com']
        )
        assert cert.san_count == 3


class TestACMService:
    """Testes para ACMService"""
    
    def test_service_creation(self):
        service = ACMService()
        assert service.service_name == 'acm'
    
    def test_health_check_success(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        mock_client.list_certificates.return_value = {'CertificateSummaryList': []}
        
        service = ACMService(client_factory=mock_factory)
        assert service.health_check() is True


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory"""
    
    def test_get_guardduty_service(self):
        factory = ServiceFactory()
        service = factory.get_guardduty_service()
        assert service is not None
        assert service.service_name == 'guardduty'
    
    def test_get_inspector_service(self):
        factory = ServiceFactory()
        service = factory.get_inspector_service()
        assert service is not None
        assert service.service_name == 'inspector2'
    
    def test_get_config_service(self):
        factory = ServiceFactory()
        service = factory.get_config_service()
        assert service is not None
        assert service.service_name == 'config'
    
    def test_get_cloudtrail_service(self):
        factory = ServiceFactory()
        service = factory.get_cloudtrail_service()
        assert service is not None
        assert service.service_name == 'cloudtrail'
    
    def test_get_kms_service(self):
        factory = ServiceFactory()
        service = factory.get_kms_service()
        assert service is not None
        assert service.service_name == 'kms'
    
    def test_get_acm_service(self):
        factory = ServiceFactory()
        service = factory.get_acm_service()
        assert service is not None
        assert service.service_name == 'acm'
    
    def test_services_in_get_all_services(self):
        factory = ServiceFactory()
        all_services = factory.get_all_services()
        
        assert 'guardduty' in all_services
        assert 'inspector' in all_services
        assert 'config' in all_services
        assert 'cloudtrail' in all_services
        assert 'kms' in all_services
        assert 'acm' in all_services


class TestGetResourcesMethods:
    """Testes para métodos get_resources()"""
    
    def test_guardduty_get_resources(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        
        paginator = MagicMock()
        mock_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [{'DetectorIds': ['detector-1']}]
        
        mock_client.get_detector.return_value = {
            'Status': 'ENABLED',
            'FindingPublishingFrequency': 'SIX_HOURS'
        }
        mock_client.list_findings.return_value = {'FindingIds': []}
        mock_client.list_members.return_value = {'Members': []}
        
        paginator_members = MagicMock()
        mock_client.get_paginator.side_effect = lambda x: paginator if x == 'list_detectors' else paginator_members
        paginator_members.paginate.return_value = [{'Members': []}]
        
        service = GuardDutyService(client_factory=mock_factory)
        result = service.get_resources()
        
        assert 'detectors' in result
        assert 'summary' in result
    
    def test_inspector_get_resources(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        
        mock_client.batch_get_account_status.return_value = {'accounts': []}
        
        paginator = MagicMock()
        mock_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [{'findings': []}]
        mock_client.list_coverage_statistics.return_value = {'countsByGroup': []}
        
        service = InspectorService(client_factory=mock_factory)
        result = service.get_resources()
        
        assert 'findings' in result
        assert 'summary' in result
    
    def test_config_get_resources(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        
        paginator = MagicMock()
        mock_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [{'ConfigRules': []}]
        mock_client.describe_configuration_recorders.return_value = {'ConfigurationRecorders': []}
        mock_client.describe_configuration_recorder_status.return_value = {'ConfigurationRecordersStatus': []}
        mock_client.describe_delivery_channels.return_value = {'DeliveryChannels': []}
        
        service = ConfigService(client_factory=mock_factory)
        result = service.get_resources()
        
        assert 'config_rules' in result
        assert 'summary' in result
    
    def test_cloudtrail_get_resources(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        
        mock_client.describe_trails.return_value = {'trailList': []}
        
        paginator = MagicMock()
        mock_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [{'EventDataStores': [], 'Channels': []}]
        
        service = CloudTrailService(client_factory=mock_factory)
        result = service.get_resources()
        
        assert 'trails' in result
        assert 'summary' in result
    
    def test_kms_get_resources(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        
        paginator = MagicMock()
        mock_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [{'Keys': [], 'Aliases': []}]
        
        service = KMSService(client_factory=mock_factory)
        result = service.get_resources()
        
        assert 'keys' in result
        assert 'summary' in result
    
    def test_acm_get_resources(self):
        mock_factory = MagicMock()
        mock_client = MagicMock()
        mock_factory.get_client.return_value = mock_client
        
        paginator = MagicMock()
        mock_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [{'CertificateSummaryList': []}]
        
        service = ACMService(client_factory=mock_factory)
        result = service.get_resources()
        
        assert 'certificates' in result
        assert 'summary' in result


class TestGetRecommendationsMethods:
    """Testes para métodos get_recommendations()"""
    
    def test_guardduty_recommendations_disabled_detector(self):
        service = GuardDutyService()
        
        with patch.object(service, 'get_detectors') as mock_detectors, \
             patch.object(service, 'get_findings') as mock_findings:
            mock_detectors.return_value = [Detector(detector_id='test', status='DISABLED')]
            mock_findings.return_value = []
            
            recommendations = service.get_recommendations()
            
            assert len(recommendations) > 0
            assert any('desabilitado' in r.get('title', '').lower() for r in recommendations)
    
    def test_inspector_recommendations_critical_exploitable(self):
        service = InspectorService()
        
        with patch.object(service, 'get_account_status') as mock_status, \
             patch.object(service, 'get_findings') as mock_findings, \
             patch.object(service, 'get_coverage_statistics') as mock_coverage:
            mock_status.return_value = [AccountStatus(account_id='123', status='ENABLED')]
            mock_findings.return_value = [
                InspectorFinding(finding_arn='crit', severity='CRITICAL', exploit_available=True)
            ]
            mock_coverage.return_value = CoverageStatistics(total_resources=100, covered_resources=90)
            
            recommendations = service.get_recommendations()
            
            assert len(recommendations) > 0
    
    def test_cloudtrail_recommendations_no_trails(self):
        service = CloudTrailService()
        
        with patch.object(service, 'get_trails') as mock_trails, \
             patch.object(service, 'get_event_data_stores') as mock_stores:
            mock_trails.return_value = []
            mock_stores.return_value = []
            
            recommendations = service.get_recommendations()
            
            assert len(recommendations) > 0
            assert any('nenhum trail' in r.get('title', '').lower() for r in recommendations)
    
    def test_acm_recommendations_expiring_certificate(self):
        service = ACMService()
        
        with patch.object(service, 'get_certificates') as mock_certs:
            future = datetime.now(timezone.utc) + timedelta(days=7)
            mock_certs.return_value = [
                Certificate(
                    certificate_arn='test',
                    domain_name='example.com',
                    status='ISSUED',
                    not_after=future
                )
            ]
            
            recommendations = service.get_recommendations()
            
            assert len(recommendations) > 0
            assert any('expirando' in r.get('title', '').lower() for r in recommendations)
