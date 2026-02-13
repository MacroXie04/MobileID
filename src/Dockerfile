FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
# We need build tools for mysqlclient (pkg-config, default-libmysqlclient-dev, build-essential)
# and libpq-dev for potential psycopg build requirements or client tools
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (production only, no dev group)
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-editable

# Copy project
COPY . /app/
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Collect static files
# Use a dummy secret key for build step; production key should be provided at runtime
RUN SECRET_KEY=build_secret uv run --no-dev python manage.py collectstatic --noinput

# Expose port
EXPOSE 8080

# Default command (can be overridden in docker-compose)
CMD ["/run.sh"]
