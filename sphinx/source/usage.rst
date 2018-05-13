How to use ETo
===============

This section will describe how to use the ETo package.

Initialising
------------
The package and general usage is via the main ETo class. It can be initialised without any initial input parameters.

.. code:: python

    from eto import ETo, datasets
    import pandas as pd

    et1 = ETo()

.. ipython:: python
   :suppress:

   from eto import ETo, datasets
   import pandas as pd

   et1 = ETo()

Parameter estimation
---------------------
The input data can be read into the class at initiatisation or via the param_est function.

We first need to get an example dataset and read it in via pd.read_csv.

.. code:: python

    ex1_path = datasets.get_path('example1')
    tsdata = pd.read_csv(ex1_path, parse_dates=True, infer_datetime_format=True, index_col='date')

Now we can run the parameter estimation using the newly loaded in dataset using the default parameters.

.. code:: python

    et2 = et1.param_est(tsdata)


Calculate ETo
-------------
Now it's just a matter of running the specific ETo function. For example, the FAO ETo.

.. code:: python

    et3 = et2.eto_fao()
