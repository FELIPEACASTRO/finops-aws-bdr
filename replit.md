# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS BDR is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations. This Python application, designed to run as an AWS Lambda function, aims to transform into a world-class FinOps product, offering comprehensive financial analysis, operational monitoring, and optimization insights for AWS environments.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## Project Status

- **Test Suite**: 357+ tests passing
- **Services Implemented**: 30 AWS services (of 253 total target)
- **Current Phase**: FASE 2.5 - High-Cost Storage & Database Services (COMPLETED)
- **Documentation**: README.md completamente atualizado (extremamente didático)

## System Architecture

The project is built with Python 3.11, adhering to Clean Architecture and Domain-Driven Design (DDD) principles. It is structured as a serverless AWS Lambda application.

**Core Architectural Decisions:**

- **Modular Design:** Organized into `core`, `domain`, `application`, `infrastructure`, `interfaces`, `services`, `models`, and `utils` layers for clear separation of concerns.
- **Factory Pattern:** Centralized creation and management of `boto3` clients and FinOps services using `AWSClientFactory` and `ServiceFactory` for dependency injection and testability.
- **State Management:** Utilizes `DynamoDBStateManager` for persistent state management and checkpointing across AWS services, supporting atomic operations and TTL for old executions.
- **Resilience:** Incorporates a `RetryHandler` with exponential backoff and jitter, and a `ResilientExecutor` for automatic recovery from failures and dependency-aware task execution.
- **Automatic Cleanup:** `CleanupManager` handles automatic removal of temporary files, old S3 objects, and `__pycache__` directories.
- **Extensible Service Layer:** Employs `BaseAWSService` as an abstract base class for all AWS service integrations, standardizing interfaces for `get_resources()`, `get_costs()`, `get_metrics()`, and `get_recommendations()`.
- **Testing Strategy:** Comprehensive unit testing with Pytest, utilizing `moto` for mocking AWS services to ensure consistent and safe testing.

## AWS Services Implemented (30 of 253)

### Storage Services
- **S3Service** - Object Storage analysis (buckets, costs, lifecycle, recommendations)
- **EBSService** - Block Storage analysis (volumes, snapshots, gp2→gp3 recommendations)
- **EFSService** - File Storage analysis (file systems, lifecycle, mount targets)

### Database Services
- **DynamoDBFinOpsService** - NoSQL analysis (tables, capacity, PITR, billing mode)
- **ElastiCacheService** - Cache analysis (Redis/Memcached clusters, replication groups)
- **RedshiftService** - Data Warehouse analysis (clusters, encryption, snapshots)

### Compute Services
- **EC2FinOpsService** - Instance analysis (state, rightsizing, stopped instances)
- **LambdaFinOpsService** - Serverless analysis (memory optimization, runtime, timeout)
- **ECSContainerService** - Container analysis (clusters, services, tasks, Fargate)
- **EMRService** - Big Data analysis (Spark/Hadoop clusters, auto-scaling, Spot)
- **SageMakerService** - ML analysis (notebooks, endpoints, training jobs)

### Networking Services
- **VPCNetworkService** - Network analysis (NAT Gateways, Elastic IPs)
- **CloudFrontService** - CDN analysis (distributions, cache, compression)
- **ELBService** - Load Balancer analysis (ALB, NLB, CLB, target groups)
- **Route53Service** - DNS analysis (hosted zones, records, health checks)

### Data & Analytics Services
- **KinesisService** - Streaming analysis (data streams, shards, retention)
- **GlueService** - ETL analysis (jobs, crawlers, data catalog)
- **MSKService** - Kafka Streaming analysis (clusters, brokers, storage, throughput)
- **OpenSearchService** - Search/Analytics (domains, nodes, UltraWarm, encryption)
- **TimestreamService** - Time series database (databases, tables, scheduled queries)

### Container & Compute Services (NEW)
- **EKSService** - Kubernetes analysis (clusters, node groups, Fargate profiles, addons)

### Database Services (Extended)
- **AuroraService** - Aurora analysis (MySQL/PostgreSQL clusters, Serverless v2, instances)
- **DocumentDBService** - DocumentDB analysis (MongoDB compatible clusters, instances)
- **NeptuneService** - Neptune analysis (graph database clusters, instances)

### Storage Services (Extended)
- **FSxService** - FSx analysis (Lustre, Windows, ONTAP, OpenZFS file systems)

### Desktop Services (NEW)
- **WorkSpacesService** - Virtual desktop analysis (workspaces, directories, bundles, billing)

### Integration Services
- **SNSSQSService** - Messaging analysis (SNS topics, SQS queues)
- **BackupService** - Backup analysis (vaults, jobs, recovery points)
- **SecretsManagerService** - Secrets analysis (rotation, encryption, usage)

## Key Features

- **Financial Analysis:** Multi-period cost analysis, trend detection, service-level cost breakdown, and top services ranking.
- **Operational Monitoring:** EC2 performance analytics, Lambda operational insights, custom metrics collection, and real-time processing.
- **Optimization Recommendations:** Integration with AWS Compute Optimizer, right-sizing recommendations (EC2, Lambda, EBS), and ROI analysis with savings estimates.

## External Dependencies

