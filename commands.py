"""Module with the commands that are run through the cjv cli."""

import datetime
import json

import networkx as nx
# Code to have colors at the console output
from colorama import Fore, Style, init

import utils
from graph import GraphHistoryLog, History, SimpleHistoryLog
from cityjson.versioning import VersionedCityJSON, SimpleVersionDiff, VersionedCityObject
import cityjson.versioning as cjv
import cityjson.citymodel as cjm

from deepdiff import DeepDiff, Delta

init()

class LogCommand:
    """Class that implements the log command."""

    def __init__(self, citymodel: 'VersionedCityJSON', refs, graph=False):
        self._citymodel = citymodel
        self._refs = refs
        self._graph = graph

    def set_refs(self, refs):
        """Set the refs to be used as end-points of the output graph."""
        self._refs = refs

    def execute(self):
        """Executes the log command, printing the graph of history."""

        version_count = len(self._citymodel.versioning.versions)
        if version_count > 0:
            print("Found {}{}{} versions.\n".format(Fore.GREEN,
                                                    version_count,
                                                    Style.RESET_ALL))
        else:
            print("No versions found. Doei!")
            return

        history = History(self._citymodel)
        for ref in self._refs:
            history.add_versions(self._citymodel.versioning.resolve_ref(ref))

        if self._graph:
            logger = GraphHistoryLog(history)
        else:
            logger = SimpleHistoryLog(history)

        logger.print_all()

class CheckoutCommand:
    """Class that implements the checkout command."""

    def __init__(self, citymodel: 'VersionedCityJSON', version_name, output_file):
        self._citymodel = citymodel
        self._version = version_name
        self._output = output_file
        self._objectid_property = "cityobject_id"

    def set_objectid_property(self, property_name):
        """Updates the property that represents the original object's name."""
        self._objectid_property = property_name

    def execute(self):
        """Executes the checkout command."""
        cm = self._citymodel
        ref = self._version
        output_file = self._output

        try:
            version = cm.versioning.get_version(ref)
        except KeyError:
            print("Oh no! '{}' does not exist...".format(version.name))
            quit()

        new_model = cjm.min_cityjson.copy()
        print("Extracting version '%s'..." % version.name)
        new_objects = version.versioned_objects

        new_model["CityObjects"] = {obj.original_cityobject.name:
                                    obj.original_cityobject.data
                                    for obj in new_objects}
        new_model["vertices"] = cm.data["vertices"]

        print("Saving {0}...".format(output_file))
        utils.save_cityjson(new_model, output_file)
        print("Done!")

class DiffCommand:
    """Class that implements the diff command."""

    def __init__(self, citymodel: 'VersionedCityJSON', new_version, old_version):
        self._citymodel = citymodel
        self._new_version = new_version
        self._old_version = old_version

    def execute(self):
        """Executes the diff command."""
        cm = self._citymodel

        new_version = cm.versioning.get_version(self._new_version)
        old_version = cm.versioning.get_version(self._old_version)

        diff = SimpleVersionDiff(old_version, new_version)
        result = diff.compute()

        print("This is the diff between {commit_color}{new_version}"
              "{reset_style} and {commit_color}{old_version}{reset_style}"
              .format(new_version=new_version.name,
                      old_version=old_version.name,
                      commit_color=Fore.YELLOW,
                      reset_style=Style.RESET_ALL))

        result.print()

class RehashCommand:
    """Class that implements the rehash command."""

    def __init__(self, citymodel: 'VersionedCityJSON', output_file):
        self._citymodel = citymodel
        self._output = output_file

    def execute(self):
        """Executes the rehash command."""
        cm = self._citymodel

        # To keep the mapping between old and new keys
        keypairs = {}
        ver_keypairs = {}

        print ("City Objects:")

        # Re-hash the city objects
        new_cityobjects = {}
        for obj_key, obj in cm.cityobjects.items():
            #TODO Later we'll have to do that first for the second-layer objects
            # and then for first ones
            new_key = utils.get_hash_of_object(obj)
            print("{newkey} <- {oldkey}".format(newkey=new_key, oldkey=obj_key))
            keypairs[obj_key] = new_key

            new_cityobjects[new_key] = cm.cityobjects[obj_key]

        print("Versions:")

        history = History(cm)
        for branch, version in cm.versioning.branches.items():
            history.add_versions(version.name)

        dag = history.dag

        new_versions = {}
        sorted_keys = list(nx.topological_sort(dag))
        for ver_key in sorted_keys:
            version = cm.versioning.versions[ver_key]
            new_objects = []
            for obj_key in version.versioned_objects:
                new_objects.append(keypairs[obj_key])
            version.data["objects"] = new_objects

            if version.has_parents:
                new_parents = []
                for parent in version.parents:
                    new_parents.append(ver_keypairs[parent.name])
                version.data["parents"] = new_parents

            new_key = utils.get_hash_of_object(version.data)
            print("{newkey} <- {oldkey}".format(newkey=new_key, oldkey=ver_key))

            new_versions[new_key] = version.data
            ver_keypairs[ver_key] = new_key

        new_branches = {}
        for branch, version in cm.versioning.branches.items():
            new_branches[branch] = ver_keypairs[version.name]

        new_tags = {}
        for tag, version in cm.versioning.tags.items():
            new_tags[tag] = ver_keypairs[version.name]

        cm.cityobjects = new_cityobjects
        cm.data["versioning"]["versions"] = new_versions
        cm.data["versioning"]["branches"] = new_branches
        cm.data["versioning"]["tags"] = new_tags

        print("Saving as {0}...".format(self._output))
        with open(self._output, "w") as outfile:
            json.dump(cm.data, outfile)

