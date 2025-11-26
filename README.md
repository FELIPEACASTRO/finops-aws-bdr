# FinOps AWS BDR - Solução Avançada de Otimização de Custos AWS

Uma solução **serverless empresarial** em Python para análise inteligente de custos, monitoramento de uso e recomendações de otimização na AWS. Implementada com **arquitetura limpa**, **padrões de design robustos** e **observabilidade completa**.

## 🎯 Visão Geral da Solução

Esta solução FinOps (Financial Operations) utiliza **AWS Lambda** como núcleo de processamento para automatizar a coleta, análise e consolidação de dados financeiros e operacionais da AWS, fornecendo:

### 📊 **Análise Financeira Inteligente**
- **Custos Multi-Período**: Análise detalhada de custos por serviço AWS (7, 15 e 30 dias)
- **Análise de Tendências**: Identificação automática de padrões de crescimento/redução de custos
- **Distribuição de Gastos**: Categorização e percentuais de custos por serviço
- **Top Services**: Ranking dos serviços mais caros com análise de impacto financeiro

### 📈 **Monitoramento Operacional**
- **Métricas de Performance**: Coleta de métricas de CPU, memória, invocações e erros
- **Análise de Utilização**: Identificação de recursos subutilizados ou sobrecarregados
- **Health Checks**: Monitoramento de saúde de recursos EC2 e Lambda
- **Alertas Proativos**: Detecção de anomalias de uso e performance

### 🎯 **Otimização Baseada em IA**
- **AWS Compute Optimizer**: Integração nativa com recomendações da AWS
- **Right-Sizing**: Sugestões de redimensionamento com cálculo de economia
- **ROI Analysis**: Análise de retorno sobre investimento para otimizações
- **Action Plans**: Planos de ação priorizados por impacto financeiro

### 📋 **Relatórios Executivos**
- **Executive Dashboard**: Resumos executivos com KPIs principais
- **Savings Opportunities**: Oportunidades de economia categorizadas
- **Cost Optimization Roadmap**: Roadmap de otimização com timeline
- **Compliance Reports**: Relatórios para auditoria e compliance

## 🏗️ Arquitetura da Solução

### Arquitetura de Alto Nível
```
                    ┌─────────────────────────────────────────┐
                    │           FINOPS AWS SOLUTION           │
                    │         (Serverless Architecture)       │
                    └─────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌─────────────────┐            ┌──────────────────┐            ┌─────────────────┐
│   EventBridge   │            │  API Gateway     │            │   CloudWatch    │
│   (Scheduler)   │            │  (REST API)      │            │   (Dashboard)   │
│                 │            │                  │            │                 │
│ • Daily Exec    │            │ • HTTP Access    │            │ • Metrics       │
│ • Custom Cron   │            │ • Auth Support   │            │ • Logs          │
│ • Multi-trigger │            │ • Rate Limiting  │            │ • Alarms        │
└─────────────────┘            └──────────────────┘            └─────────────────┘
        │                               │                               ▲
        └───────────────┐               │               ┌───────────────┘
                        │               │               │
                        ▼               ▼               │
                    ┌─────────────────────────────────────────┐
                    │         AWS LAMBDA FUNCTION             │
                    │        (Python 3.11 Runtime)           │
                    │                                         │
                    │  ┌─────────────────────────────────┐    │
                    │  │        FINOPS CORE ENGINE       │    │
                    │  │                                 │    │
                    │  │  • Cost Analysis Service        │    │
                    │  │  • Metrics Collection Service   │    │
                    │  │  • Optimization Service         │    │
                    │  │  • Report Generation Engine     │    │
                    │  │  • Error Handling & Retry       │    │
                    │  └─────────────────────────────────┘    │
                    └─────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌─────────────────┐            ┌──────────────────┐            ┌─────────────────┐
│ Cost Explorer   │            │   CloudWatch     │            │Compute Optimizer│
│                 │            │                  │            │                 │
│ • Cost Data     │            │ • EC2 Metrics    │            │ • EC2 Recommendations│
│ • Usage Reports │            │ • Lambda Metrics │            │ • Lambda Optimization│
│ • Multi-period  │            │ • Custom Metrics │            │ • EBS Recommendations│
│ • Service Costs │            │ • Performance    │            │ • Auto Scaling Tips  │
└─────────────────┘            └──────────────────┘            └─────────────────┘
```

