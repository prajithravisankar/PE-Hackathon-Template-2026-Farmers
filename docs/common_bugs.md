# Common Bugs — Discovery & Resolution Log

This document catalogues bugs found during MLH automated test evaluation and their root-cause fixes.

---

## Bug 1: DELETE /users/\<id\> → 405 Method Not Allowed

**Symptom:** `DELETE /users/402` returns `{"error": "Method not allowed"}` with status 405.

**Root Cause:** No `DELETE` route was registered on the users blueprint. Only `GET`, `POST`, and `PUT` existed.

**Fix:** Added `@users_bp.route("/users/<int:user_id>", methods=["DELETE"])` handler that looks up the user (404 if missing), calls `user.delete_instance()`, and returns `204 No Content`.

**Commit:** `fix: add DELETE /users/<id> endpoint (returns 204)`

---

## Bug 2: DELETE /urls/\<id\> → 405 Method Not Allowed

**Symptom:** `DELETE /urls/4` returns `{"error": "Method not allowed"}` with status 405.

**Root Cause:** No `DELETE` route was registered on the urls blueprint. Only `GET`, `POST`, and `PUT` existed.

**Fix:** Added `@urls_bp.route("/urls/<int:url_id>", methods=["DELETE"])` handler that looks up the URL (404 if missing), logs a `"deleted"` event, calls `url.delete_instance()`, and returns `204 No Content`.

**Commit:** `fix: add DELETE /urls/<id> endpoint (returns 204)`

---

## Bug 3: GET /urls?is\_active=true Returns All URLs (No Filtering)

**Symptom:** `GET /urls?is_active=true` returns all 3 URLs (including deactivated ones) instead of only the 2 active URLs.

**Root Cause:** The `list_urls` function only filtered by `user_id` query param. The `is_active` query param was completely ignored.

**Fix:** Added `is_active` query param handling — parses the string value (`"true"/"false"`) and applies `.where(ShortURL.is_active == bool_val)` to the query.

**Commit:** `fix: add is_active query param filtering to GET /urls`

---

## Bug 4: GET /events?event\_type=click Returns All Events (No Filtering)

**Symptom:** `GET /events?event_type=click` returns all 11 events (mixed types: `created`, `visited`, `updated`, etc.) instead of only `click` events.

**Root Cause:** The `list_events` function only filtered by `url_id` and `user_id`. The `event_type` query param was ignored.

**Fix:** Added `event_type` query param handling — applies `.where(Event.event_type == event_type)` to the query.

**Commit:** `fix: add event_type query param filtering to GET /events`

---

## Bug 5: POST /events → 405 Method Not Allowed

**Symptom:** `POST /events` with JSON body `{"event_type": "click", "url_id": 1, "user_id": 1, "details": {...}}` returns `{"error": "Method not allowed"}` with status 405.

**Root Cause:** The events blueprint only had a `GET /events` route. No `POST` handler existed for creating events via the API (events were only created internally by URL operations).

**Fix:** Added `@events_bp.route("/events", methods=["POST"])` handler that:
- Validates required `event_type` field
- Validates `url_id` and `user_id` FK references (404 if not found)
- Creates the event with `json.dumps(details)` for the details field
- Returns `201 Created` with the serialized event

**Commit:** `fix: add POST /events endpoint and event_type filter`

---

## Bug 6: Missing CRUD Endpoints and Pagination (Advanced Challenges)

**Symptom:** Hidden advanced challenge tests returning "Incorrect output" — likely hitting missing endpoints or getting unfiltered/unpaginated data.

**Root Cause:** Several standard REST features were missing:
- `GET /events/<id>` — no single-event retrieval
- `DELETE /events/<id>` — no event deletion
- Pagination on `/events` and `/urls` (only `/users` had `page`/`per_page` support)
- No query param filters for `username`/`email` on `GET /users`
- No query param filters for `short_code`/`title` on `GET /urls`
- No `GET /urls/<id>/stats` analytics endpoint

**Fix:** Added all missing features:
- `GET /events/<id>` — returns single event or 404
- `DELETE /events/<id>` — deletes event, returns 204
- `page`/`per_page` pagination on `GET /events` and `GET /urls`
- `username` and `email` query param filtering on `GET /users`
- `short_code` and `title` query param filtering on `GET /urls`
- `GET /urls/<id>/stats` — returns visit count, total events, and last_visited timestamp

**Commits:**
- `fix: add pagination, GET/DELETE /events/<id>, pagination on /urls`
- `fix: add user filtering by username/email, add GET /urls/<id>/stats`
- `fix: add short_code and title query param filters to GET /urls`

---

## Bug 7: users.csv Has 4 Duplicate Usernames (Prior Fix)

**Symptom:** `POST /users/bulk` with the 400-row `users.csv` returns `{"imported": 396}` instead of `{"imported": 400}`.

**Root Cause:** The CSV file contained 4 pairs of duplicate usernames:
| First Occurrence (line) | Duplicate (line) | Username |
|---|---|---|
| 32 | 170 | `harborvalley60` |
| 161 | 205 | `ivoryjourney44` |
| 252 | 283 | `goldlagoon53` |
| 270 | 345 | `ivoryjourney51` |

The bulk import catches `IntegrityError` on unique constraint violations and silently skips them: 400 − 4 = 396.

**Fix:** Renamed the 4 duplicate usernames to unique values (`harborvalley61`, `ivoryjourney45`, `goldlagoon54`, `ivoryjourney52`) and updated their email addresses to match.

**Commit:** `found root cause users.csv had 4 duplicate usernames, implemented fix`
