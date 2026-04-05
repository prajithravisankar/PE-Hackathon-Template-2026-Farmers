# 🛡️ Reliability Engineering Quest — Local Verification Guide

## Prerequisites — Clone & Setup

```bash
# 1. Clone the repo
git clone https://github.com/prajithravisankar/PE-Hackathon-Template-2026-Farmers.git
cd PE-Hackathon-Template-2026-Farmers

# 2. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync --dev

# 4. Start PostgreSQL (pick one)
# Option A: Docker
docker run -d --name hackathon-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=hackathon_db -p 5432:5432 postgres:16

# Option B: If you have Postgres locally, just create the database:
createdb hackathon_db

# 5. Set environment variables
cp .env.example .env   # or create .env manually:
# DATABASE_NAME=hackathon_db
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_USER=postgres
# DATABASE_PASSWORD=postgres
```

---

## 🥉 Bronze — The Shield

> _Objective: Prove your code works before you ship it._

| Requirement         | What We Built                                                                                                                                                            | How to Run Locally                                                                                   | Expected Output                                                                                                                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Unit Tests**      | 12 unit tests in `tests/unit/` covering validators (`is_valid_url`, `is_valid_email`, `is_valid_username`) and short code generation (length, alphanumeric, uniqueness). | `uv run pytest tests/unit/ -v`                                                                       | All 12 tests pass ✅. No database required.                                                                                                                                                              |
| **CI Automation**   | GitHub Actions in `.github/workflows/ci.yml`. Runs on every push/PR. Spins up PostgreSQL 16 service container, runs full test suite with coverage, uploads to Codecov.   | Push any commit to any branch or open a PR to `main`. View results in the **Actions** tab on GitHub. | Green checkmark ✅ on the commit. Tests run with `--cov-fail-under=50`.                                                                                                                                  |
| **Health Endpoint** | `GET /health` in `app/__init__.py`. Checks DB (`SELECT 1`) and Redis (`r.ping()`). Returns status for each.                                                              | `uv run flask --app app:create_app run` then `curl http://localhost:5000/health`                     | `{"status": "ok", "db": "ok", "redis": "ok"}` (200). If Redis isn't running: `{"status": "ok", "db": "ok", "redis": "down"}` — still 200 since DB is up. If DB is down: 503 with `"status": "degraded"`. |

### Run it all at once

```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Start the app
uv run flask --app app:create_app run

# In another terminal, hit health
curl -s http://localhost:5000/health | python3 -m json.tool
```

---

## 🥈 Silver — The Fortress

> _Objective: Stop bad code from ever reaching production._

| Requirement                       | What We Built                                                                                                                                                                                                                                     | How to Run Locally                                                                                                         | Expected Output                                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **50% Coverage**                  | `pytest-cov` configured in `pyproject.toml`. CI runs with `--cov-fail-under=50`. Local runs enforce **70%**.                                                                                                                                      | `uv run pytest --cov=app --cov-report=term-missing`                                                                        | Coverage report printed to terminal. Current coverage: **~74%** (exceeds 50% requirement).               |
| **Integration Tests**             | 54+ integration tests in `tests/integration/` testing full API flows: Users CRUD (19 tests), URLs CRUD + redirect (15 tests), Events CRUD (7 tests), graceful failures (11 tests), health (2 tests).                                              | `uv run pytest tests/integration/ -v`                                                                                      | All integration tests pass. Each test hits real API endpoints via Flask test client → verifies DB state. |
| **Gatekeeper (CI blocks deploy)** | CI configured with `--cov-fail-under=50`. If coverage drops below 50% or any test fails, the GitHub Actions pipeline fails and the commit gets a red ❌.                                                                                          | 1. Break a test intentionally (e.g., change expected status code in a test). 2. Push to a branch. 3. Check GitHub Actions. | Red ❌ on the commit. Deploy is blocked. Screenshot this for proof.                                      |
| **Error Handling**                | JSON error responses for all HTTP errors: 404 (`{"error": "Not found"}`), 405 (`{"error": "Method not allowed"}`), 413 (`{"error": "Request too large..."}`), 500 (`{"error": "Internal server error"}`). Documented in `docs/error_handling.md`. | `curl -s http://localhost:5000/nonexistent`                                                                                | `{"error": "Not found"}` with status 404. No stack traces. Always JSON.                                  |

