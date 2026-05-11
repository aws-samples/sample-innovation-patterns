# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""PynamoDB utility functions."""

import os

from dotenv import load_dotenv

# Populate APP_NAMESPACE / APP_ENV / AWS_* from repo-root .env for standalone
# CLI invocations (e.g., load_dynamodb_util). override=True so project-declared
# config wins over a stale shell env (e.g., AWS_PROFILE pointing at the wrong
# account). No-op in Lambda where no .env exists. Must run before any Model's
# Meta.table_name is evaluated.
load_dotenv(override=True)


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
