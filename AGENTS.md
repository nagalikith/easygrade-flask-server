# Repository Guidelines

## Project Structure & Module Organization
- `app/main.py` is the FastAPI entry point and registers routers.
- Route handlers live in `app/routers/`.
- Shared libraries are under `app/py_lib/`, including `db_libs/`, `fileop_libs/`, `models/`, and `run_lang/`.
- Settings live in `app/core/settings.py` and load from `.env`.
- Reference docs and diagrams live in `README.md`, `UML.md`, `flowchart.md`, and `DB_Schema.svg`.
- Local config files include `config.yaml` and `test_config.yaml`.

## Build, Test, and Development Commands
- `python3 -m venv .venv` then `source .venv/bin/activate` to set up the virtualenv.
- `pip install -r requirement.txt` installs Python dependencies.
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 5050` runs the FastAPI server.
- One-time setup: create `assignments/` and `submissions/` at the repo root.

## Coding Style & Naming Conventions
- Python uses 4-space indentation and `snake_case` for modules/functions.
- Route modules follow a domain-first naming (e.g., `assignments.py`, `users.py`).
- No formatter or linter is enforced; keep changes minimal and readable.

## Testing Guidelines
- No automated test framework is wired in. `app/py_lib/db_libs/test_db.py` is a manual DB stress script.
- If you add tests, prefer a `tests/` folder with `test_*.py` naming and document how to run them.

## Commit & Pull Request Guidelines
- Commit history is descriptive but informal; keep messages short and specific (e.g., “Add JWT to User Auth”).
- PRs should include: purpose, setup/config changes, and how to validate (commands or sample requests).

## Security & Configuration Tips
- Store secrets in `.env`; never commit credentials.
- Configure `DB_INFO`, `AWS_CRED`, and `AWS_BUCKET` in `.env` (JSON strings for dict values).
