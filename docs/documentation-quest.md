# 📜 Documentation Quest — Local Verification Guide

## Prerequisites — Clone & Setup

```bash
git clone https://github.com/prajithravisankar/PE-Hackathon-Template-2026-Farmers.git
cd PE-Hackathon-Template-2026-Farmers
```

---

## 🥉 Bronze — The Map

> _Objective: Setup instructions, architecture, API docs._

| Requirement              | What We Built                                                                                                                                                   | How to Verify                                                                          | Location                                       |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **README**               | Full setup instructions: clone, install `uv`, install deps, start PostgreSQL (Docker or local), set env vars, run app, run tests. Clear enough for a freshman.  | `cat README.md` — follow the instructions from scratch and verify you can run the app. | `README.md`                                    |
| **Architecture Diagram** | ASCII/text architecture diagram showing: Client → Nginx → App1/App2 → PostgreSQL/Redis, plus Prometheus → Grafana → Alertmanager → Discord monitoring pipeline. | See the diagram in `docs/incident-response-quest.md` (bottom) or in the README.        | `README.md`, `docs/incident-response-quest.md` |
| **API Docs**             | Complete endpoint reference for all 3 blueprints + built-in routes. Every endpoint listed with method, path, description, request body, and response format.    | `cat docs/api_decision_log.md` or see table below.                                     | `docs/api_decision_log.md`                     |

### Complete API Reference

| Method     | Path                | Description          | Request Body                                        | Response                                           |
| ---------- | ------------------- | -------------------- | --------------------------------------------------- | -------------------------------------------------- |
| `GET`      | `/health`           | Health check         | —                                                   | `{"status": "ok", "db": "ok", "redis": "ok"}`      |
| `GET`      | `/metrics`          | Prometheus metrics   | —                                                   | Prometheus text format                             |
| **Users**  |                     |                      |                                                     |                                                    |
| `GET`      | `/users`            | List users           | —                                                   | `[{"id", "username", "email", "created_at"}]`      |
| `GET`      | `/users/<id>`       | Get user             | —                                                   | `{"id", "username", "email", "created_at"}`        |
| `POST`     | `/users`            | Create user          | `{"username", "email"}`                             | 201 Created                                        |
| `PUT`      | `/users/<id>`       | Update user          | `{"username", "email"}`                             | 200 OK                                             |
| `DELETE`   | `/users/<id>`       | Delete user          | —                                                   | 204 No Content                                     |
| `POST`     | `/users/bulk`       | CSV bulk import      | multipart `file` field                              | `{"imported": N, "errors": [...]}`                 |
| **URLs**   |                     |                      |                                                     |                                                    |
| `POST`     | `/urls`             | Create short URL     | `{"original_url", "user_id?", "title?"}`            | 201 Created with `short_code`                      |
| `GET`      | `/urls`             | List URLs            | —                                                   | `[{"id", "short_code", "original_url", ...}]`      |
| `GET`      | `/urls/<id>`        | Get URL              | —                                                   | `{"id", "short_code", "original_url", ...}`        |
| `PUT`      | `/urls/<id>`        | Update URL           | `{"original_url?", "title?", "is_active?"}`         | 200 OK                                             |
| `DELETE`   | `/urls/<id>`        | Delete URL           | —                                                   | 204 No Content                                     |
| `GET`      | `/urls/<id>/stats`  | URL statistics       | —                                                   | `{"total_events", "total_clicks", "last_visited"}` |
| `GET`      | `/urls/<id>/events` | Events for URL       | —                                                   | `[{"id", "event_type", "timestamp", ...}]`         |
| `GET`      | `/<short_code>`     | Redirect             | —                                                   | 302 redirect to original URL                       |
| **Events** |                     |                      |                                                     |                                                    |
| `GET`      | `/events`           | List events          | —                                                   | `[{"id", "event_type", "timestamp", ...}]`         |
| `POST`     | `/events`           | Create event         | `{"url_id?", "user_id?", "event_type", "details?"}` | 201 Created                                        |
| `GET`      | `/events/<id>`      | Get event            | —                                                   | `{"id", "event_type", "timestamp", ...}`           |
| `PUT`      | `/events/<id>`      | Update event         | `{"event_type?", "details?"}`                       | 200 OK                                             |
| `PATCH`    | `/events/<id>`      | Update event (alias) | `{"event_type?", "details?"}`                       | 200 OK                                             |
| `DELETE`   | `/events/<id>`      | Delete event         | —                                                   | 204 No Content                                     |

---

## 🥈 Silver — The Manual

> _Objective: Deploy guide, troubleshooting, config._

| Requirement               | What We Built                                                                                                                                                                     | How to Verify                                           | Location                                      |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------- |
| **Deploy Guide**          | Local: `docker compose up -d --build`. Cloud: DigitalOcean App Platform with auto-deploy on push to `main`. Rollback: `git revert` + push, or Actions → Rollback in DO dashboard. | Follow the guide to deploy locally with Docker Compose. | `docs/scalability-quest.md` (Docker sections) |
| **Troubleshooting**       | `docs/common_bugs.md` — real bugs encountered during development with solutions. Covers: DB permission errors, uv.lock missing, SSL issues, coverage failures, etc.               | `cat docs/common_bugs.md`                               | `docs/common_bugs.md`                         |
| **Environment Variables** | Full list of all env vars below.                                                                                                                                                  | Verify each var is documented with default values.      | See table below, `.env.example`               |