### Run it all at once

```bash
# Full test suite with coverage report
uv run pytest --cov=app --cov-report=term-missing -v

# Test error handling manually
uv run flask --app app:create_app run &
curl -s http://localhost:5000/does-not-exist  # 404 JSON
curl -s -X DELETE http://localhost:5000/health  # 405 JSON
curl -s -X POST http://localhost:5000/users -H "Content-Type: text/plain" -d "not json"  # 400 JSON
```

---

## 🥇 Gold — The Immortal

> _Objective: Break it on purpose. Watch it survive._

| Requirement                   | What We Built                                                                                                                                                                                                                   | How to Run Locally                                             | Expected Output                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **70% Coverage**              | Enforced locally via `pyproject.toml`: `--cov-fail-under=70`.                                                                                                                                                                   | `uv run pytest`                                                | Tests pass AND coverage ≥ 70%. Currently at **~74%**. If you drop below 70%, pytest itself fails. |
| **Graceful Failure**          | 11 dedicated tests in `tests/integration/test_graceful_failures.py`. Tests: unknown route→404 JSON, wrong method→405 JSON, non-JSON body→400, missing body→422, oversized request (2MB)→413, bad CSV→400, empty CSV→0 imported. | `uv run pytest tests/integration/test_graceful_failures.py -v` | All 11 tests pass. Every bad input returns clean JSON error, never a stack trace.                 |
| **Chaos Mode (auto-restart)** | Docker Compose with `restart: always` on all app containers. Kill it → Docker restarts it.                                                                                                                                      | See "Chaos Mode Demo" below.                                   | Container dies, Docker restarts it within seconds. Health endpoint recovers.                      |
| **Failure Manual**            | `docs/failure_modes.md` — documents what happens when DB dies, Redis dies, app crashes, disk full, etc.                                                                                                                         | `cat docs/failure_modes.md`                                    | Full document describing each failure scenario and expected behavior.                             |

### Chaos Mode Demo

```bash
# 1. Start the full stack
docker compose up -d --build

# 2. Verify everything is running
docker compose ps
curl -s http://localhost:80/health | python3 -m json.tool

# 3. Start the heartbeat monitor in one terminal
bash scripts/heartbeat.sh

# 4. In another terminal, kill a container
docker kill $(docker compose ps -q app1)

# 5. Watch heartbeat — it drops briefly, then recovers
#    Docker auto-restarts the container (restart: always)

# 6. Verify recovery
docker compose ps  # app1 should be back up
curl -s http://localhost:80/health
```

### Graceful Failure Demo

```bash
uv run flask --app app:create_app run &

# Bad inputs → clean JSON errors
curl -s -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "", "email": "not-an-email"}'
# → 422 with field-level validation errors

curl -s -X POST http://localhost:5000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "not-a-url"}'
# → 422 with "Invalid URL format"

curl -s http://localhost:5000/urls/99999
# → 404 {"error": "URL not found"}

# Oversized request
python3 -c "print('x' * 2_000_000)" | curl -s -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" -d @-
# → 413 {"error": "Request too large. Maximum size is 1 MB."}
```

---

## Hidden Reliability Score

The hidden evaluator checks broadly reward:

- Rejecting bad input with proper status codes
- Preserving data consistency (unique constraints, FK integrity)
- Enforcing uniqueness (duplicate username/email → 409)
- Handling inactive resources (deactivated short URLs → 404 on redirect)
- Correct behavior across all CRUD flows

**Our score: 29/29 hidden checks passing.**
