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

variable "repository_name" {
  type        = string
  description = "CodeCommit repository name"
  validation {
    condition     = can(regex("^[a-zA-Z0-9._-]+$", var.repository_name))
    error_message = "Only alphanumeric characters, dots, underscores, and hyphens allowed"
  }
}

variable "repository_description" {
  type        = string
  description = "Repository description"
  default     = "IPA-managed source repository"
}

variable "kms_key_arn" {
  type        = string
  description = "Optional KMS key ARN for repository encryption at rest"
  default     = ""
}
