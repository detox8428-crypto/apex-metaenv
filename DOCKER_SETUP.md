# APEX Environment - Docker Setup Guide

This guide explains how to run APEX Environment in Docker with complete isolation from other projects.

## Quick Start

### Option 1: Using the New Isolated Docker Compose (Recommended)

```bash
# Build and run APEX Environment
docker-compose -f docker-compose.apex.yml up -d

# View logs
docker-compose -f docker-compose.apex.yml logs -f

# Stop the service
docker-compose -f docker-compose.apex.yml down
```

### Option 2: Using the New Isolated Dockerfile

```bash
# Build the Docker image
docker build -f Dockerfile.apex -t apex-environment:latest .

# Run the container
docker run -p 8000:8000 --name apex-server apex-environment:latest

# Or run in background
docker run -d -p 8000:8000 --name apex-server apex-environment:latest
```

### Option 3: Docker Compose with Development Mode

```bash
# Run with live code reloading
docker-compose -f docker-compose.apex.yml up

# This keeps you in the foreground to see logs in real-time
```

## Verification

Once running, verify the APEX Environment is accessible:

```bash
# Check if container is running
docker ps

# Check if API is responding
curl http://localhost:8000/health

# Access interactive API docs
# Open in browser: http://localhost:8000/docs
```

## Container Information

**Container Name**: `apex-environment-server`  
**Image Name**: `apex-environment:latest`  
**Port**: 8000  
**Network**: `apex-network` (isolated)

## File Structure in Container

```
/apex/
├── apex_env/          # Core environment code
├── requirements.txt   # Python dependencies
├── run_server.py      # Server entry point
├── config.py          # Configuration
├── openenv.yaml       # Environment configuration
└── logs/              # Application logs (volume mounted)
```

## Common Commands

### Logs
```bash
# View logs
docker-compose -f docker-compose.apex.yml logs -f

# View last 50 lines
docker-compose -f docker-compose.apex.yml logs --tail=50

# View logs for specific service
docker-compose -f docker-compose.apex.yml logs apex-environment
```

### Container Management
```bash
# Stop running container
docker-compose -f docker-compose.apex.yml down

# Remove container and volumes
docker-compose -f docker-compose.apex.yml down -v

# Restart container
docker-compose -f docker-compose.apex.yml restart

# Execute command in running container
docker exec apex-environment-server python -c "import apex_env; print(apex_env.__version__)"
```

### Build Options
```bash
# Rebuild image (useful after code changes)
docker-compose -f docker-compose.apex.yml up --build

# Rebuild without cache
docker-compose -f docker-compose.apex.yml up --build --no-cache
```

## Environment Variables

The APEX container sets these environment variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| PYTHONUNBUFFERED | 1 | Real-time log output |
| PYTHONDONTWRITEBYTECODE | 1 | No .pyc files in container |
| PIP_NO_CACHE_DIR | 1 | Smaller image size |
| APEX_ENV | docker | Identifies Docker environment |

## Network Isolation

Both the Dockerfile and docker-compose use isolated networks and containers:

**Old Setup**:
- Container: `apex-env-api` (may conflict)
- Network: `apex-network` (shared)
- Dockerfile: `Dockerfile`

**New Setup**:
- Container: `apex-environment-server` (unique)
- Network: `apex-network` (dedicated volume)
- Dockerfile: `Dockerfile.apex`
- Compose: `docker-compose.apex.yml`

## Troubleshooting

### Port Already in Use
```bash
# Kill existing container
docker kill apex-environment-server

# Or use a different port
docker run -p 8001:8000 apex-environment:latest
```

### Container Won't Start
```bash
# View detailed logs
docker-compose -f docker-compose.apex.yml logs

# Check container health
docker-compose -f docker-compose.apex.yml ps

# Execute bash in container to debug
docker exec -it apex-environment-server bash
```

### Rebuild Required
```bash
# Force rebuild (after code changes)
docker-compose -f docker-compose.apex.yml up --build --force-recreate
```

## Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile.apex` | Standalone, isolated Dockerfile for APEX |
| `docker-compose.apex.yml` | Standalone compose file, uses Dockerfile.apex |
| `Dockerfile` | Legacy (may affect other projects) |
| `docker-compose.yml` | Legacy compose file |

**Recommendation**: Use the new `.apex` files to avoid conflicts with other projects.

## Next Steps

1. ✅ Run: `docker-compose -f docker-compose.apex.yml up -d`
2. ✅ Verify: Open http://localhost:8000/docs in your browser
3. ✅ Test: Navigate to `/docs` to test the API endpoints
4. ✅ Deploy: Use this isolated setup in production

## Support

For issues specific to APEX Environment, consult:
- README.md - Main documentation
- ARCHITECTURE.md - System architecture
- API Documentation - http://localhost:8000/docs (when running)
