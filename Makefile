install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh; source ~/.bashrc; }
	uv sync --dev --extra jupyter --frozen

test:
	uv run pytest tests/unit && uv run pytest tests/integration

playground:
	@echo "+-----------------------------------------------------------------------------+"
	@echo "| Starting ADK Web Server via 'adk web' command.                              |"
	@echo "|                                                                             |"
	@echo "| Please select the app folder to start interacting with your agent.          |"
	@echo "+-----------------------------------------------------------------------------+"
	uv run adk web

backend:
	# Export dependencies to requirements file using uv export (preferred method), otherwise fall back to uv pip freeze
	uv export --no-hashes --no-sources --no-header --no-dev --no-emit-project --no-annotate --frozen > .requirements.txt 2>/dev/null || \
	uv pip freeze --exclude-editable > .requirements.txt && uv run app/agent_engine_app.py



setup-dev-env:
	@if [ -z "$$PROJECT_ID" ]; then echo "Error: PROJECT_ID environment variable is not set"; exit 1; fi
	(cd deployment/terraform/dev && terraform init && terraform apply --var-file vars/env.tfvars --var dev_project_id=$$PROJECT_ID --auto-approve)


lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .
