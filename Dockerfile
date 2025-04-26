# Dockerfile for MCP Brave Search
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# Install necessary build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy all necessary files for building the package
COPY pyproject.toml uv.lock README.md LICENSE /app/
COPY src /app/src

# Create virtual environment and install dependencies
RUN uv venv /app/.venv \
    && . /app/.venv/bin/activate \
    && uv pip install -e .

# Create final image
FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy the virtual environment and source code from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set PATH to use virtual environment by default
ENV PATH="/app/.venv/bin:$PATH"

# Set the entry point for the container
# API key should be passed at runtime using -e BRAVE_API_KEY=your_key_here
ENTRYPOINT ["mcp-brave-search"]