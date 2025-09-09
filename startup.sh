#!/bin/bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Use uv with pyproject.toml (much better!)
uv sync --frozen

# Start the application
exec "$@"