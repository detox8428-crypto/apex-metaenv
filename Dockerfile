FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# HuggingFace Spaces runs as non-root user 1000
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

EXPOSE 7860

# Run the APEX main server — NOT app_gradio.py
CMD ["python", "app.py"]

