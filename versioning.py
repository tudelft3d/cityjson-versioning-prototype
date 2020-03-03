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

    def __getitem__(self, key):
        return self._citymodel[key]

    def __setitem__(self, key, value):
        self._citymodel[key] = value

    def __iter__(self):
        return self._citymodel.itervalues()

    def __contains__(self, item):
        return item in self._citymodel

    @property
    def versioning(self):
        """Returns the versioning aspect of CityJSON"""
        return Versioning(self, self._citymodel["versioning"])

    @property
    def data(self):
        """Returns the origina json data."""
        return self._citymodel

    @property
    def cityobjects(self):
        """Returns the city objects."""
        return self._citymodel["CityObjects"]

    @cityobjects.setter
    def cityobjects(self, value):
        """Sets the city objects dictionary."""
        self._citymodel["CityObjects"] = value

    def __repr__(self):
        return self._citymodel

class Versioning:
    """Class that represents the versioning aspect of a CityJSON file."""

    def __init__(self, citymodel, data: dict):
        self._citymodel = citymodel
        self._json = data

    @property
    def citymodel(self):
        """Returns the citymodel."""
        return self._citymodel

    @property
    def data(self):
        """Returns the original json data."""
        return self._json

    @data.setter
    def data(self, value):
        """Updates the json data."""
        self._json = value

    def resolve_ref(self, ref):
        """Returns the version name for the given ref."""
        candidates = [s for s in self.versions if s.startswith(ref)]
        if len(candidates) > 1:
            raise KeyError("{ref} is ambiguoush. Try with more characters!")
        if len(candidates) == 1:
            return candidates[0]

        if ref in self._json["branches"]:
            return self._json["branches"][ref]

        if ref in self._json["tags"]:
            return self._json["tags"][ref]

        raise KeyError("Ref is not available in versioning.")

    def is_branch(self, ref):
        """Returns True if the ref is a branch."""
        return ref in self._json["branches"]

    def get_version(self, ref):
        """Returns the version for the given ref."""
        return self.versions[self.resolve_ref(ref)]

    @property
    def versions(self) -> Dict[str, 'Version']:
        """Returns a dictionary of versions."""
        versions = {k : Version(self, j, k)
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

    def __init__(self, versioning, data: dict, version_name=None):
        self._versioning = versioning
        self._json = data

        if version_name is None:
            self._version_name = utils.get_hash_of_object(data)
        else:
            self._version_name = version_name

    @property
    def name(self):
        """Returns the id of this version."""
        return self._version_name

    @property
    def author(self):
        """Returns the author of this version."""
        return self._json["author"]

    @property
    def message(self):
        """Returns the message of this version."""
        return self._json["message"]

    @message.setter
    def message(self, value):
        """Updates the value of message."""
        self._json["message"] = value

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

    @property
    def versioned_objects(self):
        """Returns the dictionary of the versioned city objects."""
        cm = self._versioning.citymodel

        new_objects = {}
        for obj_id in self._json["objects"]:
            if obj_id not in cm.cityobjects:
                print("  Object '%s' not found! Skipping..." % obj_id)
                continue

            new_objects[obj_id] = cm.cityobjects[obj_id]

        return new_objects

    @property
    def original_objects(self):
        """Returns the dictionary of the original city objects."""
        objs = self.versioned_objects

        new_objects = {}
        for _, obj in objs.items():
            new_id = obj["cityobject_id"]
            del obj["cityobject_id"]
            new_objects[new_id] = obj

        return new_objects

    def has_parents(self):
        """Returns 'True' if the version has parents, otherwise 'False'."""
        return "parents" in self._json

    @property
    def branches(self):
        """Returns the list of branch names that link to this version."""
        result = [branch_name
                  for branch_name, version in self._versioning.branches.items()
                  if version.name == self._version_name]

        return result

    @property
    def tags(self):
        """Returns the list of tag names that link to this version."""
        result = [tag_name
                  for tag_name, version in self._versioning.tags.items()
                  if version.name == self._version_name]

        return result

    @property
    def data(self):
        """Returns the original json data."""
        return self._json

    def __repr__(self):
        repr_dict = self._json.copy()
        del repr_dict["objects"]
        return str(repr_dict)
