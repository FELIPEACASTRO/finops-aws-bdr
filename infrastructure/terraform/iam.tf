################################################################################
# FinOps AWS - IAM Roles and Policies
# Permissoes minimas necessarias para analise de custos
################################################################################

################################################################################
# Lambda Execution Role
################################################################################

resource "aws_iam_role" "lambda_execution" {
  name = "${local.lambda_name}-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

################################################################################
# CloudWatch Logs Policy
################################################################################

resource "aws_iam_role_policy" "lambda_logs" {
  name = "${local.lambda_name}-logs-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:${local.partition}:logs:${local.region}:${local.account_id}:log-group:/aws/lambda/${local.lambda_name}*"
        ]
      }
    ]
  })
}

################################################################################
# X-Ray Tracing Policy
################################################################################

resource "aws_iam_role_policy" "lambda_xray" {
  count = var.enable_xray_tracing ? 1 : 0
  
  name = "${local.lambda_name}-xray-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

################################################################################
# VPC Access Policy (if enabled)
################################################################################

resource "aws_iam_role_policy" "lambda_vpc" {
  count = var.enable_vpc ? 1 : 0
  
  name = "${local.lambda_name}-vpc-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

################################################################################
# S3 Access Policy
################################################################################

resource "aws_iam_role_policy" "lambda_s3" {
  name = "${local.lambda_name}-s3-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.reports.arn,
          "${aws_s3_bucket.reports.arn}/*"
        ]
      }
    ]
  })
}

################################################################################
# DynamoDB Access Policy
################################################################################

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${local.lambda_name}-dynamodb-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.state.arn,
          "${aws_dynamodb_table.state.arn}/index/*"
        ]
      }
    ]
  })
}

################################################################################
# KMS Access Policy (if enabled)
################################################################################

resource "aws_iam_role_policy" "lambda_kms" {
  count = var.enable_kms_encryption ? 1 : 0
  
  name = "${local.lambda_name}-kms-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.main[0].arn
        ]
      }
    ]
  })
}

################################################################################
# Cost Explorer and Billing Read-Only Policy
################################################################################

resource "aws_iam_role_policy" "lambda_cost_explorer" {
  name = "${local.lambda_name}-cost-explorer-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CostExplorerReadOnly"
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast",
          "ce:GetReservationCoverage",
          "ce:GetReservationUtilization",
          "ce:GetSavingsPlansCoverage",
          "ce:GetSavingsPlansUtilization",
          "ce:GetRightsizingRecommendation",
          "ce:GetAnomalies",
          "ce:GetAnomalyMonitors",
          "ce:GetAnomalySubscriptions",
          "ce:GetDimensionValues",
          "ce:GetTags",
          "ce:ListCostAllocationTags",
          "ce:ListCostCategoryDefinitions"
        ]
        Resource = "*"
      },
      {
        Sid    = "BudgetsReadOnly"
        Effect = "Allow"
        Action = [
          "budgets:ViewBudget",
          "budgets:DescribeBudgets",
          "budgets:DescribeBudgetActionsForBudget"
        ]
        Resource = "*"
      },
      {
        Sid    = "BillingReadOnly"
        Effect = "Allow"
        Action = [
          "aws-portal:ViewBilling",
          "aws-portal:ViewUsage"
        ]
        Resource = "*"
      }
    ]
  })
}

################################################################################
# AWS Services Read-Only Policy (for all 252 services)
################################################################################

