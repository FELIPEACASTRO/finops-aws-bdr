# FinOps AWS - Apêndice: Catálogo Completo de Serviços AWS

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Compute & Serverless (25)](#2-compute--serverless)
3. [Storage (15)](#3-storage)
4. [Database (25)](#4-database)
5. [Networking (20)](#5-networking)
6. [Security & Identity (22)](#6-security--identity)
7. [AI/ML (26)](#7-aiml)
8. [Analytics (20)](#8-analytics)
9. [Developer Tools (15)](#9-developer-tools)
10. [Management & Governance (17)](#10-management--governance)
11. [Cost Management (10)](#11-cost-management)
12. [Observability (15)](#12-observability)
13. [IoT & Edge (10)](#13-iot--edge)
14. [Media (7)](#14-media)
15. [End User & Productivity (15)](#15-end-user--productivity)
16. [Specialty Services (11)](#16-specialty-services)
17. [Matriz de Capacidades](#17-matriz-de-capacidades)

---

## 1. Visão Geral

### 1.1 Cobertura Total: 253 Serviços AWS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COBERTURA DE SERVIÇOS AWS - 253 TOTAL                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CATEGORIA                         │ SERVIÇOS │ % DO TOTAL                 │
│  ─────────────────────────────────────────────────────────────────────     │
│  Compute & Serverless              │    25    │   9,9%   ████████████     │
│  AI/ML                             │    26    │  10,3%   █████████████    │
│  Database                          │    25    │   9,9%   ████████████     │
│  Security & Identity               │    22    │   8,7%   ███████████      │
│  Networking                        │    20    │   7,9%   ██████████       │
│  Analytics                         │    20    │   7,9%   ██████████       │
│  Management & Governance           │    17    │   6,7%   █████████        │
│  Storage                           │    15    │   5,9%   ████████         │
│  Developer Tools                   │    15    │   5,9%   ████████         │
│  End User & Productivity           │    15    │   5,9%   ████████         │
│  Observability                     │    15    │   5,9%   ████████         │
│  Specialty Services                │    11    │   4,3%   ██████           │
│  Cost Management                   │    10    │   4,0%   █████            │
│  IoT & Edge                        │    10    │   4,0%   █████            │
│  Media                             │     7    │   2,8%   ████             │
│  ─────────────────────────────────────────────────────────────────────     │
│  TOTAL                             │   253    │  100%                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Métodos Implementados por Serviço

Cada serviço implementa no mínimo 5 métodos:

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `health_check()` | Verifica disponibilidade do serviço | Dict com status |
| `get_resources()` | Lista todos os recursos | List ou Dict |
| `analyze_usage()` | Analisa padrões de uso | Dict com métricas |
| `get_metrics()` | Coleta métricas CloudWatch | Dict com dados |
| `get_recommendations()` | Gera recomendações de otimização | List de recomendações |

---

## 2. Compute & Serverless

**Total: 25 serviços**

| # | Serviço | Classe | Descrição | Economia Típica |
|---|---------|--------|-----------|-----------------|
| 1 | Amazon EC2 | `EC2Service` | Elastic Compute Cloud | 25-40% |
| 2 | EC2 FinOps | `EC2FinOpsService` | Análise avançada EC2 | 30-50% |
| 3 | EC2 Spot | `EC2SpotService` | Instâncias Spot | 60-90% |
| 4 | EC2 Reserved | `EC2ReservedService` | Reserved Instances | 30-60% |
| 5 | AWS Lambda | `LambdaService` | Functions serverless | 15-30% |
| 6 | Lambda FinOps | `LambdaFinOpsService` | Análise avançada Lambda | 20-40% |
| 7 | Lambda@Edge | `LambdaEdgeService` | Edge computing | 10-20% |
| 8 | AWS Batch | `BatchService` | Batch processing | 40-60% |
| 9 | Amazon Lightsail | `LightsailService` | VPS simplificado | 10-20% |
| 10 | AWS App Runner | `AppRunnerService` | Container deploy | 15-25% |
| 11 | Elastic Beanstalk | `ElasticBeanstalkService` | PaaS | 20-30% |
| 12 | AWS SAM | `SAMService` | Serverless Application Model | 15-25% |
| 13 | AWS Outposts | `OutpostsService` | On-premises AWS | 15-25% |
| 14 | Local Zones | `LocalZonesService` | Extensão de regiões | 10-20% |
| 15 | AWS Wavelength | `WavelengthService` | 5G edge computing | 10-20% |
| 16 | Private 5G | `Private5GService` | Rede 5G privada | 10-20% |
| 17 | Auto Scaling | `AutoScalingService` | Escalabilidade | 20-35% |
| 18 | Amazon ECS | `ECSContainerService` | Container orchestration | 20-35% |
| 19 | Amazon EKS | `EKSService` | Kubernetes gerenciado | 30-50% |
| 20 | Amazon ECR | `ECRService` | Container registry | 10-20% |
| 21 | AWS Fargate | `FargateService` | Serverless containers | 20-30% |
| 22 | Step Functions | `StepFunctionsService` | Workflow orchestration | 10-20% |
| 23 | EventBridge | `EventBridgeService` | Event bus | 10-15% |
| 24 | AWS Amplify | `AmplifyService` | Full-stack development | 15-25% |
| 25 | AWS Proton | `ProtonService` | Container/serverless deploy | 15-25% |

---

## 3. Storage

**Total: 15 serviços**

| # | Serviço | Classe | Descrição | Economia Típica |
|---|---------|--------|-----------|-----------------|
| 1 | Amazon S3 | `S3Service` | Object storage | 40-70% |
| 2 | Amazon EBS | `EBSService` | Block storage | 20-40% |
| 3 | Amazon EFS | `EFSService` | File storage | 30-50% |
| 4 | Amazon FSx | `FSxService` | File systems gerenciados | 20-35% |
| 5 | Storage Gateway | `StorageGatewayService` | Hybrid storage | 20-30% |
| 6 | S3 Outposts | `S3OutpostsService` | S3 on-premises | 15-25% |
| 7 | AWS Backup | `BackupService` | Backup centralizado | 15-25% |
| 8 | AWS DataSync | `DataSyncService` | Data transfer | 15-25% |
| 9 | DataSync Enhanced | `DataSyncEnhancedService` | Análise avançada | 20-30% |
| 10 | Snow Family | `SnowService` | Edge storage/compute | Por projeto |
| 11 | Transfer Family | `TransferFamilyService` | SFTP/FTPS | 15-25% |
| 12 | S3 Glacier | `S3GlacierService` | Archive storage | 60-80% |
| 13 | S3 Intelligent-Tiering | `S3IntelligentTieringService` | Auto tiering | 30-50% |
| 14 | EBS Snapshots | `EBSSnapshotsService` | Snapshot management | 20-40% |
| 15 | File Cache | `FileCacheService` | High-speed cache | 15-25% |

---

## 4. Database

**Total: 25 serviços**

| # | Serviço | Classe | Descrição | Economia Típica |
|---|---------|--------|-----------|-----------------|
| 1 | Amazon RDS | `RDSService` | Relational databases | 25-40% |
| 2 | RDS FinOps | `RDSFinOpsService` | Análise avançada RDS | 30-50% |
| 3 | Amazon Aurora | `AuroraService` | MySQL/PostgreSQL gerenciado | 20-35% |
| 4 | Aurora Serverless | `AuroraServerlessService` | Aurora auto-scaling | 30-50% |
| 5 | Amazon DynamoDB | `DynamoDBFinOpsService` | NoSQL serverless | 30-50% |
| 6 | DynamoDB Global | `DynamoDBGlobalService` | Global tables | 25-40% |
| 7 | DynamoDB Streams | `DynamoDBStreamsService` | Change data capture | 15-25% |
| 8 | Amazon ElastiCache | `ElastiCacheService` | In-memory cache | 25-35% |
| 9 | ElastiCache Global | `ElastiCacheGlobalService` | Global datastore | 25-35% |
| 10 | ElastiCache Serverless | `ElastiCacheServerlessService` | Serverless cache | 30-50% |
| 11 | Amazon MemoryDB | `MemoryDBService` | Redis-compatible | 25-35% |
| 12 | Amazon Redshift | `RedshiftService` | Data warehouse | 30-45% |
| 13 | Redshift Serverless | `RedshiftServerlessService` | Serverless analytics | 35-55% |
| 14 | Amazon DocumentDB | `DocumentDBService` | MongoDB-compatible | 20-30% |
| 15 | Amazon Neptune | `NeptuneService` | Graph database | 20-30% |
| 16 | Amazon Keyspaces | `KeyspacesService` | Cassandra-compatible | 25-40% |
| 17 | Amazon Timestream | `TimestreamService` | Time-series DB | 20-35% |
| 18 | Amazon QLDB | `QLDBService` | Ledger database | 20-30% |
| 19 | Amazon OpenSearch | `OpenSearchService` | Search/analytics | 25-40% |
| 20 | OpenSearch Serverless | `OpenSearchServerlessService` | Serverless search | 30-50% |
| 21 | RDS Proxy | `RDSProxyService` | Connection pooling | 15-25% |
| 22 | AWS DMS | `DMSService` | Database migration | 15-25% |
| 23 | DMS Migration | `DMSMigrationService` | Migration service | 15-25% |
| 24 | Schema Conversion | `SchemaConversionService` | Schema conversion | 15-25% |
| 25 | Database Insights | `DatabaseInsightsService` | Performance insights | 20-30% |

---

## 5. Networking

**Total: 20 serviços**

| # | Serviço | Classe | Descrição | Economia Típica |
|---|---------|--------|-----------|-----------------|
| 1 | Amazon VPC | `VPCService` | Virtual Private Cloud | 15-25% |
| 2 | VPC FinOps | `VPCFinOpsService` | Análise avançada VPC | 20-35% |
| 3 | Elastic Load Balancing | `ELBService` | Load balancers | 20-30% |
| 4 | ELB FinOps | `ELBFinOpsService` | Análise avançada ELB | 25-40% |
| 5 | Amazon CloudFront | `CloudFrontService` | CDN | 20-40% |
| 6 | CloudFront Functions | `CloudFrontFunctionsService` | Edge functions | 15-25% |
| 7 | Amazon Route 53 | `Route53Service` | DNS | 10-20% |
| 8 | Route 53 Resolver | `Route53ResolverService` | DNS resolver | 10-20% |
| 9 | AWS Direct Connect | `DirectConnectService` | Dedicated connection | 15-25% |
| 10 | Transit Gateway | `TransitGatewayService` | Network hub | 20-30% |
| 11 | AWS Global Accelerator | `GlobalAcceleratorService` | Global routing | 15-25% |
| 12 | AWS PrivateLink | `PrivateLinkService` | Private connectivity | 15-25% |
| 13 | VPC Endpoints | `VPCEndpointsService` | Service endpoints | 15-25% |
| 14 | NAT Gateway | `NATGatewayService` | NAT for VPC | 20-40% |
| 15 | Network Firewall | `NetworkFirewallService` | Managed firewall | 15-25% |
| 16 | AWS App Mesh | `AppMeshService` | Service mesh | 15-25% |
| 17 | AWS Cloud Map | `CloudMapService` | Service discovery | 10-20% |
| 18 | VPN | `VPNService` | VPN connections | 15-25% |
| 19 | Client VPN | `ClientVPNService` | Client VPN | 15-25% |
| 20 | Site-to-Site VPN | `SiteToSiteVPNService` | S2S VPN | 15-25% |

---

## 6. Security & Identity

**Total: 22 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | AWS IAM | `IAMService` | Identity management |
| 2 | IAM Identity Center | `IAMIdentityCenterService` | SSO |
| 3 | AWS Organizations | `OrganizationsService` | Multi-account management |
| 4 | AWS KMS | `KMSService` | Key management |
| 5 | AWS Secrets Manager | `SecretsManagerService` | Secrets management |
| 6 | AWS ACM | `ACMService` | Certificate management |
| 7 | AWS WAF | `WAFService` | Web application firewall |
| 8 | AWS Shield | `ShieldService` | DDoS protection |
| 9 | Amazon GuardDuty | `GuardDutyService` | Threat detection |
| 10 | AWS Security Hub | `SecurityHubService` | Security posture |
| 11 | Amazon Macie | `MacieService` | Data discovery |
| 12 | Amazon Inspector | `InspectorService` | Vulnerability scanning |
| 13 | Amazon Detective | `DetectiveService` | Security investigation |
| 14 | AWS Firewall Manager | `FirewallManagerService` | Firewall management |
| 15 | AWS RAM | `RAMService` | Resource sharing |
| 16 | AWS Artifact | `ArtifactService` | Compliance reports |
| 17 | AWS Audit Manager | `AuditManagerService` | Audit automation |
| 18 | AWS Directory Service | `DirectoryServiceService` | Managed AD |
| 19 | Amazon Cognito | `CognitoService` | User authentication |
| 20 | AWS STS | `STSService` | Security Token Service |
| 21 | AWS Control Tower | `ControlTowerService` | Landing zone |
| 22 | Service Control Policies | `SCPService` | Organization policies |

---

## 7. AI/ML

**Total: 26 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | Amazon SageMaker | `SageMakerService` | ML platform |
| 2 | SageMaker FinOps | `SageMakerFinOpsService` | ML cost analysis |
| 3 | SageMaker Ground Truth | `SageMakerGroundTruthService` | Data labeling |
| 4 | SageMaker JumpStart | `SageMakerJumpStartService` | ML solutions |
| 5 | Amazon Bedrock | `BedrockService` | Foundation models |
| 6 | Amazon Comprehend | `ComprehendService` | NLP |
| 7 | Comprehend Medical | `ComprehendMedicalService` | Medical NLP |
| 8 | Amazon Rekognition | `RekognitionService` | Image/video analysis |
| 9 | Amazon Textract | `TextractService` | Document analysis |
| 10 | Amazon Translate | `TranslateService` | Language translation |
| 11 | Amazon Polly | `PollyService` | Text-to-speech |
| 12 | Amazon Transcribe | `TranscribeService` | Speech-to-text |
| 13 | Amazon Lex | `LexService` | Chatbots |
| 14 | Amazon Personalize | `PersonalizeService` | Recommendations |
| 15 | Amazon Forecast | `ForecastService` | Time-series forecasting |
| 16 | Amazon Fraud Detector | `FraudDetectorService` | Fraud detection |
| 17 | Amazon Kendra | `KendraService` | Intelligent search |
| 18 | Amazon CodeGuru | `CodeGuruService` | Code review |
| 19 | Amazon DevOps Guru | `DevOpsGuruService` | ML operations |
| 20 | Amazon HealthLake | `HealthLakeService` | Healthcare data |
| 21 | Amazon Lookout for Vision | `LookoutVisionService` | Visual inspection |
| 22 | Amazon Lookout for Equipment | `LookoutEquipmentService` | Equipment monitoring |
| 23 | Amazon Lookout for Metrics | `LookoutMetricsService` | Anomaly detection |
| 24 | Amazon Monitron | `MonitronService` | Industrial monitoring |
| 25 | AWS Panorama | `PanoramaService` | Edge CV |
| 26 | AWS DeepRacer | `DeepRacerService` | RL learning |

---

## 8. Analytics

**Total: 20 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | Amazon Athena | `AthenaService` | SQL queries |
| 2 | Athena FinOps | `AthenaFinOpsService` | Query cost analysis |
| 3 | AWS Glue | `GlueService` | ETL |
| 4 | Glue Data Catalog | `GlueDataCatalogService` | Metadata catalog |
| 5 | Glue DataBrew | `GlueDataBrewService` | Data preparation |
| 6 | Amazon EMR | `EMRService` | Big data processing |
| 7 | EMR Serverless | `EMRServerlessService` | Serverless Spark |
| 8 | Amazon Kinesis | `KinesisService` | Real-time streaming |
| 9 | Kinesis Data Firehose | `KinesisFirehoseService` | Data delivery |
| 10 | Kinesis Data Analytics | `KinesisAnalyticsService` | Stream analytics |
| 11 | Amazon QuickSight | `QuickSightService` | BI dashboards |
| 12 | AWS Lake Formation | `LakeFormationService` | Data lake |
| 13 | Amazon MSK | `MSKService` | Managed Kafka |
| 14 | MSK Serverless | `MSKServerlessService` | Serverless Kafka |
| 15 | Amazon Data Pipeline | `DataPipelineService` | Data workflows |
| 16 | AWS Data Exchange | `DataExchangeService` | Data marketplace |
| 17 | Amazon FinSpace | `FinSpaceService` | Financial analytics |
| 18 | Clean Rooms | `CleanRoomsService` | Secure collaboration |
| 19 | Data Exports | `DataExportsService` | Cost data exports |
| 20 | Entity Resolution | `EntityResolutionService` | Record matching |

---

## 9. Developer Tools

**Total: 15 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | AWS CodeCommit | `CodeCommitService` | Git repository |
| 2 | AWS CodeBuild | `CodeBuildService` | Build service |
| 3 | AWS CodePipeline | `CodePipelineService` | CI/CD pipeline |
| 4 | AWS CodeDeploy | `CodeDeployService` | Deployment |
| 5 | AWS CodeArtifact | `CodeArtifactService` | Artifact repository |
| 6 | AWS CodeStar | `CodeStarService` | Development projects |
| 7 | CodeStar Connections | `CodeStarConnectionsService` | Git connections |
| 8 | AWS Cloud9 | `Cloud9Service` | Cloud IDE |
| 9 | AWS X-Ray | `XRayService` | Distributed tracing |
| 10 | AWS CloudShell | `CloudShellService` | Browser-based shell |
| 11 | AWS CodeGuru Reviewer | `CodeGuruReviewerService` | Code review |
| 12 | AWS CodeGuru Profiler | `CodeGuruProfilerService` | App profiling |
| 13 | Fault Injection Simulator | `FISService` | Chaos engineering |
| 14 | AWS Serverless Repository | `ServerlessRepoService` | Serverless apps |
| 15 | Application Composer | `ApplicationComposerService` | Visual builder |

---

## 10. Management & Governance

**Total: 17 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | AWS CloudFormation | `CloudFormationService` | IaC |
| 2 | AWS CloudTrail | `CloudTrailService` | API logging |
| 3 | AWS Config | `ConfigService` | Configuration management |
| 4 | AWS Systems Manager | `SSMService` | Operations management |
| 5 | AWS Service Catalog | `ServiceCatalogService` | IT service management |
| 6 | AWS License Manager | `LicenseManagerService` | License management |
| 7 | AWS Trusted Advisor | `TrustedAdvisorService` | Best practices |
| 8 | AWS Health | `HealthService` | Service health |
| 9 | AWS Personal Health | `PersonalHealthService` | Account health |
| 10 | AWS Launch Wizard | `LaunchWizardService` | Deployment wizard |
| 11 | AWS Compute Optimizer | `ComputeOptimizerService` | Right-sizing |
| 12 | AWS Resource Groups | `ResourceGroupsService` | Resource organization |
| 13 | Tag Editor | `TagEditorService` | Tag management |
| 14 | AWS Well-Architected Tool | `WellArchitectedService` | Architecture review |
| 15 | AWS Resilience Hub | `ResilienceHubService` | Resilience |
| 16 | AWS Application Migration | `ApplicationMigrationService` | Migration |
| 17 | Migration Hub | `MigrationHubService` | Migration tracking |

---

## 11. Cost Management

**Total: 10 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | AWS Cost Explorer | `CostExplorerService` | Cost analysis |
| 2 | Cost Explorer FinOps | `CostExplorerFinOpsService` | Advanced cost analysis |
| 3 | AWS Budgets | `BudgetsService` | Budget alerts |
| 4 | Budgets FinOps | `BudgetsFinOpsService` | Advanced budgets |
| 5 | AWS Cost Anomaly Detection | `CostAnomalyService` | Anomaly detection |
| 6 | Savings Plans | `SavingsPlansService` | Savings commitments |
| 7 | Reserved Instance Analyzer | `RIAnalyzerService` | RI analysis |
| 8 | AWS Pricing | `PricingService` | Pricing API |
| 9 | AWS Cost Categories | `CostCategoriesService` | Cost categorization |
| 10 | AWS Billing Conductor | `BillingConductorService` | Billing customization |

---

## 12. Observability

**Total: 15 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | Amazon CloudWatch | `CloudWatchService` | Monitoring |
| 2 | CloudWatch Logs | `CloudWatchLogsService` | Log management |
| 3 | CloudWatch Logs Insights | `CloudWatchLogsInsightsService` | Log analytics |
| 4 | CloudWatch Alarms | `CloudWatchAlarmsService` | Alerting |
| 5 | CloudWatch Dashboards | `CloudWatchDashboardsService` | Dashboards |
| 6 | CloudWatch Metrics | `CloudWatchMetricsService` | Metrics |
| 7 | CloudWatch Synthetics | `CloudWatchSyntheticsService` | Canary testing |
| 8 | CloudWatch RUM | `CloudWatchRUMService` | Real User Monitoring |
| 9 | CloudWatch Evidently | `CloudWatchEvidentlyService` | Feature flags |
| 10 | AWS X-Ray | `XRayService` | Tracing |
| 11 | Amazon Managed Grafana | `ManagedGrafanaService` | Grafana dashboards |
| 12 | Amazon Managed Prometheus | `ManagedPrometheusService` | Prometheus metrics |
| 13 | AWS Distro for OpenTelemetry | `OpenTelemetryService` | OpenTelemetry |
| 14 | CloudWatch Internet Monitor | `InternetMonitorService` | Internet monitoring |
| 15 | Application Signals | `ApplicationSignalsService` | APM |

---

## 13. IoT & Edge

**Total: 10 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | AWS IoT Core | `IoTCoreService` | IoT platform |
| 2 | AWS IoT Greengrass | `IoTGreengrassService` | Edge computing |
| 3 | AWS IoT Analytics | `IoTAnalyticsService` | IoT analytics |
| 4 | AWS IoT Events | `IoTEventsService` | IoT event detection |
| 5 | AWS IoT SiteWise | `IoTSiteWiseService` | Industrial IoT |
| 6 | AWS IoT TwinMaker | `IoTTwinMakerService` | Digital twins |
| 7 | AWS IoT Device Defender | `IoTDeviceDefenderService` | IoT security |
| 8 | AWS IoT Device Management | `IoTDeviceManagementService` | Device management |
| 9 | AWS IoT FleetWise | `IoTFleetWiseService` | Vehicle data |
| 10 | FreeRTOS | `FreeRTOSService` | Embedded OS |

---

## 14. Media

**Total: 7 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | Amazon Elastic Transcoder | `ElasticTranscoderService` | Video transcoding |
| 2 | AWS Elemental MediaConvert | `MediaConvertService` | File transcoding |
| 3 | AWS Elemental MediaLive | `MediaLiveService` | Live video |
| 4 | AWS Elemental MediaPackage | `MediaPackageService` | Video packaging |
| 5 | AWS Elemental MediaStore | `MediaStoreService` | Media storage |
| 6 | AWS Elemental MediaTailor | `MediaTailorService` | Ad insertion |
| 7 | Amazon Interactive Video | `InteractiveVideoService` | IVS |

---

## 15. End User & Productivity

**Total: 15 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | Amazon WorkSpaces | `WorkSpacesService` | Virtual desktops |
| 2 | WorkSpaces Web | `WorkSpacesWebService` | Web access |
| 3 | Amazon AppStream 2.0 | `AppStreamService` | App streaming |
| 4 | Amazon WorkDocs | `WorkDocsService` | Document storage |
| 5 | Amazon WorkMail | `WorkMailService` | Email |
| 6 | Amazon Chime | `ChimeService` | Communications |
| 7 | Amazon Connect | `ConnectService` | Contact center |
| 8 | Amazon Pinpoint | `PinpointService` | Marketing |
| 9 | Amazon SES | `SESService` | Email sending |
| 10 | Amazon SNS | `SNSService` | Notifications |
| 11 | Amazon SQS | `SQSService` | Message queuing |
| 12 | AWS Chatbot | `ChatbotService` | ChatOps |
| 13 | Amazon Q | `AmazonQService` | AI assistant |
| 14 | Amazon CodeWhisperer | `CodeWhispererService` | AI coding |
| 15 | Amazon Honeycode | `HoneycodeService` | No-code apps |

---

## 16. Specialty Services

**Total: 11 serviços**

| # | Serviço | Classe | Descrição |
|---|---------|--------|-----------|
| 1 | Amazon Braket | `BraketService` | Quantum computing |
| 2 | AWS Ground Station | `GroundStationService` | Satellite data |
| 3 | AWS RoboMaker | `RoboMakerService` | Robotics |
| 4 | AWS SimSpace Weaver | `SimSpaceWeaverService` | Simulation |
| 5 | AWS Supply Chain | `SupplyChainService` | Supply chain |
| 6 | AWS Marketplace | `MarketplaceService` | Software marketplace |
| 7 | AWS Data Zone | `DataZoneService` | Data governance |
| 8 | AWS Entity Resolution | `EntityResolutionService` | Record matching |
| 9 | AWS HealthImaging | `HealthImagingService` | Medical imaging |
| 10 | AWS HealthOmics | `HealthOmicsService` | Genomics |
| 11 | AWS HealthScribe | `HealthScribeService` | Medical transcription |

---

## 17. Matriz de Capacidades

### 17.1 Capacidades por Categoria

| Categoria | Health Check | Resources | Usage | Metrics | Recommendations |
|-----------|:------------:|:---------:|:-----:|:-------:|:---------------:|
| Compute | ✅ | ✅ | ✅ | ✅ | ✅ |
| Storage | ✅ | ✅ | ✅ | ✅ | ✅ |
| Database | ✅ | ✅ | ✅ | ✅ | ✅ |
| Networking | ✅ | ✅ | ✅ | ✅ | ✅ |
| Security | ✅ | ✅ | ✅ | ✅ | ✅ |
| AI/ML | ✅ | ✅ | ✅ | ✅ | ✅ |
| Analytics | ✅ | ✅ | ✅ | ✅ | ✅ |
| Developer Tools | ✅ | ✅ | ✅ | ✅ | ✅ |
| Management | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cost Management | ✅ | ✅ | ✅ | ✅ | ✅ |
| Observability | ✅ | ✅ | ✅ | ✅ | ✅ |
| IoT & Edge | ✅ | ✅ | ✅ | ✅ | ✅ |
| Media | ✅ | ✅ | ✅ | ✅ | ✅ |
| End User | ✅ | ✅ | ✅ | ✅ | ✅ |
| Specialty | ✅ | ✅ | ✅ | ✅ | ✅ |

**Total: 253 serviços com 5+ métodos cada = 1.265+ métodos implementados**

---

*Apêndice de Serviços - FinOps AWS Enterprise*
*253 Serviços AWS Cobertos*
*Versão 2.0 | Dezembro 2025*
