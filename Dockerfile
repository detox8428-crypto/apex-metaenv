FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Run
EXPOSE 7860
ENV HOST=0.0.0.0
ENV PORT=7860

# Start app with both FastAPI endpoints AND Gradio UI
CMD ["python", "app_gradio.py"]

