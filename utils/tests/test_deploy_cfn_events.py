"""Tests for deploy cfn-events — read stack events."""

import click
import pytest
from moto import mock_aws

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    get_stack_events,
)


class TestGetStackEvents:
    """Tests for get_stack_events()."""

    @mock_aws
    def test_get_events_existing_stack(self, aws_session, template_path):
        """Getting events for an existing stack returns a list."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-events-stack",
            template_path=template_path,
        )
        events = get_stack_events(aws_session, "test-events-stack")
        assert isinstance(events, list)
        assert len(events) > 0
        # Check event structure
        event = events[0]
        assert "Timestamp" in event
        assert "LogicalResourceId" in event
        assert "ResourceStatus" in event
        assert "ResourceStatusReason" in event

    @mock_aws
    def test_get_events_with_limit(self, aws_session, template_path):
        """Limit parameter restricts the number of events returned."""
        create_or_update_stack(
            session=aws_session,
            stack_name="test-events-limit",
            template_path=template_path,
        )
        events = get_stack_events(aws_session, "test-events-limit", limit=2)
        assert len(events) <= 2

    @mock_aws
    def test_get_events_nonexistent_stack(self, aws_session):
        """Getting events for a nonexistent stack raises ClickException."""
        with pytest.raises(click.ClickException, match="does not exist"):
            get_stack_events(aws_session, "nonexistent-stack")
