"""Module to manipulate history graphs for cjv."""

import networkx as nx
from versioning import VersionedCityJSON

class History:
    """Class to represent the history of versions
    of a versioned city model
    """

    def __init__(self, citymodel: VersionedCityJSON):
        self._citymodel = citymodel
        self._dag = nx.DiGraph()

    def add_versions(self, version_name):
        """Adds the versions that lead to version_name."""
        G = self._dag

        next_key = version_name
        next_ver = self._citymodel.versioning.versions[version_name]
        G.add_node(next_key)
        for parent in next_ver.parents:
            if not G.has_node(parent):
                self.add_versions(parent.name)
            G.add_edge(parent.name, next_key)

    def get_dag(self):
        """Returns the dag object."""
        return self._dag
