# Capacity Plan: URL Shortener

## Baseline (Single Flask Instance, No Cache, No Load Balancer)

**Test Parameters:**
- Tool: k6 v1.7.1
- Virtual Users (VUs): 50
- Duration: 30 seconds
- Target: `http://localhost:5000` (single Flask dev server)
- Endpoints hit per iteration: `GET /health`, `GET /users`, `GET /urls`, `GET /events`, `POST /users`

**Results:**

| Metric | Value |
|---|---|
| **p95 Response Time** | 2,470 ms |
| **Median (p50) Response Time** | 1,940 ms |
| **p90 Response Time** | 2,410 ms |
| **Average Response Time** | 1,960 ms |
| **Min Response Time** | 82 ms |
| **Max Response Time** | 2,600 ms |
| **Error Rate** | 0.00% |
| **Requests/sec (RPS)** | 24.7 |
| **Total Requests** | 765 |
| **Total Iterations** | 153 |

**Check Pass Rates:**
- health status 200: 100%
- health latency < 500ms: 0% (all above 500ms under load)
- users status 200: 100%
- users latency < 500ms: 1%
- urls status 200: 100%
- events status 200: 100%
- create user status 201: 100%

**Observations:**
- All requests returned correct status codes — zero HTTP errors
- Under 50 concurrent users, p95 latency reaches 2.47s — well above the 500ms SLO target
- Flask's single-threaded dev server is the primary bottleneck: requests are serialized, causing queuing under concurrency
- Write path (POST /users) completes successfully with no integrity errors
- The system is functionally correct but performance-constrained at this tier

**Bottleneck Analysis:**
- **Primary:** Flask dev server processes requests serially. 50 VUs create significant request queuing.
- **Secondary:** All reads hit PostgreSQL directly with no caching layer.
- **Next Steps:** Add Nginx load balancer with multiple app instances (Phase 5.2), then Redis caching (Phase 5.3).

---

## Scale-Out (2 Flask Instances + Nginx Load Balancer)

**What Changed:**
- Introduced Nginx as a reverse proxy with `least_conn` load balancing
- Deployed two identical Flask app instances (`app1`, `app2`) behind Nginx
- Prometheus now scrapes both `app1:5000` and `app2:5000` directly
- Public access to `/metrics` blocked at the Nginx layer (403 Forbidden)

**Architecture:**

```
                 ┌──────────┐
  Client ──────►│  Nginx   │
  (port 80)     │  :80     │
                 └────┬─────┘
                      │ least_conn
               ┌──────┴──────┐
               │             │
          ┌────▼────┐  ┌─────▼───┐
          │  app1   │  │  app2   │
          │  :5000  │  │  :5000  │
          └────┬────┘  └────┬────┘
               │            │
          ┌────▼────────────▼────┐
          │    PostgreSQL :5432  │
          │    Redis      :6379 │
          └──────────────────────┘
```

**Why `least_conn`?**
Round-robin distributes requests evenly regardless of how busy each instance is. With variable-length requests (e.g., a bulk CSV import takes much longer than a health check), round-robin can overload one instance while the other is idle. `least_conn` routes each new request to whichever instance currently has the fewest active connections, naturally balancing the load under mixed workloads.

**Why block `/metrics` at Nginx?**
Prometheus scrapes metrics directly from each app instance on the internal Docker network (`app1:5000/metrics`, `app2:5000/metrics`). Exposing `/metrics` publicly would leak internal operational data (request counts, error rates, latency distributions) that an attacker could use for reconnaissance. Nginx returns 403 for any external request to `/metrics`.

**Test Parameters:**
- Tool: k6
- Virtual Users (VUs): 200
- Duration: 30 seconds
- Target: `http://localhost:80` (Nginx → 2 Flask instances)
- Endpoints hit per iteration: `GET /health`, `GET /users`, `GET /urls`, `GET /events`, `POST /users`

**How to Run:**
```bash
docker-compose up -d --build
k6 run --summary-export=load_tests/scale_out_results.json load_tests/scale_out.js
```

**Results:**

> ⚠️ Fill in after running the load test against the scale-out stack.

| Metric | Baseline (1 instance) | Scale-Out (2 instances) | Change |
|---|---|---|---|
| **p95 Response Time** | 2,470 ms | _TBD_ | _TBD_ |
| **Median (p50)** | 1,940 ms | _TBD_ | _TBD_ |
| **Error Rate** | 0.00% | _TBD_ | _TBD_ |
| **Requests/sec** | 24.7 | _TBD_ | _TBD_ |
| **Total Requests** | 765 | _TBD_ | _TBD_ |
| **VUs** | 50 | 200 | 4× |

**Expected Improvements:**
- Two instances doubles request-processing capacity → higher RPS
- `least_conn` prevents queuing behind a slow request on one instance
- Nginx handles connection management (keepalive 32), reducing TCP overhead
- Silver SLO target: p95 < 3,000 ms at 200 VUs

**Observations:**
> Fill in after running the test. Note: if p95 exceeds 3,000 ms, the next optimization is Redis caching (Phase 5.3) to offload read-heavy endpoints from PostgreSQL.
