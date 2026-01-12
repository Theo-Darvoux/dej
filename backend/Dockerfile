# Use the official Python image with uv pre-installed
# Using bookworm (not slim) which includes common system libraries
FROM ghcr.io/astral-sh/uv:python3.14-bookworm

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a different filesystem
ENV UV_LINK_MODE=copy

# Install dependencies in a separate layer for better caching
# This layer will only rebuild when dependencies change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the project source code
COPY . .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set PYTHONPATH for the application
ENV PYTHONPATH=/app

# Run the FastAPI application in development mode
CMD ["fastapi", "dev", "src/main.py", "--host", "0.0.0.0", "--port", "3000", "--proxy-headers"]