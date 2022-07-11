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

class SimpleHistoryLog:
    """Class to print a simple list log of a History."""

    def __init__(self, history: 'History'):
        self._history = history

        self._theme = Theme({
            "header": "yellow",
            "branch": "cyan",
            "tag": "magenta",
            "message": "white",
            "main": "white"
        })

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

        header_line = f"[header]version {version.name}"

        if len(version.branches) > 0:
            branches_txt = self.get_refs_string(version.branches, "branch")
            header_line += f" ({branches_txt})"

        if len(version.tags) > 0:
            tags_txt = self.get_refs_string(version.tags, "tag")
            header_line += f" ({tags_txt})"

        header_line += "[/header]"

        console.print(Padding(header_line, (0, 0)))

        console.print(f"{'Author:':<7} {version.author}")
        console.print(f"{'Date:':<7} {version.date}")

        msg = f"[message]{text_wrap(version.message, 70)}[/message]"

        console.print(Padding(msg, (1, 4)))

    def get_refs_string(self, refs, ref_type):
        """Returns a string with comma-seperated names of the refs."""
        return ", ".join([f"[{ref_type}]{ref}[/{ref_type}]"
                          for ref in refs])

class GraphHistoryLog:
    """Class to print a history with a graph."""

    def __init__(self, history: 'History'):
        self._history = history

        self._colors = {
            "header": Fore.YELLOW,
            "branch": Fore.CYAN,
            "tag": Fore.MAGENTA,
            "message": Fore.CYAN,
            "main": Fore.WHITE
        }

        self._theme = Theme({
            "header": "yellow",
            "branch": "cyan",
            "tag": "magenta",
            "message": "white",
            "main": "white"
        })

        self._all_branches = []
        self._active_branch = 0
        self._branches_shown = []
        self._divide = False
        self._merge = False

    def update_status(self, version_name):
        """Updates the status of the graph (calculates if this is a merge,
        divide, which branch is etc.).
        """
        # Find in which branches exists this version name
        in_branches = [i for i, b in enumerate(self._all_branches)
                       if version_name in b]

        self._divide = False
        self._merge = False

        if len(in_branches) == 1:
            # If only one branch is found, then this is nothing special,
            # no divide or merge.
            self._active_branch = in_branches[0]

            if self._all_branches[in_branches[0]] not in self._branches_shown:
                self._branches_shown.append(self._all_branches[in_branches[0]])
        else:
            # If this exists in two branches, it is either a divide or a merge
            # version.
            self._active_branch = min(in_branches)

            # Is this a divide version?
            for b in in_branches:
                # If this is not in the existing shown branches, it's a divide
                # version.
                if self._all_branches[b] not in self._branches_shown:
                    self._branches_shown.append(self._all_branches[b])
                    self._divide = True

            # If this is not a divide version, then it's a merge version.
            if not self._divide:
                self._branches_shown.remove(self._all_branches[in_branches[1]])
                self._merge = True

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

            header_line += f"[header]{version_name}[/header]"

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

            # current_version = cm.versioning.versions[version_name]

            # self.print_version(current_version)

    def print_version(self, version: 'Version'):
        """Prints a given version."""
        colors = self._colors
        lines_txt = self.get_lines_of_branches()

        if self._merge:
            print("|/")

        print(self.get_branch_lines_with_star(self._active_branch), end='')
        print(colors["header"], end='')
        print("  version {name}".format(name=version.name), end='')

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

        if self._divide:
            print("|\\", end='')
        else:
            print(lines_txt, end='')
        print("  Author: {author}".format(author=version.author))
        print(lines_txt, end='')
        print("  Date: {date}".format(date=version.date))

        print(lines_txt, end='')
        msg = ("  Message:\n"
               "{l}\n"
               "{}{l}\t{}{}\n"
               "{l}\n").format(Fore.CYAN,
                               ('\n' + lines_txt + '\t').join(version.message.splitlines(False)),
                               Style.RESET_ALL,
                               l=lines_txt)
        print(msg, end='')

    def get_branch_lines_with_star(self, branch_i):
        """Returns a string with lines according to branches status."""
        if self._divide or self._merge:
            times = len(self._branches_shown) - 1
        else:
            times = len(self._branches_shown)

        result = "".join(['| ' for i in range(branch_i)])
        result += "* "
        result += "".join(['| ' for i in range(branch_i + 1, times)])

        return result

    def get_lines_of_branches(self):
        """Returns the text with lines for the currently shown branchs."""
        return ''.join(['| ' for i in range(len(self._branches_shown))])

    def get_refs_string(self, refs, ref_color, reset_color):
        """Returns a string with comma-seperated names of the refs."""
        return ", ".join(["{}{}{}".format(ref_color,
                                          ref,
                                          reset_color)
                          for ref in refs])
