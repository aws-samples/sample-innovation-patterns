output "log_bucket_name" {
  value       = aws_s3_bucket.logs.id
  description = "S3 bucket name for log destinations"
}

output "log_bucket_arn" {
  value       = aws_s3_bucket.logs.arn
  description = "S3 bucket ARN for IAM policy scoping"
}
