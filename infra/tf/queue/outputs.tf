output "queue_url" {
  value       = aws_sqs_queue.main.url
  description = "SQS queue URL"
}

output "queue_arn" {
  value       = aws_sqs_queue.main.arn
  description = "SQS queue ARN"
}

output "queue_name" {
  value       = aws_sqs_queue.main.name
  description = "Physical queue name"
}

output "worker_function_arn" {
  value       = aws_lambda_function.worker.arn
  description = "Worker Lambda ARN"
}

output "worker_function_name" {
  value       = aws_lambda_function.worker.function_name
  description = "Worker Lambda name"
}

output "dlq_url" {
  value       = aws_sqs_queue.dlq.url
  description = "Dead-letter queue URL"
}

output "dlq_arn" {
  value       = aws_sqs_queue.dlq.arn
  description = "Dead-letter queue ARN"
}

output "jobs_table_arn" {
  value       = var.enable_jobs_table ? aws_dynamodb_table.jobs[0].arn : ""
  description = "Jobs DynamoDB table ARN (empty if disabled)"
}
