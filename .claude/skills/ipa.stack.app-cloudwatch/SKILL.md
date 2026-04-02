---
name: ipa-stack-app-cloudwatch
description: "Deploy a CloudWatch dashboard with application metrics, error tracking, and observability for Lambda, API Gateway, and Bedrock."
---

# ipa.stack.app-cloudwatch

Application-level CloudWatch observability stack. Deploys metric filters on Lambda log groups for error detection, a modular dashboard with four sections (errors, Lambda health, API Gateway, Bedrock), and disabled-by-default alarms. Uses convention-based log group naming with optional parameter overrides.

## CloudFormation Contract

- **Template**: `infra/cfn/app-cloudwatch/app-cloudwatch.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-app-cloudwatch`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | -- | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace -- 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | -- | `dev \| staging \| prod` | "Must be dev, staging, or prod" |
| LambdaLogGroupName | String | (empty) | -- | -- |
| ApiGatewayLogGroupName | String | (empty) | -- | -- |
| MetricNamespace | String | (empty) | -- | -- |
| AlarmSnsTopicArn | String | (empty) | -- | -- |

### Parameter Classification

**Configuration** (2) -- sourced from `.env` or defaults:
- Namespace, Environment

**Configuration -- Optional Override** (4) -- convention-based defaults, override only for non-standard naming:
- LambdaLogGroupName (default: `/aws/lambda/{Namespace}-{Environment}-*`)
- ApiGatewayLogGroupName (default: `/aws/apigateway/{Namespace}-{Environment}-apigwv2`)
- MetricNamespace (default: `{Namespace}/{Environment}`)
- AlarmSnsTopicArn (default: empty -- alarms are disabled)

## Naming Convention

Log group names and metric namespaces are resolved by **convention** from Namespace and Environment:

| Resource | Convention | Override Parameter |
|----------|------------|-------------------|
| Lambda log group | `/aws/lambda/{Namespace}-{Environment}-fn` | LambdaLogGroupName |
| API Gateway log group | `/aws/apigateway/{Namespace}-{Environment}-apigwv2` | ApiGatewayLogGroupName |
| Metric namespace | `{Namespace}/{Environment}` | MetricNamespace |

No explicit wiring from upstream stacks is needed. The convention matches the naming in ipa.stack.lambda and ipa.stack.apigwv2.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| DashboardName | CloudWatch dashboard name | `{StackName}-DashboardName` | Console navigation |
| DashboardUrl | Direct console URL to the dashboard | `{StackName}-DashboardUrl` | Post-deploy reporting |
| MetricNamespace | Custom metric namespace | `{StackName}-MetricNamespace` | Observability module reference |

## Security Summary

**Required IAM actions**: cloudwatch:PutDashboard, DeleteDashboards, GetDashboard + logs:PutMetricFilter, DeleteMetricFilter, DescribeMetricFilters + cloudwatch:PutMetricAlarm, DeleteAlarms, DescribeAlarms -- scoped to `{APP_NAMESPACE}-{APP_ENV}-*`
**Runtime permissions**: None -- infrastructure-only stack
**Security controls**: No public resources, all names scoped to namespace/environment, alarms disabled by default
**Full advisory**: See [SECURITY.md](SECURITY.md)
