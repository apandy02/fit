# Fit

A comprehensive fitness assistant that combines LLM-powered nutrition analysis with fitness tracking. Leverage data from your fitness trackers along with LMP (language model programs) grounded in scientific literature to help you get (or stay) fit.

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Setup](#setup)
- [Database (Postgres) & Migrations](#database-postgres--migrations)
- [Running the Backend](#running-the-backend)
- [Run with Docker](#run-with-docker)
- [Sanity Checks](#sanity-checks)
- [Technology Stack](#technology-stack)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Overview

The project currently provides:
- FastAPI-based JSON backend (`src/fit/backend`)
- LLM-powered nutrition, performance, and rest analysis modules (`src/fit/ai`)
- Fitness tracker integrations (Whoop/Fitbit) with OAuth endpoints

Note: The previous FastHTML-based web UI has been deprecated. A new frontend (likely React Native in TypeScript) is planned but not yet implemented.

## Technology Stack

- Python 3.10+
- FastAPI (backend API)
- Pydantic (data models and validation)
- SQLite (database)
- ell (language model programming and evals) for the analysis modules under `src/fit/ai`
- Tooling: uv, ruff, unittest, coverage
- Docker

Planned frontend:
- React Native (TypeScript) – not implemented yet

## Getting Started

### Setup
1. Install uv: see `https://docs.astral.sh/uv/getting-started/installation/`
2. Clone the repository:
   ```bash
   git clone git@github.com:apandy02/fit.git
   cd fit
   ```
3. Create a virtual environment and sync dependencies:
   ```bash
   uv sync
   ```

## Running the Backend

From the project root:
```bash
uv run -m uvicorn fit.backend.main:app --reload --host 0.0.0.0 --port 5002
```

### Database (Postgres) & Migrations

This backend now uses PostgreSQL.

- Set the database URL in your environment (example):
  ```bash
  export FIT_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/fit"
  ```
- Initialize the schema with Alembic:
  ```bash
  uv run alembic -c alembic.ini upgrade head
  ```

Notes:
- Alembic migration files live in `db/migrations/`. The config is `alembic.ini`.
- The app reads `FIT_DATABASE_URL` both for runtime and migrations.
- For quick local testing, you can start Postgres via Docker:
  ```bash
  docker run --name fit-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
  docker exec -it fit-pg psql -U postgres -c 'CREATE DATABASE fit;'
  export FIT_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/fit"
  uv run alembic -c alembic.ini upgrade head
  ```

Required environment variable:
- `FIT_DATABASE_URL` (Postgres connection string; see above)



## Run with Docker

Build the image (from project root):
```bash
docker build -t fit-backend:latest .
```

Run with Postgres and secrets (from project root):
```bash
docker run --rm -p 5002:5002 \
  -e FIT_DATABASE_URL="$FIT_DATABASE_URL" \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  fit-backend:latest

Notes:
- Do not put secrets in the `Dockerfile`; pass them via `-e`, an `env_file`, or your host platform’s secret management.
- The server listens on `$PORT` (defaults to `5002`).

Render (when ready):
- Create a Docker service, point it at this repo.
- Add environment variables (e.g., `OPENAI_API_KEY`).
- Mount a persistent disk or use a managed Postgres instance; set `FIT_DATABASE_URL` accordingly.
- Render sets `$PORT` automatically; the image uses it at runtime.

## Sanity Checks

With the backend running, you can exercise most endpoints (excluding OAuth-dependent flows) using the included script:
```bash
BASE=http://localhost:5002 src/fit/backend/sanity_checks.sh
```

Notes:
- The script logs in (user_id 42) to obtain an access token and then runs nutrition, supplements, water, kitchen, profile, and onboarding flows.
- Image-based endpoints are skipped unless `FOOD_IMG` or `KITCHEN_IMG` point to existing files.
- Performance/Rest endpoints that require linked trackers are skipped.

## Testing

Run the test suite:
```bash
uv run -m unittest discover -v
```

Run with coverage:
```bash
uv run -m coverage run -m unittest discover -v
uv run -m coverage report
uv run -m coverage html
```

## Project Structure

```
src/fit/
├── backend/         # FastAPI app, routes, models, services, trackers
├── ai/              # LLM-powered analysis modules (nutrition, performance, rest)
├── trackers/        # Tracker SDKs and managers (used by backend)
└── utils/           # Shared utilities
```

Each module contains its own code and tests as applicable.

## Contributing

1. Ensure all tests pass: `uv run -m unittest discover -v`
2. Lint/fix: `uv run ruff check . --fix`
3. Follow the existing code structure and documentation patterns
4. Submit a pull request

## Builds and packaging

This project is packaged and run using Docker and uv.

Build the image from the project root:
```bash
docker build -t fit-backend:latest .
```

Run it locally (see details in "Run with Docker"):
```bash
docker run --rm -p 5002:5002 fit-backend:latest
```

Publish to a registry (example):


Render deployment (when ready):


Notes:
- uv is used inside the container; dependencies are locked by `uv.lock`.
- Do not bake secrets into the image; pass them via environment variables or your platform’s secret manager.
