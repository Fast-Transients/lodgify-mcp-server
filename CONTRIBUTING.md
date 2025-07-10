# Contributing

Thank you for considering contributing to the Lodgify MCP Server! To get started:

1. **Install development dependencies**

   Use `uv` to install all development requirements into your environment:

   ```bash
   uv pip install --system -e '.[dev]'
   ```

   This installs the server in editable mode along with testing tools.

2. **Run pre-commit checks**

   Ensure code passes linting, type checking and tests:

   ```bash
   ruff check .
   mypy .
   pytest
   ```

   The CI will run the same commands, so it's best to verify locally first.

3. **Code style**

   Follow the existing code style and keep changes focused.

Feel free to open an issue or pull request with any questions!
