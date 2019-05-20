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

Instead of ``versionedCityJson.json`` you can just type ``init`` to start with an empty file (useful in combination with the ``commit`` command to create a versioned CityJSON).

The available commands are (a *ref* can be a *version*, *branch* or *tag*.
):

- ``log``, show the history of the project starting from a ``ref`` (default is ``master``):

```
./cjv.py vCityJson.json log [<ref>]
```

- ``checkout``, extracts a regular CityJSON from a specific version:

```
./cjv.py vCityJson.json checkout <ref> <output.json>
```

- ``diff``, shows the changes between two *refs*:

```
./cjv.py vCityJson.json diff <new_ref> <old_ref>
```

- ``commit``, adds a new version from a CityJSON (``input.json``) with ``base_ref`` as parent:

```
./cjv.py vCityJson.json commit <input.json> <base_ref> <author> <message> [<output.json>]
```

- ``rehash``, converts all city object and version ids to hash (SHA-1):

```
./cjv.py vCityJson.json rehash <output.json>
```

## Examples

You can create a new versioned CityJSON using ``init`` and ``commit``:

```
./cjv.py init commit input_file.json master "John Doe" "Initial commit" new_vcityjson.json
```

You can show the log of ``master`` branch:

```
./cjv.py Examples/buildingBeforeAndAfter.json log master
```

You can checkout a version to a regular CityJSON as follows:

```
./cjv.py Examples/buildingBeforeAndAfter.json checkout v30 buildingAtVersion30.json
```

## TODO

- Add support for geometry-templates, textures and materials\
- Offer a help per commandcj
- Add option to append objects except for just replacing current ones?