# APEX Docker Helper Script for Windows PowerShell
# Usage: .\docker-helper.ps1 -Command build|start|stop|logs|health|clean|...

param(
    [Parameter(Mandatory=$false)]
    [string]$Command = "help"
)

# Configuration
$COMPOSE_FILE = "docker-compose.apex.standalone.yml"
$CONTAINER_NAME = "apex-api-server"
$IMAGE_NAME = "apex"
$IMAGE_TAG = "latest"

# Function to print colored output
function Print-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host $Text -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
}

function Print-Info {
    param([string]$Text)
    Write-Host "[INFO] $Text" -ForegroundColor Yellow
}

function Print-Success {
    param([string]$Text)
    Write-Host "[SUCCESS] $Text" -ForegroundColor Green
}

function Print-Error {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

# Build image
function Invoke-Build {
    Print-Header "Building APEX Docker Image"
    docker build -f Dockerfile.apex.standalone -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    Print-Success "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# Start with compose
function Invoke-Start {
    Print-Header "Starting APEX Container with Docker Compose"
    Print-Info "Using compose file: $COMPOSE_FILE"
    
    if (-not (Test-Path ".env")) {
        Print-Info "No .env file found. Copying from .env.example for email support"
        Copy-Item ".env.example" ".env"
    }
    
    docker-compose -f $COMPOSE_FILE up -d
    Print-Success "Container started"
    Print-Info "API available at: http://localhost:8000"
    Print-Info "Documentation at: http://localhost:8000/docs"
}

# Stop container
function Invoke-Stop {
    Print-Header "Stopping APEX Container"
    docker-compose -f $COMPOSE_FILE down
    Print-Success "Container stopped"
}

# View logs
function Invoke-Logs {
    Print-Header "APEX Container Logs (live)"
    docker-compose -f $COMPOSE_FILE logs -f $CONTAINER_NAME
}

# Health check
function Invoke-Health {
    Print-Header "APEX Health Check"
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
        Write-Host "Status: $($Response.StatusCode)"
        $Content = $Response.Content | ConvertFrom-Json
        Write-Host "Response: $($Content | ConvertTo-Json -Depth 2)"
        
        if ($Content.status -eq "healthy") {
            Print-Success "Container is healthy"
        }
    } catch {
        Print-Error "Health check failed: $_"
    }
}

# Container stats
function Invoke-Stats {
    Print-Header "Container Resource Usage"
    docker stats $CONTAINER_NAME --no-stream
}

# Shell access
function Invoke-Shell {
    Print-Header "Opening Container Shell"
    docker-compose -f $COMPOSE_FILE exec $CONTAINER_NAME /bin/bash
}

# Test email
function Invoke-TestEmail {
    Print-Header "Testing Email Integration"
    
    Print-Info "Resetting environment..."
    $resetUri = "http://localhost:8000/reset"
    $resetBody = @{"seed" = 42; "max_episode_steps" = 100} | ConvertTo-Json
    
    try {
        $resetResponse = Invoke-WebRequest -Uri $resetUri -Method Post `
            -ContentType "application/json" -Body $resetBody -UseBasicParsing
        Print-Success "Environment reset"
    } catch {
        Print-Error "Reset failed: $_"
        return
    }
    
    Print-Info "Sending test email..."
    $emailUri = "http://localhost:8000/step"
    $emailBody = @{
        "action" = @{
            "action_type" = "email"
            "recipient_id" = 1
            "subject" = "Docker Test Email"
            "body" = "Testing APEX email integration in Docker"
            "send_real" = $false
        }
    } | ConvertTo-Json
    
    try {
        $emailResponse = Invoke-WebRequest -Uri $emailUri -Method Post `
            -ContentType "application/json" -Body $emailBody -UseBasicParsing
        $Content = $emailResponse.Content | ConvertFrom-Json
        Print-Success "Test email sent"
        Write-Host "Reward: $($Content.reward)" -ForegroundColor Cyan
    } catch {
        Print-Error "Email test failed: $_"
    }
}

# Reset environment
function Invoke-Reset {
    Print-Header "Resetting APEX Environment"
    try {
        $resetUri = "http://localhost:8000/reset"
        $resetBody = @{"seed" = 42; "max_episode_steps" = 100} | ConvertTo-Json
        $resetResponse = Invoke-WebRequest -Uri $resetUri -Method Post `
            -ContentType "application/json" -Body $resetBody -UseBasicParsing
        Print-Success "Environment reset"
    } catch {
        Print-Error "Reset failed: $_"
    }
}

# Full cleanup
function Invoke-Clean {
    Print-Header "Cleaning Up APEX Docker Setup"
    
    Print-Info "Stopping container..."
    docker-compose -f $COMPOSE_FILE down -v
    
    Print-Info "Removing image..."
    docker rmi "${IMAGE_NAME}:${IMAGE_TAG}"
    
    Print-Success "Cleanup complete"
}

# Rebuild and restart
function Invoke-Rebuild {
    Print-Header "Rebuilding and Restarting APEX"
    Invoke-Stop
    Invoke-Build
    Invoke-Start
}

# Show status
function Invoke-Status {
    Print-Header "APEX Docker Status"
    docker-compose -f $COMPOSE_FILE ps
}

# Show help
function Show-Help {
    @"

APEX Docker Helper Script for Windows PowerShell

Usage: .\docker-helper.ps1 -Command <command>

Commands:
  build       - Build APEX Docker image
  start       - Start APEX container (builds if needed)
  stop        - Stop APEX container
  restart     - Restart APEX container
  rebuild     - Rebuild image and restart container
  status      - Show container status
  logs        - View live container logs
  health      - Check container health
  stats       - Show container resource usage
  shell       - Open shell in container
  testemail   - Test email integration
  reset       - Reset APEX environment
  clean       - Stop and remove everything
  help        - Show this help message

Examples:
  .\docker-helper.ps1 -Command build      # Build image
  .\docker-helper.ps1 -Command start      # Start container
  .\docker-helper.ps1 -Command logs       # View logs
  .\docker-helper.ps1 -Command status     # Check status

"@
}

# Main
switch ($Command.ToLower()) {
    "build"     { Invoke-Build }
    "start"     { Invoke-Build; Invoke-Start }
    "stop"      { Invoke-Stop }
    "restart"   { Invoke-Stop; Invoke-Start }
    "rebuild"   { Invoke-Rebuild }
    "status"    { Invoke-Status }
    "logs"      { Invoke-Logs }
    "health"    { Invoke-Health }
    "stats"     { Invoke-Stats }
    "shell"     { Invoke-Shell }
    "testemail" { Invoke-TestEmail }
    "reset"     { Invoke-Reset }
    "clean"     { Invoke-Clean }
    "help"      { Show-Help }
    default {
        Print-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
