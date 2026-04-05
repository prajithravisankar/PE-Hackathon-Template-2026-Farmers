# 🚨 Incident Response Quest — Local Verification Guide

## Prerequisites — Clone & Setup

```bash
# 1. Clone the repo
git clone https://github.com/prajithravisankar/PE-Hackathon-Template-2026-Farmers.git
cd PE-Hackathon-Template-2026-Farmers

# 2. Install Docker & Docker Compose (required for monitoring stack)
# macOS: brew install --cask docker
```

---

## 🥉 Bronze — The Watchtower

> _Objective: Stop using print statements._

| Requirement                   | What We Built                                                                                                                                                                                                                | How to Run Locally                   | Expected Output                                                                                                                                                               |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Structured Logging (JSON)** | `python-json-logger` configured in `app/__init__.py`. Every request is logged with `asctime`, `levelname`, `name`, `message`, plus extras: `method`, `path`, `status`, `duration_ms`. Warnings for 4xx+, info for 2xx-3xx.   | See "Logging Demo" below.            | JSON log lines in terminal: `{"asctime": "...", "levelname": "INFO", "message": "request_completed", "method": "GET", "path": "/health", "status": 200, "duration_ms": 1.23}` |
| **Metrics Endpoint**          | Prometheus metrics via `prometheus-flask-exporter` at `GET /metrics`. Exposes: `flask_http_request_total` (by method, status, path), `flask_http_request_duration_seconds_bucket` (histograms), `app_info{version="1.0.0"}`. | `curl http://localhost:5000/metrics` | Prometheus text format with counters, histograms, and gauges. Includes request counts, latency buckets, and app info.                                                         |
| **View Logs Without SSH**     | Docker Compose collects logs from all containers. View with `docker compose logs`. Runtime logs also visible in Grafana (via Prometheus metrics).                                                                            | `docker compose logs -f app1`        | Live-streaming structured JSON logs from the container.                                                                                                                       |

### Logging Demo

```bash
# Option A: Run locally (see logs directly in terminal)
uv run flask --app app:create_app run

# In another terminal, make some requests:
curl http://localhost:5000/health
curl http://localhost:5000/users
curl http://localhost:5000/nonexistent

# You'll see JSON log lines for each request in the Flask terminal:
# {"asctime": "2026-04-05 ...", "levelname": "INFO", "name": "app", "message": "request_completed", "method": "GET", "path": "/health", "status": 200, "duration_ms": 0.85}
# {"asctime": "2026-04-05 ...", "levelname": "WARNING", "name": "app", "message": "request_completed", "method": "GET", "path": "/nonexistent", "status": 404, "duration_ms": 0.32}

# Option B: Docker (production-like)
docker compose up -d --build
docker compose logs -f app1 app2
```

### Metrics Demo

```bash
# After starting the app, hit the metrics endpoint
curl -s http://localhost:5000/metrics | head -30

# Example output:
# # HELP flask_http_request_total Total number of HTTP requests
# # TYPE flask_http_request_total counter
# flask_http_request_total{method="GET",status="200"} 5.0
# flask_http_request_total{method="GET",status="404"} 1.0
# # HELP flask_http_request_duration_seconds Flask HTTP request duration in seconds
# flask_http_request_duration_seconds_bucket{le="0.005",method="GET",status="200"} 4.0
# ...
# # HELP app_info URL Shortener API
# app_info{version="1.0.0"} 1.0
```

---

## 🥈 Silver — The Alarm

> _Objective: Wake up the on-call engineer._

