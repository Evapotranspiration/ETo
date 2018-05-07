A Project Template for a Github project with code and webpage
=============================================================

This git repository contains sample skeleton of what is needed to set up a project
that can be compiled into a Python package in PyPI and to create a documentation
webpage. This repository is meant to be housed on a git platform like GitHub,
which can host both the code and the webpage.

There are three primary template sources: `sampleproject <https://github.com/pypa/sampleproject>`_, `python-packaging <https://python-packaging.readthedocs.io/en/latest/>`_, and `Automating GIS-processes <https://automating-gis-processes.github.io/2016>`_

The sampleproject and python-packaging describe how to prepare a Python project to package it for PyPI, while the Automating GIS-processes describes how to create very nice documentation (especially for natural scientists) using Sphinx and GitHub. `Readthedocs <https://readthedocs.org>`_ is used to run Sphinx and the associated code to create the website htmls, which then gets hosted on the Readthedocs servers. This is not necessary as the website can easily be hosted via GitHub as well. Readthedocs just automates the build process, which then doesn't need to performed by the user.

Only minor changes have been made from the original two repositories other than the removal or commenting out of certain parts due to the unnessecary bloatiness for a template (Automating GIS-processes) or functions that are unecessary for this kind of template (sampleproject). These can be esaily added back in if needed.

The associated documentation in the `official site <https://packaging.python.org/tutorials/distributing-packages/>`_ for the sampleproject is the official PyPI packaging site and includes how to create wheels during the packaging process.

The documentation to create a conda package from a PyPI package can be found `here <https://conda.io/docs/user-guide/tutorials/build-pkgs-skeleton.html>`_.

The associated webpage for this repository can be found `here <http://project-template1.readthedocs.io>`_.

Building packages for Pip and PyPI
-----------------------------------
This will summarize the necessary steps as decribed in the `official site <https://packaging.python.org/tutorials/distributing-packages/>`_ and `python-packaging <https://python-packaging.readthedocs.io/en/latest/>`_.

Clone this repository, then open and modify the root setup.py file. Most options are self explanitary and the above websites have sufficient info about the setup.py configuration.

Additionally, the folder that contains the actual python modules needs to have a well defined __init__.py file. Unlike normal __init__.py files that can simply be left empty, the one directly in the hilltoppy folder must directly reference the modules that need to be called. See the __init__.py in the hilltoppy directory as an example. If it is left empty, then the package will contain no modules.

Once the setup.py, __init__.py, and the modules as arranged appropriately make sure that setuptools and pip are installed::

  pip install setuptools pip

or::

  conda install setuptools pip

Then check to make sure that everything builds properly by running the following in the root directory::

  pip install .

If everything builds correctly, your new package should be installed in your Python installation.
To test, run a Python instance, try to import the package, and load a module::

  python
  import hilltoppy
  hilltoppy.com.makepy_hilltop()

If the package can be loaded and a module/function can be executed, then the building was successful. If not, uninstall the package, troubleshoot the issue(s), and reinstall the package.

To updoad the package to PyPI, register on `PyPI <https://pypi.org/>`_ and create a .pypirc file in your user home directory like `here <https://docs.python.org/3.2/distutils/packageindex.html>`_.

Finally, repackage and upload the package to PyPI with the following::

  python setup.py sdist upload

Building packages for conda and anaconda
-----------------------------------------
Building packages for conda/anaconda seems easiest when a PyPI package is used as a base (`skeleton <https://conda.io/docs/user-guide/tutorials/build-pkgs-skeleton.html>`_).
Create a folder called conda within the root directory and run the following to create a conda yaml file with all of the info that conda needs to build the package::

  conda skeleton pypi hilltop-py

Where hilltop-py would be the package name in PyPI.

**Note:** You may need to install m2-patch via conda if skeleton fails.

A meta.yml file will have been created with the necessary config info for conda. Look over it and make some tweaks to descriptions or names if necessary. Then, in the directory with the meta.yml file, run the following to build the conda package::

  conda-build .

If it builds sucessfully, then it will recommend to upload the package to anaconda that looks something like::

  anaconda upload D:\programs\Anaconda3_64bit\conda-bld\win-64\pdsql-1.0.1-py36_0.tar.bz2

Follow the explanation `here <https://conda.io/docs/user-guide/tutorials/build-pkgs-skeleton.html#optional-uploading-packages-to-anaconda-org>`_ on how to do this.

Building the documentation in Sphinx
-------------------------------------
Building the documentation is well described on the `Automating GIS-processes <https://github.com/Automating-GIS-processes/2016>`_ github page. It's not necessary to install specific versions of sphinx or the sphinx_rtd_theme nor is it necessary to install the google analytics package. The example rst files in this repository should be used. Make sure to modify the setup.py in the source folder in the sphinx folder with the necessary requirements to build the sphinx html files. If the output of the make html build is placed in a root folder called docs, then github can host the website with the GitHub Pages setting.

An alternative to building the html files and having GitHub host the website is to use `Readthedocs <https://readthedocs.org>`_ to do both. First, make sure that the env.yml file in the sphinx is correctly configured for Readthedocs to build the html from sphinx. Then register with Readthedocs. Then make sure your GitHub repository is public. Then on Readthedocs, pull the appropriate repository. Finally, in the Readthedocs project page, under Admin then advanced settings, add sphinx/source/conf.py for the path to the config file.

Read through both the config.py files in the root and source directories for some of the nuances for readthedocs. Go to the `pdsql <https://github.com/mullenkamp/pdsql>`_ github repository for examples of linking the package functions to the documentation.
