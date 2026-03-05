[![CI](https://github.com/DiamondLightSource/dls-bba/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/dls-bba/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/dls-bba/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/dls-bba)
[![PyPI](https://img.shields.io/pypi/v/dls-bba.svg)](https://pypi.org/project/dls-bba)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# dls_bba

Fast & Slow BBA (Beam Based Alignment) Python tools.

This repository is a Python 3 implementation of slow, fast and simultaneous beam-based
alignment for Diamond Light Source. The slow BBA process is intended to replicate the
behaviour of MATLAB BBA. Both command line and graphical user based interfaces have been
included alongside the standard python module level interface for ease of use.

Source          | <https://github.com/DiamondLightSource/dls-bba>
:---:           | :---:
PyPI            | `pip install dls-bba`
Docker          | `docker run ghcr.io/diamondlightsource/dls-bba:latest`
Documentation   | <https://diamondlightsource.github.io/dls-bba>
Releases        | <https://github.com/DiamondLightSource/dls-bba/releases>

- To use the command line interface:
    - To show the version: ``dls-bba -v``
    - To show the help menu: ``dls-bba -h``

- To use the graphical interface:
    - To show the version: ``dls-bba-gui -v``
    - To load the GUI: ``dls-bba-gui``

- Additional information about BBA:
    - DLS Paper: "Development of Fast BBA for Diamond Light Source" <https://proceedings.jacow.org/ipac2023/pdf/MOPA139.pdf>
    - ALBA Paper: "Fast beam-based alignment using ac excitations" <https://journals.aps.org/prab/abstract/10.1103/PhysRevAccelBeams.23.012802>



<!-- README only content. Anything below this line won't be included in index.md -->

See https://diamondlightsource.github.io/dls-bba for more detailed documentation.
