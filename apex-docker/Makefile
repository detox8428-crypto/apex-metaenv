.PHONY: help build up down logs shell rebuild clean restart health

help:
	@echo "APEX Environment - Docker Commands"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build     - Build Docker image"
	@echo "  up        - Start APEX (foreground)"
	@echo "  up-bg     - Start APEX (background)"
	@echo "  down      - Stop APEX"
	@echo "  logs      - View APEX logs (follow)"
	@echo "  shell     - Open shell in APEX container"
	@echo "  rebuild   - Rebuild image (no cache)"
	@echo "  clean     - Stop and remove everything"
	@echo "  restart   - Restart APEX"
	@echo "  health    - Check APEX health"
	@echo "  status    - Show container status"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up

up-bg:
	docker-compose up -d
	@echo "APEX is running in background"
	@echo "Access API at: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec apex /bin/bash

rebuild:
	docker-compose build --no-cache
	@echo "Build complete"

clean:
	docker-compose down -v
	@echo "Everything cleaned up"

restart:
	docker-compose restart
	@echo "APEX restarted"

health:
	@curl -s http://localhost:8000/health && echo "" || echo "APEX is not responding"

status:
	docker-compose ps

ps: status

logs-tail:
	docker-compose logs --tail=50

exec:
	docker-compose exec apex $(cmd)

version:
	docker-compose version
	docker version --format='Docker: {{.Server.Version}}'

# Development commands
dev:
	docker-compose up

dev-bg:
	docker-compose up -d
	@echo "Development mode - background"

prod-bg:
	docker-compose -f docker-compose.yml up -d
	@echo "Production mode - background"
