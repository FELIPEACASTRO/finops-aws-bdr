"""
Testes unitários para FASE 3.3 - Container & App Services.

ECR, App Runner, Elastic Beanstalk, Lightsail.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.finops_aws.services.ecr_service import (
    ECRService, ECRRepository, ECRImage, ECRLifecyclePolicy
)
from src.finops_aws.services.apprunner_service import (
    AppRunnerServiceManager, AppRunnerService, AppRunnerAutoScalingConfiguration, AppRunnerVpcConnector
)
from src.finops_aws.services.elasticbeanstalk_service import (
    ElasticBeanstalkService, BeanstalkApplication, BeanstalkEnvironment, BeanstalkApplicationVersion
)
from src.finops_aws.services.lightsail_service import (
    LightsailService, LightsailInstance, LightsailDatabase, LightsailContainer
)
from src.finops_aws.core.factories import ServiceFactory


class TestECRRepositoryDataclass:
    """Testes para ECRRepository dataclass."""

    def test_repository_basic(self):
        """Testa criação básica de repositório."""
        repo = ECRRepository(
            repository_name="my-app",
            repository_arn="arn:aws:ecr:us-east-1:123456789012:repository/my-app",
            repository_uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app"
        )
        assert repo.repository_name == "my-app"
        assert repo.is_immutable is False
        assert repo.has_scan_on_push is False
        assert repo.has_encryption is False

    def test_repository_immutable(self):
        """Testa repositório com tags imutáveis."""
        repo = ECRRepository(
            repository_name="secure-app",
            image_tag_mutability="IMMUTABLE"
        )
        assert repo.is_immutable is True

    def test_repository_scan_on_push(self):
        """Testa repositório com scan on push."""
        repo = ECRRepository(
            repository_name="scanned-app",
            image_scanning_configuration={"scanOnPush": True}
        )
        assert repo.has_scan_on_push is True

    def test_repository_kms_encryption(self):
        """Testa repositório com criptografia KMS."""
        repo = ECRRepository(
            repository_name="encrypted-app",
            encryption_configuration={
                "encryptionType": "KMS",
                "kmsKey": "arn:aws:kms:us-east-1:123456789012:key/my-key"
            }
        )
        assert repo.has_encryption is True
        assert repo.kms_key == "arn:aws:kms:us-east-1:123456789012:key/my-key"

    def test_repository_to_dict(self):
        """Testa conversão para dicionário."""
        repo = ECRRepository(
            repository_name="my-app",
            image_tag_mutability="IMMUTABLE"
        )
        result = repo.to_dict()
        assert result["repository_name"] == "my-app"
        assert result["is_immutable"] is True


class TestECRImageDataclass:
    """Testes para ECRImage dataclass."""

    def test_image_basic(self):
        """Testa criação básica de imagem."""
        image = ECRImage(
            repository_name="my-app",
            image_digest="sha256:abc123",
            image_tags=["latest", "v1.0"],
            image_size_in_bytes=100 * 1024 * 1024
        )
        assert image.is_tagged is True
        assert image.is_untagged is False
        assert pytest.approx(image.size_mb, rel=0.01) == 100.0

    def test_image_untagged(self):
        """Testa imagem sem tags."""
        image = ECRImage(
            repository_name="my-app",
            image_digest="sha256:xyz789",
            image_size_in_bytes=50 * 1024 * 1024
        )
        assert image.is_tagged is False
        assert image.is_untagged is True

    def test_image_size_gb(self):
        """Testa cálculo de tamanho em GB."""
        image = ECRImage(
            repository_name="large-app",
            image_size_in_bytes=2 * 1024 ** 3
        )
        assert pytest.approx(image.size_gb, rel=0.01) == 2.0

    def test_image_monthly_cost(self):
        """Testa cálculo de custo mensal."""
        image = ECRImage(
            repository_name="app",
            image_size_in_bytes=10 * 1024 ** 3
        )
        assert pytest.approx(image.estimated_monthly_cost, rel=0.01) == 1.0

    def test_image_vulnerabilities(self):
        """Testa detecção de vulnerabilidades."""
        image = ECRImage(
            repository_name="vulnerable-app",
            image_scan_findings_summary={
                "findingSeverityCounts": {
                    "CRITICAL": 2,
                    "HIGH": 5,
                    "MEDIUM": 10
                }
            }
        )
        assert image.has_vulnerabilities is True
        assert image.critical_vulnerabilities == 2
        assert image.high_vulnerabilities == 5

    def test_image_no_vulnerabilities(self):
        """Testa imagem sem vulnerabilidades."""
        image = ECRImage(
            repository_name="clean-app"
        )
        assert image.has_vulnerabilities is False
        assert image.critical_vulnerabilities == 0

    def test_image_to_dict(self):
        """Testa conversão para dicionário."""
        image = ECRImage(
            repository_name="my-app",
            image_tags=["latest"]
        )
        result = image.to_dict()
        assert result["repository_name"] == "my-app"
        assert result["is_tagged"] is True


class TestECRLifecyclePolicyDataclass:
    """Testes para ECRLifecyclePolicy dataclass."""

    def test_lifecycle_with_policy(self):
        """Testa lifecycle com política."""
        policy = ECRLifecyclePolicy(
            repository_name="my-app",
            lifecycle_policy_text='{"rules":[{"rulePriority":1},{"rulePriority":2}]}'
        )
        assert policy.has_policy is True
        assert policy.rules_count == 2

    def test_lifecycle_without_policy(self):
        """Testa lifecycle sem política."""
        policy = ECRLifecyclePolicy(
            repository_name="my-app"
        )
        assert policy.has_policy is False
        assert policy.rules_count == 0

    def test_lifecycle_to_dict(self):
        """Testa conversão para dicionário."""
        policy = ECRLifecyclePolicy(
            repository_name="my-app",
            lifecycle_policy_text='{"rules":[]}'
        )
        result = policy.to_dict()
        assert result["has_policy"] is True


class TestECRService:
    """Testes para ECRService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = ECRService(mock_factory)
        assert service._client_factory == mock_factory
        assert service._ecr_client is None

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_ecr = MagicMock()
        mock_ecr.describe_repositories.return_value = {"repositories": []}
        mock_factory.get_client.return_value = mock_ecr

        service = ECRService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "ecr"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_ecr = MagicMock()
        
        mock_ecr.get_paginator.return_value.paginate.return_value = [{
            "repositories": [{
                "repositoryName": "test-repo",
                "repositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/test-repo",
                "imageScanningConfiguration": {"scanOnPush": True}
            }]
        }]
        
        mock_factory.get_client.return_value = mock_ecr
        service = ECRService(mock_factory)
        
        with patch.object(service, 'get_images', return_value=[]):
            result = service.get_resources()
        
        assert "repositories" in result
        assert "summary" in result
        assert result["summary"]["total_repositories"] == 1

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_ecr = MagicMock()
        
        mock_ecr.get_paginator.return_value.paginate.return_value = [{
            "repositories": []
        }]
        
        mock_factory.get_client.return_value = mock_ecr
        service = ECRService(mock_factory)
        
        result = service.get_metrics()
        
        assert "repositories_count" in result
        assert "images_count" in result

    def test_service_get_recommendations(self):
        """Testa get_recommendations."""
        mock_factory = MagicMock()
        mock_ecr = MagicMock()
        
        mock_ecr.get_paginator.return_value.paginate.return_value = [{
            "repositories": [{
                "repositoryName": "test-repo",
                "imageScanningConfiguration": {"scanOnPush": False}
            }]
        }]
        
        mock_factory.get_client.return_value = mock_ecr
        service = ECRService(mock_factory)
        
        with patch.object(service, 'get_images', return_value=[]):
            result = service.get_recommendations()
        
        assert isinstance(result, list)


