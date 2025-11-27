################################################################################
# FinOps AWS - Terraform Outputs
# Arquitetura otimizada: Step Functions + S3 (sem DynamoDB)
################################################################################

################################################################################
# Lambda Outputs
################################################################################

output "lambda_function_name" {
  description = "Nome da funcao Lambda principal (Worker)"
  value       = aws_lambda_function.main.function_name
}

output "lambda_function_arn" {
  description = "ARN da funcao Lambda principal"
  value       = aws_lambda_function.main.arn
}

output "lambda_mapper_name" {
  description = "Nome da funcao Lambda Mapper"
  value       = aws_lambda_function.mapper.function_name
}

output "lambda_mapper_arn" {
  description = "ARN da funcao Lambda Mapper"
  value       = aws_lambda_function.mapper.arn
}

output "lambda_aggregator_name" {
  description = "Nome da funcao Lambda Aggregator"
  value       = aws_lambda_function.aggregator.function_name
}

output "lambda_aggregator_arn" {
  description = "ARN da funcao Lambda Aggregator"
  value       = aws_lambda_function.aggregator.arn
}

output "lambda_layer_arn" {
  description = "ARN do layer de dependencias"
  value       = aws_lambda_layer_version.dependencies.arn
}

output "lambda_function_url" {
  description = "URL da funcao Lambda (apenas dev)"
  value       = var.environment == "dev" ? aws_lambda_function_url.main[0].function_url : null
}

################################################################################
# Step Functions Outputs
################################################################################

output "stepfunctions_arn" {
  description = "ARN do Step Functions State Machine"
  value       = aws_sfn_state_machine.main.arn
}

output "stepfunctions_name" {
  description = "Nome do Step Functions State Machine"
  value       = aws_sfn_state_machine.main.name
}

################################################################################
# IAM Outputs
################################################################################

output "lambda_execution_role_arn" {
  description = "ARN da role de execucao do Lambda"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Nome da role de execucao do Lambda"
  value       = aws_iam_role.lambda_execution.name
}

################################################################################
# Storage Outputs (S3 only - no DynamoDB)
################################################################################

output "s3_bucket_name" {
  description = "Nome do bucket S3 para estado e relatorios"
  value       = aws_s3_bucket.reports.id
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.reports.arn
}

output "s3_state_prefix" {
  description = "Prefixo S3 para estado das execucoes"
  value       = "state/"
}

output "s3_reports_prefix" {
  description = "Prefixo S3 para relatorios"
  value       = "reports/"
}

################################################################################
# SQS Outputs
################################################################################

output "sqs_dlq_url" {
  description = "URL da Dead Letter Queue"
  value       = aws_sqs_queue.dlq.url
}

output "sqs_dlq_arn" {
  description = "ARN da Dead Letter Queue"
  value       = aws_sqs_queue.dlq.arn
}

################################################################################
# Logging and Monitoring Outputs
################################################################################

output "cloudwatch_log_group_lambda" {
  description = "Nome do log group do Lambda principal"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "cloudwatch_log_group_stepfunctions" {
  description = "Nome do log group do Step Functions"
  value       = aws_cloudwatch_log_group.stepfunctions.name
}

output "cloudwatch_dashboard_name" {
  description = "Nome do dashboard CloudWatch"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

################################################################################
# Security Outputs
################################################################################

output "kms_key_arn" {
  description = "ARN da chave KMS"
  value       = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
}

output "kms_key_alias" {
  description = "Alias da chave KMS"
  value       = var.enable_kms_encryption ? aws_kms_alias.main[0].name : null
}

output "sns_topic_arn" {
  description = "ARN do topico SNS para alertas"
  value       = var.enable_alerts ? aws_sns_topic.alerts[0].arn : null
}

################################################################################
# Summary Output
################################################################################

output "deployment_summary" {
  description = "Resumo do deployment"
  value = {
    architecture          = "Step Functions + S3 (Optimized for 100 runs/day)"
    environment           = var.environment
    region                = local.region
    account_id            = local.account_id
    
    step_functions        = aws_sfn_state_machine.main.name
    lambda_worker         = aws_lambda_function.main.function_name
    lambda_mapper         = aws_lambda_function.mapper.function_name
    lambda_aggregator     = aws_lambda_function.aggregator.function_name
    
    lambda_memory_mb      = var.lambda_memory_size
    lambda_timeout_sec    = var.lambda_timeout
    batch_size            = var.batch_size
    max_concurrency       = var.stepfunctions_max_concurrency
    
    schedule_enabled      = var.schedule_enabled
    multi_account_enabled = var.enable_multi_account
    multi_region_enabled  = var.enable_multi_region
    target_regions        = var.target_regions
    
    storage_type          = "S3 (no DynamoDB)"
    kms_encryption        = var.enable_kms_encryption
    xray_tracing          = var.enable_xray_tracing
    alerts_enabled        = var.enable_alerts
  }
}

################################################################################
# Invocation Examples
################################################################################

output "invoke_examples" {
  description = "Exemplos de como invocar a solucao"
  value = {
    start_step_functions = "aws stepfunctions start-execution --state-machine-arn ${aws_sfn_state_machine.main.arn} --input '{\"analysis_type\": \"full\"}'"
    
    invoke_lambda_directly = "aws lambda invoke --function-name ${aws_lambda_function.main.function_name} --payload '{\"analysis_type\": \"full\"}' response.json"
    
    boto3_stepfunctions = <<-EOT
import boto3
sfn_client = boto3.client('stepfunctions')
response = sfn_client.start_execution(
    stateMachineArn='${aws_sfn_state_machine.main.arn}',
    input='{"analysis_type": "full"}'
)
print(f"Execution ARN: {response['executionArn']}")
EOT
  }
}

################################################################################
# Cost Estimation
################################################################################

output "estimated_monthly_cost" {
  description = "Estimativa de custo mensal para 100 execucoes/dia"
  value = {
    step_functions = "$1.50 (100 exec/dia x 20 transicoes x 30 dias)"
    lambda_compute = "$0.35 (estimado)"
    s3_storage     = "$0.30 (estado + relatorios)"
    sqs            = "$0.01 (negligivel)"
    cloudwatch     = "$1.00 (logs e metricas)"
    total_estimate = "~$3.00/mes"
    note           = "Valores estimados - custos reais podem variar"
  }
}
