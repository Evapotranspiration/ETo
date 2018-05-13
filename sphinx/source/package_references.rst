MSSQL
======

The mssql module contains a variety of functions to interact with MSSQL databases through Python and Pandas.

Reading tables
--------------

.. autofunction:: pdsql.mssql.rd_sql

.. autofunction:: pdsql.mssql.rd_sql_ts

.. autofunction:: pdsql.mssql.rd_sql_geo

Creating tables
---------------

.. autofunction:: pdsql.mssql.create_mssql_table

Writing to tables
-----------------

.. autofunction:: pdsql.mssql.to_mssql

Updating tables
---------------

.. autofunction:: pdsql.mssql.update_mssql_table_rows

Deleting rows in tables
---------------------

.. autofunction:: pdsql.mssql.del_mssql_table_rows

Helper functions
----------------

.. autofunction:: pdsql.mssql.sql_where_stmts

.. autofunction:: pdsql.mssql.sql_ts_agg_stmt


API Pages
---------

.. currentmodule:: pdsql
.. autosummary::
  :template: autosummary.rst
  :toctree: mssql/
