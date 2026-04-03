# APEX Environment - Standalone Docker Configuration
# This Dockerfile is isolated for APEX and does not affect other projects

FROM python:3.13-slim

# Set metadata
LABEL maintainer="APEX Environment"
LABEL description="APEX Environment - Agent Training Platform"
LABEL version="1.0"

# Set working directory
WORKDIR /apex

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APEX_ENV=docker

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application structure
RUN mkdir -p /apex/apex_env /apex/logs

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY apex_env/ /apex/apex_env/
COPY *.py /apex/
COPY config.py /apex/
COPY openenv.yaml /apex/

# Expose APEX API port
EXPOSE 8000

# Health check for APEX server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run APEX server
CMD ["python", "run_server.py"]
