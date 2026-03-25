---
name: airflow-run-pytest
description: Run pytest for Apache Airflow tests. Use this skill whenever you need to run, execute, or trigger tests, pytest, or test files in the Airflow repository. Handles the correct uv-first execution pattern with Breeze as fallback for system dependency errors. Also use when deciding which command to use for running tests, or when choosing between uv and Breeze for test execution. Always use this skill in the Airflow repo — don't rely on generic pytest knowledge.
compatibility: Requires uv installed on host. Breeze (Docker) required only as fallback.
---

## How to run Airflow tests

Airflow is a uv workspace monorepo. Always try uv first — it runs on the host, needs no Docker,
and is 10x faster than Breeze.

```bash
uv run --project <PROJECT> pytest <path> -xvs
```

`<PROJECT>` is the folder containing `pyproject.toml` for the package you want to test:

| What you're testing | `<PROJECT>` |
|---|---|
| Core Airflow | `airflow-core` |
| A provider | `providers/<name>` (e.g. `providers/amazon`, `providers/mysql`) |
| Task SDK | `task-sdk` |

### Examples

```bash
# Core test
uv run --project airflow-core pytest airflow-core/tests/unit/models/test_dag.py -xvs

# Provider test
uv run --project providers/mysql pytest providers/mysql/tests/unit/mysql/hooks/test_mysql.py -xvs
```

## Airflow 3.x test paths

Test paths changed in Airflow 3.x. Always use the new structure:

- **Core:** `airflow-core/tests/unit/<subfolder>/test_<name>.py`
- **Provider:** `providers/<name>/tests/unit/<subfolder>/test_<name>.py`

Old Airflow 2.x paths like `tests/models/test_dag.py` no longer exist — don't use them.

## When uv fails: fall back to Breeze

If `uv run` fails with a missing system dependency error (e.g. `mysqlclient`, `pkg-config`,
`libxml`), fall back to:

```bash
breeze run pytest <path> -xvs
```

`breeze run` starts a fresh Docker container with all system deps pre-installed, runs the command,
and cleans up automatically. Pass the same host-relative path — Breeze maps it internally.

**Always try `uv run --project` first.** Only reach for `breeze run` after a system dependency
error — not as a default, not because it "feels safer".

## Breeze command reference

| Command | Use for |
|---|---|
| `breeze run pytest <path>` | Fallback test execution — non-interactive, exits when done |
| `breeze shell` | Interactive debugging inside the container |
| `breeze exec` | Exec into an already-running Breeze container |

Do not use `breeze shell` to run tests — it starts an unnecessary interactive session.
