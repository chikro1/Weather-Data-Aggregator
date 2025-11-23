# Repository Guidelines

## Project Structure & Modules
- `src/` core code: `clients/` (API wrappers for Open-Meteo, NOAA ISD/LCD, Meteostat, NASA POWER, IEM ASOS, GIBS), `exporters/` (dataframe/image exporters + registry), `core/` (config/date/runtime helpers), `visualization/` (coverage chart).
- `scripts/`: CLI entry points (`combined_export.py` for full runs, `healthcheck.py` for quick provider checks).
- `tests/`: smoke tests (`test_basic.py` imports/instantiation).
- `config.json` (user secrets and layers) and `config.json.template` (safe starter). Data and logs are written to `data/` and `logs/` when running exports.

## Build, Test, and Development Commands
- Create env: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Example export (one shot, all providers): `python3 scripts/combined_export.py --once`.
- Targeted run (GIBS only, 2 days, first location): `python3 scripts/combined_export.py --once --providers gibs --limit-locations 1 --since 2023-11-21 --until 2023-11-22 --gibs-frequency 1d`.
- Health check sample fetches: `python3 scripts/healthcheck.py`.
- Tests: `pytest` (currently only basic import test present).

## Coding Style & Naming
- Python-only; follow PEP 8 defaults (4-space indents, snake_case for variables/functions, PascalCase for classes).
- Keep JSON configs formatted with two-space indents as in repo.
- When adding modules, place provider code under `src/clients/`, export logic under `src/exporters/`, and shared helpers under `src/core/`.

## Testing Guidelines
- Add/extend pytest suites under `tests/`; mirror package structure where possible.
- Prefer deterministic, network-free unit tests; for API wrappers, mock HTTP calls.
- Name tests `test_*.py` and functions `test_*`.
- Run `pytest` before opening a PR; add coverage for new branches/edge cases.

## Commit & PR Guidelines
- Write clear, descriptive commits (present tense, concise scope, e.g., `Add GIBS layer validation`).
- PRs should summarize scope, note config changes (e.g., new provider settings), and include runtime/test results (`pytest`, sample `combined_export.py` invocation if relevant).
- Highlight any breaking changes (config schema shifts, new required tokens).

## Security & Configuration Tips
- Do not commit real tokens; keep secrets in `config.json` (gitignored). Use `config.json.template` for defaults.
- Validate GIBS layers against WMS `Name` values; invalid layers produce XML error payloads instead of PNGs.
- Large runs write to `data/` and `logs/`; clean old runs before new benchmarks to avoid confusion.
