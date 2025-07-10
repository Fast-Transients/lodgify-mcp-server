# Add unit tests for get_occupancy_summary

The PR #33 introduces error handling for invalid date strings in `get_occupancy_summary`, but there are no tests covering these cases.

## Tasks
- [ ] Write pytest tests verifying that invalid `start_date` or `end_date` return `{"success": False}` with the expected error message.
- [ ] Test that invalid date entries in calendar data also trigger the error path.
