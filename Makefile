.PHONY: help install start stop restart logs test clean

help:
	@echo "AI RPG - Development Commands"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make start      - Start all services with Docker"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up containers and volumes"
	@echo ""

install:
	cd backend && pip install -r requirements.txt

start:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📝 API Docs: http://localhost:8000/docs"

stop:
	docker-compose down
	@echo "✅ Services stopped!"

restart:
	docker-compose restart
	@echo "✅ Services restarted!"

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

test:
	cd backend && pytest

clean:
	docker-compose down -v
	@echo "✅ Cleaned up containers and volumes!"

migrate:
	cd backend && alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

shell:
	docker-compose exec backend /bin/bash

db-shell:
	docker-compose exec postgres psql -U postgres -d ai_rpg
