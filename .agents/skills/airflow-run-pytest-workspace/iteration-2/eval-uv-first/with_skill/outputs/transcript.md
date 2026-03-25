# Eval 1 — uv-first-core-test (with_skill)

## Prompt
Run the tests in airflow-core/tests/unit/models/test_dag.py

## Skill consulted
`/Users/michael/Projects/airflow/.agents/skills/airflow-run-pytest/SKILL.md`

## Approach

The skill is explicit: always try `uv run --project` first. It runs on the host with no Docker
overhead and is ~10x faster than Breeze. Breeze is only a fallback for system dependency errors
(e.g., missing `mysqlclient`, `pkg-config`, `libxml`). `test_dag.py` is a core Airflow model
test with no known C-library system dependencies, so there is no reason to reach for Breeze.

## First command (uv)

```bash
uv run --project airflow-core pytest airflow-core/tests/unit/models/test_dag.py -xvs
```

**Path used:** `airflow-core/tests/unit/models/test_dag.py`
This is the Airflow 3.x path structure (`airflow-core/tests/unit/<subfolder>/test_<name>.py`).
The skill explicitly warns against using the old 2.x path (`tests/models/test_dag.py`).

## Fallback (only if uv fails with a system dep error)

```bash
breeze run pytest airflow-core/tests/unit/models/test_dag.py -xvs
```

Breeze is held in reserve — not the default, not because it "feels safer".
