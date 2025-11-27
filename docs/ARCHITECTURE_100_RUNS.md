# FinOps AWS - Arquitetura para 100 Execuções/Dia

## Visão Geral

Esta documentação descreve a arquitetura otimizada para suportar **100 execuções por dia** da solução FinOps AWS, mantendo alta confiabilidade e custos mínimos.

## Mudanças Arquiteturais

### Antes (5 execuções/dia)
```
EventBridge → Lambda (monolítico) → DynamoDB + S3
```

### Depois (100 execuções/dia)
```
EventBridge → Step Functions → Lambda Workers (paralelo) → S3
                    ↓
              Lambda Mapper → Lambda Aggregator
                    ↓
                 SQS DLQ (erros)
```

---

## Diagrama da Nova Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA PARA 100 EXECUÇÕES/DIA                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐ │
│  │  EventBridge │────▶│              STEP FUNCTIONS                      │ │
│  │  (Scheduler) │     │         Orquestrador Central                     │ │
│  └──────────────┘     │                                                  │ │
│                       │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │ │
│                       │  │ Mapper  │─▶│ Workers │─▶│Aggregator│          │ │
│                       │  │ Lambda  │  │ Paralelo│  │ Lambda  │          │ │
│                       │  └─────────┘  └────┬────┘  └────┬────┘          │ │
│                       └───────────────────────────────────────────────────┘ │
│                                            │              │                 │
│                                            ▼              ▼                 │
│  ┌──────────────┐     ┌──────────────┐  ┌──────────────────────────────┐   │
│  │     SQS      │◀────│   Lambda     │  │           S3 BUCKET          │   │
│  │     DLQ      │     │  Workers     │  │  ┌─────────┐  ┌──────────┐  │   │
│  │   (Erros)    │     │ (20 paralelo)│  │  │ state/  │  │ reports/ │  │   │
│  └──────────────┘     └──────────────┘  │  └─────────┘  └──────────┘  │   │
│                                          └──────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        OBSERVABILIDADE                               │   │
│  │  CloudWatch Dashboard │ X-Ray Tracing │ Alarmes SNS │ Métricas       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

### 1. Step Functions (Orquestrador)

O Step Functions orquestra todo o fluxo de análise:

```
START → InitializeExecution (Mapper)
          ↓
        ProcessServiceBatches (Map paralelo)
          ↓
        AggregateResults (Aggregator)
          ↓
        END
```

**Benefícios:**
- Retry automático por batch (não por execução inteira)
- Timeout individual por Lambda
- Rastreamento visual de onde falhou
- Custo: ~$1.50/mês para 100 execuções/dia

### 2. Lambda Mapper

Responsável por:
- Dividir 252 serviços em batches de ~20
- Agrupar serviços que usam Cost Explorer (rate limiting)
- Salvar estado inicial no S3

**Configuração:**
- Memory: 256 MB
- Timeout: 60 segundos
- Handler: `finops_aws.lambda_mapper.lambda_handler`

### 3. Lambda Worker (Principal)

Processa cada batch de serviços:
- Coleta métricas
- Analisa custos
- Gera recomendações

**Configuração:**
- Memory: 512 MB
- Timeout: 300 segundos
- Concurrency: até 20 paralelos

### 4. Lambda Aggregator

Consolida todos os resultados:
- Merge de métricas e recomendações
- Geração de relatório final
- Notificação via SNS

**Configuração:**
- Memory: 512 MB
- Timeout: 120 segundos
- Handler: `finops_aws.lambda_aggregator.lambda_handler`

### 5. S3 (Estado + Relatórios)

Substitui DynamoDB para redução de custo:

```
s3://finops-aws-storage-{account}/
├── state/
│   └── executions/{execution_id}/
│       └── state.json
├── reports/
│   ├── YYYY/MM/DD/{execution_id}/
│   │   ├── report.json
│   │   └── summary.json
│   └── latest/
│       └── report.json
├── checkpoints/
│   └── {execution_id}/{service}.json
└── archives/
    └── (relatórios antigos)
```

