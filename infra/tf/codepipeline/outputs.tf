output "pipeline_name" {
  value       = aws_codepipeline.pipeline.name
  description = "CodePipeline pipeline name"
}

output "pipeline_arn" {
  value       = aws_codepipeline.pipeline.arn
  description = "CodePipeline ARN"
}

output "codebuild_project_name" {
  value       = aws_codebuild_project.build.name
  description = "CodeBuild project name"
}

output "artifacts_bucket" {
  value       = aws_s3_bucket.artifacts.id
  description = "Pipeline artifacts S3 bucket"
}
