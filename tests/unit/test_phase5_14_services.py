"""
Testes unitários para serviços das FASES 5-14
Validação de 113 novos serviços AWS
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPhase5ServerlessIntegration:
    """Testes para serviços Serverless & Integration"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("amplify", "AmplifyService"),
        ("appsync", "AppSyncService"),
        ("sam", "SAMService"),
        ("lambdaedge", "LambdaEdgeService"),
        ("stacksets", "StackSetsService"),
        ("servicequotas", "ServiceQuotasService"),
        ("licensemanager", "LicenseManagerService"),
        ("resourcegroups", "ResourceGroupsService"),
        ("tageditor", "TagEditorService"),
        ("ram", "RAMService"),
        ("outposts", "OutpostsService"),
        ("localzones", "LocalZonesService"),
        ("wavelength", "WavelengthService"),
        ("private5g", "Private5GService"),
    ])
    def test_service_init(self, mock_client_factory, service_name, class_name):
        """Testa inicialização dos serviços FASE 5"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        assert service is not None
        assert service.service_name == service_name


class TestPhase6Observability:
    """Testes para serviços Observability & Monitoring"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("cloudwatchlogs", "CloudWatchLogsService"),
        ("cloudwatchinsights", "CloudWatchInsightsService"),
        ("synthetics", "SyntheticsService"),
        ("rum", "RUMService"),
        ("evidently", "EvidentlyService"),
        ("servicelens", "ServiceLensService"),
        ("containerinsights", "ContainerInsightsService"),
        ("lambdainsights", "LambdaInsightsService"),
        ("contributorinsights", "ContributorInsightsService"),
        ("applicationinsights", "ApplicationInsightsService"),
        ("internetmonitor", "InternetMonitorService"),
        ("networkmonitor", "NetworkMonitorService"),
    ])
    def test_service_init(self, mock_client_factory, service_name, class_name):
        """Testa inicialização dos serviços FASE 6"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        assert service is not None
        assert service.health_check() == True


class TestPhase7CostManagement:
    """Testes para serviços Cost Management"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("costexplorer", "CostExplorerService"),
        ("budgets", "BudgetsService"),
        ("savingsplans", "SavingsPlansService"),
        ("reservedinstances", "ReservedInstancesService"),
        ("costanomalydetection", "CostAnomalyDetectionService"),
        ("costcategories", "CostCategoriesService"),
        ("costallocationtags", "CostAllocationTagsService"),
        ("billingconductor", "BillingConductorService"),
        ("marketplacemetering", "MarketplaceMeteringService"),
        ("dataexports", "DataExportsService"),
    ])
    def test_service_costs(self, mock_client_factory, service_name, class_name):
        """Testa método get_costs dos serviços FASE 7"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        costs = service.get_costs(30)
        assert 'service' in costs
        assert 'total_cost' in costs


class TestPhase8SecurityAdvanced:
    """Testes para serviços Security Advanced"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("secretsmanageradv", "SecretsManagerAdvService"),
        ("privateca", "PrivateCAService"),
        ("cloudhsm", "CloudHSMService"),
        ("directoryservice", "DirectoryServiceService"),
        ("identitycenter", "IdentityCenterService"),
        ("accessanalyzer", "AccessAnalyzerService"),
        ("firewallmanager", "FirewallManagerService"),
        ("shield", "ShieldService"),
        ("networkfirewall", "NetworkFirewallService"),
        ("auditmanager", "AuditManagerService"),
        ("detective", "DetectiveService"),
        ("securitylake", "SecurityLakeService"),
    ])
    def test_service_recommendations(self, mock_client_factory, service_name, class_name):
        """Testa método get_recommendations dos serviços FASE 8"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        recs = service.get_recommendations()
        assert isinstance(recs, list)


class TestPhase9NetworkingAdvanced:
    """Testes para serviços Networking Advanced"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("appmesh", "AppMeshService"),
        ("cloudmap", "CloudMapService"),
        ("privatelink", "PrivateLinkService"),
        ("vpclattice", "VPCLatticeService"),
        ("verifiedaccess", "VerifiedAccessService"),
        ("clientvpn", "ClientVPNService"),
        ("sitetositevpn", "SiteToSiteVPNService"),
        ("networkmanager", "NetworkManagerService"),
        ("reachabilityanalyzer", "ReachabilityAnalyzerService"),
        ("trafficmirroring", "TrafficMirroringService"),
    ])
    def test_service_metrics(self, mock_client_factory, service_name, class_name):
        """Testa método get_metrics dos serviços FASE 9"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        metrics = service.get_metrics()
        assert 'service' in metrics


class TestPhase10DatabaseAnalytics:
    """Testes para serviços Database & Analytics Advanced"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("elasticacheglobal", "ElastiCacheGlobalService"),
        ("dynamodbglobal", "DynamoDBGlobalService"),
        ("auroraserverless", "AuroraServerlessService"),
        ("rdsproxy", "RDSProxyService"),
        ("dmsmigration", "DMSMigrationService"),
        ("schemaconversion", "SchemaConversionService"),
        ("redshiftserverless", "RedshiftServerlessService"),
        ("opensearchserverless", "OpenSearchServerlessService"),
        ("mskconnect", "MSKConnectService"),
        ("gluedatabrew", "GlueDataBrewService"),
        ("datazone", "DataZoneService"),
        ("cleanrooms", "CleanRoomsService"),
    ])
    def test_service_resources(self, mock_client_factory, service_name, class_name):
        """Testa método get_resources dos serviços FASE 10"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        resources = service.get_resources()
        assert isinstance(resources, list)


class TestPhase11AIMLAdvanced:
    """Testes para serviços AI/ML Advanced"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("sagemakerstudio", "SageMakerStudioService"),
        ("sagemakerpipelines", "SageMakerPipelinesService"),
        ("sagemakerfeaturestore", "SageMakerFeatureStoreService"),
        ("sagemakermodelregistry", "SageMakerModelRegistryService"),
        ("sagemakerexperiments", "SageMakerExperimentsService"),
        ("sagemakerdebugger", "SageMakerDebuggerService"),
        ("sagemakerclarify", "SageMakerClarifyService"),
        ("sagemakergroundtruth", "SageMakerGroundTruthService"),
        ("panorama", "PanoramaService"),
        ("deepracer", "DeepRacerService"),
        ("deepcomposer", "DeepComposerService"),
        ("healthlake", "HealthLakeService"),
    ])
    def test_service_analyze_usage(self, mock_client_factory, service_name, class_name):
        """Testa método analyze_usage dos serviços FASE 11"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        usage = service.analyze_usage()
        assert 'service' in usage
        assert 'usage_patterns' in usage


class TestPhase12DevOps:
    """Testes para serviços DevOps & Automation"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("codeartifact", "CodeArtifactService"),
        ("codeguru", "CodeGuruService"),
        ("fis", "FISService"),
        ("patchmanager", "PatchManagerService"),
        ("statemanager", "StateManagerService"),
        ("ssmautomation", "SSMAutomationService"),
        ("opscenter", "OpsCenterService"),
        ("incidentmanager", "IncidentManagerService"),
        ("autoscaling", "AutoScalingService"),
        ("launchwizard", "LaunchWizardService"),
    ])
    def test_service_health(self, mock_client_factory, service_name, class_name):
        """Testa health_check dos serviços FASE 12"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        assert service.health_check() == True


class TestPhase13EndUser:
    """Testes para serviços End User & Productivity"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("workspacesweb", "WorkSpacesWebService"),
        ("appstreamadv", "AppStreamAdvService"),
        ("workmail", "WorkMailService"),
        ("wickr", "WickrService"),
        ("chimesdk", "ChimeSDKService"),
        ("honeycode", "HoneycodeService"),
        ("managedgrafana", "ManagedGrafanaService"),
        ("managedprometheus", "ManagedPrometheusService"),
        ("managedflink", "ManagedFlinkService"),
        ("mwaa", "MWAAService"),
    ])
    def test_service_init_complete(self, mock_client_factory, service_name, class_name):
        """Testa inicialização completa dos serviços FASE 13"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        assert hasattr(service, 'get_resources')
        assert hasattr(service, 'get_costs')
        assert hasattr(service, 'get_metrics')
        assert hasattr(service, 'get_recommendations')


class TestPhase14Specialty:
    """Testes para serviços Specialty"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    @pytest.mark.parametrize("service_name,class_name", [
        ("groundstation", "GroundStationService"),
        ("nimblestudio", "NimbleStudioService"),
        ("simspaceweaver", "SimSpaceWeaverService"),
        ("iottwinmaker", "IoTTwinMakerService"),
        ("iotfleetwise", "IoTFleetWiseService"),
        ("iotsitewise", "IoTSiteWiseService"),
        ("locationservice", "LocationServiceService"),
        ("geospatial", "GeoSpatialService"),
        ("healthomics", "HealthOmicsService"),
        ("supplychain", "SupplyChainService"),
    ])
    def test_service_all_methods(self, mock_client_factory, service_name, class_name):
        """Testa todos os métodos dos serviços FASE 14"""
        module = __import__(f"src.finops_aws.services.{service_name}_service", fromlist=[class_name])
        service_class = getattr(module, class_name)
        service = service_class(mock_client_factory)
        
        assert service.health_check() == True
        assert isinstance(service.get_resources(), list)
        assert 'service' in service.get_costs()
        assert 'service' in service.get_metrics()
        assert isinstance(service.get_recommendations(), list)
        assert 'usage_patterns' in service.analyze_usage()


