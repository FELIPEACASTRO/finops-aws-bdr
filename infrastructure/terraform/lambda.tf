################################################################################
# FinOps AWS - Lambda Function Configuration
################################################################################

################################################################################
# Lambda Layer - Python Dependencies
################################################################################

resource "null_resource" "pip_install" {
  triggers = {
    requirements_hash = filesha256("${path.module}/../../requirements.txt")
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${path.module}/layer/python
      mkdir -p ${path.module}/layer/python
      pip install -r ${path.module}/../../requirements.txt -t ${path.module}/layer/python --quiet
    EOT
  }
}

data "archive_file" "layer" {
  type        = "zip"
  source_dir  = "${path.module}/layer"
  output_path = "${path.module}/dist/layer.zip"

  depends_on = [null_resource.pip_install]
}

resource "aws_lambda_layer_version" "dependencies" {
  filename            = data.archive_file.layer.output_path
  source_code_hash    = data.archive_file.layer.output_base64sha256
  layer_name          = "${local.lambda_name}-dependencies"
  compatible_runtimes = [var.lambda_runtime]
  
  description = "Python dependencies for FinOps AWS Lambda"

  lifecycle {
    create_before_destroy = true
  }
}

################################################################################
# Lambda Function Package
################################################################################

data "archive_file" "function" {
  type        = "zip"
  source_dir  = "${path.module}/../../src"
  output_path = "${path.module}/dist/function.zip"
  
  excludes = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    "tests"
  ]
}

################################################################################
# CloudWatch Log Group
################################################################################

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = var.log_retention_days
  
  kms_key_id = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null

  tags = local.common_tags
}

################################################################################
# Lambda Function
################################################################################

resource "aws_lambda_function" "main" {
  filename         = data.archive_file.function.output_path
  source_code_hash = data.archive_file.function.output_base64sha256
  
  function_name = local.lambda_name
  description   = "FinOps AWS - Analise de custos e otimizacao para 252 servicos AWS"
  
  role    = aws_iam_role.lambda_execution.arn
  handler = "finops_aws.resilient_lambda_handler.lambda_handler"
  runtime = var.lambda_runtime
  
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size
  
  architectures = [var.lambda_architecture]
  
  reserved_concurrent_executions = var.lambda_reserved_concurrent_executions
  
  layers = [
    aws_lambda_layer_version.dependencies.arn
  ]

  environment {
    variables = {
      LOG_LEVEL                = var.log_level
      ENVIRONMENT              = var.environment
      
      STATE_TABLE_NAME         = aws_dynamodb_table.state.name
      REPORTS_BUCKET_NAME      = aws_s3_bucket.reports.id
      
      ENABLE_MULTI_ACCOUNT     = tostring(var.enable_multi_account)
      ENABLE_MULTI_REGION      = tostring(var.enable_multi_region)
      TARGET_REGIONS           = join(",", var.target_regions)
      ORGANIZATION_ROLE_NAME   = var.organization_role_name
      
      ENABLED_SERVICES         = join(",", var.enabled_services)
      EXCLUDED_SERVICES        = join(",", var.excluded_services)
      
      SNS_TOPIC_ARN            = var.enable_alerts ? aws_sns_topic.alerts[0].arn : ""
      
      KMS_KEY_ARN              = var.enable_kms_encryption ? aws_kms_key.main[0].arn : ""
    }
  }

  dynamic "tracing_config" {
    for_each = var.enable_xray_tracing ? [1] : []
    content {
      mode = "Active"
    }
  }

  dynamic "vpc_config" {
    for_each = var.enable_vpc ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda_logs,
    aws_iam_role_policy.lambda_s3,
    aws_iam_role_policy.lambda_dynamodb
  ]

  tags = merge(local.common_tags, {
    Name = local.lambda_name
  })
}

################################################################################
# Lambda Alias (for stable reference)
################################################################################

resource "aws_lambda_alias" "live" {
  name             = "live"
  description      = "Alias para versao de producao"
  function_name    = aws_lambda_function.main.function_name
  function_version = aws_lambda_function.main.version
}

################################################################################
# Lambda Permission for EventBridge
################################################################################

resource "aws_lambda_permission" "eventbridge" {
  count = var.schedule_enabled ? 1 : 0
  
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule[0].arn
}

################################################################################
# Lambda Function URL (optional - for testing)
################################################################################

resource "aws_lambda_function_url" "main" {
  count = var.environment == "dev" ? 1 : 0
  
  function_name      = aws_lambda_function.main.function_name
  authorization_type = "AWS_IAM"
  
  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["content-type"]
    max_age           = 86400
  }
}