class TestAppRunnerServiceDataclass:
    """Testes para AppRunnerService dataclass."""

    def test_service_basic(self):
        """Testa criação básica de serviço."""
        svc = AppRunnerService(
            service_arn="arn:aws:apprunner:us-east-1:123456789012:service/my-service/id",
            service_name="my-service",
            status="RUNNING"
        )
        assert svc.service_name == "my-service"
        assert svc.is_running is True
        assert svc.is_paused is False

    def test_service_paused(self):
        """Testa serviço pausado."""
        svc = AppRunnerService(
            service_arn="arn",
            status="PAUSED"
        )
        assert svc.is_running is False
        assert svc.is_paused is True

    def test_service_instance_config(self):
        """Testa configuração de instância."""
        svc = AppRunnerService(
            service_arn="arn",
            instance_configuration={
                "Cpu": "2048",
                "Memory": "4096"
            }
        )
        assert svc.cpu == "2048"
        assert svc.memory == "4096"
        assert pytest.approx(svc.cpu_vcpu, rel=0.01) == 2.0
        assert pytest.approx(svc.memory_gb, rel=0.01) == 4.0

    def test_service_auto_scaling(self):
        """Testa configuração de auto scaling."""
        svc = AppRunnerService(
            service_arn="arn",
            auto_scaling_configuration_summary={
                "MinSize": 2,
                "MaxSize": 10
            }
        )
        assert svc.min_instances == 2
        assert svc.max_instances == 10

    def test_service_source_ecr(self):
        """Testa serviço usando ECR."""
        svc = AppRunnerService(
            service_arn="arn",
            source_configuration={
                "ImageRepository": {
                    "ImageRepositoryType": "ECR"
                }
            }
        )
        assert svc.uses_ecr is True
        assert svc.uses_github is False

    def test_service_source_github(self):
        """Testa serviço usando GitHub."""
        svc = AppRunnerService(
            service_arn="arn",
            source_configuration={
                "CodeRepository": {
                    "RepositoryUrl": "https://github.com/user/repo"
                }
            }
        )
        assert svc.uses_github is True

    def test_service_vpc_connector(self):
        """Testa serviço com VPC connector."""
        svc = AppRunnerService(
            service_arn="arn",
            network_configuration={
                "EgressConfiguration": {
                    "EgressType": "VPC"
                }
            }
        )
        assert svc.has_vpc_connector is True

    def test_service_cost_estimation(self):
        """Testa estimativa de custo."""
        svc = AppRunnerService(
            service_arn="arn",
            instance_configuration={
                "Cpu": "1024",
                "Memory": "2048"
            },
            auto_scaling_configuration_summary={
                "MinSize": 1
            }
        )
        assert svc.estimated_hourly_cost > 0
        assert svc.estimated_monthly_cost > 0

    def test_service_to_dict(self):
        """Testa conversão para dicionário."""
        svc = AppRunnerService(
            service_arn="arn",
            service_name="my-service",
            status="RUNNING"
        )
        result = svc.to_dict()
        assert result["service_name"] == "my-service"
        assert result["is_running"] is True


