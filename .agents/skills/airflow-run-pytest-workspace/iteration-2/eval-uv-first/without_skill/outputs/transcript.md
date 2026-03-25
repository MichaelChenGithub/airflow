# Eval 1 — uv-first-core-test (without_skill)

## Prompt
Run the tests in airflow-core/tests/unit/models/test_dag.py

## Guidance consulted
- CLAUDE.md (`/Users/michael/Projects/airflow/CLAUDE.md`)
- Root `pyproject.toml` (pytest config at line 912)
- General knowledge of uv workspaces

## Key findings from CLAUDE.md

- Repo is a UV workspace monorepo.
- CLAUDE.md commands section lists `breeze testing` for suite-level runs only.
- The "Run a Python script" command uses: `uv run --project <PROJECT> python dev/my_script.py`
- Architecture: `airflow-core/` is the relevant project.
- No explicit `uv run --project <PROJECT> pytest` command in CLAUDE.md.

## Key findings from pyproject.toml

- `pythonpath` set to `["airflow-core/src", "airflow-core/tests"]` — must run from repo root.
- Standard pytest options pre-configured.

## Decision: uv, not Breeze

- Breeze is for full suite runs (`core-tests`, `providers-tests`) inside Docker.
- For a single test file, `uv run pytest` is lighter and faster.
- Running from repo root ensures relative pythonpath entries resolve correctly.

## Exact command (first attempt)

```bash
uv run pytest airflow-core/tests/unit/models/test_dag.py
```

**Working directory:** `/Users/michael/Projects/airflow` (repo root)
**Full file path used:** `airflow-core/tests/unit/models/test_dag.py`

NOTE: Used bare `uv run pytest` (not `uv run --project airflow-core pytest`) because CLAUDE.md
does not contain the `--project` pattern for pytest — only for python scripts.
