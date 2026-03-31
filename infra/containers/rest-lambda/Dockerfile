FROM public.ecr.aws/docker/library/python:3.12-slim

ARG APP_VERSION=0.1.0
ARG BUILD_VERSION=unknown
ENV APP_VERSION=${APP_VERSION}
ENV BUILD_VERSION=${BUILD_VERSION}

# Lambda Web Adapter — proxies Lambda runtime API to local HTTP server.
# Harmless if not activated (requires AWS_LWA_INVOKE_MODE env var).
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0-rc1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app

# Install app-lib with api_lambda dependencies (fastapi + uvicorn)
COPY app-lib/ ./app-lib/
RUN pip install --no-cache-dir ./app-lib[api_lambda]

# Copy Lambda entry points
COPY app-lib/src/app_lib/patterns/lambda/api_lambda/ ./
COPY app-lib/src/app_lib/patterns/lambda/handler/ ./
# Default: Lambda Web Adapter mode (uvicorn on port 8080).
# Override at deploy time via CFN ImageCommand parameter for custom entrypoints.
CMD ["python", "-m", "uvicorn", "api_lambda_handler:app", "--host", "0.0.0.0", "--port", "8080"]
