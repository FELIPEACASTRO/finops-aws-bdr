# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS is an enterprise-grade serverless solution designed for intelligent AWS cost analysis, usage monitoring, and optimization recommendations across 246 AWS services. It operates as an AWS Lambda application, delivering comprehensive financial analysis, operational monitoring, and optimization insights. A key feature is the **Automated Financial Consultant, powered by multiple AI Providers** (Amazon Q Business, OpenAI ChatGPT, Google Gemini, Perplexity), which generates intelligent reports to aid in decision-making and cost reduction. The project aims to provide a robust FinOps solution with deep analytical capabilities and actionable recommendations.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## System Architecture

The system is built with Python 3.11, adhering to Clean Architecture and Domain-Driven Design (DDD) principles. It leverages a modular and extensible design with a strong emphasis on architectural patterns.

**Core Architecture:**
The system comprises a Web Dashboard interacting with an API Layer, which in turn communicates with an Analysis Facade. This facade orchestrates operations between various Analyzers (implemented using a Strategy pattern), Integration Modules (for AWS APIs and AI Providers), and a Cost Data Module. The Analyzers Factory dynamically creates specialized analyzers (Compute, Storage, Database, Network, Security, Analytics). AI Providers are also managed via a Factory and Registry, allowing for interchangeable AI models (Amazon Q Business, OpenAI ChatGPT, Google Gemini, Perplexity AI).

**Key Architectural Components:**
- **Analyzers (Strategy Pattern)**: Six modular analyzers (Compute, Storage, Database, Network, Security, Analytics) for different AWS cost aspects.
- **AI Providers (Strategy Pattern)**: Four interchangeable AI providers for report generation and insights.
- **Factory + Registry**: Dynamic creation and management of analyzers and AI providers.
- **Template Method**: Provides a common analysis structure for consistency.
- **Facade**: Simplifies the API interface for the dashboard.
- **Exception Hierarchy**: A robust hierarchy of 15 typed exceptions for error handling.
- **AI Consultant Personas**: Supports various output personas (EXECUTIVE, CTO, DEVOPS, ANALYST) for tailored report generation.
- **UI/UX**: The solution integrates with a web dashboard for visualization and interaction.
- **FinOps Cache**: Sistema de cache com TTL configurável para reduzir chamadas AWS repetidas.
- **KPI Calculator**: 21 KPIs FinOps calculados automaticamente, incluindo tag_coverage integrado.

## Recent Changes (December 2025)

- **Performance Optimization**: Refatorado get_commitments_summary() para aceitar parâmetros sp_data e ri_data, evitando duplicação de chamadas AWS.
- **Cache System**: Implementado FinOpsCache com TTL configurável (padrão 5 minutos) e estatísticas de hit/miss.
- **Tag Coverage Integration**: tag_coverage_percent agora é automaticamente calculado e integrado nos KPIs via TagGovernanceService.
- **Type Safety**: Corrigidos todos os erros de tipagem LSP, incluindo problemas de Dict[str, int] vs List[str] nos analyzer resources.

## FinOps Compliance Status

- Nível 1 (Crawl): ~80% completo
- Nível 2 (Walk): ~65% completo
- Nível 3 (Run): ~15% completo
- Nível 4 (Fly): ~5% completo

### Next Steps for Higher Compliance

- Ingestão CUR real via S3/Athena
- Unit Economics com dados reais de transações/clientes
- Campos CUR adicionais para análise granular

## External Dependencies

- **AWS Services**:
    - AWS Lambda
    - AWS Compute Optimizer
    - AWS Cost Explorer
    - AWS Trusted Advisor
    - Amazon Q Business
    - AWS Budgets
    - AWS Cost Anomaly Detection
    - AWS Savings Plans
    - AWS Reserved Instances
    - AWS Resource Groups (for Tag Governance)
    - boto3 (AWS SDK for Python)
- **AI Providers**:
    - OpenAI ChatGPT (via API)
    - Google Gemini (via API)
    - Perplexity AI (via API)
- **Python Libraries**:
    - Python 3.11
- **Configuration**:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION
    - Q_BUSINESS_APPLICATION_ID (for Amazon Q Business)
    - OPENAI_API_KEY (for OpenAI ChatGPT)
    - GEMINI_API_KEY (for Google Gemini)
    - PERPLEXITY_API_KEY (for Perplexity AI)
```