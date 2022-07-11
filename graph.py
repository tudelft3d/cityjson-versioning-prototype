"""Module to manipulate history graphs for cjv."""

from textwrap import fill, wrap, indent

import networkx as nx
from colorama import Fore, Style
from rich.console import Console
from rich.themes import Theme
from rich.padding import Padding

from cityjson.versioning import VersionedCityJSON

class History:
    """Class to represent the history of versions of a versioned city model."""

    def __init__(self, citymodel: VersionedCityJSON):
        self._citymodel = citymodel
        self._dag = nx.DiGraph()

    def add_versions(self, version_name):
        """Adds the versions that lead to version_name."""
        G = self._dag

        next_key = version_name
        next_ver = self._citymodel.versioning.versions[version_name]
        G.add_node(next_key, **next_ver.data)
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

class AbstractLog:
    """Abstract class that shares logic related to formatting of logs"""

    def __init__(self, history: 'History'):
        self._history = history

        self._theme = Theme({
            "header": "yellow",
            "branch": "cyan",
            "tag": "magenta",
            "message": "white",
            "main": "white"
        })
    
    def get_header_text(self, version):
        """Returns the header line of a version, formatted."""
        header_line = f"[header]version {version.name}"

        if len(version.branches) > 0:
            branches_txt = self.get_refs_string(version.branches, "branch")
            header_line += f" ({branches_txt})"

        if len(version.tags) > 0:
            tags_txt = self.get_refs_string(version.tags, "tag")
            header_line += f" ({tags_txt})"

        header_line += "[/header]"

        return header_line
    
    def get_refs_string(self, refs, ref_type):
        """Returns a string with comma-seperated names of the refs."""
        return ", ".join([f"[{ref_type}]{ref}[/{ref_type}]"
                          for ref in refs])

class SimpleHistoryLog(AbstractLog):
    """Class to print a simple list log of a History."""

    def print_all(self):
        """Prints the history as a list."""
        dag = self._history.dag
        sorted_keys = list(nx.topological_sort(dag))
        sorted_keys.reverse()

        for version_name in sorted_keys:
            version = self._history.citymodel.versioning.versions[version_name]
            self.print_version(version)

    def print_version(self, version: 'Version', console=None):
        """Prints a given version."""
        def text_wrap(text, width):
            return '\n'.join(wrap(text, width))

        console = Console(theme=self._theme, highlight=False)

        header_line = self.get_header_text(version)

        console.print(Padding(header_line, (0, 0)))

        console.print(f"{'Author:':<7} {version.author}")
        console.print(f"{'Date:':<7} {version.date}")

        msg = f"[message]{text_wrap(version.message, 70)}[/message]"

        console.print(Padding(msg, (1, 4)))

    
class GraphHistoryLog(AbstractLog):
    """Class to print a history with a graph."""

    def print_all(self):
        """Prints the history as a graph."""
        def get_branch_lines(num_lines, num_empty_lines):
            """
            Returns the lines for the given branches
            """
            txt = num_lines * "| " + num_empty_lines * "  "

            return txt

        console = Console(theme = self._theme, highlight=False)

        cm = self._history.citymodel

        dag = self._history.dag
        sorted_keys = list(nx.topological_sort(dag))
        sorted_keys.reverse()

        # Get the leafs of the graph
        leafs = [x for x in dag.nodes() if dag.out_degree(x) == 0]

        all_paths = []
        for leaf in leafs:
            version = cm.versioning.versions[leaf]
            all_paths.extend(list(nx.shortest_simple_paths(dag,
                                                           sorted_keys[-1],
                                                           version.name)))

        active_paths = [all_paths[0]]
        for version_name in sorted_keys:
            version = self._history.citymodel.versioning.versions[version_name]
            found = False
            header_line = ""

            is_merge = dag.in_degree(version_name) > 1
            is_fork = dag.out_degree(version_name) > 1

            if is_merge:
                for path in all_paths:
                    if version_name in path and path not in active_paths:
                        active_paths.append(path)

            width = len(active_paths)
            empty_lines = 0

            # Find to which branch this version belongs
            for path in active_paths:
                # TODO: This set of conditional branches is awful!
                if version_name in path:
                    if found:
                        if not is_fork:
                            header_line += "  "
                            continue
                    else:
                        header_line += "* "
                        found = True
                        continue

                header_line += "| "

            header_line += self.get_header_text(version)

            console.print(header_line)

            if is_merge:
                console.print("|\\")
            if is_fork:
                console.print("|/")
                width -= 1
                empty_lines += 1
            if not (is_merge or is_fork):
                console.print("".join(["| " for _ in active_paths]))

            lines = get_branch_lines(width, empty_lines)
            console.print(indent(f"{'Author:':<7} {version.author}", lines))
            console.print(indent(f"{'Date:':<7} {version.date}", lines))
            console.print(lines)
            msg = indent(fill(version.message, 70, initial_indent="[message]    ", subsequent_indent="[message]    "), lines)
            console.print(msg)
            console.print(lines)
