# FinOps AWS - Guia Ultra-Detalhado de Deploy com Terraform

## Visão Geral

Este guia passo a passo explica como fazer o deploy do **FinOps AWS** na sua conta AWS usando Terraform. Não importa seu nível técnico - cada etapa está explicada em detalhes com analogias do dia a dia.

---

## O Que é Terraform?

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    O QUE É TERRAFORM?                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ANALOGIA: Pense no Terraform como uma "receita de bolo" para infraestrutura║
║                                                                              ║
║  SEM TERRAFORM (Manual):                                                     ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  1. Abra o Console AWS                                                       ║
║  2. Clique em Lambda > Create Function                                       ║
║  3. Preencha 15 campos                                                       ║
║  4. Crie uma Role IAM                                                        ║
║  5. Preencha mais 20 campos                                                  ║
║  6. Repita para Step Functions                                               ║
║  7. Repita para S3                                                           ║
║  8. Configure EventBridge                                                    ║
║  9. ... 2 horas depois ...                                                   ║
║                                                                              ║
║  COM TERRAFORM:                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  1. terraform init                                                           ║
║  2. terraform apply                                                          ║
║  3. PRONTO! Tudo criado em 15 minutos                                        ║
║                                                                              ║
║  BENEFÍCIOS:                                                                 ║
║  ✅ Reproduzível - mesma infraestrutura toda vez                             ║
║  ✅ Versionável - histórico no Git                                           ║
║  ✅ Revisável - code review antes de aplicar                                 ║
║  ✅ Documentado - código É a documentação                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## O Que Será Criado

O Terraform vai criar automaticamente:

| Recurso | Quantidade | Para Que Serve |
|---------|------------|----------------|
| **Lambda Functions** | 4 | Processamento (Mapper, Worker, Aggregator, Handler) |
| **Step Functions** | 1 | Orquestração do fluxo de análise |
| **S3 Bucket** | 1 | Armazenamento de estado e relatórios |
| **EventBridge Rules** | 5 | Agendamento (5 execuções/dia) |
| **SQS Queue** | 1 | Dead Letter Queue para erros |
| **SNS Topic** | 1 | Alertas e notificações |
| **IAM Roles** | 4 | Permissões mínimas para cada componente |
| **KMS Key** | 1 | Criptografia de dados sensíveis |
| **CloudWatch** | 5 | Log Groups e métricas |

### Diagrama da Arquitetura

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ARQUITETURA CRIADA PELO TERRAFORM                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────┐                                                         ║
║  │  EventBridge    │  ← Dispara 5x por dia (6h, 10h, 14h, 18h, 22h)         ║
║  │  (Agendador)    │                                                         ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │ Step Functions  │  ← Orquestra todo o fluxo                               ║
║  │ (State Machine) │                                                         ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║     ┌─────┴─────┐                                                            ║
║     ▼           ▼                                                            ║
║  ┌─────────┐ ┌─────────┐                                                     ║
║  │ Lambda  │ │ Lambda  │  ← Workers paralelos analisam serviços              ║
║  │ Worker 1│ │ Worker N│                                                     ║
║  └────┬────┘ └────┬────┘                                                     ║
║       │           │                                                          ║
║       └─────┬─────┘                                                          ║
║             │                                                                ║
║             ▼                                                                ║
║  ┌─────────────────┐     ┌─────────┐                                         ║
║  │ Lambda          │────▶│   S3    │  ← Armazena relatórios                  ║
║  │ Aggregator      │     │ (State) │                                         ║
║  └────────┬────────┘     └─────────┘                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │      SNS        │  ← Envia alertas por email/Slack                        ║
║  │   (Alertas)     │                                                         ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐                                                         ║
║  │     SQS DLQ     │  ← Captura erros para análise                           ║
║  │ (Dead Letter)   │                                                         ║
║  └─────────────────┘                                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Pré-requisitos

### 1. Ferramentas Necessárias

```bash
# 1. Terraform >= 1.5.0
terraform --version
# Esperado: Terraform v1.5.x ou superior

# 2. AWS CLI configurado
aws --version
# Esperado: aws-cli/2.x.x

# Verificar se está autenticado
aws sts get-caller-identity
# Esperado: Retorna seu Account ID, ARN, etc.

# 3. Python 3.11 (para build do layer)
python3 --version
# Esperado: Python 3.11.x
```

### 2. Como Instalar as Ferramentas

#### Instalando Terraform

```bash
# macOS (Homebrew)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Windows
# Baixe de https://developer.hashicorp.com/terraform/downloads
# Ou use chocolatey: choco install terraform
```

#### Instalando AWS CLI

```bash
# macOS
brew install awscli

# Ubuntu/Debian
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Baixe de https://aws.amazon.com/cli/
```

