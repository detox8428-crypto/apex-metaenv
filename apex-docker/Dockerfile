# ==============================================================================
# APEX Environment - Isolated Docker Image
# ==============================================================================
# This Dockerfile builds a completely isolated APEX Environment container
# Independent from any other projects - safe to use anywhere
# ==============================================================================

FROM python:3.13-slim

# Metadata
LABEL maintainer="APEX Team"
LABEL project="apex-environment"
LABEL version="1.0"

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PROJECT_NAME="apex-environment" \
    APEX_ISOLATED="true"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application directories
RUN mkdir -p /app/logs /app/apex_env

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy APEX application code
COPY apex_env/ /app/apex_env/
COPY config.py /app/
COPY run_server.py /app/
COPY openenv.yaml /app/

# Copy all other supporting Python files
COPY *.py /app/

# Working directory
WORKDIR /app

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "run_server.py"]
