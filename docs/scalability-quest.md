# 🚀 Scalability Engineering Quest — Local Verification Guide

## Prerequisites — Clone & Setup

```bash
# 1. Clone the repo
git clone https://github.com/prajithravisankar/PE-Hackathon-Template-2026-Farmers.git
cd PE-Hackathon-Template-2026-Farmers

# 2. Install Docker & Docker Compose (required for all tiers)
# macOS: brew install --cask docker
# Linux: https://docs.docker.com/engine/install/

# 3. Install k6 (load testing tool)
# macOS:
brew install k6
# Linux:
# sudo gpg -k && sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D68
# echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
# sudo apt-get update && sudo apt-get install k6
```

---

## 🥉 Bronze — The Baseline

> _Objective: Stress test your system._

| Requirement             | What We Built                                                                                                                    | How to Run Locally                                | Expected Output                                                                     |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Load Test Tool**      | k6 load test scripts in `load_tests/`. Three scripts: `baseline.js` (50 VUs), `scale_out.js` (200 VUs), `tsunami.js` (500 VUs).  | `ls load_tests/`                                  | `baseline.js`, `scale_out.js`, `tsunami.js`                                         |
| **50 Concurrent Users** | `load_tests/baseline.js` — 50 virtual users for 30 seconds, hitting a single app instance on port 5000.                          | See "Bronze Demo" below.                          | Terminal output showing 50 VUs, request stats, p95 latency, error rate.             |
| **Record Stats**        | k6 outputs response time (p50, p95, p99), error rate, requests/sec, and data transfer. Results saved to `baseline_results.json`. | Results printed to terminal after test completes. | Documented baseline: p95 response time and error rate (SLO: p95 < 3s, errors < 5%). |

### Bronze Demo

```bash
# 1. Start the single-instance stack
docker compose -f docker-compose.app.yml up -d --build

# 2. Wait for it to be healthy
sleep 5
curl -s http://localhost:5001/health | python3 -m json.tool

# 3. Seed some data (optional, makes the test more realistic)
uv run python scripts/load_csv_data.py

# 4. Run the 50-user baseline load test
k6 run load_tests/baseline.js

# 5. Screenshot the terminal output — it shows:
#    - http_req_duration p(95): the p95 response time
#    - http_req_failed: the error rate
#    - vus: 50

# 6. Save results to JSON
k6 run --out json=baseline_results.json load_tests/baseline.js

# 7. Clean up
docker compose -f docker-compose.app.yml down
```

---

## 🥈 Silver — The Scale-Out

> _Objective: One server isn't enough. Build a fleet._

| Requirement                   | What We Built                                                                                                                        | How to Run Locally                                      | Expected Output                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **200 Concurrent Users**      | `load_tests/scale_out.js` — 200 VUs for 30 seconds, hitting through the Nginx load balancer on port 80.                              | See "Silver Demo" below.                                | k6 output: 200 VUs, p95 < 3s, error rate < 5%.                                                                         |
| **Clone Army (2+ instances)** | `docker-compose.yml` runs **2 app containers** (`app1`, `app2`) plus DB, Redis, Nginx, Prometheus, Grafana, Alertmanager.            | `docker compose up -d --build && docker compose ps`     | `docker ps` shows: `app1`, `app2`, `nginx`, `db`, `redis`, `prometheus`, `grafana`, `alertmanager` — **8 containers**. |
| **Load Balancer (Nginx)**     | `nginx/nginx.conf` — Nginx with `least_conn` algorithm distributes traffic across app1 and app2. Blocks `/metrics` externally (403). | Nginx runs on **port 80**. All traffic goes through it. | `curl http://localhost:80/health` returns OK. Both backends serve traffic.                                             |
| **Response Time < 3s**        | SLO threshold configured in k6 scripts: `http_req_duration: ['p(95)<3000']`. Test fails if p95 exceeds 3 seconds.                    | Check k6 output for threshold status.                   | `✓ http_req_duration...p(95)<3000` — green checkmark.                                                                  |

### Silver Demo

