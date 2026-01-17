# Repository Guidelines

## Project Structure & Module Organization
- `app.py` is the Flask entry point (`create_app`) and registers blueprints.
- Route handlers live in `route_*.py` (e.g., `route_user_rel.py`), with additional REST modules in `api/`.
- Shared libraries are under `py_lib/`, including `db_libs/`, `fileop_libs/`, `models/`, and `run_lang/`.
- Environment helpers and examples are in `py_lib/helper_libs/` (use `example.env.json` to create `.env.json`).
- Reference docs and diagrams live in `README.md`, `UML.md`, `flowchart.md`, and `DB_Schema.svg`.
- Local config files include `config.yaml` and `test_config.yaml`.

## Build, Test, and Development Commands
- `python3 -m venv .venv` then `source .venv/bin/activate` to set up the virtualenv.
- `pip install -r requirement.txt` installs Python dependencies.
- `python3 app.py` runs the development server (defaults to `0.0.0.0:5050`).
- `flask --app easygrade-flask-server` is also supported if you follow README setup.
- One-time setup: create `assignments/` and `submissions/` at the repo root and set `PYTHONPATH` to `py_lib/helper_libs`.

## Coding Style & Naming Conventions
- Python uses 4-space indentation and `snake_case` for modules/functions.
- Route modules follow `route_<domain>_rel.py`; API modules use `<domain>_api.py`.
- No formatter or linter is enforced; keep changes minimal and readable.

## Testing Guidelines
- No automated test framework is wired in. `py_lib/db_libs/test_db.py` is a manual DB stress script.
- If you add tests, prefer a `tests/` folder with `test_*.py` naming and document how to run them.

## Commit & Pull Request Guidelines
- Commit history is descriptive but informal; keep messages short and specific (e.g., “Add JWT to User Auth”).
- PRs should include: purpose, setup/config changes, and how to validate (commands or sample requests).

## Security & Configuration Tips
- Store secrets in `.env.json`; never commit credentials.
- Update `ROOT_PATH` in `py_lib/helper_libs/import_helper.py` and set DB/AWS values in `.env.json`.
