"""Module that describes the handle simple CityJSON city models."""

import json

min_cityjson = {
    "type": "CityJSON",
    "version": "1.1",
    "extensions": {},
    "metadata": {},
    "CityObjects": {},
    "vertices": []
}

class CityJSON:
    """Class that represents a CityJSON city model."""

    def __init__(self, data: dict = None):
        if data is None:
            self._citymodel = min_cityjson.copy()
        elif isinstance(data, dict):
            self._citymodel = data
        else:
            raise TypeError("Not a dictionary.")
        if "transform" in self._citymodel:
            self._coords_transformer = CoordinatesTransformer(
                data["transform"]["translate"],
                data["transform"]["scale"])
        else:
            self._coords_transformer = CoordinatesTransformer([0, 0, 0],
                                                              [1, 1, 1])
        self._vertex_handler = IndexedVerticesHandler(self)

    @classmethod
    def from_file(cls, filename: str):
        """Loads a CityJSON from a given file."""
        cityjson_data = open(filename, encoding="UTF-8")
        try:
            citymodel = json.load(cityjson_data)
        except Exception as exp:
            raise TypeError("Not a JSON file!") from exp
        cityjson_data.close()

        return cls(citymodel)

    @property
    def coordinates_transformer(self):
        """Returns the coordinates trasnformer for the given object."""
        return self._coords_transformer

    @property
    def data(self):
        """Returns the origina json data."""
        return self._citymodel

    @property
    def cityobjects(self):
        """Returns the city objects."""
        return CityObjectDict(self._citymodel["CityObjects"])

    def set_transform(self, translate, scale):
        """Sets the translation and scale of vertices in the model."""
        self._citymodel["transform"] = {
            "translate": translate,
            "scale": scale
        }
        self._coords_transformer = CoordinatesTransformer(translate, scale)
        self._vertex_handler.update_vertex_list()

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
        with open(filename, "w", encoding="UTF-8") as outfile:
            json.dump(self.data, outfile)

class CityObjectDict:
    """Wrapper class for a dict of city objects."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key: str) -> 'CityObject':
        #TODO: This should dereference the vertices
        return CityObject(self._data[key], key)

    def __setitem__(self, key: str, value: 'CityObject'):
        #TODO: This should reference the vertices
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

    def copy(self):
        """Make a copy of this object."""
        return CityObject(self._data.copy(), self._name)

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

class IndexedVerticesHandler:
    """Class that handles vertices of city objects as indices with a global
    list of coordinates in the city model.
    """

    def __init__(self, citymodel: 'VersionedCityJSON', precision: int = 3):
        self._citymodel = citymodel
        self._precision = precision
        self._lookup = {}
        self.prepare_cache()

    def prepare_cache(self):
        """Calculates the lookup cache for vertices."""
        cm = self._citymodel.data
        h = {}
        for v in cm["vertices"]:
            c = self._citymodel.coordinates_transformer.decode_coords(v)
            s = ("{{x:.{p}f}} {{y:.{p}f}} {{z:.{p}f}}"
                 .format(p=self._precision).format(x=c[0], y=c[1], z=c[2]))
            if s not in h:
                newid = len(h)
                h[s] = newid
        self._lookup = h

    def update_vertex_list(self):
        """Updates the city model's vertex list based on the lookup."""
        new_vertices = []
        for v in self._lookup:
            new_v = list(map(float, v.split()))
            new_v = self._citymodel.coordinates_transformer.encode_coords(new_v)
            new_vertices.append(new_v)
        self._citymodel["vertices"] = new_vertices

    def dereference(self, cityobject: 'CityObject'):
        """Dereferences the geometries of the provided city object.

        The city object is expected to have boundary values as indices, so this
        method will replace them with the actual coordinates."""
        new_object = cityobject.copy()
        for geom in new_object["geometry"]:
            l = geom["boundaries"]
            self.dereference_list(l)
        return new_object

    def dereference_list(self, vertex_list: list):
        """Dereferences a list of vertices (e.g. 'boundaries')."""
        for i, l in enumerate(vertex_list):
            if isinstance(l, list):
                self.dereference_list(l)
            else:
                vertex_list[i] = self.get_coords_of_index(l)

    def get_coords_of_index(self, i: int) -> list:
        """Returns the coordinates of the i-th vertex from the global list."""
        return self._citymodel["vertices"][i]

    def reference(self, cityobject: 'CityObject'):
        """References the geometries of the provided city object."""
        new_object = cityobject.copy()
        for geom in new_object["geometry"]:
            l = geom["boundaries"]
            self.reference_list(l)
        return new_object

    def reference_list(self, vertex_list: list):
        """References a list of vertices."""
        for i, l in enumerate(vertex_list):
            if isinstance(l[0], list):
                self.reference_list(l)
            else:
                vertex_list[i] = self.get_index_of_coords(l)

    def get_index_of_coords(self, v: list) -> int:
        """Returns the index of the specified coords in the global list."""
        s = ("{{x:.{p}f}} {{y:.{p}f}} {{z:.{p}f}}"
             .format(p=self._precision).format(x=v[0], y=v[1], z=v[2]))
        if s in self._lookup:
            return self._lookup[s]

        newid = len(self._lookup)
        self._lookup[s] = newid
        return newid

class CoordinatesTransformer:
    """Class that transforms coordinates according to the given parameters."""

    def __init__(self, translate: list, scale: list):
        self._translate = translate
        self._scale = scale

    def decode_coords(self, coords: list):
        """Applies the transformation to the provided coordinates."""
        return [coords[0] * self._scale[0] + self._translate[0],
                coords[1] * self._scale[1] + self._translate[1],
                coords[2] * self._scale[2] + self._translate[2]]

    def encode_coords(self, coords: list):
        """Applies the reverse transformation to the provided coordinates."""
        return [int((coords[0] - self._translate[0]) / self._scale[0]),
                int((coords[1] - self._translate[1]) / self._scale[1]),
                int((coords[2] - self._translate[2]) / self._scale[2])]
