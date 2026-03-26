"""Tests for deploy cfn-delete — delete CloudFormation stack."""

import pytest
from moto import mock_aws

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    delete_stack,
    get_stack_status,
)


class TestDeleteStack:
    """Tests for delete_stack()."""

    @mock_aws
    def test_delete_existing_stack(self, aws_session, template_path):
        """Deleting an existing stack succeeds."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-delete-stack",
            template_path=template_path,
        )
        delete_stack(aws_session, "test-delete-stack")
        status = get_stack_status(aws_session, "test-delete-stack")
        # moto may return None or DELETE_COMPLETE
        assert status is None or status == "DELETE_COMPLETE"

    @mock_aws
    def test_delete_nonexistent_stack(self, aws_session):
        """Deleting a nonexistent stack is a no-op."""
        # Should not raise
        delete_stack(aws_session, "nonexistent-stack")

    @mock_aws
    def test_delete_no_wait(self, aws_session, template_path):
        """Deleting with wait=False returns immediately."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-delete-nowait",
            template_path=template_path,
        )
        delete_stack(aws_session, "test-delete-nowait", wait=False)
