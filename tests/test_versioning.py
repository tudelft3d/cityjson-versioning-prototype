import pytest
import cityjson.versioning as v
import cityjson.citymodel as cm
from utils import get_hash_of_object

class TestVersion:
    """Tests the Version class."""

    def test_hash_calculation(self):
        """Is hash of object correct?"""

        cm = v.VersionedCityJSON()
        versioning = v.Versioning(cm)

        version = v.Version(versioning)
        expected_hash = get_hash_of_object(version.data)
        assert version.hash() == expected_hash

class TestVersionedCityObject:
    """Tests the VersionedCityObject class."""

    def test_initialisation(self):
        """Can we create a verioned city object?"""

        obj = cm.CityObject({"type" : "Building"}, "building1")
        ver_obj = v.VersionedCityObject(obj)

        assert ver_obj.original_cityobject.name == "building1"
        assert ver_obj.name == ver_obj.hash()
        assert ver_obj.name == "d1a15b40c76164b118a73201255fbee8ad48d8ea"
