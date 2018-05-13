ETo - A Python package for calculating reference evapotranspiration
===================================================================

The ETo package contains a class and associated functions to calculate reference evapotranspiration (ETo) using the `UN-FAO 56 paper <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ [1]. Additional functions have been added to calculate historic ETo or potential evapotranspiration (PET) for comparison purposes.

A parameter estimation function hs also been added to the base class to convert most any variety of metereological parameter inputs to the necessary parameters needed to calculate ETo.


.. toctree::
   :maxdepth: 2
   :caption: Modules

   intro
   installaiton
   methods
   usage
   .. package_references
   license-terms


.. [1] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop evapotranspiration-Guidelines for computing crop water requirements-FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.
