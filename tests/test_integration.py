"""A series of integration tests to check the validity of the API against real data"""

import pytest
from citymodel.model import CityModel, CityObject, Building
from citymodel.geometry import MultiSurface

import json

class TestRegularFile:
    """A class to test the loading of a regular file"""

    def test_open_file(self):
        file_data = open("..\\Examples\\buildingBeforeAndAfter.json")
        citymodel = json.load(file_data)