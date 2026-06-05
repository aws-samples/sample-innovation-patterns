data "terraform_remote_state" "codecommit" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "${var.namespace}-${var.environment}/codecommit/terraform.tfstate"
    region = var.region
  }
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.namespace}-${var.environment}-pipeline-artifacts-${var.account_id}"

  tags = {
    Tier = "codepipeline"
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-artifacts"
    status = "Enabled"
    expiration {
      days = 30
    }
  }
}

resource "aws_codebuild_project" "build" {
  name           = "${var.namespace}-${var.environment}-build"
  service_role   = var.codebuild_role_arn
  build_timeout  = 30
  encryption_key = var.kms_key_arn != "" ? var.kms_key_arn : null

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type    = var.compute_type
    image           = var.build_image
    type            = "LINUX_CONTAINER"
    privileged_mode = true

    environment_variable {
      name  = "APP_NAMESPACE"
      value = var.namespace
    }

    environment_variable {
      name  = "APP_ENV"
      value = var.environment
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = var.account_id
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.region
    }

    environment_variable {
      name  = "TF_STATE_BUCKET"
      value = var.state_bucket
    }

    environment_variable {
      name  = "IPA_MAKEFILE"
      value = "build.mk"
    }

    environment_variable {
      name  = "IPA_TARGET"
      value = "build"
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = <<-BUILDSPEC
      version: 0.2
      env:
        variables:
          TERRAFORM_VERSION: "1.10.5"
      phases:
        install:
          commands:
            - |
              curl -fsSL "https://releases.hashicorp.com/terraform/$${TERRAFORM_VERSION}/terraform_$${TERRAFORM_VERSION}_linux_amd64.zip" -o /tmp/terraform.zip
              unzip -q /tmp/terraform.zip -d /usr/local/bin/
              rm /tmp/terraform.zip
              terraform version
            - |
              curl -LsSf https://astral.sh/uv/install.sh | sh
              cp $HOME/.local/bin/uv /usr/local/bin/uv
              cp $HOME/.local/bin/uvx /usr/local/bin/uvx
              uv --version
            - |
              if ! command -v jq > /dev/null; then
                echo "ERROR: jq not found in build image"
                exit 1
              fi
              jq --version
        pre_build:
          commands:
            - echo "Stage $IPA_MAKEFILE / $IPA_TARGET"
            - |
              if ! command -v terraform > /dev/null; then
                echo "ERROR: terraform binary not found"
                exit 1
              fi
            - |
              if ! command -v uv > /dev/null; then
                echo "ERROR: uv binary not found"
                exit 1
              fi
            - cd app-lib && uv sync --all-extras && cd ..
            - |
              if [ "$IPA_MAKEFILE" != "test.mk" ]; then
                make -f scripts/env.mk update-env-tfstate
                make -f scripts/env.mk update-env
              fi
            - |
              if [ "$IPA_MAKEFILE" = "post-deploy.mk" ] && [ ! -f web-client/dist/index.html ]; then
                echo "PostDeploy: building frontend from source"
                cd web-client && npm ci && npm run build && cd ..
              fi
        build:
          commands:
            - make -f scripts/$IPA_MAKEFILE $IPA_TARGET
    BUILDSPEC
  }

  tags = {
    Tier = "codepipeline"
  }
}

resource "aws_iam_role" "pipeline" {
  name = "${var.namespace}-${var.environment}-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "codepipeline.amazonaws.com"
      }
    }]
  })

  tags = {
    Tier = "codepipeline"
  }
}

resource "aws_iam_role_policy" "pipeline" {
  name = "pipeline-policy"
  role = aws_iam_role.pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "codecommit:GetBranch",
          "codecommit:GetCommit",
          "codecommit:UploadArchive",
          "codecommit:GetUploadArchiveStatus",
          "codecommit:CancelUploadArchive"
        ]
        Resource = "arn:aws:codecommit:${var.region}:${var.account_id}:${var.source_repo_name}"
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild"
        ]
        Resource = aws_codebuild_project.build.arn
      }
    ]
  })
}

resource "aws_codepipeline" "pipeline" {
  name     = "${var.namespace}-${var.environment}-pipeline"
  role_arn = aws_iam_role.pipeline.arn

  artifact_store {
    location = aws_s3_bucket.artifacts.id
    type     = "S3"

    dynamic "encryption_key" {
      for_each = var.kms_key_arn != "" ? [var.kms_key_arn] : []
      content {
        id   = encryption_key.value
        type = "KMS"
      }
    }
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        RepositoryName       = var.source_repo_name
        BranchName           = var.source_branch
        PollForSourceChanges = "false"
      }
    }
  }

  stage {
    name = "Test"

    action {
      name            = "Test"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["source_output"]

      configuration = {
        ProjectName = aws_codebuild_project.build.name
        EnvironmentVariables = jsonencode([
          { name = "IPA_MAKEFILE", value = "test.mk", type = "PLAINTEXT" },
          { name = "IPA_TARGET", value = "test", type = "PLAINTEXT" }
        ])
      }
    }
  }

  stage {
    name = "Build"

    action {
      name            = "Build"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["source_output"]

      configuration = {
        ProjectName = aws_codebuild_project.build.name
        EnvironmentVariables = jsonencode([
          { name = "IPA_MAKEFILE", value = "build.mk", type = "PLAINTEXT" },
          { name = "IPA_TARGET", value = "build", type = "PLAINTEXT" }
        ])
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["source_output"]

      configuration = {
        ProjectName = aws_codebuild_project.build.name
        EnvironmentVariables = jsonencode([
          { name = "IPA_MAKEFILE", value = "deploy.mk", type = "PLAINTEXT" },
          { name = "IPA_TARGET", value = "deploy", type = "PLAINTEXT" }
        ])
      }
    }
  }

  stage {
    name = "PostDeploy"

    action {
      name            = "PostDeploy"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["source_output"]

      configuration = {
        ProjectName = aws_codebuild_project.build.name
        EnvironmentVariables = jsonencode([
          { name = "IPA_MAKEFILE", value = "post-deploy.mk", type = "PLAINTEXT" },
          { name = "IPA_TARGET", value = "post-deploy", type = "PLAINTEXT" }
        ])
      }
    }
  }

  tags = {
    Tier = "codepipeline"
  }
}

resource "aws_iam_role" "eventbridge" {
  name = "${var.namespace}-${var.environment}-pipeline-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })

  tags = {
    Tier = "codepipeline"
  }
}

resource "aws_iam_role_policy" "eventbridge" {
  name = "start-pipeline"
  role = aws_iam_role.eventbridge.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "codepipeline:StartPipelineExecution"
      Resource = aws_codepipeline.pipeline.arn
    }]
  })
}

resource "aws_cloudwatch_event_rule" "codecommit" {
  name = "${var.namespace}-${var.environment}-pipeline-trigger"

  event_pattern = jsonencode({
    source      = ["aws.codecommit"]
    detail-type = ["CodeCommit Repository State Change"]
    resources   = ["arn:aws:codecommit:${var.region}:${var.account_id}:${var.source_repo_name}"]
    detail = {
      event         = ["referenceCreated", "referenceUpdated"]
      referenceType = ["branch"]
      referenceName = [var.source_branch]
    }
  })

  tags = {
    Tier = "codepipeline"
  }
}

resource "aws_cloudwatch_event_target" "pipeline" {
  rule     = aws_cloudwatch_event_rule.codecommit.name
  arn      = aws_codepipeline.pipeline.arn
  role_arn = aws_iam_role.eventbridge.arn
}
