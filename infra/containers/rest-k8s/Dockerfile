# REST API container for Kubernetes (plain uvicorn on :8000).
#
# Counterpart to ../rest-lambda/Dockerfile. Same app-lib code, different
# runtime contract:
#   - rest-lambda → port 8080, ships the AWS Lambda Web Adapter (API Gateway/Lambda)
#   - rest-k8s    → port 8000, plain uvicorn (k3d/Helm/EKS)
# See CLAUDE.md for why these are kept as two Dockerfiles, not one.
#
# Build context MUST be app-lib/ (the directory that holds pyproject.toml):
#   docker build -f infra/containers/rest-k8s/Dockerfile app-lib/ -t app-lib:dev
FROM public.ecr.aws/docker/library/python:3.12-slim

ARG APP_VERSION=0.1.0
ARG BUILD_VERSION=unknown
ENV APP_VERSION=${APP_VERSION}
ENV BUILD_VERSION=${BUILD_VERSION}

WORKDIR /app

# Editable install so Tilt live-update can sync source into /app/app-lib/src
# and uvicorn --reload picks it up without a full image rebuild.
# The [rest] extra (fastapi + pynamodb + PyJWT + uvicorn) is byte-identical to
# [api_lambda]; see CLAUDE.md.
# Build context is app-lib/, so "." is the app-lib package root.
COPY . ./app-lib/
RUN pip install --no-cache-dir -e ./app-lib[rest]

# Plain uvicorn entrypoint on :8000. The chart names this container port "http".
CMD ["python", "-m", "uvicorn", "app_lib.common.app:app", "--host", "0.0.0.0", "--port", "8000"]
