# scripts/util/docker.mk — Docker/ECR build helpers
# Included by scripts/build.mk for container build targets
#
# Required variables (from .env):
#   AWS_ACCOUNT_ID, AWS_REGION, APP_NAMESPACE, APP_ENV

ECR_REGISTRY = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

# Authenticate Docker to ECR
define ecr-login
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin $(ECR_REGISTRY)
endef

# Build, tag, and push a container image
# $(1) = image tag (e.g., myapp-dev-lambda)
# $(2) = Dockerfile path (default: Dockerfile)
# $(3) = build context (default: .)
# $(4) = ECR repo URI
define docker-build-push
	docker build \
		-t $(1) \
		-f $(or $(2),Dockerfile) \
		--platform linux/amd64 \
		$(or $(3),.)
	docker tag $(1) $(4):$(1)
	docker push $(4):$(1)
endef
