# Quick Start: Build & Run APEX Docker

## Step 1: Make Sure Docker Desktop is Running ✅

From your screenshot, Docker Desktop is open. Make sure:
- ✅ The Docker icon in taskbar shows it's running
- ✅ You see "Docker daemon is running" in Docker Desktop

If Docker isn't running, click **Docker Desktop** in Windows Start menu.

---

## Step 2: Copy Email Configuration (Optional)

```powershell
cd d:\APEX
cp .env.example .env
```

Edit `.env` to add email credentials (or leave empty for simulation-only mode).

---

## Step 3: Build the Image

Run this command in PowerShell:

```powershell
cd d:\APEX
docker build -f Dockerfile.apex.standalone -t apex:latest .
```

This will:
- Download Python 3.13-slim base image
- Install dependencies from requirements.txt
- Set up APEX environment
- Create image "apex:latest"

**First build takes 2-3 minutes** (downloads base image)

---

## Step 4: Verify Image Created

```powershell
docker images | findstr apex
```

You should see:
```
apex             latest    [IMAGE_ID]    [SIZE]
```

---

## Step 5: Start the Container

```powershell
cd d:\APEX
docker-compose -f docker-compose.apex.standalone.yml up -d
```

This will:
- Start APEX API server on port 8000
- Set up volumes for logs and data
- Enable health checks
- Run in background (-d)

---

## Step 6: Verify APEX is Running

```powershell
docker ps
```

You should see:
```
CONTAINER ID  IMAGE        STATUS         PORTS
[ID]          apex:latest  Up 5 seconds   0.0.0.0:8000->8000/tcp
```

OR check Docker Desktop - you'll see "apex-api-server" in the Containers list!

---

## Step 7: Check Health

```powershell
curl http://localhost:8000/health
```

You should see:
```json
{"status":"healthy","timestamp":"..."}
```

---

## Step 8: Access the API

Visit in your browser:
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Quick Commands

```powershell
# View logs
docker logs apex-api-server -f

# Stop container
docker stop apex-api-server

# Remove container
docker rm apex-api-server

# Remove image
docker rmi apex:latest

# Full cleanup
docker-compose -f docker-compose.apex.standalone.yml down -v
```

---

## Or Use Helper Script (Easier!)

```powershell
# Make sure Docker Desktop is running first!

# Build and start
.\docker-helper.ps1 -Command start

# View logs
.\docker-helper.ps1 -Command logs

# Check health
.\docker-helper.ps1 -Command health

# Stop
.\docker-helper.ps1 -Command stop
```

---

## Troubleshooting

### "Docker daemon not running"
- Open Docker Desktop from Start menu
- Wait for it to fully load (check taskbar icon)
- Try again

### "Image file too large"
- First build downloads base image (~300MB)
- Subsequent builds are faster
- Be patient!

### Port 8000 already in use
Edit `docker-compose.apex.standalone.yml`:
```yaml
ports:
  - "9000:8000"  # Use 9000 instead
```

### Can't see container in Docker Desktop
- Refresh Docker Desktop UI
- Make sure it fully started
- Check: `docker ps`

---

## Next: Reference Files

- **Setup Guide**: DOCKER_STANDALONE_SETUP.md (50+ pages)
- **Summary**: APEX_DOCKER_STANDALONE_SUMMARY.md
- **Email Guide**: EMAIL_INTEGRATION.md
- **Quick Start**: REAL_EMAIL_GETTING_STARTED.md

---

**Status**: Ready to build! 🚀
Ensure Docker Desktop is running, then run the commands above.