class CommitCommand:
    """Class that implements the commit command."""

    def __init__(self, vcitymodel: 'VersionedCityJSON', new_citymodel, ref, author, message):
        self._vcitymodel = vcitymodel
        self._new_citymodel = new_citymodel
        self._ref = ref
        self._author = author
        self._message = message

    def execute(self):
        """Executes the commit command"""
        vcm = self._vcitymodel
        new_citymodel = self._new_citymodel

        parent_versionid = None
        if len(vcm.versioning.versions) > 0:
            parent_versionid = vcm.versioning.resolve_ref(self._ref)

        print("Appending vertices...")
        offset = len(vcm.data["vertices"])
        vcm.data["vertices"] += new_citymodel["vertices"]
        for _, obj in new_citymodel["CityObjects"].items():
            for g in obj['geometry']:
                utils.update_geom_indices_by_offset(g["boundaries"], offset)

        print("Removing duplicate vertices...")
        newids, _ = utils.remove_duplicate_vertices(vcm, 3)

        for obj_id, obj in new_citymodel["CityObjects"].items():
            for g in obj['geometry']:
                utils.update_geom_indices_by_map(g["boundaries"], newids)

        new_version = cjv.Version(vcm.versioning)
        new_version.author = self._author
        new_version.date = datetime.datetime.now()
        new_version.message = self._message

        for obj_id, obj in new_citymodel.cityobjects.items():
            new_object = cjv.VersionedCityObject(cjm.CityObject(obj, obj_id))
            new_version.add_cityobject(new_object)

        if parent_versionid is not None:
            parent_version = vcm.versioning.get_version(parent_versionid)
            diff = cjv.SimpleVersionDiff(parent_version, new_version)
            result = diff.compute()
            if (len(result.added) == 0 and
                    len(result.removed) == 0 and
                    len(result.changed) == 0):
                print("Nothing changed! Skipping this...")
                return

            result.print()
            new_version.add_parent(parent_version)
        new_version.name = new_version.hash()
        vcm.versioning.add_version(new_version)

        if (vcm.versioning.is_branch(self._ref) or
                len(vcm.versioning.versions) == 1):
            print("Updating {branch} to {id}".format(branch=self._ref,
                                                     id=new_version.name))
            vcm.versioning.set_branch(self._ref, new_version)

class BranchCommand:
    """Class that creates a branch at a given ref"""

    def __init__(self, citymodel: 'VersionedCityJSON', ref, branch_name, output_file):
        self._citymodel = citymodel
        self._ref = ref
        self._branch_name = branch_name
        self._output_file = output_file

    def set_ref(self, ref):
        """Set the ref to be used as point for the new branch."""
        self._ref = ref

    def execute(self):
        """Executes the branch command."""
        vcm = self._citymodel

        version = utils.find_version_from_ref(self._ref, vcm["versioning"])

        if utils.is_ref_branch(self._branch_name, vcm["versioning"]):
            print("Branch '{branch}' already exists! "
                  "Nothing to do.".format(branch=self._branch_name))
            return

        print("Creating '{branch}' at"
              " {version}...".format(branch=self._branch_name, version=version))

        vcm["versioning"]["branches"][self._branch_name] = version

        print("Saving file at {filename}...".format(filename=self._output_file))

        vcm.save(self._output_file)

        print("Done! Tot ziens.")

class BranchDeleteCommand:
    """Class that deletes a branch"""

    def __init__(self, citymodel: 'VersionedCityJSON', branch_name, output_file):
        self._citymodel = citymodel
        self._branch_name = branch_name
        self._output_file = output_file

    def execute(self):
        """Executes the delete branch command."""
        vcm = self._citymodel

        if not utils.is_ref_branch(self._branch_name, vcm["versioning"]):
            print("Branch '{branch}' does not exist! "
                  "Nothing to do.".format(branch=self._branch_name))
            return

        del vcm["versioning"]["branches"][self._branch_name]

        print("Saving file at {filename}...".format(filename=self._output_file))

        vcm.save(self._output_file)

        print("Done! Tot ziens.")

