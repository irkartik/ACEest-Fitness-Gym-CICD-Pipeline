[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=irkartik_ACEest-Fitness-Gym-CICD-Pipeline&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=irkartik_ACEest-Fitness-Gym-CICD-Pipeline)

# ACEest Fitness & Gym — CI/CD Pipeline

A Flask REST API for ACEest Functional Fitness, with a full CI/CD pipeline powered by **Jenkins** and **GitHub Actions**. The application manages fitness programs, client profiles, workouts, and progress tracking — all containerized with Docker for portable, consistent deployments.

---

## Project Structure

```
├── app/
│   ├── main.py              # Flask REST API (entry point)
│   └── requirements.txt     # Python dependencies
├── tests/
│   └── test_main.py         # Pytest suite (19 tests)
├── Dockerfile               # Docker image definition
├── Jenkinsfile              # Jenkins declarative pipeline
├── .github/
│   └── workflows/
│       └── main.yml         # GitHub Actions CI/CD workflow
├── HistoricalVersions/      # Legacy tkinter app versions
└── Screenshots/             # App screenshots
```

---

## Local Setup & Execution

### Prerequisites

- Python 3.9+ (3.12 recommended)
- pip
- Docker (for containerized runs)

### 1. Clone the repository

```bash
git clone https://github.com/irkartik/ACEest-Fitness-Gym-CICD-Pipeline.git
cd ACEest-Fitness-Gym-CICD-Pipeline
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r app/requirements.txt
```

### 4. Run the application

```bash
python app/main.py
```

The API starts at `http://localhost:5000`. Verify with:

```bash
curl http://localhost:5000/health
```

### 5. Run with Docker

```bash
docker build -t aceest-fitness .
docker run -p 5000:5000 aceest-fitness
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/programs` | List all fitness programs |
| GET | `/api/programs/<name>` | Get a specific program |
| GET | `/api/site-metrics` | Gym capacity & metrics |
| GET | `/api/clients` | List all clients |
| POST | `/api/clients` | Create a client |
| GET | `/api/clients/<name>` | Get client details |
| PUT | `/api/clients/<name>` | Update a client |
| DELETE | `/api/clients/<name>` | Delete a client |
| GET | `/api/clients/<name>/workouts` | List client workouts |
| POST | `/api/clients/<name>/workouts` | Log a workout |
| GET | `/api/clients/<name>/progress` | List weekly progress |
| POST | `/api/clients/<name>/progress` | Log weekly adherence |

---

## Running Tests

### Locally (via venv)

```bash
python -m pytest tests/ -v
```

### Inside Docker

```bash
docker build -t aceest-fitness:test .
docker run --rm aceest-fitness:test python -m pytest tests/ -v
```

The test suite contains **19 tests** covering health checks, program endpoints, full client CRUD, workout logging, progress tracking, and input validation.

---

## CI/CD Pipeline Overview

This project uses a **dual CI/CD** setup — Jenkins for the primary build server and GitHub Actions for automated pipeline-on-push.

### Jenkins Pipeline (`Jenkinsfile`)

Triggered manually or via GitHub webhook. Runs on the Jenkins server with access to Docker.

```
Checkout → Setup Python Env → Lint (flake8) → Tests (pytest + JUnit) → Docker Build
```

| Stage | Purpose |
|-------|---------|
| **Checkout** | Pulls latest code from GitHub |
| **Setup Python Environment** | Creates a clean venv, installs dependencies |
| **Quality Gate — Lint** | Runs `flake8` static analysis; fails on errors |
| **Quality Gate — Tests** | Runs `pytest` with JUnit XML reporting for Jenkins UI |
| **Docker Build** | Builds the image tagged with build number + `latest` |

**Setup:** Create a Pipeline project in Jenkins → set SCM to the GitHub repo → Script Path: `Jenkinsfile`.

### GitHub Actions (`.github/workflows/main.yml`)

Triggered automatically on every **push** or **pull request** to `main`.

```
Build & Lint → Docker Image Assembly → Automated Testing (inside container)
```

| Job | Purpose |
|-----|---------|
| **Build & Lint** | Installs deps on Python 3.12, runs `flake8` |
| **Docker Image Assembly** | Builds the Docker image (depends on lint passing) |
| **Automated Testing** | Runs `pytest` inside the Docker container to verify stability |

The three jobs run sequentially — each depends on the previous one passing. This ensures code quality, image integrity, and runtime correctness before any merge.

---

## Tech Stack

- **Backend:** Flask 3.1.0, SQLite
- **Testing:** pytest 8.3.4, flake8
- **Containerization:** Docker (python:3.12-slim)
- **CI/CD:** Jenkins, GitHub Actions
