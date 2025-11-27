# FinOps AWS - Guia de Deploy com Terraform

## Visão Geral

Este guia descreve como fazer o deploy do **FinOps AWS** na AWS usando Terraform. A infraestrutura inclui:

- **Step Functions** - Orquestração do fluxo de execução
- **AWS Lambda** - Funções de análise (Mapper, Worker, Aggregator)
- **EventBridge** - Agendamento de execuções automáticas
- **S3** - Estado e relatórios (substituindo DynamoDB)
- **SQS DLQ** - Dead Letter Queue para erros
- **CloudWatch** - Logs, métricas e dashboard
- **SNS** - Alertas e notificações
- **KMS** - Criptografia de dados sensíveis
- **IAM** - Permissões mínimas necessárias

---

## Pré-requisitos

### 1. Ferramentas Necessárias

```bash
# Terraform >= 1.5.0
terraform --version

# AWS CLI configurado
aws --version
aws sts get-caller-identity

# Python 3.11 (para build do layer)
python3 --version
```

### 2. Permissões AWS

O usuário/role que executar o Terraform precisa das seguintes permissões:

- `iam:*` - Para criar roles e policies
- `lambda:*` - Para criar a função Lambda
- `s3:*` - Para criar buckets
- `states:*` - Para criar Step Functions
- `events:*` - Para criar regras EventBridge
- `logs:*` - Para criar log groups
- `kms:*` - Para criar chaves KMS
- `sns:*` - Para criar tópicos SNS

### 3. Backend S3 (Opcional mas Recomendado)

Crie o bucket para o state do Terraform:

```bash
# Criar bucket para state
aws s3 mb s3://finops-aws-terraform-state --region us-east-1

# Habilitar versionamento
aws s3api put-bucket-versioning \
  --bucket finops-aws-terraform-state \
  --versioning-configuration Status=Enabled

# Criar tabela DynamoDB para lock
aws dynamodb create-table \
  --table-name finops-aws-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

---

## Configuração

### 1. Copiar Arquivo de Variáveis

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```

### 2. Editar Configurações

Abra `terraform.tfvars` e ajuste:

```hcl
# Seu ambiente
environment = "prod"
aws_region  = "us-east-1"
owner       = "seu-time"
alert_email = "seu-email@empresa.com"

# Agendamento (5 execuções por dia - UTC)
schedule_expressions = [
  "cron(0 6 * * ? *)",   # 06:00 UTC = 03:00 BRT
  "cron(0 9 * * ? *)",   # 09:00 UTC = 06:00 BRT
  "cron(0 12 * * ? *)",  # 12:00 UTC = 09:00 BRT
  "cron(0 15 * * ? *)",  # 15:00 UTC = 12:00 BRT
  "cron(0 18 * * ? *)"   # 18:00 UTC = 15:00 BRT
]

# Regiões para análise
target_regions = [
  "us-east-1",
  "us-east-2",
  "sa-east-1"
]
```

---

## Deploy

### 1. Inicializar Terraform

```bash
cd infrastructure/terraform

# Inicializar providers e backend
terraform init
```

### 2. Planejar Mudanças

```bash
# Ver o que será criado
terraform plan -out=tfplan

# Revisar o plano detalhadamente
terraform show tfplan
```

### 3. Aplicar

```bash
# Aplicar as mudanças
terraform apply tfplan

# Ou aplicar diretamente (com confirmação)
terraform apply
```

### 4. Verificar Deploy

```bash
# Ver outputs
terraform output

# Testar a função
aws lambda invoke \
  --function-name finops-aws-prod \
  --payload '{"analysis_type": "full"}' \
  response.json

# Ver resultado
cat response.json | jq
```

---

## Estrutura de Arquivos

```
infrastructure/terraform/
├── main.tf              # Provider e configurações principais
├── variables.tf         # Definição de variáveis
├── versions.tf          # Constraints de versão
├── iam.tf               # Roles e policies IAM
├── lambda.tf            # Função Lambda e layer
├── eventbridge.tf       # Agendamentos
├── storage.tf           # S3 Bucket (estado e relatórios)
├── security.tf          # KMS e SNS
├── outputs.tf           # Outputs do deploy
├── terraform.tfvars.example  # Exemplo de configuração
└── README_TERRAFORM.md  # Este arquivo
```

