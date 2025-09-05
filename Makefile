# 2KCompLeague Discord Bot - Makefile
# Provides common commands for development and deployment

.PHONY: help build run stop clean test lint format docker-build docker-run docker-stop docker-clean deploy logs

# Default target
help:
	@echo "2KCompLeague Discord Bot - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  test        - Run all tests"
	@echo "  test-cov    - Run tests with coverage"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and isort"
	@echo "  install     - Install development dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run bot in Docker"
	@echo "  docker-stop  - Stop Docker container"
	@echo "  docker-clean - Clean Docker resources"
	@echo "  docker-logs  - View Docker logs"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy      - Deploy bot to production"
	@echo "  deploy-auto - Automated production deployment with backup"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  logs        - View application logs"
	@echo "  status      - Check bot status"
	@echo "  health-monitor - Start continuous health monitoring"
	@echo "  health-check   - Run single health check"
	@echo ""
	@echo "Performance Testing:"
	@echo "  performance-test     - Run comprehensive performance test suite"
	@echo "  performance-analysis - Run performance analysis only"
	@echo "  load-test           - Run load testing"
	@echo "  stress-test         - Run stress testing"
	@echo "  performance-optimize - Run performance optimizations"
	@echo ""

# Development Commands
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	python -m pytest tests/ --cov=core --cov-report=html --cov-report=term

lint:
	@echo "Running linting checks..."
	ruff check .
	ruff format --check .

format:
	@echo "Formatting code..."
	black .
	isort .

format-check:
	@echo "Checking code formatting..."
	black --check .
	isort --check-only .

type-check:
	@echo "Running type checks..."
	mypy core/ tests/

quality:
	@echo "Running all code quality checks..."
	@echo "1. Formatting..."
	@make format
	@echo "2. Linting..."
	@make lint
	@echo "3. Type checking..."
	@make type-check
	@echo "4. Tests..."
	@make test
	@echo "✅ All quality checks passed!"

install:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"

# Docker Commands
docker-build:
	@echo "Building Docker image..."
	docker build -t 2kcomp-league-bot .

docker-run:
	@echo "Starting Discord bot in Docker..."
	docker-compose up -d

docker-stop:
	@echo "Stopping Discord bot..."
	docker-compose down

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f discord-bot

# Deployment Commands
deploy:
	@echo "Deploying Discord bot..."
	docker-compose down
	docker-compose up -d --build
	@echo "Deployment complete!"

logs:
	@echo "Viewing application logs..."
	docker-compose logs -f discord-bot

status:
	@echo "Checking bot status..."
	docker-compose ps
	@echo ""
	@echo "Container health:"
	docker inspect --format='{{.State.Health.Status}}' 2kcomp-league-bot || echo "Container not running"

# Utility Commands
clean:
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Cleanup complete!"

setup:
	@echo "Setting up development environment..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev]"
	@echo "Setup complete!"

# Production Commands
prod-deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-logs:
	@echo "Viewing production logs..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Deployment Automation
deploy-auto:
	@echo "Running automated deployment..."
	@if [ -f "scripts/deploy.sh" ]; then \
		./scripts/deploy.sh production --backup; \
	else \
		echo "Deployment script not found"; \
		exit 1; \
	fi

deploy-staging:
	@echo "Deploying to staging..."
	@if [ -f "scripts/deploy.sh" ]; then \
		./scripts/deploy.sh staging; \
	else \
		echo "Deployment script not found"; \
		exit 1; \
	fi

# Health Monitoring
health-monitor:
	@echo "Starting health monitor..."
	@if [ -f "scripts/health-monitor.sh" ]; then \
		./scripts/health-monitor.sh; \
	else \
		echo "Health monitor script not found"; \
		exit 1; \
	fi

health-check:
	@echo "Running health check..."
	@curl -s http://localhost:8080/health | jq . || echo "Health check failed"

# Backup and Restore
backup:
	@echo "Creating backup of data..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/

restore:
	@echo "Restoring from backup..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "Usage: make restore BACKUP_FILE=backup-file.tar.gz"; \
		exit 1; \
	fi
	tar -xzf $(BACKUP_FILE)
	@echo "Restore complete!"

# CI/CD Commands
ci-test:
	@echo "Running CI test suite..."
	python -m pytest tests/ --cov=core --cov-report=xml --cov-report=html

ci-security:
	@echo "Running security scans..."
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r core/ -f json -o bandit-report.json; \
	else \
		echo "Bandit not installed, skipping security scan"; \
	fi
	@if command -v safety >/dev/null 2>&1; then \
		safety check --json --output safety-report.json; \
	else \
		echo "Safety not installed, skipping dependency check"; \
	fi

# Performance Testing Commands
performance-test:
	@echo "Running comprehensive performance test suite..."
	@if [ -f "scripts/performance_test.py" ]; then \
		python scripts/performance_test.py --mode comprehensive; \
	else \
		echo "Performance test script not found"; \
		exit 1; \
	fi

performance-analysis:
	@echo "Running performance analysis..."
	@if [ -f "scripts/performance_test.py" ]; then \
		python scripts/performance_test.py --mode analysis; \
	else \
		echo "Performance test script not found"; \
		exit 1; \
	fi

load-test:
	@echo "Running load test..."
	@if [ -f "scripts/performance_test.py" ]; then \
		python scripts/performance_test.py --mode load-test --scenario normal_load; \
	else \
		echo "Performance test script not found"; \
		exit 1; \
	fi

stress-test:
	@echo "Running stress test..."
	@if [ -f "scripts/performance_test.py" ]; then \
		python scripts/performance_test.py --mode stress-test --max-users 30; \
	else \
		echo "Performance test script not found"; \
		exit 1; \
	fi

performance-optimize:
	@echo "Running performance optimizations..."
	@if [ -f "scripts/performance_test.py" ]; then \
		python scripts/performance_test.py --mode optimize; \
	else \
		echo "Performance test script not found"; \
		exit 1; \
	fi
