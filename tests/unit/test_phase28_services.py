"""
Testes Unitários para FASE 2.8 - DevOps & CI/CD Services

Testa os serviços:
- CodeBuildService
- CodePipelineService
- CodeDeployService
- CodeCommitService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.finops_aws.services.codebuild_service import (
    CodeBuildService, BuildProject, BuildHistory, ReportGroup
)
from src.finops_aws.services.codepipeline_service import (
    CodePipelineService, Pipeline, PipelineExecution, Webhook
)
from src.finops_aws.services.codedeploy_service import (
    CodeDeployService, DeploymentApplication, DeploymentGroup, Deployment, DeploymentConfig
)
from src.finops_aws.services.codecommit_service import (
    CodeCommitService, Repository, Branch, PullRequest, ApprovalRule
)
from src.finops_aws.core.factories import ServiceFactory, AWSClientFactory


class TestBuildProject:
    """Testes para dataclass BuildProject"""
    
    def test_create_build_project(self):
        project = BuildProject(
            name='my-project',
            arn='arn:aws:codebuild:us-east-1:123456789012:project/my-project',
            compute_type='BUILD_GENERAL1_LARGE',
            environment_type='LINUX_CONTAINER',
            cache_type='S3'
        )
        
        assert project.name == 'my-project'
        assert project.is_large_compute
        assert project.has_cache
        assert not project.is_arm_based
    
    def test_gpu_project(self):
        project = BuildProject(
            name='gpu-project',
            compute_type='BUILD_GENERAL1_LARGE_GPU'
        )
        
        assert project.is_gpu_enabled
        assert project.is_large_compute
    
    def test_arm_project(self):
        project = BuildProject(
            name='arm-project',
            environment_type='ARM_CONTAINER',
            compute_type='BUILD_GENERAL1_SMALL'
        )
        
        assert project.is_arm_based
        assert project.is_small_compute
    
    def test_build_project_to_dict(self):
        project = BuildProject(
            name='test-project',
            compute_type='BUILD_GENERAL1_MEDIUM',
            timeout_in_minutes=120
        )
        
        result = project.to_dict()
        assert result['name'] == 'test-project'
        assert result['is_medium_compute'] is True
        assert result['timeout_hours'] == 2.0


class TestBuildHistory:
    """Testes para dataclass BuildHistory"""
    
    def test_create_build_history(self):
        history = BuildHistory(
            project_name='my-project',
            build_id='my-project:12345',
            build_number=42,
            build_status='SUCCEEDED',
            duration_seconds=300
        )
        
        assert history.is_successful
        assert not history.is_failed
        assert history.duration_minutes == 5.0
    
    def test_failed_build(self):
        history = BuildHistory(
            project_name='my-project',
            build_id='my-project:12346',
            build_status='FAILED'
        )
        
        assert history.is_failed
        assert not history.is_successful


class TestReportGroup:
    """Testes para dataclass ReportGroup"""
    
    def test_create_report_group(self):
        report = ReportGroup(
            name='test-reports',
            type='TEST',
            export_config_type='S3'
        )
        
        assert report.is_test_report
        assert report.exports_to_s3
    
    def test_code_coverage_report(self):
        report = ReportGroup(
            name='coverage-reports',
            type='CODE_COVERAGE'
        )
        
        assert report.is_code_coverage
        assert not report.is_test_report


class TestCodeBuildService:
    """Testes para CodeBuildService"""
    
    def test_service_name(self):
        mock_factory = Mock()
        service = CodeBuildService(mock_factory)
        assert service.service_name == "codebuild"
    
    def test_health_check(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_client.list_projects.return_value = {'projects': []}
        mock_factory.get_client.return_value = mock_client
        
        service = CodeBuildService(mock_factory)
        assert service.health_check() is True
    
    def test_get_projects_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'projects': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeBuildService(mock_factory)
        projects = service.get_projects()
        assert projects == []
    
    def test_get_resources(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'projects': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeBuildService(mock_factory)
        resources = service.get_resources()
        
        assert 'projects' in resources
        assert 'report_groups' in resources
        assert 'summary' in resources


class TestPipeline:
    """Testes para dataclass Pipeline"""
    
    def test_create_pipeline(self):
        pipeline = Pipeline(
            name='my-pipeline',
            pipeline_type='V2',
            execution_mode='PARALLEL',
            stages=[
                {'name': 'Source', 'actions': [{'name': 'S3Source'}]},
                {'name': 'Build', 'actions': [{'name': 'CodeBuild'}]},
                {'name': 'Deploy', 'actions': [{'name': 'ECS', 'actionTypeId': {'category': 'Deploy'}}]}
            ]
        )
        
        assert pipeline.is_v2_pipeline
        assert pipeline.uses_parallel_execution
        assert pipeline.stage_count == 3
        assert pipeline.action_count == 3
        assert pipeline.has_deploy_stage
    
    def test_v1_pipeline(self):
        pipeline = Pipeline(
            name='old-pipeline',
            pipeline_type='V1',
            execution_mode='SUPERSEDED'
        )
        
        assert not pipeline.is_v2_pipeline
        assert not pipeline.uses_parallel_execution
    
    def test_pipeline_with_approval(self):
        pipeline = Pipeline(
            name='approval-pipeline',
            stages=[
                {'name': 'Source', 'actions': [{'name': 'S3'}]},
                {'name': 'Approval', 'actions': [{'name': 'ManualApproval', 'actionTypeId': {'category': 'Approval'}}]}
            ]
        )
        
        assert pipeline.has_manual_approval


class TestPipelineExecution:
    """Testes para dataclass PipelineExecution"""
    
    def test_create_execution(self):
        execution = PipelineExecution(
            pipeline_name='my-pipeline',
            execution_id='exec-123',
            status='Succeeded',
            trigger_type='Webhook'
        )
        
        assert execution.is_successful
        assert execution.is_webhook_trigger
        assert not execution.is_manual_trigger
    
    def test_failed_execution(self):
        execution = PipelineExecution(
            pipeline_name='my-pipeline',
            execution_id='exec-124',
            status='Failed'
        )
        
        assert execution.is_failed
        assert not execution.is_successful


class TestCodePipelineService:
    """Testes para CodePipelineService"""
    
    def test_service_name(self):
        mock_factory = Mock()
        service = CodePipelineService(mock_factory)
        assert service.service_name == "codepipeline"
    
    def test_health_check(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_client.list_pipelines.return_value = {'pipelines': []}
        mock_factory.get_client.return_value = mock_client
        
        service = CodePipelineService(mock_factory)
        assert service.health_check() is True
    
    def test_get_pipelines_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'pipelines': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodePipelineService(mock_factory)
        pipelines = service.get_pipelines()
        assert pipelines == []
    
    def test_get_resources(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'pipelines': [], 'webhooks': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodePipelineService(mock_factory)
        resources = service.get_resources()
        
        assert 'pipelines' in resources
        assert 'webhooks' in resources
        assert 'summary' in resources


class TestDeploymentApplication:
    """Testes para dataclass DeploymentApplication"""
    
    def test_create_application(self):
        app = DeploymentApplication(
            name='my-app',
            compute_platform='Server'
        )
        
        assert app.is_ec2_server
        assert not app.is_lambda
        assert not app.is_ecs
    
    def test_lambda_application(self):
        app = DeploymentApplication(
            name='lambda-app',
            compute_platform='Lambda'
        )
        
        assert app.is_lambda
        assert not app.is_ec2_server
    
    def test_ecs_application(self):
        app = DeploymentApplication(
            name='ecs-app',
            compute_platform='ECS'
        )
        
        assert app.is_ecs


class TestDeploymentGroup:
    """Testes para dataclass DeploymentGroup"""
    
    def test_create_deployment_group(self):
        group = DeploymentGroup(
            name='my-group',
            application_name='my-app',
            deployment_style={'deploymentType': 'BLUE_GREEN', 'deploymentOption': 'WITH_TRAFFIC_CONTROL'},
            auto_rollback_configuration={'enabled': True},
            alarm_configuration={'enabled': True}
        )
        
        assert group.is_blue_green
        assert group.has_auto_rollback
        assert group.has_alarms
        assert group.uses_load_balancer
    
    def test_in_place_deployment(self):
        group = DeploymentGroup(
            name='in-place-group',
            application_name='my-app',
            deployment_style={'deploymentType': 'IN_PLACE'}
        )
        
        assert group.is_in_place
        assert not group.is_blue_green


class TestDeployment:
    """Testes para dataclass Deployment"""
    
    def test_create_deployment(self):
        deployment = Deployment(
            deployment_id='d-123',
            application_name='my-app',
            deployment_group_name='my-group',
            status='Succeeded',
            deployment_overview={'Succeeded': 5, 'Failed': 0}
        )
        
        assert deployment.is_successful
        assert deployment.instances_succeeded == 5
        assert deployment.instances_failed == 0
    
    def test_failed_deployment(self):
        deployment = Deployment(
            deployment_id='d-124',
            application_name='my-app',
            deployment_group_name='my-group',
            status='Failed',
            rollback_info={'rollbackDeploymentId': 'd-125'}
        )
        
        assert deployment.is_failed
        assert deployment.was_rolled_back


class TestCodeDeployService:
    """Testes para CodeDeployService"""
    
    def test_service_name(self):
        mock_factory = Mock()
        service = CodeDeployService(mock_factory)
        assert service.service_name == "codedeploy"
    
    def test_health_check(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_client.list_applications.return_value = {'applications': []}
        mock_factory.get_client.return_value = mock_client
        
        service = CodeDeployService(mock_factory)
        assert service.health_check() is True
    
    def test_get_applications_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'applications': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeDeployService(mock_factory)
        apps = service.get_applications()
        assert apps == []
    
    def test_get_resources(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'applications': [], 'deploymentConfigsList': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeDeployService(mock_factory)
        resources = service.get_resources()
        
        assert 'applications' in resources
        assert 'deployment_groups' in resources
        assert 'summary' in resources


class TestRepository:
    """Testes para dataclass Repository"""
    
    def test_create_repository(self):
        repo = Repository(
            name='my-repo',
            kms_key_id='arn:aws:kms:us-east-1:123456789012:key/12345',
            description='My repository'
        )
        
        assert repo.has_encryption
        assert repo.has_description
    
    def test_stale_repository(self):
        old_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        repo = Repository(
            name='old-repo',
            last_modified_date=old_date
        )
        
        assert repo.days_since_modified > 180
        assert repo.is_stale


class TestBranch:
    """Testes para dataclass Branch"""
    
    def test_create_branch(self):
        branch = Branch(
            name='main',
            repository_name='my-repo',
            commit_id='abc123'
        )
        
        assert branch.is_main_branch
        assert not branch.is_feature_branch
    
    def test_feature_branch(self):
        branch = Branch(
            name='feature/new-feature',
            repository_name='my-repo'
        )
        
        assert branch.is_feature_branch
        assert not branch.is_main_branch
    
    def test_release_branch(self):
        branch = Branch(
            name='release/v1.0',
            repository_name='my-repo'
        )
        
        assert branch.is_release_branch


class TestPullRequest:
    """Testes para dataclass PullRequest"""
    
    def test_create_pull_request(self):
        pr = PullRequest(
            pull_request_id='1',
            title='Add new feature',
            repository_name='my-repo',
            status='OPEN',
            source_branch='feature/new-feature',
            destination_branch='main'
        )
        
        assert pr.is_open
        assert not pr.is_merged
    
    def test_merged_pull_request(self):
        pr = PullRequest(
            pull_request_id='2',
            title='Fix bug',
            repository_name='my-repo',
            status='CLOSED',
            merge_metadata={'isMerged': True}
        )
        
        assert pr.is_closed
        assert pr.is_merged


class TestCodeCommitService:
    """Testes para CodeCommitService"""
    
    def test_service_name(self):
        mock_factory = Mock()
        service = CodeCommitService(mock_factory)
        assert service.service_name == "codecommit"
    
    def test_health_check(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_client.list_repositories.return_value = {'repositories': []}
        mock_factory.get_client.return_value = mock_client
        
        service = CodeCommitService(mock_factory)
        assert service.health_check() is True
    
    def test_get_repositories_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'repositories': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeCommitService(mock_factory)
        repos = service.get_repositories()
        assert repos == []
    
    def test_get_resources(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'repositories': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_client.list_approval_rule_templates.return_value = {'approvalRuleTemplateNames': []}
        mock_factory.get_client.return_value = mock_client
        
        service = CodeCommitService(mock_factory)
        resources = service.get_resources()
        
        assert 'repositories' in resources
        assert 'branches' in resources
        assert 'summary' in resources


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory"""
    
    def test_get_all_services_includes_new_services(self):
        AWSClientFactory._instance = None
        ServiceFactory._instance = None
        
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_client.list_projects.return_value = {'projects': []}
        mock_client.list_pipelines.return_value = {'pipelines': []}
        mock_client.list_applications.return_value = {'applications': []}
        mock_client.list_repositories.return_value = {'repositories': []}
        
        with patch('boto3.client', return_value=mock_client):
            factory = ServiceFactory()
            services = factory.get_all_services()
            
            assert 'codebuild' in services
            assert 'codepipeline' in services
            assert 'codedeploy' in services
            assert 'codecommit' in services
    
    def test_services_are_cached(self):
        AWSClientFactory._instance = None
        ServiceFactory._instance = None
        
        mock_client = Mock()
        
        with patch('boto3.client', return_value=mock_client):
            factory = ServiceFactory()
            
            service1 = factory.get_codebuild_service()
            service2 = factory.get_codebuild_service()
            
            assert service1 is service2


