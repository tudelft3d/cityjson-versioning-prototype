"""Module that contains logic to handle versioned CityJSON files"""

import abc
import datetime
import hashlib
import json
from typing import Dict, List

from colorama import Fore, Style
from cityjson.citymodel import CityJSON, CityObject

empty_vcityjson = {
    "type": "CityJSON",
    "version": "1.0",
    "CityObjects": {
    },
    "versioning": {
        "versions": {},
        "tags": {},
        "branches": {}
    },
    "vertices": [],
    "appearance": {},
    "geometry-templates": {}
}

class Hashable(abc.ABC):
    """Abstract class that represents a hashable object."""

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

    def __init__(self, data: dict = None):
        if data is None:
            self._citymodel = empty_vcityjson.copy()
        else:
            super(VersionedCityJSON, self).__init__(data)

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
    def citymodel(self) -> 'VersionedCityJSON':
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

    def add_version(self, new_version: 'Version'):
        """Adds version to the city model."""
        if new_version.name is None:
            new_version.name = new_version.hash()
        self._json["versions"][new_version.name] = new_version.data

    @property
    def branches(self) -> Dict[str, 'Version']:
        """Returns a dictionary of branches."""
        branches = {k : self.versions[j]
                    for k, j
                    in self._json["branches"].items()}
        return branches

    def set_branch(self, branch_name: str, version: 'Version'):
        """Sets the branch to a specific version."""
        self._json["branches"][branch_name] = version.name

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

    def __init__(self,
                 versioning: 'Versioning',
                 data: dict = None,
                 version_name: str = None):
        self._versioning = versioning
        self._date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        if data is None:
            self._json = {
                "objects": {}
            }.copy()
        elif isinstance(data["objects"], list):
            raise Exception("This is an old versioning file!")
        else:
            self._json = data

        if version_name is None:
            self._version_name = self.hash
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

    def add_parent(self, value: 'Version'):
        """Adds a parent version to this version."""
        if "parents" not in self._json:
            self._json["parents"] = [value.name]
        else:
            self._json["parents"].append(value.name)

    @property
    def versioned_objects(self) -> List['VersionedCityObject']:
        """Returns a list of versioned city objects."""
        cm = self._versioning.citymodel

        result = []
        for obj_id, vobj_id in self._json["objects"].items():
            if vobj_id not in cm.cityobjects:
                print("  Object '%s' not found! Skipping..." % vobj_id)
                continue

            obj = CityObject(cm.cityobjects[vobj_id].data, obj_id)
            vobj = VersionedCityObject(obj, vobj_id)
            result.append(vobj)

        return result

    def add_cityobject(self, value: 'VersionedCityObject'):
        """Adds the provided versioned city object to the version."""
        self._json["objects"][value.original_cityobject.name] = value.name

        cm = self._versioning.citymodel["CityObjects"]
        cm[value.name] = value.original_cityobject.data

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

    def __eq__(self, obj):
        return self.hash() == obj.hash()

    def __hash__(self):
        return int(self.hash(), 16)

    @property
    def original_cityobject(self) -> 'CityObject':
        """Returns the original city object."""
        return self._cityobject

    @property
    def data(self):
        return self._cityobject.data

    @property
    def name(self):
        """Returns the name of the city object."""
        return self._name

class SimpleVersionDiff:
    """Class that implements the calculation of a diff of two versions."""

    def __init__(self, source_version: 'Version', dest_version: 'Version'):
        self._source_version = source_version
        self._dest_version = dest_version
        self._result = VersionsDiffResult()

    def compute(self) -> 'VersionsDiffResult':
        """Computes the diff of the provided versions."""

        new_objects = (set(self._dest_version.versioned_objects) -
                       set(self._source_version.versioned_objects))

        old_objects = (set(self._source_version.versioned_objects) -
                       set(self._dest_version.versioned_objects))

        same_objects = (set(self._dest_version.versioned_objects).intersection(
                        set(self._source_version.versioned_objects)))

        new_names = {obj.original_cityobject.name: obj
                     for obj in new_objects}
        old_names = {obj.original_cityobject.name: obj
                     for obj in old_objects}

        # new_objects might contain changed ones
        common_names = set(obj.original_cityobject.name for obj in new_objects
                           if obj.original_cityobject.name in old_names)

        new_objects = set(obj for obj in new_objects
                          if obj.original_cityobject.name not in common_names)
        old_objects = set(obj for obj in old_objects
                          if obj.original_cityobject.name not in common_names)

        result = VersionsDiffResult()

        for obj_id in common_names:
            result.changed[obj_id] = {
                "source": old_names[obj_id],
                "dest": new_names[obj_id]
            }

        for obj in new_objects:
            result.added[obj.original_cityobject.name] = obj

        for obj in old_objects:
            result.removed[obj.original_cityobject.name] = obj

        for obj in same_objects:
            result.unchanged[obj.original_cityobject.name] = obj

        return result

class VersionsDiffResult:
    """Class that represents a versions' diff result."""

    def __init__(self):
        self.changed: Dict[str, Dict[str, VersionedCityObject]] = {}
        self.added: Dict[str, VersionedCityObject] = {}
        self.removed: Dict[str, VersionedCityObject] = {}
        self.unchanged: Dict[str, VersionedCityObject] = {}

    def print(self):
        """Prints the diff to the output console."""
        print("\nChanges:\n")

        if len(self.changed) > 0:
            print("{color}".format(color=Fore.BLUE), end='')
            for obj_name, objs in self.changed.items():
                print("\tchanged: {id} ({old_hash} -> {new_hash})"
                      .format(id=obj_name,
                              old_hash=trim_string(objs["source"].name),
                              new_hash=trim_string(objs["dest"].name)))
        if len(self.added) > 0:
            print("{color}".format(color=Fore.GREEN), end='')
            for obj_name, obj in self.added.items():
                print("\tadded: {id} ({hash})"
                      .format(id=obj_name, hash=trim_string(obj.name)))
        if len(self.removed) > 0:
            print("{color}".format(color=Fore.RED), end='')
            for obj_name, obj in self.removed.items():
                print("\tremoved: {id} ({hash})"
                      .format(id=obj_name, hash=trim_string(obj.name)))

        if len(self.unchanged) > 0:
            print("{color}\n{objcount} objects not changed.\n"
                  .format(color=Style.RESET_ALL, objcount=len(self.unchanged)))

def trim_string(text, width=15, suffix=".."):
    """Trims a string at the given width."""
    if len(text) > width:
        return "{text}{suffix}".format(text=text[:width], suffix=suffix)

    return text