class TestAppRunnerAutoScalingConfigDataclass:
    """Testes para AppRunnerAutoScalingConfiguration dataclass."""

    def test_config_basic(self):
        """Testa configuração básica."""
        config = AppRunnerAutoScalingConfiguration(
            auto_scaling_configuration_arn="arn",
            auto_scaling_configuration_name="default",
            status="ACTIVE"
        )
        assert config.is_active is True
        assert config.is_inactive is False

    def test_config_can_scale_to_zero(self):
        """Testa configuração com scale to zero."""
        config = AppRunnerAutoScalingConfiguration(
            auto_scaling_configuration_arn="arn",
            min_size=0
        )
        assert config.can_scale_to_zero is True

    def test_config_cannot_scale_to_zero(self):
        """Testa configuração sem scale to zero."""
        config = AppRunnerAutoScalingConfiguration(
            auto_scaling_configuration_arn="arn",
            min_size=1
        )
        assert config.can_scale_to_zero is False

    def test_config_to_dict(self):
        """Testa conversão para dicionário."""
        config = AppRunnerAutoScalingConfiguration(
            auto_scaling_configuration_arn="arn",
            auto_scaling_configuration_name="test"
        )
        result = config.to_dict()
        assert result["is_active"] is True


class TestAppRunnerVpcConnectorDataclass:
    """Testes para AppRunnerVpcConnector dataclass."""

    def test_connector_basic(self):
        """Testa conector básico."""
        connector = AppRunnerVpcConnector(
            vpc_connector_arn="arn",
            vpc_connector_name="my-connector",
            subnets=["subnet-1", "subnet-2"],
            security_groups=["sg-1"]
        )
        assert connector.is_active is True
        assert connector.subnets_count == 2
        assert connector.security_groups_count == 1

    def test_connector_to_dict(self):
        """Testa conversão para dicionário."""
        connector = AppRunnerVpcConnector(
            vpc_connector_arn="arn",
            vpc_connector_name="test"
        )
        result = connector.to_dict()
        assert result["vpc_connector_name"] == "test"


