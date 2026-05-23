output "repository_name" {
  value       = aws_codecommit_repository.this.repository_name
  description = "CodeCommit repository name"
}

output "repository_arn" {
  value       = aws_codecommit_repository.this.arn
  description = "CodeCommit repository ARN"
}

output "clone_url_http" {
  value       = aws_codecommit_repository.this.clone_url_http
  description = "HTTPS clone URL"
}
