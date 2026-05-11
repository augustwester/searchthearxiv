FROM python:3.10.6-slim

RUN apt-get update && apt-get -y install zip unzip

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
COPY data/paper.py data/embed.py data/helpers.py ./
COPY data/setup_kaggle.py data/update_kaggle.py data/run.sh ./

RUN uv pip install --system --extra data .

CMD sh run.sh
