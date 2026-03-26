"""Tests for deploy cfn — create/update CloudFormation stack."""

from pathlib import Path

import click
import pytest
from moto import mock_aws

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    get_stack_status,
    parse_key_value_pairs,
)


class TestCreateOrUpdateStack:
    """Tests for create_or_update_stack()."""

    @mock_aws
    def test_create_new_stack(self, aws_session, template_path):
        """Creating a new stack succeeds and returns outputs."""
        outputs = create_or_update_stack(
            session=aws_session,
            stack_name="test-stack",
            template_path=template_path,
        )
        assert isinstance(outputs, dict)
        status = get_stack_status(aws_session, "test-stack")
        assert status == "CREATE_COMPLETE"

    @mock_aws
    def test_create_with_parameters(self, aws_session, template_path):
        """Stack creation passes parameters correctly."""
        outputs = create_or_update_stack(
            session=aws_session,
            stack_name="test-param-stack",
            template_path=template_path,
            parameters={"TableName": "custom-table"},
        )
        assert isinstance(outputs, dict)

    @mock_aws
    def test_create_with_tags(self, aws_session, template_path):
        """Stack creation passes tags correctly."""
        outputs = create_or_update_stack(
            session=aws_session,
            stack_name="test-tags-stack",
            template_path=template_path,
            tags={"Project": "test", "Environment": "dev"},
        )
        assert isinstance(outputs, dict)

    @mock_aws
    def test_update_existing_stack(self, aws_session, template_path):
        """Updating an existing stack works (no-op if no changes)."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-update-stack",
            template_path=template_path,
        )
        # Second call should succeed (no changes = no-op)
        outputs = create_or_update_stack(
            session=aws_session,
            stack_name="test-update-stack",
            template_path=template_path,
        )
        assert isinstance(outputs, dict)

    @mock_aws
    def test_create_no_wait(self, aws_session, template_path):
        """Creating with wait=False returns empty dict."""
        outputs = create_or_update_stack(
            session=aws_session,
            stack_name="test-nowait-stack",
            template_path=template_path,
            wait=False,
        )
        assert outputs == {}


class TestParseKeyValuePairs:
    """Tests for parse_key_value_pairs()."""

    def test_parse_single_pair(self):
        result = parse_key_value_pairs("Key=Value")
        assert result == {"Key": "Value"}

    def test_parse_multiple_pairs(self):
        result = parse_key_value_pairs("Key1=Val1 Key2=Val2")
        assert result == {"Key1": "Val1", "Key2": "Val2"}

    def test_parse_value_with_equals(self):
        result = parse_key_value_pairs("Key=Val=ue")
        assert result == {"Key": "Val=ue"}

    def test_parse_none(self):
        result = parse_key_value_pairs(None)
        assert result is None

    def test_parse_empty_string(self):
        result = parse_key_value_pairs("")
        assert result is None

    def test_parse_invalid_format(self):
        with pytest.raises(click.BadParameter, match="Invalid format"):
            parse_key_value_pairs("InvalidNoEquals")
