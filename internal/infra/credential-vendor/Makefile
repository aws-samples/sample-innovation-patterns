# Credential vendor role — the one-time, hand-run deploy of the IAM role this
# repository's GitLab CI jobs assume. Internal maintainer tooling; not shipped.
#
# A bare `make` prints help and creates nothing. Both targets that change an AWS
# account require CONFIRM=1, and WITHOUT it they print exactly what they would
# do — against which account, read from sts:get-caller-identity rather than from
# a variable — and stop. That is the guard that matters here: the risk is not a
# malformed template, it is landing the role in the wrong account. `make deploy`
# with no CONFIRM is therefore the dry run.
#
# This mirrors ../codepipeline/Makefile deliberately, including the target names.
# Two sibling directories under internal/infra/ disagreeing about which
# operations need confirmation, or about whether the destructive one is called
# `delete` or `destroy`, is exactly the drift that gets a guard skipped.
#
# This wraps commands README.md also documents directly. Windows has no `make` —
# use those.

.DEFAULT_GOAL := help
.PHONY: help validate deploy outputs status destroy

HERE := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TEMPLATE := $(HERE)credential-vendor.yml

STACK_NAME ?= ipa-gitlab-ci-role
ROLE_NAME ?= InnovationPatternsGitLabCI

# The pipeline stack this role is allowed to start. Its outputs supply
# SOURCE_BUCKET below when that is not passed explicitly.
PIPELINE_STACK ?= ipa-integration-test-pipeline
SOURCE_OBJECT_KEY ?= source/source.zip

# Empty by default and resolved from the pipeline stack inside the deploy recipe.
# Not a $(shell ...) at parse time: that would call AWS on every invocation of
# this Makefile, including `make help`, which must cost nothing.
SOURCE_BUCKET ?=

# `aws configure list-profiles` is the check rather than grepping ~/.aws/config,
# because it reads both config and credentials files and knows their formats.
# grep -Fx so the profile's '+' is matched literally, and so a longer profile
# that merely CONTAINS this name does not count as a match.
#
# The existence check is the part that matters. A maintainer-specific default is
# right for the person who wrote it and wrong on a CloudDesktop or EC2 host using
# an instance role — and `--profile <missing>` is a HARD failure there ("could
# not be found"), not a fall-through to ambient credentials. So the default
# applies only where it is real.
AWS_DEFAULT_PROFILE_NAME := vincilb+ip-dev-Admin
AWS_PROFILE ?= $(shell aws configure list-profiles 2>/dev/null \
	| grep -Fxq "$(AWS_DEFAULT_PROFILE_NAME)" \
	&& echo "$(AWS_DEFAULT_PROFILE_NAME)")

# DEFAULTED, unlike the reference implementation's credential-vendor Makefile,
# and the difference is deliberate. That stack creates a role with only a global
# managed policy attached, so omitting the region is right there. This role's
# inline policy names REGIONAL ARNs — the pipeline, the build project, the log
# group — so a stack landing in whatever region a profile happens to default to
# would grant nothing usable, and would be discovered only by a CI job being
# denied.
#
# us-east-1 matches ../codepipeline/Makefile and the region .gitlab-ci.yml's
# credentials block already sets.
#
# `:=` rather than `?=`, for the reason recorded in ../codepipeline/Makefile: `?=`
# yields to an EXPORTED variable, and a shell exporting AWS_REGION=us-west-2
# silently captured it. A command-line `make AWS_REGION=<r> <target>` still wins.
AWS_REGION := us-east-1

# Passed as flags, never exported. A maintainer deploys this by hand under a
# named profile, but exporting AWS_PROFILE leaks into everything else the shell
# later runs, and an empty default keeps these same targets usable under vended
# credentials.
PROFILE_FLAG := $(if $(AWS_PROFILE),--profile "$(AWS_PROFILE)",)
AWS := aws $(PROFILE_FLAG) --region "$(AWS_REGION)"

# Derive the identity values from the remote rather than hardcoding them. A fork,
# a renamed project, or a moved group makes literals wrong, and a wrong group
# path fails CLOSED at assume time — denied, with nothing naming the path as the
# cause. Both remote forms are handled:
#   git@ssh.code.aws.dev:proserve/genaiid/other/candidate-reusable-assets/innovation-patterns.git
#   https://code.aws.dev/proserve/genaiid/other/candidate-reusable-assets/innovation-patterns.git
# by stripping scheme+host, then user@host:, then the .git suffix. The group is
# everything but the last path segment — every subgroup included, which is the
# part that must not be shortened.
#
# sed uses | as its delimiter, not the usual #, because Make treats # as the
# start of a comment even inside $(shell ...) — with # here the whole call is
# swallowed and Make dies on an unterminated function.
REMOTE_PATH := $(shell git -C "$(HERE)" remote get-url origin 2>/dev/null \
	| sed -e 's|^[a-z+]*://[^/]*/||' -e 's|^.*:||' -e 's|\.git$$||')
