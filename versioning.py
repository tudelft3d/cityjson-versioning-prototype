"""Module that contains logic to handle versioned CityJSON files"""

from typing import Dict, List
import json
import utils

class VersionedCityJSON:
    """Class that represents a versioned CityJSON file."""

    def __init__(self, file):
        if file is None:
            self._citymodel = utils.create_vcityjson()
        elif isinstance(file, str):
            cityjson_data = open(file)
            try:
                citymodel = json.load(cityjson_data)
            except:
                raise TypeError("Not a JSON file!")
            cityjson_data.close()

            self._citymodel = citymodel
        elif isinstance(file, dict):
            self._citymodel = file
        else:
            raise TypeError("Not a file or a dictionary.")

    @property
    def versioning(self):
        """Returns the versioning aspect of CityJSON"""
        return Versioning(self, self._citymodel["versioning"])

    def __repr__(self):
        return self._citymodel

class Versioning:
    """Class that represents the versioning aspect of a CityJSON file."""

    def __init__(self, citymodel, data: dict):
        self._citymodel = citymodel
        self._json = data

    @property
    def versions(self) -> Dict[str, 'Version']:
        """Returns a dictionary of versions."""
        versions = {k : Version(self, j)
                    for k, j
                    in self._json["versions"].items()}
        return versions

    @property
    def branches(self) -> Dict[str, 'Version']:
        """Returns a dictionary of branches."""
        branches = {k : self.versions[j]
                    for k, j
                    in self._json["branches"].items()}
        return branches

    @property
    def tags(self) -> Dict[str, 'Version']:
        """Returns a dictionary of tags."""
        tags = {k : self.versions[j]
                for k, j
                in self._json["tags"].items()}
        return tags

    def __repr__(self):
        return str(self._json)

class Version:
    """Class that represent a CityJSON version."""

    def __init__(self, versioning, data: dict):
        self._versioning = versioning
        self._json = data

    @property
    def author(self):
        """Returns the author of this version."""
        return self._json["author"]

    @property
    def message(self):
        """Returns the message of this version."""
        return self._json["message"]

    @property
    def date(self):
        """Returns the date and time of this version."""
        return self._json["date"]

    @property
    def parents(self) -> List['Version']:
        """Returns the id of the parent(s) version(s)."""
        if self.has_parents():
            return [self._versioning.versions[v]
                    for v in self._json["parents"]]

        return []

    def has_parents(self):
        """Returns 'True' if the version has parents, otherwise 'False'."""
        return "parents" in self._json

    def __repr__(self):
        return str(self._json)