### Arquitetura de Software (Clean Architecture + Domain-Driven Design)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           🔧 INFRASTRUCTURE LAYER                           │
│                        (External Systems & Frameworks)                     │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐ │
│  │   AWS Services  │  │   CloudWatch    │  │ Cost Explorer   │  │  Boto3  │ │
│  │                 │  │                 │  │                 │  │   SDK   │ │
│  │ • EC2 Client    │  │ • Metrics API   │  │ • Cost API      │  │ • Retry │ │
│  │ • Lambda Client │  │ • Log Groups    │  │ • Usage API     │  │ • Auth  │ │
│  │ • STS Client    │  │ • Dashboards    │  │ • Billing API   │  │ • Error │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │ (Dependency Injection)
                                        │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            🌐 INTERFACE LAYER                              │
│                           (Controllers & Adapters)                         │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐ │
│  │ Lambda Handler  │  │   API Gateway   │  │   EventBridge   │  │  JSON   │ │
│  │                 │  │                 │  │                 │  │ Logger  │ │
│  │ • Entry Point   │  │ • REST Adapter  │  │ • Event Adapter │  │ • Struct│ │
│  │ • Error Handler │  │ • Auth Handler  │  │ • Cron Trigger  │  │ • Format│ │
│  │ • Response      │  │ • CORS Support  │  │ • Schedule Mgmt │  │ • Filter│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │ (Use Case Orchestration)
                                        │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          🎯 APPLICATION LAYER                              │
│                         (Use Cases & Orchestration)                        │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐ │
│  │   Use Cases     │  │      DTOs       │  │   Strategies    │  │ Service │ │
│  │                 │  │                 │  │                 │  │ Layer   │ │
│  │ • Analyze Costs │  │ • Cost Analysis │  │ • Cost Strategy │  │ • Cost  │ │
│  │ • Collect Usage │  │ • Usage Report  │  │ • Usage Strategy│  │ • Metric│ │
│  │ • Generate Recs │  │ • Optimization  │  │ • Optim Strategy│  │ • Optim │ │
│  │ • Create Report │  │ • Executive Sum │  │ • Report Builder│  │ • Report│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │ (Business Rules & Entities)
                                        │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            🏛️ DOMAIN LAYER                                 │
│                          (Core Business Logic)                             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐ │
│  │    Entities     │  │ Value Objects   │  │ Domain Services │  │ Repos   │ │
│  │                 │  │                 │  │                 │  │ (Interf)│ │
│  │ • CostEntity    │  │ • Money         │  │ • Cost Rules    │  │ • Cost  │ │
│  │ • UsageEntity   │  │ • TimePeriod    │  │ • Usage Rules   │  │ • Usage │ │
│  │ • OptimEntity   │  │ • ServiceName   │  │ • Optim Rules   │  │ • Optim │ │
│  │ • ReportEntity  │  │ • ResourceType  │  │ • Report Rules  │  │ • Report│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Princípios Arquiteturais Implementados

#### 🎯 **Clean Architecture**
- **Separação de Responsabilidades**: Cada camada tem responsabilidades bem definidas
- **Inversão de Dependências**: Camadas internas não dependem de camadas externas
- **Testabilidade**: Cada camada pode ser testada independentemente
- **Flexibilidade**: Mudanças em uma camada não afetam outras

#### 🏛️ **Domain-Driven Design (DDD)**
- **Entities**: Objetos com identidade e ciclo de vida (CostEntity, UsageEntity)
- **Value Objects**: Objetos imutáveis sem identidade (Money, TimePeriod)
- **Domain Services**: Lógica de negócio que não pertence a entidades
- **Repository Pattern**: Abstração para acesso a dados

