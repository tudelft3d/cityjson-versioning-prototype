# CityJSON versioning prototype

A prototype implementation of interaction with versioned CityJSON files.

This tool implements versioning as initially proposed in [Vitalis et al, 2019](https://www.isprs-ann-photogramm-remote-sens-spatial-inf-sci.net/IV-4-W8/123/2019/).

## Requirements

- Python 3 with virtualenv

## Installation

Clone this repository and install Python 3 with virtualenv.

To install the script and necessary dependencies:

```
virtualenv venv
. venv/bin/activate
pip install --editable .
```

Then you can use the application by calling `cjv`.

## Usage

General syntax is:

```
cjv versionedCityJson.json <command> [<args>]
```

Instead of ``versionedCityJson.json`` you can just type ``init`` to start with an empty file (useful in combination with the ``commit`` command to create a versioned CityJSON).

Call `cjv` with no arguments to list all commands. Help for an individual command is available with:

```
cjv <command_name> --help
```

The available commands are (a *ref* can be a *version*, *branch* or *tag*):

### ``log``
Shows the history of the project starting from a ``ref`` (default is ``master``):

```
cjv vCityJson.json log [<ref>]
```

### ``checkout``

Extracts a regular CityJSON from a specific version:

```
cjv vCityJson.json checkout <ref> <output.json>
```

### ``diff``

Shows the changes between two *refs*:

```
cjv vCityJson.json diff <new_ref> <old_ref>
```

### ``commit``

Adds a new version from a CityJSON (``input.json``) with ``base_ref`` as parent:

```
cjv vCityJson.json commit <input.json> [<base_ref>] [-a <author>] [-m <message>] [-o <output.json>]
```

If a ``base_ref`` is not provided, then the ``master`` branch is implied.

Available options:
- `-a` or `--author`: name of the commit's author (if not provided, user will be prompted),
- `-m` or `--message`: description of the commit's changes (if not provided user will be prompted),
- `-o` or `--output`: the output filename (if not provided the original versioned CityJSON file will be written)

### ``branch``

Creates a branch at a given ``base_ref`` (default is ``master``):

```
cjv vCityJson.json branch <branch_name> [<base_ref>]
```

or deletes a branch using the `-d` or `--delete` flag:

```
cjv vCityJson.json branch -d <branch_name>
```

### ``merge``

Merges ``source_ref`` to ``dest_ref``:

```
cjv vCityJson.json merge <source_ref> <dest_ref>
```

Normally you'd use branches for refs.

### ``rehash``

Converts all city object and version ids to hash (SHA-1):

```
cjv vCityJson.json rehash <output.json>
```

## Examples

You can create a new versioned CityJSON using ``init`` and ``commit``:

```
cjv init commit input_file.json master -a "John Doe" -m "Initial commit" -o new_vcityjson.json
```

You can show the log of ``master`` branch:

```
cjv Examples/buildingBeforeAndAfter.json log master
```

You can checkout a version to a regular CityJSON as follows:

```
cjv Examples/buildingBeforeAndAfter.json checkout v30 buildingAtVersion30.json
```

## TODO

- Add support for compressed CityJSONs.
- Add support for geometry-templates, textures and materials.
- Add option to append objects except for just replacing current ones?