class TestRecommendations:
    """Testes para recomendações dos serviços"""
    
    def test_codebuild_recommendations_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'projects': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeBuildService(mock_factory)
        recommendations = service.get_recommendations()
        
        assert isinstance(recommendations, list)
    
    def test_codepipeline_recommendations_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'pipelines': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodePipelineService(mock_factory)
        recommendations = service.get_recommendations()
        
        assert isinstance(recommendations, list)
    
    def test_codedeploy_recommendations_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'applications': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_factory.get_client.return_value = mock_client
        
        service = CodeDeployService(mock_factory)
        recommendations = service.get_recommendations()
        
        assert isinstance(recommendations, list)
    
    def test_codecommit_recommendations_empty(self):
        mock_factory = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{'repositories': []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_client.list_approval_rule_templates.return_value = {'approvalRuleTemplateNames': []}
        mock_factory.get_client.return_value = mock_client
        
        service = CodeCommitService(mock_factory)
        recommendations = service.get_recommendations()
        
        assert isinstance(recommendations, list)


class TestWebhook:
    """Testes para dataclass Webhook"""
    
    def test_create_webhook(self):
        webhook = Webhook(
            name='my-webhook',
            pipeline_name='my-pipeline',
            authentication='GITHUB_HMAC',
            filters=[{'jsonPath': '$.ref', 'matchEquals': 'refs/heads/main'}]
        )
        
        assert webhook.is_github_webhook
        assert webhook.has_filters
    
    def test_webhook_to_dict(self):
        webhook = Webhook(
            name='test-webhook',
            pipeline_name='test-pipeline'
        )
        
        result = webhook.to_dict()
        assert result['name'] == 'test-webhook'
        assert result['pipeline_name'] == 'test-pipeline'


class TestDeploymentConfig:
    """Testes para dataclass DeploymentConfig"""
    
    def test_all_at_once_config(self):
        config = DeploymentConfig(
            name='CodeDeployDefault.AllAtOnce'
        )
        
        assert config.is_all_at_once
        assert not config.is_one_at_a_time
    
    def test_canary_config(self):
        config = DeploymentConfig(
            name='Canary10Percent5Minutes',
            traffic_routing_config={'type': 'TimeBasedCanary'}
        )
        
        assert config.is_canary
        assert not config.is_linear


class TestApprovalRule:
    """Testes para dataclass ApprovalRule"""
    
    def test_create_approval_rule(self):
        rule = ApprovalRule(
            name='require-two-approvers',
            rule_content={'minApprovalsCount': 2, 'approvalPoolMembers': ['user1', 'user2']}
        )
        
        assert rule.approvers_required == 2
        assert rule.has_pool_members
    
    def test_approval_rule_to_dict(self):
        rule = ApprovalRule(
            name='test-rule',
            rule_content={'minApprovalsCount': 1}
        )
        
        result = rule.to_dict()
        assert result['name'] == 'test-rule'
        assert result['approvers_required'] == 1