class TestAppRunnerServiceManager:
    """Testes para AppRunnerServiceManager."""

    def test_manager_init(self):
        """Testa inicialização do manager."""
        mock_factory = MagicMock()
        manager = AppRunnerServiceManager(mock_factory)
        assert manager._client_factory == mock_factory
        assert manager._apprunner_client is None

    def test_manager_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_apprunner = MagicMock()
        mock_apprunner.list_services.return_value = {"ServiceSummaryList": []}
        mock_factory.get_client.return_value = mock_apprunner

        manager = AppRunnerServiceManager(mock_factory)
        result = manager.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "apprunner"

    def test_manager_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_apprunner = MagicMock()
        
        mock_apprunner.get_paginator.return_value.paginate.return_value = [{
            "ServiceSummaryList": [],
            "AutoScalingConfigurationSummaryList": [],
            "VpcConnectors": []
        }]
        
        mock_factory.get_client.return_value = mock_apprunner
        manager = AppRunnerServiceManager(mock_factory)
        
        result = manager.get_resources()
        
        assert "services" in result
        assert "summary" in result

    def test_manager_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_apprunner = MagicMock()
        
        mock_apprunner.get_paginator.return_value.paginate.return_value = [{
            "ServiceSummaryList": [],
            "AutoScalingConfigurationSummaryList": [],
            "VpcConnectors": []
        }]
        
        mock_factory.get_client.return_value = mock_apprunner
        manager = AppRunnerServiceManager(mock_factory)
        
        result = manager.get_metrics()
        
        assert "services_count" in result

    def test_manager_get_recommendations(self):
        """Testa get_recommendations."""
        mock_factory = MagicMock()
        mock_apprunner = MagicMock()
        
        mock_apprunner.get_paginator.return_value.paginate.return_value = [{
            "ServiceSummaryList": []
        }]
        
        mock_factory.get_client.return_value = mock_apprunner
        manager = AppRunnerServiceManager(mock_factory)
        
        result = manager.get_recommendations()
        
        assert isinstance(result, list)


class TestBeanstalkApplicationDataclass:
    """Testes para BeanstalkApplication dataclass."""

    def test_application_basic(self):
        """Testa criação básica de aplicação."""
        app = BeanstalkApplication(
            application_name="my-app",
            versions=["v1", "v2", "v3"],
            configuration_templates=["prod", "dev"]
        )
        assert app.versions_count == 3
        assert app.templates_count == 2
        assert app.has_lifecycle_policy is False

    def test_application_with_lifecycle(self):
        """Testa aplicação com lifecycle policy."""
        app = BeanstalkApplication(
            application_name="my-app",
            resource_lifecycle_config={
                "ServiceRole": "arn:aws:iam::123456789012:role/aws-elasticbeanstalk-service-role"
            }
        )
        assert app.has_lifecycle_policy is True

    def test_application_to_dict(self):
        """Testa conversão para dicionário."""
        app = BeanstalkApplication(
            application_name="test-app"
        )
        result = app.to_dict()
        assert result["application_name"] == "test-app"