```bash
# 1. Start the FULL stack (2 app instances + load balancer)
docker compose up -d --build

# 2. Verify all containers are running
docker compose ps
# Should show: app1, app2, nginx, db, redis, prometheus, grafana, alertmanager

# 3. Verify load balancer
curl -s http://localhost:80/health | python3 -m json.tool
# → {"status": "ok", "db": "ok", "redis": "ok"}

# 4. Verify metrics are blocked externally
curl -s http://localhost:80/metrics
# → 403 Forbidden

# 5. Run the 200-user scale-out test
k6 run load_tests/scale_out.js

# 6. Screenshot the output showing:
#    - vus: 200
#    - p95 < 3s
#    - error rate < 5%
#    - All thresholds passing ✓

# 7. Save results
k6 run --out json=scale_out_results.json load_tests/scale_out.js
```

---

## 🥇 Gold — The Speed of Light

> _Objective: Optimization and Caching._

| Requirement               | What We Built                                                                                                                                                                                                                 | How to Run Locally              | Expected Output                                                                                                                      |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **500+ Concurrent Users** | `load_tests/tsunami.js` — Staged ramp: 0→100→300→500 VUs over 60 seconds. 80/20 read-write traffic split. Hits Nginx on port 80.                                                                                              | See "Gold Demo" below.          | k6 output: 500 VUs peak, p95 < 3s, error rate < 5%.                                                                                  |
| **Redis Caching**         | `app/utils/cache.py` — Cache-aside pattern with `@cache_response` decorator. `/users` cached 30s, `/urls` cached 15s. Sets `X-Cache: HIT/MISS` header. Write operations invalidate cache. Graceful degradation if Redis down. | See "Cache Verification" below. | First request: `X-Cache: MISS`. Second identical request: `X-Cache: HIT`. After write: cache invalidated, next read is `MISS` again. |
| **Bottleneck Analysis**   | Documented in `docs/capacity_plan.md`. Identified DB as primary bottleneck pre-cache. Redis caching reduced DB load by ~80% for reads. Nginx least_conn balancing distributes write load.                                     | `cat docs/capacity_plan.md`     | Full bottleneck analysis document.                                                                                                   |
| **Error Rate < 5%**       | SLO in k6: `http_req_failed: ['rate<0.05']`. All three load tests enforce this.                                                                                                                                               | Check k6 output threshold.      | `✓ http_req_failed...rate<0.05` — green checkmark.                                                                                   |

### Gold Demo

```bash
# 1. Start the full stack
docker compose up -d --build

# 2. Seed data for realistic load test
uv run python scripts/load_csv_data.py

# 3. Run the 500-user tsunami test
k6 run load_tests/tsunami.js

# 4. Screenshot showing:
#    - Staged ramp up to 500 VUs
#    - p95 < 3s
#    - Error rate < 5%
#    - All thresholds ✓

# 5. Save results
k6 run --out json=tsunami_results.json load_tests/tsunami.js
```

### Cache Verification

```bash
# Start the stack
docker compose up -d --build

# First request — cache MISS
curl -sI http://localhost:80/users | grep X-Cache
# X-Cache: MISS

# Second request — cache HIT
curl -sI http://localhost:80/users | grep X-Cache
# X-Cache: HIT

# Create a user (write invalidates cache)
curl -s -X POST http://localhost:80/users \
  -H "Content-Type: application/json" \
  -d '{"username": "cachetest", "email": "cache@test.com"}'

# Next read — cache MISS again (was invalidated)
curl -sI http://localhost:80/users | grep X-Cache
# X-Cache: MISS
```

### Speed Comparison (Before vs After Cache)

```bash
# Without cache — direct DB query every time
# With cache — Redis serves from memory

# You can see the difference in k6 output:
# - Pre-cache p95 latency: ~50-200ms (DB bound)
# - Post-cache p95 latency: ~5-20ms (Redis memory)
```

---

## Summary of All Load Tests

| Test               | File                      | VUs | Duration | Target                        | SLO                   |
| ------------------ | ------------------------- | --- | -------- | ----------------------------- | --------------------- |
| Baseline (Bronze)  | `load_tests/baseline.js`  | 50  | 30s      | `localhost:5000` (single app) | p95 < 3s, errors < 5% |
| Scale-Out (Silver) | `load_tests/scale_out.js` | 200 | 30s      | `localhost:80` (Nginx LB)     | p95 < 3s, errors < 5% |
| Tsunami (Gold)     | `load_tests/tsunami.js`   | 500 | 60s      | `localhost:80` (Nginx LB)     | p95 < 3s, errors < 5% |
