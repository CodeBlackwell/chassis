set dotenv-load := true

# list recipes
default:
    @just --list

# install deps (base + dev)
setup:
    uv sync

# run all tests
test:
    uv run pytest -q

# lint + typecheck
lint:
    uv run ruff check lib app config tests scripts
    uv run mypy lib app config

# auto-fix lint
fix:
    uv run ruff check --fix lib app config tests scripts

# start backing services (Qdrant) for the qdrant-local profile
services:
    docker compose up -d

# stop services
down:
    docker compose down

# run the dashboard locally (four-tab Gradio app on :8000)
dev:
    -lsof -ti :8000 | xargs kill -9 2>/dev/null
    uv run --extra ui python -m app.ui

# run the JSON API locally (FastAPI on :8001 — POST /ask, GET /trace, GET /health)
api:
    -lsof -ti :8001 | xargs kill -9 2>/dev/null
    uv run --extra api python -m app.api

# Ralph solo: one agent iterating a PRD bundle (prds/<slug>)
ralph target iters="10":
    uv run python scripts/ralph.py {{target}} {{iters}}

# Ralph's Army: parallel agents in gated waves
army target:
    uv run python scripts/ralph.py {{target}} --army

# build the app image
build:
    docker build -t chassis:latest .

# deploy: push + ssh + pull + rebuild (host/dir from env)
deploy:
    git push
    ssh {{ env_var_or_default("DEPLOY_HOST", "root@localhost") }} 'cd {{ env_var_or_default("DEPLOY_DIR", "/opt/chassis") }} && git pull && docker compose -f docker-compose.prod.yml up -d --build'

# tail production logs
logs:
    ssh {{ env_var_or_default("DEPLOY_HOST", "root@localhost") }} 'cd {{ env_var_or_default("DEPLOY_DIR", "/opt/chassis") }} && docker compose -f docker-compose.prod.yml logs -f'

# remove caches and run artifacts
clean:
    rm -rf runs .pytest_cache .mypy_cache .ruff_cache
