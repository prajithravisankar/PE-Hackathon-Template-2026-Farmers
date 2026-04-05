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