class TestBeanstalkEnvironmentDataclass:
    """Testes para BeanstalkEnvironment dataclass."""

    def test_environment_basic(self):
        """Testa criação básica de ambiente."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            environment_name="my-env",
            status="Ready",
            health="Green"
        )
        assert env.is_ready is True
        assert env.is_healthy is True
        assert env.has_warnings is False
        assert env.has_errors is False

    def test_environment_updating(self):
        """Testa ambiente atualizando."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            status="Updating"
        )
        assert env.is_updating is True
        assert env.is_ready is False

    def test_environment_unhealthy(self):
        """Testa ambiente com problemas."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            health="Yellow"
        )
        assert env.has_warnings is True
        assert env.is_healthy is False

    def test_environment_error(self):
        """Testa ambiente com erro."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            health="Red"
        )
        assert env.has_errors is True
        assert env.is_healthy is False

    def test_environment_web_server(self):
        """Testa ambiente web server."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            tier={"Name": "WebServer", "Type": "Standard"}
        )
        assert env.is_web_server is True
        assert env.is_worker is False

    def test_environment_worker(self):
        """Testa ambiente worker."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            tier={"Name": "Worker", "Type": "Standard"}
        )
        assert env.is_worker is True
        assert env.is_web_server is False

    def test_environment_platform(self):
        """Testa extração de plataforma."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            solution_stack_name="64bit Amazon Linux 2 v5.4.0 running Python 3.8"
        )
        assert env.platform == "64bit"

    def test_environment_to_dict(self):
        """Testa conversão para dicionário."""
        env = BeanstalkEnvironment(
            environment_id="e-123",
            environment_name="test-env"
        )
        result = env.to_dict()
        assert result["environment_name"] == "test-env"


class TestBeanstalkApplicationVersionDataclass:
    """Testes para BeanstalkApplicationVersion dataclass."""

    def test_version_basic(self):
        """Testa versão básica."""
        ver = BeanstalkApplicationVersion(
            application_name="my-app",
            version_label="v1.0.0",
            status="Processed"
        )
        assert ver.is_processed is True
        assert ver.is_failed is False

    def test_version_processing(self):
        """Testa versão em processamento."""
        ver = BeanstalkApplicationVersion(
            application_name="my-app",
            version_label="v2.0.0",
            status="Processing"
        )
        assert ver.is_processing is True
        assert ver.is_processed is False

    def test_version_failed(self):
        """Testa versão com falha."""
        ver = BeanstalkApplicationVersion(
            application_name="my-app",
            version_label="v3.0.0",
            status="Failed"
        )
        assert ver.is_failed is True

    def test_version_source_bundle(self):
        """Testa source bundle."""
        ver = BeanstalkApplicationVersion(
            application_name="my-app",
            version_label="v1.0.0",
            source_bundle={
                "S3Bucket": "my-bucket",
                "S3Key": "my-app/v1.0.0.zip"
            }
        )
        assert ver.s3_bucket == "my-bucket"
        assert ver.s3_key == "my-app/v1.0.0.zip"

    def test_version_to_dict(self):
        """Testa conversão para dicionário."""
        ver = BeanstalkApplicationVersion(
            application_name="test-app",
            version_label="v1.0"
        )
        result = ver.to_dict()
        assert result["version_label"] == "v1.0"


class TestElasticBeanstalkService:
    """Testes para ElasticBeanstalkService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = ElasticBeanstalkService(mock_factory)
        assert service._client_factory == mock_factory
        assert service._eb_client is None

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_eb = MagicMock()
        mock_eb.describe_applications.return_value = {"Applications": []}
        mock_factory.get_client.return_value = mock_eb

        service = ElasticBeanstalkService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "elasticbeanstalk"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_eb = MagicMock()
        
        mock_eb.describe_applications.return_value = {"Applications": []}
        mock_eb.describe_environments.return_value = {"Environments": []}
        mock_eb.describe_application_versions.return_value = {"ApplicationVersions": []}
        
        mock_factory.get_client.return_value = mock_eb
        service = ElasticBeanstalkService(mock_factory)
        
        result = service.get_resources()
        
        assert "applications" in result
        assert "environments" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_eb = MagicMock()
        
        mock_eb.describe_applications.return_value = {"Applications": []}
        mock_eb.describe_environments.return_value = {"Environments": []}
        mock_eb.describe_application_versions.return_value = {"ApplicationVersions": []}
        
        mock_factory.get_client.return_value = mock_eb
        service = ElasticBeanstalkService(mock_factory)
        
        result = service.get_metrics()
        
        assert "applications_count" in result
        assert "environments_count" in result

    def test_service_get_recommendations(self):
        """Testa get_recommendations."""
        mock_factory = MagicMock()
        mock_eb = MagicMock()
        
        mock_eb.describe_applications.return_value = {"Applications": []}
        mock_eb.describe_environments.return_value = {"Environments": []}
        mock_eb.describe_application_versions.return_value = {"ApplicationVersions": []}
        
        mock_factory.get_client.return_value = mock_eb
        service = ElasticBeanstalkService(mock_factory)
        
        result = service.get_recommendations()
        
        assert isinstance(result, list)


