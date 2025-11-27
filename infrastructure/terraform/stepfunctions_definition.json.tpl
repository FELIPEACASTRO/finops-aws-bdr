{
  "Comment": "FinOps AWS - Orquestrador de analise de custos para 252 servicos AWS",
  "StartAt": "InitializeExecution",
  "States": {
    "InitializeExecution": {
      "Type": "Task",
      "Resource": "${mapper_arn}",
      "Parameters": {
        "execution_id.$": "$$.Execution.Id",
        "start_time.$": "$$.Execution.StartTime",
        "input.$": "$"
      },
      "ResultPath": "$.initialization",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed", "Lambda.ServiceException"],
          "IntervalSeconds": 5,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "ExecutionFailed"
        }
      ],
      "Next": "ProcessServiceBatches"
    },
    "ProcessServiceBatches": {
      "Type": "Map",
      "ItemsPath": "$.initialization.batches",
      "MaxConcurrency": ${max_concurrency},
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "INLINE"
        },
        "StartAt": "ProcessBatch",
        "States": {
          "ProcessBatch": {
            "Type": "Task",
            "Resource": "${worker_arn}",
            "Parameters": {
              "batch.$": "$",
              "execution_id.$": "$$.Execution.Id"
            },
            "Retry": [
              {
                "ErrorEquals": ["States.TaskFailed", "Lambda.ServiceException", "Lambda.TooManyRequestsException"],
                "IntervalSeconds": 10,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "Catch": [
              {
                "ErrorEquals": ["States.ALL"],
                "ResultPath": "$.error",
                "Next": "BatchFailed"
              }
            ],
            "End": true
          },
          "BatchFailed": {
            "Type": "Task",
            "Resource": "arn:aws:states:::sqs:sendMessage",
            "Parameters": {
              "QueueUrl": "${dlq_url}",
              "MessageBody": {
                "error.$": "$.error",
                "batch.$": "$",
                "execution_id.$": "$$.Execution.Id",
                "timestamp.$": "$$.State.EnteredTime"
              }
            },
            "End": true
          }
        }
      },
      "ResultPath": "$.batch_results",
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "ExecutionFailed"
        }
      ],
      "Next": "AggregateResults"
    },
    "AggregateResults": {
      "Type": "Task",
      "Resource": "${aggregator_arn}",
      "Parameters": {
        "execution_id.$": "$$.Execution.Id",
        "batch_results.$": "$.batch_results",
        "start_time.$": "$.initialization.start_time"
      },
      "ResultPath": "$.aggregation",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 5,
          "MaxAttempts": 2,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "ExecutionFailed"
        }
      ],
      "Next": "ExecutionSucceeded"
    },
    "ExecutionSucceeded": {
      "Type": "Succeed"
    },
    "ExecutionFailed": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${sns_topic_arn}",
        "Message": {
          "status": "FAILED",
          "execution_id.$": "$$.Execution.Id",
          "error.$": "$.error",
          "timestamp.$": "$$.State.EnteredTime"
        },
        "Subject": "FinOps AWS - Execucao Falhou"
      },
      "Next": "FailState"
    },
    "FailState": {
      "Type": "Fail",
      "Error": "ExecutionFailed",
      "Cause": "One or more steps failed during execution"
    }
  }
}
