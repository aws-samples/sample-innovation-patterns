"""Tests for deploy cfn-status — check stack existence and status."""

from moto import mock_aws

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    get_stack_status,
)


class TestGetStackStatus:
    """Tests for get_stack_status()."""

    @mock_aws
    def test_existing_stack(self, aws_session, template_path):
        """Existing stack returns its status string."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-status-stack",
            template_path=template_path,
        )
        status = get_stack_status(aws_session, "test-status-stack")
        assert status == "CREATE_COMPLETE"

    @mock_aws
    def test_nonexistent_stack(self, aws_session):
        """Nonexistent stack returns None."""
        status = get_stack_status(aws_session, "nonexistent-stack")
        assert status is None
