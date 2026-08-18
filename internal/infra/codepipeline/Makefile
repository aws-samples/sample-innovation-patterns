# Integration-test pipeline — the hand-run lifecycle of the stack that runs
# internal/integration-tests on CodeBuild, and the hand-run lifecycle of a RUN.
# Internal maintainer tooling; not shipped.
#
# A bare `make` prints help and creates nothing. Every target that changes an AWS
# account or spends money requires CONFIRM=1, and WITHOUT it prints exactly what
# it would do — against which account, read from sts:get-caller-identity rather
# than from a variable — and stops. That is the guard that matters: the risk is
# not a malformed template, it is landing an AdministratorAccess role in the wrong
# account, deleting shared infrastructure other maintainers are using, or starting
# a billable run nobody was expecting.
#
# This mirrors ../credential-vendor/Makefile deliberately, including the target
# names. Two sibling directories under internal/infra/ disagreeing about which
# operations need confirmation, or about whether the destructive one is called
# `delete` or `destroy`, is exactly the drift that gets a guard skipped.
#
# THE STACK's lifecycle:  validate  deploy  outputs  status  destroy
# A RUN's lifecycle:      archive  upload  start  watch  trigger  logs
#
# The reference implementation splits those two groups into separate directories
# so that `destroy` is not in the file invoked on every run. They are together
# here because this is installed by hand as one unit; the compensating control is
# that `destroy` needs CONFIRM=1 and prints what it will delete first.
#
# This wraps commands README.md also documents directly. Windows has no `make` —
# use those.

.DEFAULT_GOAL := help
.PHONY: help validate deploy outputs status destroy archive upload start watch \
        trigger logs

HERE := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(HERE)../../..)
TEMPLATE := $(HERE)integration-test-pipeline.yml

STACK_NAME ?= ipa-integration-test-pipeline
SOURCE_OBJECT_KEY ?= source/source.zip

# Written outside the repository, so an archive of the tree never contains a
# previous archive of the tree.
ARCHIVE ?= /tmp/ipa-integration-test-source.zip

# `aws configure list-profiles` is the check rather than grepping ~/.aws/config,
# because it reads both config and credentials files and knows their formats.
# grep -Fx so the profile's '+' is matched literally, and so a longer profile that
# merely CONTAINS this name does not count as a match.
#
# The existence check is the part that matters: `--profile <missing>` is a HARD
# failure on a host using an instance role, not a fall-through to ambient
# credentials, so the default applies only where it is real.
#
# NOTE the account this names, because three contexts can disagree and this line
# is where that decision is recorded.
#
# This profile is only for DEPLOYING this stack from a workstation. The harness
# itself no longer has a profile default of any kind: it authenticates from the
# default credential chain (harness/aws.py), and the constant that used to hold a
# maintainer's profile is deleted. Inside the build there is no profile with
# credentials either — the buildspec creates a credential-less `ipa-it` profile
# that falls through to the container's own role.
#
# So the only remaining question is which account owns this stack. This
# repository's .env names vincilb+ip-dev-Admin; the manual harness runs recorded
# in DECISIONS.md were measured against a different, evaluation-sandbox account.
# Decide before deploying.
AWS_DEFAULT_PROFILE_NAME := vincilb+ip-dev-Admin
AWS_PROFILE ?= $(shell aws configure list-profiles 2>/dev/null \
	| grep -Fxq "$(AWS_DEFAULT_PROFILE_NAME)" \
	&& echo "$(AWS_DEFAULT_PROFILE_NAME)")

# PINNED, and `:=` rather than `?=` — measured, not stylistic. Everything in this
# stack is REGIONAL — a bucket, a pipeline, a build project, a log group — so a
# stack landing in whatever region something else chose would be discovered only
# by failing to find it.
#
# `?=` does not defend against that, because it yields to an EXPORTED variable.
# The shell this was written in exports AWS_REGION=us-west-2 (the same ambient
# value preflight.py's docstring calls out), and `?=` silently adopted it: `make
# help` printed AWS_REGION=us-west-2 while this line said us-east-1. A simple `:=`
# is what pins it, and a command-line `make AWS_REGION=<r> <target>` still wins,
# because a command-line variable overrides a makefile assignment.
AWS_REGION := us-east-1