**Lifecycle Rules:**
- `state/`: Expira em 7 dias
- `checkpoints/`: Expira em 3 dias
- `reports/`: Expira em 90 dias
- `archives/`: Glacier após 90 dias, deleta após 365 dias

### 6. SQS Dead Letter Queue

Captura falhas para análise:
- Mensagens retidas por 14 dias
- Alarme dispara quando há mensagens na DLQ
- Permite reprocessamento manual

---

## Comparação de Custos

| Componente | Antes (DynamoDB) | Depois (S3) | Economia |
|------------|-----------------|-------------|----------|
| Estado | $1.50/mês | $0.01/mês | 99% |
| Step Functions | $0 | $1.50/mês | - |
| Lambda | $0.10/mês | $0.35/mês | - |
| CloudWatch | $0.50/mês | $1.00/mês | - |
| SQS | $0 | $0.01/mês | - |
| **TOTAL** | **~$2.10/mês** | **~$3.00/mês** | +$0.90 |

**Nota:** O aumento de $0.90/mês habilita 100 execuções/dia com alta confiabilidade (vs 5/dia antes).

---

## Configuração

### Variáveis Terraform

```hcl
# Step Functions
stepfunctions_max_concurrency = 20
stepfunctions_log_level       = "ERROR"

# Batching
batch_size = 20

# SQS (opcional)
enable_sqs_processing = false
```

### Deploy

```bash
cd infrastructure/terraform
terraform init
terraform plan -var="environment=prod"
terraform apply
```

---

## Observabilidade

### Dashboard CloudWatch

O dashboard inclui:
- Execuções Step Functions (iniciadas, sucesso, falhas)
- Taxa de sucesso (%)
- Duração P50/P90/P99
- Invocações e erros Lambda
- Mensagens na DLQ
- Operações S3

### Alarmes Configurados

| Alarme | Threshold | Ação |
|--------|-----------|------|
| Step Functions Falhas | > 0 | SNS |
| Step Functions Duração | P95 > 10 min | SNS |
| Lambda Erros | > 5 em 5 min | SNS |
| Lambda Throttles | > 0 | SNS |
| DLQ Mensagens | > 0 | SNS |
| Taxa Sucesso | < 95% | SNS |

---

## Rate Limiting

### Cost Explorer API

- Limite: 5 TPS
- Estratégia: Batches separados para serviços CE
- Batch size reduzido para CE: 10 serviços

### Outras APIs AWS

- Exponential backoff implementado
- Circuit breaker para falhas consecutivas
- Retry máximo: 3 tentativas

---

## Invocação

### Via AWS CLI

```bash
# Iniciar execução Step Functions
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:123456789:stateMachine:finops-aws-prod-orchestrator \
  --input '{"analysis_type": "full"}'

# Verificar status
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:us-east-1:123456789:execution:finops-aws-prod-orchestrator:exec-123
```

### Via boto3

```python
import boto3

sfn = boto3.client('stepfunctions')

response = sfn.start_execution(
    stateMachineArn='arn:aws:states:us-east-1:123456789:stateMachine:finops-aws-prod-orchestrator',
    input='{"analysis_type": "full"}'
)

print(f"Execution ARN: {response['executionArn']}")
```

---

## Troubleshooting

### Execução Falhou

1. Verifique o console Step Functions
2. Identifique o estado que falhou
3. Verifique logs no CloudWatch
4. Cheque mensagens na DLQ

### DLQ com Mensagens

```bash
# Visualizar mensagens na DLQ
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789/finops-aws-prod-dlq \
  --max-number-of-messages 10
```

### Throttling

1. Aumente `stepfunctions_max_concurrency` gradualmente
2. Reduza `batch_size` para serviços Cost Explorer
3. Verifique Service Quotas no AWS

---

## Conclusão

Esta arquitetura otimizada permite:

- **100 execuções/dia** com alta confiabilidade
- **Custo reduzido** usando S3 em vez de DynamoDB
- **Observabilidade completa** via CloudWatch
- **Recuperação automática** de falhas
- **Escalabilidade** para mais execuções se necessário

---

*FinOps AWS - Arquitetura para 100 Execuções/Dia*
*Novembro 2025*
