import http from "k6/http";
import { check, sleep } from "k6";

// Scale-out test: 200 VUs through Nginx load balancer (2 app instances)
// Usage: k6 run load_tests/scale_out.js
// Or with custom base URL: k6 run -e BASE_URL=http://localhost:80 load_tests/scale_out.js

const BASE_URL = __ENV.BASE_URL || "http://localhost:80";

export const options = {
  vus: 200,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<3000"],  // Silver SLO: p95 < 3s
    http_req_failed: ["rate<0.05"],     // < 5% error rate
  },
};

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    "health status 200": (r) => r.status === 200,
    "health latency < 500ms": (r) => r.timings.duration < 500,
  });

  // List users
  const usersRes = http.get(`${BASE_URL}/users`);
  check(usersRes, {
    "users status 200": (r) => r.status === 200,
    "users latency < 1s": (r) => r.timings.duration < 1000,
  });

  // List URLs
  const urlsRes = http.get(`${BASE_URL}/urls`);
  check(urlsRes, {
    "urls status 200": (r) => r.status === 200,
  });

  // List events
  const eventsRes = http.get(`${BASE_URL}/events`);
  check(eventsRes, {
    "events status 200": (r) => r.status === 200,
  });

  // Create + read a user to test write path through LB
  const createRes = http.post(
    `${BASE_URL}/users`,
    JSON.stringify({
      username: `scale_${__VU}_${__ITER}`,
      email: `scale_${__VU}_${__ITER}@load.test`,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(createRes, {
    "create user status 201": (r) => r.status === 201,
  });

  sleep(0.1);
}
