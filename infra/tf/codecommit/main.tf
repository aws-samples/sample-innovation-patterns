resource "aws_codecommit_repository" "this" {
  repository_name = var.repository_name
  description     = var.repository_description
  kms_key_id      = var.kms_key_arn != "" ? var.kms_key_arn : null

  tags = {
    Tier = "codecommit"
  }
}
