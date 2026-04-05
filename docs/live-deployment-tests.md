# 🌐 Live Deployment — Judge Testing Guide

**Live URL:** `https://walrus-app-mkqo6.ondigitalocean.app`
**Platform:** DigitalOcean App Platform (TOR1 region)
**Stack:** 1 container (Gunicorn, 8 workers) + Dev PostgreSQL

> All commands below can be copy-pasted into any terminal with `curl` installed.

---

## Health Check

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/health | python3 -m json.tool
```

**Expected:**

```json
{
  "status": "ok",
  "db": "ok",
  "redis": "down"
}
```

> Redis is "down" because the DigitalOcean deployment runs PostgreSQL only (no managed Redis). The app degrades gracefully — all features work, just without caching.

---

## Users CRUD

### Create a User

```bash
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}' | python3 -m json.tool
```

**Expected:** 201 Created with `id`, `username`, `email`, `created_at`.

### List Users

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/users | python3 -m json.tool
```

### Get Single User

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/users/1 | python3 -m json.tool
```

### Update User

```bash
curl -s -X PUT https://walrus-app-mkqo6.ondigitalocean.app/users/1 \
  -H "Content-Type: application/json" \
  -d '{"username": "updated_user", "email": "updated@example.com"}' | python3 -m json.tool
```

### Delete User

```bash
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -X DELETE \
  https://walrus-app-mkqo6.ondigitalocean.app/users/1
```

**Expected:** `HTTP Status: 204`

---

## URLs CRUD + Redirect

### Create a Short URL

```bash
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com/MLH/PE-Hackathon-Template-2026", "title": "MLH Hackathon"}' | python3 -m json.tool
```

**Expected:** 201 Created with `short_code` (6-char alphanumeric).

### Test Redirect (replace SHORT_CODE with the value above)

```bash
curl -sI https://walrus-app-mkqo6.ondigitalocean.app/SHORT_CODE
```

**Expected:** `HTTP/2 302` with `location: https://github.com/MLH/PE-Hackathon-Template-2026`

### List URLs

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/urls | python3 -m json.tool
```

### Get URL Stats

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/urls/1/stats | python3 -m json.tool
```

**Expected:** `total_clicks`, `total_events`, `last_visited`.

### Deactivate a URL

```bash
curl -s -X PUT https://walrus-app-mkqo6.ondigitalocean.app/urls/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}' | python3 -m json.tool
```

Then try to redirect — it returns **404** (correctly blocked):

```bash
curl -sI https://walrus-app-mkqo6.ondigitalocean.app/SHORT_CODE
# HTTP/2 404
```

---

## Events

### List Events

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/events | python3 -m json.tool
```

### Create Event

```bash
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/events \
  -H "Content-Type: application/json" \
  -d '{"url_id": 1, "event_type": "click", "details": {"source": "judge_test"}}' | python3 -m json.tool
```

---

## Error Handling (Graceful Failures)

Every error returns clean JSON — no stack traces.

### 404 — Resource Not Found

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/nonexistent | python3 -m json.tool
```

```json
{ "error": "URL not found" }
```

### 404 — User Not Found

```bash
curl -s https://walrus-app-mkqo6.ondigitalocean.app/users/999 | python3 -m json.tool
```

```json
{ "error": "User not found" }
```

### 405 — Method Not Allowed

```bash
curl -s -X PATCH https://walrus-app-mkqo6.ondigitalocean.app/users \
  -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

```json
{ "error": "Method not allowed" }
```

### 422 — Validation: Missing Fields

```bash
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/users \
  -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

```json
{
  "error": "Validation failed",
  "details": {
    "username": "Username is required.",
    "email": "Email is required."
  }
}
```

### 422 — Validation: Invalid Email

```bash
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/users \
  -H "Content-Type: application/json" \
  -d '{"username": "bad", "email": "not-an-email"}' | python3 -m json.tool
```

```json
{
  "error": "Validation failed",
  "details": { "email": "Invalid email format." }
}
```

### 422 — Validation: Invalid URL

```bash
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "not-a-url"}' | python3 -m json.tool
```

```json
{
  "error": "Invalid URL format",
  "details": {
    "original_url": "Must be a valid URL with http:// or https:// scheme"
  }
}
```

### 409 — Duplicate Username

```bash
# Create a user first, then try the same username again
curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/users \
  -H "Content-Type: application/json" \
  -d '{"username": "duplicate_test", "email": "dup@test.com"}' | python3 -m json.tool

curl -s -X POST https://walrus-app-mkqo6.ondigitalocean.app/users \
  -H "Content-Type: application/json" \
  -d '{"username": "duplicate_test", "email": "dup2@test.com"}' | python3 -m json.tool
```

```json
{ "error": "Username already exists" }
```

---

## Quest Verification Summary

### Reliability Quest — What's Testable on Live

| Requirement                    | Live Status | Evidence                                               |
| ------------------------------ | ----------- | ------------------------------------------------------ |
| `/health` returns 200          | ✅          | `curl /health` → `{"status":"ok","db":"ok"}`           |
| Graceful error handling (JSON) | ✅          | 404, 405, 409, 422 all return clean JSON               |
| Bad input → polite errors      | ✅          | Missing fields, invalid email, invalid URL, duplicates |
| No Python stack traces         | ✅          | Every error is structured JSON                         |

### Scalability Quest — What's Testable on Live

| Requirement                | Live Status | Evidence                                    |
| -------------------------- | ----------- | ------------------------------------------- |
| App responds under load    | ✅          | Single DO container with 8 Gunicorn workers |
| Redis graceful degradation | ✅          | Redis down, app still works perfectly       |

### Incident Response Quest — What's Testable on Live

| Requirement             | Live Status | Evidence                               |
| ----------------------- | ----------- | -------------------------------------- |
| Structured JSON logging | ✅          | Visible in DO dashboard → Runtime Logs |

### Documentation Quest — What's Testable on Live

| Requirement                      | Live Status | Evidence                                      |
| -------------------------------- | ----------- | --------------------------------------------- |
| API endpoints work as documented | ✅          | All CRUD operations match API docs            |
| Deploy is live                   | ✅          | `https://walrus-app-mkqo6.ondigitalocean.app` |
