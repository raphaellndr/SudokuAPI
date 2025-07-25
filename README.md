# SudokuArena API

![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1.6-green)
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

- **Backend:** Django 5.1.6 + DRF
- **Auth:** SimpleJWT, dj-rest-auth, django-allauth
- **API Schema:** drf-spectacular (OpenAPI 3.0)
- **Task Queue:** Celery + Redis
- **Detection:** `opencv-python-headless`, `onnxruntime`, [sudoku-resolver](https://github.com/raphaellndr/sudoku-resolver)
- **Database:** PostgreSQL
- **Dev Tools:** pytest, factory-boy, ruff, mypy

---

## 🐳 Running with Docker Compose

You can run the entire development stack using Docker Compose:

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
├── .envs/                         # Environment variable files
│   ├── .local/                    # Local development env vars
│   └── .production/               # Production env vars

├── app/                           # Django app modules
│   ├── authentication/            # Login, registration, tokens
│   ├── core/                      # Shared utilities and base logic
│   ├── game_record/               # Game sessions and scores
│   ├── sudoku/                    # Sudoku logic, tasks (solving, detection, cleaning)
│   └── user/                      # User profiles, stats, leaderboard

├── compose/                       # Docker Compose setups
│   ├── local/                     # Local dev configs and scripts
│   └── production/                # Production configs and scripts

├── config/                        # Django settings and Celery config
│   └── settings/                  # base.py, local.py, production.py

├── tests/                         # Test suite
├── docker-compose.local.yml       # Docker Compose for local dev
├── docker-compose.production.yml  # Docker Compose for production
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
| GET    | `/api/games/`                     | List all games                    |
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

---

## 🧩 Sudoku Endpoints

| Method | Endpoint                              | Description                     |
|--------|---------------------------------------|---------------------------------|
| GET    | `/api/sudokus/`                       | List all sudokus                |
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
| POST   | `/api/sudokus/detect/`                | Grid detection                  |

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

---

## 📄 Environment Variables

Environment variables are organized by service in the `.envs/` folder:

```
.envs/
├── .local/
│   ├── .django      # Django-related variables (e.g. DJANGO_SETTINGS_MODULE, GOOGLE_CLIENT_ID)
│   ├── .postgres    # PostgreSQL configuration (e.g. POSTGRES_DB, POSTGRES_USER)
│   └── .redis       # Redis configuration (e.g. REDIS_URL)
├── .production/
    ...
```

Make sure your docker compose files references these files using `env_file`.

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

---

## 📤 Production

For production, use the dependencies listed under the `[tool.poetry.group.production]` section, and configure:

- **Gunicorn** for WSGI
- **Django Redis** for caching
- **Whitenoise** for static file serving
- **Proper environment variables** and secure settings

---

## 📃 License

This project is licensed under the MIT License.

---

## 🙋 Author

**Raphael Landure**  
📧 [raph.landure@gmail.com](mailto:raph.landure@gmail.com)  
🔗 [GitHub](https://github.com/raphaellndr)
