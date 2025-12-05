# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations across 246 AWS services (60% boto3 coverage - focused on high-impact services). It functions as an AWS Lambda application, providing comprehensive financial analysis, operational monitoring, and optimization insights. The solution includes an **Automated Financial Consultant powered by Multiple AI Providers** (Amazon Q Business, OpenAI ChatGPT, Google Gemini, Perplexity) for intelligent report generation.

## User Preferences

- Idioma de comunicação: Português do Brasil
- Perguntar antes de fazer suposições
- Seguir padrões Clean Architecture e DDD

## System Architecture

The system is built with Python 3.11, adhering to Clean Architecture and Domain-Driven Design (DDD) principles.

**Core Architecture:**
```
Web Dashboard → API Layer → Analysis Facade
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   Analyzers           Integrations            Cost Data
   Factory               Module                  Module
   (Strategy)              │                        │
        │                  ▼                        │
   6 Analyzers      AWS APIs + AI Providers         │
        │        ┌──────────────────────┐          │
        │        │ - Compute Optimizer  │          │
        │        │ - Cost Explorer RI   │          │
        │        │ - Trusted Advisor    │          │
        │        │ - AI Providers:      │          │
        │        │   * Amazon Q Business│          │
        │        │   * OpenAI ChatGPT   │          │
        │        │   * Google Gemini    │          │
        │        │   * Perplexity AI    │          │
        │        └──────────────────────┘          │
        └──────────────────┼────────────────────────┘
                           ▼
                 boto3 + AI SDK Clients
                           │
                           ▼
                  AWS Cloud + AI APIs
```

**Key Architectural Components:**
- **Analyzers (Strategy Pattern)**: 6 analyzers modulares (Compute, Storage, Database, Network, Security, Analytics)
- **AI Providers (Strategy Pattern)**: 4 provedores de IA intercambiáveis
- **Factory + Registry**: Criação dinâmica de analyzers e AI providers
- **Template Method**: Estrutura comum de análise
- **Facade**: API simplificada para o dashboard
- **Exception Hierarchy**: 15 tipos de exceções tipadas

## AI Consultant - Multi-Provider Architecture

### Provedores de IA Suportados

| Provedor | Modelo | API Key | Status | Características |
|----------|--------|---------|--------|-----------------|
| **Amazon Q Business** | Q Business | Não (IAM) | ⚠️ Não configurado | RAG nativo, segurança AWS |
| **OpenAI ChatGPT** | gpt-4o, gpt-4o-mini | Sim | ⚠️ Sem créditos | Alta precisão, grande contexto |
| **Google Gemini** | gemini-2.5-flash, gemini-2.5-pro | Sim | ✅ Testado | Contexto 2M, custo-benefício |
| **Perplexity AI** | sonar, sonar-pro | Sim | ✅ Testado | Busca online, citações |

### Uso Programático

```python
from finops_aws.ai_consultant.providers import AIProviderFactory, PersonaType

# Criar provedor específico
provider = AIProviderFactory.create("openai")

# Ou seleção automática
available = AIProviderFactory.create_all_available()

# Gerar relatório
response = provider.generate_report(costs, resources, PersonaType.EXECUTIVE)
print(response.content)
```

### Personas Disponíveis

| Persona | Audiência | Foco | Formato da Resposta |
|---------|-----------|------|---------------------|
| **EXECUTIVE** | CEO/CFO | ROI, tendências, decisões | 2 páginas, bullet points |
| **CTO** | CTO/VP Eng | Arquitetura, trade-offs | Roadmap, diagramas |
| **DEVOPS** | DevOps/SRE | Scripts, AWS CLI | Comandos copy-paste |
| **ANALYST** | FinOps | KPIs, métricas | Tabelas, benchmarks |

## Quality Metrics (Verified)

| Metric | Value | Details |
|--------|-------|---------|
| **Unit Tests** | 1,865 | 100% passing |
| **Integration Tests** | 44 | 42 passed, 2 skipped |
| **QA Tests** | 240 | 100% passing |
| **E2E Tests** | 55 | 100% passing |
| **Total Tests** | 2,204 | 100% passing |
| **AWS Services Suportados** | 246 | 60% boto3 coverage |
| **Verificações de Otimização** | 23 | Serviços com regras específicas |
| **Design Patterns** | 6 | Strategy, Factory, Template, Registry, Facade, Singleton |
| **Exception Types** | 15 | Hierarquia tipada |
| **AI Providers** | 4 | Amazon Q, OpenAI, Gemini, Perplexity |

## Key Documentation Files

| File | Description |
|------|-------------|
| `docs/TECHNICAL_GUIDE.md` | Guia técnico completo |
| `docs/AI_PROVIDERS_GUIDE.md` | Guia de provedores de IA |
| `docs/PROMPTS_AMAZON_Q.md` | Prompts detalhados do Amazon Q |
| `docs/USER_MANUAL.md` | Manual do usuário |
| `docs/HEAD_FIRST_FINOPS.md` | Guia executivo FinOps |
| `docs/ARCHITECTURE_AND_PATTERNS.md` | Design Patterns aplicados |
| `docs/ROADMAP.md` | Roadmap e gaps conhecidos |

## AWS Integrations (Implemented)

