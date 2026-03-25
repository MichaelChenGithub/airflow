# Eval 2 — breeze-fallback-provider-test (without_skill)

## Prompt
Run the tests in providers/mysql/tests/unit/mysql/hooks/test_mysql.py

## Guidance consulted
- CLAUDE.md (`/Users/michael/Projects/airflow/CLAUDE.md`)
- Test file inspection: `providers/mysql/tests/unit/mysql/hooks/test_mysql.py`

## Key findings from CLAUDE.md

- Only provider test commands in CLAUDE.md use `breeze testing`:
  `breeze testing providers-tests --test-type "Providers[mysql]"`
- No `uv run --project providers/mysql pytest` pattern present.
- SQLite is default backend; `--backend mysql` only needed for integration tests.

## Key findings from test file

- Imports `MySQLdb`, skips if not available (`@pytest.mark.skipif(not MYSQL_AVAILABLE, ...)`)
- All connections are mocked — no live DB needed.
- Located under `tests/unit/`, confirming unit tests.

## Decision: Breeze as default

The MySQL provider depends on `mysqlclient`, which requires native C libraries
(`libmysqlclient-dev`) often absent on the local host. CLAUDE.md only shows `uv run` for
Python scripts, not pytest. Breeze is the standard recommended tool for provider tests.

## Exact command (first attempt)

```bash
breeze testing providers-tests -- providers/mysql/tests/unit/mysql/hooks/test_mysql.py
```

**Full file path used:** `providers/mysql/tests/unit/mysql/hooks/test_mysql.py`

NOTE: Jumped straight to Breeze without attempting `uv run --project providers/mysql pytest`
first. CLAUDE.md provided no guidance on the uv-first pattern for pytest.
