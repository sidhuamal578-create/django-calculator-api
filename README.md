# Calculator Backend API

Django + Django REST Framework backend for a simple calculator app.

This repository is **backend only**. A separate React frontend (built by another developer) consumes these REST APIs.

---

## Features

- Evaluate mathematical expressions on the server
- Persist calculation history in SQLite (via Django ORM)
- List, retrieve, delete, and clear history
- Safe expression evaluation (no `eval()` on user input)
- CORS configured for React development servers
- Django admin for viewing history
- Automated tests
- Environment-based production settings

---

## Technology stack

- Python 3
- Django
- Django REST Framework
- SQLite (local development)
- Optional PostgreSQL (production via environment variables)
- django-cors-headers
- python-dotenv

---

## Project setup

### 1. Open the project

```bash
cd Job
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables

```powershell
copy .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

Local defaults work for development. **Always** set a strong `DJANGO_SECRET_KEY` before production.

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create an admin user (optional)

```bash
python manage.py createsuperuser
```

Admin UI: http://127.0.0.1:8000/admin/

### 7. Start the Django development server

```bash
python manage.py runserver
```

**API base URL:**

```text
http://127.0.0.1:8000/api/
```

Opening `/api/` in a browser returns a JSON discovery document of available endpoints.

---

## Environment variables

| Variable | Purpose | Local default |
|----------|---------|---------------|
| `DJANGO_SECRET_KEY` | Django secret | insecure dev fallback (blocked when `DEBUG=False`; production needs ≥ 50 chars) |
| `DJANGO_DEBUG` | Debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Allowed React origins | CRA + Vite localhost ports |
| `CORS_ALLOW_ALL_ORIGINS` | Allow all origins | `False` (never enable in production) |
| `CSRF_TRUSTED_ORIGINS` | Trusted HTTPS origins for admin | empty |
| `DATABASE_URL` | Optional DB URL (`postgres://...`) | unset → SQLite |
| `DB_ENGINE` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Alt production DB config | unused for SQLite |

---

## API contract

All JSON responses follow one of these shapes.

**Success with payload:**

```json
{
  "success": true,
  "data": { }
}
```

**Success with message only** (delete / clear):

```json
{
  "success": true,
  "message": "..."
}
```

**Error:**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_EXPRESSION",
    "message": "Invalid mathematical expression."
  }
}
```

Use header: `Content-Type: application/json`

---

## Endpoints

### GET `/api/`

API discovery / health-style overview.

### POST `/api/calculate/`

Evaluate an expression on the backend and store it.

**Request:**

```json
{
  "expression": "25 + 10 * 2"
}
```

**Response — `201 Created`:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "expression": "25 + 10 * 2",
    "result": 45.0,
    "created_at": "2026-09-22T12:00:00.000000Z"
  }
}
```

The React app must **not** compute the final result itself.

### GET `/api/history/`

List history, newest first.

**Response — `200 OK`:**

```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "expression": "100 / 5",
      "result": 20.0,
      "created_at": "2026-09-22T12:05:00.000000Z"
    },
    {
      "id": 1,
      "expression": "25 + 10 * 2",
      "result": 45.0,
      "created_at": "2026-09-22T12:00:00.000000Z"
    }
  ]
}
```

### GET `/api/history/<id>/`

**Response — `200 OK`:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "expression": "25 + 10 * 2",
    "result": 45.0,
    "created_at": "2026-09-22T12:00:00.000000Z"
  }
}
```

**Not found — `404`:**

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Calculation not found."
  }
}
```

### DELETE `/api/history/<id>/`

**Response — `200 OK`:**

```json
{
  "success": true,
  "message": "Calculation deleted successfully."
}
```

### DELETE `/api/history/clear/`

**Response — `200 OK`:**

```json
{
  "success": true,
  "message": "Calculation history cleared successfully."
}
```

---

## Supported operations

| Operation | Example |
|-----------|---------|
| Addition | `10 + 5` |
| Subtraction | `20 - 8` |
| Multiplication | `7 * 6` |
| Division | `100 / 4` |
| Decimals | `10.5 + 2.5` |
| Parentheses | `(10 + 5) * 2` |
| Negatives | `-5 + 10`, `-(2 + 3)` |

Operator precedence follows normal math rules (`*` / `/` before `+` / `-`).

---

## Error examples

| Status | Code | When |
|--------|------|------|
| `400` | `INVALID_EXPRESSION` | Empty, malformed, invalid chars, malicious input |
| `400` | `DIVISION_BY_ZERO` | Division by zero |
| `404` | `NOT_FOUND` | Unknown calculation id |
| `405` | `METHOD_NOT_ALLOWED` | Wrong HTTP method |
| `500` | `SERVER_ERROR` | Unexpected failure (no traceback leaked) |

