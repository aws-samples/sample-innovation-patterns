"""Dynamic CloudFormation template generation.

Generates CloudFormation YAML templates at runtime so that
security-sensitive configurations (managed policies, role ARNs)
are never committed to the repository.

Generated templates are written to infra/cfn/generated/ which
is .gitignored.
"""

from pathlib import Path

import yaml


def generate_security_template(
    namespace: str,
    env: str,
    account_id: str,
    managed_policy: str | None = None,
    role_arn: str | None = None,
) -> str:
    """Generate the security stack CloudFormation template.

    Creates a template with:
    - Builder Execution Role (assumes builder's principal, attaches managed policy)
    - CodeBuild Execution Role (assumes codebuild.amazonaws.com, attaches managed policy)

    If role_arn is provided, skips role creation and just outputs the ARN.

    Returns YAML string.
    """
    if role_arn:
        # Existing role — just output it
        template: dict = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"Security stack for {namespace}-{env} (existing role reference)",
            "Outputs": {
                "BuilderRoleArn": {
                    "Value": role_arn,
                    "Export": {
                        "Name": {"Fn::Sub": "${AWS::StackName}-BuilderRoleArn"},
                    },
                },
            },
        }
        return yaml.dump(template, default_flow_style=False, sort_keys=False)

    policy_arn = f"arn:aws:iam::aws:policy/{managed_policy}" if managed_policy else "arn:aws:iam::aws:policy/ReadOnlyAccess"

    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": f"Security stack for {namespace}-{env} — Builder and CodeBuild execution roles",
        "Parameters": {
            "Namespace": {
                "Type": "String",
                "Default": namespace,
            },
            "AppEnv": {
                "Type": "String",
                "Default": env,
            },
        },
        "Resources": {
            "BuilderExecutionRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": {"Fn::Sub": f"{namespace}-{env}-builder-role"},
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": f"arn:aws:iam::{account_id}:root",
                                },
                                "Action": "sts:AssumeRole",
                            },
                        ],
                    },
                    "ManagedPolicyArns": [policy_arn],
                },
            },
            "CodeBuildExecutionRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": {"Fn::Sub": f"{namespace}-{env}-codebuild-role"},
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "codebuild.amazonaws.com",
                                },
                                "Action": "sts:AssumeRole",
                            },
                        ],
                    },
                    "ManagedPolicyArns": [policy_arn],
                },
            },
        },
        "Outputs": {
            "BuilderRoleArn": {
                "Value": {"Fn::GetAtt": ["BuilderExecutionRole", "Arn"]},
                "Export": {
                    "Name": {"Fn::Sub": "${AWS::StackName}-BuilderRoleArn"},
                },
            },
            "CodeBuildRoleArn": {
                "Value": {"Fn::GetAtt": ["CodeBuildExecutionRole", "Arn"]},
                "Export": {
                    "Name": {"Fn::Sub": "${AWS::StackName}-CodeBuildRoleArn"},
                },
            },
        },
    }

    return yaml.dump(template, default_flow_style=False, sort_keys=False)


def write_template(content: str, output_path: Path) -> None:
    """Write template to disk, creating parent directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
