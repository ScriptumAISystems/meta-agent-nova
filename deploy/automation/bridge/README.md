# LangChain ↔︎ n8n Bridge Skeleton

This service exposes a hardened FastAPI layer that proxies workflow events
from LangChain agents into the n8n automation stack. It ships with request
signature verification, Basic Auth forwarding and a minimal workflow catalog.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns basic metadata about the bridge configuration. |
| `POST` | `/workflows/summary-refresh` | Proxies summary refresh events towards the n8n webhook. |
| `POST` | `/workflows/finetune-status` | Emits finetuning status updates to n8n for downstream notifications. |

All POST requests must include an `X-Nova-Signature` header containing an
HMAC-SHA256 digest of the raw request body. The shared secret is defined via
`NOVA_BRIDGE_TOKEN`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `N8N_WEBHOOK_URL` | `http://n8n:5678/webhook` | Base webhook endpoint that receives forwarded payloads. |
| `N8N_WEBHOOK_USER` | `admin` | Basic Auth username passed to n8n. |
| `N8N_WEBHOOK_PASSWORD` | `change_me` | Basic Auth password. |
| `NOVA_BRIDGE_TOKEN` | `nova-dev-secret` | HMAC token used to validate incoming requests. |
| `NOVA_BRIDGE_TIMEOUT` | `10` | Timeout (seconds) for outgoing webhook calls. |

## Local development

```bash
docker compose \
  -f deploy/automation/n8n/docker-compose.yml \
  -f deploy/automation/bridge/docker-compose.override.yml \
  up --build
```

The bridge will be available on `http://localhost:8080`. Update `NOVA_BRIDGE_TOKEN`
in your client calls to match the token used inside the container (defaults to
`nova-dev-secret`).
