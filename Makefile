CURRENT_DIR = $(shell pwd)
include .env
export

.PHONY: help test test-agent test-setup install clean run-perplexity chat configure-langfuse

setup: ## Initial setup - copy env file
	@echo "⚙️  Initial project setup..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from template"; \
		echo "⚠️  Please edit .env and add your Mapbox token"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Testing
test-setup: ## Verify environment configuration
	@echo "🔍 Checking environment setup..."
	PYTHONPATH=src uv run python scripts/test_setup.py

test-agent: ## Test agent tools (geocoding, routing, etc.)
	@echo "🧪 Testing agent tools..."
	PYTHONPATH=src uv run python scripts/test_agent.py

test: test-setup test-agent ## Run all tests

# Environment validation
check-env: ## Check if environment is properly configured
	@echo "🔍 Checking environment configuration..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file missing - run 'make setup'"; \
		exit 1; \
	fi
	@if ! grep -q "MAPBOX_ACCESS_TOKEN=" .env 2>/dev/null; then \
		echo "❌ Mapbox access token not configured in .env"; \
		exit 1; \
	fi
	@echo "✅ Environment configuration looks good!"

# Cleanup
clean: ## Remove Python cache files
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

clean-all: clean ## Remove cache and virtual environment
	@echo "🧹 Deep cleaning..."
	rm -rf .venv

# Development
dev: setup install test ## Complete development setup
	@echo ""
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Available commands:"
	@echo "  make test-agent   - Test agent tools"
	@echo "  make chat         - Start interactive chat"
	@echo ""

# Quick commands
quick-test: test-agent ## Quick test of agent functionality

run-perplexity: ## Run Perplexity event searcher
	ENV_FILE_PATH=${CURRENT_DIR}/.env uv run python src/agent/perplexity.py

chat: ## Start interactive chat with the agent
	@echo "💬 Starting interactive chat with agent..."
	PYTHONPATH=src uv run python scripts/chat.py

configure-langfuse: ## Configure Langfuse model pricing for cost tracking
	@echo "🔧 Configuring Langfuse model pricing..."
	uv run python scripts/configure_langfuse_model.py
