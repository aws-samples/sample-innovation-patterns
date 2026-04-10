"""DynamoDB model for background jobs."""

from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

from app_lib.common.util.pynamodb_util import PynamodbUtil


class JobTable(Model):
    """Background job DynamoDB table model."""

    class Meta:
        """PynamoDB table configuration for background jobs."""

        table_name = PynamodbUtil.env_table_name("jobs")

    id = UnicodeAttribute(hash_key=True)
    status = UnicodeAttribute()  # PENDING | PROCESSING | COMPLETED | FAILED
    job_type = UnicodeAttribute()  # e.g., "passenger_analysis"
    input_data = UnicodeAttribute()  # JSON string
    metadata = UnicodeAttribute(null=True)  # Small JSON dict for use-case references
    error = UnicodeAttribute(null=True)
    created_at = UnicodeAttribute()  # ISO 8601
    updated_at = UnicodeAttribute()  # ISO 8601