| Requirement                | What We Built                                                                                                                                                      | How to Run Locally                                                   | Expected Output                                                             |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Alert: Service Down**    | Prometheus alert rule in `monitoring/alert_rules.yml`: `ServiceDown` fires when `up{job="url-shortener"} == 0` for 1 minute. Severity: **critical**.               | See "Alert Demo" below.                                              | Alertmanager fires, sends notification to Discord.                          |
| **Alert: High Error Rate** | Prometheus alert rule: `HighErrorRate` fires when 5xx rate exceeds 5% of total traffic for 2 minutes. Severity: **warning**.                                       | Generate 5xx errors → watch Alertmanager.                            | Alert triggers when error threshold exceeded.                               |
| **Alert: High Latency**    | Prometheus alert rule: `HighLatency` fires when p95 latency exceeds 1 second for 5 minutes. Severity: **warning**.                                                 | k6 load test with heavy traffic.                                     | Alert triggers when latency degrades.                                       |
| **Discord Notifications**  | Alertmanager configured in `monitoring/alertmanager.yml` with Discord webhook receiver. Groups alerts by `alertname`, waits 10s before grouping, repeats every 1h. | Configure your Discord webhook URL in `monitoring/alertmanager.yml`. | Discord channel gets alert notification within ~1-2 minutes of the failure. |
| **Fire Within 5 Minutes**  | ServiceDown: 1min evaluation. HighErrorRate: 2min. HighLatency: 5min. All within the 5-minute requirement.                                                         | Kill a container → alert fires in ~1-2 minutes.                      | Timestamp on Discord message shows alert within 5 minutes of incident.      |

### Alert Demo

```bash
# 1. Start the full monitoring stack
docker compose up -d --build

# 2. Verify Prometheus is scraping
open http://localhost:9090/targets
# Both app1:5000 and app2:5000 should show "UP"

# 3. Verify Alertmanager is running
open http://localhost:9093
# Should show "No alerts" initially

# 4. Trigger a ServiceDown alert — kill an app container
docker kill $(docker compose ps -q app1)

# 5. Wait ~1-2 minutes, then check:
open http://localhost:9093
# "ServiceDown" alert should appear in FIRING state

# 6. Check Discord channel for notification
# (requires valid webhook URL in monitoring/alertmanager.yml)

# 7. Recover — restart the container
docker compose up -d app1

# 8. Alert resolves after the instance is healthy again
```

### Alert Rules Summary

| Alert Name    | Condition                      | For Duration | Severity | File                         |
| ------------- | ------------------------------ | ------------ | -------- | ---------------------------- |
| ServiceDown   | `up{job="url-shortener"} == 0` | 1 minute     | critical | `monitoring/alert_rules.yml` |
| HighErrorRate | 5xx rate > 5% of total         | 2 minutes    | warning  | `monitoring/alert_rules.yml` |
| HighLatency   | p95 > 1 second                 | 5 minutes    | warning  | `monitoring/alert_rules.yml` |

### Discord Webhook Setup

```yaml
# In monitoring/alertmanager.yml, replace the webhook_url:
receivers:
  - name: "discord"
    discord_configs:
      - webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"
```

---

## 🥇 Gold — The Command Center

> _Objective: Total situational awareness._

| Requirement                             | What We Built                                                                                                                                                                                                              | How to Run Locally                                      | Expected Output                                                                |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Grafana Dashboard**                   | Pre-built dashboard: "URL Shortener — Four Golden Signals" with 9 panels. Auto-provisioned via `monitoring/grafana/dashboards/url-shortener.json`. Datasource auto-configured.                                             | See "Dashboard Demo" below.                             | Full Grafana dashboard at `http://localhost:3000` with live data.              |
| **4+ Metrics Tracked**                  | **Latency** (p50/p95/p99), **Traffic** (RPS by method, RPS total), **Errors** (5xx/s, 4xx/s, error rate %), **Saturation** (in-flight requests, requests/min). Plus: service status (up/down), endpoint breakdown by path. | Generate traffic → watch dashboard update in real-time. | 9 panels all showing live data. Refresh: every 10 seconds.                     |
| **Runbook**                             | `docs/runbook.md` — step-by-step emergency guide for ServiceDown, HighErrorRate, HighLatency, DB failure, Redis failure. Written for "3 AM nonfunctional self."                                                            | `cat docs/runbook.md`                                   | Full runbook with diagnosis steps, commands to run, and resolution procedures. |
| **Sherlock Mode (Root Cause Analysis)** | Use dashboard to diagnose: which endpoint is slow? which container is down? is it a DB bottleneck or app bottleneck?                                                                                                       | See "Root Cause Demo" below.                            | Walkthrough of using dashboard panels to pinpoint a fake issue's root cause.   |

