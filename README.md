# MeepleTime

MeepleTime is a self-hosted, mobile-first meeting availability app for private groups. Members join circles, mark which days they're **attending** or **hosting**, and the app surfaces which days are viable meetups based on configurable thresholds.

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python 3.12, FastAPI, SQLAlchemy    |
| Database  | PostgreSQL 16                       |
| Frontend  | Vue 3, Vuetify 3, Vite, Pinia       |
| Container | Docker, Docker Compose              |

## Quick Start (Docker Compose)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose v2

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd meepletime

# 2. Create your environment file
cp .env.example .env
# Edit .env and set a strong SECRET_KEY before running in production

# 3. Build and start all services
docker compose up --build

# 4. Open the app
#    Frontend: http://localhost
#    API docs: http://localhost:8000/docs
```

To stop:

```bash
docker compose down
```

To wipe the database volume as well:

```bash
docker compose down -v
```

## Configuration

All settings are controlled via environment variables. Copy `.env.example` to `.env` and adjust:

| Variable       | Default                                        | Description                                  |
|----------------|------------------------------------------------|----------------------------------------------|
| `DB_PASSWORD`  | `changeme`                                     | PostgreSQL password                          |
| `SECRET_KEY`   | `changeme-replace-in-production`               | JWT signing secret — **change in production**|
| `FRONTEND_URL` | `http://localhost`                             | Allowed CORS origin for the frontend         |

The backend also supports:

| Variable                       | Default | Description                          |
|--------------------------------|---------|--------------------------------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `10080` | JWT lifetime (7 days)                |
| `NOTIFICATION_DEBOUNCE_SECONDS`| `10`    | Notification debounce window         |

## Development Setup

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or use a .env file in backend/)
export DATABASE_URL=postgresql://meepletime:changeme@localhost:5432/meepletime
export SECRET_KEY=dev-secret

# Start a local Postgres (or point DATABASE_URL at your own instance)
docker run -d --name meepletime-db \
  -e POSTGRES_DB=meepletime \
  -e POSTGRES_USER=meepletime \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 postgres:16-alpine

# Run the API server (auto-reload)
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are available at <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server (proxies /api to http://localhost:8000)
npm run dev
```

The dev server is available at <http://localhost:5173>.

## API Overview

All endpoints are prefixed with the base URL (`http://localhost:8000`).

| Method   | Path                                              | Description                     |
|----------|---------------------------------------------------|---------------------------------|
| `GET`    | `/health`                                         | Health check                    |
| `POST`   | `/auth/register`                                  | Register a new user             |
| `POST`   | `/auth/token`                                     | Log in, receive JWT             |
| `GET`    | `/auth/me`                                        | Get current user profile        |
| `GET`    | `/circles`                                        | List your circles               |
| `POST`   | `/circles`                                        | Create a circle                 |
| `GET`    | `/circles/{id}`                                   | Get circle details              |
| `PATCH`  | `/circles/{id}`                                   | Update circle settings          |
| `DELETE` | `/circles/{id}`                                   | Delete a circle                 |
| `POST`   | `/circles/{id}/invite`                            | Regenerate invite token         |
| `GET`    | `/circles/join/{invite_token}`                    | Preview circle before joining   |
| `POST`   | `/circles/join`                                   | Join a circle via invite token  |
| `GET`    | `/circles/{id}/members`                           | List circle members             |
| `PATCH`  | `/circles/{id}/members/{user_id}`                 | Update a member's role          |
| `DELETE` | `/circles/{id}/members/{user_id}`                 | Remove a member                 |
| `GET`    | `/circles/{id}/availability`                      | Get availability for date range |
| `PUT`    | `/circles/{id}/availability/{date}`               | Set your availability for a day |
| `DELETE` | `/circles/{id}/availability/{date}`               | Clear your availability         |
| `GET`    | `/circles/{id}/viability`                         | Get viability for date range    |
| `GET`    | `/circles/{id}/overrides/{date}`                  | Get day override                |
| `PUT`    | `/circles/{id}/overrides/{date}`                  | Upsert day override             |
| `DELETE` | `/circles/{id}/overrides/{date}`                  | Delete day override             |
| `GET`    | `/circles/{id}/notes/{date}`                      | List notes for a day            |
| `POST`   | `/circles/{id}/notes/{date}`                      | Add a note to a day             |

Full interactive documentation with request/response schemas is available at `/docs` (Swagger UI) or `/redoc`.

## Architecture Overview

```
┌─────────────────────┐        ┌───────────────────────┐
│   Browser / Mobile  │◄──────►│  Frontend (Vue 3)     │
│                     │  :80   │  Nginx + Vite build   │
└─────────────────────┘        └──────────┬────────────┘
                                          │ /api → :8000
                               ┌──────────▼────────────┐
                               │  Backend (FastAPI)     │
                               │  Uvicorn :8000         │
                               └──────────┬────────────┘
                                          │ SQLAlchemy
                               ┌──────────▼────────────┐
                               │  PostgreSQL 16         │
                               │  (persistent volume)   │
                               └───────────────────────┘
```

- **Frontend** is a static Vue 3 + Vuetify 3 SPA served by Nginx. In development, Vite's dev server proxies `/api` requests to the backend.
- **Backend** is a FastAPI application with JWT authentication, role-based access control (Owner / Admin / Member), and an APScheduler-based notification system.
- **Database** schema is managed via [Alembic](https://alembic.sqlalchemy.org/) migrations stored in `backend/alembic/`.
- **Availability states** per user per day: empty (no preference) → attending → hosting (cycles on tap).
- **Viability** is computed server-side based on configurable thresholds per circle (minimum attendees, at least one host, etc.).