class TestLightsailInstanceDataclass:
    """Testes para LightsailInstance dataclass."""

    def test_instance_basic(self):
        """Testa criação básica de instância."""
        inst = LightsailInstance(
            name="my-instance",
            bundle_id="micro_2_0",
            state={"name": "running"}
        )
        assert inst.name == "my-instance"
        assert inst.is_running is True
        assert inst.is_stopped is False

    def test_instance_stopped(self):
        """Testa instância parada."""
        inst = LightsailInstance(
            name="my-instance",
            state={"name": "stopped"}
        )
        assert inst.is_running is False
        assert inst.is_stopped is True

    def test_instance_hardware(self):
        """Testa hardware da instância."""
        inst = LightsailInstance(
            name="my-instance",
            hardware={
                "cpuCount": 2,
                "ramSizeInGb": 4.0,
                "disks": [{"sizeInGb": 80}]
            }
        )
        assert inst.cpu_count == 2
        assert inst.ram_size_gb == 4.0
        assert inst.disk_size_gb == 80

    def test_instance_location(self):
        """Testa localização da instância."""
        inst = LightsailInstance(
            name="my-instance",
            location={
                "availabilityZone": "us-east-1a",
                "regionName": "us-east-1"
            }
        )
        assert inst.availability_zone == "us-east-1a"
        assert inst.region == "us-east-1"

    def test_instance_static_ip(self):
        """Testa instância com IP estático."""
        inst = LightsailInstance(
            name="my-instance",
            is_static_ip=True
        )
        assert inst.has_static_ip is True

    def test_instance_ipv6(self):
        """Testa instância com IPv6."""
        inst = LightsailInstance(
            name="my-instance",
            ipv6_addresses=["2001:0db8:85a3:0000:0000:8a2e:0370:7334"]
        )
        assert inst.has_ipv6 is True

    def test_instance_transfer(self):
        """Testa transferência mensal."""
        inst = LightsailInstance(
            name="my-instance",
            networking={
                "monthlyTransfer": {"gbPerMonthAllocated": 2000}
            }
        )
        assert inst.monthly_transfer_gb == 2000

    def test_instance_cost_estimation(self):
        """Testa estimativa de custo."""
        inst = LightsailInstance(
            name="my-instance",
            bundle_id="medium_2_0"
        )
        assert inst.estimated_monthly_cost == 20.0

    def test_instance_to_dict(self):
        """Testa conversão para dicionário."""
        inst = LightsailInstance(
            name="test-instance"
        )
        result = inst.to_dict()
        assert result["name"] == "test-instance"