# Passed as a flag, never exported. A maintainer runs this by hand under a named
# profile, but exporting AWS_PROFILE leaks into everything else the shell later
# runs, and an empty default keeps these same targets usable under vended
# credentials.
PROFILE_FLAG := $(if $(AWS_PROFILE),--profile "$(AWS_PROFILE)",)
AWS := aws $(PROFILE_FLAG) --region "$(AWS_REGION)"

# A bare python3. archive.py and empty_bucket.py are stdlib-only precisely so this
# needs no virtualenv: teardown must not fail with an ImportError at the moment an
# operator is trying to delete infrastructure.
PYTHON ?= python3

help: ## Show this help
	@echo "Integration-test pipeline — hand-run stack and run lifecycle"
	@echo ""
	@echo "THE STACK (deploy/destroy need CONFIRM=1):"
	@echo "  deploy    Create or update the stack: a versioned S3 bucket, a narrow"
	@echo "            pipeline role, a build role holding AdministratorAccess, one"
	@echo "            CodeBuild project and one pipeline. The pipeline is INERT —"
	@echo "            uploading an archive starts nothing. Without CONFIRM=1 this"
	@echo "            is a DRY RUN: it prints the target account, then stops."
	@echo "  destroy   Delete the stack. Empties every object VERSION and delete"
	@echo "            marker first, because the bucket is versioned and"
	@echo "            delete-stack fails otherwise. DESTROYS SHARED"
	@echo "            INFRASTRUCTURE — any maintainer or CI job using this"
	@echo "            pipeline stops being able to trigger a run."
	@echo "  validate  Check the template is structurally valid (creates nothing)"
	@echo "  outputs   Print the stack's outputs — including the two values"
	@echo "            ../credential-vendor needs"
	@echo "  status    Print the stack's current status"
	@echo ""
	@echo "A RUN (start/trigger need CONFIRM=1 — they SPEND MONEY):"
	@echo "  archive   Build the source zip from the WORKING TREE, including .git."
	@echo "            Free. Refuses to run from a linked git worktree."
	@echo "  upload    Upload the archive to the source key. Starts nothing."
	@echo "  start     Start one pipeline execution. BILLABLE."
	@echo "  watch     Poll the latest execution until it finishes."
	@echo "  trigger   archive + upload + start + watch. BILLABLE."
	@echo "  logs      Tail the most recent build's CloudWatch log stream."
	@echo ""
	@echo "COST. The stack itself is close to free at rest: an empty bucket, two IAM"
	@echo "  roles, a pipeline definition and a log group. Every EXECUTION costs:"
	@echo "    - BUILD_GENERAL1_LARGE build minutes, up to the template's"
	@echo "      $(shell grep -A3 'BuildTimeoutMinutes:' "$(TEMPLATE)" | grep Default | tr -dc '0-9')-minute ceiling"
	@echo "    - model spend, up to \$$15 on the full-lifecycle path (driver.py:371)"
	@echo "    - everything the integration test itself deploys, until it is torn"
	@echo "      down. post_build tears down unconditionally, but a build killed"
	@echo "      outside its own lifecycle can still leave seven stacks standing."
	@echo ""
	@echo "Variables:"
	@echo "  STACK_NAME=$(STACK_NAME)  AWS_REGION=$(AWS_REGION)"
	@echo "  SOURCE_OBJECT_KEY=$(SOURCE_OBJECT_KEY)"
	@echo "  ARCHIVE=$(ARCHIVE)"
	@echo "  AWS profile: $(if $(AWS_PROFILE),$(AWS_PROFILE),<none — ambient credentials>)"
	@echo ""
	@echo "SECURITY POSTURE, stated plainly: the build role holds"
	@echo "  AdministratorAccess. s3:PutObject on the source key plus"
	@echo "  codepipeline:StartPipelineExecution are the ENTIRE control on running"
	@echo "  arbitrary code as an administrator in the target account. See README.md."

validate: ## Check the template is structurally valid (creates nothing)
	@$(AWS) cloudformation validate-template \
		--template-body "file://$(TEMPLATE)" --output table

