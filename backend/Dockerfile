FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim


# On installe weasyprint via apt juste pour avoir toutes les dépendances C d'un coup
RUN apt-get update && apt-get install -y weasyprint && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies before copying the source code
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

EXPOSE 3000

CMD ["/app/.venv/bin/fastapi", "dev", "src/main.py", "--host", "0.0.0.0", "--port", "3000", "--proxy-headers"]