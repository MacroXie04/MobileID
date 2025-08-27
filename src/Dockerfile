FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
# Prefer binary wheels but allow compilation only for mysqlclient
ENV PIP_PREFER_BINARY=1

# Set working directory
WORKDIR /app

# Install minimal system dependencies + mysqlclient build deps
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    default-mysql-client \
    # Minimal build tools only for mysqlclient
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY src/requirements.txt /app/requirements.txt

# Upgrade pip and build tools for better wheel support
RUN pip install --no-cache-dir --upgrade \
    pip>=24.0 \
    setuptools>=70.0 \
    wheel>=0.42

# Install packages with binary wheels where available, allow source for mysqlclient
RUN pip install --no-cache-dir \
    --prefer-binary \
    --only-binary=:all: \
    --no-binary=mysqlclient \
    -r /app/requirements.txt

# Copy application code
COPY src /app/src
COPY manage.py /app/manage.py

# Copy environment file (use docker.env as the main config file)
COPY docker.env /app/.env

# Copy and make entrypoint script executable
COPY src/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Start the application
CMD ["/app/entrypoint.sh"]

