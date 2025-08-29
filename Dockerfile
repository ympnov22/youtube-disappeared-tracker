FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Satisfy Poetry's [tool.poetry] readme metadata early
COPY README.md LICENSE* ./

# Install only dependencies first for better cache reuse
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY app/ ./app/
COPY alembic.ini ./

# Now install local package (our app)
RUN poetry install --no-interaction --no-ansi

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["bash", "-lc", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
