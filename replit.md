# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS is an enterprise-grade serverless solution designed for intelligent AWS cost analysis, usage monitoring, and optimization recommendations across 246 AWS services. It operates as an AWS Lambda application, delivering comprehensive financial analysis, operational monitoring, and optimization insights. A key feature is the **Automated Financial Consultant, powered by multiple AI Providers** (Amazon Q Business, OpenAI ChatGPT, Google Gemini, Perplexity, **StackSpot AI**), which generates intelligent reports to aid in decision-making and cost reduction. The project aims to provide a robust FinOps solution with deep analytical capabilities and actionable recommendations.

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
- **AI Providers (Strategy Pattern)**: Five interchangeable AI providers for report generation and insights (Perplexity, OpenAI, Gemini, Amazon Q, StackSpot).
- **Factory + Registry**: Dynamic creation and management of analyzers and AI providers.
- **Template Method**: Provides a common analysis structure for consistency.
- **Facade**: Simplifies the API interface for the dashboard.
- **Exception Hierarchy**: A robust hierarchy of 15 typed exceptions for error handling.
- **AI Consultant Personas**: Supports various output personas (EXECUTIVE, CTO, DEVOPS, ANALYST) for tailored report generation.
- **UI/UX**: The solution integrates with a web dashboard for visualization and interaction.
- **FinOps Cache**: Sistema de cache com TTL configurável para reduzir chamadas AWS repetidas.
- **KPI Calculator**: 21 KPIs FinOps calculados automaticamente, incluindo tag_coverage integrado.

## FinOps Services (20+ Services Implemented)

### CRAWL Level Services
- **CUR Ingestion Service**: Ingestão de Cost and Usage Reports via S3/Athena com fallback para Cost Explorer
- **Cost Allocation Service**: Motor de alocação de custos com scorecard de maturidade
- **Tag Governance Service**: Governança de tags com políticas obrigatórias

### WALK Level Services
- **Showback/Chargeback Service**: Relatórios de showback por BU/projeto e invoices de chargeback
- **Budgets Service**: Integração com AWS Budgets para alertas e monitoramento
- **Savings Plans Service**: Análise de cobertura e recomendações de Savings Plans
- **Reserved Instances Service**: Monitoramento de utilização e expiração de RIs

### RUN Level Services
- **Unit Economics Service**: Métricas de custo por cliente, transação, API call
- **Policy Automation Service**: Orquestração de políticas automatizadas com workflow de aprovação
- **Predictive Optimization Service**: Previsão de custos e recomendações AI-driven
- **KPI Calculator Service**: 21 KPIs FinOps calculados automaticamente

### FLY Level Services
- **Real-Time Insights Service**: Pipeline de insights com latência <5 min
- **FinOps Maturity Service**: Avaliação de maturidade com OKRs e roadmap
- **AI Consultant Service**: Consultor financeiro automatizado com múltiplos provedores

## Recent Changes (December 2025)

### StackSpot AI Integration (December 8, 2025)
Integração do StackSpot AI como 5º provedor de IA no Consultor Financeiro:
- **StackSpotProvider**: Implementado seguindo padrão Strategy (BaseAIProvider)
- **OAuth 2.0 Flow**: Client Credentials com token endpoint e refresh automático
- **Health Check**: Endpoint `/api/v1/integrations/status` expandido para StackSpot
- **Frontend Settings**: StackSpot AI visível na aba API & Integrações
- **Secrets configurados**: STACKSPOT_CLIENT_ID, STACKSPOT_CLIENT_SECRET, STACKSPOT_REALM
- **Nota**: Contas Enterprise podem requerer VPN/IP whitelist para autenticação

### Settings Full Backend Integration (December 8, 2025)
Página de Configurações com integração completa backend-to-backend, sem mocks:
- **Endpoint `/api/v1/integrations/status`**: Status real de cada API (AWS, Perplexity, OpenAI, Gemini, Amazon Q)
- **Endpoint `/api/v1/cache/clear`**: Limpar cache com feedback visual
- **SETTINGS_STORE expandido**: Inclui `ai_provider` e `notifications.types`
- **PUT /api/v1/settings**: Aceita ai_provider, notifications.frequency, notifications.types com validação
- **Settings.tsx refatorado**: Checkboxes controlados, integrações dinâmicas, cache clearing real

### Localização Português Brasil - Níveis de Maturidade (December 8, 2025)
Termos de maturidade FinOps traduzidos para Português do Brasil intuitivo:
- **Níveis renomeados**: CRAWL→"Nível 1", WALK→"Nível 2", RUN→"Nível 3", FLY→"Nível 4"
- **Títulos descritivos**: "Visibilidade de Custos", "Alocação e Controle", "Otimização Ativa", "Excelência Operacional"
- **Badge localizado**: CRAWL→"Iniciante", WALK→"Intermediário", RUN→"Avançado", FLY→"Excelência"
- **Descrições detalhadas**: Cada nível com explicação clara do que significa na prática
- **Backend atualizado**: API retorna `level_name` e `levels_info` com metadados localizados

