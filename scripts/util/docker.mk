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
# $(1) = local image name (e.g., myapp-dev-fn)
# $(2) = Dockerfile path (default: Dockerfile)
# $(3) = build context (default: .)
# $(4) = ECR repo URI (e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp-dev-ecr)
# $(5) = version tag (e.g., 0.1.0-abc1234)
# $(6) = APP_VERSION build arg (e.g., 0.1.0)
# $(7) = BUILD_VERSION build arg (e.g., abc1234)
define docker-build-push
	docker build \
		-t $(1) \
		-f $(or $(2),Dockerfile) \
		--platform linux/amd64 \
		--provenance=false \
		--build-arg APP_VERSION=$(6) \
		--build-arg BUILD_VERSION=$(7) \
		$(or $(3),.)
	docker tag $(1) $(4):$(5)
	docker tag $(1) $(4):latest
	docker push $(4):$(5)
	docker push $(4):latest
endef
