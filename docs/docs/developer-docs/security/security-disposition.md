---
title: Security Disposition
sidebar_position: 2
---

# Security Disposition

This document catalogs the known security findings in the Innovation Patterns reference implementation and records their disposition. All findings listed here are **accepted for the POC** because this repository is a public proof-of-concept intended for demonstration and reuse. Every finding must be addressed on any path to production.

Findings are grouped by severity: High, Medium, Low, and Informational. Each entry includes the affected file, the relevant CWE identifier, a description of the issue, the impact, and the recommended resolution.

:::warning
This disposition applies to the reference implementation only. Consumers adapting IPA for production workloads are responsible for remediating each finding against their target deployment context.
:::

## High

### H-1: No WAF on API Gateway — L7 Attack Surface Exposed

- **File:** `infra/cfn/backend/backend.yml` (HttpApi resource)
- **CWE:** [CWE-693](https://cwe.mitre.org/data/definitions/693.html) — Protection Mechanism Failure

**Description:** The HTTP API Gateway v2 has no AWS WAF WebACL attached. All routes (`GET`/`POST`/`PUT`/`DELETE /{proxy+}`, SSE routes) are directly exposed to the internet with only JWT auth as a gate. There is no rate limiting, no SQL injection filtering, no request size limiting, and no bot mitigation at the edge.

**Impact:** Attackers can perform credential stuffing against the JWT auth layer, abuse the Bedrock inference endpoint to generate high token costs, or attempt injection attacks against the API without any L7 filtering.

**Resolution:** HTTP API v2 does not natively support WAF. Attach WAF to a CloudFront distribution and route API traffic through it. Configure rate-based rules (for example, 100 requests per 5 minutes per IP), AWS managed rule groups (`AWSManagedRulesCommonRuleSet`, `AWSManagedRulesSQLiRuleSet`), and request size constraints.

### H-2: User-Controlled Bedrock Model ID — Unrestricted Model Invocation

- **File:** `app-lib/src/app_lib/features/inference/routes/inference_dto.py` (line 18); `inference_sse_routes.py` (line 44)
- **CWE:** [CWE-20](https://cwe.mitre.org/data/definitions/20.html) — Improper Input Validation

**Description:** The `ConverseRequest` DTO accepts `model_id` as a user-supplied string with only `min_length=1` validation. This value is passed directly to `client.converse_stream(modelId=body.model_id)`. The IAM policy grants `bedrock:InvokeModel` on `arn:aws:bedrock:{region}::foundation-model/*`, meaning any authenticated user can invoke any foundation model in the region.

**Impact:** An authenticated user can invoke arbitrarily expensive models, generating significant Bedrock costs. They could also invoke models with different safety profiles than intended.

**Resolution:** Restrict `model_id` to an allowlist in the DTO:

```python
ALLOWED_MODELS = {
    "anthropic.claude-3-haiku-20240307-v1:0",
    "anthropic.claude-3-sonnet-...",
}
model_id: str = Field(..., pattern=f"^({'|'.join(re.escape(m) for m in ALLOWED_MODELS)})$")
```

Also scope the IAM policy to specific model ARNs instead of `foundation-model/*`.

### H-3: Lambda Functions Not in VPC — No Network Isolation

- **File:** `infra/cfn/backend/backend.yml` (LambdaFunction); `infra/cfn/queue/queue.yml` (WorkerLambdaFunction)
- **CWE:** [CWE-284](https://cwe.mitre.org/data/definitions/284.html) — Improper Access Control

**Description:** Both Lambda functions run in the AWS-managed VPC with no `VpcConfig`. All outbound traffic (to DynamoDB, SQS, Bedrock, S3, CloudWatch) traverses the public internet rather than VPC endpoints.

**Impact:** No network-level isolation for data in transit between Lambda and AWS services. If a dependency is compromised, there is no network segmentation to limit lateral movement. Data exfiltration via DNS or HTTPS to arbitrary endpoints is unrestricted.

**Resolution:** Deploy Lambda functions in a VPC with private subnets and create VPC endpoints (Gateway endpoints for S3 and DynamoDB; Interface endpoints for SQS, Bedrock, CloudWatch, and ECR). Add a security group that restricts outbound traffic to only the VPC endpoint ENIs.

## Medium

### M-1: Bedrock IAM Policy Scoped to All Foundation Models

- **File:** `infra/cfn/backend/backend.yml` (line 251); `infra/cfn/queue/queue.yml` (line 294)
- **CWE:** [CWE-250](https://cwe.mitre.org/data/definitions/250.html) — Execution with Unnecessary Privileges

**Description:** The Bedrock IAM policy grants `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on `arn:aws:bedrock:${AWS::Region}::foundation-model/*`. This allows invocation of any foundation model in the region.

**Impact:** Any code path that reaches Bedrock can invoke any model, including expensive ones. Even without H-2, a code change or misconfiguration could accidentally invoke unintended models.

**Resolution:** Scope to the specific model(s) used:

```yaml
Resource: !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0'
```

### M-2: ECR Pull IAM Uses Wildcard Resource

- **File:** `infra/cfn/backend/backend.yml` (line 242)
- **CWE:** [CWE-250](https://cwe.mitre.org/data/definitions/250.html) — Execution with Unnecessary Privileges

**Description:** The ECR pull policy grants `ecr:BatchGetImage` and `ecr:GetDownloadUrlForLayer` on `Resource: '*'`, allowing the Lambda execution role to pull images from any ECR repository in the account.

**Impact:** If the Lambda execution role is compromised, it can pull container images from any ECR repository, potentially accessing proprietary code or data embedded in other images.

**Resolution:** Scope to the specific ECR repository ARN. Pass the ECR repository ARN as a parameter to the backend and queue stacks and use it in the IAM policy resource.

### M-3: MFA Not Enabled on Cognito User Pool

- **File:** `infra/cfn/cognito/cognito.yml` (CognitoUserPool resource)
- **CWE:** [CWE-308](https://cwe.mitre.org/data/definitions/308.html) — Use of Single-factor Authentication

**Description:** The Cognito User Pool has no `MfaConfiguration` property. The `cdk_nag` suppression for `AwsSolutions-COG2` acknowledges this as a POC decision, but for any customer-facing deployment, single-factor auth is insufficient.

**Impact:** Compromised passwords grant full access to the application. No second factor to prevent account takeover.

**Resolution:** Enable optional TOTP MFA:

```yaml
MfaConfiguration: OPTIONAL
EnabledMfas:
  - SOFTWARE_TOKEN_MFA
```

### M-4: No API Request Throttling

- **File:** `infra/cfn/backend/backend.yml` (DefaultStage resource)
- **CWE:** [CWE-770](https://cwe.mitre.org/data/definitions/770.html) — Allocation of Resources Without Limits

**Description:** The API Gateway v2 stage has no `DefaultRouteSettings` with `ThrottlingBurstLimit` or `ThrottlingRateLimit`. The only concurrency control is Lambda's `ReservedConcurrentExecutions: 50`.

**Impact:** A single authenticated user can consume all 50 concurrent Lambda executions, causing denial of service for other users. The Bedrock inference endpoint is particularly expensive to abuse.

**Resolution:** Add route-level throttling:

```yaml
DefaultRouteSettings:
  ThrottlingBurstLimit: 20
  ThrottlingRateLimit: 10
```

### M-5: CORS Allows Wildcard During Initial Deploy

- **File:** `app-lib/src/app_lib/common/app.py` (line 47)
- **CWE:** [CWE-942](https://cwe.mitre.org/data/definitions/942.html) — Permissive Cross-domain Policy

**Description:** The FastAPI CORS middleware reads `CORS_ALLOWED_ORIGINS` from env, defaulting to `"*"`:

```python
allow_origins=os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(",")
```

While the CloudFormation template sets `AllowedOrigin` to `https://none.invalid`, the application-level default is `*`. If the env var is unset or misconfigured, CORS is wide open.

**Impact:** If CORS is misconfigured, any origin can make authenticated API requests using stolen tokens, enabling cross-site request forgery variants.

**Resolution:** Remove the `"*"` default. Fail closed:

```python
allow_origins=os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
```

### M-6: Error Messages Leak Exception Details to Clients

- **File:** `app-lib/src/app_lib/features/inference/routes/inference_sse_routes.py` (line 64)
- **CWE:** [CWE-209](https://cwe.mitre.org/data/definitions/209.html) — Generation of Error Message Containing Sensitive Information

**Description:** The SSE inference endpoint catches all exceptions and streams `str(exc)` to the client:

```python
except Exception as exc:
    yield f"data: {json.dumps({'error': str(exc)})}\n\n"
```

Boto3 exceptions can contain account IDs, ARNs, region names, and internal service details.

**Impact:** Attackers can trigger errors to enumerate AWS account details, IAM role names, and service configurations.

**Resolution:** Return a generic error message to clients and log the full exception server-side:

```python
except Exception as exc:
    logger.error(f"Inference error: {exc}")
    yield f"data: {json.dumps({'error': 'Inference request failed'})}\n\n"
```

### M-7: DynamoDB Tables Lack Deletion Protection

- **File:** `infra/cfn/backend/backend.yml` (PassengersTable); `infra/cfn/queue/queue.yml` (JobsTable)
- **CWE:** [CWE-693](https://cwe.mitre.org/data/definitions/693.html) — Protection Mechanism Failure

**Description:** Neither DynamoDB table has `DeletionProtectionEnabled: true`. Tables can be accidentally deleted via CloudFormation stack deletion or direct API calls.

**Impact:** Accidental data loss. A teardown command or stack deletion removes all data with no recovery path (no PITR either).

**Resolution:** Add `DeletionProtectionEnabled: true` for production deployments. Consider enabling Point-in-Time Recovery (PITR) as well.

### M-8: ECR Image Tag Mutability Allows Tag Overwrite

- **File:** `infra/cfn/ecr/ecr.yml` (line 22)
- **CWE:** [CWE-345](https://cwe.mitre.org/data/definitions/345.html) — Insufficient Verification of Data Authenticity

**Description:** `ImageTagMutability: MUTABLE` allows existing image tags to be overwritten. A `latest` or version tag can be replaced with a different image.

**Impact:** Supply chain risk — a compromised CI/CD pipeline or credential could push a malicious image under an existing tag, which Lambda would pull on the next cold start.

**Resolution:** Set `ImageTagMutability: IMMUTABLE` and use unique tags per build (for example, the git SHA).

## Low

### L-1: No CloudWatch Alarms or Dashboards

- **File:** `infra/cfn/backend/backend.yml`; `infra/cfn/queue/queue.yml`
- **CWE:** [CWE-778](https://cwe.mitre.org/data/definitions/778.html) — Insufficient Logging

**Description:** CloudWatch alarms and dashboards have been removed from tier stacks due to IAM permission conflicts with the centralized security stack. No operational alerting or dashboards exist until a dedicated observability stack is introduced.

**Impact:** Security-relevant events (high error rates, DLQ messages, exceptions) go unnoticed without manual CloudWatch console inspection.

**Resolution:** Introduce a dedicated observability stack with its own scoped IAM permissions for CloudWatch dashboards and alarms.

### L-2: No Budget Alarms for Bedrock Token Usage

- **File:** N/A (missing resource)
- **CWE:** [CWE-770](https://cwe.mitre.org/data/definitions/770.html) — Allocation of Resources Without Limits

**Description:** No AWS Budgets alarm exists for the account or namespace. Bedrock token usage is metered but not cost-capped.

**Impact:** Runaway inference costs from legitimate use or abuse.

**Resolution:** Create an AWS Budgets alarm scoped to the Bedrock service.

### L-3: CloudFront Uses Default Certificate — No Custom Domain

- **File:** `infra/cfn/frontend/frontend.yml` (Distribution ViewerCertificate)
- **CWE:** [CWE-295](https://cwe.mitre.org/data/definitions/295.html) — Improper Certificate Validation

**Description:** CloudFront uses the default `*.cloudfront.net` certificate with `CloudFrontDefaultCertificate: true`. No custom domain or ACM certificate is configured.

**Impact:** Users access the application via a non-branded URL. No ability to enforce HSTS on a custom domain. Phishing risk — users cannot distinguish the legitimate CloudFront URL from a spoofed one.

**Resolution:** Configure Route 53 and ACM for a custom domain. Add HSTS headers via a CloudFront response headers policy.

### L-4: Cognito Deletion Protection Defaults to INACTIVE

- **File:** `infra/cfn/cognito/cognito.yml` (line 23, DeletionProtection parameter, `Default: INACTIVE`)
- **CWE:** [CWE-693](https://cwe.mitre.org/data/definitions/693.html) — Protection Mechanism Failure

**Description:** The `DeletionProtection` parameter defaults to `INACTIVE`. The user pool can be accidentally deleted via stack deletion or direct API call.

**Impact:** Loss of all user accounts and authentication configuration.

**Resolution:** Set the default to `ACTIVE` for production deployments.

## Informational

### I-1: JWT Audience Verification Disabled at Decode, Custom Check Used

- **File:** `app-lib/src/app_lib/common/auth.py` (line 62)
- **CWE:** [CWE-287](https://cwe.mitre.org/data/definitions/287.html) — Improper Authentication

**Description:** The `jwt.decode()` call uses `options={"verify_aud": False}` and then performs a custom audience check via `_check_audience()`. This is intentional to handle Cognito's non-standard `client_id` claim, but it means the PyJWT library's built-in audience verification is bypassed.

**Impact:** Low — the custom check is functionally equivalent. However, any future modification to `_check_audience()` could introduce a bypass.

**Resolution:** Document the rationale inline. Consider adding a unit test that verifies tokens with the wrong audience are rejected.

### I-2: CodeBuild Privileged Mode Enabled

- **File:** `infra/cfn/codepipeline/codepipeline.yml` (CodeBuildProject, `PrivilegedMode: true`)
- **CWE:** [CWE-250](https://cwe.mitre.org/data/definitions/250.html) — Execution with Unnecessary Privileges

**Description:** CodeBuild runs in privileged mode to support Docker-in-Docker builds. This grants the build environment elevated capabilities.

**Impact:** If the build environment is compromised (for example, via a malicious dependency), the attacker has elevated privileges within the container.

**Resolution:** Accept the risk for POC. For production, consider using CodeBuild's native Docker layer caching or ECR image building without privileged mode.
