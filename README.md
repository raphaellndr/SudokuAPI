# SudokuArena API

![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-6.0.7-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

SudokuArenaAPI is a RESTful API built with Django and Django REST Framework to power my web-based Sudoku application, [SudokuArena](https://github.com/raphaellndr/sudoku-front-end). Users can register, solve or play Sudoku puzzles, track their stats, and compete on a leaderboard.

---

## 🚀 Features

- 🔐 JWT Authentication (via `djangorestframework-simplejwt`)
- 📧 Social login (Google via `django-allauth`)
- 🧩 Create, play, and solve Sudoku puzzles
- 📊 User statistics (daily, weekly, monthly, yearly)
- 🏆 Global leaderboard
- 🧠 Sudoku detection on an image
- 🗃️ Game history
- 🔄 Real-time support via Channels
- ⚙️ Admin dashboard and management tools

---

## 📦 Tech Stack

- **Backend:** Django 6.0.7 + DRF 3.17
- **Auth:** SimpleJWT, dj-rest-auth, django-allauth
- **API Schema:** drf-spectacular (OpenAPI 3.0)
- **Task Queue:** Celery + Redis
- **Real-time:** Channels + Daphne (ASGI)
- **Detection:** `opencv-python-headless`, `onnxruntime`, [sudoku-resolver](https://github.com/raphaellndr/sudoku-resolver)
- **Database:** PostgreSQL
- **Dev Tools:** pytest, factory-boy, ruff, mypy

---

## 🐳 Running with Docker Compose

You can run the entire development stack using Docker Compose:

### Create the env files:

The real env files are gitignored; copy the committed templates first (see
[Environment Variables](#-environment-variables)):

```bash
for f in .envs/.local/.*.example; do cp "$f" "${f%.example}"; done
```

### Build and start services:

```bash
docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up
```

Or in a single step:

```bash
docker compose -f docker-compose.local.yml up --build
```

### Tear down services:

```bash
docker compose -f docker-compose.local.yml down
```

---

## 📂 Project Structure

```
sudokuapi/
├── .envs/                         # Environment variable files (gitignored,
│   ├── .local/                    # only the *.example templates are committed)
│   └── .production/

├── app/                           # Django app modules
│   ├── authentication/            # Login, registration, tokens
│   ├── core/                      # Shared utilities and base logic
│   ├── game_record/               # Game sessions and scores
│   ├── sudoku/                    # Sudoku logic, tasks (solving, detection, cleaning),
│   │                              # consumers/routing (WebSockets), detection/ (OpenCV + ONNX)
│   └── user/                      # User profiles, stats, leaderboard

├── compose/                       # Docker Compose setups
│   ├── local/                     # Local dev configs and scripts
│   └── production/                # Production configs and scripts

├── config/                        # Django settings and Celery config
│   └── settings/                  # base.py, local.py, production.py

├── tests/                         # Test suite
├── docker-compose.local.yml       # Docker Compose for local dev
├── docker-compose.yml             # Docker Compose for production
└── manage.py                      # Django CLI entrypoint
```

---

## 🔐 Authentication Endpoints

| Method | Endpoint                      | Description            |
|--------|-------------------------------|------------------------|
| POST   | `/api/auth/register/`         | Register a new user   |
| POST   | `/api/auth/login/`            | Login with credentials|
| POST   | `/api/auth/logout/`           | Logout user           |
| POST   | `/api/auth/google/`           | Google login          |
| POST   | `/api/auth/token/`            | Obtain access token   |
| POST   | `/api/auth/token/refresh/`    | Refresh access token  |
| POST   | `/api/auth/token/verify/`     | Verify JWT token      |

---

## 🎮 Game Endpoints

| Method | Endpoint                          | Description                       |
|--------|-----------------------------------|-----------------------------------|
| GET    | `/api/games/`                     | List your games                   |
| POST   | `/api/games/`                     | Create a new game                 |
| GET    | `/api/games/{id}/`                | Retrieve a game                   |
| PUT    | `/api/games/{id}/`                | Update a game                     |
| PATCH  | `/api/games/{id}/`                | Partially update a game           |
| DELETE | `/api/games/{id}/`                | Delete a game                     |
| POST   | `/api/games/{id}/abandon/`        | Mark a game as abandonned         |
| POST   | `/api/games/{id}/complete/`       | Mark a game as completed          |
| POST   | `/api/games/{id}/stop/`           | Mark a game as stopped            |
| GET    | `/api/games/best_scores/`         | Fetch best scores                 |
| GET    | `/api/games/best_times/`          | Fetch best times                  |
| DELETE | `/api/games/bulk_delete/`         | Bulk delete games                 |
| GET    | `/api/games/recent/`              | Fetch recent games                |

All game endpoints require authentication and only ever expose your own records.

Query parameters on `GET /api/games/`: `status`, `won` (`true`/`1`/`yes`), `date_from`, `date_to`
(`YYYY-MM-DD`), plus `page` / `page_size` (max 100) pagination. `DELETE /api/games/bulk_delete/`
takes an `ids` list of at most 100 game ids.

---

## 🧩 Sudoku Endpoints

| Method | Endpoint                              | Description                     |
|--------|---------------------------------------|---------------------------------|
| GET    | `/api/sudokus/`                       | List your sudokus               |
| POST   | `/api/sudokus/`                       | Create a sudoku                 |
| GET    | `/api/sudokus/{id}/`                  | Retrieve a sudoku               |
| PUT    | `/api/sudokus/{id}/`                  | Update a sudoku                 |
| PATCH  | `/api/sudokus/{id}/`                  | Partially update a sudoku       |
| DELETE | `/api/sudokus/{id}/`                  | Delete a sudoku                 |
| GET    | `/api/sudokus/{id}/solution/`         | Get solution                    |
| DELETE | `/api/sudokus/{id}/solution/`         | Delete solution                 |
| POST   | `/api/sudokus/{id}/solver/`           | Start solving the sudoku        |
| DELETE | `/api/sudokus/{id}/solver/`           | Cancel solving task             |
| GET    | `/api/sudokus/{id}/status/`           | Get solver status               |
| POST   | `/api/sudokus/detect/`                | Start grid detection on an image |

Unlike the rest of the API, these endpoints are **open to anonymous users** for `create`, `list`,
`retrieve`, `solver`, `solution`, `status` and `detect`; only update and delete require
authentication. Anonymous sudokus are stored with no owner, served through a reduced serializer,
and periodically cleaned up by a Celery beat task. Every detail action checks ownership.

Query parameters on `GET /api/sudokus/`: `difficulties` (comma-separated, among `unknown`, `easy`,
`medium`, `hard`) and `limit` / `offset` pagination (default 5, max 25).

Solving is asynchronous: `POST /api/sudokus/{id}/solver/` returns
`{"status", "message", "sudoku_id", "task_id"}` immediately and the puzzle moves through the
`pending` → `running` → `completed` / `failed` / `aborted` statuses. Poll
`GET /api/sudokus/{id}/status/` or subscribe to the [status WebSocket](#-websocket-endpoints), then
read the result on `GET /api/sudokus/{id}/solution/`.

### 🧠 Grid detection flow

`POST /api/sudokus/detect/` is asynchronous too, and **the detected grid is never returned in the
HTTP response** — it is pushed over the detection WebSocket.

1. Generate a `session_id` (UUID) on the client and open
   `ws://<host>/ws/sudokus/detection/{session_id}/`.
2. `POST /api/sudokus/detect/` as `multipart/form-data`:

   | Field        | Required | Constraints                                              |
   |--------------|----------|----------------------------------------------------------|
   | `image`      | yes      | JPEG or PNG, ≤ 10 MB (and ≤ 25 MP once decoded)          |
   | `session_id` | yes      | the same UUID the WebSocket is connected with            |

   Returns `{"status": "success", "message": "Digit detection started", "task_id": "..."}`, or
   `400` (missing/oversized/unsupported image, missing or non-UUID `session_id`), `429` (rate
   limit) or `500`.
3. The task broadcasts `detection_status_update` events on the WebSocket: `pending` → `running` →
   `completed` (with `grid`) or `failed` (with `message`). The grid is an 81-character string read
   left-to-right, top-to-bottom, `0` meaning an empty or uncertain cell.

---

## 🔌 WebSocket Endpoints

Served by Channels; `daphne` sits first in `INSTALLED_APPS`, so `runserver` handles WebSockets too.

| Endpoint                              | Description                    |
|---------------------------------------|--------------------------------|
| `ws/sudokus/{sudoku_id}/status/`      | Solver status updates          |
| `ws/sudokus/detection/{session_id}/`  | Grid detection updates         |

- **Solver channel** — the server pushes
  `{"type": "status_update", "sudoku_id": "<uuid>", "status": "<status>"}`. The client can also ask
  for the current value by sending `{"type": "get_status", "sudoku_id": "<uuid>"}`. Statuses:
  `created`, `pending`, `running`, `completed`, `failed`, `aborted`, `invalid`.
- **Detection channel** — the server pushes
  `{"type": "detection_status_update", "status": "<status>", "grid": <string|null>, "message": <string|null>}`.
  Statuses: `pending`, `running`, `completed`, `failed`.

---

## 👤 User Endpoints

| Method | Endpoint                                         | Description                   |
|--------|--------------------------------------------------|-------------------------------|
| GET    | `/api/users/{id}/`                               | Get user info                 |
| GET    | `/api/users/{id}/games/`                         | Get user's games              |
| GET    | `/api/users/{id}/stats/`                         | Get user's stats              |
| GET    | `/api/users/{id}/stats/daily/`                   | Daily stats                   |
| GET    | `/api/users/{id}/stats/weekly/`                  | Weekly stats                  |
| GET    | `/api/users/{id}/stats/monthly/`                 | Monthly stats                 |
| GET    | `/api/users/{id}/stats/yearly/`                  | Yearly stats                  |
| GET    | `/api/users/me/`                                 | Get current user              |
| PUT    | `/api/users/me/`                                 | Update current user           |
| PATCH  | `/api/users/me/`                                 | Partially update user         |
| GET    | `/api/users/me/games/`                           | Get current user's games      |
| GET    | `/api/users/me/stats/`                           | Get current user's stats      |
| GET    | `/api/users/me/stats/daily/`                     | Daily stats                   |
| GET    | `/api/users/me/stats/weekly/`                    | Weekly stats                  |
| GET    | `/api/users/me/stats/monthly/`                   | Monthly stats                 |
| GET    | `/api/users/me/stats/yearly/`                    | Yearly stats                  |
| POST   | `/api/users/me/stats/refresh/`                   | Refresh cached stats          |
| GET    | `/api/users/stats/leaderboard/`                  | Global leaderboard            |

Only the leaderboard is public; everything else requires authentication. `{id}` is a user UUID and
`me` is accepted as an alias for the current user on the stats and games routes. Game history
(`/games/`) is restricted to the owner (or staff) and returns `403` otherwise, while stats routes
are readable for any user id. Stats are cached for 5 minutes (10 for the leaderboard) —
`POST /api/users/me/stats/refresh/` queues a recomputation of your own stats.

Query parameters: `date` on daily stats, `year` + `week` on weekly, `year` + `month` on monthly,
`year` on yearly, `limit` (max 100) on the leaderboard, and `status` + `page` / `page_size` on the
games routes.

---

## 🚦 Rate Limits

DRF throttling is enabled globally (`config/settings/base.py`); exceeding a rate returns `429`:

| Scope                                | Rate     |
|--------------------------------------|----------|
| Anonymous (default)                  | 60/min   |
| Authenticated (default)              | 240/min  |
| `POST /api/sudokus/{id}/solver/`     | 10/min   |
| `POST /api/sudokus/detect/`          | 10/min   |

---

## 📄 Environment Variables

Environment variables are organized by service in the `.envs/` folder. The real files are
gitignored — only the `*.example` templates are committed, so copy them before the first run:

```
.envs/
├── .local/
│   ├── .django      # DJANGO_SETTINGS_MODULE, DJANGO_CORS_ALLOWED_ORIGINS, GOOGLE_CLIENT_ID/SECRET
│   ├── .postgres    # POSTGRES_HOST/PORT/DB/USER/PASSWORD, locale
│   └── .redis       # REDIS_URL
└── .production/     # same three files, plus DJANGO_SECRET_KEY and DJANGO_ALLOWED_HOSTS
```

```bash
for f in .envs/.local/.*.example; do cp "$f" "${f%.example}"; done
```

Do the same in `.envs/.production/` when deploying. The compose files reference these files with
`env_file`; `docker-compose.yml` additionally loads `.envs/.env`.

> 📝 Docker Compose automatically injects variables from these files into each service container.

---

## 🌐 API Documentation

- Interactive documentation: `http://localhost:8000/api/docs/`
- YAML docs: `http://localhost:8000/api/schema/`

---

## 🧪 Running Tests

If you're running tests inside Docker:

```bash
docker compose -f docker-compose.local.yml exec web pytest
```

Or locally, with the Poetry environment:

```bash
poetry run pytest
```

---

## 📤 Production

The production stack lives in `docker-compose.yml` (built from `compose/production/`) and runs on
`config.settings.production`, which enables the `django-redis` cache, HTTPS redirects, secure
cookies and HSTS. Install the dependencies listed under the `production` group in
`[dependency-groups]` and fill in `.envs/.production/`: `DJANGO_SECRET_KEY` is mandatory (the
settings module refuses to start without it) and `DJANGO_ALLOWED_HOSTS` must list the real hosts,
otherwise every request is rejected.

```bash
docker compose up --build
```

> ⚠️ The production entrypoint still starts the app with `manage.py runserver`; put a proper ASGI
> server (Daphne/Uvicorn) behind a reverse proxy before exposing it — WebSockets rule out a plain
> WSGI server such as Gunicorn.

---

## 📃 License

This project is licensed under the MIT License.

---

## 🙋 Author

**Raphael Landure**  
📧 [raph.landure@gmail.com](mailto:raph.landure@gmail.com)  
🔗 [GitHub](https://github.com/raphaellndr)