Malicious payloads such as `__import__("os")`, `exec(...)`, `open(...)`, and `globals()` are rejected and never executed.

---

## CORS / React integration

Default allowed origins (development):

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

Production example:

```env
CORS_ALLOWED_ORIGINS=https://your-frontend.example.com
CORS_ALLOW_ALL_ORIGINS=False
```

Do **not** set `CORS_ALLOW_ALL_ORIGINS=True` in production.

### Example fetch — calculate

```javascript
fetch("http://127.0.0.1:8000/api/calculate/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    expression: "25 + 10",
  }),
})
  .then((response) => response.json())
  .then((payload) => {
    // payload.success === true
    // payload.data.result === 35
    console.log(payload);
  });
```

### Example fetch — history

```javascript
fetch("http://127.0.0.1:8000/api/history/")
  .then((response) => response.json())
  .then((payload) => console.log(payload.data));
```

### Example fetch — clear history

```javascript
fetch("http://127.0.0.1:8000/api/history/clear/", {
  method: "DELETE",
})
  .then((response) => response.json())
  .then((payload) => console.log(payload.message));
```

---

## Testing

```bash
python manage.py test
```

---

## Project structure

```text
.
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── calculator/
    ├── admin.py
    ├── apps.py
    ├── exceptions.py
    ├── models.py
    ├── serializers.py
    ├── services.py
    ├── urls.py
    ├── views.py
    └── tests.py
```

Business logic lives in `calculator/services.py`. Views handle HTTP only.

---

## Production setup (hosting)

This backend is prepared for deployment. **Hosting itself is a separate step** — do not put real secrets in this repository.

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` already includes production packages:

- `psycopg[binary]` — PostgreSQL driver
- `gunicorn` — WSGI server
- `whitenoise` — static files
- Django / DRF / django-cors-headers / python-dotenv

### 2. Set environment variables on the host

| Variable | Required in production | What to set |
|----------|------------------------|-------------|
| `DJANGO_SECRET_KEY` | **Yes** | Long random string (**≥ 50 characters**). Never commit the real value. |
| `DJANGO_DEBUG` | **Yes** | `False` |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | Your API domain(s), comma-separated (example: `api.example.com`) |
| `CORS_ALLOWED_ORIGINS` | **Yes** (once React is live) | Your deployed React origin(s), e.g. `https://app.example.com` |
| `CORS_ALLOW_ALL_ORIGINS` | **Yes** | Must stay `False` |
| `DATABASE_URL` **or** `DB_*` | Recommended | PostgreSQL connection (see below) |
| `CSRF_TRUSTED_ORIGINS` | If using HTTPS admin | `https://YOUR-API-DOMAIN` |
| `DJANGO_SECURE_SSL_REDIRECT` | Usually yes | `True` behind HTTPS (set `False` only if the platform handles redirects and conflicts) |

**Insert your React production URL here after the frontend is deployed:**

```env
CORS_ALLOWED_ORIGINS=https://YOUR-REACT-FRONTEND-DOMAIN
CORS_ALLOW_ALL_ORIGINS=False
```

Do not invent domains in advance — set this when you know the real frontend URL.

### 3. Database

- **Local:** SQLite (default) — no extra config.
- **Production:** Prefer PostgreSQL.

Option A — `DATABASE_URL` (common on PaaS):

```env
DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/NAME
```

Option B — discrete variables:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432
```

### 4. Migrate, collect static files, start

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

WSGI entrypoint: `config.wsgi:application`  
ASGI entrypoint: `config.asgi:application`

Static files are served via **WhiteNoise** (`STATIC_ROOT` + `collectstatic`).

### 5. API base URL after hosting

```text
https://YOUR-API-DOMAIN/api/
```

React should call that base URL (not localhost) once both apps are deployed.

### 6. Production security notes

When `DJANGO_DEBUG=False`, Django enables:

- `SECURE_SSL_REDIRECT` (configurable)
- Secure session/CSRF cookies
- HSTS (`SECURE_HSTS_SECONDS`)
- `SECURE_PROXY_SSL_HEADER` for reverse-proxy TLS

`SECURE_HSTS_PRELOAD` stays `False` by default on purpose (browser preload is hard to undo). Set `DJANGO_SECURE_HSTS_PRELOAD=True` only if you intentionally want preload.

`python manage.py check --deploy` should be run with production env vars set.

---

## Quick endpoint cheat sheet

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/` | API discovery |
| `POST` | `/api/calculate/` | Evaluate expression |
| `GET` | `/api/history/` | List history |
| `GET` | `/api/history/<id>/` | Get one calculation |
| `DELETE` | `/api/history/<id>/` | Delete one |
| `DELETE` | `/api/history/clear/` | Clear all history |

Base URL (local): `http://127.0.0.1:8000/api/`
