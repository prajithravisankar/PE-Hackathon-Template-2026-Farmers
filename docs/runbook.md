# On-Call Runbook: URL Shortener

> Use this runbook when an alert fires or a user reports an issue. Follow the steps in order. Escalate if unresolved after 5 minutes.

---

## Alert: ServiceDown

**Severity:** Critical | **SLO Impact:** Full outage — 0% availability

**Symptoms:**
- All API endpoints return connection refused or timeout
- Prometheus `up{job="url-shortener"} == 0`
- Health check polling shows no response

**Triage Steps:**

1. **Check container status:**
   ```bash
   docker ps -a | grep -E 'app1|app2|nginx'
   ```
   - If container is restarting: check logs (step 3)
   - If container is stopped: restart it (step 2)

2. **Restart the app instances:**
   ```bash
   docker-compose restart app1 app2 nginx
   ```
   Wait 30 seconds, then verify:
   ```bash
   curl -s http://localhost/health | python -m json.tool
   ```

3. **Check application logs:**
   ```bash
   docker-compose logs --tail=50 app1 app2
   ```
   Look for:
   - `OperationalError` → database connection issue (see DB Down section)
   - `ImportError` → dependency missing, redeploy
   - `PermissionError` → file system issue in container

4. **Check if database is down:**
   ```bash
   docker-compose exec db pg_isready -U postgres
   ```
   If not ready:
   ```bash
   docker-compose restart db
   ```
   Wait for health check, then restart app.

5. **Escalate** if not resolved after 5 minutes. Gather: `docker-compose logs app`, `docker ps -a`, and the time the alert fired.

**Resolution Verification:**
- `curl http://localhost/health` returns `{"status": "ok", "db": "ok", "redis": "ok"}`
- Prometheus `up{job="url-shortener"} == 1`
- Discord alert resolves automatically

---

## Alert: HighErrorRate

**Severity:** Warning | **SLO Impact:** Degraded — users experiencing failures

**Symptoms:**
- 5xx error rate > 5% over 2 minutes
- Grafana "Errors — 5xx Rate" panel shows spike
- User reports of failed requests

**Triage Steps:**

1. **Check which endpoints are failing:**
   Open Grafana dashboard → "Endpoint Breakdown" panel. Identify the endpoint(s) with elevated error rates.

2. **Check application logs for errors:**
   ```bash
   docker-compose logs --tail=100 app1 app2 | python -c "
   import sys, json
   for line in sys.stdin:
       try:
           obj = json.loads(line)
           if obj.get('levelname') in ('ERROR', 'WARNING'):
               print(json.dumps(obj, indent=2))
       except: pass
   "
   ```

3. **Common error patterns:**

   | Log Pattern | Likely Cause | Fix |
   |---|---|---|
   | `IntegrityError` on POST /users | Duplicate username/email | Expected behavior (409) — not a real error |
   | `OperationalError: connection refused` | DB is down | Restart DB: `docker-compose restart db` |
   | `ConnectionError` to Redis | Redis is down | Restart Redis: `docker-compose restart redis` |
   | `ValueError` in serialization | Bad data in DB | Check the specific record, fix or delete |

4. **If errors started after a deployment:**
   ```bash
   git log --oneline -5
   ```
   Roll back to the previous commit:
   ```bash
   git checkout <previous_sha>
   docker-compose up -d --build app1 app2
   ```

5. **If errors are input-related (4xx):** No action needed — these are client errors, not service errors. Verify the alert threshold isn't counting 4xx as errors.

**Resolution Verification:**
- Grafana error rate panel returns below 5%
- No new ERROR lines in logs for 2 minutes

---

## Alert: HighLatency

**Severity:** Warning | **SLO Impact:** Degraded UX — users experiencing slow responses

**Symptoms:**
- p95 latency > 1 second for 5+ minutes
- Grafana "Latency — p50 / p95 / p99" panel shows elevated values
- Users report slow page loads

**Triage Steps:**

1. **Identify the slow endpoint:**
   Open Grafana → "Endpoint Breakdown" panel. Which path has the highest request rate? Cross-reference with the latency panel.

2. **Check for resource saturation:**
   ```bash
   docker stats --no-stream
   ```
   Look for:
   - CPU > 90% → app is compute-bound, consider scaling horizontally
   - Memory > 80% → possible memory leak, restart app

3. **Check database performance:**
   ```bash
   docker-compose exec db psql -U postgres -d hackathon_db -c "
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC
   LIMIT 5;"
   ```
   If slow queries found, check for missing indexes.

4. **Check Redis (if caching is enabled):**
   ```bash
   docker-compose exec redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
   ```
   Low hit ratio = cache isn't helping. Check TTL values and whether cache invalidation is too aggressive.

5. **Quick mitigation — restart app instances to clear any connection pool exhaustion:**
   ```bash
   docker-compose restart app1 app2
   ```

**Resolution Verification:**
- Grafana p95 latency panel drops below 1s
- `curl -w "%{time_total}\n" -o /dev/null -s http://localhost/users` shows < 500ms

---

## General: Health Check Returns "degraded"

**Symptoms:**
- `GET /health` returns `{"status": "degraded", ...}` with HTTP 503
- One or more dependencies are marked as "down"

**Triage Steps:**

1. **Check which dependency is down:**
   ```bash
   curl -s http://localhost:5000/health | python -m json.tool
   ```

2. **If `"db": "down"`:**
   ```bash
   docker-compose exec db pg_isready -U postgres
   # If not ready:
   docker-compose restart db
   ```

3. **If `"redis": "down"`:**
   ```bash
   docker-compose exec redis redis-cli ping
   # If no PONG:
   docker-compose restart redis
   ```

4. **Verify recovery:**
   ```bash
   curl -s http://localhost:5000/health
   # Should return {"status": "ok", "db": "ok", "redis": "ok"} with 200
   ```

---

## Grafana Dashboard Reference

**URL:** http://localhost:3000 (admin / hackathon)

**Dashboard:** "URL Shortener — Four Golden Signals"

| Panel | Signal | What to Look For |
|---|---|---|
| Traffic — Request Rate | Traffic | Sudden drop = outage; sudden spike = possible abuse |
| Errors — 5xx Rate | Errors | Any sustained 5xx = investigate immediately |
| Latency — p50/p95/p99 | Latency | p95 > 1s = degraded UX |
| Saturation — In-flight | Saturation | Sustained high throughput + rising latency = at capacity |
| Endpoint Breakdown | Traffic | Isolate which endpoint is the bottleneck |
| Service Status | Availability | RED = Prometheus can't reach the app |
| Error Rate (stat) | Errors | Quick glance at current error percentage |
| p95 Latency (stat) | Latency | Quick glance at current tail latency |
| Total Requests/min (stat) | Traffic | Current load level |
