# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""PynamoDB utility functions."""

import os


class PynamodbUtil:
    """Utilities for PynamoDB model configuration."""

    @staticmethod
    def env_table_name(base_name: str) -> str:
        """Prefix table name with APP_NAMESPACE and APP_ENV.

        Args:
            base_name: Base table name (e.g., "titanic_passengers")

        Returns:
            "{APP_NAMESPACE}_{APP_ENV}_{base_name}" when APP_NAMESPACE is set,
            "{APP_ENV}_{base_name}" otherwise. APP_ENV defaults to "dev".
        """
        env = os.environ.get("APP_ENV", "dev")
        namespace = os.environ.get("APP_NAMESPACE", "")
        if namespace:
            return f"{namespace}_{env}_{base_name}"
        return f"{env}_{base_name}"
