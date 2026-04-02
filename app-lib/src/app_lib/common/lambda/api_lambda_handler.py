"""REST Lambda entry point — Lambda Web Adapter mode.

Lambda Web Adapter runs uvicorn, which serves `app`.
Local dev:  uvicorn api_lambda_handler:app --reload --port 8080
"""

from app_lib.common.app import app  # noqa: F401
