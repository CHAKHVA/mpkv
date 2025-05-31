FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install ruff \
    && pip install .

COPY . .

ENTRYPOINT ["python", "cli.py"] 