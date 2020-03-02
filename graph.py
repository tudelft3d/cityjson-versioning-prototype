"""Module to manipulate history graphs for cjv."""

import networkx as nx
from colorama import Fore, Style
from versioning import VersionedCityJSON, Version

class History:
    """Class to represent the history of versions of a versioned city model"""

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

    @property
    def citymodel(self):
        """Returns the versioned city model."""
        return self._citymodel

    @property
    def dag(self):
        """Returns the dag object."""
        return self._dag

class SimpleHistoryLog:
    """Class to print a simple list log of a History."""

    def __init__(self, history: 'History'):
        self._history = history

        self._colors = {
            "header": Fore.YELLOW,
            "branch": Fore.CYAN,
            "tag": Fore.MAGENTA,
            "message": Fore.CYAN,
            "main": Fore.WHITE
        }

    def print_all(self):
        """Returns the output of the history."""
        dag = self._history.dag
        sorted_keys = list(nx.topological_sort(dag))
        sorted_keys.reverse()

        for version_name in sorted_keys:
            version = self._history.citymodel.versioning.versions[version_name]
            self.print_version(version)

    def print_version(self, version: 'Version'):
        """Prints a given version."""
        colors = self._colors

        print(colors["header"], end='')
        print("* version {name}".format(name=version.name), end='')

        if len(version.branches) > 0:
            branches_txt = self.get_refs_string(version.branches,
                                                colors["branch"],
                                                colors["header"])
            print(' ({branches})'.format(branches=branches_txt), end='')

        if len(version.tags) > 0:
            tags_txt = self.get_refs_string(version.tags,
                                            colors["tag"],
                                            colors["header"])
            print(' ({tags})'.format(tags=tags_txt), end='')

        print(colors["main"])

        print("  Author: {author}".format(author=version.author))
        print("  Date: {date}".format(date=version.date))

        msg = "  Message:\n\n{}\t{}{}".format(Fore.CYAN,
                                              '\t'.join(version.message.splitlines(True)),
                                              Style.RESET_ALL)
        print(msg, end='\n\n')

    def get_refs_string(self, refs, ref_color, reset_color):
        """Returns a string with comma-seperated names of the refs."""
        return ", ".join(["{}{}{}".format(ref_color,
                                          ref,
                                          reset_color)
                          for ref in refs])
