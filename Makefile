# Local Development
# Start the full stack: make dev
# Backend only:        make dev-backend
# Frontend only:       make dev-frontend
#
# Lint & format (run before commit/push):
# Everything:          make lint        (auto-fixes app-lib, web-client, infra)
# Check only (no fix): make lint-check  (CI-style; fails on issues)
# Per project:         make -f infra/scripts/lint.mk lint-app-lib | lint-web-client | lint-infra

.PHONY: dev dev-backend dev-frontend lint lint-check \
	doctor local-setup local-up local-destroy local-reset

# FastAPI backend with auto-reload (uv run finds the .venv automatically)
dev-backend:
	cd app-lib && uv run uvicorn app_lib.common.app:app --reload --port 8000

# Vite dev server (proxies /api to backend)
dev-frontend:
	cd web-client && npm run dev

# Lint & format — see infra/scripts/lint.mk for per-project targets.
# `make lint` auto-fixes app-lib, web-client, and infra; `make lint-check`
# is the CI-style read-only variant. Both delegate to lint.mk.
lint:
	@$(MAKE) -f infra/scripts/lint.mk lint

lint-check:
	@$(MAKE) -f infra/scripts/lint.mk lint-check

# ---------------------------------------------------------------------------
# Local Kubernetes inner-dev loop (k3d + Helm + Tilt)
#
# Turnkey:   make local-setup   # check tools, create k3d cluster + registry
#            make local-up       # build + deploy via Tilt, port-forward :8000
#            make local-destroy  # tear down Tilt + the k3d cluster
#            make local-reset    # destroy then setup + up (fresh loop)
#            make doctor         # check required tools; print install commands
#
# The pod consumes a REAL deployed DynamoDB table using your host ~/.aws creds
# (split-plane model). The data plane is stood up by /ipa-deploy; only the
# compute plane runs locally. See docs/guides/kubernetes-local-development.md.
# ---------------------------------------------------------------------------

CTLPTL_CLUSTER := infra/k8s/envs/local-tilt/ctlptl-cluster.yaml
K3D_CLUSTER_NAME := k3d-ipa-local

# doctor — verify the six required CLIs (plus aws) are installed. Prints the
# exact install command for each missing tool and FAILS FAST. Never installs
# anything and never creates a partial cluster.
doctor:
	@missing=0; \
	check() { \
	  if command -v $$1 >/dev/null 2>&1; then \
	    printf '  ✓ %s\n' "$$1"; \
	  else \
	    printf '  ✗ %s MISSING — install: %s\n' "$$1" "$$2"; \
	    missing=1; \
	  fi; \
	}; \
	echo "Checking required tools for the local k8s loop:"; \
	check docker  "https://docs.docker.com/get-docker/"; \
	check kubectl "brew install kubectl  (or https://kubernetes.io/docs/tasks/tools/)"; \
	check helm    "brew install helm  (or https://helm.sh/docs/intro/install/)"; \
	check k3d     "brew install k3d  (or https://k3d.io/#installation)"; \
	check tilt    "brew install tilt-dev/tap/tilt  (or https://docs.tilt.dev/install.html)"; \
	check ctlptl  "brew install tilt-dev/tap/ctlptl  (or https://github.com/tilt-dev/ctlptl#how-do-i-install-it)"; \
	check aws     "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"; \
	if [ "$$missing" -ne 0 ]; then \
	  echo "ERROR: install the tool(s) above, then re-run. No cluster was created."; \
	  exit 1; \
	fi; \
	echo "All required tools present."

# local-setup — doctor first (Q2.A), then reconcile the k3d cluster + registry.
# ctlptl apply is idempotent: safe to re-run.
local-setup: doctor
	ctlptl apply -f $(CTLPTL_CLUSTER)

# local-up — guard that kubectl is pointed at the local cluster, then hand off
# to Tilt. Tilt builds the image, deploys the chart, port-forwards :8000, and
# verifies AWS creds before the pod starts.
local-up:
	@ctx=$$(kubectl config current-context 2>/dev/null || true); \
	case "$$ctx" in \
	  *$(K3D_CLUSTER_NAME)*) : ;; \
	  *) echo "ERROR: kubectl context is '$$ctx', not the local k3d cluster."; \
	     echo "Run 'make local-setup' first, or: kubectl config use-context k3d-$(K3D_CLUSTER_NAME)"; \
	     exit 1 ;; \
	esac
	tilt up

# local-destroy — stop Tilt and delete the k3d cluster + registry.
local-destroy:
	-tilt down
	-ctlptl delete -f $(CTLPTL_CLUSTER)

# local-reset — full fresh loop.
local-reset: local-destroy local-setup local-up
