FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen

COPY . .

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "-w", "8", "-b", "0.0.0.0:5000", "app:create_app()"]
