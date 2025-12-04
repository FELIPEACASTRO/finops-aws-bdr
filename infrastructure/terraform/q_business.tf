# ═══════════════════════════════════════════════════════════════════════════
# Amazon Q Business Infrastructure
# FinOps AWS - AI Consultant Integration
# 
# Recursos criados:
# - Q Business Application
# - Q Business Index
# - Q Business Data Source (S3)
# - Q Business Retriever
# - Lambda para Report Generation
# - IAM Roles e Policies
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "enable_q_business" {
  description = "Habilitar integração Amazon Q Business"
  type        = bool
  default     = false
}

variable "identity_center_instance_arn" {
  description = "ARN do IAM Identity Center (obrigatório para Q Business)"
  type        = string
  default     = ""
}

variable "q_business_index_type" {
  description = "Tipo de índice Q Business (STARTER ou ENTERPRISE)"
  type        = string
  default     = "ENTERPRISE"
}

# ─────────────────────────────────────────────────────────────────────────────
# Locals
# ─────────────────────────────────────────────────────────────────────────────

locals {
  q_business_enabled = var.enable_q_business && var.identity_center_instance_arn != ""
  q_app_name         = "finops-aws-${var.environment}-consultant"
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM Role for Q Business
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_iam_role" "q_business_role" {
  count = local.q_business_enabled ? 1 : 0

  name = "finops-q-business-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "qbusiness.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "q_business_policy" {
  count = local.q_business_enabled ? 1 : 0

  name = "finops-q-business-policy"
  role = aws_iam_role.q_business_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.finops_state.arn,
          "${aws_s3_bucket.finops_state.arn}/*"
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.finops_key.arn
      }
    ]
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# Q Business Application
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_qbusiness_application" "finops_consultant" {
  count = local.q_business_enabled ? 1 : 0

  display_name = local.q_app_name
  description  = "FinOps AWS AI Consultant - Análise inteligente de custos"

  identity_center_instance_arn = var.identity_center_instance_arn

  attachments_configuration {
    attachments_control_mode = "ENABLED"
  }

  tags = merge(local.common_tags, {
    Component = "AIConsultant"
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# Q Business Index
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_qbusiness_index" "finops_knowledge" {
  count = local.q_business_enabled ? 1 : 0

  application_id = aws_qbusiness_application.finops_consultant[0].application_id
  display_name   = "finops-knowledge-base"
  description    = "Base de conhecimento FinOps - custos, recomendações e best practices"

  type = var.q_business_index_type

  capacity_configuration {
    units = 1
  }

  tags = merge(local.common_tags, {
    Component = "KnowledgeBase"
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# Q Business Retriever
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_qbusiness_retriever" "native" {
  count = local.q_business_enabled ? 1 : 0

  application_id = aws_qbusiness_application.finops_consultant[0].application_id
  display_name   = "finops-native-retriever"
  type           = "NATIVE_INDEX"

  configuration {
    native_index_configuration {
      index_id = aws_qbusiness_index.finops_knowledge[0].index_id
    }
  }

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────────────────────
# Q Business Data Source (S3)
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_qbusiness_data_source" "s3_reports" {
  count = local.q_business_enabled ? 1 : 0

  application_id = aws_qbusiness_application.finops_consultant[0].application_id
  index_id       = aws_qbusiness_index.finops_knowledge[0].index_id
  display_name   = "finops-s3-reports"
  description    = "Relatórios de custo e documentos de conhecimento"

  role_arn = aws_iam_role.q_business_role[0].arn

  configuration = jsonencode({
    type = "S3"
    connectionConfiguration = {
      repositoryEndpointMetadata = {
        BucketName = aws_s3_bucket.finops_state.id
      }
    }
    repositoryConfigurations = {
      document = {
        fieldMappings = [
          {
            indexFieldName   = "_document_title"
            indexFieldType   = "STRING"
            dataSourceFieldName = "title"
          }
        ]
      }
    }
    syncConfiguration = {
      schedule = "cron(0 6 * * ? *)"
    }
    additionalProperties = {
      inclusionPrefixes = ["processed/", "knowledge/"]
      exclusionPatterns = ["*.tmp", "*.log"]
    }
  })

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────────────────────
# Lambda for Q Report Generation
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_lambda_function" "q_report_generator" {
  count = local.q_business_enabled ? 1 : 0

  function_name = "finops-q-report-generator-${var.environment}"
  description   = "Gera relatórios FinOps com Amazon Q Business"

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  handler = "finops_aws.ai_consultant.q_report_handler.lambda_handler"
  runtime = "python3.11"
  timeout = 300
  memory_size = 512

  role = aws_iam_role.q_report_lambda_role[0].arn

  layers = [aws_lambda_layer_version.finops_layer.arn]

  environment {
    variables = {
      Q_BUSINESS_APP_ID         = aws_qbusiness_application.finops_consultant[0].application_id
      Q_BUSINESS_INDEX_ID       = aws_qbusiness_index.finops_knowledge[0].index_id
      Q_BUSINESS_RETRIEVER_ID   = aws_qbusiness_retriever.native[0].retriever_id
      Q_BUSINESS_DATA_SOURCE_ID = aws_qbusiness_data_source.s3_reports[0].data_source_id
      Q_BUSINESS_REGION         = var.aws_region
      FINOPS_REPORTS_BUCKET     = aws_s3_bucket.finops_state.id
      ENVIRONMENT               = var.environment
      LOG_LEVEL                 = "INFO"
    }
  }

  vpc_config {
    subnet_ids         = var.lambda_subnet_ids
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  tags = merge(local.common_tags, {
    Component = "QReportGenerator"
  })
}

# IAM Role for Q Report Lambda
resource "aws_iam_role" "q_report_lambda_role" {
  count = local.q_business_enabled ? 1 : 0

  name = "finops-q-report-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "q_report_lambda_policy" {
  count = local.q_business_enabled ? 1 : 0

  name = "finops-q-report-lambda-policy"
  role = aws_iam_role.q_report_lambda_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "QBusinessAccess"
        Effect = "Allow"
        Action = [
          "qbusiness:ChatSync",
          "qbusiness:GetApplication",
          "qbusiness:GetIndex",
          "qbusiness:SearchRelevantContent",
          "qbusiness:StartDataSourceSyncJob",
          "qbusiness:ListDataSourceSyncJobs"
        ]
        Resource = [
          aws_qbusiness_application.finops_consultant[0].arn,
          "${aws_qbusiness_application.finops_consultant[0].arn}/*"
        ]
      },
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.finops_state.arn,
          "${aws_s3_bucket.finops_state.arn}/*"
        ]
      },
      {
        Sid    = "SESAccess"
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Sid    = "VPCAccess"
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      },
      {
        Sid    = "KMSAccess"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.finops_key.arn
      }
    ]
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# Step Functions Integration (Add Q Report step)
# ─────────────────────────────────────────────────────────────────────────────

# Nota: A integração com Step Functions existente deve ser feita
# adicionando um estado após o Aggregator para chamar a Lambda de Q Report.
# 
# Exemplo de estado a adicionar ao state machine:
#
# "GenerateAIReport": {
#   "Type": "Task",
#   "Resource": "arn:aws:lambda:${region}:${account}:function:finops-q-report-generator",
#   "Parameters": {
#     "type": "full_report",
#     "cost_data.$": "$.aggregated_data",
#     "period.$": "$.period",
#     "persona": "executive"
#   },
#   "Next": "EndState",
#   "Catch": [
#     {
#       "ErrorEquals": ["States.ALL"],
#       "Next": "EndState",
#       "ResultPath": "$.ai_report_error"
#     }
#   ]
# }

# ─────────────────────────────────────────────────────────────────────────────
# Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "q_business_application_id" {
  description = "ID da aplicação Q Business"
  value       = local.q_business_enabled ? aws_qbusiness_application.finops_consultant[0].application_id : null
}

output "q_business_index_id" {
  description = "ID do índice Q Business"
  value       = local.q_business_enabled ? aws_qbusiness_index.finops_knowledge[0].index_id : null
}

output "q_business_retriever_id" {
  description = "ID do retriever Q Business"
  value       = local.q_business_enabled ? aws_qbusiness_retriever.native[0].retriever_id : null
}

output "q_report_lambda_arn" {
  description = "ARN da Lambda de geração de relatórios"
  value       = local.q_business_enabled ? aws_lambda_function.q_report_generator[0].arn : null
}

output "q_business_enabled" {
  description = "Status da integração Q Business"
  value       = local.q_business_enabled
}
