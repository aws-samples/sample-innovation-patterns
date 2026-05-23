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

variable "image_uri" {
  type        = string
  description = "ECR image URI with tag"
}

variable "auth_issuer" {
  type        = string
  description = "Cognito OIDC issuer URL"
}

variable "auth_audience" {
  type        = string
  description = "Cognito app client ID"
}

variable "queue_name" {
  type        = string
  description = "Logical queue name"
  default     = "jobs"
}

variable "visibility_timeout" {
  type        = number
  description = "Message visibility timeout (seconds)"
  default     = 300
}

variable "message_retention_period" {
  type        = number
  description = "Message retention (seconds)"
  default     = 345600
}

variable "max_receive_count" {
  type        = number
  description = "Attempts before DLQ"
  default     = 3
}

variable "function_name" {
  type        = string
  description = "Worker Lambda name suffix"
  default     = "fn-worker"
}

variable "memory_size" {
  type        = number
  description = "Worker Lambda memory (MB)"
  default     = 512
}

variable "timeout" {
  type        = number
  description = "Worker Lambda timeout (seconds)"
  default     = 300
}

variable "image_command" {
  type        = string
  description = "Worker container CMD (comma-separated)"
  default     = "python,-m,sqs_handler"
}

variable "enable_jobs_table" {
  type        = bool
  description = "Create jobs DynamoDB table"
  default     = false
}
