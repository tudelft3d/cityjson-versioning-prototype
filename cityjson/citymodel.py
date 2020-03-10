"""Module that describes the handle simple CityJSON city models."""

import json

import utils

class CityJSON:
    """Class that represents a CityJSON city model."""

    def __init__(self, data: dict = None):
        if data is None:
            self._citymodel = utils.create_vcityjson()
        elif isinstance(data, dict):
            self._citymodel = data
        else:
            raise TypeError("Not a file or a dictionary.")

    @classmethod
    def from_file(cls, filename: str):
        """Loads a CityJSON from a given file."""
        cityjson_data = open(filename)
        try:
            citymodel = json.load(cityjson_data)
        except:
            raise TypeError("Not a JSON file!")
        cityjson_data.close()

        return cls(citymodel)

    @property
    def data(self):
        """Returns the origina json data."""
        return self._citymodel

    @property
    def cityobjects(self):
        """Returns the city objects."""
        return CityObjectDict(self._citymodel["CityObjects"])

    def __repr__(self):
        return self._citymodel

    def __getitem__(self, key):
        return self._citymodel[key]

    def __setitem__(self, key, value):
        self._citymodel[key] = value

    def __iter__(self):
        return self._citymodel.itervalues()

    def __contains__(self, item):
        return item in self._citymodel

    def save(self, filename):
        """Saves the CityJSON model in a file."""
        with open(filename, "w") as outfile:
            json.dump(self.data, outfile)

class CityObjectDict:
    """Wrapper class for a dict of city objects."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key: str) -> 'CityObject':
        return CityObject(self._data[key], key)

    def __setitem__(self, key: str, value: 'CityObject'):
        self._data[key] = value._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return self._data.__iter__()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def __contains__(self, item):
        return item in self._data

class CityObject:
    """Class that represents a city object in CityJSON."""

    def __init__(self, data: dict = None, name: str = None):
        self._data = data
        self._name = name

    @property
    def name(self):
        """Returns the id of the city object."""
        return self._name

    @property
    def data(self):
        """Returns the original dict of the city object."""
        return self._data

    def __repr__(self):
        return self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.itervalues()

    def __contains__(self, item):
        return item in self._data
