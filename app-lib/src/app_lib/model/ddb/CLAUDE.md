# model/ddb/

PynamoDB models. See `pynamodb-conventions.md` steering for template.

**Critical:** Use `null=True` for optional fields — omitting this causes `AttributeNullError` at runtime.