### Dashboard Demo

```bash
# 1. Start the full stack
docker compose up -d --build

# 2. Open Grafana
open http://localhost:3000
# Login: admin / hackathon

# 3. Navigate to Dashboards → URL Shortener — Four Golden Signals
# All 9 panels should be visible (may show "No data" until traffic flows)

# 4. Generate traffic to populate the dashboard
k6 run load_tests/baseline.js

# 5. Watch the dashboard update in real-time:
#    - Traffic panel shows RPS climbing
#    - Latency panel shows p50/p95/p99
#    - Error panel shows 4xx/5xx rates
#    - Service Status shows UP (green)
```

### Dashboard Panels

| #   | Panel                  | Type        | What It Shows                                  |
| --- | ---------------------- | ----------- | ---------------------------------------------- |
| 1   | Traffic — Request Rate | Time series | Total RPS + RPS by HTTP method                 |
| 2   | Errors — 5xx Rate      | Time series | 5xx/s and 4xx/s over time                      |
| 3   | Latency — p50/p95/p99  | Time series | Response time percentiles, red threshold at 1s |
| 4   | Saturation — In-flight | Time series | Throughput and requests/min                    |
| 5   | Endpoint Breakdown     | Bar chart   | Request rate broken down by URL path           |
| 6   | Service Status         | Stat        | UP/DOWN indicator (green/red)                  |
| 7   | Error Rate             | Stat        | 5xx percentage (yellow >1%, red >5%)           |
| 8   | p95 Latency            | Stat        | Current p95 (yellow >0.5s, red >1s)            |
| 9   | Total Requests/min     | Stat        | Request throughput (yellow >100, red >500)     |

### Root Cause Demo

```bash
# Scenario: "Users are reporting slow responses"

# 1. Open Grafana dashboard
open http://localhost:3000

# 2. Check Service Status panel → Both instances UP? If one is DOWN, that's your cause.

# 3. Check Latency panel → Is p95 spiking? When did it start?

# 4. Check Endpoint Breakdown → Which endpoint is getting hammered?

# 5. Check Error Rate → Are we returning 5xx errors? That points to app/DB crash.

# 6. Check Saturation → Are requests/min unusually high? Could be a traffic spike.

# 7. Diagnosis example:
#    - p95 spiked at 14:30
#    - Endpoint breakdown shows /urls getting 10x normal traffic
#    - Error rate is 0% (no crashes)
#    - Conclusion: Traffic spike on /urls endpoint, need to scale or increase cache TTL
```

---

## Full Monitoring Stack Architecture

```
                    ┌─────────────┐
                    │   Grafana    │ :3000
                    │  Dashboard   │
                    └──────┬──────┘
                           │ queries
                    ┌──────▼──────┐      ┌──────────────┐
                    │ Prometheus  │─────→│ Alertmanager │ :9093
                    │   :9090     │      │   → Discord  │
                    └──────┬──────┘      └──────────────┘
                           │ scrapes /metrics every 10s
                    ┌──────▼──────┐
                    │    Nginx    │ :80
                    │ least_conn  │
                    ├──────┬──────┤
               ┌────▼──┐  ┌──▼────┐
               │ app1  │  │ app2  │ :5000
               └───┬───┘  └───┬───┘
                   │           │
              ┌────▼───────────▼────┐
              │    PostgreSQL :5432  │
              └─────────────────────┘
              ┌─────────────────────┐
              │    Redis :6379      │
              └─────────────────────┘
```
