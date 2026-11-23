# 1. Use Python 3.13 as the base image
FROM python:3.13-slim

# 2. Set the working directory
WORKDIR /app

# 3. Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. Copy dependency files
COPY pyproject.toml uv.lock ./

# 5. Install project dependencies
RUN uv sync --frozen --no-dev --no-install-project

# 6. Copy backend application
COPY app ./app

# 7. Copy frontend application
COPY frontend.py .

# 8. Expose backend and frontend ports
EXPOSE 8000
EXPOSE 8501