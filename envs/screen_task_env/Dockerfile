FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for GUI automation and virtual display
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    gedit \
    && rm -rf /var/lib/apt/lists/*

# Copy environment files
COPY pyproject.toml .
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port for FastAPI server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Start virtual display and server
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & DISPLAY=:99 python -m uvicorn server.app:app --host 0.0.0.0 --port 8000"]
