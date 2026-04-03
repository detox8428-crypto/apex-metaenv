@echo off
REM APEX Environment - Docker Quick Start Script for Windows

setlocal enabledelayedexpansion

cls
echo ========================================
echo APEX Environment - Docker Setup
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Docker is not installed
    echo Please install Docker from https://www.docker.com/
    pause
    exit /b 1
)

echo [OK] Docker found

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Docker Compose is not installed
    echo Please install Docker Compose
    pause
    exit /b 1
)

echo [OK] Docker Compose found
echo.

color 0A

:menu
echo Select an option:
echo 1. Build and run APEX (foreground)
echo 2. Build and run APEX (background)
echo 3. Stop APEX
echo 4. View logs
echo 5. Rebuild APEX
echo 6. Clean up (stop + remove volumes)
echo.

set /p choice="Enter choice [1-6]: "

if "%choice%"=="1" (
    echo Starting APEX in foreground...
    docker-compose up
    goto end
)

if "%choice%"=="2" (
    echo Starting APEX in background...
    docker-compose up -d
    echo [OK] APEX is running in background
    echo View logs: docker-compose logs -f
    echo API docs: http://localhost:8000/docs
    goto end
)

if "%choice%"=="3" (
    echo Stopping APEX...
    docker-compose down
    echo [OK] APEX stopped
    goto end
)

if "%choice%"=="4" (
    echo Showing APEX logs...
    docker-compose logs -f
    goto end
)

if "%choice%"=="5" (
    echo Rebuilding APEX...
    docker-compose build --no-cache
    echo [OK] Build complete
    goto end
)

if "%choice%"=="6" (
    color 0C
    echo Cleaning up APEX (this will remove volumes)...
    set /p confirm="Are you sure? (yes/no): "
    if "!confirm!"=="yes" (
        docker-compose down -v
        color 0A
        echo [OK] Cleanup complete
    ) else (
        color 0A
        echo Cancelled
    )
    goto end
)

color 0C
echo Invalid choice
goto menu

:end
echo.
echo ========================================
echo Done!
echo ========================================
pause
