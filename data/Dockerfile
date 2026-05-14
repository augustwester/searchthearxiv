FROM python:3.11-slim

RUN apt-get update && apt-get -y install zip unzip

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
COPY data/paper.py data/embed.py data/helpers.py data/models.py ./
COPY data/setup_kaggle.py data/update_kaggle.py data/run.sh ./

ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --extra data --no-dev

CMD ["sh", "run.sh"]
