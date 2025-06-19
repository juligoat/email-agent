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
	@echo "4. Test: make demo"

.PHONY: run
run: ## Start the autonomous email agent
	@echo "🚀 Starting Autonomous Email Agent..."
	@uv run python teton_email_agent/main.py

.PHONY: demo
demo: ## Run the interview demonstration
	@echo "🎬 Running interview demo..."
	@uv run python interview_demo.py

.PHONY: check
check: ## Run code quality tools
	@echo "🚀 Checking code quality: Running pre-commit"
	@uv run pre-commit run -a

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run pytest

.PHONY: quick-test
quick-test: ## Quick readiness check for interview
	@echo "🔍 Quick readiness check..."
	@uv run python quick_test.py

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

.PHONY: setup-env
setup-env: ## Setup environment file from example
	@if [ ! -f .env ]; then \
		echo "⚙️ Creating .env file from example..."; \
		cp .env.example .env; \
		echo "🔑 Please add your GROQ_API_KEY to .env file"; \
	else \
		echo "✅ .env file already exists"; \
	fi

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

.PHONY: interview-prep
interview-prep: install setup-env quick-test ## Complete interview preparation
	@echo ""
	@echo "🎯 INTERVIEW PREPARATION COMPLETE!"
	@echo "========================================="
	@echo "📋 Checklist:"
	@echo "  ✅ Dependencies installed"
	@echo "  ✅ Environment configured"
	@echo "  ✅ Quick test passed"
	@echo ""
	@echo "🔑 Final steps:"
	@echo "1. Add GROQ_API_KEY to .env (https://console.groq.com)"
	@echo "2. Start agent: make run"
	@echo "3. Run demo: make demo"
	@echo ""
	@echo "🏆 Ready for interview success!"

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
