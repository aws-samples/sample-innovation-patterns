output "user_pool_id" {
  value       = aws_cognito_user_pool.this.id
  description = "Cognito User Pool ID"
}

output "user_pool_arn" {
  value       = aws_cognito_user_pool.this.arn
  description = "Cognito User Pool ARN"
}

output "user_pool_client_id" {
  value       = aws_cognito_user_pool_client.this.id
  description = "Cognito App Client ID"
}

output "issuer_url" {
  value       = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.this.id}"
  description = "OIDC Issuer URL"
}

output "end_session_endpoint" {
  value       = "https://${var.cognito_domain_prefix}.auth.${var.region}.amazoncognito.com/logout"
  description = "Cognito logout endpoint"
}

output "cognito_domain" {
  value       = var.cognito_domain_prefix
  description = "Cognito domain prefix (pass back on stack updates to prevent drift)"
}

output "discovery_url" {
  value       = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.this.id}/.well-known/openid-configuration"
  description = "OIDC Discovery URL"
}

output "hosted_ui_url" {
  value       = "https://${var.cognito_domain_prefix}.auth.${var.region}.amazoncognito.com/login?client_id=${aws_cognito_user_pool_client.this.id}&response_type=code&scope=openid+profile+email&redirect_uri=${var.callback_url}"
  description = "Cognito Hosted UI Login URL"
}
