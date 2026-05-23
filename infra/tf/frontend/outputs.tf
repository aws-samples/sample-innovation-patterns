output "app_url" {
  value       = "https://${aws_cloudfront_distribution.web.domain_name}"
  description = "CloudFront HTTPS URL"
}

output "distribution_id" {
  value       = aws_cloudfront_distribution.web.id
  description = "CloudFront distribution ID for cache invalidation"
}

output "distribution_domain_name" {
  value       = aws_cloudfront_distribution.web.domain_name
  description = "CloudFront domain name"
}

output "bucket_name" {
  value       = aws_s3_bucket.web.id
  description = "S3 bucket name for upload"
}
