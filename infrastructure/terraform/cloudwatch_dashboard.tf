################################################################################
# FinOps AWS - CloudWatch Dashboard and Alarms
# Observabilidade completa para 100 execucoes/dia
################################################################################

################################################################################
# CloudWatch Dashboard
################################################################################

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.lambda_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# FinOps AWS - Dashboard de Monitoramento\n**252 Servicos AWS | 100 Execucoes/Dia | Step Functions + S3**"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Execucoes Step Functions"
          region = local.region
          metrics = [
            ["AWS/States", "ExecutionsStarted", "StateMachineArn", aws_sfn_state_machine.main.arn, { label = "Iniciadas", color = "#2ca02c" }],
            [".", "ExecutionsSucceeded", ".", ".", { label = "Sucesso", color = "#1f77b4" }],
            [".", "ExecutionsFailed", ".", ".", { label = "Falhas", color = "#d62728" }],
            [".", "ExecutionsTimedOut", ".", ".", { label = "Timeout", color = "#ff7f0e" }]
          ]
          view    = "timeSeries"
          stacked = false
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Taxa de Sucesso (%)"
          region = local.region
          metrics = [
            [{
              expression = "100 * succeeded / started"
              label      = "Taxa de Sucesso"
              id         = "rate"
              color      = "#1f77b4"
            }],
            ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", aws_sfn_state_machine.main.arn, { id = "succeeded", visible = false }],
            [".", "ExecutionsStarted", ".", ".", { id = "started", visible = false }]
          ]
          view   = "gauge"
          period = 86400
          stat   = "Sum"
          yAxis = {
            left = { min = 0, max = 100 }
          }
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Duracao das Execucoes"
          region = local.region
          metrics = [
            ["AWS/States", "ExecutionTime", "StateMachineArn", aws_sfn_state_machine.main.arn, { stat = "p50", label = "P50" }],
            ["...", { stat = "p90", label = "P90" }],
            ["...", { stat = "p99", label = "P99" }],
            ["...", { stat = "Maximum", label = "Max" }]
          ]
          view   = "timeSeries"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 7
        width  = 8
        height = 6
        properties = {
          title  = "Lambda - Invocacoes"
          region = local.region
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.main.function_name, { label = "Worker" }],
            [".", ".", ".", aws_lambda_function.mapper.function_name, { label = "Mapper" }],
            [".", ".", ".", aws_lambda_function.aggregator.function_name, { label = "Aggregator" }]
          ]
          view   = "timeSeries"
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 7
        width  = 8
        height = 6
        properties = {
          title  = "Lambda - Erros"
          region = local.region
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.main.function_name, { label = "Worker", color = "#d62728" }],
            [".", ".", ".", aws_lambda_function.mapper.function_name, { label = "Mapper", color = "#ff7f0e" }],
            [".", ".", ".", aws_lambda_function.aggregator.function_name, { label = "Aggregator", color = "#9467bd" }]
          ]
          view   = "timeSeries"
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 7
        width  = 8
        height = 6
        properties = {
          title  = "Lambda - Duracao (ms)"
          region = local.region
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.main.function_name, { stat = "p95", label = "Worker P95" }],
            [".", ".", ".", aws_lambda_function.mapper.function_name, { stat = "p95", label = "Mapper P95" }],
            [".", ".", ".", aws_lambda_function.aggregator.function_name, { stat = "p95", label = "Aggregator P95" }]
          ]
          view   = "timeSeries"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 13
        width  = 8
        height = 6
        properties = {
          title  = "DLQ - Mensagens"
          region = local.region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.dlq.name, { label = "Mensagens", color = "#d62728" }]
          ]
          view   = "timeSeries"
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 13
        width  = 8
        height = 6
        properties = {
          title  = "S3 - Operacoes"
          region = local.region
          metrics = [
            ["AWS/S3", "PutRequests", "BucketName", aws_s3_bucket.reports.id, { label = "PUT" }],
            [".", "GetRequests", ".", ".", { label = "GET" }],
            [".", "ListRequests", ".", ".", { label = "LIST" }]
          ]
          view   = "timeSeries"
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 13
        width  = 8
        height = 6
        properties = {
          title  = "Custo Estimado (diario)"
          region = "us-east-1"
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", { label = "Custo Total", stat = "Maximum" }]
          ]
          view   = "singleValue"
          period = 86400
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 19
        width  = 24
        height = 6
        properties = {
          title  = "Logs Recentes - Step Functions"
          region = local.region
          query  = "SOURCE '/aws/vendedlogs/states/${local.lambda_name}-orchestrator' | fields @timestamp, @message | sort @timestamp desc | limit 50"
        }
      }
    ]
  })
}

################################################################################
# CloudWatch Alarms - Step Functions
################################################################################

resource "aws_cloudwatch_metric_alarm" "sfn_failures" {
  alarm_name          = "${local.lambda_name}-sfn-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Step Functions execucao falhou"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.main.arn
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []
  ok_actions    = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "sfn_duration" {
  alarm_name          = "${local.lambda_name}-sfn-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionTime"
  namespace           = "AWS/States"
  period              = 300
  extended_statistic  = "p95"
  threshold           = 600000  # 10 minutos em ms
  alarm_description   = "Step Functions P95 duracao > 10 minutos"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.main.arn
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "sfn_throttles" {
  alarm_name          = "${local.lambda_name}-sfn-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsAborted"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Step Functions execucoes abortadas"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.main.arn
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

################################################################################
# CloudWatch Alarms - Lambda
################################################################################

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.lambda_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda erros > 5 em 5 minutos"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []
  ok_actions    = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.lambda_name}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Lambda throttling detectado"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.lambda_name}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p95"
  threshold           = var.lambda_timeout * 1000 * 0.8  # 80% do timeout
  alarm_description   = "Lambda P95 duracao > 80% do timeout"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}

################################################################################
# CloudWatch Alarms - Success Rate
################################################################################

resource "aws_cloudwatch_metric_alarm" "success_rate" {
  alarm_name          = "${local.lambda_name}-success-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  threshold           = 95

  metric_query {
    id          = "rate"
    expression  = "100 * succeeded / started"
    label       = "Success Rate"
    return_data = true
  }

  metric_query {
    id = "succeeded"
    metric {
      metric_name = "ExecutionsSucceeded"
      namespace   = "AWS/States"
      period      = 3600
      stat        = "Sum"
      dimensions = {
        StateMachineArn = aws_sfn_state_machine.main.arn
      }
    }
  }

  metric_query {
    id = "started"
    metric {
      metric_name = "ExecutionsStarted"
      namespace   = "AWS/States"
      period      = 3600
      stat        = "Sum"
      dimensions = {
        StateMachineArn = aws_sfn_state_machine.main.arn
      }
    }
  }

  alarm_description  = "Taxa de sucesso < 95% na ultima hora"
  treat_missing_data = "notBreaching"

  alarm_actions = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []
  ok_actions    = var.enable_alerts ? [aws_sns_topic.alerts[0].arn] : []

  tags = local.common_tags
}