#### 🔧 **SOLID Principles**
- **Single Responsibility**: Cada classe tem uma única responsabilidade
- **Open/Closed**: Extensível para novos recursos sem modificar código existente
- **Liskov Substitution**: Subtipos podem substituir tipos base
- **Interface Segregation**: Interfaces específicas ao invés de genéricas
- **Dependency Inversion**: Dependências de abstrações, não implementações

## 🚀 Funcionalidades Avançadas

### 📊 **Análise Financeira Inteligente**

#### 💰 **Multi-Period Cost Analysis**
- **Períodos Configuráveis**: Análise de custos para 7, 15 e 30 dias
- **Granularidade Diária**: Coleta de dados com granularidade diária para precisão
- **Agregação por Serviço**: Custos organizados por serviço AWS
- **Moeda Padronizada**: Todos os valores em USD com precisão decimal
- **Filtros Automáticos**: Remove serviços com custo < $0.01 para reduzir ruído

#### 📈 **Trend Analysis Engine**
- **Padrões Automáticos**: Detecção de tendências INCREASING/DECREASING/STABLE
- **Análise Comparativa**: Comparação entre períodos para identificar mudanças
- **Alertas de Anomalias**: Identificação de picos ou quedas anômalas de custo
- **Projeções**: Estimativas de custos futuros baseadas em tendências históricas

#### 🏆 **Top Services Ranking**
- **Ranking Dinâmico**: Classificação dos serviços por custo e impacto
- **Análise Percentual**: Distribuição percentual de custos por serviço
- **Categorização**: Agrupamento de serviços por categoria (Compute, Storage, etc.)
- **Impact Analysis**: Análise de impacto financeiro de cada serviço

### 📈 **Monitoramento Operacional Avançado**

#### 🖥️ **EC2 Performance Analytics**
- **CPU Utilization**: Monitoramento de utilização de CPU multi-período
- **Resource Efficiency**: Identificação de instâncias subutilizadas (<20% CPU)
- **Instance Profiling**: Análise por tipo de instância e zona de disponibilidade
- **State Management**: Monitoramento de estado (running, stopped, terminated)
- **Cost-Performance Correlation**: Correlação entre custo e performance

#### ⚡ **Lambda Operational Insights**
- **Invocation Analytics**: Análise detalhada de invocações por função
- **Performance Metrics**: Duração média, erros e throttles
- **Reliability Scoring**: Score de confiabilidade baseado em métricas
- **Active vs Inactive**: Identificação de funções ativas vs dormentes
- **Cost Optimization**: Análise de custo-benefício por função

#### 📊 **Custom Metrics Collection**
- **Multi-Source Data**: Coleta de métricas de CloudWatch, Cost Explorer e Compute Optimizer
- **Real-time Processing**: Processamento em tempo real com cache inteligente
- **Data Validation**: Validação e sanitização automática de dados
- **Error Handling**: Tratamento robusto de erros com retry automático

### 🎯 **Otimização Baseada em Machine Learning**

#### 🤖 **AWS Compute Optimizer Integration**
- **Native AI Recommendations**: Integração com recomendações nativas da AWS
- **Multi-Resource Support**: Suporte para EC2, Lambda, EBS e Auto Scaling
- **Confidence Scoring**: Score de confiança para cada recomendação
- **Historical Analysis**: Análise baseada em dados históricos de 14+ dias

#### 💡 **Intelligent Right-Sizing**
- **EC2 Optimization**: Recomendações de redimensionamento com economia estimada
- **Lambda Memory Optimization**: Otimização de memória e configuração
- **EBS Volume Optimization**: Recomendações para volumes EBS
- **Auto Scaling Optimization**: Otimização de grupos de Auto Scaling

#### 📊 **ROI Analysis Engine**
- **Savings Calculation**: Cálculo preciso de economia mensal estimada
- **Implementation Cost**: Análise de custo de implementação das recomendações
- **Risk Assessment**: Avaliação de riscos de cada otimização
- **Priority Matrix**: Matriz de priorização baseada em impacto vs esforço

#### 🏷️ **Finding Classification System**
- **OVER_PROVISIONED**: Recursos com capacidade excessiva
- **UNDER_PROVISIONED**: Recursos com capacidade insuficiente
- **OPTIMIZED**: Recursos já otimizados
- **NOT_OPTIMIZED**: Recursos que podem ser otimizados
- **INSUFFICIENT_DATA**: Recursos sem dados suficientes para análise

