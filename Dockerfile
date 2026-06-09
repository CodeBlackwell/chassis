# CHASSIS app image. uv-based, non-root. Install only the adapter extras your
# deployed profile needs via the EXTRAS build arg (keeps the image lean).
#   docker build --build-arg EXTRAS="embeddings-sbert,vectorstore-qdrant" -t chassis .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

ARG EXTRAS="embeddings-sbert,vectorstore-qdrant"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev $(echo ",$EXTRAS" | sed 's/,/ --extra /g')

COPY lib/ lib/
COPY app/ app/
COPY config/ config/
COPY scripts/ scripts/

RUN useradd -m -u 1000 chassis && mkdir -p /app/runs && chown -R chassis /app/runs
USER chassis

EXPOSE 8000
# The Gradio dashboard (app.ui) is the Wave 2 entrypoint; until then this image
# is built/validated as deployment scaffolding.
CMD ["uv", "run", "python", "-m", "app.ui"]