### Environment Variables

| Variable            | Required | Default                    | Description                                                                           |
| ------------------- | -------- | -------------------------- | ------------------------------------------------------------------------------------- |
| `DATABASE_URL`      | No\*     | —                          | Full PostgreSQL connection string (overrides individual vars). Used for DigitalOcean. |
| `DATABASE_NAME`     | No       | `hackathon_db`             | PostgreSQL database name                                                              |
| `DATABASE_HOST`     | No       | `localhost`                | PostgreSQL host                                                                       |
| `DATABASE_PORT`     | No       | `5432`                     | PostgreSQL port                                                                       |
| `DATABASE_USER`     | No       | `postgres`                 | PostgreSQL username                                                                   |
| `DATABASE_PASSWORD` | No       | `postgres`                 | PostgreSQL password                                                                   |
| `DATABASE_SSLMODE`  | No       | —                          | SSL mode for database connection (`require`, `disable`, etc.)                         |
| `REDIS_URL`         | No       | `redis://localhost:6379/0` | Redis connection URL                                                                  |
| `FLASK_DEBUG`       | No       | `false`                    | Enable Flask debug mode (never `true` in production)                                  |

_If `DATABASE_URL` is set, the individual `DATABASE\__` vars are ignored.

### Local Deploy (Docker Compose)

```bash
# Full stack (2 app instances + LB + monitoring)
docker compose up -d --build

# Simple stack (1 app instance + DB + Redis)
docker compose -f docker-compose.app.yml up -d --build

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

### Rollback Procedures

```bash
# Local rollback
git log --oneline -5          # find the good commit
git revert HEAD               # revert last commit
docker compose up -d --build  # redeploy

# DigitalOcean rollback
# Option A: Actions → Rollback in dashboard
# Option B: git revert + push to main (auto-deploys)
```

---

## 🥇 Gold — The Codex

> _Objective: Runbooks, decision logs, capacity plan._

| Requirement       | What We Built                                                                                                                                        | How to Verify               | Location                |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ----------------------- |
| **Runbooks**      | Step-by-step emergency guides for each alert type: ServiceDown, HighErrorRate, HighLatency, DB failure, Redis failure. Written for 3 AM readability. | `cat docs/runbook.md`       | `docs/runbook.md`       |
| **Decision Log**  | 7 decision log documents covering every major technical choice.                                                                                      | See table below.            | `docs/` directory       |
| **Capacity Plan** | Analysis of max users, bottleneck identification, scaling recommendations.                                                                           | `cat docs/capacity_plan.md` | `docs/capacity_plan.md` |

### Decision Logs

| Document                             | Key Decisions Documented                                                      |
| ------------------------------------ | ----------------------------------------------------------------------------- |
| `docs/api_decision_log.md`           | REST design, endpoint naming, pagination, response format                     |
| `docs/schema_decision_log.md`        | Peewee ORM, table structure, FK relationships, CASCADE vs SET NULL            |
| `docs/testing_decision_log.md`       | pytest, factory-boy, coverage thresholds (70% local / 50% CI), test isolation |
| `docs/observability_decision_log.md` | Prometheus + Grafana, structured JSON logging, golden signals                 |
| `docs/alerting_decision_log.md`      | Alert thresholds, Discord webhook, Alertmanager config                        |
| `docs/chaos_reliability_decision.md` | Docker restart policies, graceful degradation, Redis optional                 |
| `docs/error_handling.md`             | JSON error responses, validation strategy, status code mapping                |

### Additional Documentation

| Document                             | Purpose                                            |
| ------------------------------------ | -------------------------------------------------- |
| `docs/failure_modes.md`              | What happens when each component fails             |
| `docs/capacity_plan.md`              | How many users we can handle, where the limits are |
| `docs/runbook.md`                    | Emergency response procedures for each alert       |
| `docs/common_bugs.md`                | Bugs encountered and their fixes                   |
| `docs/chaos_demo_recording_guide.md` | How to record the chaos engineering demo           |

### Verify All Docs Exist

```bash
ls -la docs/
# Should show 13+ markdown files covering all quest documentation requirements
```

---

## Summary: All Quest Docs

| Quest             | Doc File                          | What It Covers                                        |
| ----------------- | --------------------------------- | ----------------------------------------------------- |
| Reliability       | `docs/reliability-quest.md`       | Tests, CI, health checks, error handling, chaos mode  |
| Scalability       | `docs/scalability-quest.md`       | Load tests, Docker Compose, Nginx LB, Redis caching   |
| Incident Response | `docs/incident-response-quest.md` | Logging, metrics, alerts, Grafana dashboard           |
| Documentation     | `docs/documentation-quest.md`     | API docs, env vars, deploy guide, runbooks, decisions |