### 📋 **Relatórios Executivos e Dashboards**

#### 📊 **Executive Summary Dashboard**
- **KPI Overview**: Visão geral dos principais indicadores financeiros
- **Cost Trends**: Tendências de custo com visualizações gráficas
- **Savings Opportunities**: Oportunidades de economia categorizadas
- **Action Items**: Itens de ação priorizados por impacto

#### 📈 **Detailed Analytics Reports**
- **Service-Level Analysis**: Análise detalhada por serviço AWS
- **Resource Utilization**: Relatórios de utilização de recursos
- **Performance Benchmarks**: Benchmarks de performance por categoria
- **Compliance Reports**: Relatórios para auditoria e compliance

#### 🎯 **Optimization Roadmap**
- **Phased Implementation**: Plano de implementação em fases
- **Timeline Estimates**: Estimativas de timeline para cada otimização
- **Resource Requirements**: Recursos necessários para implementação
- **Success Metrics**: Métricas de sucesso para cada otimização

### 🔍 **Observabilidade e Monitoramento**

#### 📝 **Structured Logging**
- **JSON Format**: Logs estruturados em formato JSON
- **Contextual Information**: Informações contextuais ricas
- **Performance Metrics**: Métricas de performance integradas
- **Error Tracking**: Rastreamento detalhado de erros

#### 📊 **CloudWatch Integration**
- **Custom Dashboards**: Dashboards personalizados no CloudWatch
- **Automated Alerts**: Alertas automáticos baseados em métricas
- **Log Analysis**: Análise avançada de logs com queries personalizadas
- **Performance Monitoring**: Monitoramento contínuo de performance

## 🛠️ Stack Tecnológico

### Core Technologies
- **Runtime**: Python 3.11 com type hints completos
- **Cloud Platform**: AWS (Lambda, CloudWatch, Cost Explorer, Compute Optimizer)
- **Infrastructure as Code**: CloudFormation com parâmetros configuráveis
- **Testing Framework**: pytest + moto para mocking AWS

### Architecture Patterns
- **Domain-Driven Design (DDD)**: Entities, Value Objects, Domain Services
- **Clean Architecture**: Separação clara de responsabilidades em camadas
- **SOLID Principles**: Código extensível e manutenível
- **Strategy Pattern**: Análises plugáveis e extensíveis
- **Repository Pattern**: Abstração de acesso a dados

### Quality & Observability
- **Structured Logging**: JSON logs com contexto rico
- **Error Handling**: Retry com backoff exponencial
- **Monitoring**: CloudWatch Dashboard automático
- **Type Safety**: Mypy-compatible type annotations

## 📦 Estrutura do Projeto (Clean Architecture + DDD)