---

## Configurações Importantes

### Agendamento (EventBridge)

O sistema suporta até 5 execuções por dia conforme seu requisito:

```hcl
schedule_expressions = [
  "cron(0 6 * * ? *)",   # Execução 1
  "cron(0 9 * * ? *)",   # Execução 2
  "cron(0 12 * * ? *)",  # Execução 3
  "cron(0 15 * * ? *)",  # Execução 4
  "cron(0 18 * * ? *)"   # Execução 5
]
```

**Nota:** Horários em UTC. Para converter para horário de Brasília (BRT), subtraia 3 horas.

### Multi-Account (Opcional)

Para analisar múltiplas contas AWS:

```hcl
enable_multi_account   = true
organization_role_name = "FinOpsReadOnlyRole"
target_account_ids = [
  "111111111111",
  "222222222222"
]
```

**Requisito:** Criar a role `FinOpsReadOnlyRole` em cada conta-alvo com trust policy para a conta principal.

### Segurança

```hcl
# Criptografia KMS (recomendado para produção)
enable_kms_encryption = true

# X-Ray tracing para debugging
enable_xray_tracing = true

# Alertas por email
enable_alerts = true
alert_email   = "finops@empresa.com"
```

---

## Custos Estimados

Para 5 execuções diárias com configuração padrão:

| Serviço | Custo Mensal Estimado |
|---------|----------------------|
| Step Functions (100 exec/dia) | ~$1.50 |
| Lambda (Mapper, Worker, Aggregator) | ~$0.35 |
| S3 (estado + relatórios) | ~$0.05 |
| CloudWatch Logs/Dashboard | ~$1.00 |
| SQS DLQ | ~$0.01 |
| EventBridge | ~$0.00 |
| **Total** | **~$3.16/mês** (100 exec/dia) |

---

## Comandos Úteis

### Invocar Lambda Manualmente

```bash
# Análise completa
aws lambda invoke \
  --function-name finops-aws-prod \
  --payload '{"analysis_type": "full"}' \
  response.json

# Apenas custos
aws lambda invoke \
  --function-name finops-aws-prod \
  --payload '{"analysis_type": "costs_only"}' \
  response.json

# Apenas recomendações
aws lambda invoke \
  --function-name finops-aws-prod \
  --payload '{"analysis_type": "recommendations_only"}' \
  response.json
```

### Ver Logs

```bash
# Últimos logs
aws logs tail /aws/lambda/finops-aws-prod --follow

# Buscar erros
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-aws-prod \
  --filter-pattern "ERROR"
```

### Atualizar Código

```bash
# Após modificar o código Python
terraform apply -target=data.archive_file.function -target=aws_lambda_function.main
```

---

## Troubleshooting

### Erro: "Access Denied"

Verifique se o usuário tem permissões suficientes:

```bash
aws sts get-caller-identity
```

### Erro: "Timeout"

Aumente o timeout do Lambda:

```hcl
lambda_timeout = 600  # 10 minutos
```

### Erro: "Memory Limit"

Aumente a memória:

```hcl
lambda_memory_size = 1024  # 1GB
```

### Erro: "Rate Exceeded"

Adicione mais tempo entre execuções ou reduza o número de regiões:

```hcl
target_regions = ["us-east-1", "sa-east-1"]
```

---

## Destruir Infraestrutura

```bash
# CUIDADO: Remove todos os recursos
terraform destroy

# Destruir com confirmação automática
terraform destroy -auto-approve
```

**Nota:** O bucket S3 não será destruído em produção devido ao `force_destroy = false`.

---

## Suporte

Para dúvidas ou problemas:

1. Verifique os logs no CloudWatch
2. Consulte a documentação em `docs/`
3. Revise as configurações em `terraform.tfvars`

---

## Próximos Passos

Após o deploy:

1. ✅ Confirme que a função foi criada: `terraform output lambda_function_name`
2. ✅ Verifique o agendamento no EventBridge Console
3. ✅ Configure alertas de email (confirme a subscription no SNS)
4. ✅ Execute manualmente para testar
5. ✅ Revise os relatórios no bucket S3
