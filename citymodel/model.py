"""A module that describes the semantic data model of a 3D city model"""

class CityModel:
    """Describes a 3D city model"""

    def __init__(self, cityobjects=[]):
        self._cityobjects = {c.cityobject_id: c for c in cityobjects}
    
    @property
    def cityobjects(self):
        return self._cityobjects

class CityObject:
    """Describes a city object"""

    def __init__(self, cityobject_id: str, objtype: str, attributes=None, geometry=None, children=None):
        self._cityobject_id = cityobject_id
        self._type = objtype
        self._attributes = attributes
        self._geometry = geometry
        self._children = children

    @property
    def cityobject_id(self) -> str:
        """Return the id of the city object"""
        return self._cityobject_id
    
    @property
    def children(self):
        """Return the parent city object"""
        return self._children

    @property
    def type(self) -> str:
        """Return the type of the city object"""
        return self._type
    
    @property
    def attributes(self):
        """Return the attributes of the city object"""
        return self._attributes

    @property
    def geometry(self):
        """Return the geometry of the city object"""
        return self._geometry

    def __repr__(self):
        """Return a dictionary that represents the city object"""

        result = {
            "cityobject_id": self._cityobject_id,
            "type": self._type,
            }

        if self._attributes is not None:
            result["attributes"] = self._attributes
        
        if self._geometry is not None:
            result["geometry"] = self._geometry

        return repr(result)

class Building(CityObject):
    """Describes a building"""

    def __init__(self, cityobject_id, attributes={}, geometry=None):
        CityObject.__init__(self, cityobject_id, "Building", attributes, geometry)