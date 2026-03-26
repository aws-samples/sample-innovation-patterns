"""Tests for list_managed_stacks()."""

from moto import mock_aws

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    list_managed_stacks,
)
from tests.conftest import SIMPLE_STACK_TEMPLATE


def _create_stack(session, stack_name, template_path):
    """Helper to create a stack with a unique table name to avoid DynamoDB collisions."""
    create_or_update_stack(
        session, stack_name, template_path,
        parameters={"TableName": f"table-{stack_name}"},
    )


class TestListManagedStacks:
    """Unit tests for list_managed_stacks()."""

    @mock_aws
    def test_lists_matching_stacks(self, aws_session, template_path):
        """Stacks matching namespace-env prefix are returned."""
        _create_stack(aws_session, "myapp-dev-security", template_path)
        _create_stack(aws_session, "myapp-dev-dynamodb", template_path)

        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        assert len(stacks) == 2
        names = [s["StackName"] for s in stacks]
        assert "myapp-dev-security" in names
        assert "myapp-dev-dynamodb" in names

    @mock_aws
    def test_excludes_non_matching_stacks(self, aws_session, template_path):
        """Stacks from a different namespace are excluded."""
        _create_stack(aws_session, "myapp-dev-security", template_path)
        _create_stack(aws_session, "other-dev-lambda", template_path)

        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        assert len(stacks) == 1
        assert stacks[0]["StackName"] == "myapp-dev-security"

    @mock_aws
    def test_extracts_service_name(self, aws_session, template_path):
        """Service name is extracted by stripping the prefix."""
        _create_stack(aws_session, "myapp-dev-cognito", template_path)

        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        assert stacks[0]["Service"] == "cognito"

    @mock_aws
    def test_returns_empty_list_when_no_matches(self, aws_session):
        """Empty list returned when no stacks match the prefix."""
        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        assert stacks == []

    @mock_aws
    def test_returns_stack_status(self, aws_session, template_path):
        """Stack status is included in results."""
        _create_stack(aws_session, "myapp-dev-s3", template_path)

        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        assert stacks[0]["StackStatus"] == "CREATE_COMPLETE"

    @mock_aws
    def test_sorted_by_name(self, aws_session, template_path):
        """Results are sorted alphabetically by stack name."""
        _create_stack(aws_session, "myapp-dev-s3", template_path)
        _create_stack(aws_session, "myapp-dev-dynamodb", template_path)
        _create_stack(aws_session, "myapp-dev-cognito", template_path)

        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        names = [s["StackName"] for s in stacks]
        assert names == ["myapp-dev-cognito", "myapp-dev-dynamodb", "myapp-dev-s3"]

    @mock_aws
    def test_filters_by_environment(self, aws_session, template_path):
        """Only stacks matching the specified environment are returned."""
        _create_stack(aws_session, "myapp-dev-security", template_path)
        _create_stack(aws_session, "myapp-staging-security", template_path)

        stacks = list_managed_stacks(aws_session, namespace="myapp", env="dev")

        assert len(stacks) == 1
        assert stacks[0]["StackName"] == "myapp-dev-security"