# ONE shell block, continuations included, so the dry-run `exit 0` ends the whole
# target. Do NOT split the post-deploy reporting into separate recipe lines:
# `exit 0` only leaves its own line's subshell, so make would carry on and run
# `outputs` against a stack the dry run never created — which fails with a bare
# DescribeStacks ValidationError and makes a successful dry run look broken.
deploy: ## Create/update the stack. Needs CONFIRM=1. CREATES AWS RESOURCES.
	@set -e; \
	echo "Deploying INTO this account — check it before confirming:"; \
	$(AWS) sts get-caller-identity \
		--query "join('  ', [Account, Arn])" --output text \
		|| { echo "ERROR: no usable AWS credentials. Set AWS_PROFILE or refresh them."; exit 1; }; \
	echo ""; \
	echo "Stack:       $(STACK_NAME)"; \
	echo "Region:      $(AWS_REGION)"; \
	echo "Template:    $(TEMPLATE)"; \
	echo ""; \
	echo "Creates a versioned S3 bucket, a narrow pipeline role, a build role"; \
	echo "holding AdministratorAccess, one CodeBuild project and one pipeline. The"; \
	echo "pipeline is INERT: PollForSourceChanges is false, so uploading an archive"; \
	echo "starts nothing."; \
	echo ""; \
	echo "The build role has NO permissions boundary and NO session cap. Write"; \
	echo "access to the source key is write access to code that runs as an"; \
	echo "administrator here."; \
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
		--capabilities CAPABILITY_IAM; \
	echo ""; \
	$(MAKE) --no-print-directory outputs; \
	echo ""; \
	echo "Next: 'make trigger CONFIRM=1' to run the test, or deploy the CI role"; \
	echo "with 'make -C ../credential-vendor deploy CONFIRM=1'."

outputs: ## Print the stack's outputs — what the trigger and CI role read
	@$(AWS) cloudformation describe-stacks --stack-name "$(STACK_NAME)" \
		--query "Stacks[0].Outputs" --output table \
		|| { echo "No stack named '$(STACK_NAME)' in $(AWS_REGION)."; \
			echo "Deploy it with: make deploy CONFIRM=1"; exit 1; }

status: ## Print the stack's current status
	@$(AWS) cloudformation describe-stacks --stack-name "$(STACK_NAME)" \
		--query "Stacks[0].StackStatus" --output text \
		|| { echo "No stack named '$(STACK_NAME)' in $(AWS_REGION)."; exit 1; }

destroy: ## DELETE the stack. Needs CONFIRM=1. DESTROYS SHARED INFRASTRUCTURE.
	@set -e; \
	echo "Deleting stack '$(STACK_NAME)' FROM this account:"; \
	$(AWS) sts get-caller-identity \
		--query "join('  ', [Account, Arn])" --output text \
		|| { echo "ERROR: no usable AWS credentials. Set AWS_PROFILE or refresh them."; exit 1; }; \
	echo ""; \
	echo "This DELETES the source bucket and everything in it, both IAM roles, the"; \
	echo "CodeBuild project and the pipeline. Any maintainer or CI job configured"; \
	echo "to trigger runs against this stack stops working, and re-creating it does"; \
	echo "not restore the archives or the run artifacts."; \
	echo ""; \
	echo "It does NOT touch infrastructure the integration test itself deployed."; \
	echo "Check 'make -C $(REPO_ROOT)/internal/integration-tests list-stacks' for that."; \
	if [ "$(CONFIRM)" != "1" ]; then \
		echo ""; \
		echo "DRY RUN — nothing was deleted. To delete it for real:"; \
		echo "  make destroy CONFIRM=1"; \
		exit 0; \
	fi; \
	echo ""; \
	echo "Emptying the bucket first — it is versioned, so delete-stack fails on it"; \
	echo "until every object VERSION and delete marker is gone."; \
	"$(PYTHON)" "$(HERE)empty_bucket.py" \
		--stack "$(STACK_NAME)" --region "$(AWS_REGION)" \
		$(if $(AWS_PROFILE),--profile "$(AWS_PROFILE)",); \
	echo ""; \
	$(AWS) cloudformation delete-stack --stack-name "$(STACK_NAME)"; \
	echo "Delete requested. Waiting for it to finish..."; \
	$(AWS) cloudformation wait stack-delete-complete --stack-name "$(STACK_NAME)"; \
	echo "Deleted."

# ─────────────────────────────────────────────────────────────────────────────
# A RUN's lifecycle
# ─────────────────────────────────────────────────────────────────────────────

archive: ## Build the source zip from the working tree, including .git. Free.
	@"$(PYTHON)" "$(HERE)archive.py" --repo "$(REPO_ROOT)" --out "$(ARCHIVE)"

