################################################################################
# FinOps AWS - EventBridge (CloudWatch Events) Configuration
# Agendamento de execucoes automaticas
################################################################################

################################################################################
# EventBridge Rule - Scheduled Execution
################################################################################

resource "aws_cloudwatch_event_rule" "schedule" {
  count = var.schedule_enabled ? 1 : 0
  
  name                = "${local.lambda_name}-schedule"
  description         = "Agendamento para execucao do FinOps AWS Lambda"
  schedule_expression = var.schedule_expression
  state               = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "lambda" {
  count = var.schedule_enabled ? 1 : 0
  
  rule      = aws_cloudwatch_event_rule.schedule[0].name
  target_id = "FinOpsLambda"
  arn       = aws_lambda_function.main.arn

  input = jsonencode({
    source          = "scheduled"
    detail-type     = "Scheduled Event"
    time            = "$$.time"
    analysis_type   = "full"
    include_metrics = true
    include_recommendations = true
  })
}

################################################################################
# Multiple Daily Schedules (optional)
################################################################################

resource "aws_cloudwatch_event_rule" "multi_schedule" {
  for_each = var.schedule_enabled ? toset(var.schedule_expressions) : toset([])
  
  name                = "${local.lambda_name}-schedule-${index(var.schedule_expressions, each.value)}"
  description         = "Agendamento ${index(var.schedule_expressions, each.value) + 1} para FinOps AWS"
  schedule_expression = each.value
  state               = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "lambda_multi" {
  for_each = var.schedule_enabled ? toset(var.schedule_expressions) : toset([])
  
  rule      = aws_cloudwatch_event_rule.multi_schedule[each.key].name
  target_id = "FinOpsLambda"
  arn       = aws_lambda_function.main.arn

  input = jsonencode({
    source          = "scheduled"
    schedule_id     = index(var.schedule_expressions, each.value)
    detail-type     = "Scheduled Event"
    analysis_type   = "full"
  })
}

resource "aws_lambda_permission" "eventbridge_multi" {
  for_each = var.schedule_enabled ? toset(var.schedule_expressions) : toset([])
  
  statement_id  = "AllowEventBridgeInvoke-${index(var.schedule_expressions, each.value)}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.multi_schedule[each.key].arn
}

################################################################################
# Cost Anomaly Detection Integration
################################################################################

resource "aws_cloudwatch_event_rule" "cost_anomaly" {
  count = var.enable_alerts ? 1 : 0
  
  name        = "${local.lambda_name}-cost-anomaly"
  description = "Trigger FinOps Lambda quando anomalia de custo for detectada"
  state       = "ENABLED"

  event_pattern = jsonencode({
    source      = ["aws.ce"]
    detail-type = ["AWS Cost Anomaly Detection Alert"]
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "cost_anomaly" {
  count = var.enable_alerts ? 1 : 0
  
  rule      = aws_cloudwatch_event_rule.cost_anomaly[0].name
  target_id = "FinOpsLambdaAnomaly"
  arn       = aws_lambda_function.main.arn

  input_transformer {
    input_paths = {
      anomalyId         = "$.detail.anomalyId"
      monitorArn        = "$.detail.monitorArn"
      anomalyStartDate  = "$.detail.anomalyStartDate"
      impact            = "$.detail.impact"
    }

    input_template = <<EOF
{
  "source": "cost_anomaly",
  "detail-type": "Cost Anomaly Alert",
  "anomaly_id": <anomalyId>,
  "monitor_arn": <monitorArn>,
  "start_date": <anomalyStartDate>,
  "impact": <impact>,
  "analysis_type": "anomaly_investigation"
}
EOF
  }
}

resource "aws_lambda_permission" "cost_anomaly" {
  count = var.enable_alerts ? 1 : 0
  
  statement_id  = "AllowCostAnomalyInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_anomaly[0].arn
}