```
finops-aws-bdr/
├── src/finops_aws/
│   ├── domain/                    # 🏛️ DOMAIN LAYER (Core Business Logic)
│   │   ├── entities/
│   │   │   └── cost_entity.py            # Rich domain entities
│   │   ├── value_objects/
│   │   │   ├── money.py                  # Money value object with precision
│   │   │   ├── time_period.py            # Time period abstraction
│   │   │   └── service_name.py           # AWS service name with categories
│   │   ├── repositories/
│   │   │   └── cost_repository.py        # Repository interfaces
│   │   └── services/
│   │       └── domain_services.py        # Domain business rules
│   │
│   ├── application/               # 🎯 APPLICATION LAYER (Use Cases)
│   │   ├── use_cases/
│   │   │   └── analyze_costs_use_case.py # Main business use case
│   │   ├── dto/
│   │   │   └── cost_analysis_dto.py      # Data transfer objects
│   │   └── interfaces/
│   │       └── logger_interface.py       # Application interfaces
│   │
│   ├── infrastructure/            # 🔧 INFRASTRUCTURE LAYER (External Concerns)
│   │   └── services/
│   │       ├── aws_cost_repository.py    # AWS Cost Explorer implementation
│   │       └── aws_metrics_service.py    # CloudWatch implementation
│   │
│   ├── interfaces/                # 🌐 INTERFACE LAYER (Controllers)
│   │   └── lambda_handler.py             # AWS Lambda entry point
│   │
│   ├── services/                  # 📊 LEGACY SERVICES (Refactoring in progress)
│   │   ├── cost_service.py               # Cost Explorer service
│   │   ├── metrics_service.py            # CloudWatch metrics service
│   │   └── optimizer_service.py          # Compute Optimizer service
│   │
│   ├── models/                    # 📋 DATA MODELS (DTOs)
│   │   └── finops_models.py              # Data transfer models
│   │
│   └── utils/                     # 🛠️ SHARED UTILITIES
│       ├── logger.py                     # Structured JSON logging
│       └── aws_helpers.py                # AWS SDK helpers with retry logic
│
├── tests/                         # 🧪 COMPREHENSIVE TEST SUITE
│   ├── unit/                             # Unit tests with mocking
│   │   ├── test_cost_service.py
│   │   ├── test_metrics_service.py
│   │   └── test_optimizer_service.py
│   ├── integration/                      # Integration tests (future)
│   └── fixtures/                         # Test data fixtures
│
├── infrastructure/                # 🏗️ INFRASTRUCTURE AS CODE
│   └── cloudformation-template.yaml     # Complete AWS stack definition
│
├── example_events/                # 📝 SAMPLE DATA
│   ├── api_gateway_event.json           # API Gateway test event
│   └── scheduled_event.json             # EventBridge test event
│
├── deploy.sh                      # 🚀 AUTOMATED DEPLOYMENT SCRIPT
├── requirements.txt               # 📦 Python dependencies
├── pytest.ini                    # 🧪 Test configuration
├── .env.example                   # 🔐 Environment variables template
└── README.md                      # 📖 This documentation
```

### Arquitetura em Camadas

#### 🏛️ Domain Layer (Núcleo do Negócio)
- **Entities**: `CostEntity` com lógica de negócio rica
- **Value Objects**: `Money`, `TimePeriod`, `ServiceName` com validações
- **Domain Services**: Regras de negócio complexas
- **Repository Interfaces**: Contratos para acesso a dados

#### 🎯 Application Layer (Casos de Uso)
- **Use Cases**: `AnalyzeCostsUseCase` com Strategy Pattern
- **DTOs**: Objetos de transferência de dados
- **Application Services**: Orquestração de casos de uso

#### 🔧 Infrastructure Layer (Detalhes Técnicos)
- **AWS Services**: Implementações concretas dos repositórios
- **External APIs**: Integração com Cost Explorer, CloudWatch
- **Persistence**: (Future) DynamoDB para histórico

#### 🌐 Interface Layer (Pontos de Entrada)
- **Lambda Handler**: Controlador principal
- **API Gateway**: Interface REST (opcional)
- **EventBridge**: Trigger agendado

## 🔧 Instalação e Configuração

### Pré-requisitos

1. **AWS CLI** configurado com credenciais adequadas
2. **Python 3.11+**
3. **Bucket S3** para deploy do código
4. **Permissões IAM** necessárias (veja seção de Permissões)

### Deploy Rápido

```bash
# Clone o repositório
git clone <repository-url>
cd finops-aws-bdr

# Instale dependências
pip install -r requirements.txt

# Execute testes
python -m pytest tests/ -v

# Deploy na AWS
./deploy.sh -b SEU_BUCKET_S3
```

### Deploy Personalizado

```bash
# Deploy com configurações específicas
./deploy.sh \
  --stack-name finops-prod \
  --function-name finops-analyzer \
  --region us-west-2 \
  --bucket meu-bucket-deploy \
  --log-level DEBUG
```

### Opções do Deploy

| Parâmetro | Descrição | Padrão |
|-----------|-----------|---------|
| `--stack-name` | Nome da stack CloudFormation | `finops-aws-stack` |
| `--function-name` | Nome da função Lambda | `finops-aws-analyzer` |
| `--region` | Região AWS | `us-east-1` |
| `--bucket` | Bucket S3 para código | **obrigatório** |
| `--log-level` | Nível de log | `INFO` |
| `--no-schedule` | Desabilitar execução agendada | - |
| `--no-api` | Não criar API Gateway | - |
| `--update-only` | Apenas atualizar código | - |

