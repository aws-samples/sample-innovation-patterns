# infra/containers/rest-k8s/

Container image for running the `app-lib` FastAPI service under Kubernetes
(local k3d via Tilt, or any cluster via the Helm chart at
`infra/k8s/helm/app-lib/`).

## Why a second Dockerfile

There are two REST Dockerfiles for one application library:

| | `rest-lambda/` | `rest-k8s/` (this dir) |
|---|---|---|
| Runtime | AWS Lambda (API Gateway → Lambda) | Kubernetes pod |
| Port | 8080 | 8000 |
| Adapter | AWS Lambda Web Adapter extension | none — plain uvicorn |
| Install | `./app-lib[api_lambda]` (non-editable) | `-e ./app-lib[rest]` (editable) |
| Entry | `api_lambda_handler:app` | `app_lib.common.app:app` |

The `[rest]` and `[api_lambda]` extras in `app-lib/pyproject.toml` are
**byte-identical** dependency sets (fastapi + pynamodb + PyJWT + uvicorn). The
split is purely about the **entrypoint, port, and adapter** — not dependencies.

## Do not unify the two Dockerfiles

It is tempting to collapse these into one parameterized Dockerfile. Do not:

- The Lambda image bundles the Lambda Web Adapter from a `COPY --from=...`
  stage; the k8s image must not carry it.
- The k8s image installs **editable** (`-e`) so Tilt's `live_update` can sync
  `app-lib/src/app_lib` into the running container without rebuilding. The
  Lambda image is non-editable (immutable artifact pushed to ECR).
- Keeping them separate keeps each Dockerfile readable and each runtime's
  contract explicit. This is intentional duplication, not an oversight.

## Build

The build context is `app-lib/` (where `pyproject.toml` lives), not the repo
root:

```bash
docker build -f infra/containers/rest-k8s/Dockerfile app-lib/ -t app-lib:dev
docker run --rm -p 8000:8000 app-lib:dev
curl -s localhost:8000/health   # -> {"status":"ok"}
```

Tilt builds this image with `docker_build_with_restart` (see the repo-root
`Tiltfile`); you rarely build it by hand outside of a one-off smoke test.
