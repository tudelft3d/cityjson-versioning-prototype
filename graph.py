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

    def add_versions(self, final_version):
        """Adds the versions that lead to final_version."""
        G = self._dag

        next_key = final_version
        next_ver = self._citymodel.versioning.versions[final_version]
        G.add_node(next_key)
        for parent in next_ver.parents:
            if not G.has_node(parent):
                self.add_versions(parent)
            G.add_edge(parent, next_key)

    def get_dag(self):
        """Returns the dag object."""
        return self._dag
