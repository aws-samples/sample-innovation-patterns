"""Tests for PynamodbUtil."""

import os
from unittest.mock import patch

from app_lib.common.util.pynamodb_util import PynamodbUtil


class TestEnvTableName:
    def test_default_env_no_namespace(self):
        with patch.dict(os.environ, {}, clear=True):
            assert PynamodbUtil.env_table_name("passengers") == "dev_passengers"

    def test_custom_env_no_namespace(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=True):
            assert PynamodbUtil.env_table_name("passengers") == "staging_passengers"

    def test_namespace_with_default_env(self):
        with patch.dict(os.environ, {"APP_NAMESPACE": "titanic"}, clear=True):
            assert PynamodbUtil.env_table_name("passengers") == "titanic_dev_passengers"

    def test_namespace_with_custom_env(self):
        with patch.dict(
            os.environ, {"APP_NAMESPACE": "acme", "APP_ENV": "prod"}, clear=True
        ):
            assert PynamodbUtil.env_table_name("passengers") == "acme_prod_passengers"

    def test_empty_namespace_ignored(self):
        with patch.dict(
            os.environ, {"APP_NAMESPACE": "", "APP_ENV": "dev"}, clear=True
        ):
            assert PynamodbUtil.env_table_name("passengers") == "dev_passengers"
