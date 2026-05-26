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

resource "aws_iam_role" "lambda_execution" {
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
    Tier = "backend"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "dynamodb" {
  count = var.enable_passengers_table ? 1 : 0
  name  = "dynamodb-access"
  role  = aws_iam_role.lambda_execution.id

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
        aws_dynamodb_table.passengers[0].arn,
        "${aws_dynamodb_table.passengers[0].arn}/index/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "sqs_send" {
  count = var.enable_sqs_integration ? 1 : 0
  name  = "sqs-send"
  role  = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = [var.sqs_queue_arn]
    }]
  })
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.namespace}-${var.environment}-${var.function_name}"
  retention_in_days = 30
}

resource "aws_lambda_function" "backend" {
  function_name = "${var.namespace}-${var.environment}-${var.function_name}"
  package_type  = "Image"
  image_uri     = var.image_uri
  memory_size   = var.memory_size
  timeout       = var.timeout
  role          = aws_iam_role.lambda_execution.arn

  environment {
    variables = {
      APP_NAMESPACE = var.namespace
      APP_ENV       = var.environment
      INVOKE_MODE   = var.invoke_mode
      SQS_QUEUE_URL = var.enable_sqs_integration ? var.sqs_queue_url : ""
    }
  }

  dynamic "image_config" {
    for_each = var.image_command != "" ? [1] : []
    content {
      command = split(",", var.image_command)
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = {
    Tier = "backend"
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.namespace}-${var.environment}-backend-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [var.allowed_origin]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Authorization", "Content-Type"]
    max_age       = 86400
  }
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.http.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-jwt"

  jwt_configuration {
    issuer   = var.auth_issuer
    audience = [var.auth_audience]
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "$default"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${var.namespace}-${var.environment}-backend-api"
  retention_in_days = 30
}

resource "aws_dynamodb_table" "passengers" {
  count        = var.enable_passengers_table ? 1 : 0
  name         = "${var.namespace}_${var.environment}_passengers"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PassengerId"

  attribute {
    name = "PassengerId"
    type = "N"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Tier = "backend"
  }
}
