# FinOps AWS - Enterprise-Grade AWS Cost Optimization Platform

## Overview

FinOps AWS is an **enterprise-grade serverless solution** developed with **Python 3.11** for intelligent AWS cost analysis, usage monitoring, and optimization recommendations across **246 AWS services**. The system functions as an AWS Lambda application with a professional **React 18 Frontend** (TypeScript + Vite) and **Flask Backend**, delivering comprehensive financial analysis, operational monitoring, and real-time optimization insights. Key capabilities include a professional web dashboard, real-time notification panel, integration with 5 AI providers, a complete REST API, and multi-region/multi-account analysis of real AWS data. The project aims to provide full FinOps compliance across four maturity levels: Cost Visibility, Allocation & Control, Active Optimization, and Operational Excellence.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## System Architecture

The system is built with Python 3.11, adhering to Clean Architecture and Domain-Driven Design (DDD) principles, emphasizing a modular and extensible design.

**Core Architecture:**
A Web Dashboard interacts with an API Layer, which communicates with an Analysis Facade. This facade orchestrates operations between various Analyzers (Strategy pattern), Integration Modules (for AWS APIs and AI Providers), and a Cost Data Module. Analyzers are dynamically created via a Factory (Compute, Storage, Database, Network, Security, Analytics). AI Providers are managed via a Factory and Registry, allowing for interchangeable AI models (Amazon Q Business, OpenAI ChatGPT, Google Gemini, Perplexity AI, StackSpot AI).

**Key Architectural Components:**
- **Analyzers (Strategy Pattern)**: Six modular analyzers for different AWS cost aspects.
- **AI Providers (Strategy Pattern)**: Five interchangeable AI providers for report generation and insights.
- **Factory + Registry**: Dynamic creation and management of analyzers and AI providers.
- **Template Method**: Ensures a common analysis structure.
- **Facade**: Simplifies the API interface for the dashboard.
- **Exception Hierarchy**: Robust error handling with 15 typed exceptions.
- **AI Consultant Personas**: Supports various output personas (EXECUTIVE, CTO, DEVOPS, ANALYST) for tailored reports.
- **UI/UX**: React 18 + TypeScript + Vite frontend with a complete design system, professional dashboard, and real-time notification panel.
- **FinOps Cache**: Configurable TTL cache to reduce repeated AWS calls and latency.
- **KPI Calculator**: Automatically calculates 21 FinOps KPIs, including tag_coverage.

**FinOps Services Implemented (by Maturity Level):**
- **Nível 1 - Iniciante (Cost Visibility)**: CUR Ingestion, Cost Allocation, Tag Governance.
- **Nível 2 - Intermediário (Allocation & Control)**: Showback/Chargeback, Budgets, Savings Plans, Reserved Instances.
- **Nível 3 - Avançado (Active Optimization)**: Unit Economics, Policy Automation, Predictive Optimization, KPI Calculator.
- **Nível 4 - Excelência (Operational Excellence)**: Real-Time Insights, FinOps Maturity, AI Consultant.

## External Dependencies

### AWS Services Integrados
- **Cost Management**: Cost Explorer, Budgets, Savings Plans, Reserved Instances
- **Optimization**: Compute Optimizer, Trusted Advisor, Cost Anomaly Detection
- **AI**: Amazon Q Business
- **Storage & Query**: S3, Athena (for CUR queries)
- **Resource Management**: Resource Groups Tagging API
- **SDK**: boto3 (60+ services supported via enum AWSServiceType)

### AI Providers Suportados (5 Provedores)
1. **Amazon Q Business**
2. **OpenAI ChatGPT** (gpt-4o, gpt-4o-mini, gpt-4-turbo)
3. **Google Gemini** (gemini-2.5-pro, gemini-2.5-flash)
4. **Perplexity AI** (sonar-pro, real-time online search)
5. **StackSpot AI** (OAuth 2.0)

### Stack Técnico Completo
- **Backend**: Python 3.11, Flask 2.3+, boto3 1.34+
- **Frontend**: React 18, TypeScript 5.7, Vite 7.2
- **Banco de Dados**: Nenhum (análise stateless)
- **Cache**: Em memória com TTL configurável
- **Deployment**: AWS Lambda, S3, EventBridge, Step Functions

### Variáveis de Ambiente Requeridas
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `OPENAI_API_KEY` (Optional)
- `GEMINI_API_KEY` (Optional)
- `PERPLEXITY_API_KEY` (Optional)
- `STACKSPOT_CLIENT_ID` (Optional)
- `STACKSPOT_CLIENT_SECRET` (Optional)
- `STACKSPOT_REALM` (Optional)
- `Q_BUSINESS_APPLICATION_ID` (Optional)