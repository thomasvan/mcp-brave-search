# Dockerfile for MCP Brave Search
# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv

# Set the working directory in the container
WORKDIR /app

# Copy the project descriptor files for dependency installation
COPY pyproject.toml uv.lock README.md LICENSE /app/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY src /app/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Create a minimal runtime image
FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy the virtual environment and source code from the builder stage
COPY --from=uv /root/.local /root/.local
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# Set PATH to use virtual environment by default
ENV PATH="/app/.venv/bin:$PATH"

# Set the entry point for the container
# API key should be passed at runtime using -e BRAVE_API_KEY=your_key_here
ENTRYPOINT ["mcp-brave-search"]