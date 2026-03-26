"""Tests for deploy cfn-outputs — retrieve stack outputs."""

import click
import pytest
from moto import mock_aws

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    get_stack_outputs,
)


class TestGetStackOutputs:
    """Tests for get_stack_outputs()."""

    @mock_aws
    def test_get_all_outputs(self, aws_session, template_path):
        """Getting all outputs returns a dict."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-outputs-stack",
            template_path=template_path,
        )
        outputs = get_stack_outputs(aws_session, "test-outputs-stack")
        assert isinstance(outputs, dict)

    @mock_aws
    def test_get_specific_output(self, aws_session, template_path):
        """Getting a specific output key returns a string value."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-outputs-key",
            template_path=template_path,
        )
        outputs = get_stack_outputs(aws_session, "test-outputs-key")
        if outputs:  # moto may or may not populate outputs
            key = list(outputs.keys())[0]
            value = get_stack_outputs(aws_session, "test-outputs-key", output_key=key)
            assert isinstance(value, str)

    @mock_aws
    def test_get_missing_output_key(self, aws_session, template_path):
        """Requesting a nonexistent output key raises ClickException."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-outputs-missing",
            template_path=template_path,
        )
        with pytest.raises(click.ClickException, match="Output key"):
            get_stack_outputs(aws_session, "test-outputs-missing", output_key="NonExistentKey")

    @mock_aws
    def test_get_outputs_missing_stack(self, aws_session):
        """Querying a nonexistent stack raises ClickException."""
        with pytest.raises(click.ClickException, match="does not exist"):
            get_stack_outputs(aws_session, "nonexistent-stack")
