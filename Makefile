.DEFAULT_GOAL := help
.PHONY: help bootstrap check check-all test deps-upgrade

help:
	@echo "Available targets:"
	@echo "  help                 - Show this help message"
	@echo "  bootstrap            - Install all development tools and hooks"
	@echo "  check                - Run checks on staged changes"
	@echo "  check-all            - Run checks on all files"
	@echo "  test                 - Run the full pytest suite"
	@echo "  deps-upgrade         - Bump kivy nightly, pre-commit hooks, npm dev deps"

bootstrap:
	@echo "==> Installing Python 3.12 (via uv)..."
	uv python install 3.12
	@echo "==> Installing pre-commit..."
	uv tool install pre-commit || uv tool upgrade pre-commit
	@echo "==> Installing pre-commit hooks..."
	@PATH="$(HOME)/.local/bin:$(PATH)" pre-commit install
	@echo ""
	@echo "==> Bootstrap complete!"
	@echo "    Make sure $(HOME)/.local/bin is on your PATH."

check:
	pre-commit run

check-all:
	pre-commit run --all-files

# Run occasionally (e.g. monthly). Everything else is handled by Dependabot
# (.github/dependabot.yml); this covers what it cannot: the exact-pinned
# kivy nightly, pre-commit hook revs, and npm dev deps.
deps-upgrade:
	uv lock --upgrade-package kivy
	uv sync
	pre-commit autoupdate
	cd web && npm update
	@echo "==> If ruff was bumped, sync its version in .github/workflows/ci.yaml"

test:
	@echo "==> Checking help for quick-herbalist..."
	uv run quick-herbalist --help >/dev/null
	@echo "==> Checking help for manage-sprites..."
	uv run manage-sprites --help >/dev/null
	@echo "==> Running pytest..."
	uv run pytest -v
