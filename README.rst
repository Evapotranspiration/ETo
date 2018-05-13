ETo - A Python package for calculating reference evapotranspiration
===================================================================

The ETo package contains a class and associated functions to calculate reference evapotranspiration (ETo) using the `UN-FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_. Additional functions have been added to calculate historic ETo or potential evapotranspiration (PET) for comparison purposes.

A parameter estimation function hs also been added to the base class to convert most any variety of metereological parameter inputs to the necessary parameters needed to calculate ETo.

Documentation
--------------
The primary documentation for the package can be found `here <http://eto.readthedocs.io>`_.

Installation
------------
ETo can be installed via pip or conda::

  pip install eto

or::

  conda install -c mullenkamp eto

The core dependency is Pandas.
