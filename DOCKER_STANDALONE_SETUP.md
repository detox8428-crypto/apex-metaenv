# APEX Docker Standalone Setup Guide

## Overview

This is a **separate, dedicated Docker setup** for APEX that includes:
- Python 3.13 slim base image
- Core APEX environment with all components
- FastAPI server on port 8000
- Email integration support (Gmail, Outlook, SMTP)
- Production-ready configuration
- Health checks and resource limits
- Non-root user for security

---

## Quick Start

### Option 1: Build and Run with Docker Compose (Recommended)

```bash
# Clone/navigate to APEX directory
cd d:\APEX

# Create .env file for email credentials (optional)
cp .env.example .env
# Edit .env with your email provider credentials

# Build and start
docker-compose -f docker-compose.apex.standalone.yml up -d

# View logs
docker-compose -f docker-compose.apex.standalone.yml logs -f apex-api

# Stop
docker-compose -f docker-compose.apex.standalone.yml down
```

### Option 2: Build and Run with Docker CLI

```bash
# Build image
docker build -f Dockerfile.apex.standalone -t apex:latest .

# Run container
docker run -d \
  --name apex-server \
  -p 8000:8000 \
  -e EMAIL_PROVIDER=gmail \
  -e GMAIL_EMAIL=your-email@gmail.com \
  -e GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx \
  apex:latest

# Check logs
docker logs -f apex-server

# Stop container
docker stop apex-server
docker rm apex-server
```

---

## Email Configuration

### Without Email Credentials (Simulation Mode)
```bash
docker-compose -f docker-compose.apex.standalone.yml up -d
# Email will work in simulation mode only
```

### With Gmail
```bash
# Create .env file
EMAIL_PROVIDER=gmail
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Start
docker-compose -f docker-compose.apex.standalone.yml up -d
```

### With Outlook
```bash
# Create .env file
EMAIL_PROVIDER=outlook
OUTLOOK_EMAIL=your-email@outlook.com
OUTLOOK_PASSWORD=your-app-password

# Start
docker-compose -f docker-compose.apex.standalone.yml up -d
```

### With Custom SMTP
```bash
# Create .env file
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_EMAIL=apikey
SMTP_PASSWORD=SG.your-sendgrid-key

# Start
docker-compose -f docker-compose.apex.standalone.yml up -d
```

---

## Accessing the API

Once running:

### Health Check
```bash
curl http://localhost:8000/health
```

### Interactive API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Example API Call
```bash
# Reset environment
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"seed": 42, "max_episode_steps": 100}'

# Send email action
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "email",
      "recipient_id": 1,
      "subject": "Hello from Docker",
      "body": "Running APEX in Docker",
      "send_real": false
    }
  }'
```

---

## File Structure

```
d:\APEX\
├── Dockerfile.apex.standalone        # ← THIS DOCKERFILE
├── docker-compose.apex.standalone.yml ← THIS COMPOSE FILE
├── requirements.txt                  # Python dependencies
├── apex_env/                         # Core environment package
├── server.py                         # FastAPI server
├── run_server.py                     # Server startup
├── inference.py                      # Inference module
├── openenv.yaml                      # OpenEnv specification
└── email_setup_guide.py              # Email helper functions
```

---

## Environment Variables

### Email Configuration (Optional)
```
EMAIL_PROVIDER=gmail|outlook|smtp
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
OUTLOOK_EMAIL=your-email@outlook.com
OUTLOOK_PASSWORD=password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_EMAIL=email@example.com
SMTP_PASSWORD=password
```

### API Configuration
```
API_HOST=0.0.0.0          # Listen on all interfaces
API_PORT=8000             # Container port
MODEL_NAME=gpt-3.5-turbo  # LLM model name
```

---

## Resource Limits

The docker-compose file includes resource limits:
- **CPU Limit:** 2 cores
- **Memory Limit:** 2GB
- **CPU Request:** 1 core
- **Memory Request:** 1GB

Modify in `docker-compose.apex.standalone.yml` if needed:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Change CPU limit
      memory: 4G       # Change memory limit
```

---

## Security Features

✅ **Non-root user**: Container runs as `apex` user (UID 1000)
✅ **Slim base image**: Reduced attack surface
✅ **Health checks**: Automatic monitoring
✅ **No root access**: Safe for production
✅ **Environment secrets**: Credentials via .env
✅ **Restart policy**: `unless-stopped` for reliability

---

## Volume Mounting

The docker-compose file creates volumes for:
- **logs/**: Application logs
- **data/**: Persistent data

Access from host:
```bash
docker-compose -f docker-compose.apex.standalone.yml \
  -v /local/logs:/app/logs \
  -v /local/data:/app/data \
  up -d
```

---

## Networking

The docker-compose file uses a custom bridge network `apex-network` for:
- Service isolation
- Easy DNS resolution
- Clear network boundaries

---

## Health Endpoint

The container includes a health check:
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-03T12:00:00Z"
}
```

---

## Development Workflow

