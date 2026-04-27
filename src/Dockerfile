# syntax=docker/dockerfile:1.7

# ---------- Stage 1: builder ----------
# Install build toolchain + dev headers needed to compile mysqlclient,
# Pillow, argon2-cffi (if no wheel is available) into an isolated venv.
# Nothing from this stage ships to the runtime image except /opt/venv.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt


# ---------- Stage 2: runtime ----------
# Minimal runtime: Python + only the shared libraries needed to load the
# compiled extensions from /opt/venv. No compilers, no dev headers.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Runtime shared libraries:
#   libmariadb3 - mysqlclient loads this at runtime on Debian bookworm
#   libpq5      - defensive, in case someone swaps psycopg2-binary for psycopg2
#   curl        - used by docker-compose healthcheck (curl -sf /health/)
# tini gives us a proper PID 1 for Gunicorn signal handling.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmariadb3 \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root user. System uid/gid 1000 matches the common host developer uid,
# which keeps the docker-compose bind mount writable on Linux hosts.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app \
        --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app

# WORKDIR creates /app owned by root; chown the directory itself so the
# non-root user can create /app/staticfiles (COPY --chown below handles
# the contents, but not the parent).
RUN chown app:app /app

# Bring in the pre-built virtualenv from the builder.
COPY --from=builder --chown=app:app /opt/venv /opt/venv

# Project source + entrypoint, owned by the non-root user.
COPY --chown=app:app . /app/
RUN chmod +x /app/run.sh

USER app

# Collect static at build time. Use dev settings so the prod module's strict
# env-var guards (ALLOWED_HOSTS, ADMIN_URL_PATH, SECRET_KEY != dev-secret)
# don't abort the build. The runtime injects real prod settings separately.
RUN SECRET_KEY=build_secret \
    DJANGO_SETTINGS_MODULE=core.settings.dev \
    python manage.py collectstatic --noinput

EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/run.sh"]
