# patterns/

Deployable pattern implementations. Each pattern is self-contained with its own routes, services, models, and handlers. Patterns are registered in `rest/app.py` via `include_router`.

## Directory Structure

```
patterns/
├── bedrock/
│   ├── kb/                          # Bedrock Knowledge Base (RAG, S3 Vectors, SSE query)
│   │   ├── routes/                  # FastAPI routers (kb_sse_routes, kb_dto)
│   │   ├── service/                 # BedrockKBService (retrieve, sync, stream)
│   │   └── util/                    # Sample data generator
│   └── agent_core/                  # Agent Core patterns (shared parent)
│       ├── service/                 # SHARED services for all agent_core sub-patterns
│       │   └── chat_memory_service.py
│       ├── chat/                    # Chat pattern (add-on to react-rest-lambda)
│       │   └── routes/              # chat_routes, chat_sse_routes, chat_dto
│       └── agent_mcp_server/        # Agent + MCP server pattern
│           ├── agents/              # Agent entrypoints and implementations
│           ├── mcp/                 # MCP server entrypoints
│           └── model/               # Pydantic models for agent responses
├── sqs/                             # SQS background processing
│   ├── routes/                      # job_routes, job_sse_routes, job_dto
│   ├── service/                     # JobDataService, SqsService
│   ├── model/                       # PynamoDB JobTable
│   └── handler/                     # SQS Lambda handler
├── lambda/
│   ├── handler/                     # Lambda handlers (REST, SQS, S3)
│   └── api_lambda/                  # FastAPI on Lambda
├── sagemaker/                       # SageMaker pipelines (train, transform)
└── streamlit/                       # Streamlit on ECS
```

## Conventions

### Where to place files

| File type | Location | Example |
|-----------|----------|---------|
| FastAPI routers | `{pattern}/routes/` | `sqs/routes/job_routes.py` |
| Pydantic DTOs | `{pattern}/routes/` | `sqs/routes/job_dto.py` |
| Service classes | `{pattern}/service/` | `bedrock/kb/service/bedrock_kb_service.py` |
| PynamoDB models | `{pattern}/model/` | `sqs/model/job_table.py` |
| Lambda handlers | `{pattern}/handler/` | `sqs/handler/sqs_handler.py` |
| Agent entrypoints | `{pattern}/agents/` | `bedrock/agent_core/agent_mcp_server/agents/` |

### Shared services within a pattern family

When multiple sub-patterns share a service, place it at the common parent level:

```
bedrock/agent_core/
├── service/                 # Shared by chat/ and agent_mcp_server/
│   └── chat_memory_service.py
├── chat/                    # Sub-pattern A
└── agent_mcp_server/        # Sub-pattern B
```

Import: `from app_lib.patterns.bedrock.agent_core.service.chat_memory_service import ChatMemoryService`

### Registering routes in app.py

Add-on patterns register their routers in `rest/app.py` with a comment identifying the pattern:

```python
from app_lib.patterns.sqs.routes.job_routes import job_router
app.include_router(job_router)  # SQS pattern
```

To disconnect a pattern, remove its import and `include_router` call.

### Self-contained patterns

Each pattern should be removable by:
1. Deleting its directory under `patterns/`
2. Removing its `include_router` lines from `app.py`
3. Deleting its CloudFormation stacks

No other code should break.
