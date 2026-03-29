---
name: airflow-run-pytest
description: Run pytest for Apache Airflow tests. Use this skill whenever you need to run, execute, or trigger tests, pytest, or test files in the Airflow repository. Always attempt uv first, then fall back to Breeze only when system dependencies are missing.
compatibility: Requires uv installed on host. Breeze (Docker) required only as fallback.
---

.. code:: bash

    uv run pytest

Non-DB tests are run once for each tested Python version with the ``none`` database backend (which
causes any database access to fail). These tests are run with the ``pytest-xdist`` plugin in parallel, which
means we can efficiently utilize multi-processor machines (including ``self-hosted`` runners with
8 CPUs, where we run tests with maximum parallelism).

It is usually straightforward to run these tests in a local virtualenv because they do not require any
database setup. They also run much faster than DB tests. You can run them with the ``pytest`` command
or with ``breeze`` (which has all dependencies automatically installed). You can also select specific tests, folders, or modules for Pytest to collect/run.
The example below shows how to run all tests, parallelizing them with ``pytest-xdist`` (by specifying the ``tests`` folder):

.. code-block:: bash

    pytest airflow-core/tests --skip-db-tests -n auto

The ``--skip-db-tests`` flag will only run tests that are not marked as DB tests.

You can also use the ``breeze`` command to run all the tests (they will run in a separate container,
with the selected Python version and without access to any database). Adding the ``--use-xdist`` flag will run all
tests in parallel using the ``pytest-xdist`` plugin.

You can run parallel commands via ``breeze testing core-tests`` or ``breeze testing providers-tests``
by adding the parallel flags:

.. code-block:: bash

    breeze testing core-tests --skip-db-tests --backend none --use-xdist

You can pass a list of test types to execute via ``--parallel-test-type`` or exclude them via ``--exclude-parallel-test-types``:

.. code-block:: bash

    breeze testing providers-tests --run-in-parallel --skip-db-tests --backend none --parallel-test-types "Providers[google] Providers[amazon]"

.. code-block:: bash

    pytest airflow-core/tests --run-db-tests-only

You can also run DB tests within the ``breeze`` dockerized environment. You can choose the backend with the
``--backend`` flag. The default is ``sqlite``, but you can also use ``postgres`` or ``mysql``.
You can also select the backend version and Python version. Breeze will list the available test types via ``--help`` and provide auto-complete.
The example below runs ``Core`` tests with the ``postgres`` backend and Python ``3.10``:

You can also run the commands via ``breeze testing core-tests`` or ``breeze testing providers-tests``
by adding the parallel flags manually:

.. code-block:: bash

    breeze testing core-tests --run-db-tests-only --backend postgres --run-in-parallel

You can pass a list of test types to execute via ``--parallel-test-type`` or exclude them via ``--exclude-parallel-test-types``:

.. code-block:: bash

    breeze testing providers-tests --run-in-parallel --run-db-tests-only --parallel-test-types "Providers[google] Providers[amazon]"

.. code-block:: bash

    breeze testing core-tests --db-reset

You can run the whole providers test suite without adding the test target:

.. code-block:: bash

    breeze testing providers-tests --db-reset
