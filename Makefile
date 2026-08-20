PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
VENV_PYTHON ?= python3.12
PWSH ?= pwsh
VENV_STAMP := .venv/.requirements-installed

.PHONY: setup lint test report powershell-test verify verify-all

setup: $(VENV_STAMP)

$(VENV_STAMP): pyproject.toml
	@if [ ! -x "$(PYTHON)" ]; then \
		command -v "$(VENV_PYTHON)" >/dev/null 2>&1 || { \
			echo "$(VENV_PYTHON) is required" >&2; \
			exit 1; \
		}; \
		"$(VENV_PYTHON)" -m venv .venv; \
	fi
	$(PIP) install --disable-pip-version-check -e . pytest ruff
	@touch $(VENV_STAMP)

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest -q

report:
	PYTHONPATH=src $(PYTHON) -m tenant_guard.cli inventory/sample-tenant.json \
		--output reports/local --fail-on never

powershell-test:
	@command -v "$(PWSH)" >/dev/null 2>&1 || { echo "pwsh is required" >&2; exit 1; }
	$(PWSH) -NoProfile -Command \
		'if (-not (Get-Module -ListAvailable Pester | Where-Object Version -ge 5.6.1)) { Install-Module Pester -MinimumVersion 5.6.1 -Force -Scope CurrentUser }; Invoke-Pester powershell/tests -CI'

verify: setup lint test report

verify-all: verify powershell-test
