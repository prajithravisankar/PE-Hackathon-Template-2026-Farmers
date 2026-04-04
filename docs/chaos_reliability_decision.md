# Phase 3.3 — Reliability Quest Gold: Decision Log

> How we made the app survive chaos and why each choice was made.

---

## ADR-1: Why raise coverage to 70% (not 90%+)?

**Context:** Bronze established 87% coverage with 46 tests. Gold requires ≥70% as the CI enforcement threshold.

**Decision:** Set `--cov-fail-under=70` in `pyproject.toml`. We focused new tests on untested code paths (error branches, edge cases) rather than chasing 100%.

**Consequence:** CI blocks PRs that drop below 70%. The remaining uncovered lines are mostly defensive fallbacks (generic IntegrityError catch-all, JSON decode fallback in events) — code that's hard to trigger in normal operation but still protected by the global 500 handler.

---

## ADR-2: Why a 1 MB content length limit?

**Context:** Without a size limit, a malicious or buggy client can send a multi-gigabyte request and exhaust server memory.

**Decision:** Set `MAX_CONTENT_LENGTH = 1 * 1024 * 1024` in the Flask app config. Flask rejects oversized requests at the WSGI layer before route code runs. Added a `@app.errorhandler(413)` to return JSON instead of the default HTML.

**Consequence:** Any request body over 1 MB gets an immediate `413 Request Too Large` JSON response. Normal API payloads (JSON objects, CSV uploads with thousands of rows) are well under this limit.

---

## ADR-3: Why `restart: always`?

**Context:** We need Docker to restart crashed containers automatically for the chaos demo. Docker offers three restart policies:

- `always` — restart unconditionally whenever the container exits
- `on-failure` — only restarts on non-zero exit codes
- `unless-stopped` — restarts on crash but respects manual stops

**Decision:** `restart: always` on both `app` and `db` services. This gives the strongest self-healing guarantee.

**Consequence:** If the app process crashes (OOM, uncaught exception, SIGKILL), Docker restarts it automatically. To truly stop the stack, use `docker compose -f docker-compose.app.yml down`.

**Caveat:** Docker Desktop for Mac doesn't reliably honor restart policies after `docker kill`. On Linux (production, CI), it works as expected. For a live hackathon demo on Mac, use `docker compose up -d` to demonstrate recovery after a `docker compose stop app`.

---

## ADR-4: Why a separate `docker-compose.app.yml`?

**Context:** The existing `docker-compose.yml` runs only infrastructure (postgres, redis) for local development. The chaos demo needs the Flask app containerized too.

**Decision:** Created `docker-compose.app.yml` as a standalone file for the full app stack. It includes the app service (built from our Dockerfile), postgres with health checks, and a named volume for data persistence.

**Consequence:** Two clear environments:

- `docker-compose.yml` — dev mode (run Flask locally with `uv run run.py`, DB in Docker)
- `docker-compose.app.yml` — production-like mode (everything in Docker, used for chaos demo)

---

## ADR-5: Why multi-stage isn't needed in the Dockerfile?

**Context:** Multi-stage Docker builds reduce image size by separating build and runtime layers. Common in compiled languages (Go, Rust, Java).

**Decision:** Single-stage build with `python:3.13-slim`. We copy `uv` from its official image, install deps with `uv sync --no-dev --frozen`, and copy the app.

**Consequence:** Simple, fast builds. The `--no-dev` flag excludes test dependencies. `--frozen` ensures the lockfile isn't modified during build (reproducible). The slim base image keeps the final size reasonable (~200 MB).

---

## Graceful Failure Checklist

Every error the API can return is JSON. Here's the full set:

| Status | When                               | Response body                            |
| ------ | ---------------------------------- | ---------------------------------------- |
| 400    | Missing or non-JSON request body   | `{"error": "Request body must be JSON"}` |
| 404    | Resource not found / unknown route | `{"error": "... not found"}`             |
| 405    | Wrong HTTP method                  | `{"error": "Method not allowed"}`        |
| 409    | Duplicate username/email           | `{"error": "Username already exists"}`   |
| 410    | Deactivated short URL redirect     | `{"error": "URL is deactivated"}`        |
| 413    | Request body > 1 MB                | `{"error": "Request too large..."}`      |
| 422    | Field validation failed            | `{"error": "...", "details": {...}}`     |
| 500    | Unhandled exception (last resort)  | `{"error": "Internal server error"}`     |

---

## Files Changed in This Phase

| File                                          | Change                                                |
| --------------------------------------------- | ----------------------------------------------------- |
| `pyproject.toml`                              | `--cov-fail-under` bumped from 50 → 70                |
| `app/__init__.py`                             | Added `MAX_CONTENT_LENGTH`, 413 error handler         |
| `run.py`                                      | Reads `FLASK_RUN_HOST` and `FLASK_DEBUG` from env     |
| `Dockerfile`                                  | New — single-stage build with uv                      |
| `docker-compose.app.yml`                      | New — full app stack with restart policies, port 5001 |
| `tests/integration/test_graceful_failures.py` | New — 13 edge-case tests                              |
| `tests/integration/test_users.py`             | Added 5 tests (GET success, PUT validation/dupe)      |
| `tests/integration/test_urls.py`              | Added 5 tests (redirect, PUT edge cases)              |
| `tests/integration/test_events.py`            | Added 2 tests (url_id/user_id filters)                |
| `docs/failure_modes.md`                       | New — 6 documented failure modes with recovery steps  |
