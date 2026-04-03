#!/bin/bash
# APEX Environment - Docker Quick Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}APEX Environment - Docker Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker from https://www.docker.com/"
    exit 1
fi

echo -e "${GREEN}✅ Docker found${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose found${NC}"
echo ""

# Show menu
echo -e "${YELLOW}Select an option:${NC}"
echo "1. Build and run APEX (foreground)"
echo "2. Build and run APEX (background)"
echo "3. Stop APEX"
echo "4. View logs"
echo "5. Rebuild APEX"
echo "6. Clean up (stop + remove volumes)"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo -e "${YELLOW}Starting APEX in foreground...${NC}"
        docker-compose up
        ;;
    2)
        echo -e "${YELLOW}Starting APEX in background...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ APEX is running in background${NC}"
        echo -e "${GREEN}View logs: docker-compose logs -f${NC}"
        echo -e "${GREEN}API docs: http://localhost:8000/docs${NC}"
        ;;
    3)
        echo -e "${YELLOW}Stopping APEX...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ APEX stopped${NC}"
        ;;
    4)
        echo -e "${YELLOW}Showing APEX logs...${NC}"
        docker-compose logs -f
        ;;
    5)
        echo -e "${YELLOW}Rebuilding APEX...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}✅ Build complete${NC}"
        ;;
    6)
        echo -e "${RED}Cleaning up APEX (this will remove volumes)...${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            docker-compose down -v
            echo -e "${GREEN}✅ Cleanup complete${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
        fi
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Done!${NC}"
echo -e "${GREEN}========================================${NC}"
