################################################################################
# FinOps AWS - Lambda Workers (Mapper and Aggregator)
# Funcoes Lambda para arquitetura Step Functions
################################################################################

################################################################################
# Lambda Mapper - Divide servicos em batches
################################################################################

resource "aws_cloudwatch_log_group" "mapper" {
  name              = "/aws/lambda/${local.lambda_name}-mapper"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_lambda_function" "mapper" {
  filename         = data.archive_file.function.output_path
  source_code_hash = data.archive_file.function.output_base64sha256

  function_name = "${local.lambda_name}-mapper"
  description   = "FinOps AWS - Mapper: Divide 252 servicos em batches para processamento paralelo"

  role    = aws_iam_role.lambda_execution.arn
  handler = "finops_aws.lambda_mapper.lambda_handler"
  runtime = var.lambda_runtime

  timeout     = 60
  memory_size = 256

  architectures = [var.lambda_architecture]

  layers = [
    aws_lambda_layer_version.dependencies.arn
  ]

  environment {
    variables = {
      LOG_LEVEL           = var.log_level
      ENVIRONMENT         = var.environment
      REPORTS_BUCKET_NAME = aws_s3_bucket.reports.id
      STATE_PREFIX        = "state/"
      BATCH_SIZE          = tostring(var.batch_size)
      ENABLED_SERVICES    = join(",", var.enabled_services)
      EXCLUDED_SERVICES   = join(",", var.excluded_services)
    }
  }

  dynamic "tracing_config" {
    for_each = var.enable_xray_tracing ? [1] : []
    content {
      mode = "Active"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.mapper
  ]

  tags = merge(local.common_tags, {
    Name     = "${local.lambda_name}-mapper"
    Function = "Mapper"
  })
}

################################################################################
# Lambda Aggregator - Consolida resultados
################################################################################

resource "aws_cloudwatch_log_group" "aggregator" {
  name              = "/aws/lambda/${local.lambda_name}-aggregator"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_lambda_function" "aggregator" {
  filename         = data.archive_file.function.output_path
  source_code_hash = data.archive_file.function.output_base64sha256

  function_name = "${local.lambda_name}-aggregator"
  description   = "FinOps AWS - Aggregator: Consolida resultados e gera relatorio final"

  role    = aws_iam_role.lambda_execution.arn
  handler = "finops_aws.lambda_aggregator.lambda_handler"
  runtime = var.lambda_runtime

  timeout     = 120
  memory_size = 512

  architectures = [var.lambda_architecture]

  layers = [
    aws_lambda_layer_version.dependencies.arn
  ]

  environment {
    variables = {
      LOG_LEVEL           = var.log_level
      ENVIRONMENT         = var.environment
      REPORTS_BUCKET_NAME = aws_s3_bucket.reports.id
      STATE_PREFIX        = "state/"
      REPORTS_PREFIX      = "reports/"
      SNS_TOPIC_ARN       = var.enable_alerts ? aws_sns_topic.alerts[0].arn : ""
    }
  }

  dynamic "tracing_config" {
    for_each = var.enable_xray_tracing ? [1] : []
    content {
      mode = "Active"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.aggregator
  ]

  tags = merge(local.common_tags, {
    Name     = "${local.lambda_name}-aggregator"
    Function = "Aggregator"
  })
}
