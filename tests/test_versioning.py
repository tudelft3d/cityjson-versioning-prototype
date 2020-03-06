import pytest
import cityjson.versioning as cjv
import cityjson.citymodel as cjm
from utils import get_hash_of_object

class TestVersion:
    """Tests the Version class."""

    def test_hash_calculation(self):
        """Is hash of object correct?"""

        cm = cjv.VersionedCityJSON()
        versioning = cjv.Versioning(cm)

        version = cjv.Version(versioning)
        expected_hash = get_hash_of_object(version.data)
        assert version.hash() == expected_hash

    def test_create_true_version(self):
        """Is the version created properly when city objects are added?"""

        cm = cjv.VersionedCityJSON()
        versioning = cjv.Versioning(cm)

        version = cjv.Version(versioning)

        obj = cjm.CityObject({"type" : "Building"}, "building1")
        ver_obj = cjv.VersionedCityObject(obj)
        version.add_cityobject(ver_obj)

        assert len(version.data["objects"]) == 1
        assert len(cm.cityobjects) == 1
        assert isinstance(version.versioned_objects, list)

        obtained_vobj = version.versioned_objects[0]
        assert obtained_vobj.name == ver_obj.name
        assert obtained_vobj.original_cityobject.name == "building1"


class TestVersionedCityObject:
    """Tests the VersionedCityObject class."""

    def test_initialisation(self):
        """Can we create a verioned city object?"""

        obj = cjm.CityObject({"type" : "Building"}, "building1")
        ver_obj = cjv.VersionedCityObject(obj)

        assert ver_obj.original_cityobject.name == "building1"
        assert ver_obj.name == ver_obj.hash()
        assert ver_obj.name == "d1a15b40c76164b118a73201255fbee8ad48d8ea"
