CURRENT_DIR = $(shell pwd)
NETWORK_NAME = backtier_network
include .env
export

.PHONY: help test test-agent test-setup install clean run-perplexity chat list-redis configure-langfuse redis-start redis-stop api-dev api-prod api-test

prepare-dirs:
	mkdir -p ${CURRENT_DIR}/data/redis_data || true

stop-redis:
	docker container rm -f redis-server || true

build-network:
	docker network create ${NETWORK_NAME} -d bridge || true

run-redis: build-network stop-redis
	@echo "🛑 Stopping Redis..."
	@docker run -d \
	--name redis-server \
	-p 6379:6379 \
	--network ${NETWORK_NAME} \
	-v ${CURRENT_DIR}/data/redis-data:/data \
	redis:8.0.0 \
	redis-server --appendonly yes

test-agent: ## Test agent tools (geocoding, routing, etc.)
	@echo "🧪 Testing agent tools..."
	PYTHONPATH=src uv run python scripts/test_agent.py

clean: ## Remove Python cache files
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

run-perplexity: ## Run Perplexity event searcher
	ENV_FILE_PATH=${CURRENT_DIR}/.env uv run python src/agent/perplexity.py

chat: ## Start interactive chat with the FastAPI agent
	@echo "💬 Starting interactive chat with FastAPI agent..."
	@echo "📝 Make sure API server is running (make api-dev in another terminal)"
	PYTHONPATH=src uv run python scripts/test_chat.py

list-redis: ## List all Redis sessions with message counts
	@echo "📊 Listing Redis sessions..."
	PYTHONPATH=src uv run python scripts/test_redis.py

api-dev: run-redis
	@echo "🚀 Starting FastAPI development server..."
	PYTHONPATH=src uv run uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

api-prod: ## Start FastAPI in production mode
	@echo "🚀 Starting FastAPI production server..."
	@echo "📝 Make sure Redis is running (make redis-start)"
	PYTHONPATH=src uv run uvicorn src.api.app:app --workers 4 --host 0.0.0.0 --port 8000
