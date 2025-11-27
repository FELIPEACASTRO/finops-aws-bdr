# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS BDR is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations. This Python application, designed to run as an AWS Lambda function, aims to transform into a world-class FinOps product, offering comprehensive financial analysis, operational monitoring, and optimization insights for AWS environments. Key capabilities include multi-period cost analysis, EC2/Lambda operational insights, and integration with AWS Compute Optimizer for right-sizing recommendations and ROI analysis.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## Project Status

- **Test Suite**: 1726+ tests collected
- **Services Implemented**: 140 AWS services (of 253 total target) - ~55.3% complete
- **Current Phase**: FASE 4.2+ - Multiple categories complete

### Recent Changes (November 27, 2025)
- FASE 4.2: Management & Governance (Trusted Advisor, Organizations, Control Tower) - 36 tests
- FASE 4.3+: Application Integration, Streaming, Database Advanced, Storage Advanced, Developer Tools, ML Advanced, Analytics Advanced - 42 services bootstrapped
- All services properly registered in ServiceFactory with getters and get_all_services()
- Zero gaps between service files and factory registration

### Completed Phases
- FASE 4.0: Developer Tools (X-Ray, CloudFormation, SSM, AppConfig, SQS) - 111 tests
- FASE 4.1: Security & Identity (IAM, Security Hub, Macie) - 79 tests
- FASE 4.2: Management & Governance (Trusted Advisor, Organizations, Control Tower) - 36 tests
- FASE 3.0-3.9: AI/ML, Analytics, Networking, Containers, IoT, Media, Migration, End User Computing, Game/Robotics, Blockchain/Quantum

### Services by Category
- **Compute & Storage**: EC2, Lambda, S3, EBS, EFS, FSx, Storage Gateway, S3 Outposts
- **Database**: RDS, DynamoDB, Aurora, DocumentDB, Neptune, MemoryDB, Keyspaces, Timestream, QLDB
- **Networking**: VPC, ELB, CloudFront, Route53, Global Accelerator, Direct Connect, Transit Gateway
- **Security & Identity**: IAM, Security Hub, Macie, GuardDuty, Inspector, KMS, ACM, WAF, Cognito
- **AI/ML**: Bedrock, SageMaker, Comprehend, Rekognition, Textract, Lex, Polly, Transcribe, Personalize, Forecast
- **Analytics**: Athena, QuickSight, Glue, EMR, Kinesis, DataSync, Lake Formation, FinSpace
- **Developer Tools**: X-Ray, CloudFormation, SSM, AppConfig, CodeBuild, CodePipeline, CodeDeploy, CodeCommit, CodeStar, Cloud9, Proton
- **Containers**: ECS, EKS, ECR, App Runner, Elastic Beanstalk, Lightsail
- **IoT & Edge**: IoT Core, IoT Analytics, Greengrass, IoT Events
- **Media**: MediaConvert, MediaLive, MediaPackage, IVS, MediaStore
- **Migration**: DMS, MGN, Snow Family, DataPipeline, DataExchange
- **Management & Governance**: CloudTrail, Config, Trusted Advisor, Organizations, Control Tower
- **Application Integration**: SNS, SQS, EventBridge, AppFlow, MQ, Pinpoint, SES, Connect
- **Blockchain & Quantum**: QLDB, Managed Blockchain, Braket

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

**Key Features:**

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
- **AWS S3:** Used for state storage and S3 object cleanup.
- **AWS Lambda:** The primary execution environment for the application.
- **AWS CloudWatch:** For collecting and analyzing metrics.
- **AWS Compute Optimizer:** Integrated for optimization recommendations.
