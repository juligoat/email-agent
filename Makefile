PYTHON_VERSION := 3.12

.PHONY: install
install: ## Install the virtual environment and dependencies
	@echo "🚀 Installing python $(PYTHON_VERSION)"
	@uv python install $(PYTHON_VERSION)
	@uv python pin $(PYTHON_VERSION)
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install
	@uv export --locked --no-dev --format requirements-txt > requirements.txt
	@echo "✅ Installation complete!"
	@echo ""
	@echo "🔑 Next steps:"
	@echo "1. Get FREE Groq API key: https://console.groq.com"
	@echo "2. Add it to .env file: GROQ_API_KEY=your_key_here"
	@echo "3. Run: make run"

.PHONY: run
run: ## Start the enhanced email agent with dashboard
	@echo "🚀 Starting Enhanced Email Agent System..."
	@echo "📡 Starting API server on http://localhost:8000"
	@uv run python teton_email_agent/main.py &
	@echo "⏳ Waiting for API server to start..."
	@sleep 5
	@echo "🎨 Starting Streamlit dashboard on http://localhost:8501"
	@echo ""
	@echo "🎯 SYSTEM READY!"
	@echo "📊 Dashboard: http://localhost:8501"
	@echo "🔧 API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Press CTRL+C to stop dashboard, then 'make stop' to stop API"
	@uv run streamlit run dashboard/app.py

.PHONY: run-api-only
run-api-only: ## Start only the API server
	@echo "🚀 Starting API server only..."
	@uv run python teton_email_agent/main.py

.PHONY: run-dashboard-only
run-dashboard-only: ## Start only the dashboard
	@echo "🎨 Starting dashboard only..."
	@uv run streamlit run dashboard/app.py

.PHONY: setup-env
setup-env: ## Setup environment file from example
	@if [ ! -f .env ]; then \
		echo "⚙️ Creating .env file from example..."; \
		cp .env.example .env; \
		echo "🔑 Please add your GROQ_API_KEY to .env file"; \
	else \
		echo "✅ .env file already exists"; \
	fi

.PHONY: stop
stop: ## Stop all running services
	@echo "🛑 Stopping email agent services..."
	@pkill -f "python teton_email_agent/main.py" || echo "API server not running"
	@pkill -f "streamlit run dashboard/app.py" || echo "Dashboard not running"
	@echo "✅ All services stopped"

.PHONY: restart
restart: stop run ## Restart all services
	@echo "🔄 Restarting email agent system..."

.PHONY: status
status: ## Check system status
	@echo "📊 System Status Check:"
	@echo "======================"
	@pgrep -f "python teton_email_agent/main.py" > /dev/null && echo "📡 API Server: ✅ Running" || echo "📡 API Server: ❌ Stopped"
	@pgrep -f "streamlit run dashboard/app.py" > /dev/null && echo "🎨 Dashboard: ✅ Running" || echo "🎨 Dashboard: ❌ Stopped"
	@echo ""
	@echo "🔗 Access URLs:"
	@echo "📊 Dashboard: http://localhost:8501"
	@echo "🔧 API: http://localhost:8000"

.PHONY: clean
clean: ## Clean up cache and temporary files
	@echo "🧹 Cleaning up..."
	@rm -rf .pytest_cache
	@rm -rf __pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -name ".DS_Store" -delete

.PHONY: check
check: ## Run code quality tools
	@echo "🚀 Checking code quality: Running pre-commit"
	@uv run pre-commit run -a

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run pytest

.PHONY: lint
lint: ## Run linting tools
	@echo "🔍 Running linting..."
	@uv run ruff check .
	@uv run mypy teton_email_agent --ignore-missing-imports

.PHONY: format
format: ## Format code with black and ruff
	@echo "🎨 Formatting code..."
	@uv run ruff format .
	@uv run ruff check . --fix

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
