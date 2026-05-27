data "terraform_remote_state" "cognito" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "${var.namespace}-${var.environment}/cognito/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "ecr" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "${var.namespace}-${var.environment}/ecr/terraform.tfstate"
    region = var.region
  }
}

resource "aws_sqs_queue" "main" {
  name                       = "${var.namespace}-${var.environment}-${var.queue_name}"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention_period

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  sqs_managed_sse_enabled = true

  tags = {
    Tier = "queue"
  }
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.namespace}-${var.environment}-${var.queue_name}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    Tier = "queue"
  }
}

resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyNonSSL"
      Effect    = "Deny"
      Principal = "*"
      Action    = "sqs:*"
      Resource  = aws_sqs_queue.main.arn
      Condition = {
        Bool = {
          "aws:SecureTransport" = "false"
        }
      }
    }]
  })
}

resource "aws_iam_role" "worker_execution" {
  name = "${var.namespace}-${var.environment}-${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Tier = "queue"
  }
}

resource "aws_iam_role_policy_attachment" "worker_basic" {
  role       = aws_iam_role.worker_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "sqs_receive" {
  name = "sqs-receive"
  role = aws_iam_role.worker_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = [aws_sqs_queue.main.arn]
    }]
  })
}

resource "aws_iam_role_policy" "dynamodb_jobs" {
  count = var.enable_jobs_table ? 1 : 0
  name  = "dynamodb-access"
  role  = aws_iam_role.worker_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
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
        aws_dynamodb_table.jobs[0].arn,
        "${aws_dynamodb_table.jobs[0].arn}/index/*"
      ]
    }]
  })
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${var.namespace}-${var.environment}-${var.function_name}"
  retention_in_days = 30
}

resource "aws_lambda_function" "worker" {
  function_name = "${var.namespace}-${var.environment}-${var.function_name}"
  package_type  = "Image"
  image_uri     = var.image_uri
  memory_size   = var.memory_size
  timeout       = var.timeout
  role          = aws_iam_role.worker_execution.arn

  environment {
    variables = {
      APP_NAMESPACE = var.namespace
      APP_ENV       = var.environment
      INVOKE_MODE   = "SQS_WORKER"
    }
  }

  image_config {
    command = split(",", var.image_command)
  }

  depends_on = [aws_cloudwatch_log_group.worker]

  tags = {
    Tier = "queue"
  }
}

resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.main.arn
  function_name    = aws_lambda_function.worker.arn
  batch_size       = 10
  enabled          = true
}

resource "aws_dynamodb_table" "jobs" {
  count        = var.enable_jobs_table ? 1 : 0
  name         = "${var.namespace}_${var.environment}_jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "JobId"

  attribute {
    name = "JobId"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Tier = "queue"
  }
}
