# Bluesgoal v2.0.0 Fix Bundle

These files are replacements/additions for the `jpk300/bluesgoal` `v2.0.0` branch.

## What This Addresses

- Converts live `goalhorn/_*.php` endpoints to JSON responses expected by `index.html`.
- Adds `goalhorn/_helpers.php` for shared JSON response handling, activity logging, command execution, and nonblocking action locks.
- Adds the missing `log_activity.py` PHP logging bridge.
- Adds the missing `goalhorn/_status.php` endpoint and `goalhorn/status/status.py` backend used by the UI volume/audio indicator.
- Updates the remaining active Python master scripts that still used `python` to use Python 3.
- Removes malformed trailing output from the live goalhorn PHP endpoints by replacing them completely.

## Notes

- Sound-trigger endpoints use `/tmp/bluesgoal_action.lock` so only one long-running horn/music action runs at a time.
- Stop and volume endpoints intentionally do not use that long-running lock so Stop stays responsive and volume can be adjusted while audio is active.
- The GitHub connector available in this Codex session could read the repo but returned `403 Resource not accessible by integration` for branch/file writes, so this bundle was prepared locally instead of pushed directly.
