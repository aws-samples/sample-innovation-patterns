resource "aws_ecr_repository" "this" {
  name                 = "${var.namespace}-${var.environment}"
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Tier = "ecr"
  }
}