### Mock Data Elimination (December 8, 2025)
All pages now use exclusively real API data with zero mock/hardcoded data:
- **Costs.tsx**: Removed Math.random, using real trends from API
- **Recommendations.tsx**: Removed RECOMMENDATION_TEMPLATES and getDemoRecommendations(), only API data
- **MultiRegion.tsx**: Updated parser for object format from API, useRef to prevent race conditions
- **Analytics.tsx**: Fixed getKpiStatus bug (inverted parameters), real maturity data from API
- **Settings.tsx**: Added localStorage persistence with STORAGE_KEY, TTL validation (1-1440 min)

### React Frontend Migration (Phase 1 Complete)
- **Frontend Architecture**: Migrated from inline HTML/CSS/JS to professional React + TypeScript + Vite
- **Design System**: Complete CSS Variables system with tokens for colors, typography, spacing, shadows
- **UI Components**: Button, Card, Badge, Alert, Skeleton, Table (all with accessibility features)
- **Layout System**: Sidebar navigation, Header with actions, responsive design
- **Dashboard Page**: Metrics cards, loading states, data tables, action buttons
- **API Integration**: Service layer with Vite proxy (port 5000→8000), custom hooks (useApi, useDashboard)
- **Accessibility**: Focus states, ARIA attributes, skip links, keyboard navigation

### Frontend Stack
- React 18 + TypeScript
- Vite 7 (dev server on port 5000)
- React Router DOM (client-side routing)
- Lucide React (icons)
- CSS Modules (scoped styles)

### New Services Implemented
- **CUR Ingestion Service** (`cur_ingestion_service.py`): Ingestão de dados CUR com reconciliação automática
- **Cost Allocation Service** (`cost_allocation_service.py`): Engine de alocação com scorecard por nível de maturidade
- **Showback/Chargeback Service** (`showback_chargeback_service.py`): Relatórios de showback e workflow de chargeback
- **Unit Economics Service** (`unit_economics_service.py`): Métricas de custo unitário por cliente/transação
- **Policy Automation Service** (`policy_automation_service.py`): Automação de políticas com aprovação
- **Real-Time Insights Service** (`realtime_insights_service.py`): Insights em tempo real com detecção de anomalias
- **Predictive Optimization Service** (`predictive_optimization_service.py`): Otimização preditiva com forecasting
- **FinOps Maturity Service** (`finops_maturity_service.py`): Avaliação de maturidade 4 níveis com OKRs

### Dashboard Integration
- **Full Integration Module** (`finops_full_integration.py`): Integração completa de todos os serviços no dashboard

### Cache System Updates
- Cache agora aceita `default_ttl` no construtor
- Método `set()` aceita parâmetro `ttl` como alternativa a `ttl_seconds`

## FinOps Compliance Status

- Nível 1 (Crawl): ~100% completo ✓
- Nível 2 (Walk): ~100% completo ✓
- Nível 3 (Run): ~100% completo ✓
- Nível 4 (Fly): ~100% completo ✓

### Compliance Details by Level

**CRAWL (100%)**
- ✓ Cost visibility via Cost Explorer
- ✓ CUR ingestion (S3/Athena ou fallback)
- ✓ Cost allocation scorecard ≥50%
- ✓ Basic tag governance

**WALK (100%)**
- ✓ Cost allocation engine com mapeamento de tags
- ✓ Showback reports por BU/projeto
- ✓ Commitment dashboard (RI/SP)
- ✓ Budget alerting integrado

**RUN (100%)**
- ✓ Unit Economics com métricas de negócio
- ✓ Chargeback workflow com invoices
- ✓ Policy automation orquestrada
- ✓ Forecasting com ±12% precisão

**FLY (100%)**
- ✓ Real-time insights <5 min latência
- ✓ Predictive optimization AI-driven
- ✓ FinOps culture artifacts (OKRs, scorecards)
- ✓ Automated AI consultant

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
    - AWS Athena (for CUR queries)
    - AWS S3 (for CUR storage)
    - boto3 (AWS SDK for Python)
- **AI Providers**:
    - OpenAI ChatGPT (via API)
    - Google Gemini (via API)
    - Perplexity AI (via API)
- **Python Libraries**:
    - Python 3.11
    - Flask (web dashboard)
- **Configuration**:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION
    - Q_BUSINESS_APPLICATION_ID (for Amazon Q Business)
    - OPENAI_API_KEY (for OpenAI ChatGPT)
    - GEMINI_API_KEY (for Google Gemini)
    - PERPLEXITY_API_KEY (for Perplexity AI)
    - CUR_DATABASE (optional, for Athena)
    - CUR_TABLE (optional, for Athena)
    - CUR_S3_BUCKET (optional, for CUR files)
