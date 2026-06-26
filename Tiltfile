# Tiltfile — local k3d inner-dev loop for the app-lib FastAPI service.
#
# Driven by `make local-up` (which runs `tilt up`). Builds the rest-k8s image,
# deploys the Helm chart with the local-tilt overlay, port-forwards :8000, and
# gates the pod on a live AWS credential check.
#
# Split-plane model: the DynamoDB data plane is deployed in AWS by /ipa-deploy;
# only this compute plane runs locally. The two converge on the SAME table name
# because the T1 trio below is injected from the repo-root .env — the same file
# /ipa-init and /ipa-deploy treat as the source of truth.

load('ext://restart_process', 'docker_build_with_restart')
load('ext://dotenv', 'dotenv')

# Read repo-root .env so APP_NAMESPACE/APP_ENV/AWS_REGION are in os.environ.
# This is the SAME .env the backend tier was deployed with — table-name
# convergence depends on it.
dotenv()

ns = os.getenv('APP_NAMESPACE', '')
env = os.getenv('APP_ENV', 'dev')
region = os.getenv('AWS_REGION', '')

if not ns or not region:
    fail("APP_NAMESPACE and AWS_REGION must be set in the repo-root .env. " +
         "Run /ipa-init (or copy .env.example) before `make local-up`.")

# Build the rest-k8s image (uvicorn:8000). docker_build_with_restart live-syncs
# app-lib source and restarts uvicorn in place — no full rebuild on edit.
docker_build_with_restart(
    'app-lib',
    'app-lib',
    dockerfile='infra/containers/rest-k8s/Dockerfile',
    live_update=[
        # A pyproject change alters dependencies — fall back to a full rebuild.
        # fall_back_on steps must appear first in the live_update list.
        fall_back_on(['app-lib/pyproject.toml']),
        sync('app-lib/src/app_lib', '/app/app-lib/src/app_lib'),
    ],
    entrypoint='python -m uvicorn app_lib.common.app:app --host 0.0.0.0 --port 8000',
)

# Deploy the chart with the local overlay, injecting the T1 convergence trio
# from .env. Both AWS_REGION and APP_REGION are set (Risk #9: app-lib / boto3
# read AWS_REGION; some code paths read APP_REGION — set both so the pod and
# the SDK agree on region no matter which is consulted).
k8s_yaml(helm(
    'infra/k8s/helm/app-lib',
    name='app-lib',
    values=['infra/k8s/envs/local-tilt/values.yaml'],
    set=[
        'env.APP_NAMESPACE=%s' % ns,
        'env.APP_ENV=%s' % env,
        'env.AWS_REGION=%s' % region,
        'env.APP_REGION=%s' % region,
    ],
))

# Credential gate: verify the developer's AWS session is live BEFORE the pod
# starts, so it never comes up with dead credentials and fails opaquely on the
# first DynamoDB call. Goes red on expired/absent creds.
local_resource(
    'aws-check-creds',
    'aws sts get-caller-identity',
    deps=[],
    labels=['aws'],
)

# Manual-trigger helper to refresh an expired SSO session without leaving Tilt.
local_resource(
    'aws-sso-login',
    'aws sso login',
    trigger_mode=TRIGGER_MODE_MANUAL,
    auto_init=False,
    deps=[],
    labels=['aws'],
)

# The app waits for the credential check to pass.
k8s_resource(
    'app-lib',
    port_forwards='8000:8000',
    resource_deps=['aws-check-creds'],
)
