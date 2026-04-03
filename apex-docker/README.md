# APEX Environment - Docker (Isolated Project)

This is a **completely separate Docker project structure** for APEX Environment. It is completely isolated and won't interfere with any other projects.

## 📁 Project Structure

```
apex-docker/                  ← SEPARATE PROJECT DIRECTORY
├── Dockerfile                ← Isolated Dockerfile (just called Dockerfile)
├── docker-compose.yml        ← Isolated compose file (just called docker-compose.yml)
├── .dockerignore             ← Docker ignore rules
├── requirements.txt          ← Python dependencies (copy)
└── README.md                 ← This file
```

## 🚀 Quick Start

### Prerequisites
- Docker installed
- Docker Compose installed

### Run APEX in Docker

```bash
# Navigate to apex-docker directory
cd apex-docker

# Build and run APEX
docker-compose up

# Or run in background
docker-compose up -d
```

### Access APEX API

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📋 Common Commands

### Build Image
```bash
# Build without running
docker-compose build

# Rebuild with no cache
docker-compose build --no-cache
```

### Start/Stop Container
```bash
# Start in foreground (see logs)
docker-compose up

# Start in background
docker-compose up -d

# Stop container
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail=50

# View logs for specific service
docker-compose logs apex
```

### Container Management
```bash
# List running containers
docker-compose ps

# Execute command in container
docker-compose exec apex python -c "print('APEX running!')"

# Open shell in container
docker-compose exec apex /bin/bash

# Restart container
docker-compose restart

# View container details
docker-compose config
```

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to modify:
- `LOG_LEVEL` - Set to debug, info, warning, error
- Port mapping (default: 8000:8000)
- Volume mount locations
- Container name (apex-app)

### Network Isolation

- **Network**: `apex-isolated-net` (isolated bridge network)
- **No port conflicts** with other projects
- **No volume name conflicts**

### Resource Limits (Optional)

To limit resources, add to `docker-compose.yml` service:

```yaml
services:
  apex:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 📊 Container Info

| Property | Value |
|----------|-------|
| Image Name | `apex-app:latest` |
| Container Name | `apex-app` |
| Port | 8000 |
| Network | `apex-isolated-net` |
| Volume | `apex-logs` |
| Status | Healthy ✅ |

## ✅ Health Checks

The container automatically checks health every 30 seconds:
```bash
curl http://localhost:8000/health
```

If unhealthy:
```bash
# View health status
docker-compose ps

# View detailed logs
docker-compose logs apex

# Restart if needed
docker-compose restart
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill existing container
docker-compose down

# Or use different port (edit docker-compose.yml)
# Change: "8000:8000" to "8001:8000"
```

### Container Won't Start
```bash
# View logs
docker-compose logs -f

# Rebuild image
docker-compose build --no-cache

# Run with verbose logging
docker-compose up --verbose
```

### Permission Denied
```bash
# On Linux/Mac, you might need sudo
sudo docker-compose up

# Or add your user to docker group
sudo usermod -aG docker $USER
```

## 🔐 Security Notes

- Container runs as non-root user (best practice)
- `.dockerignore` prevents sensitive files from being copied
- Health checks ensure container is responsive
- Network is isolated from other containers

## 📦 What's Installed

Inside the Docker container:
- Python 3.13 slim
- All APEX dependencies (from requirements.txt)
- System tools: gcc, g++, curl, git
- Application logs directory

## 🌐 API Endpoints

Once running, access:

```
GET    /                           - Root endpoint
GET    /health                     - Health check
POST   /reset                      - Reset environment
POST   /step                       - Execute action
GET    /observation                - Get current observation
POST   /email                      - Send email
POST   /meeting                    - Schedule meeting
POST   /translate                  - Translate text
POST   /gesture                    - Execute gesture
GET    /docs                       - Interactive docs
GET    /redoc                      - Alternative docs
```

## 📝 Notes

- This is a **completely separate** project structure
- Can be deployed independently
- Won't conflict with main APEX project
- Can be used as a template for other isolated Docker projects

## 💡 Tips

1. **Development**: Run `docker-compose up` to see live logs
2. **Production**: Run `docker-compose up -d` for background operation
3. **Logs**: Use `docker-compose logs -f` to monitor
4. **Updates**: Edit code, then `docker-compose build && docker-compose up`
5. **Cleanup**: Run `docker-compose down -v` to remove everything

## 📚 Related Files

- Main project: Go up one level to `/`
- Docker setup guide: `../DOCKER_SETUP.md`
- Environment config: `../config.py`
- Server code: `../run_server.py`

---

**Status**: ✅ Production Ready  
**Isolation**: ✅ Complete  
**Tested**: ✅ Yes