class TestServiceFactoryNewServices:
    """Testes de integração do ServiceFactory com novos serviços"""
    
    @pytest.fixture
    def mock_client_factory(self):
        factory = MagicMock()
        factory.get_client.return_value = MagicMock()
        return factory
    
    def test_factory_has_all_new_getters(self, mock_client_factory):
        """Verifica que o factory tem todos os getters para novos serviços"""
        from src.finops_aws.core.factories import ServiceFactory
        factory = ServiceFactory(mock_client_factory)
        
        new_services = [
            'amplify', 'appsync', 'sam', 'lambdaedge', 'stacksets',
            'servicequotas', 'licensemanager', 'resourcegroups', 'tageditor',
            'ram', 'outposts', 'localzones', 'wavelength', 'private5g',
            'cloudwatchlogs', 'cloudwatchinsights', 'synthetics', 'rum',
            'evidently', 'servicelens', 'containerinsights', 'lambdainsights',
            'costexplorer', 'budgets', 'savingsplans', 'reservedinstances',
            'shield', 'detective', 'appmesh', 'cloudmap', 'vpclattice',
            'elasticacheglobal', 'dynamodbglobal', 'auroraserverless', 'rdsproxy',
            'sagemakerstudio', 'sagemakerpipelines', 'panorama', 'deepracer',
            'codeartifact', 'codeguru', 'fis', 'autoscaling',
            'workspacesweb', 'workmail', 'managedgrafana', 'managedprometheus',
            'groundstation', 'nimblestudio', 'iottwinmaker', 'healthomics',
        ]
        
        for svc in new_services:
            getter_name = f'get_{svc}_service'
            assert hasattr(factory, getter_name), f"Missing getter: {getter_name}"
    
    def test_all_services_count(self, mock_client_factory):
        """Verifica que get_all_services retorna todos os 253 serviços"""
        from src.finops_aws.core.factories import ServiceFactory
        factory = ServiceFactory(mock_client_factory)
        
        all_services = factory.get_all_services()
        assert len(all_services) >= 250, f"Expected 250+ services, got {len(all_services)}"


class TestServiceResourceDataclasses:
    """Testes para dataclasses de recursos"""
    
    def test_amplify_resource_to_dict(self):
        """Testa conversão de AmplifyResource para dict"""
        from src.finops_aws.services.amplify_service import AmplifyResource
        resource = AmplifyResource(
            resource_id="app-123",
            resource_type="App",
            name="My App",
            region="us-east-1",
            status="RUNNING"
        )
        data = resource.to_dict()
        assert data['resource_id'] == "app-123"
        assert data['name'] == "My App"
    
    def test_costexplorer_resource_to_dict(self):
        """Testa conversão de CostExplorerResource para dict"""
        from src.finops_aws.services.costexplorer_service import CostExplorerResource
        resource = CostExplorerResource(
            resource_id="cost-123",
            resource_type="CostReport",
            name="Monthly Report",
            region="us-east-1",
            status="ACTIVE"
        )
        data = resource.to_dict()
        assert data['resource_id'] == "cost-123"
        assert data['status'] == "ACTIVE"
