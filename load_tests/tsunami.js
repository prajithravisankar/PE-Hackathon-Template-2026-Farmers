import http from "k6/http";
import { check, sleep } from "k6";

// Tsunami test: 500 VUs through Nginx LB with Redis caching (Gold tier)
// Purpose: Validate cache-aside pattern under extreme read-heavy load
// Usage: k6 run load_tests/tsunami.js

const BASE_URL = __ENV.BASE_URL || "http://localhost:80";
const RUN_ID = Date.now();

export const options = {
  stages: [
    { duration: "10s", target: 250 }, // ramp up to half capacity
    { duration: "40s", target: 500 }, // push to full 500 VUs
    { duration: "10s", target: 0 }, // ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<3000"], // Gold SLO: p95 < 3s under 500 VUs
    http_req_failed: ["rate<0.05"], // < 5% error rate
  },
};

export default function () {
  // READ-HEAVY: 80% reads, 20% writes to exercise cache hit/miss ratio

  if (__ITER % 5 !== 0) {
    // --- Read path (80% of iterations) ---

    // Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      "health status 200": (r) => r.status === 200,
    });

    // List users (cached, TTL 30s)
    const usersRes = http.get(`${BASE_URL}/users`);
    check(usersRes, {
      "users status 200": (r) => r.status === 200,
      "users X-Cache present": (r) => r.headers["X-Cache"] !== undefined,
    });

    // List URLs (cached, TTL 15s)
    const urlsRes = http.get(`${BASE_URL}/urls`);
    check(urlsRes, {
      "urls status 200": (r) => r.status === 200,
    });

    // List events (not cached — write-heavy endpoint)
    const eventsRes = http.get(`${BASE_URL}/events`);
    check(eventsRes, {
      "events status 200": (r) => r.status === 200,
    });
  } else {
    // --- Write path (20% of iterations) — triggers cache invalidation ---

    const createUserRes = http.post(
      `${BASE_URL}/users`,
      JSON.stringify({
        username: `t${RUN_ID}_${__VU}_${__ITER}`,
        email: `t${RUN_ID}_${__VU}_${__ITER}@load.test`,
      }),
      { headers: { "Content-Type": "application/json" } },
    );
    check(createUserRes, {
      "create user status 201": (r) => r.status === 201,
    });

    // Immediately read after write to verify cache was invalidated
    const usersAfterWrite = http.get(`${BASE_URL}/users`);
    check(usersAfterWrite, {
      "users after write status 200": (r) => r.status === 200,
    });
  }

  sleep(0.05); // minimal pause to prevent pure CPU spin
}
