# FastAPI — frontend serving and telemetry

## Serve a built frontend

Use `app.frontend()` for a built static app (Vite, Astro, Angular, Svelte, Vue):

```python
from fastapi import FastAPI

app = FastAPI()
app.frontend("/", directory="dist")
```

Use `router.frontend()` when the frontend belongs to a router; the router prefix
applies normally when it is included:

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()
router = APIRouter(prefix="/admin")
router.frontend("/", directory="admin-dist")
app.include_router(router)
```

These are low-priority routes: API routes match first, then files, then the
client-side routing fallback. Prefer them over mounting `StaticFiles` by hand.

In this workspace a built frontend under `dist/` is a build artifact — it is not
committed, and `register_preview` shows the dev server, not a stale `dist`.

## OpenTelemetry

Prefer FastAPI's native support for traces, metrics and logs.

- Install `fastapi[standard]` to get the SDK and the HTTP/protobuf exporters.
- `FASTAPI_OTEL_AUTO_CONFIGURE=true` enables exporter setup.
- Set `OTEL_SERVICE_NAME` for the service name and `OTEL_EXPORTER_OTLP_ENDPOINT`
  for the collector base URL; `OTEL_EXPORTER_OTLP_HEADERS` when auth is needed.
- A provider configured by another telemetry library is reused without automatic
  setup.
- `FastAPI(telemetry={...})` for custom configuration (signals, providers).

Reference: <https://fastapi.tiangolo.com/advanced/opentelemetry/>.

Secrets for the collector belong in `.env` (gitignored) with the key name
documented in `TOOLS.md`, never in the app config or the docs.
