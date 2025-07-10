# Refactor get_occupancy_summary for ruff

Ruff reports `PLR0911 Too many return statements` in `get_occupancy_summary`. The function currently has seven returns.

## Tasks
- [ ] Simplify the control flow to reduce the number of return statements, or configure ruff to ignore `PLR0911` for this function.
- [ ] Ensure the refactor keeps existing behavior and all tests pass.