resource "aws_iam_role_policy" "lambda_aws_services_readonly" {
  name = "${local.lambda_name}-aws-services-readonly"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ComputeReadOnly"
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "ec2:GetCapacityReservationUsage",
          "ec2:GetHostReservationPurchasePreview",
          "ec2:GetReservedInstancesExchangeQuote",
          "lambda:List*",
          "lambda:Get*",
          "ecs:Describe*",
          "ecs:List*",
          "eks:Describe*",
          "eks:List*",
          "batch:Describe*",
          "batch:List*",
          "lightsail:Get*",
          "apprunner:Describe*",
          "apprunner:List*",
          "elasticbeanstalk:Describe*",
          "elasticbeanstalk:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "StorageReadOnly"
        Effect = "Allow"
        Action = [
          "s3:GetBucket*",
          "s3:GetObject*",
          "s3:GetLifecycleConfiguration",
          "s3:GetIntelligentTieringConfiguration",
          "s3:GetStorageLensConfiguration",
          "s3:ListAllMyBuckets",
          "s3:ListBucket",
          "ebs:Get*",
          "ebs:List*",
          "elasticfilesystem:Describe*",
          "fsx:Describe*",
          "storagegateway:Describe*",
          "storagegateway:List*",
          "backup:Describe*",
          "backup:List*",
          "datasync:Describe*",
          "datasync:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "DatabaseReadOnly"
        Effect = "Allow"
        Action = [
          "rds:Describe*",
          "rds:List*",
          "dynamodb:Describe*",
          "dynamodb:List*",
          "elasticache:Describe*",
          "elasticache:List*",
          "redshift:Describe*",
          "redshift-serverless:Get*",
          "redshift-serverless:List*",
          "neptune:Describe*",
          "docdb:Describe*",
          "docdb-elastic:Get*",
          "docdb-elastic:List*",
          "memorydb:Describe*",
          "memorydb:List*",
          "keyspaces:Get*",
          "keyspaces:List*",
          "timestream:Describe*",
          "timestream:List*",
          "qldb:Describe*",
          "qldb:List*",
          "opensearch:Describe*",
          "opensearch:List*",
          "es:Describe*",
          "es:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "NetworkingReadOnly"
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:Describe*",
          "cloudfront:Get*",
          "cloudfront:List*",
          "route53:Get*",
          "route53:List*",
          "globalaccelerator:Describe*",
          "globalaccelerator:List*",
          "directconnect:Describe*",
          "apigateway:GET",
          "vpc-lattice:Get*",
          "vpc-lattice:List*",
          "networkmanager:Describe*",
          "networkmanager:Get*",
          "networkmanager:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "SecurityReadOnly"
        Effect = "Allow"
        Action = [
          "iam:Get*",
          "iam:List*",
          "iam:GenerateCredentialReport",
          "iam:GenerateServiceLastAccessedDetails",
          "securityhub:Get*",
          "securityhub:Describe*",
          "securityhub:List*",
          "guardduty:Get*",
          "guardduty:List*",
          "inspector2:Get*",
          "inspector2:List*",
          "macie2:Get*",
          "macie2:List*",
          "detective:Get*",
          "detective:List*",
          "kms:Describe*",
          "kms:Get*",
          "kms:List*",
          "acm:Describe*",
          "acm:Get*",
          "acm:List*",
          "waf:Get*",
          "waf:List*",
          "wafv2:Get*",
          "wafv2:List*",
          "cognito-idp:Describe*",
          "cognito-idp:List*",
          "secretsmanager:Describe*",
          "secretsmanager:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "MonitoringReadOnly"
        Effect = "Allow"
        Action = [
          "cloudwatch:Describe*",
          "cloudwatch:Get*",
          "cloudwatch:List*",
          "logs:Describe*",
          "logs:Get*",
          "logs:List*",
          "logs:FilterLogEvents",
          "events:Describe*",
          "events:List*",
          "sns:Get*",
          "sns:List*",
          "sqs:Get*",
          "sqs:List*",
          "cloudtrail:Describe*",
          "cloudtrail:Get*",
          "cloudtrail:List*",
          "config:Describe*",
          "config:Get*",
          "config:List*",
          "application-autoscaling:Describe*",
          "autoscaling:Describe*"
        ]
        Resource = "*"
      },
      {
        Sid    = "AIMLReadOnly"
        Effect = "Allow"
        Action = [
          "bedrock:Get*",
          "bedrock:List*",
          "sagemaker:Describe*",
          "sagemaker:List*",
          "comprehend:Describe*",
          "comprehend:List*",
          "rekognition:Describe*",
          "rekognition:List*",
          "textract:Get*",
          "transcribe:Get*",
          "transcribe:List*",
          "translate:Get*",
          "translate:List*",
          "polly:Describe*",
          "polly:List*",
          "lex:Get*",
          "lex:List*",
          "personalize:Describe*",
          "personalize:List*",
          "forecast:Describe*",
          "forecast:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "AnalyticsReadOnly"
        Effect = "Allow"
        Action = [
          "athena:Get*",
          "athena:List*",
          "glue:Get*",
          "glue:List*",
          "quicksight:Describe*",
          "quicksight:List*",
          "emr:Describe*",
          "emr:List*",
          "emr-serverless:Get*",
          "emr-serverless:List*",
          "kinesis:Describe*",
          "kinesis:List*",
          "firehose:Describe*",
          "firehose:List*",
          "kafka:Describe*",
          "kafka:List*",
          "lakeformation:Describe*",
          "lakeformation:Get*",
          "lakeformation:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "ManagementReadOnly"
        Effect = "Allow"
        Action = [
          "organizations:Describe*",
          "organizations:List*",
          "controltower:Describe*",
          "controltower:Get*",
          "controltower:List*",
          "servicequotas:Get*",
          "servicequotas:List*",
          "support:Describe*",
          "trustedadvisor:Describe*",
          "trustedadvisor:Get*",
          "trustedadvisor:List*",
          "compute-optimizer:Get*",
          "compute-optimizer:Describe*",
          "ssm:Describe*",
          "ssm:Get*",
          "ssm:List*",
          "cloudformation:Describe*",
          "cloudformation:Get*",
          "cloudformation:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "DevToolsReadOnly"
        Effect = "Allow"
        Action = [
          "codebuild:BatchGet*",
          "codebuild:Describe*",
          "codebuild:List*",
          "codepipeline:Get*",
          "codepipeline:List*",
          "codecommit:Get*",
          "codecommit:List*",
          "codedeploy:Get*",
          "codedeploy:List*",
          "codeartifact:Describe*",
          "codeartifact:Get*",
          "codeartifact:List*"
        ]
        Resource = "*"
      },
      {
        Sid    = "MiscServicesReadOnly"
        Effect = "Allow"
        Action = [
          "workspaces:Describe*",
          "appstream:Describe*",
          "mediaconvert:Describe*",
          "mediaconvert:Get*",
          "mediaconvert:List*",
          "medialive:Describe*",
          "medialive:List*",
          "iot:Describe*",
          "iot:Get*",
          "iot:List*",
          "greengrass:Get*",
          "greengrass:List*",
          "states:Describe*",
          "states:List*",
          "amplify:Get*",
          "amplify:List*",
          "appsync:Get*",
          "appsync:List*",
          "transfer:Describe*",
          "transfer:List*",
          "dms:Describe*",
          "resource-groups:Get*",
          "resource-groups:List*",
          "tag:Get*",
          "ram:Get*",
          "ram:List*",
          "pricing:Describe*",
          "pricing:Get*"
        ]
        Resource = "*"
      }
    ]
  })
}

################################################################################
# Cross-Account Assume Role Policy (if multi-account enabled)
################################################################################

resource "aws_iam_role_policy" "lambda_assume_role" {
  count = var.enable_multi_account ? 1 : 0
  
  name = "${local.lambda_name}-assume-role-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Resource = [
          for account_id in var.target_account_ids :
          "arn:${local.partition}:iam::${account_id}:role/${var.organization_role_name}"
        ]
      }
    ]
  })
}

################################################################################
# SNS Publish Policy (for alerts)
################################################################################

resource "aws_iam_role_policy" "lambda_sns" {
  count = var.enable_alerts ? 1 : 0
  
  name = "${local.lambda_name}-sns-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.alerts[0].arn
        ]
      }
    ]
  })
}