GITLAB_GROUP ?= $(patsubst %/,%,$(dir $(REMOTE_PATH)))
GITLAB_PROJECT ?= $(notdir $(REMOTE_PATH))

help: ## Show this help
	@echo "Credential vendor role — one-time manual deploy"
	@echo ""
	@echo "Targets that CHANGE an AWS account (both need CONFIRM=1):"
	@echo "  deploy    Create or update the role. Without CONFIRM=1 this is a DRY"
	@echo "            RUN: it prints the target account and parameters, then stops."
	@echo "  destroy   Delete the stack and the role. Any CI job configured with"
	@echo "            its ARN starts failing."
	@echo ""
	@echo "Read-only targets (create nothing, cost nothing):"
	@echo "  validate  Check the template is structurally valid"
	@echo "  outputs   Print the stack's outputs, including the role ARN"
	@echo "  status    Print the stack's current status"
	@echo "  help      Show this message (default)"
	@echo ""
	@echo "Derived from 'git remote get-url origin':"
	@echo "  GitLabGroupName    $(if $(GITLAB_GROUP),$(GITLAB_GROUP),<COULD NOT DERIVE>)"
	@echo "  GitLabProjectName  $(if $(GITLAB_PROJECT),$(GITLAB_PROJECT),<COULD NOT DERIVE>)"
	@echo "  Override either with 'make GITLAB_GROUP=<group/path> ... <target>'."
	@echo ""
	@echo "Other variables:"
	@echo "  STACK_NAME=$(STACK_NAME)  ROLE_NAME=$(ROLE_NAME)"
	@echo "  AWS_REGION=$(AWS_REGION)  PIPELINE_STACK=$(PIPELINE_STACK)"
	@echo "  SOURCE_BUCKET=$(if $(SOURCE_BUCKET),$(SOURCE_BUCKET),<read from $(PIPELINE_STACK) at deploy time>)"
	@echo ""
	@echo "AWS profile: $(if $(AWS_PROFILE),$(AWS_PROFILE),<none — using ambient credentials>)"
	@echo "  Defaults to $(AWS_DEFAULT_PROFILE_NAME) when that profile exists on"
	@echo "  this machine; otherwise no --profile is passed. Either way, 'make"
	@echo "  deploy' prints the resolved account before doing anything — that line"
	@echo "  is the one to check, not this one."
	@echo ""
	@echo "ORDER: deploy ../codepipeline FIRST. This role's policy names that"
	@echo "  stack's bucket and pipeline, and the bucket name is generated."
	@echo ""
	@echo "This role is deployed ONCE, BY HAND, per account. No CI job deploys it."
	@echo "It holds NO deploy permissions — see README.md for what it can do and"
	@echo "for why that is still indirect administrator access."

validate: ## Check the template is structurally valid (creates nothing)
	@$(AWS) cloudformation validate-template \
		--template-body "file://$(TEMPLATE)" --output table

