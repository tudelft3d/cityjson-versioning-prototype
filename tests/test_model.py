import pytest
from citymodel.model import CityModel, CityObject, Building
from citymodel.geometry import GeometryObject, MultiSurface

class TestCityObject:
    
    def test_id_and_type_is_initialised_properly(self):
        """Is a simple city object initialised properly?"""

        cityobject = CityObject("one_id", "Building")

        assert cityobject.cityobject_id == "one_id"
        assert cityobject.type == "Building"
    
    def test_one_attribute_is_initialised_properly(self):
        """Is a simple city object working with attributes?"""

        cityobject = CityObject("one_id", "Building", {"one_attribute": "one_value"})

        assert cityobject.attributes["one_attribute"] == "one_value"
    
    def test_create_with_geometry(self):
        """Is a city object with geometry created properly?"""

        geometry = GeometryObject(1, MultiSurface([
            [
                ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))
            ]
        ]))

        cityobject = CityObject("one_id", "Building", geometry=geometry)

        assert isinstance(cityobject, CityObject)
        assert len(cityobject.geometry) == 1
        assert isinstance(cityobject.geometry[0], GeometryObject)
        assert isinstance(cityobject.geometry[0].boundaries, MultiSurface)
    
    def test_representation_without_attributes_and_geometry(self):
        """Is a building without geometry returning the expected representation?"""

        building = CityObject("one_id", "Building")

        assert building.__repr__() == repr({"cityobject_id": "one_id", "type": "Building"})
    
    def test_representation_without_geometry(self):
        """Is a building without geometry returning the expected representation?"""

        building = CityObject("one_id", "Building", {"date": "2000-01-01"})

        assert building.__repr__() == repr({"cityobject_id": "one_id", "type": "Building", "attributes": {"date": "2000-01-01"}})
    
    def test_create_cityobject_with_parent(self):
        """Is a city object with a parent initialised properly?"""

        child = CityObject("child_building", "Building")
        building = CityObject("parent_building", "Building", children=[child])

        assert isinstance(child, CityObject)
        assert len(building.children) == 1
        for c in building.children:
            assert isinstance(c, CityObject)

class TestBuilding:

    def test_building_has_type_of_building(self):
        """Tests is building?"""

        building = Building("one_id")

        assert building.type == "Building"
