variable "namespace" {
  type        = string
  description = "Project namespace prefix"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,11}$", var.namespace))
    error_message = "1-12 chars, lowercase alphanumeric + hyphens, starts with letter"
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod"
  }
}

variable "region" {
  type        = string
  description = "AWS region"
}

variable "state_bucket" {
  type        = string
  description = "S3 bucket for Terraform state"
}

variable "cognito_domain_prefix" {
  type        = string
  description = "Cognito custom domain prefix (globally unique)"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,62}$", var.cognito_domain_prefix))
    error_message = "1-63 lowercase chars, starts with letter"
  }
}

variable "callback_url" {
  type        = string
  description = "OAuth callback URL"
  default     = "http://localhost:8080/authentication/callback"
}
