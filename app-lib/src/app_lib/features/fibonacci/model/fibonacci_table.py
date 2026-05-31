# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""DynamoDB model for Fibonacci records."""

from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from pynamodb.models import Model

from app_lib.common.util.pynamodb_util import PynamodbUtil


class FibonacciTable(Model):
    """Fibonacci record DynamoDB table model."""

    class Meta:
        """PynamoDB table configuration for Fibonacci records."""

        table_name = PynamodbUtil.env_table_name("fibonacci")

    id = UnicodeAttribute(hash_key=True)
    value = NumberAttribute()
    created_at = UnicodeAttribute()  # ISO 8601
