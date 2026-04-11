---
title: Quickstart
sidebar_position: 2
---

# Quickstart

Go from fresh clone to running backend + frontend in under 5 minutes.

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.12 | `python3 --version` |
| uv | latest | `uv --version` (or use pip — see below) |
| Node.js | 22+ | `node --version` |
| npm | (bundled with Node) | `npm --version` |
| AWS CLI | v2 | `aws --version` (optional — needed for backend features) |

New to the project? See [Installation](installation.md) for detailed setup instructions.

## Quick Start

```bash
# 1. Install backend dependencies
cd app-lib && uv sync --all-extras && cd ..

# 2. Install frontend dependencies
cd web-client && npm install && cd ..

# 3. Start both services
make dev
```

That's it. The backend starts on **:8000** and the frontend on **:8080**.

- **Frontend:** [http://localhost:8080](http://localhost:8080)
- **Backend API docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)

Press **Ctrl+C** to stop both services.

:::tip No pip? No uv?
If you don't have `uv`, install backend deps with pip instead:
```bash
cd app-lib && pip install -e ".[all]" && cd ..
```
:::

## Development Modes

| Mode | Command | What it starts | AWS needed? |
|------|---------|----------------|-------------|
| **Full stack** | `make dev` | Backend (:8000) + Frontend (:8080) | Yes (for DynamoDB, Bedrock, SQS) |
| **Backend only** | `make dev-backend` | Backend (:8000) with Swagger UI | Yes |
| **Frontend only** | `make dev-frontend` | Frontend (:8080) | No (API calls fail gracefully) |
| **Full stack + auth** | `make dev` + `config.local.js` | Both + Cognito OIDC | Yes |

**Frontend-only mode** is useful when you're working on UI and don't need live API responses. The frontend will load but API calls will fail with connection errors — that's expected.

### Enabling Auth Locally

Auth is disabled by default. To test with Cognito:

1. Create `web-client/public/config.local.js`:
   ```javascript
   window.__CONFIG__ = {
     ...window.__CONFIG__,
     OIDC_AUTHORITY: "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXX",
     OIDC_CLIENT_ID: "your-client-id",
   };
   ```
2. Set `AUTH_ENABLED=true` in your `.env` (or export it before starting the backend)
3. Restart both services

The `config.local.js` file is gitignored and only loaded on localhost.

## OpenAPI Codegen

When backend routes change, regenerate the typed API client:

```bash
cd web-client && npm run codegen
```

This fetches the OpenAPI schema from `http://localhost:8000/openapi.json` and generates `src/services/api/generated.ts`. The backend must be running. The generated file is committed — run codegen deliberately, not on every build.

## Environment Variables

The backend loads environment from the project root `.env` via python-dotenv. Key variables for local dev:

| Variable | Default | Purpose |
|----------|---------|---------|
| `AUTH_ENABLED` | `false` | Enable JWT validation (disable for local dev) |
| `CORS_ALLOWED_ORIGINS` | `*` | Allowed CORS origins |
| `APP_NAMESPACE` | `""` | DynamoDB table name prefix |
| `APP_ENV` | `dev` | Environment segment in table names |
| `AWS_PROFILE` | (none) | AWS CLI profile for DynamoDB/Bedrock/SQS access |
| `APP_REGION` | `us-east-1` | AWS region for Bedrock calls |
| `SQS_QUEUE_URL` | (none) | Queue URL for background jobs |

Without AWS credentials, the server starts but features that access DynamoDB, Bedrock, or SQS will return errors. The `/health`, `/version`, `/docs`, and `/openapi.json` endpoints always work.

## Ports

| Service | Port | Notes |
|---------|------|-------|
| FastAPI backend | 8000 | Swagger UI at `/docs` |
| Vite frontend | 8080 | Proxies `/api` → `:8000` |
| Docusaurus docs | 3001 | `cd docs && npm start` |

## Troubleshooting

### "Module not found" when starting the backend

Install backend dependencies: `cd app-lib && uv sync --all-extras` (or `pip install -e ".[all]"`).

### "Python 3.12 required"

The backend requires Python >=3.12,<3.13. Check with `python3 --version`. Use pyenv to install: `pyenv install 3.12`.

### Port already in use

Another process is using port 8000 or 8080. Find and stop it:
```bash
lsof -i :8000   # Find what's using port 8000
lsof -i :8080   # Find what's using port 8080
```

### API calls failing in the frontend

Make sure the backend is running on port 8000. The Vite dev server proxies `/api` requests to `http://localhost:8000`. If the backend is down, you'll see connection errors in the browser console.

### DynamoDB / Bedrock / SQS errors

These features require AWS credentials. Set `AWS_PROFILE` in your `.env` or configure the default credential chain via `aws configure`.
