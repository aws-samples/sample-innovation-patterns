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

variable "account_id" {
  type        = string
  description = "AWS account ID"
  validation {
    condition     = can(regex("^\\d{12}$", var.account_id))
    error_message = "Must be 12-digit AWS account ID"
  }
}
