.. _installation:

Installation
============

The `geopyv` package contains C++ code that must be compiled.
Binary wheels for most platforms are supplied alongside the source distribution on PyPi,
which allows pip or pipenv to install geopyv.

Via pip or pipenv
~~~~~~~~~~~~~~~~~

To install geopyv via pip:

.. code-block:: python

   pip install geopyv

Or via pipenv:

.. code-block:: python

   pipenv install geopyv

Compile from source
~~~~~~~~~~~~~~~~~~~

If you want to make edits and then compile from the source code you will need to install git and a C++ compiler.
It is recommended to use pipenv in order to develop in a virtualenv. All of the C++ dependencies are loaded by git as
submodules so you can then simply:

.. code-block:: bash

   git clone https://github.com/sas229/geopyv.git
   cd geopyv
   cd external
   git submodule update --init
   cd ..
   pip install pipenv
   pipenv shell
   pipenv install --dev -e .

This will set `geopyv` up as a package in the virtualenv managed by pipenv, but will allow you to make edits to the Python source
without having to recompile the C++ extensions.
