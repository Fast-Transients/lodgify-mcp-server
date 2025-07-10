# LLM Contributor Guide

This repository contains a Model Context Protocol (MCP) server for the Lodgify vacation rental API.
Use this document as a quick reference when proposing changes via an LLM.

## Repository overview
- Python 3.10+ project (`pyproject.toml` defines dependencies and dev tools)
- Entry point: `entrypoint.py`
- Main server module: `lodgify_server.py`
- Configuration examples live in the `examples/` directory
- Tests live under `tests/`

## Development setup
1. Install dev dependencies
   ```bash
   uv pip install --system -e '.[dev]'
   ```
2. Run the unit tests
   ```bash
   pytest
   ```
3. Follow the existing code style. The project uses `ruff` (line length 88)
   and `mypy` with `disallow_untyped_defs = true`.
4. Ensure `LODGIFY_API_KEY` is set when running the server.

## Useful commands
- Start the server with uvx:
  ```bash
  export LODGIFY_API_KEY=your_key
  uvx lodgify-mcp-server
  ```
- Run from source:
  ```bash
  uv run python entrypoint.py
  ```

## Contribution tips
- Keep documentation concise and avoid duplication.
- Update or add tests when changing code.
- See `CONTRIBUTING.md` for more details.
