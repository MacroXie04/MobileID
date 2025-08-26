FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y default-libmysqlclient-dev build-essential curl git pkg-config \
    chromium chromium-driver fonts-liberation libnss3 ca-certificates libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Symlink chromium to expected google-chrome path for Selenium code
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome || true
EXPOSE 8000
