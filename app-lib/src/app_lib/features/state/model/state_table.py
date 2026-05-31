# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""DynamoDB model for singleton state record."""

from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

from app_lib.common.util.pynamodb_util import PynamodbUtil


class StateTable(Model):
    """Singleton state DynamoDB table model.

    Manages a single record with id="current" containing a random
    banded level (low, mid, high) and last update timestamp.
    """

    class Meta:
        """PynamoDB table configuration for state records."""

        table_name = PynamodbUtil.env_table_name("state")

    id = UnicodeAttribute(hash_key=True)  # Fixed value: "current"
    level = UnicodeAttribute()  # One of: "low", "mid", "high"
    updated_at = UnicodeAttribute()  # ISO 8601 timestamp
