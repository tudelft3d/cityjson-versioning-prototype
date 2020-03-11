"""Module with tests for the commands."""

import commands
import cityjson.citymodel as cjm
import cityjson.versioning as cjv

class TestCommitCommand:
    """Group of tests of the commit command."""

    def test_create_new_vcj(self):
        """Tests if a version is created properly in a new versioned CityJSON.
        """
        vcm = cjv.VersionedCityJSON()

        cm = cjm.CityJSON()

        command = commands.CommitCommand(vcm,
                                         cm,
                                         "master",
                                         "John Doe",
                                         "Test Message")

        command.execute()

        assert len(vcm.versioning.versions) == 1

        version = list(vcm.versioning.versions.values())[0]
        assert version.author == "John Doe"
        assert version.message == "Test Message"
        assert len(version.versioned_objects) == 0
