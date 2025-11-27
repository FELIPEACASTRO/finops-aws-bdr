################################################################################
# FinOps AWS - Terraform Variables
# Variaveis de configuracao para deploy
################################################################################

################################################################################
# Configuracoes Gerais
################################################################################

variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "finops-aws"
}

variable "environment" {
  description = "Ambiente de deploy (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment deve ser: dev, staging ou prod."
  }
}

variable "aws_region" {
  description = "Regiao AWS principal para deploy"
  type        = string
  default     = "us-east-1"
}

variable "owner" {
  description = "Responsavel pelo projeto"
  type        = string
  default     = "finops-team"
}

variable "cost_center" {
  description = "Centro de custo para billing"
  type        = string
  default     = "finops"
}

variable "app_version" {
  description = "Versao da aplicacao"
  type        = string
  default     = "1.0.0"
}

################################################################################
# Configuracoes Lambda
################################################################################

variable "lambda_runtime" {
  description = "Runtime do Lambda"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Timeout do Lambda em segundos (max 900)"
  type        = number
  default     = 300

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout deve estar entre 1 e 900 segundos."
  }
}

variable "lambda_memory_size" {
  description = "Memoria do Lambda em MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory deve estar entre 128 e 10240 MB."
  }
}

variable "lambda_reserved_concurrent_executions" {
  description = "Execucoes concorrentes reservadas (-1 para sem limite)"
  type        = number
  default     = 5
}

variable "lambda_architecture" {
  description = "Arquitetura do Lambda (x86_64 ou arm64)"
  type        = string
  default     = "x86_64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.lambda_architecture)
    error_message = "Arquitetura deve ser x86_64 ou arm64."
  }
}

################################################################################
# Configuracoes de Agendamento
################################################################################

variable "schedule_enabled" {
  description = "Habilitar execucao agendada"
  type        = bool
  default     = true
}

variable "schedule_expression" {
  description = "Expressao cron para agendamento (UTC)"
  type        = string
  default     = "cron(0 6 * * ? *)"
}

variable "schedule_expressions" {
  description = "Lista de expressoes cron para multiplas execucoes diarias"
  type        = list(string)
  default     = [
    "cron(0 6 * * ? *)",
    "cron(0 12 * * ? *)",
    "cron(0 18 * * ? *)"
  ]
}

################################################################################
# Configuracoes Multi-Account
################################################################################

variable "enable_multi_account" {
  description = "Habilitar analise multi-account via Organizations"
  type        = bool
  default     = false
}

variable "organization_role_name" {
  description = "Nome da role para assume em outras contas"
  type        = string
  default     = "FinOpsReadOnlyRole"
}

variable "target_account_ids" {
  description = "Lista de Account IDs para analise (vazio = apenas conta atual)"
  type        = list(string)
  default     = []
}

################################################################################
# Configuracoes Multi-Region
################################################################################

variable "enable_multi_region" {
  description = "Habilitar analise em multiplas regioes"
  type        = bool
  default     = true
}

variable "target_regions" {
  description = "Lista de regioes para analise"
  type        = list(string)
  default     = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-central-1",
    "ap-southeast-1",
    "ap-northeast-1",
    "sa-east-1"
  ]
}

################################################################################
# Configuracoes de Servicos AWS para Analise
################################################################################

variable "enabled_services" {
  description = "Lista de servicos AWS para analisar (vazio = todos)"
  type        = list(string)
  default     = []
}

variable "excluded_services" {
  description = "Lista de servicos AWS para excluir da analise"
  type        = list(string)
  default     = []
}

################################################################################
# Configuracoes de Armazenamento
################################################################################

variable "s3_bucket_name" {
  description = "Nome do bucket S3 para resultados (deixe vazio para auto-gerar)"
  type        = string
  default     = ""
}

variable "s3_retention_days" {
  description = "Dias para reter relatorios no S3"
  type        = number
  default     = 90
}

variable "enable_s3_versioning" {
  description = "Habilitar versionamento no bucket S3"
  type        = bool
  default     = true
}

################################################################################
# Configuracoes de Estado (DynamoDB)
################################################################################

variable "dynamodb_billing_mode" {
  description = "Modo de billing do DynamoDB (PAY_PER_REQUEST ou PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.dynamodb_billing_mode)
    error_message = "Billing mode deve ser PAY_PER_REQUEST ou PROVISIONED."
  }
}

variable "dynamodb_read_capacity" {
  description = "Capacidade de leitura (apenas se PROVISIONED)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "Capacidade de escrita (apenas se PROVISIONED)"
  type        = number
  default     = 5
}

################################################################################
# Configuracoes de Logging e Monitoring
################################################################################

variable "log_retention_days" {
  description = "Dias para reter logs no CloudWatch"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention deve ser um valor valido do CloudWatch."
  }
}

variable "enable_xray_tracing" {
  description = "Habilitar tracing com AWS X-Ray"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Nivel de log da aplicacao"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level deve ser: DEBUG, INFO, WARNING, ERROR ou CRITICAL."
  }
}

################################################################################
# Configuracoes de Alertas
################################################################################

variable "enable_alerts" {
  description = "Habilitar alertas via SNS"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email para receber alertas"
  type        = string
  default     = ""
}

variable "alert_slack_webhook_url" {
  description = "URL do webhook Slack para alertas"
  type        = string
  default     = ""
  sensitive   = true
}

################################################################################
# Configuracoes de Seguranca
################################################################################

variable "enable_kms_encryption" {
  description = "Habilitar criptografia KMS para dados sensiveis"
  type        = bool
  default     = true
}

variable "kms_key_deletion_window" {
  description = "Dias para aguardar antes de deletar chave KMS"
  type        = number
  default     = 30

  validation {
    condition     = var.kms_key_deletion_window >= 7 && var.kms_key_deletion_window <= 30
    error_message = "KMS deletion window deve estar entre 7 e 30 dias."
  }
}

variable "enable_vpc" {
  description = "Executar Lambda dentro de VPC"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "ID da VPC (obrigatorio se enable_vpc = true)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Lista de subnet IDs (obrigatorio se enable_vpc = true)"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Lista de security group IDs (obrigatorio se enable_vpc = true)"
  type        = list(string)
  default     = []
}
