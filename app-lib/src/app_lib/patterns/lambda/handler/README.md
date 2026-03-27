# Handler-Based Lambda Pattern

A simple `handler(event, context)` Lambda entry point. No web framework — just a function wrapped in a minimal HTTP server.

## How It Works

This handler is deployed using the same ECR image as the REST Lambda (`infra/containers/rest-lambda/Dockerfile`). At deploy time, the CloudFormation template overrides the container CMD via `ImageConfig.Command` to run `python -m lambda_handler` instead of the default uvicorn entrypoint. The Lambda Web Adapter POSTs each Lambda event as JSON to the handler's HTTP server on port 8080.

The handler module includes a minimal `http.server` that receives the POST, calls `handler(event)`, and returns the result as JSON.

## Customization

Edit the `handler()` function in `lambda_handler.py` with your logic. The handler has access to all `app-lib` services since the full library is installed in the image. The HTTP server boilerplate at the bottom of the file should not need changes.

## Deploy

```python
deploy_handler_lambda(
    stack_name="my-handler",
    function_name="my-handler-fn",
    image_uri=image_uri,  # from build_rest_lambda_image
    region="us-east-1",
)
```