# ONE shell block, continuations included, so the dry-run `exit 0` ends the whole
# target. Do NOT split the post-deploy reporting into separate recipe lines:
# `exit 0` only leaves its own line's subshell, so make would carry on and run
# `outputs` against a stack the dry run never created — which fails with a bare
# DescribeStacks ValidationError and makes a successful dry run look broken.
deploy: ## Create/update the role. Needs CONFIRM=1. CREATES AN IAM ROLE.
	@set -e; \
	if [ -z "$(GITLAB_GROUP)" ] || [ -z "$(GITLAB_PROJECT)" ]; then \
		echo "ERROR: could not derive the GitLab group and project from the origin remote."; \
		echo "  Pass them explicitly — the group path must include every subgroup:"; \
		echo "    make deploy GITLAB_GROUP=<group/path> GITLAB_PROJECT=<project> CONFIRM=1"; \
		exit 1; \
	fi; \
	echo "Deploying INTO this account — check it before confirming:"; \
	$(AWS) sts get-caller-identity \
		--query "join('  ', [Account, Arn])" --output text \
		|| { echo "ERROR: no usable AWS credentials. Set AWS_PROFILE or refresh them."; exit 1; }; \
	bucket="$(SOURCE_BUCKET)"; \
	if [ -z "$$bucket" ]; then \
		bucket="$$($(AWS) cloudformation describe-stacks --stack-name "$(PIPELINE_STACK)" \
			--query "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue | [0]" \
			--output text 2>/dev/null || true)"; \
	fi; \
	if [ -z "$$bucket" ] || [ "$$bucket" = "None" ]; then \
		echo ""; \
		echo "ERROR: could not resolve the source bucket."; \
		echo "  It is read from the '$(PIPELINE_STACK)' stack's SourceBucketName"; \
		echo "  output, which means that stack must exist in this account and region."; \
		echo "  Deploy it first:   make -C ../codepipeline deploy CONFIRM=1"; \
		echo "  Or pass it:        make deploy SOURCE_BUCKET=<bucket> CONFIRM=1"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "Stack:              $(STACK_NAME)"; \
	echo "Region:             $(AWS_REGION)"; \
	echo "RoleName:           $(ROLE_NAME)"; \
	echo "GitLabGroupName:    $(GITLAB_GROUP)"; \
	echo "GitLabProjectName:  $(GITLAB_PROJECT)"; \
	echo "PipelineName:       $(PIPELINE_STACK)"; \
	echo "SourceBucketName:   $$bucket"; \
	echo "SourceObjectKey:    $(SOURCE_OBJECT_KEY)"; \
	echo ""; \
	echo "Creates an IAM role assumable ONLY by the code.aws.dev credential"; \
	echo "vendor's hop-2 role, and only for the group and project above. It can"; \
	echo "upload one S3 key, start that one pipeline, and read the result. It"; \
	echo "holds no deploy permissions — but the code it uploads runs under the"; \
	echo "pipeline's AdministratorAccess build role, so this is still INDIRECT"; \
	echo "administrator access. A wrong group or project is the whole security"; \
	echo "surface: there is no permissions boundary and no trust expiry."; \
	if [ "$(CONFIRM)" != "1" ]; then \
		echo ""; \
		echo "DRY RUN — nothing was deployed. To create it for real:"; \
		echo "  make deploy CONFIRM=1"; \
		exit 0; \
	fi; \
	echo ""; \
	$(AWS) cloudformation deploy \
		--template-file "$(TEMPLATE)" \
		--stack-name "$(STACK_NAME)" \
		--parameter-overrides \
			RoleName="$(ROLE_NAME)" \
			GitLabGroupName="$(GITLAB_GROUP)" \
			GitLabProjectName="$(GITLAB_PROJECT)" \
			PipelineName="$(PIPELINE_STACK)" \
			SourceBucketName="$$bucket" \
			SourceObjectKey="$(SOURCE_OBJECT_KEY)" \
		--capabilities CAPABILITY_NAMED_IAM; \
	echo ""; \
	$(MAKE) --no-print-directory outputs; \
	echo ""; \
	echo "Next: set GitLabRoleArn as the AWS_CREDS_TARGET_ROLE CI/CD variable and"; \
	echo "uncomment the variables block in .gitlab-ci.yml (lines 32-43)."

outputs: ## Print the stack's outputs, including the role ARN
	@$(AWS) cloudformation describe-stacks --stack-name "$(STACK_NAME)" \
		--query "Stacks[0].Outputs" --output table \
		|| { echo "No stack named '$(STACK_NAME)' in $(AWS_REGION)."; \
			echo "Deploy it with: make deploy CONFIRM=1"; exit 1; }
	@echo "GitLabRoleArn is the value for the AWS_CREDS_TARGET_ROLE CI/CD variable."

status: ## Print the stack's current status
	@$(AWS) cloudformation describe-stacks --stack-name "$(STACK_NAME)" \
		--query "Stacks[0].StackStatus" --output text \
		|| { echo "No stack named '$(STACK_NAME)' in $(AWS_REGION)."; exit 1; }

destroy: ## Delete the stack and the role. Needs CONFIRM=1. DELETES AN IAM ROLE.
	@set -e; \
	echo "Deleting stack '$(STACK_NAME)' FROM this account:"; \
	$(AWS) sts get-caller-identity \
		--query "join('  ', [Account, Arn])" --output text \
		|| { echo "ERROR: no usable AWS credentials. Set AWS_PROFILE or refresh them."; exit 1; }; \
	echo ""; \
	echo "This DELETES the IAM role. Any CI job configured with its ARN starts"; \
	echo "failing, and re-creating it does not restore the old sessions."; \
	echo ""; \
	echo "It does NOT touch the pipeline. Delete that separately with"; \
	echo "'make -C ../codepipeline destroy CONFIRM=1'."; \
	if [ "$(CONFIRM)" != "1" ]; then \
		echo ""; \
		echo "DRY RUN — nothing was deleted. To delete it for real:"; \
		echo "  make destroy CONFIRM=1"; \
		exit 0; \
	fi; \
	echo ""; \
	$(AWS) cloudformation delete-stack --stack-name "$(STACK_NAME)"; \
	echo "Delete requested. Waiting for it to finish..."; \
	$(AWS) cloudformation wait stack-delete-complete --stack-name "$(STACK_NAME)"; \
	echo "Deleted."
