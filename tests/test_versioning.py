import pytest
import versioning as v
from utils import get_hash_of_object

class TestVersion:
    """Tests the Version class."""

    def test_hash(self):
        """Is hash of object correct?"""

        cm = v.VersionedCityJSON()
        versioning = v.Versioning(cm)

        version = v.Version(versioning)
        expected_hash = get_hash_of_object(version.data)
        assert version.hash() == expected_hash