## 🔐 Permissões IAM Necessárias

A função Lambda precisa das seguintes permissões:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "ec2:DescribeInstances",
        "lambda:ListFunctions",
        "compute-optimizer:GetEC2InstanceRecommendations",
        "compute-optimizer:GetLambdaFunctionRecommendations",
        "compute-optimizer:GetEnrollmentStatus",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🧪 Execução Local

### Teste Básico
```bash
# Configure credenciais AWS
aws configure

# Execute localmente
python -m src.finops_aws.lambda_handler
```

### Com Variáveis de Ambiente
```bash
export LOG_LEVEL=DEBUG
export AWS_DEFAULT_REGION=us-east-1
python -m src.finops_aws.lambda_handler
```

## 📊 Exemplo de Resposta Detalhada

### Resposta Completa da API
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "X-Request-ID": "abc123-def456-ghi789"
  },
  "body": {
    "account_id": "123456789012",
    "generated_at": "2025-01-26T10:00:00Z",

    "costs": {
      "last_7_days": {
        "Amazon Elastic Compute Cloud - Compute": 123.45,
        "Amazon Simple Storage Service": 12.34,
        "AWS Lambda": 8.90,
        "Amazon CloudWatch": 5.67
      },
      "last_15_days": {
        "Amazon Elastic Compute Cloud - Compute": 267.89,
        "Amazon Simple Storage Service": 24.68,
        "AWS Lambda": 17.80,
        "Amazon CloudWatch": 11.34
      },
      "last_30_days": {
        "Amazon Elastic Compute Cloud - Compute": 534.21,
        "Amazon Simple Storage Service": 49.36,
        "AWS Lambda": 35.60,
        "Amazon CloudWatch": 22.68
      }
    },

    "usage": {
      "ec2": [
        {
          "instance_id": "i-0123456789abcdef0",
          "instance_type": "t3.xlarge",
          "state": "running",
          "availability_zone": "us-east-1a",
          "avg_cpu_7d": 27.3,
          "avg_cpu_15d": 29.1,
          "avg_cpu_30d": 30.0
        },
        {
          "instance_id": "i-0987654321fedcba0",
          "instance_type": "m5.large",
          "state": "running",
          "availability_zone": "us-east-1b",
          "avg_cpu_7d": 85.7,
          "avg_cpu_15d": 82.4,
          "avg_cpu_30d": 79.8
        }
      ],
      "lambda": [
        {
          "function_name": "data-processor",
          "invocations_7d": 1500,
          "avg_duration_7d": 245.2,
          "errors_7d": 3,
          "throttles_7d": 0
        },
        {
          "function_name": "api-handler",
          "invocations_7d": 8750,
          "avg_duration_7d": 89.5,
          "errors_7d": 12,
          "throttles_7d": 2
        }
      ]
    },

    "optimizer": {
      "ec2_recommendations": [
        {
          "resource_id": "i-0123456789abcdef0",
          "resource_type": "EC2",
          "current_configuration": "t3.xlarge",
          "recommended_configurations": ["t3.large", "t3.medium"],
          "estimated_monthly_savings": 45.67,
          "finding": "OVER_PROVISIONED",
          "utilization_metrics": {
            "cpu_utilization": 30.0,
            "memory_utilization": 42.5
          }
        }
      ],
      "lambda_recommendations": [
        {
          "resource_id": "data-processor",
          "resource_type": "Lambda",
          "current_configuration": "512MB",
          "recommended_configurations": ["256MB"],
          "estimated_monthly_savings": 12.34,
          "finding": "OVER_PROVISIONED",
          "utilization_metrics": {
            "memory_utilization": 35.2,
            "duration_average": 245.2
          }
        }
      ]
    },

    "summary": {
      "total_estimated_monthly_savings": 158.01,

      "cost_analysis": {
        "total_cost_last_30_days": 641.85,
        "top_5_services": [
          {
            "service": "Amazon Elastic Compute Cloud - Compute",
            "cost": 534.21,
            "percentage": 83.2
          },
          {
            "service": "Amazon Simple Storage Service",
            "cost": 49.36,
            "percentage": 7.7
          },
          {
            "service": "AWS Lambda",
            "cost": 35.60,
            "percentage": 5.5
          },
          {
            "service": "Amazon CloudWatch",
            "cost": 22.68,
            "percentage": 3.5
          }
        ]
      },

      "usage_insights": {
        "ec2": {
          "total_instances": 2,
          "running_instances": 2,
          "low_utilization_instances": 1,
          "avg_cpu_utilization_30d": 54.9
        },
        "lambda": {
          "total_functions": 2,
          "active_functions_7d": 2,
          "total_invocations_7d": 10250,
          "total_errors_7d": 15
        }
      },

      "optimization_opportunities": [
        {
          "finding": "OVER_PROVISIONED",
          "resource_count": 2,
          "estimated_monthly_savings": 158.01
        }
      ]
    },

    "metadata": {
      "analysis_duration_seconds": 12.45,
      "services_analyzed": 4,
      "recommendations_found": 2,
      "data_sources": ["Cost Explorer", "CloudWatch", "Compute Optimizer"]
    }
  }
}
```

### Estrutura de Dados Tipada (Domain Models)

```python
# Domain Entity Example
@dataclass(frozen=True)
class CostEntity:
    account_id: str
    service_costs: Dict[ServiceName, Dict[TimePeriod, Money]]
    analysis_date: datetime

    def get_total_cost_for_period(self, period: TimePeriod) -> Money:
        # Rich domain behavior with business logic

    def calculate_cost_trend(self, service: ServiceName) -> str:
        # Domain-specific trend analysis

