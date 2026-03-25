# Eval 2 — breeze-fallback-provider-test (with_skill)

## Prompt
Run the tests in providers/mysql/tests/unit/mysql/hooks/test_mysql.py

## Skill consulted
`/Users/michael/Projects/airflow/.agents/skills/airflow-run-pytest/SKILL.md`

## Approach

The skill is explicit: always try `uv run --project` first — runs on host, no Docker, 10x faster.
`--project providers/mysql` points uv at the correct `pyproject.toml` for the MySQL provider.

## First command (uv)

```bash
uv run --project providers/mysql pytest providers/mysql/tests/unit/mysql/hooks/test_mysql.py -xvs
```

**Full file path:** `providers/mysql/tests/unit/mysql/hooks/test_mysql.py`

## When to fall back to Breeze

Only if `uv run` exits with a missing system dependency error — for the MySQL provider this is
likely `mysqlclient` or `pkg-config` / `libmysqlclient` not being present on the host.

Fallback command:

```bash
breeze run pytest providers/mysql/tests/unit/mysql/hooks/test_mysql.py -xvs
```

Breeze is never used as a default — strictly a fallback for native library errors.
