# Failure Mode Document

> How each known failure manifests, how we detect it, and how to recover.
> Written so anyone can diagnose issues at 3 AM with zero prior context.

---

## Quick Reference

| ID     | Failure                     | Symptom                          | Recovery     |
| ------ | --------------------------- | -------------------------------- | ------------ |
| FM-001 | Database connection lost    | All endpoints return 500         | Auto-restart |
| FM-002 | Duplicate key violation     | POST returns 409 (or 500 if bug) | Automatic    |
| FM-003 | Invalid input crashes route | POST returns 500 HTML traceback  | Automatic    |
| FM-004 | Short code collision        | POST /urls returns 500           | Automatic    |
| FM-005 | Request body too large      | POST returns 413                 | Automatic    |
| FM-006 | App container crashes       | Connection refused on port 5000  | Auto-restart |

---

## FM-001: Database Connection Failure

**What happens:** The app cannot reach PostgreSQL. Every API endpoint returns HTTP 500 because all routes query the database.

**How you'll see it:**

```
$ curl http://localhost:5000/users
{"error": "Internal server error"}
```

The `/health` endpoint also returns 500 (it queries no data but needs an active DB connection via the `before_request` hook).

**Root causes:**

- PostgreSQL container stopped or crashed
- Network partition between app and DB containers
- Wrong `DATABASE_HOST` or `DATABASE_PORT` environment variable

**How to fix it:**

1. Check if the DB container is running: `docker ps | grep db`
2. If it's not running: `docker-compose -f docker-compose.app.yml up -d db`
3. If it is running, check connectivity: `docker exec <db_container> pg_isready -U postgres`
4. Check app logs for the exact error: `docker logs <app_container> --tail 20`

**Built-in protection:** The `docker-compose.app.yml` uses `restart: always` on both the app and DB containers. If either crashes, Docker restarts it automatically.

> **Note for Mac users:** Docker Desktop for Mac doesn't reliably honor restart policies after `docker kill`. On Linux (production, CI runners), it works as expected. For a live demo on Mac, use `docker compose -f docker-compose.app.yml up -d` to recover after a `docker compose stop app`.

---

## FM-002: Duplicate Key Constraint Violation

**What happens:** Someone tries to create a user with a `username` or `email` that already exists in the database. Peewee raises an `IntegrityError`.

**How you'll see it:**

```
$ curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "existinguser", "email": "new@example.com"}'
{"error": "Username already exists"}   # HTTP 409
```

**Root cause:** The `users` table has `UNIQUE` constraints on both `username` and `email`. The `short_urls` table has a `UNIQUE` constraint on `short_code`.

**How we handle it:** Every route that creates or updates records wraps the DB write in a `try/except IntegrityError` block. The error message is parsed to determine which field caused the conflict (username vs email), and the correct 409 response is returned.

**No data corruption occurs.** The failed INSERT is rolled back by PostgreSQL automatically. No manual cleanup needed.

---

## FM-003: Invalid Input Causes Unhandled Exception

**What happens:** A client sends data the route doesn't expect — integer where a string is required, missing fields, non-JSON body, etc.

**How you'll see it (before our fixes):**

```
$ curl -X POST http://localhost:5000/users -d 'garbage'
<!DOCTYPE HTML PUBLIC ...>   # HTML 500 traceback — bad!
```

**How you'll see it (after our fixes):**

```
$ curl -X POST http://localhost:5000/users -d 'garbage'
{"error": "Request body must be JSON"}   # HTTP 400 — good
```

**The three layers of defense:**

1. **Input validation:** Every POST/PUT route checks `request.get_json(silent=True)`. If it returns `None`, we return 400 immediately.
2. **Field validators:** `is_valid_username()`, `is_valid_email()`, `is_valid_url()` reject bad data before it touches the DB.
3. **Global 500 handler:** Even if something slips through, `@app.errorhandler(500)` returns JSON instead of an HTML traceback.

---

## FM-004: Short Code Collision

**What happens:** The randomly generated 6-character short code for a new URL already exists in the database.

**How you'll see it:** You won't — it's handled automatically.

**How we handle it:** `generate_short_code()` in `app/utils/short_code.py` runs a retry loop:

1. Generate a random 6-char alphanumeric code
2. Check if it already exists in the `short_urls` table
3. If it exists, try again (up to 10 attempts)
4. If all 10 collide (astronomically unlikely), fall back to an 8-char code

**The math:** 62^6 = ~56.8 billion possible codes. Even with 1 million URLs in the DB, the collision probability per attempt is ~0.002%. Ten retries makes exhaustion virtually impossible.

---

## FM-005: Request Body Too Large

**What happens:** A client sends a request body larger than 1 MB. Flask rejects it before the route handler ever runs.

**How you'll see it:**

```
$ curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d "$(python3 -c 'print("x" * 2_000_000)')"
{"error": "Request too large. Maximum size is 1 MB."}   # HTTP 413
```

**Why 1 MB?** A JSON user object is a few hundred bytes. A bulk CSV with 10,000 rows is ~200 KB. Anything over 1 MB is either a mistake or abuse. Flask's `MAX_CONTENT_LENGTH` setting enforces this at the WSGI layer, before any parsing happens.

---

## FM-006: App Container Crashes (Chaos Scenario)

**What happens:** The Flask app container dies — killed by OOM, a bug, or manual `docker kill`.

**How you'll see it:**

```
$ curl http://localhost:5001/health
curl: (7) Failed to connect to localhost port 5001: Connection refused
```

**How it recovers (the self-healing demo):**

1. `docker-compose.app.yml` sets `restart: always` on the app service
2. Docker detects the container exited
3. Docker restarts the container automatically
4. The app reconnects to the DB on startup (the `depends_on: condition: service_healthy` ensures DB is ready)
5. Requests start succeeding again — no manual intervention

> **Docker Desktop caveat:** On Mac, `docker kill` doesn't always trigger the restart policy. On Linux (production, CI), it works reliably. For a live demo on Mac, use `docker compose stop app && docker compose -f docker-compose.app.yml up -d` instead.

**How to verify (Linux / CI):**

```bash
# Terminal 1: watch health (polls every second)
watch -n1 "curl -s http://localhost:5001/health"

# Terminal 2: kill the app
docker kill $(docker ps -q --filter name=app)

# Watch Terminal 1: connection refused → then back to {"status": "ok"}
```

**How to verify (Mac — Docker Desktop):**

```bash
# Stop the app
docker compose -f docker-compose.app.yml stop app

# Verify it's down
curl -s http://localhost:5001/health   # connection refused

# Bring it back
docker compose -f docker-compose.app.yml up -d

# Verify it's back
curl -s http://localhost:5001/health   # {"status": "ok"}
```

**What survives a crash:** All data. The database is a separate container with a persistent volume (`pgdata`). Killing the app loses zero data.

**What doesn't survive:** Any in-flight requests at the moment of the crash get a connection error. There's no request queue or retry layer (that would be Phase 4 territory).
