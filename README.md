# CityJSON versioning prototype

A prototype implementation of interaction with versioned CityJSON files.

## Requirements

- Python 3 (with ``json`` and ``colorama`` modules)

## Installation

Just clone this repository and install Python 3 with the above modules.

In Unix-like operating systems, you might also need to add execution permission to ``cjv.py``:

```
chmod u+x cjv.py
```

## Usage

General syntax is:

```
./cjv.py versionedCityJson.json <command> [<args>]
```

The command can be:
- ``log`` with one optional argument: ``<ref>``, or
- ``checkout`` with two arguments: ``<version_name> <output_cityjson>``.

## Examples

You can show the log of ``master`` branch:

```
./cjv.py Examples/buildingBeforeAndAfter.json log master
```

You can checkout a version to a regular CityJSON as follows:

```
./cjv.py Examples/buildingBeforeAndAfter.json checkout v30 buildingAtVersion30.json
```