Additionally, you can enter an interactive shell with ``breeze`` and run tests from there to iterate. Source files in ``breeze`` are mounted as volumes, so you can modify them locally and
rerun in Breeze as needed (``-n auto`` will parallelize tests using the ``pytest-xdist`` plugin):

.. code-block:: bash

    breeze shell --backend none --python 3.10
    > pytest airflow-core/tests --skip-db-tests -n auto
