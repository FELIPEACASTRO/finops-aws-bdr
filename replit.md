# FinOps AWS - AWS Lambda Cost Optimization Solution

## Overview

FinOps AWS is an enterprise-grade serverless solution for intelligent AWS cost analysis, usage monitoring, and optimization recommendations across 246 AWS services (60% boto3 coverage - focused on high-impact services). It functions as an AWS Lambda application, providing comprehensive financial analysis, operational monitoring, and optimization insights. The solution includes an Automated Financial Consultant powered by Amazon Q Business for intelligent report generation.

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
   6 Analyzers      AWS APIs:                       │
        │        - Compute Optimizer               │
        │        - Cost Explorer RI                │
        │        - Trusted Advisor                 │
        │        - Amazon Q Business               │
        │                  │                        │
        └──────────────────┼────────────────────────┘
                           ▼
                     boto3 Clients
                           │
                           ▼
                      AWS Cloud
```

**Key Architectural Components:**
- **Analyzers (Strategy Pattern)**: 6 analyzers modulares (Compute, Storage, Database, Network, Security, Analytics)
- **Factory + Registry**: Criação dinâmica de analyzers
- **Template Method**: Estrutura comum de análise
- **Facade**: API simplificada para o dashboard
- **Exception Hierarchy**: 15 tipos de exceções tipadas

**AI Consultant (Amazon Q Business)**:
- 4 personas: EXECUTIVE, CTO, DEVOPS, ANALYST
- Prompts especializados para cada audiência
- Respostas em Português do Brasil
- Integração via `Q_BUSINESS_APPLICATION_ID`

## Amazon Q Business - Prompts e Respostas

### Personas Disponíveis

| Persona | Audiência | Foco | Formato da Resposta |
|---------|-----------|------|---------------------|
| **EXECUTIVE** | CEO/CFO | ROI, tendências, decisões | 2 páginas, bullet points |
| **CTO** | CTO/VP Eng | Arquitetura, trade-offs | Roadmap, diagramas |
| **DEVOPS** | DevOps/SRE | Scripts, AWS CLI | Comandos copy-paste |
| **ANALYST** | FinOps | KPIs, métricas | Tabelas, benchmarks |

### Estrutura do Prompt

```markdown
## Contexto do Sistema
Você é um consultor senior de FinOps especializado em AWS...

## Dados de Custo AWS
**Custo Total (30 dias):** $X.XX
**Top Serviços:** [lista com valores]

## Recursos AWS Ativos
- ec2_instances: X
- s3_buckets: Y
- rds_instances: Z

## Instruções
[Template específico da persona]
```

### Exemplo de Resposta (EXECUTIVE)

```markdown
# Relatório Executivo FinOps

## Resumo Executivo
O custo total foi de **$0.15**, distribuído entre RDS (95%) e S3 (3%).

## Top 3 Oportunidades
| # | Oportunidade | Economia/Mês |
|---|--------------|--------------|
| 1 | Versionamento S3 | $0 (governança) |
| 2 | Lifecycle policies | $0-5 |
| 3 | Dimensionamento RDS | TBD |

## Próximos Passos
1. Habilitar versionamento S3 (esta semana)
2. Implementar lifecycle policies (2 semanas)
3. Revisar utilização RDS (este mês)
```

### Exemplo de Resposta (CTO)

```markdown
# Relatório Técnico FinOps

## Distribuição de Recursos
| Categoria | Custo/Mês | % Total |
|-----------|-----------|---------|
| Database | $0.14 | 95% |
| Storage | $0.004 | 3% |

## Roadmap de Modernização
**Fase 1 (0-30d)**: Lifecycle policies S3
**Fase 2 (30-90d)**: Avaliar Aurora Serverless
**Fase 3 (90-180d)**: FinOps as Code
```

### Exemplo de Resposta (DEVOPS)

```markdown
# Relatório Operacional

## Ações Imediatas

### 1. Habilitar Versionamento S3
```bash
aws s3api put-bucket-versioning \
  --bucket meu-bucket \
  --versioning-configuration Status=Enabled
```

### 2. Criar Lifecycle Policy
```bash
cat > lifecycle.json << 'EOF'
{
  "Rules": [{"ID": "TransitionToIA", "Status": "Enabled", ...}]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket meu-bucket \
  --lifecycle-configuration file://lifecycle.json
```

### Exemplo de Resposta (ANALYST)

```markdown
# Relatório Analítico FinOps

## Dashboard de Métricas
| KPI | Valor | Meta | Status |
|-----|-------|------|--------|
| Custo Total | $0.15 | $10 | 🟢 |
| Cobertura RI/SP | 0% | 70% | 🔴 |
| Waste Ratio | 0% | <5% | 🟢 |

## Análise por Serviço
| Serviço | Custo | % Total | Tendência |
|---------|-------|---------|-----------|
| RDS | $0.14 | 95% | ➡️ Estável |
| S3 | $0.004 | 3% | ➡️ Estável |
```

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
| **Design Patterns** | 5 | Strategy, Factory, Template, Registry, Facade |
| **Exception Types** | 15 | Hierarquia tipada |

## Key Documentation Files

| File | Description |
|------|-------------|
| `docs/TECHNICAL_GUIDE.md` | Guia técnico completo |
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
```

## Recent Changes (December 2024)

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
