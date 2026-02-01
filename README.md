# Orchestration Cockpit

## PyCharm Execution Assumption
- Script is executed from project root.
- All relative paths are resolved from project root.
- Do NOT change working directory at runtime.

## Discovery Policy
- Search engines are discovery-only.
- Cached URLs are the source of truth.
- Re-scraping discovery sources on every run is forbidden.
- Clearing discovery cache is a conscious, manual act.
