.PHONY: format
format:
	@poetry run autoflake -ri --remove-all-unused-imports --ignore-init-module-imports --remove-unused-variables --exclude venv,node_modules .
	@poetry run black .
	@poetry run isort .

.PHONY: check-format
check-format:
	@poetry run black --diff --check .
	@poetry run isort --check-only .

.PHONY: test
test:
	@poetry run pytest tests $(ARGS)