### 3. Permissões AWS Necessárias

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PERMISSÕES NECESSÁRIAS PARA DEPLOY                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  O usuário que executa o Terraform precisa criar recursos.                   ║
║  Recomendamos usar AdministratorAccess para o deploy inicial.                ║
║                                                                              ║
║  PERMISSÕES MÍNIMAS (se não puder usar AdministratorAccess):                 ║
║                                                                              ║
║  • iam:* (criar roles e policies)                                            ║
║  • lambda:* (criar funções Lambda)                                           ║
║  • s3:* (criar buckets)                                                      ║
║  • states:* (criar Step Functions)                                           ║
║  • events:* (criar EventBridge rules)                                        ║
║  • logs:* (criar log groups)                                                 ║
║  • kms:* (criar chaves KMS)                                                  ║
║  • sns:* (criar tópicos SNS)                                                 ║
║  • sqs:* (criar filas SQS)                                                   ║
║                                                                              ║
║  IMPORTANTE: Estas são permissões para CRIAR a infraestrutura.               ║
║  O FinOps AWS em execução usa apenas permissões ReadOnly!                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Passo a Passo do Deploy

### Passo 1: Preparar Backend S3 (Opcional, Recomendado)

O backend S3 armazena o estado do Terraform. Isso permite:
- Trabalho em equipe (múltiplas pessoas usando o mesmo state)
- Histórico de mudanças (versionamento)
- Lock para evitar conflitos (DynamoDB)

```bash
# Criar bucket para state
aws s3 mb s3://finops-aws-terraform-state-SEU-ACCOUNT-ID --region us-east-1

# Habilitar versionamento
aws s3api put-bucket-versioning \
  --bucket finops-aws-terraform-state-SEU-ACCOUNT-ID \
  --versioning-configuration Status=Enabled

# Criar tabela DynamoDB para lock
aws dynamodb create-table \
  --table-name finops-aws-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Passo 2: Configurar Variáveis

```bash
# Entre na pasta do Terraform
cd infrastructure/terraform

# Copie o arquivo de exemplo
cp terraform.tfvars.example terraform.tfvars

# Edite as variáveis
nano terraform.tfvars  # ou use seu editor preferido
```

**Conteúdo do terraform.tfvars:**

```hcl
# ============================================
# CONFIGURAÇÕES OBRIGATÓRIAS
# ============================================

# Nome do ambiente (dev, staging, prod)
environment = "prod"

# Região AWS principal
aws_region = "us-east-1"

# Email para receber alertas de economia
alert_email = "finops@suaempresa.com"

# ============================================
# CONFIGURAÇÕES OPCIONAIS
# ============================================

# Horários de execução (cron expressions)
# Padrão: 5 execuções por dia
schedule_expressions = [
  "cron(0 6 * * ? *)",   # 6h da manhã
  "cron(0 10 * * ? *)",  # 10h da manhã
  "cron(0 14 * * ? *)",  # 2h da tarde
  "cron(0 18 * * ? *)",  # 6h da tarde
  "cron(0 22 * * ? *)"   # 10h da noite
]

# Tags para identificação e governança
tags = {
  Project     = "FinOps"
  Environment = "Production"
  Owner       = "CloudTeam"
  CostCenter  = "12345"
}

# ============================================
# CONFIGURAÇÕES AVANÇADAS (raramente alteradas)
# ============================================

# Memória das Lambda Functions
lambda_memory_mapper     = 256
lambda_memory_worker     = 512
lambda_memory_aggregator = 1024

# Timeout das Lambda Functions (segundos)
lambda_timeout_mapper     = 30
lambda_timeout_worker     = 300
lambda_timeout_aggregator = 600

# Retenção de logs (dias)
log_retention_days = 30
```

### Passo 3: Inicializar Terraform

```bash
terraform init
```

**Saída esperada:**

```
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching ">= 4.0.0"...
- Installing hashicorp/aws v5.31.0...
- Installed hashicorp/aws v5.31.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!
```

### Passo 4: Revisar o Plano

```bash
terraform plan
```

Este comando mostra TUDO que será criado. Revise com atenção!

**Saída esperada (resumida):**

```
Terraform will perform the following actions:

  # aws_lambda_function.finops_mapper will be created
  + resource "aws_lambda_function" "finops_mapper" {
      + function_name = "finops-aws-mapper-prod"
      + memory_size   = 256
      + timeout       = 30
      ...
    }

  # aws_lambda_function.finops_worker will be created
  ...

  # aws_sfn_state_machine.finops will be created
  ...

  # aws_s3_bucket.finops_state will be created
  ...

Plan: 25 to add, 0 to change, 0 to destroy.
```

### Passo 5: Aplicar o Deploy

```bash
terraform apply
```

Digite `yes` quando solicitado:

```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Tempo estimado:** 5-10 minutos

**Saída esperada ao final:**

```
Apply complete! Resources: 25 added, 0 changed, 0 destroyed.

Outputs:

lambda_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:finops-aws-handler-prod"
state_machine_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:finops-aws-prod"
s3_bucket_name = "finops-aws-state-prod-123456789012"
```

### Passo 6: Verificar o Deploy

```bash
# Verificar Lambda Functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `finops`)].[FunctionName,Runtime,MemorySize]' --output table

# Verificar Step Functions
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `finops`)].[name,status]' --output table

# Verificar S3 Bucket
aws s3 ls | grep finops

# Verificar EventBridge Rules
aws events list-rules --query 'Rules[?contains(Name, `finops`)].[Name,State]' --output table
```

