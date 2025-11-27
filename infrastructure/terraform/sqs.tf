################################################################################
# FinOps AWS - SQS Configuration
# Filas para processamento assincrono e dead-letter queue
################################################################################

################################################################################
# Dead Letter Queue (DLQ)
################################################################################

resource "aws_sqs_queue" "dlq" {
  name = "${local.lambda_name}-dlq"

  message_retention_seconds  = 1209600  # 14 dias
  receive_wait_time_seconds  = 20       # Long polling
  visibility_timeout_seconds = 300

  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}-dlq"
    Type = "DeadLetterQueue"
  })
}

################################################################################
# Main Processing Queue (optional - for async patterns)
################################################################################

resource "aws_sqs_queue" "main" {
  count = var.enable_sqs_processing ? 1 : 0
  
  name = "${local.lambda_name}-queue"

  delay_seconds              = 0
  max_message_size           = 262144   # 256 KB
  message_retention_seconds  = 345600   # 4 dias
  receive_wait_time_seconds  = 20       # Long polling
  visibility_timeout_seconds = var.lambda_timeout * 6  # 6x Lambda timeout

  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}-queue"
    Type = "ProcessingQueue"
  })
}

################################################################################
# SQS Queue Policy - DLQ
################################################################################

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowStepFunctions"
        Effect    = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.dlq.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sfn_state_machine.main.arn
          }
        }
      },
      {
        Sid       = "AllowLambda"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.dlq.arn
      }
    ]
  })
}

################################################################################
# CloudWatch Alarms for DLQ
################################################################################

resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${local.lambda_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Mensagens na DLQ indicam falhas de processamento"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []
  ok_actions    = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "dlq_age" {
  alarm_name          = "${local.lambda_name}-dlq-message-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 86400  # 24 horas
  alarm_description   = "Mensagens antigas na DLQ precisam de atencao"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}
