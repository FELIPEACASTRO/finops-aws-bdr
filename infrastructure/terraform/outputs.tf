################################################################################
# FinOps AWS - Terraform Outputs
################################################################################

################################################################################
# Lambda Outputs
################################################################################

output "lambda_function_name" {
  description = "Nome da funcao Lambda"
  value       = aws_lambda_function.main.function_name
}

output "lambda_function_arn" {
  description = "ARN da funcao Lambda"
  value       = aws_lambda_function.main.arn
}

output "lambda_function_invoke_arn" {
  description = "ARN para invocar a funcao Lambda"
  value       = aws_lambda_function.main.invoke_arn
}

output "lambda_function_version" {
  description = "Versao atual da funcao Lambda"
  value       = aws_lambda_function.main.version
}

output "lambda_alias_arn" {
  description = "ARN do alias 'live'"
  value       = aws_lambda_alias.live.arn
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
# Storage Outputs
################################################################################

output "s3_bucket_name" {
  description = "Nome do bucket S3 para relatorios"
  value       = aws_s3_bucket.reports.id
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.reports.arn
}

output "dynamodb_state_table_name" {
  description = "Nome da tabela DynamoDB de estado"
  value       = aws_dynamodb_table.state.name
}

output "dynamodb_state_table_arn" {
  description = "ARN da tabela DynamoDB de estado"
  value       = aws_dynamodb_table.state.arn
}

output "dynamodb_history_table_name" {
  description = "Nome da tabela DynamoDB de historico"
  value       = aws_dynamodb_table.cost_history.name
}

################################################################################
# Logging and Monitoring Outputs
################################################################################

output "cloudwatch_log_group_name" {
  description = "Nome do log group do CloudWatch"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN do log group do CloudWatch"
  value       = aws_cloudwatch_log_group.lambda.arn
}

################################################################################
# EventBridge Outputs
################################################################################

output "eventbridge_rule_name" {
  description = "Nome da regra do EventBridge"
  value       = var.schedule_enabled ? aws_cloudwatch_event_rule.schedule[0].name : null
}

output "eventbridge_rule_arn" {
  description = "ARN da regra do EventBridge"
  value       = var.schedule_enabled ? aws_cloudwatch_event_rule.schedule[0].arn : null
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
    environment           = var.environment
    region                = local.region
    account_id            = local.account_id
    lambda_function       = aws_lambda_function.main.function_name
    lambda_memory_mb      = var.lambda_memory_size
    lambda_timeout_sec    = var.lambda_timeout
    schedule_enabled      = var.schedule_enabled
    multi_account_enabled = var.enable_multi_account
    multi_region_enabled  = var.enable_multi_region
    target_regions        = var.target_regions
    kms_encryption        = var.enable_kms_encryption
    xray_tracing          = var.enable_xray_tracing
    alerts_enabled        = var.enable_alerts
  }
}

################################################################################
# Invocation Examples
################################################################################

output "invoke_examples" {
  description = "Exemplos de como invocar a funcao Lambda"
  value = {
    aws_cli = "aws lambda invoke --function-name ${aws_lambda_function.main.function_name} --payload '{\"analysis_type\": \"full\"}' response.json"
    
    aws_cli_async = "aws lambda invoke --function-name ${aws_lambda_function.main.function_name} --invocation-type Event --payload '{\"analysis_type\": \"full\"}' response.json"
    
    boto3 = <<-EOT
import boto3
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='${aws_lambda_function.main.function_name}',
    InvocationType='RequestResponse',
    Payload='{"analysis_type": "full"}'
)
EOT
  }
}
