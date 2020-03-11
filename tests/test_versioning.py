import pytest
import cityjson.versioning as cjv
import cityjson.citymodel as cjm
from utils import get_hash_of_object

class TestVersionedCityJSON:
    """Test the VersionedCityJSON class."""

    def test_create_empty_vcityjson(self):
        """Initialising a VersionedCityJSON without arguments should return
        minimal versioned CityJSON.
        """
        vcm = cjv.VersionedCityJSON()

        assert vcm.data == cjv.empty_vcityjson

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

class TestSimpleVersionDiff:
    """Tests the SimpleVersionDiff class."""

    def test_unchaged(self):
        """Are unchaged objects detected corretcly?"""
        cm = cjv.VersionedCityJSON()
        versioning = cjv.Versioning(cm)

        common_obj = cjm.CityObject({"type" : "Building"}, "building1")
        common_ver_obj = cjv.VersionedCityObject(common_obj)

        source_version = cjv.Version(versioning)
        source_version.add_cityobject(common_ver_obj)

        dest_version = cjv.Version(versioning)
        dest_version.add_cityobject(common_ver_obj)

        diff = cjv.SimpleVersionDiff(source_version, dest_version)
        result = diff.compute()

        assert len(result.changed) == 0
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.unchanged) == 1

    def test_removed(self):
        """Are deleted objects detected correctly?"""

        cm = cjv.VersionedCityJSON()
        versioning = cjv.Versioning(cm)

        obj = cjm.CityObject({"type" : "Building"}, "building1")
        ver_obj = cjv.VersionedCityObject(obj)

        source_version = cjv.Version(versioning)
        source_version.add_cityobject(ver_obj)

        dest_version = cjv.Version(versioning)

        diff = cjv.SimpleVersionDiff(source_version, dest_version)
        result = diff.compute()

        assert len(result.changed) == 0
        assert len(result.added) == 0
        assert len(result.removed) == 1
        assert len(result.unchanged) == 0

    def test_added(self):
        """Are new objects detected correctly?"""

        cm = cjv.VersionedCityJSON()
        versioning = cjv.Versioning(cm)

        obj = cjm.CityObject({"type" : "Building"}, "building1")
        ver_obj = cjv.VersionedCityObject(obj)

        source_version = cjv.Version(versioning)

        dest_version = cjv.Version(versioning)
        dest_version.add_cityobject(ver_obj)

        diff = cjv.SimpleVersionDiff(source_version, dest_version)
        result = diff.compute()

        assert len(result.changed) == 0
        assert len(result.added) == 1
        assert len(result.removed) == 0
        assert len(result.unchanged) == 0

    def test_changed(self):
        """Are deleted objects detected correctly?"""

        cm = cjv.VersionedCityJSON()
        versioning = cjv.Versioning(cm)

        old_obj = cjm.CityObject({"type" : "Building"}, "building1")
        old_ver_obj = cjv.VersionedCityObject(old_obj)

        new_obj = cjm.CityObject({"type" : "BuildingPart"}, "building1")
        new_ver_obj = cjv.VersionedCityObject(new_obj)

        source_version = cjv.Version(versioning)
        source_version.add_cityobject(old_ver_obj)

        dest_version = cjv.Version(versioning)
        dest_version.add_cityobject(new_ver_obj)

        diff = cjv.SimpleVersionDiff(source_version, dest_version)
        result = diff.compute()

        assert len(result.changed) == 1
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.unchanged) == 0

    def test_dummy_data(self):
        """Are changes in the dummy file detected correctly?"""
        cm = (cjv.VersionedCityJSON
              .from_file("Examples/dummy/buildingBeforeAndAfter.json"))
        v30 = cm.versioning.get_version("v30")
        v29 = cm.versioning.get_version("v29")

        diff = cjv.SimpleVersionDiff(v29, v30)
        result = diff.compute()

        assert len(result.changed) == 0
        assert len(result.added) == 0
        assert len(result.removed) == 1
        assert len(result.unchanged) == 0