### 1. Build Custom Image
```bash
docker build -f Dockerfile.apex.standalone -t apex:v1.0 .
```

### 2. Tag for Registry
```bash
docker tag apex:v1.0 myregistry.azurecr.io/apex:v1.0
```

### 3. Push to Registry
```bash
docker push myregistry.azurecr.io/apex:v1.0
```

### 4. Run from Registry
```bash
docker run -p 8000:8000 myregistry.azurecr.io/apex:v1.0
```

---

## Kubernetes Deployment

### Create Kubernetes Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apex-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apex
  template:
    metadata:
      labels:
        app: apex
    spec:
      containers:
      - name: apex
        image: myregistry.azurecr.io/apex:latest
        ports:
        - containerPort: 8000
        env:
        - name: EMAIL_PROVIDER
          valueFrom:
            secretKeyRef:
              name: apex-secrets
              key: email-provider
        - name: GMAIL_EMAIL
          valueFrom:
            secretKeyRef:
              name: apex-secrets
              key: gmail-email
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
```

### Create Kubernetes Secret
```bash
kubectl create secret generic apex-secrets \
  --from-literal=email-provider=gmail \
  --from-literal=gmail-email=your@email.com \
  --from-literal=gmail-app-password=xxxx-xxxx-xxxx-xxxx
```

### Deploy
```bash
kubectl apply -f apex-deployment.yaml
```

---

## Docker Hub Push

### 1. Login to Docker Hub
```bash
docker login
```

### 2. Build with Username
```bash
docker build -f Dockerfile.apex.standalone -t yourusername/apex:latest .
```

### 3. Push
```bash
docker push yourusername/apex:latest
```

### 4. Run from Docker Hub
```bash
docker run -p 8000:8000 yourusername/apex:latest
```

---

## Troubleshooting

### Container won't start
```bash
docker logs apex-api-server
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "9000:8000"  # Maps host:9000 to container:8000
```

### Email not working
1. Verify .env file has credentials
2. Check docker logs: `docker logs apex-api-server`
3. Ensure EMAIL_PROVIDER is set
4. Test with send_real=false (simulation mode) first

### High memory usage
1. Reduce resource limits in compose file
2. Check logs for memory leaks
3. Monitor with: `docker stats apex-api-server`

---

## Performance Tuning

### Increase Python Workers
Edit `Dockerfile.apex.standalone`:
```dockerfile
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Enable Caching
```dockerfile
ENV PYTHONBUFFERED=0
```

### Reduce Image Size
```dockerfile
# Use alpine base instead
FROM python:3.13-alpine
# Install libc for compatibility
RUN apk add --no-cache musl-dev gcc
```

---

## Monitoring

### Container Stats
```bash
docker stats apex-api-server
```

### View Logs
```bash
# Live logs
docker logs -f apex-api-server

# Last 100 lines
docker logs --tail 100 apex-api-server

# With timestamps
docker logs -t apex-api-server
```

### Inspect Container
```bash
docker inspect apex-api-server
```

---

## Cleanup

### Stop Container
```bash
docker stop apex-api-server
```

### Remove Container
```bash
docker rm apex-api-server
```

### Remove Image
```bash
docker rmi apex:latest
```

### Clean Up All (Docker Compose)
```bash
docker-compose -f docker-compose.apex.standalone.yml down -v
```

---

## Production Deployment Checklist

- [ ] Build and test image locally
- [ ] Update Python dependencies in requirements.txt
- [ ] Set EMAIL_PROVIDER and credentials via .env
- [ ] Configure resource limits based on expected load
- [ ] Set up logging volume for persistence
- [ ] Test health endpoint: `curl http://localhost:8000/health`
- [ ] Load test with sample requests
- [ ] Set up monitoring (Prometheus, DataDog, etc.)
- [ ] Configure CI/CD pipeline for auto-build
- [ ] Push to container registry (Docker Hub, Azure ACR, etc.)
- [ ] Deploy to Kubernetes or cloud platform
- [ ] Set up alerts for unhealthy containers

---

## Files Reference

### Dockerfile.apex.standalone
- **Purpose:** Build APEX Docker image
- **Base:** Python 3.13-slim
- **Includes:** Email support, health checks, non-root user
- **Build:** `docker build -f Dockerfile.apex.standalone -t apex:latest .`

### docker-compose.apex.standalone.yml
- **Purpose:** Orchestrate APEX container
- **Includes:** Port mapping, volumes, environment variables, health checks
- **Start:** `docker-compose -f docker-compose.apex.standalone.yml up -d`

---

## Support

For issues:
1. Check logs: `docker logs apex-api-server`
2. Read EMAIL_INTEGRATION.md for email setup
3. See PRODUCTION_STATUS.txt for API details
4. Review REAL_EMAIL_GETTING_STARTED.md for quick setup

---

## Version Info

- **Status:** Production Ready ✅
- **Created:** 2026-04-03
- **DockerBase:** Python 3.13-slim
- **API Port:** 8000
- **Health Check:** Enabled
- **Email Support:** Full

---

**Happy containerizing!** 🐳
