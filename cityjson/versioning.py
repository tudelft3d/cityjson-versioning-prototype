"""Module that contains logic to handle versioned CityJSON files"""

import abc
import datetime
import hashlib
import json
from typing import Dict, List

from cityjson.citymodel import CityJSON, CityObject
import utils

class Hashable(abc.ABC):
    """Class that represents a hashable object."""

    @property
    @abc.abstractmethod
    def data(self):
        """Returns the original json data of the object."""

    def hash(self):
        """Computes the hash of the objects."""
        encoded = json.dumps(self.data).encode('utf-8')
        m = hashlib.new('sha1')
        m.update(encoded)

        return m.hexdigest()

class VersionedCityJSON(CityJSON):
    """Class that represents a versioned CityJSON file."""

    @property
    def versioning(self):
        """Returns the versioning aspect of CityJSON"""
        return Versioning(self, self._citymodel["versioning"])

class Versioning:
    """Class that represents the versioning aspect of a CityJSON file."""

    def __init__(self, citymodel, data: dict = None):
        self._citymodel = citymodel
        if data is None:
            self._json = {
                "versions": {},
                "branches": {},
                "tags": {}
            }
        else:
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

class Version(Hashable):
    """Class that represent a CityJSON version."""

    _date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self,
                 versioning: 'Versioning',
                 data: dict = None,
                 version_name: str = None):
        self._versioning = versioning
        if data is None:
            self._json = {}
        else:
            self._json = data

        if version_name is None:
            self._version_name = utils.get_hash_of_object(data)
        else:
            self._version_name = version_name

    @property
    def name(self):
        """Returns the id of this version."""
        return self._version_name

    @name.setter
    def name(self, value):
        """Updates the id of this version."""
        self._version_name = value

    @property
    def author(self):
        """Returns the author of this version."""
        return self._json["author"]

    @author.setter
    def author(self, value: str):
        """Updates the author of this version."""
        self._json["author"] = value

    @property
    def message(self):
        """Returns the message of this version."""
        return self._json["message"]

    @message.setter
    def message(self, value: str):
        """Updates the value of message."""
        self._json["message"] = value

    @property
    def date(self):
        """Returns the date and time of this version."""
        return datetime.datetime.strptime(self._json["date"], self._date_format)

    @date.setter
    def date(self, value: datetime.datetime):
        """Updates the date and time of this version."""
        self._json["date"] = value.strftime(self._date_format)

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

class VersionedCityObject(Hashable):
    """Class that represents a versioned city object."""

    def __init__(self, cityobject: 'CityObject', name: str = None):
        self._cityobject = cityobject
        if name is None:
            self._name = self.hash()
        else:
            self._name = name

    @property
    def original_cityobject(self):
        """Returns the original city object."""
        return self._cityobject

    @property
    def data(self):
        return self._cityobject.data

    @property
    def name(self):
        return self._name
