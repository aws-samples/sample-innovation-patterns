# Backend Tier Template — Agent Context

Consolidated backend tier: Lambda + API Gateway v2 + DynamoDB (feature-flagged).

Template: `infra/cfn/backend/backend.yml`

## DynamoDB Customization — 4-Touchpoint Workflow

Adding, renaming, or removing a DynamoDB table requires coordinated changes across 4 files. All 4 must stay in sync.

### The 4 Touchpoints

1. **This template** (`backend.yml`) — Parameter + Condition + Resource + IAM + Output
2. **PynamoDB model** (`app-lib/src/app_lib/features/{name}/models/`) — `PynamodbUtil.env_table_name("{suffix}")` must match the CFN table suffix
3. **Makefile** (`scripts/deploy.mk`) — `Enable{Name}Table=true` in `--parameter-overrides`
4. **App registration** (`app-lib/src/app_lib/main.py`) — `app.include_router(...)` for the feature

### Naming Contract

```
CFN TableName:  {Namespace}_{Environment}_{suffix}
PynamoDB:       PynamodbUtil.env_table_name("{suffix}")
```

The `{suffix}` value (e.g., `passengers`, `jobs`, `products`) is the contract between CFN and app-lib. They MUST match.

### Common Operations

#### Rename `passengers` → `products`

1. **backend.yml Section 3**: Change `_passengers` → `_products` in TableName, rename resource `PassengersTable` → `ProductsTable`
2. **backend.yml Section 2**: Rename condition `HasPassengersTable` → `HasProductsTable`
3. **backend.yml Section 1**: Rename parameter `EnablePassengersTable` → `EnableProductsTable`
4. **backend.yml Section 4**: Update IAM policy condition and `!GetAtt` reference
5. **backend.yml Outputs**: Rename `PassengersTableArn` → `ProductsTableArn`
6. **PynamoDB model**: `env_table_name("passengers")` → `env_table_name("products")`
7. **Makefile**: `EnablePassengersTable=true` → `EnableProductsTable=true`
8. **App**: Rename feature directory and router registration

#### Add a new table (e.g., `orders`)

1. **backend.yml Section 1**: Add `EnableOrdersTable` parameter (default `'false'`)
2. **backend.yml Section 2**: Add `HasOrdersTable: !Equals [!Ref EnableOrdersTable, 'true']`
3. **backend.yml Section 3**: Copy `PassengersTable`, rename to `OrdersTable`, change suffix to `_orders`
4. **backend.yml Section 4**: Add conditional DynamoDB IAM policy with `!GetAtt OrdersTable.Arn`
5. **backend.yml Outputs**: Add `OrdersTableArn` with `Condition: HasOrdersTable`
6. **PynamoDB model**: Create `orders` model with `PynamodbUtil.env_table_name("orders")`
7. **Makefile**: Add `EnableOrdersTable=true` to `deploy-backend` parameter overrides
8. **App**: Register orders router

#### Remove `passengers` table

1. **backend.yml**: Remove the parameter, condition, resource, IAM policy, and output
2. **PynamoDB model**: Delete the passengers model
3. **Makefile**: Remove `EnablePassengersTable=true` from parameter overrides
4. **App**: Remove passengers router registration

### Section Navigation

| Section | Line Range | Contents |
|---------|-----------|----------|
| 1: Parameters | Top | Core, wirable, Lambda config, DDB feature flags, SQS |
| 2: Conditions | After params | Feature flag conditions |
| 3: DynamoDB Tables | After conditions | Conditional table resources |
| 4: Lambda Function | After DDB | Execution role + IAM policies + function + log group |
| 5: API Gateway v2 | After Lambda | HTTP API + JWT authorizer + routes + stage |
| 6: Outputs | Bottom | Stack outputs |

## Internal Wiring

These connections are handled internally via `!Ref`/`!GetAtt` — no cross-stack parameters needed:

- `IntegrationUri: !Sub '...${LambdaFunction.Arn}...'` — API GW → Lambda
- `Resource: !GetAtt PassengersTable.Arn` — Lambda IAM → DynamoDB

## Security Properties

- DynamoDB: SSE enabled, PAY_PER_REQUEST billing, conditional creation
- Lambda: Per-function execution role, least-privilege IAM
- API Gateway: JWT authorizer (Cognito), CORS configured, access logging
- IAM: No wildcard resource ARNs for DynamoDB (uses `!GetAtt Table.Arn`)
- IAM: `Resource: '*'` for ECR pull (AWS API limitation — documented)
- Log groups: 30-day retention