# Value Object Example
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __add__(self, other: 'Money') -> 'Money':
        # Type-safe monetary operations
```

## 🔄 Uso da API

Se habilitada, a API Gateway fornece acesso HTTP:

```bash
# GET request para análise
curl https://api-id.execute-api.region.amazonaws.com/prod/analyze

# Com autenticação (se configurada)
curl -H "Authorization: Bearer TOKEN" \
     https://api-id.execute-api.region.amazonaws.com/prod/analyze
```

## 📅 Execução Agendada

Por padrão, a função executa diariamente via EventBridge:
- **Agendamento**: `rate(1 day)` (configurável)
- **Logs**: CloudWatch Logs `/aws/lambda/function-name`
- **Dashboard**: CloudWatch Dashboard automático

## 🧪 Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python -m pytest tests/unit/test_cost_service.py -v

# Com cobertura
python -m pytest tests/ --cov=src --cov-report=html
```

## 🔍 Monitoramento

### CloudWatch Logs
```bash
# Visualizar logs
aws logs tail /aws/lambda/finops-aws-analyzer --follow

# Filtrar erros
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-aws-analyzer \
  --filter-pattern "ERROR"
```

### Métricas Lambda
- Duration, Errors, Invocations
- Dashboard automático criado
- Alertas configuráveis

## ⚠️ Limitações e Considerações

### AWS Compute Optimizer
- Deve ser habilitado previamente na conta
- Requer pelo menos 12 horas de dados para recomendações
- Disponível apenas em regiões específicas

### Cost Explorer
- Dados podem ter até 24h de atraso
- Custos em USD por padrão
- Paginação automática implementada

### Timeouts
- Função Lambda: 5 minutos máximo
- Comandos de lint/test: 5 minutos máximo
- Retry automático para throttling

## 🚀 Próximos Passos

1. **Multi-conta**: Suporte a AWS Organizations
2. **Mais serviços**: RDS, EBS, ELB métricas
3. **Alertas**: Integração com SNS
4. **Histórico**: Armazenamento em DynamoDB
5. **Dashboard**: Interface web personalizada

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Add nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs no CloudWatch
2. Confirme permissões IAM
3. Valide configuração do Compute Optimizer
4. Abra uma issue no repositório

---

**Desenvolvido com ❤️ para otimização de custos AWS**
