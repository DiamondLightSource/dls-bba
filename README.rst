dls-bba
===========================

|code_ci| |docs_ci| |coverage| |pypi_version| |license|

dls-bba is a Python 3 implimentation of beam-based alignment processes.

============== ==============================================================
PyPI           ``pip install dls-bba``
Source code    https://github.com/DiamondLightSource/dls-bba
Documentation  https://DiamondLightSource.github.io/dls-bba
Releases       https://github.com/DiamondLightSource/dls-bba/releases
============== ==============================================================

.. |code_ci| image:: https://github.com/DiamondLightSource/dls-bba/actions/workflows/code.yml/badge.svg?branch=main
    :target: https://github.com/DiamondLightSource/dls-bba/actions/workflows/code.yml
    :alt: Code CI

.. |docs_ci| image:: https://github.com/DiamondLightSource/dls-bba/actions/workflows/docs.yml/badge.svg?branch=main
    :target: https://github.com/DiamondLightSource/dls-bba/actions/workflows/docs.yml
    :alt: Docs CI

.. |coverage| image:: https://codecov.io/gh/DiamondLightSource/dls-bba/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/DiamondLightSource/dls-bba
    :alt: Test Coverage

.. |pypi_version| image:: https://img.shields.io/pypi/v/dls-bba.svg
    :target: https://pypi.org/project/dls-bba
    :alt: Latest PyPI version

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License

Introduction
============

Description
-----------

This repository is a Python 3 implimentation of slow, fast and simultaneous beam-based alignment for Diamond Light Source.
The slow BBA process was written in MATLAB, but has been converted to be included into the tool, whereas the fast based processes were written specifically in Python.
Both command line and graphical user based interfaces have been included alongside the standard python module level interface for ease of use.

Instructions
------------

Installation:
    ``pip install dls-bba``

To use the command line interface:
    To show the version: ``dls-bba -v``
    To show the help menu: ``dls-bba -h``

To use the graphical interface:
    To show the version: ``dls-bba-gui -v``
    To load the GUI: ``dls-bba-gui``

Additional information about BBA
--------------------------------

- DLS Paper {preproc}: `"Development of Fast BBA for Diamond Light Source" <https://www.ipac23.org/preproc/doi/mopa139/index.html>`_
- ALBA Paper: `"Fast beam-based alignment using ac excitations" <https://journals.aps.org/prab/abstract/10.1103/PhysRevAccelBeams.23.012802>`_


..
    Anything below this line is used when viewing README.rst and will be replaced
    when included in index.rst

See https://DiamondLightSource.github.io/dls-bba for more detailed documentation.
