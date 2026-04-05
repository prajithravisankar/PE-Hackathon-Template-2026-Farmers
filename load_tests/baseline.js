import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:5000";

export const options = {
  vus: 50,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<3000"],
    http_req_failed: ["rate<0.05"],
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
    "users latency < 500ms": (r) => r.timings.duration < 500,
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

  // Create + read a user to test write path
  const createRes = http.post(
    `${BASE_URL}/users`,
    JSON.stringify({
      username: `k6user_${__VU}_${__ITER}`,
      email: `k6_${__VU}_${__ITER}@load.test`,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(createRes, {
    "create user status 201": (r) => r.status === 201,
  });

  sleep(0.1);
}
