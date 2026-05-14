FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
EXPOSE 8000

COPY pyproject.toml uv.lock ./
COPY app/app.py app/helpers.py app/paper.py app/models.py ./
COPY app/static static/
COPY app/templates templates/

ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --extra app --no-dev

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
