FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies including those needed for pycairo, pandas, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    cron \
    pkg-config \
    libcairo2-dev \
    libjpeg-dev \
    libgif-dev \
    libpng-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/media /app/static /app/invoices /app/logs

# Copy cron file
COPY docker/crontab /etc/cron.d/inviflow-cron
RUN chmod 644 /etc/cron.d/inviflow-cron

# Ensure cron logs exist
RUN touch /app/logs/cron.log

# Run both cron and Django in foreground using supervisord
CMD ["sh", "-c", "\
    cron && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8000 \
"]