import pytest
import cityjson.citymodel as citymodel

class TestCityJSON:
    """Class that tests CityJSON class."""

    def test_load_cityjson(self):
        """Tests if the CityJSON class loads the file correctly."""

        cm = citymodel.CityJSON.from_file("Examples/rotterdam/initial.json")

        assert cm["version"] == "1.0"
        print(cm.cityobjects)
