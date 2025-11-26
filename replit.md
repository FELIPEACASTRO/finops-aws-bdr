# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

**FinOps AWS BDR** is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations. Built with Clean Architecture and Domain-Driven Design (DDD) principles, this Python application is designed to run as an AWS Lambda function.

### Project Type
- **Primary Platform**: AWS Lambda (Serverless)
- **Language**: Python 3.11
- **Architecture**: Clean Architecture + Domain-Driven Design
- **Testing**: Pytest with mocked AWS services (moto)

## Current State

This project is undergoing transformation into a world-class FinOps product following a 10-phase roadmap.

### What's Working
- ✅ Python 3.11 installed and configured
- ✅ All dependencies installed (boto3, pytest, moto, pytest-asyncio, etc.)
- ✅ Test suite fully passing (83 passed, 1 skipped)
- ✅ Local demo runner for testing Lambda handler with mocked AWS services
- ✅ Comprehensive .gitignore for Python projects
- ✅ **CleanupManager** - Sistema de limpeza automática de arquivos temporários

### Recent Changes (Nov 26, 2025)

#### FASE 1.1 - Sistema de Limpeza BKP (CONCLUÍDO)
- Implementado `CleanupManager` em `src/finops_aws/core/cleanup_manager.py`
- Limpeza automática de arquivos: `.bkp`, `.tmp`, `.cache`, `.log`, `.pyc`, `.pyo`
- Limpeza de objetos S3 antigos (execuções expiradas)
- Limpeza de diretórios `__pycache__`
- Modo dry-run para simulação
- Métricas detalhadas de limpeza integradas ao relatório JSON
- 27 testes unitários criados em `tests/unit/test_cleanup_manager.py`
- Integração no `lambda_handler.py` via helper `cleanup_after_execution`

### Roadmap Progress
- [x] FASE 1.1 - Sistema de Limpeza BKP
- [ ] FASE 1.2 - Controle de Execução (DynamoDB)
- [ ] FASE 1.3 - Refatoração Core (Factory Pattern)
- [ ] FASE 2 - Expansão de Serviços AWS
- [ ] FASE 3 - Inteligência e Automação (ML)
- [ ] FASE 4 - Interface e Experiência (Dashboard)
- [ ] FASE 5 - Escalabilidade e Performance
- [ ] FASE 6 - Segurança e Compliance
- [ ] FASE 7 - Governança e Automação
- [ ] FASE 8 - Testes e Qualidade
- [ ] FASE 9 - Deployment e Operações
- [ ] FASE 10 - Go-to-Market

## Project Structure

```
finops-aws-bdr/
├── src/finops_aws/           # Main application code
│   ├── core/                 # Core business logic (NEW)
│   │   ├── cleanup_manager.py   # Sistema de limpeza automática
│   │   ├── state_manager.py     # Gerenciamento de estado
│   │   └── resilient_executor.py # Execução resiliente
│   ├── domain/               # Domain layer (entities, value objects)
│   ├── application/          # Application layer (use cases, DTOs)
│   ├── infrastructure/       # Infrastructure layer (AWS services)
│   ├── interfaces/           # Interface layer (Lambda handlers)
│   ├── services/             # Service layer (cost, metrics, optimizer)
│   ├── models/               # Data models
│   └── utils/                # Utilities (logging, AWS helpers)
├── tests/                    # Unit tests (83 tests)
│   └── unit/
│       ├── test_cleanup_manager.py  # 27 tests for cleanup system
│       ├── test_cost_service.py
│       ├── test_metrics_service.py
│       ├── test_optimizer_service.py
│       ├── test_resilient_executor.py
│       └── test_state_manager.py
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

**Note**: The current implementation always uses mocked AWS services (via moto) regardless of whether AWS credentials are present. This ensures consistent, safe testing in the Replit environment.

### Test Options
The demo runner provides three modes:
1. Run Lambda handler demo (with mocked AWS services)
2. Run test suite
3. Run both

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

### Cleanup System (NEW - FASE 1.1)
- Automatic cleanup of temporary files (.bkp, .tmp, .cache)
- S3 object cleanup for expired executions
- __pycache__ directory cleanup
- Dry-run mode for simulation
- Detailed cleanup metrics in JSON reports

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

## Environment Variables

### Cleanup Configuration
- `CLEANUP_ENABLED` - Enable/disable automatic cleanup (default: `true`)
- `CLEANUP_FILE_EXTENSIONS` - File extensions to clean (default: `.bkp,.tmp,.cache,.log,.pyc,.pyo`)
- `CLEANUP_MAX_FILE_AGE_HOURS` - Max file age in hours (default: `24`)
- `CLEANUP_S3_ENABLED` - Enable S3 cleanup (default: `true`)
- `CLEANUP_S3_MAX_AGE_DAYS` - Max S3 object age in days (default: `7`)
- `CLEANUP_DRY_RUN` - Simulate cleanup without deleting (default: `false`)

### Application Configuration
- `FINOPS_STATE_BUCKET` - S3 bucket for state storage
- `LOG_LEVEL` - Logging level (default: `INFO`)

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## Notes

- This is a **serverless application** designed for AWS Lambda
- Local execution uses **mocked AWS services** (no real AWS API calls without credentials)
- The application requires **AWS credentials** for production use
- State management uses **S3** for persistence between Lambda invocations
- The resilient handler supports **automatic recovery** from failures

## Resources

- **README.md** - Detailed documentation in Portuguese
- **README_RESILIENT.md** - Resilient execution system documentation
- **EXPANSION_ROADMAP.md** - Future enhancements and expansion plans
- **infrastructure/cloudformation-template.yaml** - AWS infrastructure definition
- **attached_assets/** - Contract and roadmap documents
