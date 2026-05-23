output "repository_uri" {
  value       = aws_ecr_repository.this.repository_url
  description = "ECR repository URI for container images"
}

output "repository_arn" {
  value       = aws_ecr_repository.this.arn
  description = "ECR repository ARN for security policy scoping"
}