class TestLightsailDatabaseDataclass:
    """Testes para LightsailDatabase dataclass."""

    def test_database_basic(self):
        """Testa criação básica de database."""
        db = LightsailDatabase(
            name="my-db",
            engine="mysql",
            engine_version="8.0",
            state="available"
        )
        assert db.name == "my-db"
        assert db.is_available is True
        assert db.is_mysql is True
        assert db.is_postgres is False

    def test_database_postgres(self):
        """Testa database PostgreSQL."""
        db = LightsailDatabase(
            name="my-db",
            engine="postgres",
            engine_version="14"
        )
        assert db.is_postgres is True
        assert db.is_mysql is False

    def test_database_hardware(self):
        """Testa hardware do database."""
        db = LightsailDatabase(
            name="my-db",
            hardware={
                "cpuCount": 1,
                "ramSizeInGb": 2.0,
                "diskSizeInGb": 40
            }
        )
        assert db.cpu_count == 1
        assert db.ram_size_gb == 2.0
        assert db.disk_size_gb == 40

    def test_database_backup(self):
        """Testa configuração de backup."""
        db = LightsailDatabase(
            name="my-db",
            backup_retention_enabled=True
        )
        assert db.has_backup_enabled is True

    def test_database_public(self):
        """Testa database público."""
        db = LightsailDatabase(
            name="my-db",
            publicly_accessible=True
        )
        assert db.is_public is True

    def test_database_endpoint(self):
        """Testa endpoint do database."""
        db = LightsailDatabase(
            name="my-db",
            master_endpoint={
                "address": "my-db.123456789012.us-east-1.rds.amazonaws.com",
                "port": 3306
            }
        )
        assert db.endpoint_address == "my-db.123456789012.us-east-1.rds.amazonaws.com"
        assert db.endpoint_port == 3306

    def test_database_cost_estimation(self):
        """Testa estimativa de custo."""
        db = LightsailDatabase(
            name="my-db",
            relational_database_bundle_id="small_2_0"
        )
        assert db.estimated_monthly_cost == 30.0

    def test_database_to_dict(self):
        """Testa conversão para dicionário."""
        db = LightsailDatabase(
            name="test-db"
        )
        result = db.to_dict()
        assert result["name"] == "test-db"


class TestLightsailContainerDataclass:
    """Testes para LightsailContainer dataclass."""

    def test_container_basic(self):
        """Testa criação básica de container."""
        container = LightsailContainer(
            container_service_name="my-container",
            power="micro",
            scale=2,
            state="RUNNING"
        )
        assert container.container_service_name == "my-container"
        assert container.is_running is True
        assert container.nodes_count == 2

    def test_container_disabled(self):
        """Testa container desabilitado."""
        container = LightsailContainer(
            container_service_name="my-container",
            is_disabled=True
        )
        assert container.is_disabled_state is True

    def test_container_with_deployment(self):
        """Testa container com deployment."""
        container = LightsailContainer(
            container_service_name="my-container",
            current_deployment={
                "version": 1,
                "state": "ACTIVE"
            }
        )
        assert container.has_deployment is True

    def test_container_custom_domains(self):
        """Testa container com domínios customizados."""
        container = LightsailContainer(
            container_service_name="my-container",
            public_domain_names={
                "default": ["example.com"]
            }
        )
        assert container.has_custom_domains is True

    def test_container_cost_estimation(self):
        """Testa estimativa de custo."""
        container = LightsailContainer(
            container_service_name="my-container",
            power="small",
            scale=2
        )
        assert container.estimated_monthly_cost == 50.0

    def test_container_to_dict(self):
        """Testa conversão para dicionário."""
        container = LightsailContainer(
            container_service_name="test-container"
        )
        result = container.to_dict()
        assert result["container_service_name"] == "test-container"


