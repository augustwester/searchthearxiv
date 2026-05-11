FROM python:3.10.6-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
EXPOSE 8000

COPY pyproject.toml uv.lock ./
COPY app/app.py app/helpers.py app/paper.py ./
COPY app/static static/
COPY app/templates templates/

RUN uv pip install --system --extra app .

CMD gunicorn --bind 0.0.0.0:8000 app:app
