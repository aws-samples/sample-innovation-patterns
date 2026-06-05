resource "aws_cognito_user_pool" "this" {
  name = "${var.namespace}-${var.environment}-users"

  auto_verified_attributes = ["email"]

  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  deletion_protection = var.deletion_protection

  tags = {
    Tier = "cognito"
  }
}

resource "aws_cognito_user_pool_client" "this" {
  name         = "${var.namespace}-${var.environment}-app"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "profile", "email"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = [
    var.callback_url,
    "http://localhost:8080/authentication/callback"
  ]

  logout_urls = [
    var.callback_url,
    "http://localhost:8080/authentication/callback",
    replace(var.callback_url, "/authentication/callback", ""),
    "http://localhost:8080"
  ]

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "minutes"
  }

  access_token_validity  = 480
  id_token_validity      = 480
  refresh_token_validity = 1440
}

resource "aws_cognito_user_pool_domain" "this" {
  domain               = var.cognito_domain_prefix
  user_pool_id         = aws_cognito_user_pool.this.id
  managed_login_version = 2
}

resource "aws_cognito_managed_login_branding" "this" {
  user_pool_id                  = aws_cognito_user_pool.this.id
  client_id                     = aws_cognito_user_pool_client.this.id
  use_cognito_provided_values   = true

  depends_on = [aws_cognito_user_pool_domain.this]
}