class TestLightsailService:
    """Testes para LightsailService."""

    def test_service_init(self):
        """Testa inicialização do serviço."""
        mock_factory = MagicMock()
        service = LightsailService(mock_factory)
        assert service._client_factory == mock_factory
        assert service._lightsail_client is None

    def test_service_health_check_healthy(self):
        """Testa health check saudável."""
        mock_factory = MagicMock()
        mock_lightsail = MagicMock()
        mock_lightsail.get_instances.return_value = {"instances": []}
        mock_factory.get_client.return_value = mock_lightsail

        service = LightsailService(mock_factory)
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "lightsail"

    def test_service_get_resources(self):
        """Testa get_resources."""
        mock_factory = MagicMock()
        mock_lightsail = MagicMock()
        
        mock_lightsail.get_instances.return_value = {"instances": []}
        mock_lightsail.get_relational_databases.return_value = {"relationalDatabases": []}
        mock_lightsail.get_container_services.return_value = {"containerServices": []}
        
        mock_factory.get_client.return_value = mock_lightsail
        service = LightsailService(mock_factory)
        
        result = service.get_resources()
        
        assert "instances" in result
        assert "databases" in result
        assert "container_services" in result
        assert "summary" in result

    def test_service_get_metrics(self):
        """Testa get_metrics."""
        mock_factory = MagicMock()
        mock_lightsail = MagicMock()
        
        mock_lightsail.get_instances.return_value = {"instances": []}
        mock_lightsail.get_relational_databases.return_value = {"relationalDatabases": []}
        mock_lightsail.get_container_services.return_value = {"containerServices": []}
        
        mock_factory.get_client.return_value = mock_lightsail
        service = LightsailService(mock_factory)
        
        result = service.get_metrics()
        
        assert "instances_count" in result
        assert "databases_count" in result
        assert "containers_count" in result

    def test_service_get_recommendations(self):
        """Testa get_recommendations."""
        mock_factory = MagicMock()
        mock_lightsail = MagicMock()
        
        mock_lightsail.get_instances.return_value = {"instances": []}
        mock_lightsail.get_relational_databases.return_value = {"relationalDatabases": []}
        mock_lightsail.get_container_services.return_value = {"containerServices": []}
        
        mock_factory.get_client.return_value = mock_lightsail
        service = LightsailService(mock_factory)
        
        result = service.get_recommendations()
        
        assert isinstance(result, list)


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""

    def test_service_factory_get_ecr_service(self):
        """Testa obtenção do ECRService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_ecr_service()
        
        assert isinstance(service, ECRService)

    def test_service_factory_get_apprunner_service(self):
        """Testa obtenção do AppRunnerServiceManager via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_apprunner_service()
        
        assert isinstance(service, AppRunnerServiceManager)

    def test_service_factory_get_elasticbeanstalk_service(self):
        """Testa obtenção do ElasticBeanstalkService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_elasticbeanstalk_service()
        
        assert isinstance(service, ElasticBeanstalkService)

    def test_service_factory_get_lightsail_service(self):
        """Testa obtenção do LightsailService via factory."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        service = factory.get_lightsail_service()
        
        assert isinstance(service, LightsailService)

    def test_service_factory_get_all_services_includes_container_app(self):
        """Testa que get_all_services inclui serviços Container & App."""
        mock_client_factory = MagicMock()
        factory = ServiceFactory(mock_client_factory)
        
        services = factory.get_all_services()
        
        assert 'ecr' in services
        assert 'apprunner' in services
        assert 'elasticbeanstalk' in services
        assert 'lightsail' in services
