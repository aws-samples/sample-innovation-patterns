resource "aws_cognito_user_pool" "this" {
  name = "${var.namespace}-${var.environment}-users"

  username_attributes      = ["email"]
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

  deletion_protection = "INACTIVE"

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
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = [var.callback_url]
  logout_urls                          = [replace(var.callback_url, "/authentication/callback", "/")]

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
}

resource "aws_cognito_user_pool_domain" "this" {
  domain       = var.cognito_domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}
