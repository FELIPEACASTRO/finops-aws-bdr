# FinOps AWS - Solução Empresarial de Otimização de Custos AWS

Uma solução **serverless empresarial** em Python para análise inteligente de custos, monitoramento de uso e recomendações de otimização na AWS. Projetada para analisar até **253 serviços AWS**, oferecendo insights financeiros e operacionais abrangentes.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [O Que Este Sistema Faz](#o-que-este-sistema-faz)
3. [Arquitetura da Solução](#arquitetura-da-solução)
4. [Serviços AWS Suportados](#serviços-aws-suportados)
5. [Funcionalidades Detalhadas](#funcionalidades-detalhadas)
6. [Estrutura do Projeto](#estrutura-do-projeto)
7. [Como Usar](#como-usar)
8. [Configuração](#configuração)
9. [Testes](#testes)
10. [Deploy na AWS](#deploy-na-aws)
11. [Stack Tecnológico](#stack-tecnológico)
12. [Roadmap](#roadmap)

---

## Visão Geral

### O Que é FinOps?

**FinOps (Financial Operations)** é uma prática de gerenciamento financeiro em nuvem que combina sistemas, melhores práticas e cultura para aumentar a capacidade de uma organização de entender os custos da nuvem e tomar decisões de negócios informadas.

### Por Que Esta Solução?

| Problema | Nossa Solução |
|----------|---------------|
| Custos AWS crescendo sem controle | Análise automática multi-período (7, 15, 30 dias) |
| Recursos subutilizados | Identificação de instâncias com CPU < 20% |
| Falta de visibilidade | Dashboard consolidado com 21+ serviços |
| Recomendações manuais | Integração com AWS Compute Optimizer (ML) |
| Dificuldade de monitoramento | Alertas proativos e métricas em tempo real |

### Métricas do Projeto

| Métrica | Valor |
|---------|-------|
| Serviços AWS Implementados | 21 de 253 (8.3%) |
| Testes Automatizados | 271 passando |
| Cobertura de Categorias | Compute, Storage, Database, Networking, Analytics |

---

## O Que Este Sistema Faz

### 1. Análise Financeira Inteligente

O sistema coleta e analisa custos da sua conta AWS automaticamente:

```
Exemplo de Saida - Custos por Periodo:
-------------------------------------
Ultimos 30 dias:
  - Amazon EC2:      $1,234.56 (45.2%)
  - Amazon RDS:      $567.89  (20.8%)
  - Amazon S3:       $234.56  (8.6%)
  - AWS Lambda:      $123.45  (4.5%)
  - Outros:          $567.89  (20.9%)
  
  TOTAL: $2,728.35
  
Tendência: INCREASING (+12% vs mês anterior)
```

### 2. Monitoramento Operacional

Coleta métricas de performance dos seus recursos:

```
Exemplo de Saida - EC2 Performance:
-----------------------------------
Instancia: i-0abc123def456
  - Tipo: m5.xlarge
  - Estado: running
  - CPU Média (30d): 15.3%
  - Status: SUBUTILIZADA (candidata a downsizing)
  
Instância: i-0xyz789ghi012
  - Tipo: t3.medium
  - Estado: stopped (há 45 dias)
  - Status: CANDIDATA A TERMINAÇÃO
```

### 3. Recomendações de Otimização

Gera recomendações inteligentes baseadas em ML:

```
Exemplo de Saída - Recomendações:
---------------------------------
[ALTA PRIORIDADE] EC2 Right-Sizing
  Recurso: i-0abc123def456
  Ação: Reduzir de m5.xlarge para m5.large
  Economia Mensal: $45.60
  Confiança: 92%

[MÉDIA PRIORIDADE] EBS Volume Type
  Recurso: vol-0abc123def456
  Ação: Migrar de gp2 para gp3
  Economia Mensal: $12.30
  Confiança: 88%

ECONOMIA TOTAL POTENCIAL: $57.90/mês
```

---

## Arquitetura da Solução

### Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRIGGERS (Gatilhos)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  EventBridge │  │ API Gateway  │  │   Manual     │          │
│  │  (Agendado)  │  │  (HTTP/REST) │  │  (Console)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS LAMBDA FUNCTION                          │
│                    (Python 3.11 Runtime)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   FINOPS CORE ENGINE                      │  │
│  │                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │  │
│  │  │    Cost     │ │   Metrics   │ │  Optimizer  │         │  │
│  │  │   Service   │ │   Service   │ │   Service   │         │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘         │  │
│  │                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │  │
│  │  │   State     │ │   Retry     │ │   Cleanup   │         │  │
│  │  │   Manager   │ │   Handler   │ │   Manager   │         │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Cost Explorer │    │  CloudWatch   │    │   Compute     │
│               │    │               │    │   Optimizer   │
│ - Custos      │    │ - Metricas    │    │ - ML Recs     │
│ - Uso         │    │ - Logs        │    │ - Savings     │
│ - Tendencias  │    │ - Alertas     │    │ - Confidence  │
└───────────────┘    └───────────────┘    └───────────────┘
```

### Arquitetura de Software (Clean Architecture)

O projeto segue **Clean Architecture** com 4 camadas distintas:

```
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│              (Serviços Externos e Frameworks)                   │
│                                                                 │
│  - Boto3 (AWS SDK)           - Cost Explorer API                │
│  - CloudWatch API            - Compute Optimizer API            │
│  - DynamoDB (State)          - S3 (Storage)                     │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER                              │
│                 (Controladores e Adaptadores)                   │
│                                                                 │
│  - Lambda Handler            - Event Processors                 │
│  - API Adapters              - Response Formatters              │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                             │
│                  (Casos de Uso e DTOs)                          │
│                                                                 │
│  - AnalyzeCostsUseCase       - GenerateReportUseCase            │
│  - CollectMetricsUseCase     - CostAnalysisDTO                  │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                                │
│                  (Lógica de Negócio Core)                       │
│                                                                 │
│  - Entities (CostEntity)     - Value Objects (Money, Period)    │
│  - Domain Services           - Repository Interfaces            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Serviços AWS Suportados

### Serviços Implementados (21 de 253)

#### Compute (Computação)

| Serviço | Descrição | Recursos Analisados |
|---------|-----------|---------------------|
| **EC2** | Máquinas virtuais | Instâncias, Reserved, Spot, estados |
| **Lambda** | Funções serverless | Memória, durações, invocações, erros |
| **ECS** | Containers | Clusters, services, tasks, Fargate |
| **EMR** | Big Data (Spark/Hadoop) | Clusters, auto-scaling, Spot |
| **SageMaker** | Machine Learning | Notebooks, endpoints, training jobs |

#### Storage (Armazenamento)

| Serviço | Descrição | Recursos Analisados |
|---------|-----------|---------------------|
| **S3** | Object Storage | Buckets, lifecycle, classes de storage |
| **EBS** | Block Storage | Volumes, snapshots, tipos (gp2/gp3) |
| **EFS** | File Storage | File systems, lifecycle, mount targets |

#### Database (Banco de Dados)

| Serviço | Descrição | Recursos Analisados |
|---------|-----------|---------------------|
| **RDS** | Bancos relacionais | Instâncias, Multi-AZ, backups |
| **DynamoDB** | NoSQL | Tabelas, capacidade, PITR, billing |
| **ElastiCache** | Cache (Redis/Memcached) | Clusters, replication groups |
| **Redshift** | Data Warehouse | Clusters, encriptação, snapshots |

#### Networking (Rede)

| Serviço | Descrição | Recursos Analisados |
|---------|-----------|---------------------|
| **VPC** | Rede virtual | NAT Gateways, Elastic IPs, VPNs |
| **CloudFront** | CDN | Distribuições, cache, compressão |
| **ELB** | Load Balancers | ALB, NLB, CLB, target groups |
| **Route53** | DNS | Hosted zones, health checks, records |

#### Analytics e Integração

| Serviço | Descrição | Recursos Analisados |
|---------|-----------|---------------------|
| **Kinesis** | Streaming | Data Streams, Firehose, shards |
| **Glue** | ETL | Jobs, crawlers, data catalog |
| **SNS/SQS** | Messaging | Topics, queues, subscribers |
| **Backup** | Backup centralizado | Vaults, plans, recovery points |
| **Secrets Manager** | Gerenciamento de secrets | Rotação, encriptação, uso |

---

## Funcionalidades Detalhadas

### 1. Sistema de Análise de Custos

#### Como Funciona

```python
# O CostService coleta dados do AWS Cost Explorer
cost_service = CostService()

# Coleta custos dos ultimos 30 dias
costs = cost_service.get_costs_by_service(days=30)

# Resultado estruturado
{
    "period": "last_30_days",
    "total_cost": 2728.35,
    "currency": "USD",
    "services": {
        "Amazon EC2": 1234.56,
        "Amazon RDS": 567.89,
        "Amazon S3": 234.56,
        ...
    },
    "trend": "INCREASING",
    "trend_percentage": 12.5
}
```

#### Períodos Disponíveis

| Período | Descrição | Uso Recomendado |
|---------|-----------|-----------------|
| 7 dias | Última semana | Monitoramento rápido |
| 15 dias | Duas semanas | Análise de tendências |
| 30 dias | Último mês | Planejamento financeiro |

### 2. Sistema de Métricas

#### Métricas EC2

```python
# Coleta métricas de performance EC2
metrics_service = MetricsService()
ec2_usage = metrics_service.get_ec2_usage_data()

# Cada instância retorna:
{
    "instance_id": "i-0abc123def456",
    "instance_type": "m5.xlarge",
    "state": "running",
    "launch_time": "2024-01-15T10:30:00Z",
    "avg_cpu_7d": 15.3,
    "avg_cpu_30d": 18.2,
    "is_underutilized": true  # CPU < 20%
}
```

#### Métricas Lambda

```python
# Coleta métricas de funções Lambda
lambda_usage = metrics_service.get_lambda_usage_data()

# Cada função retorna:
{
    "function_name": "my-function",
    "runtime": "python3.11",
    "memory_mb": 256,
    "timeout_seconds": 30,
    "invocations_7d": 15420,
    "errors_7d": 23,
    "avg_duration_ms": 145.5,
    "error_rate": 0.15  # percentual
}
```

### 3. Sistema de Recomendações

#### Tipos de Recomendações

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| **RIGHT_SIZING** | Ajuste de tamanho | m5.xlarge -> m5.large |
| **STOP_INSTANCE** | Parar recurso | Instância parada há 30+ dias |
| **TERMINATE** | Encerrar recurso | Volume EBS não anexado |
| **UPGRADE** | Atualizar tipo | gp2 -> gp3 (mais barato) |
| **ENABLE_FEATURE** | Ativar recurso | Ativar lifecycle S3 |

#### Estrutura de Recomendação

```python
{
    "service": "EC2",
    "resource_id": "i-0abc123def456",
    "finding": "OVER_PROVISIONED",
    "title": "Instancia Subutilizada",
    "description": "CPU media de 15% nos ultimos 30 dias",
    "action": "Reduzir para m5.large",
    "estimated_monthly_savings": 45.60,
    "confidence_score": 0.92,
    "implementation_effort": "LOW",
    "risk_level": "LOW"
}
```

### 4. Sistema de Resiliência

#### Retry Handler

O sistema inclui tratamento automático de erros com retry:

```python
# Configuração de retry
retry_policy = RetryPolicy(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True  # Adiciona aleatoriedade
)

# Erros que disparam retry automático:
# - Throttling (429)
# - Service Unavailable (503)
# - Timeout
# - Connection Errors
```

#### Circuit Breaker

Protege contra falhas em cascata:

```python
from src.finops_aws.core import CircuitBreaker, CircuitBreakerConfig

# Estados do Circuit Breaker:
# - CLOSED: Operação normal
# - OPEN: Serviço indisponível, falha imediata
# - HALF_OPEN: Testando recuperação

# Configuração
config = CircuitBreakerConfig(
    failure_threshold=5,      # Abre após 5 falhas
    recovery_timeout=60       # Tenta recuperar em 60s
)
circuit_breaker = CircuitBreaker(config=config)

# Uso
if circuit_breaker.can_execute():
    try:
        result = call_aws_service()
        circuit_breaker.record_success()
    except Exception:
        circuit_breaker.record_failure()
```

#### State Manager (DynamoDB)

Gerencia estado de execuções longas:

```python
# Permite retomar execuções interrompidas
state_manager = DynamoDBStateManager(table_name="finops-state")

# Salva checkpoint
state_manager.save_checkpoint(
    execution_id="exec-123",
    service="EC2",
    progress={"instances_processed": 150, "total": 500}
)

# Resume de onde parou
checkpoint = state_manager.get_checkpoint("exec-123", "EC2")
```

### 5. Sistema de Limpeza Automática

Remove arquivos temporários automaticamente:

```python
# Configuração
cleanup_config = CleanupConfig(
    file_extensions={'.bkp', '.tmp', '.cache', '.log'},
    max_file_age_hours=24,
    max_file_size_mb=100,
    s3_cleanup_enabled=True,
    s3_max_age_days=7,
    dry_run=False  # True para simular
)

# Execução
cleanup_manager = CleanupManager(config=cleanup_config)
result = cleanup_manager.cleanup_all()

# Resultado
{
    "files_deleted": 45,
    "bytes_freed": 125829120,  # 120 MB
    "s3_objects_deleted": 12,
    "execution_time_seconds": 3.5
}
```

---

## Estrutura do Projeto

```
finops-aws/
├── src/
│   └── finops_aws/
│       ├── application/           # Camada de Aplicação
│       │   ├── dto/               # Data Transfer Objects
│       │   │   └── cost_analysis_dto.py
│       │   ├── interfaces/        # Interfaces da aplicação
│       │   │   └── logger_interface.py
│       │   └── use_cases/         # Casos de uso
│       │       └── analyze_costs_use_case.py
│       │
│       ├── core/                  # Núcleo do sistema
│       │   ├── factories.py       # Factory Pattern (clientes AWS)
│       │   ├── retry_handler.py   # Retry com backoff exponencial
│       │   ├── resilient_executor.py  # Circuit breaker
│       │   ├── state_manager.py   # Gerenciamento de estado
│       │   ├── dynamodb_state_manager.py  # Estado no DynamoDB
│       │   └── cleanup_manager.py # Limpeza automática
│       │
│       ├── domain/                # Camada de Domínio
│       │   ├── entities/          # Entidades de negócio
│       │   │   └── cost_entity.py
│       │   ├── repositories/      # Interfaces de repositório
│       │   │   └── cost_repository.py
│       │   └── value_objects/     # Objetos de valor
│       │       ├── money.py
│       │       ├── service_name.py
│       │       └── time_period.py
│       │
│       ├── infrastructure/        # Camada de Infraestrutura
│       │   └── services/          # Implementações externas
│       │
│       ├── services/              # Serviços FinOps (21 serviços)
│       │   ├── base_service.py    # Classe base abstrata
│       │   ├── cost_service.py    # Análise de custos
│       │   ├── metrics_service.py # Coleta de métricas
│       │   ├── optimizer_service.py  # Recomendações
│       │   ├── ec2_finops_service.py
│       │   ├── lambda_finops_service.py
│       │   ├── s3_service.py
│       │   ├── ebs_service.py
│       │   ├── dynamodb_finops_service.py
│       │   ├── rds_service.py
│       │   ├── elasticache_service.py
│       │   ├── ecs_service.py
│       │   ├── efs_service.py
│       │   ├── redshift_service.py
│       │   ├── cloudfront_service.py
│       │   ├── elb_service.py
│       │   ├── emr_service.py
│       │   ├── vpc_network_service.py
│       │   ├── kinesis_service.py
│       │   ├── glue_service.py
│       │   ├── sagemaker_service.py
│       │   ├── route53_service.py
│       │   ├── backup_service.py
│       │   ├── sns_sqs_service.py
│       │   └── secrets_manager_service.py
│       │
│       ├── models/                # Modelos de dados
│       │   └── finops_models.py
│       │
│       ├── utils/                 # Utilitários
│       │   ├── logger.py          # Logging estruturado
│       │   ├── aws_helpers.py     # Helpers AWS
│       │   └── execution_monitor.py
│       │
│       ├── lambda_handler.py      # Entry point Lambda
│       └── resilient_lambda_handler.py  # Handler resiliente
│
├── tests/
│   └── unit/                      # Testes unitários (271 testes)
│       ├── test_cleanup_manager.py
│       ├── test_cost_service.py
│       ├── test_dynamodb_state_manager.py
│       ├── test_factories.py
│       ├── test_metrics_service.py
│       ├── test_new_services.py
│       ├── test_new_services_phase2.py
│       ├── test_optimizer_service.py
│       ├── test_phase2_priority_services.py
│       ├── test_resilient_executor.py
│       ├── test_retry_handler.py
│       └── test_state_manager.py
│
├── example_events/                # Eventos de exemplo
│   ├── api_gateway_event.json
│   └── scheduled_event.json
│
├── infrastructure/                # IaC (CloudFormation)
│   └── cloudformation-template.yaml
│
├── requirements.txt               # Dependencias Python
├── pytest.ini                     # Configuracao pytest
├── deploy.sh                      # Script de deploy
├── service_aws.json               # Catalogo 253 servicos AWS
└── replit.md                      # Documentacao do projeto
```

---

## Como Usar

### 1. Instalacao de Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configuração de Credenciais AWS

```bash
# Opção 1: Variáveis de ambiente
export AWS_ACCESS_KEY_ID="sua-access-key"
export AWS_SECRET_ACCESS_KEY="sua-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Opção 2: AWS CLI
aws configure
```

### 3. Execução Local

```bash
# Executar demo com serviços mockados
python run_local_demo.py 1

# Executar testes
python run_local_demo.py 2

# Executar ambos
python run_local_demo.py 3
```

### 4. Usando como Biblioteca

```python
from src.finops_aws.services import (
    CostService,
    MetricsService,
    OptimizerService,
    S3Service,
    EC2FinOpsService
)
from src.finops_aws.core.factories import ServiceFactory

# Usando o Factory Pattern
factory = ServiceFactory()

# Obter serviços
cost_service = factory.get_cost_service()
metrics_service = factory.get_metrics_service()
optimizer_service = factory.get_optimizer_service()

# Coletar dados de custos
costs_7d = cost_service.get_costs_by_service(days=7)
costs_30d = cost_service.get_costs_by_service(days=30)

# Coletar métricas
ec2_metrics = metrics_service.get_ec2_usage_data()
lambda_metrics = metrics_service.get_lambda_usage_data()

# Obter recomendações de otimização
ec2_recs = optimizer_service.get_ec2_recommendations()
lambda_recs = optimizer_service.get_lambda_recommendations()

print(f"Custo 30 dias: ${costs_30d.get('total', 0):.2f}")
```

---

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `AWS_DEFAULT_REGION` | Região AWS | us-east-1 |
| `LOG_LEVEL` | Nível de log | INFO |
| `CLEANUP_ENABLED` | Ativar limpeza automática | true |
| `CLEANUP_DRY_RUN` | Simular limpeza | false |
| `FINOPS_STATE_BUCKET` | Bucket para estado | finops-aws-state |
| `FINOPS_STATE_TABLE` | Tabela DynamoDB | finops-state |

### Configuração de Limpeza

```bash
# Extensões de arquivos para limpar
CLEANUP_FILE_EXTENSIONS=".bkp,.tmp,.cache,.log"

# Idade máxima dos arquivos (horas)
CLEANUP_MAX_FILE_AGE_HOURS=24

# Tamanho máximo por arquivo (MB)
CLEANUP_MAX_FILE_SIZE_MB=100

# Limpar objetos S3
CLEANUP_S3_ENABLED=true
CLEANUP_S3_MAX_AGE_DAYS=7
```

---

## Testes

### Executar Todos os Testes

```bash
pytest tests/ -v
```

### Executar Testes Específicos

```bash
# Testes de um arquivo
pytest tests/unit/test_cost_service.py -v

# Testes por categoria
pytest tests/unit/test_phase2_priority_services.py -v
```

### Estrutura dos Testes

| Arquivo | Cobertura |
|---------|-----------|
| test_cleanup_manager.py | Sistema de limpeza |
| test_cost_service.py | Serviço de custos |
| test_dynamodb_state_manager.py | Gerenciamento de estado |
| test_factories.py | Factory Pattern |
| test_metrics_service.py | Coleta de métricas |
| test_new_services.py | S3, EBS, DynamoDB |
| test_new_services_phase2.py | EFS, ElastiCache, ECS |
| test_optimizer_service.py | Recomendações |
| test_phase2_priority_services.py | 14 serviços prioritários |
| test_resilient_executor.py | Circuit Breaker |
| test_retry_handler.py | Retry com backoff |
| test_state_manager.py | State Manager |

---

## Deploy na AWS

### 1. Preparar Pacote Lambda

```bash
# Criar pacote de deploy
./deploy.sh package
```

### 2. Deploy via CloudFormation

```bash
# Deploy completo
./deploy.sh deploy --stack-name finops-aws-prod

# Ou usando AWS CLI diretamente
aws cloudformation deploy \
  --template-file infrastructure/cloudformation-template.yaml \
  --stack-name finops-aws-prod \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=prod \
    ScheduleExpression="rate(1 day)"
```

### 3. Verificar Deploy

```bash
# Ver status da stack
aws cloudformation describe-stacks --stack-name finops-aws-prod

# Ver logs da Lambda
aws logs tail /aws/lambda/finops-aws-prod --follow
```

---

## Stack Tecnológico

### Linguagem e Runtime

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Python | 3.11 | Linguagem principal |
| Boto3 | Latest | AWS SDK |
| Pytest | 9.0+ | Framework de testes |
| Moto | Latest | Mock AWS para testes |

### Serviços AWS Utilizados

| Serviço | Uso |
|---------|-----|
| Lambda | Execução serverless |
| Cost Explorer | Dados de custo |
| CloudWatch | Métricas e logs |
| Compute Optimizer | Recomendações ML |
| DynamoDB | Gerenciamento de estado |
| S3 | Armazenamento |
| EventBridge | Agendamento |
| IAM | Permissões |

### Padrões de Design

| Padrão | Aplicação |
|--------|-----------|
| Clean Architecture | Separação de camadas |
| Domain-Driven Design | Modelagem de domínio |
| Factory Pattern | Criação de serviços |
| Strategy Pattern | Algoritmos de análise |
| Repository Pattern | Acesso a dados |
| Circuit Breaker | Resiliência |
| Retry with Backoff | Tratamento de erros |

---

## Roadmap

### Fase Atual: FASE 2.3 (Concluída)

- 21 serviços implementados
- 271 testes automatizados
- Sistema de resiliência completo

### Próximas Fases

#### FASE 3: Serviços de Prioridade 2 (Planejado)

- AWS Organizations (multi-conta)
- AWS Budgets (alertas de orçamento)
- Cost Anomaly Detection
- Savings Plans Analysis

#### FASE 4: Serviços de Prioridade 3 (Planejado)

- API Gateway
- Step Functions
- CodeBuild/CodePipeline
- EKS (Kubernetes)

#### FASE 5: Features Avançadas (Planejado)

- Dashboard Web (React)
- Alertas proativos (Slack, Email)
- Predição ML de custos
- Multi-account consolidation
- Cost Allocation Tags

---

## Suporte e Contribuição

### Reportar Problemas

1. Verifique os logs no CloudWatch
2. Execute os testes localmente
3. Abra uma issue com detalhes

### Contribuir

1. Fork o repositório
2. Crie uma branch feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## Licença

Este projeto é de uso interno. Todos os direitos reservados.

---

**Desenvolvido para otimização de custos AWS**

*Versão: 2.3 | Última atualização: Novembro 2025*
