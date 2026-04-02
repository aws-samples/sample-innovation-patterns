# Security Advisory: ipa.stack.lambda

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the Lambda stack.

```yaml
permissions:
  - actions:
      - lambda:CreateFunction
      - lambda:UpdateFunctionCode
      - lambda:UpdateFunctionConfiguration
      - lambda:DeleteFunction
      - lambda:GetFunction
      - lambda:GetFunctionConfiguration
      - lambda:TagResource
      - lambda:UntagResource
      - lambda:ListTags
    resource: "arn:aws:lambda:{AWS_REGION}:{AWS_ACCOUNT_ID}:function:{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "CloudFormation CRUD operations on Lambda function resources"

  - actions:
      - iam:CreateRole
      - iam:DeleteRole
      - iam:GetRole
      - iam:PutRolePolicy
      - iam:DeleteRolePolicy
      - iam:GetRolePolicy
      - iam:TagRole
      - iam:UntagRole
      - iam:PassRole
    resource: "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{APP_NAMESPACE}-{APP_ENV}-*-exec"
    purpose: "CloudFormation CRUD operations on Lambda execution role"

  - actions:
      - logs:CreateLogGroup
      - logs:DeleteLogGroup
      - logs:PutRetentionPolicy
      - logs:DeleteRetentionPolicy
      - logs:TagResource
      - logs:UntagResource
    resource: "arn:aws:logs:{AWS_REGION}:{AWS_ACCOUNT_ID}:log-group:/aws/lambda/{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "CloudFormation CRUD operations on CloudWatch log group"
```

## Runtime Permissions (Advisory)

IAM actions granted to the Lambda execution role at runtime. These are created by the CloudFormation template — **not** consumed by the Builder Execution Role.

```yaml
runtime_permissions:
  - actions:
      - dynamodb:PutItem
      - dynamodb:GetItem
      - dynamodb:Query
      - dynamodb:Scan
      - dynamodb:DeleteItem
      - dynamodb:UpdateItem
    resource: "!Ref DynamoDbTableArns (comma-separated)"
    purpose: "DynamoDB CRUD operations — only granted when DynamoDbTableArns parameter is non-empty (HasDynamoDb condition)"

  - actions:
      - ecr:BatchGetImage
      - ecr:GetDownloadUrlForLayer
    resource: "*"
    purpose: "ECR container image pull at function startup — explicit for auditability"

  - actions:
      - bedrock:InvokeModel
      - bedrock:InvokeModelWithResponseStream
    resource: "arn:aws:bedrock:{AWS_REGION}::foundation-model/*"
    purpose: "Bedrock model invocation — always included for all Lambda instances"

  - actions:
      - logs:CreateLogStream
      - logs:PutLogEvents
    resource: "arn:aws:logs:{AWS_REGION}:{AWS_ACCOUNT_ID}:log-group:/aws/lambda/{APP_NAMESPACE}-{APP_ENV}-{FunctionName}:*"
    purpose: "CloudWatch Logs write — granted via AWSLambdaBasicExecutionRole managed policy"

  - actions:
      - cloudwatch:PutMetricData
    resource: "*"
    condition: "cloudwatch:namespace == {Namespace}/{Environment}"
    purpose: "Custom CloudWatch metric emission — observability module (always included)"
```

## Security Controls

Controls enforced by the CloudFormation template. These are not configurable — they are hardcoded security posture.

```yaml
controls:
  - type: access_control
    enabled: true
    method: "No public function URL — Lambda is invoked only via API Gateway, never directly exposed"

  - type: iam
    enabled: true
    method: "Dedicated least-privilege execution role per function instance — no shared roles across stacks"

  - type: encryption
    enabled: true
    method: "Encryption in transit — HTTPS only via API Gateway; Lambda environment variables encrypted at rest by default"

  - type: logging
    enabled: true
    method: "CloudWatch log group with 30-day retention — created before the function to ensure log capture from first invocation"

  - type: conditional_permissions
    enabled: true
    method: "DynamoDB IAM policy only created when DynamoDbTableArns is non-empty (HasDynamoDb condition) — no unused permissions"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No VPC attachment | POC scope — Lambda runs in default networking | Low — VPC config is a production concern; add for compliance |
| No reserved concurrency | POC scope — default concurrency limits are sufficient | Low — configure for production workloads |
| No X-Ray tracing | POC scope — can be enabled via template parameter later | Low — add when observability requirements are defined |
| `ecr:BatchGetImage` on `*` | Container image pull does not reliably support resource-level scoping in all configurations | Low — documented; scope to specific repo ARN if needed |
| `bedrock:InvokeModel` on `foundation-model/*` | AWS Bedrock does not support model-level ARN scoping for InvokeModel | Low — service limitation; all foundation models in region |