upload: ## Upload the archive to the source key. Starts nothing.
	@set -e; \
	if [ ! -f "$(ARCHIVE)" ]; then \
		echo "No archive at $(ARCHIVE). Build it first: make archive"; exit 1; \
	fi; \
	bucket="$$($(AWS) cloudformation describe-stacks --stack-name "$(STACK_NAME)" \
		--query "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue | [0]" \
		--output text)"; \
	if [ -z "$$bucket" ] || [ "$$bucket" = "None" ]; then \
		echo "Could not read SourceBucketName from '$(STACK_NAME)'."; exit 1; \
	fi; \
	echo "Uploading $(ARCHIVE) to s3://$$bucket/$(SOURCE_OBJECT_KEY)"; \
	$(AWS) s3 cp "$(ARCHIVE)" "s3://$$bucket/$(SOURCE_OBJECT_KEY)"; \
	echo "Uploaded. Nothing started — PollForSourceChanges is false."

start: ## Start ONE pipeline execution. Needs CONFIRM=1. BILLABLE.
	@set -e; \
	echo "Starting a run in this account:"; \
	$(AWS) sts get-caller-identity \
		--query "join('  ', [Account, Arn])" --output text; \
	echo ""; \
	echo "This BILLS: LARGE build minutes, up to \$$15 of model spend, and every"; \
	echo "stack the test deploys until it is torn down."; \
	if [ "$(CONFIRM)" != "1" ]; then \
		echo ""; \
		echo "DRY RUN — nothing was started. To run it for real:"; \
		echo "  make start CONFIRM=1"; \
		exit 0; \
	fi; \
	echo ""; \
	$(AWS) codepipeline start-pipeline-execution --name "$(STACK_NAME)" \
		--query "pipelineExecutionId" --output text

# Polls the LATEST execution rather than an id threaded out of `start`, so this is
# usable on a run someone else started, and after a lost terminal.
watch: ## Poll the latest execution until it finishes
	@set -e; \
	while :; do \
		summary="$$($(AWS) codepipeline list-pipeline-executions \
			--pipeline-name "$(STACK_NAME)" --max-items 1 \
			--query "pipelineExecutionSummaries[0].[pipelineExecutionId,status]" \
			--output text)"; \
		id="$$(echo "$$summary" | awk '{print $$1}')"; \
		state="$$(echo "$$summary" | awk '{print $$2}')"; \
		echo "$$(date -u +%H:%M:%S)  $$id  $$state"; \
		case "$$state" in \
			Succeeded) exit 0 ;; \
			Failed|Cancelled|Superseded|Stopped) exit 1 ;; \
		esac; \
		sleep 30; \
	done

# ONE shell block, the four sub-makes included. This is the same trap the `deploy`
# comment above describes, and it was WRITTEN here first: with the guard on its own
# recipe line, `exit 0` left only that line's subshell and make carried on to
# `archive`, `upload`, `start CONFIRM=1` and `watch`. A dry run printed "nothing was
# done" and then started a billable run. Measured, not hypothetical — it was caught
# only because a linked worktree made `archive` fail first.
#
# So: never put a CONFIRM guard on its own recipe line in this file. The cost of
# getting it wrong here is money, not a confusing error.
trigger: ## archive + upload + start + watch. Needs CONFIRM=1. BILLABLE.
	@set -e; \
	if [ "$(CONFIRM)" != "1" ]; then \
		echo "This builds an archive, uploads it, starts a BILLABLE run and waits."; \
		echo ""; \
		echo "DRY RUN — nothing was done. To run it for real:"; \
		echo "  make trigger CONFIRM=1"; \
		exit 0; \
	fi; \
	$(MAKE) --no-print-directory archive; \
	$(MAKE) --no-print-directory upload; \
	$(MAKE) --no-print-directory start CONFIRM=1; \
	$(MAKE) --no-print-directory watch

logs: ## Tail the most recent build's CloudWatch log stream
	@set -e; \
	group="/aws/codebuild/$(STACK_NAME)-lifecycle"; \
	stream="$$($(AWS) logs describe-log-streams --log-group-name "$$group" \
		--order-by LastEventTime --descending --max-items 1 \
		--query "logStreams[0].logStreamName" --output text)"; \
	if [ -z "$$stream" ] || [ "$$stream" = "None" ]; then \
		echo "No log streams in $$group yet."; exit 1; \
	fi; \
	echo "Tailing $$group / $$stream"; \
	$(AWS) logs tail "$$group" --log-stream-names "$$stream" --follow
