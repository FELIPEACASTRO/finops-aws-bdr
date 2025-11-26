# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS BDR is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations. This Python application, designed to run as an AWS Lambda function, aims to transform into a world-class FinOps product, offering comprehensive financial analysis, operational monitoring, and optimization insights for AWS environments.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## Project Status

- **Test Suite**: 268 tests passing, 1 skipped
- **Services Implemented**: 21 AWS services (of 253 total target)
- **Current Phase**: FASE 2.3 - High Priority Services (COMPLETED)

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

## AWS Services Implemented (21 of 253)

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

## Recent Changes (Nov 26, 2025)

### FASE 2.3 - High Priority Services (COMPLETED)
- Added 15 new FinOps services covering high-cost-impact AWS resources
- Expanded `AWSServiceType` enum with 14 new service types
- Updated `ServiceFactory` with getters for all new services
- Enhanced `ServiceRecommendation` dataclass with `title` and `action` fields
- Fixed ELB service type to use correct boto3 service name ('elb')
- Added 37 new unit tests for priority services

### Key Service Files Added
- `src/finops_aws/services/ec2_finops_service.py`
- `src/finops_aws/services/lambda_finops_service.py`
- `src/finops_aws/services/redshift_service.py`
- `src/finops_aws/services/cloudfront_service.py`
- `src/finops_aws/services/elb_service.py`
- `src/finops_aws/services/emr_service.py`
- `src/finops_aws/services/vpc_network_service.py`
- `src/finops_aws/services/kinesis_service.py`
- `src/finops_aws/services/glue_service.py`
- `src/finops_aws/services/sagemaker_service.py`
- `src/finops_aws/services/route53_service.py`
- `src/finops_aws/services/backup_service.py`
- `src/finops_aws/services/sns_sqs_service.py`
- `src/finops_aws/services/secrets_manager_service.py`