class MergeBranchesCommand:
    """Class that merges two branches"""

    def __init__(self, citymodel: 'VersionedCityJSON', source_branch, dest_branch, author, output):
        self._citymodel = citymodel
        self._source_branch = source_branch
        self._dest_branch = dest_branch
        self._author = author
        self._output_file = output

    @staticmethod
    def is_conflict(diff1: DeepDiff, diff2: DeepDiff) -> bool:
        """Returns true if the two diffs are actually conflicting"""
        paths1 = set([path for cat in diff1.to_dict() for path in diff1[cat]])
        paths2 = set([path for cat in diff2.to_dict() for path in diff2[cat]])

        return len(paths1.intersection(paths2)) > 0

    def execute(self):
        """Executers the merge command."""
        vcm = self._citymodel
        source_branch = self._source_branch
        dest_branch = self._dest_branch

        source_version = vcm.versioning.get_version(source_branch)
        dest_version = vcm.versioning.get_version(dest_branch)

        if source_version.name == dest_version.name:
            print("This is the same version. Nothing to do here...")
            return

        # Build a DAG that contains the two given refs
        history = History(vcm)
        history.add_versions(source_version.name)
        history.add_versions(dest_version.name)

        dag = history.dag

        if dest_version.name in nx.ancestors(dag, source_version.name):
            print("{dest_ref} is earlier than {source_ref}! "
                  "Can't do this.".format(dest_ref=dest_branch,
                                          source_ref=source_branch))
            return

        common_ancestor = nx.lowest_common_ancestor(dag,
                                                    source_version.name,
                                                    dest_version.name)

        print("Common ancestor: {}".format(common_ancestor))

        ancestor_version = vcm.versioning.get_version(common_ancestor)

        diff = SimpleVersionDiff(ancestor_version, source_version)
        source_changes = diff.compute()

        diff = SimpleVersionDiff(ancestor_version, dest_version)
        dest_changes = diff.compute()

        source_ids_changed = (set(k for k in source_changes.changed)
                              .union(set(k for k in source_changes.added))
                              .union(set(k for k in source_changes.removed)))
        dest_ids_changed = (set(k for k in dest_changes.changed)
                            .union(set(k for k in dest_changes.added))
                            .union(set(k for k in dest_changes.removed)))

        # Compute candidate conflicts
        conflicts = source_ids_changed.intersection(dest_ids_changed)

        # Remove changes that aren't conflicts
        both_changed = (set(k for k in source_changes.changed)
                        .intersection(set(k for k in dest_changes.changed)))

        resolved = {}
        for co_id in both_changed:
            common_obj = source_changes.changed[co_id]["source"].data
            left_dest = source_changes.changed[co_id]["dest"].data
            right_dest = dest_changes.changed[co_id]["dest"].data

            left_diff = DeepDiff(common_obj, left_dest)
            right_diff = DeepDiff(common_obj, right_dest)

            if not self.is_conflict(left_diff, right_diff):
                # print(f"Conflicts on {co_id} can be resolved...")
                conflicts.remove(co_id)

                delta = Delta(left_diff)
                new_obj = common_obj + delta

                delta = Delta(right_diff)
                new_obj = new_obj + delta

                new_versioned_obj = VersionedCityObject(cjm.CityObject(new_obj, name=co_id))
                resolved[co_id] = new_versioned_obj

        if len(conflicts) > 0:
            print("There are conflicts!")

            for c in conflicts:
                print(f"- {c}")
            print("Forgive me for not being able to resolve them right now...")
            return

        new_version = cjv.Version(vcm.versioning, {
            "author": self._author,
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "message": "Merge {} to {}".format(source_branch, dest_branch),
            "parents": [source_version.name, dest_version.name],
            "objects": {}
        })

        objects = (set(k for k in source_version.versioned_objects)
                   .intersection(set(k for k in dest_version.versioned_objects)))

        for obj in objects:
            new_version.add_cityobject(obj)

        for co_id, obj in source_changes.changed.items():
            if not co_id in resolved:
                new_version.add_cityobject(obj["dest"])
        for co_id, obj in dest_changes.changed.items():
            if not co_id in resolved:
                new_version.add_cityobject(obj["dest"])
        for obj in source_changes.added.values():
            new_version.add_cityobject(obj)
        for obj in dest_changes.added.values():
            new_version.add_cityobject(obj)
        
        for obj in resolved.values():
            new_version.add_cityobject(obj)

        new_version.name = new_version.hash()
        vcm.versioning.add_version(new_version)

        if vcm.versioning.is_branch(dest_branch):
            print("Moving {} to {}".format(dest_branch, new_version.name))
            vcm.versioning.set_branch(dest_branch, new_version)

        print("Saving to {0}...".format(self._output_file))
        vcm.save(self._output_file)
