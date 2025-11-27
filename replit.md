# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS BDR is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations. This Python application, designed to run as an AWS Lambda function, aims to transform into a world-class FinOps product, offering comprehensive financial analysis, operational monitoring, and optimization insights for AWS environments. Key capabilities include multi-period cost analysis, EC2/Lambda operational insights, and integration with AWS Compute Optimizer for right-sizing recommendations and ROI analysis.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## Project Status

- **Test Suite**: 582+ tests passing
- **Services Implemented**: 48 AWS services (of 253 total target)
- **Current Phase**: FASE 2.9 - Security & Compliance Services (COMPLETED)

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