---

## Executando Manualmente

Após o deploy, você pode testar executando manualmente:

```bash
# Disparar execução manual da Step Function
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:us-east-1:123456789012:stateMachine:finops-aws-prod" \
  --input '{"source": "manual-test"}'

# Verificar execução
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:us-east-1:123456789012:stateMachine:finops-aws-prod" \
  --query 'executions[0].[executionArn,status,startDate]' \
  --output table
```

---

## Custos Estimados

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CUSTOS ESTIMADOS MENSAIS                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CENÁRIO: 5 execuções por dia, 100 serviços analisados por execução          ║
║                                                                              ║
║  RECURSO                    │ UNIDADES          │ CUSTO/MÊS                  ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  Lambda (execuções)         │ 150/dia × 30      │ ~$0.50                     ║
║  Lambda (memória/tempo)     │ 512MB × 5min      │ ~$1.00                     ║
║  Step Functions             │ 150 transições/dia│ ~$0.20                     ║
║  S3 (armazenamento)         │ ~1GB              │ ~$0.02                     ║
║  S3 (requests)              │ ~1000/dia         │ ~$0.05                     ║
║  CloudWatch Logs            │ ~500MB            │ ~$0.25                     ║
║  EventBridge                │ 5 regras          │ ~$0.00                     ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  TOTAL ESTIMADO             │                   │ ~$2-3/mês                  ║
║                                                                              ║
║  ⚠️  NOTA: Economia identificada típica é $5.000-50.000/mês                 ║
║      ROI: Custo de $3 para economizar $10.000+ = 333.000% ROI               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Atualizando a Infraestrutura

Para atualizar após mudanças no código:

```bash
# Atualizar código Python (rebuild layer)
cd ../../
zip -r lambda-layer.zip src/

# Voltar e aplicar
cd infrastructure/terraform
terraform apply
```

---

## Destruindo a Infraestrutura

Para remover tudo criado pelo Terraform:

```bash
# ATENÇÃO: Isso remove TUDO!
terraform destroy
```

**Importante:** Isso é irreversível. Todos os relatórios armazenados no S3 serão perdidos.

---

## Troubleshooting

### Erro: "Access Denied"

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ERRO: Access Denied                                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CAUSA: Usuário não tem permissões necessárias                               ║
║                                                                              ║
║  SOLUÇÃO:                                                                    ║
║  1. Verifique se está usando o usuário correto:                              ║
║     aws sts get-caller-identity                                              ║
║                                                                              ║
║  2. Adicione permissões necessárias ao usuário                               ║
║     (veja seção de Permissões acima)                                         ║
║                                                                              ║
║  3. Se usa MFA, certifique-se de ter sessão válida                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Erro: "Bucket already exists"

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ERRO: Bucket already exists                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CAUSA: Nome de bucket S3 já está em uso (globalmente único)                 ║
║                                                                              ║
║  SOLUÇÃO:                                                                    ║
║  1. Edite terraform.tfvars                                                   ║
║  2. Mude o prefixo do bucket:                                                ║
║     bucket_prefix = "finops-aws-minha-empresa"                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Erro: "Lambda timeout"

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ERRO: Task timed out                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CAUSA: Lambda demorou mais que o timeout configurado                        ║
║                                                                              ║
║  SOLUÇÃO:                                                                    ║
║  1. Aumente o timeout em terraform.tfvars:                                   ║
║     lambda_timeout_worker = 600  # 10 minutos                                ║
║                                                                              ║
║  2. Aplique a mudança:                                                       ║
║     terraform apply                                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Estrutura dos Arquivos Terraform

```
infrastructure/terraform/
├── main.tf              # Recursos principais (Lambda, Step Functions)
├── variables.tf         # Definição de variáveis
├── outputs.tf           # Saídas do deploy (ARNs, URLs)
├── providers.tf         # Configuração do provider AWS
├── backend.tf           # Configuração do backend S3
├── iam.tf               # Roles e policies IAM
├── s3.tf                # Bucket S3
├── eventbridge.tf       # Regras de agendamento
├── cloudwatch.tf        # Log groups e métricas
├── kms.tf               # Chaves de criptografia
├── sns.tf               # Tópicos de alertas
├── sqs.tf               # Dead letter queue
├── terraform.tfvars     # SUAS configurações (não commitar!)
└── terraform.tfvars.example  # Exemplo de configurações
```

---

## Conclusão

Após seguir este guia, você terá:

1. ✅ Infraestrutura completa do FinOps AWS na sua conta
2. ✅ 5 execuções automáticas por dia
3. ✅ Alertas configurados por email
4. ✅ Relatórios salvos no S3
5. ✅ Logs completos no CloudWatch

**Próximos passos:**
1. Verifique os primeiros relatórios após 24h
2. Configure alertas adicionais (Slack, etc.)
3. Ajuste thresholds de economia conforme sua realidade

---

**FinOps AWS v2.1** | Guia Terraform atualizado em Dezembro 2024
