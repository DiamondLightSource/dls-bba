[![pipeline status](https://gitlab.diamond.ac.uk/controls/python3/pyburt/badges/master/pipeline.svg)](https://gitlab.diamond.ac.uk/controls/python3/pyburt/commits/master)
[![coverage report](https://gitlab.diamond.ac.uk/controls/python3/pyburt/badges/master/coverage.svg)](https://gitlab.diamond.ac.uk/controls/python3/pyburt/commits/master)
[![Documentation Status](https://readthedocs.org/projects/pyburt/badge/?version=latest)](https://pyburt.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blueviolet.svg)](https://www.python.org/downloads/release/python-373/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# pyburt

**pyburt** is the Python version of the Burt EPICS extension. It utilises the
[cothread](https://cothread.readthedocs.io/en/latest/) python library for
Channel Access operations.

## Documentation

Full documentation is available at [readthedocs](https://readthedocs.org/projects/pyburt/).

## Installation

```bash
$ pipenv install pyburt
```

## Development

```bash
$ git clone git@gitlab.diamond.ac.uk:controls/python3/pyburt.git
$ cd pyburt
$ pipenv install -d
$ python setup.py install
```

## API Usage

```python
import burt

# Saves PV values in a single .req file into a .snap file along with some additional
# metadata.
burt.take_snapshot(["/path/to/.req/file.req"],
    "/path/to/.snap/file.snap", "comment", "keywords")

# As above, except take a snapshot of several .req files, combining the values into
# one .snap file.
burt.take_snapshot(["/path/to/.req/file.req", "/path/to/.req/file2.req"],
    "/path/to/.snap/file.snap", "comment", "keywords")
    
# Restores PV values in a .snap file.
burt.restore("/path/to/.snap/file.snap")

# Specify a restore group to restore.
burt.restore_group("/path/to/.rgr/file.rgr")
    
# TODO: specify a request group to take a snapshot of.
burt.take_snapshot_group("/path/to/.rqg/file.rqg",
    "/path/to/.snap/file.snap", "comment", "keywords")
```

## CLI Usage

```bash
$ burt-read -h
usage: burt-read [-h] [-c C] [-k K] [-v] [-l L] request_file snap_destination

positional arguments:
  request_file      The path to either a .req or .rqg file.
  snap_destination  The path to the destination .snap file.

optional arguments:
  -h, --help        show this help message and exit
  -c C              Optional snapshot comments.
  -k K              Optional snapshot keywords.
  -v                Enable verbose logging (debug) level.
  -l L              Optional backup log file destination.
```

```bash
$ burt-write -h
usage: burt-write [-h] [-v] [-l L] restore_file

positional arguments:
  restore_file  The path to either a .snap or .rgr file.

optional arguments:
  -h, --help    show this help message and exit
  -v            Enable verbose logging (debug) level.
  -l L          Optional restore log file destination.
```

## License

See [LICENSE](). 

### Build
 
To build the Sphinx documentation:

```bash
$ pipenv shell
(pyburt) $ cd docs
(pyburt) $ make html
```

The generated pages are in `docs/_build/html`.

### Tests

##### Unit Tests
To run the core pytest unit tests:

```bash
$ pipenv shell
$ pytest -vv test
```

Note: the unit tests should be run from the root project directory.

##### DLS Integration Tests

There are separate DLS integration tests for pyburt. These tests run snapshot
and restore operations against known Diamond and Pytac PV's. See 
`integration/README.md` for instructions.

Note that running pytest against `integration` without running the test IOC
 first,
as described in `integration/README.md`, will cause the tests to
fail.