| Integração | Função | Requisitos |
|------------|--------|------------|
| **Analyzers** | 6 analyzers modulares | Nenhum |
| **AWS Compute Optimizer** | Right-sizing EC2 | Opt-in habilitado |
| **AWS Cost Explorer** | RI e Savings Plans | Dados de uso |
| **AWS Trusted Advisor** | Verificações de custo | Business/Enterprise |
| **Amazon Q Business** | Análise com IA | Q_BUSINESS_APPLICATION_ID |
| **OpenAI ChatGPT** | Análise com IA | OPENAI_API_KEY |
| **Google Gemini** | Análise com IA | GEMINI_API_KEY |
| **Perplexity AI** | Análise com IA + busca | PERPLEXITY_API_KEY |

## Verificações de Otimização (23 serviços)

- **EC2**: Instâncias paradas, tipos antigos
- **EBS**: Volumes órfãos não anexados
- **EIP**: Elastic IPs não associados ($3.60/mês)
- **NAT Gateway**: Alertas de custo (~$32/mês)
- **S3**: Versionamento, lifecycle, encryption
- **RDS**: Multi-AZ em dev, dimensionamento
- **DynamoDB**: Billing mode
- **ELB/ALB**: Load balancers sem targets
- **CloudWatch**: Log groups sem retenção
- **ECR**: Imagens sem tag
- **IAM**: Access keys inativas

## Configuration

```bash
# Credenciais AWS (obrigatório)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Amazon Q Business (opcional)
Q_BUSINESS_APPLICATION_ID=seu-app-id

# OpenAI ChatGPT (opcional)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # opcional, default: gpt-4o

# Google Gemini (opcional)
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.5-flash  # opcional

# Perplexity AI (opcional)
PERPLEXITY_API_KEY=pplx-...
PERPLEXITY_MODEL=sonar  # opcional, default: sonar (sonar-pro tem bugs conhecidos)
```

## AI Providers Directory Structure

```
src/finops_aws/ai_consultant/
├── providers/
│   ├── __init__.py          # Exports públicos
│   ├── base_provider.py     # BaseAIProvider (ABC)
│   ├── provider_factory.py  # AIProviderFactory + Registry
│   ├── amazon_q_provider.py # Amazon Q Business
│   ├── openai_provider.py   # OpenAI ChatGPT
│   ├── gemini_provider.py   # Google Gemini
│   └── perplexity_provider.py # Perplexity AI
└── ...
```

## Recent Changes (December 2024)

- **Correções de Prompts e Idioma (Dec 5 - MAIS RECENTE)**:
  - Prompts atualizados para garantir respostas 100% em Português do Brasil
  - Relatórios agora são EXTREMAMENTE detalhados com dados, justificativas e cálculos
  - Cada recomendação inclui: Por que, Como implementar, Preços AWS, ROI esperado, Risco
  - Perplexity: Modelo padrão alterado de sonar-pro para sonar (sonar-pro tem bugs de resposta incompleta)
  - Gemini: Funcionando com relatórios de ~8.300 caracteres em ~20s
  - Perplexity: Funcionando com relatórios de ~9.900 caracteres em ~28s

- **Testes Multi-IA Validados (Dec 5)**:
  - Perplexity: ✅ Testado com sonar (9.896 chars, 28s, busca online)
  - Gemini: ✅ Testado com gemini-2.5-flash (8.319 chars, 20s)
  - OpenAI: ⚠️ Requer créditos em platform.openai.com/account/billing
  - Amazon Q: ⚠️ Requer Q_BUSINESS_APPLICATION_ID

- **Correções de Provedores (Dec 5)**:
  - Perplexity: Modelo padrão alterado para "sonar" (sonar-pro retorna respostas incompletas)
  - Perplexity: Modelos suportados: sonar, sonar-pro, sonar-reasoning
  - Gemini: Configurações de segurança ajustadas (BLOCK_NONE)
  - Gemini: Suporte dual para GEMINI_API_KEY e GOOGLE_API_KEY
  - Gemini: Tratamento robusto de respostas bloqueadas

- **Suporte Multi-IA (Dec 5)**:
  - Implementado Strategy Pattern para AI providers
  - Adicionado OpenAI ChatGPT (GPT-4o)
  - Adicionado Google Gemini (2.5)
  - Adicionado Perplexity AI (com busca online)
  - Factory + Registry para seleção dinâmica
  - Documentação AI_PROVIDERS_GUIDE.md

- **Documentação Atualizada (Dec 5)**:
  - TECHNICAL_GUIDE.md com arquitetura completa
  - PROMPTS_AMAZON_Q.md com exemplos de resposta
  - USER_MANUAL.md simplificado
  - HEAD_FIRST_FINOPS.md para executivos
  - ARCHITECTURE_AND_PATTERNS.md com Design Patterns
  - ROADMAP.md com status atual

- **Refatoração Arquitetural (Dec 5)**:
  - Strategy Pattern para 6 analyzers
  - Factory + Registry Pattern
  - Template Method em BaseAnalyzer
  - Hierarquia de exceções tipadas (15 tipos)

- **Integrações AWS (Dec 5)**:
  - Compute Optimizer
  - Cost Explorer RI/SP
  - Trusted Advisor
  - Amazon Q Business