- **AWS SDK for Python (boto3):** Core library for interacting with AWS services.
- **pytest:** Python testing framework.
- **moto:** Library for mocking AWS services in tests.
- **pytest-asyncio:** Pytest plugin for testing asyncio code.
- **pytest-mock:** Pytest plugin for mocking.
- **tabulate:** Library for pretty-printing tabular data.
- **AWS DynamoDB:** Used for state persistence and checkpointing.
- **AWS S3:** Used for state storage (legacy) and S3 object cleanup.
- **AWS Lambda:** The primary execution environment for the application.
- **AWS CloudWatch:** For collecting and analyzing metrics.
- **AWS Compute Optimizer:** Integrated for optimization recommendations.

## Project Structure

```
finops-aws/
├── src/finops_aws/           # Main application code
│   ├── application/          # Use cases and DTOs
│   ├── core/                 # Core infrastructure (factories, retry, state)
│   ├── domain/               # Domain entities and value objects
│   ├── infrastructure/       # External service adapters
│   ├── interfaces/           # Interface definitions
│   ├── models/               # Data models
│   ├── services/             # AWS FinOps service implementations (21 services)
│   ├── utils/                # Utilities (logger, helpers)
│   ├── lambda_handler.py     # Main Lambda entry point
│   └── resilient_lambda_handler.py
├── tests/unit/               # Unit tests (271 tests)
├── example_events/           # Sample Lambda event payloads
├── infrastructure/           # CloudFormation templates
├── deploy.sh                 # Deployment script
├── requirements.txt          # Python dependencies
├── service_aws.json          # AWS services catalog (253 services)
└── replit.md                 # This file
```

## Recent Changes (Nov 26, 2025)

### Project Cleanup
- Removed unnecessary files: `attached_assets/`, `test_resilient_simple.py`, `test_resilient_system.py`
- Removed redundant documentation: `README_RESILIENT.md`, `EXPANSION_ROADMAP.md`
- Cleaned `.pytest_cache/` and `__pycache__` directories
- Updated `.gitignore` to prevent future clutter
- All 268 tests passing after cleanup

### FASE 2.3 - High Priority Services (COMPLETED)
- Added 14 new FinOps services covering high-cost-impact AWS resources
- Expanded `AWSServiceType` enum with 14 new service types
- Updated `ServiceFactory` with getters for all new services
- Enhanced `ServiceRecommendation` dataclass with `title` and `action` fields
- Fixed ELB service type to use correct boto3 service name ('elb')
- Fixed critical export gap in `services/__init__.py` (all 14 services + 15+ dataclasses)
- Added 37 new unit tests for priority services

### FASE 2.4 - Non-Serverless High-Cost Services (COMPLETED)
- Added **MSKService** for Amazon Managed Streaming for Apache Kafka analysis
- Added **EKSService** for Amazon Elastic Kubernetes Service analysis
- Added **AuroraService** for Amazon Aurora MySQL/PostgreSQL analysis
- Added **OpenSearchService** for Amazon OpenSearch Service analysis
- Added **WorkSpacesService** for Amazon WorkSpaces analysis
- Updated `AWSServiceType` enum with 4 new types (EKS, OPENSEARCH, WORKSPACES, and MSK)
- Updated `ServiceFactory` with getters for all 4 new services
- Added 34 new unit tests for Phase 2.4 services
- Total: 318+ tests passing

### FASE 2.5 - High-Cost Storage & Database Services (COMPLETED)
- Added **FSxService** for Amazon FSx analysis (Lustre, Windows, ONTAP, OpenZFS)
- Added **DocumentDBService** for Amazon DocumentDB analysis (MongoDB compatible)
- Added **NeptuneService** for Amazon Neptune analysis (graph database)
- Added **TimestreamService** for Amazon Timestream analysis (time series database)
- Updated `AWSServiceType` enum with 5 new types (FSX, DOCUMENTDB, NEPTUNE, TIMESTREAM_WRITE, TIMESTREAM_QUERY)
- Updated `ServiceFactory` with getters for all 4 new services
- Added 39 new unit tests for Phase 2.5 services
- Total: 357+ tests passing

### Service Files (30 total)
**Core Services:** `cost_service.py`, `metrics_service.py`, `optimizer_service.py`, `rds_service.py`
**Storage:** `s3_service.py`, `ebs_service.py`, `efs_service.py`
**Database:** `dynamodb_finops_service.py`, `elasticache_service.py`, `redshift_service.py`, `aurora_service.py`, `documentdb_service.py`, `neptune_service.py`
**Compute:** `ec2_finops_service.py`, `lambda_finops_service.py`, `ecs_service.py`, `emr_service.py`, `sagemaker_service.py`, `eks_service.py`
**Networking:** `vpc_network_service.py`, `cloudfront_service.py`, `elb_service.py`, `route53_service.py`
**Streaming/Analytics:** `kinesis_service.py`, `msk_service.py`, `glue_service.py`, `opensearch_service.py`, `timestream_service.py`
**Desktop:** `workspaces_service.py`
**Integration:** `sns_sqs_service.py`, `backup_service.py`, `secrets_manager_service.py`
**Graph/Document DB:** `neptune_service.py`, `documentdb_service.py`
**File Systems:** `fsx_service.py`
