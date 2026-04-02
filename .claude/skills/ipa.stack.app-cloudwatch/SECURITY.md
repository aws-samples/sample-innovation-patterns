# Security Advisory: ipa.stack.app-cloudwatch

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the app-cloudwatch stack.

```yaml
permissions:
  - actions:
      - cloudwatch:PutDashboard
      - cloudwatch:DeleteDashboards
      - cloudwatch:GetDashboard
    resource: "arn:aws:cloudwatch::{AWS_ACCOUNT_ID}:dashboard/{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "CloudFormation CRUD on CloudWatch dashboard"

  - actions:
      - logs:PutMetricFilter
      - logs:DeleteMetricFilter
      - logs:DescribeMetricFilters
    resource: "arn:aws:logs:{AWS_REGION}:{AWS_ACCOUNT_ID}:log-group:/aws/lambda/{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "CloudFormation CRUD on metric filters attached to Lambda log groups"

  - actions:
      - cloudwatch:PutMetricAlarm
      - cloudwatch:DeleteAlarms
      - cloudwatch:DescribeAlarms
    resource: "arn:aws:cloudwatch:{AWS_REGION}:{AWS_ACCOUNT_ID}:alarm:{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "CloudFormation CRUD on CloudWatch alarms"
```

## Runtime Permissions (Advisory)

None -- this is an infrastructure-only stack. It deploys dashboards, metric filters, and alarms but does not run any compute. Runtime metric emission is handled by the Lambda execution role (see ipa.stack.lambda SECURITY.md).

## Security Controls

Controls enforced by the CloudFormation template. These are not configurable -- they are hardcoded security posture.

```yaml
controls:
  - type: access_control
    enabled: true
    method: "No public resources — dashboard is CloudWatch console-only, no public URL exposed"

  - type: naming_scope
    enabled: true
    method: "All resource names (dashboard, filters, alarms) scoped to {Namespace}-{Environment} prefix"

  - type: alarm_safety
    enabled: true
    method: "Alarms disabled by default (ActionsEnabled: false) — no unintended notifications without explicit opt-in"

  - type: no_secrets
    enabled: true
    method: "No secrets, credentials, or sensitive data in the template — only metric configuration"

  - type: no_resource_creation
    enabled: true
    method: "Does not create log groups — attaches to existing log groups from ipa.stack.lambda and ipa.stack.apigwv2"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No KMS encryption on dashboard | CloudWatch dashboards do not support CMK encryption | None — service limitation |
| No X-Ray tracing integration | POC scope — add when observability requirements are defined | Low |
| No multi-account dashboard | POC scope — single-account only | Low |
