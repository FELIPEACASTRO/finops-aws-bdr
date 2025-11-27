################################################################################
# FinOps AWS - Step Functions Orchestration
# Orquestracao de execucoes para 100 runs/dia com alta confiabilidade
################################################################################

################################################################################
# Step Functions State Machine
################################################################################

resource "aws_sfn_state_machine" "main" {
  name     = "${local.lambda_name}-orchestrator"
  role_arn = aws_iam_role.stepfunctions.arn
  type     = "STANDARD"

  definition = templatefile("${path.module}/stepfunctions_definition.json.tpl", {
    mapper_arn      = aws_lambda_function.mapper.arn
    worker_arn      = aws_lambda_function.main.arn
    aggregator_arn  = aws_lambda_function.aggregator.arn
    dlq_url         = aws_sqs_queue.dlq.url
    sns_topic_arn   = var.enable_alerts ? aws_sns_topic.alerts[0].arn : ""
    max_concurrency = var.stepfunctions_max_concurrency
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.stepfunctions.arn}:*"
    include_execution_data = true
    level                  = var.stepfunctions_log_level
  }

  tracing_configuration {
    enabled = var.enable_xray_tracing
  }

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}-orchestrator"
  })
}

################################################################################
# Step Functions CloudWatch Log Group
################################################################################

resource "aws_cloudwatch_log_group" "stepfunctions" {
  name              = "/aws/vendedlogs/states/${local.lambda_name}-orchestrator"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

################################################################################
# Step Functions IAM Role
################################################################################

resource "aws_iam_role" "stepfunctions" {
  name = "${local.lambda_name}-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "stepfunctions_lambda" {
  name = "lambda-invoke"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.main.arn,
          aws_lambda_function.mapper.arn,
          aws_lambda_function.aggregator.arn,
          "${aws_lambda_function.main.arn}:*",
          "${aws_lambda_function.mapper.arn}:*",
          "${aws_lambda_function.aggregator.arn}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "stepfunctions_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutLogEvents",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "stepfunctions_sqs" {
  name = "sqs-send"
  role = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.dlq.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "stepfunctions_sns" {
  count = var.enable_alerts ? 1 : 0
  name  = "sns-publish"
  role  = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.alerts[0].arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "stepfunctions_xray" {
  count = var.enable_xray_tracing ? 1 : 0
  name  = "xray-tracing"
  role  = aws_iam_role.stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      }
    ]
  })
}

################################################################################
# EventBridge Rule to Trigger Step Functions
################################################################################

resource "aws_cloudwatch_event_rule" "stepfunctions_schedule" {
  for_each = var.schedule_enabled ? toset(var.schedule_expressions) : toset([])

  name                = "${local.lambda_name}-sfn-schedule-${index(var.schedule_expressions, each.value)}"
  description         = "Trigger Step Functions para FinOps AWS - Schedule ${index(var.schedule_expressions, each.value) + 1}"
  schedule_expression = each.value
  state               = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "stepfunctions" {
  for_each = var.schedule_enabled ? toset(var.schedule_expressions) : toset([])

  rule      = aws_cloudwatch_event_rule.stepfunctions_schedule[each.key].name
  target_id = "FinOpsSFN"
  arn       = aws_sfn_state_machine.main.arn
  role_arn  = aws_iam_role.eventbridge_sfn.arn

  input = jsonencode({
    source        = "scheduled"
    schedule_id   = index(var.schedule_expressions, each.value)
    analysis_type = "full"
  })
}

resource "aws_iam_role" "eventbridge_sfn" {
  name = "${local.lambda_name}-eventbridge-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "stepfunctions-start"
  role = aws_iam_role.eventbridge_sfn.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.main.arn
      }
    ]
  })
}
