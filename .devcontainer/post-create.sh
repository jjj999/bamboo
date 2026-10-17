#!/usr/bin/env bash
set -euo pipefail

poetry config virtualenvs.in-project true --local
poetry install --with dev,docs
npm install --global @openai/codex@0.163.0

python --version
poetry --version
poetry run pytest --version
poetry run ruff --version
poetry run pyright --version
codex --version
claude --version
gh --version
