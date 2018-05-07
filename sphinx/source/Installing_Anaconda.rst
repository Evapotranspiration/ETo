Installing Python
=======================

.. note::

	**If you are using the RDS for running all of the Python code, this section can be skipped**

**How to start using Python on your own computer?**

The purpose of this page is to help you
to install Python and all those modules into your own computer. Even though it is possible to install Python from their `homepage <https://www.python.org/>`_,
**we highly recommend using** `Anaconda <https://www.continuum.io/anaconda-overview>`_ which is an open source distribution of the Python and R programming
languages for large-scale data processing, predictive analytics, and scientific computing, that aims to simplify package management and deployment. In short,
it makes life much easier when installing new tools on your Python to play with.

Installing Python on Windows
-------------------------------

Following steps have been tested to work on Windows 7, 8, and 10 with Anaconda3 version 4.3.0.

`Download Anaconda installer (64 bit) <https://www.continuum.io/downloads>`_ for Windows.

Install Anaconda to your computer by double clicking the installer and install it into a directory you want.
Install for **Just Me** then use the desination folder **C:\\Anaconda2_64bit**. You will not need admin rights and you will be able to install additional Python packages as needed.

Test that the Anaconda´s package manage called ``conda`` works by `opening a command prompt <http://www.howtogeek.com/194041/how-to-open-the-command-prompt-as-administrator-in-windows-8.1/>`_
and running command ``conda --version``.

Anaconda installs the base Python packages and many additional 3rd-party packages that are very useful. Nevertheless, Anaconda does not install all necessary packages.
Install additional packages with conda (and pip) by running in command prompt following commands (in the same order as they are listed):

.. code::

    conda install -y psycopg2 matplotlib bokeh holoviews seaborn xarray networkx pymssql bottleneck dask netCDF4
    conda install -y -c conda-forge basemap pyproj fiona shapely pyproj rtree geopandas rasterio cartopy
    conda install -y -c ioam geoviews
    pip install pycrs lxml

Let's also upgrade few packages:

.. code::

    conda upgrade spyder pandas scipy

Install Python on Linux / Mac
-----------------------------------

The following have been tested on Ubuntu 16.04. Might work also on Mac (not tested yet).

**Install Anaconda 3 and add it to system path**

.. code::

    # Download and install Anaconda
    sudo wget https://repo.continuum.io/archive/Anaconda3-4.1.1-Linux-x86_64.sh
    sudo bash Anaconda3-4.1.1-Linux-x86_64.sh

    # Add Anaconda installation permanently to PATH variable
    nano ~/.bashrc

    # Add following line at the end of the file and save (EDIT ACCORDING YOUR INSTALLATION PATH)
    export PATH=$PATH:/PATH_TO_ANACONDA/anaconda3/bin:/PATH_TO_ANACONDA/anaconda3/lib/python3.5/site-packages

**Install Python packages**

.. code::

    conda install -y psycopg2 matplotlib bokeh holoviews seaborn xarray networkx pymssql bottleneck dask netCDF4
    conda install -y -c conda-forge basemap pyproj fiona shapely pyproj rtree geopandas rasterio cartopy
    conda install -y -c ioam geoviews
    pip install pycrs lxml


How to find out which conda -command to use when installing a package?
----------------------------------------------------------------------

The easiest way
~~~~~~~~~~~~~~~

The first thing to try when installing a new module ``X`` is to run in a command prompt following command (here we try to install a hypothetical
module called X)

.. code::

    conda install X

In most cases this approach works but sometimes you get errors like (example when installing a module called shapely):

.. code::

    C:\WINDOWS\system32>conda install shapely
    Using Anaconda API: https://api.anaconda.org
    Fetching package metadata .........
    Solving package specifications: .
    Error: Package missing in current win-64 channels:
      - shapely

    You can search for packages on anaconda.org with

        anaconda search -t conda shapely

Okay, so conda couldn't find the shapely module from the typical channel it uses for downloading the module.


Alternative way to install if typical doesn't work
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

How to find a way to install a module if it cannot be installed on a typical way?
Well, the answer is the same is in many other cases nowadays, **Google it!**

Let's find our way to install the Shapely module by typing following query to Google:

.. image:: img/google_query_conda.PNG

Okay, we have different pages showing how to install Shapely using conda package manager.

**Which one of them is the correct one to use?**

We need to check the operating system banners and if you find a logo of the operating system of your computer,
that is the one to use! Thus, in our case the first page that Google gives does not work in Windows but the second one does, as it has Windows logo on it:

.. image:: img/conda_shapely_windows.PNG

From here we can get the correct installation command for conda and it works!

.. image:: img/install_shapely.PNG

You can follow these steps similarly for all of the other Python modules that you are interested to install.


