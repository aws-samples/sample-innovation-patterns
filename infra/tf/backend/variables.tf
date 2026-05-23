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

variable "function_name" {
  type        = string
  description = "Lambda function name suffix"
  default     = "fn"
}

variable "invoke_mode" {
  type        = string
  description = "Lambda invocation mode"
  default     = "RESPONSE_STREAM"
}

variable "memory_size" {
  type        = number
  description = "Lambda memory in MB"
  default     = 512
}

variable "timeout" {
  type        = number
  description = "Lambda timeout in seconds"
  default     = 300
}

variable "image_command" {
  type        = string
  description = "Override container CMD (comma-separated)"
  default     = ""
}

variable "allowed_origin" {
  type        = string
  description = "Allowed CORS origin"
  default     = "https://none.invalid"
}

variable "enable_passengers_table" {
  type        = bool
  description = "Create passengers DynamoDB table"
  default     = false
}

variable "enable_sqs_integration" {
  type        = bool
  description = "Enable SQS send permissions"
  default     = false
}

variable "sqs_queue_url" {
  type        = string
  description = "SQS queue URL for env var injection"
  default     = ""
}

variable "sqs_queue_arn" {
  type        = string
  description = "SQS queue ARN for send IAM policy"
  default     = ""
}
