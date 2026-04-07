FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN useradd -m -u 1000 user
USER user

ENV PATH="/home/user/.local/bin:$PATH"
ENV PORT=7860
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

# Run Gradio app for HF Spaces
CMD ["python", "app_gradio.py"]

