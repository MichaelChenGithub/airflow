If you want to iterate on tests, you can enter the interactive shell and run tests iteratively—either by package/module/test or by test type, whatever ``pytest`` supports.

.. code-block:: bash

    breeze shell --backend postgres --python 3.10
    > pytest airflow-core/tests --run-db-tests-only

As explained before, you cannot run DB tests in parallel using the ``pytest-xdist`` plugin. However, ``breeze`` supports splitting all tests into test-types to run in separate containers with separate databases using the ``--run-in-parallel`` flag.

.. code-block:: bash

    breeze testing core-tests --run-db-tests-only --backend postgres --python 3.10 --run-in-parallel
