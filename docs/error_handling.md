# Error Handling

This document describes how the URL Shortener API handles errors. All error responses are returned as JSON — the application never returns HTML error pages.

## Response Format

All error responses follow a consistent structure:

```json
{
  "error": "Human-readable error message",
  "details": {
    "field_name": "Field-specific error description"
  }
}
```

The `details` field is only present when there are field-level validation errors.

---

## HTTP Status Codes

### 400 Bad Request

**When:** The request body is missing, not valid JSON, or missing required fields.

**Example — missing JSON body:**

```bash
curl -X POST http://localhost:5000/users -d 'not json'
```

```json
{ "error": "Request body must be JSON" }
```

**Example — missing file in bulk upload:**

```bash
curl -X POST http://localhost:5000/users/bulk
```

```json
{ "error": "No file provided. Send a CSV as multipart form field named 'file'." }
```

---

### 404 Not Found

**When:** A requested resource does not exist, or an unknown route is accessed.

**Example — unknown user ID:**

```bash
curl http://localhost:5000/users/999999
```

```json
{ "error": "User not found" }
```

**Example — unknown URL ID:**

```bash
curl http://localhost:5000/urls/999999
```

```json
{ "error": "URL not found" }
```

**Example — unknown route:**

```bash
curl http://localhost:5000/nonexistent
```

```json
{ "error": "Not found" }
```

**Example — user_id does not exist when creating a URL:**

```bash
curl -X POST http://localhost:5000/urls \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999999, "original_url": "https://example.com"}'
```

```json
{ "error": "User not found" }
```

---

### 405 Method Not Allowed

**When:** An HTTP method is used that the endpoint does not support.

**Example:**

```bash
curl -X DELETE http://localhost:5000/users/1
```

```json
{ "error": "Method not allowed" }
```

---

### 409 Conflict

**When:** A unique constraint is violated (duplicate username or email).

**Example — duplicate username:**

```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "existinguser", "email": "new@example.com"}'
```

```json
{ "error": "Username already exists" }
```

**Example — duplicate email:**

```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "existing@example.com"}'
```

```json
{ "error": "Email already exists" }
```

---

### 410 Gone

**When:** A short URL exists but has been deactivated (`is_active = false`).

**Example:**

```bash
curl http://localhost:5000/abc123
```

```json
{ "error": "URL is deactivated" }
```

---

### 422 Unprocessable Entity

**When:** The request body is valid JSON but contains invalid field values.

**Example — invalid username (integer instead of string):**

```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": 123, "email": "test@example.com"}'
```

```json
{
  "error": "Validation failed",
  "details": {
    "username": "Invalid username. Must be a non-empty alphanumeric string (max 150 chars)."
  }
}
```

**Example — invalid URL format:**

```bash
curl -X POST http://localhost:5000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "not-a-url"}'
```

```json
{
  "error": "Invalid URL format",
  "details": {
    "original_url": "Must be a valid URL (e.g. https://example.com)"
  }
}
```

---

### 500 Internal Server Error

**When:** An unexpected error occurs. The global error handler ensures a JSON response is returned instead of an HTML traceback.

```json
{ "error": "Internal server error" }
```

This handler prevents the test suite from encountering HTML responses and ensures clients always receive machine-parseable JSON.
