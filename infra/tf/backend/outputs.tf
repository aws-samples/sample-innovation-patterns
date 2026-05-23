output "api_url" {
  value       = aws_apigatewayv2_stage.default.invoke_url
  description = "HTTP API invoke URL"
}

output "function_arn" {
  value       = aws_lambda_function.backend.arn
  description = "Lambda function ARN"
}

output "function_name" {
  value       = aws_lambda_function.backend.function_name
  description = "Lambda function name"
}

output "passengers_table_arn" {
  value       = var.enable_passengers_table ? aws_dynamodb_table.passengers[0].arn : ""
  description = "Passengers DynamoDB table ARN (empty if disabled)"
}
