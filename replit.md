# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

**FinOps AWS BDR** is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations. Built with Clean Architecture and Domain-Driven Design (DDD) principles, this Python application is designed to run as an AWS Lambda function.

### Project Type
- **Primary Platform**: AWS Lambda (Serverless)
- **Language**: Python 3.11
- **Architecture**: Clean Architecture + Domain-Driven Design
- **Testing**: Pytest with mocked AWS services (moto)

## Current State

This project has been successfully set up in the Replit environment for local development and testing.

### What's Working
- ✅ Python 3.11 installed and configured
- ✅ All dependencies installed (boto3, pytest, moto, pytest-asyncio, etc.)
- ✅ Test suite fully passing (56 passed, 1 skipped)
- ✅ Local demo runner for testing Lambda handler with mocked AWS services
- ✅ Comprehensive .gitignore for Python projects

### Recent Changes (Nov 26, 2025)
- Installed Python 3.11 runtime
- Installed all project dependencies from requirements.txt
- Added pytest-asyncio for async test support (required for resilient executor tests)
- Created `run_local_demo.py` for local testing without AWS credentials
- Configured "Run Tests" workflow to execute test suite automatically
- All tests now passing after installing pytest-asyncio

## Project Structure

```
finops-aws-bdr/
├── src/finops_aws/           # Main application code
│   ├── domain/               # Domain layer (entities, value objects)
│   ├── application/          # Application layer (use cases, DTOs)
│   ├── infrastructure/       # Infrastructure layer (AWS services)
│   ├── interfaces/           # Interface layer (Lambda handlers)
│   ├── services/             # Service layer (cost, metrics, optimizer)
│   ├── models/               # Data models
│   └── utils/                # Utilities (logging, AWS helpers)
├── tests/                    # Unit tests
├── infrastructure/           # CloudFormation templates
├── run_local_demo.py        # Local testing script (Replit)
└── deploy.sh                # AWS deployment script
```

## Running in Replit

### Testing
The "Run Tests" workflow automatically executes the test suite using pytest with mocked AWS services.

To run manually:
```bash
python run_local_demo.py 2
```

### Demo Mode
To test the Lambda handler locally with mocked AWS services:
```bash
python run_local_demo.py 1
```

This runs the handler without requiring actual AWS credentials, using the moto library to mock AWS API calls.

**Note**: The current implementation always uses mocked AWS services (via moto) regardless of whether AWS credentials are present. This ensures consistent, safe testing in the Replit environment. To test against real AWS resources, you would need to run the Lambda handler outside of the demo script's mock context.

### Test Options
The demo runner provides three modes:
1. Run Lambda handler demo (with mocked AWS services)
2. Run test suite
3. Run both

## AWS Deployment

This application is designed to run in AWS as a Lambda function. Deployment requires:

1. AWS Account with appropriate IAM permissions
2. S3 bucket for Lambda code deployment
3. S3 bucket for execution state storage

### Deploy to AWS
```bash
./deploy.sh -b your-s3-bucket
```

For full deployment options, see `./deploy.sh --help`

### Infrastructure
The CloudFormation template (`infrastructure/cloudformation-template.yaml`) includes:
- Lambda function with 15-minute timeout
- IAM role with necessary permissions
- EventBridge rule for scheduled execution (daily by default)
- Optional API Gateway for HTTP access
- CloudWatch log group

## Key Features

### Financial Analysis
- Multi-period cost analysis (7, 15, 30 days)
- Trend detection (increasing/decreasing/stable)
- Service-level cost breakdown
- Top services ranking

### Operational Monitoring
- EC2 performance analytics (CPU utilization)
- Lambda operational insights (invocations, errors, throttles)
- Custom metrics collection
- Real-time processing with retry logic

### Optimization Recommendations
- AWS Compute Optimizer integration
- Right-sizing recommendations (EC2, Lambda, EBS)
- ROI analysis with savings estimates
- Finding classification system

### Resilience Features
- State management with S3 persistence
- Automatic recovery from failures
- Retry logic with exponential backoff
- Circuit breaker pattern
- Dependency-aware task execution

## Development

### Dependencies
See `requirements.txt` for all Python dependencies. Key libraries:
- `boto3` - AWS SDK for Python
- `pytest` - Testing framework
- `moto` - AWS service mocking
- `tabulate` - Table formatting

### Testing
Tests are located in the `tests/` directory and use:
- `pytest` for test execution
- `pytest-mock` for mocking
- `pytest-asyncio` for async test support
- `moto` for AWS service mocking

### Code Quality
The project follows:
- Clean Architecture principles
- SOLID design principles
- Domain-Driven Design (DDD)
- Type hints (Python 3.11+)
- Structured logging (JSON format)

## User Preferences

*No specific user preferences recorded yet.*

## Notes

- This is a **serverless application** designed for AWS Lambda
- Local execution uses **mocked AWS services** (no real AWS API calls without credentials)
- The application requires **AWS credentials** for production use
- State management uses **S3** for persistence between Lambda invocations
- The resilient handler supports **automatic recovery** from failures

## Next Steps

To use this application in production:

1. Configure AWS credentials
2. Create S3 buckets for deployment and state storage
3. Review and customize CloudFormation parameters
4. Deploy using the `deploy.sh` script
5. Enable AWS Compute Optimizer for recommendations
6. Configure EventBridge schedule or API Gateway access

## Resources

- **README.md** - Detailed documentation in Portuguese
- **README_RESILIENT.md** - Resilient execution system documentation
- **EXPANSION_ROADMAP.md** - Future enhancements and expansion plans
- **infrastructure/cloudformation-template.yaml** - AWS infrastructure definition
