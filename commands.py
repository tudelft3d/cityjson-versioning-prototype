import json
from utils import *
import networkx as nx
import datetime

# Code to have colors at the console output
from colorama import init, Fore, Back, Style
init()

minimal_json = {
  "type": "CityJSON",
  "version": "1.0",
  "extensions": {},
  "metadata": {},
  "CityObjects": {}
}

class LogCommand:
    def __init__(self, citymodel, refs=["master"]):
        self._citymodel = citymodel
        self._refs = refs
    
    def set_ref(self, ref):
        self._refs = refs

    def execute(self):
        cm = self._citymodel
        refs = self._refs

        # Isolate the versioning property
        versioning = cm["versioning"]
        
        # The number of versions
        version_count = len(versioning["versions"])

        # Check if versions are present in the file
        if version_count > 0:
            print("Found %s%d%s versions.\n" % (Fore.GREEN, len(versioning["versions"]), Style.RESET_ALL))
        else:
            print("No versions found. Doei!")
            return
        
        dag = nx.DiGraph()
        for ref in refs:
            ref_version = find_version_from_ref(ref, versioning)
            dag = build_dag_from_version(dag, versioning["versions"], ref_version)

        sorted_keys = list(nx.topological_sort(dag))
        sorted_keys.reverse()

        found_branches = []
        for ref in refs:
            ref_version = find_version_from_ref(ref, versioning)
            found_branches.extend(list(nx.shortest_simple_paths(dag, sorted_keys[-1], ref_version)))
        for version_name in sorted_keys:
            tabs = min([i for i, b in enumerate(found_branches) if version_name in b])

            current_version = versioning["versions"][version_name]

            branches = []
            for branch_name, branch_ref in versioning["branches"].items():
                if branch_ref == version_name:
                    branches.append(branch_name)
            
            tags = []
            for tag_name, tag_ref in versioning["tags"].items():
                if tag_ref == version_name:
                    tags.append(tag_name)

            print_version(version_name, current_version, branches, tags, tabs)

class CheckoutCommand:
    def __init__(self, citymodel, version_name, output_file, **args):
        self._citymodel = citymodel
        self._version = version_name
        self._output = output_file
        self._objectid_property = "cityobject_id"
    
    def set_objectid_property(self, property_name):
        self._objectid_property = property_name

    def execute(self):
        # TODO Also add the vertices
        cm = self._citymodel
        ref = self._version
        output_file = self._output

        versioning = cm["versioning"]
        try:
            version_name = find_version_from_ref(ref, versioning)
        except:
            print("There is no ref '%s' in the provided versioned CityJSON" % version_name)
            quit()
        
        new_model = minimal_json
        print("Extracting version '%s'..." % version_name)
        new_objects = get_versioned_city_objects(cm, version_name)
        new_objects = convert_to_regular_city_objects(new_objects, self._objectid_property)
        new_model["CityObjects"] = new_objects
        new_model["vertices"] = cm["vertices"]

        print("Saving {0}...".format(output_file))
        save_cityjson(new_model, output_file)
        print("Done!")

class DiffCommand:
    def __init__(self, citymodel, new_version, old_version, **args):
        self._citymodel = citymodel
        self._new_version = new_version
        self._old_version = old_version

    def execute(self):
        cm = self._citymodel
        new_version = self._new_version
        old_version = self._old_version

        new_version = find_version_from_ref(new_version, cm["versioning"])
        old_version = find_version_from_ref(old_version, cm["versioning"])

        new_objs = get_versioned_city_objects(cm, new_version)
        old_objs = get_versioned_city_objects(cm, old_version)

        print("This is the diff between {commit_color}{new_version}{reset_style} and {commit_color}{old_version}{reset_style}".format(new_version=new_version, old_version=old_version, commit_color=Fore.YELLOW, reset_style=Style.RESET_ALL))

        print_diff_of_versioned_objects(new_objs, old_objs)

class RehashCommand:
    def __init__(self, citymodel, output_file, **args):
        self._citymodel = citymodel
        self._output = output_file
    
    def execute(self):
        cm = self._citymodel

        # To keep the mapping between old and new keys
        keypairs = {}
        ver_keypairs = {}
        
        print ("City Objects:")

        # Re-hash the city objects
        new_cityobjects = {}
        for obj_key, obj in cm["CityObjects"].items():
            #TODO Later we'll have to do that first for the second-layer objects and then for first ones
            new_key = get_hash_of_object(obj)
            print("{newkey} <- {oldkey}".format(newkey=new_key, oldkey=obj_key))
            keypairs[obj_key] = new_key

            new_cityobjects[new_key] = cm["CityObjects"][obj_key]
        
        print("Versions:")

        # Build the DAG
        dag = nx.DiGraph()
        for branch, version in cm["versioning"]["branches"].items():
            dag = build_dag_from_version(dag, cm["versioning"]["versions"], version)

        new_versions = {}
        sorted_keys = list(nx.topological_sort(dag))
        for ver_key in sorted_keys:
            version = cm["versioning"]["versions"][ver_key]
            new_objects = []
            for obj_key in version["objects"]:
                new_objects.append(keypairs[obj_key])
            version["objects"] = new_objects

            if "parents" in version:
                new_parents = []
                for parent_key in version["parents"]:
                    new_parents.append(ver_keypairs[parent_key])
                version["parents"] = new_parents
            
            new_key = get_hash_of_object(version)
            print("{newkey} <- {oldkey}".format(newkey=new_key, oldkey=ver_key))

            new_versions[new_key] = version
            ver_keypairs[ver_key] = new_key
        
        new_branches = {}
        for branch, version in cm["versioning"]["branches"].items():
            new_branches[branch] = ver_keypairs[version]
        
        new_tags = {}
        for tag, version in cm["versioning"]["tags"].items():
            new_tags[tag] = ver_keypairs[version]
        
        cm["CityObjects"] = new_cityobjects
        cm["versioning"]["versions"] = new_versions
        cm["versioning"]["branches"] = new_branches
        cm["versioning"]["tags"] = new_tags

        print("Saving as {0}...".format(self._output))
        with open(self._output, "w") as outfile:
            json.dump(cm, outfile)

class CommitCommand:
    def __init__(self, vcitymodel, in_file, ref, author, message, output_file, **args):
        self._vcitymodel = vcitymodel
        self._input_file = in_file
        self._ref = ref
        self._author = author
        self._message = message
        self._output_file = output_file
    
    def execute(self):
        # TODO Also update the vertices
        vcm = self._vcitymodel
        in_file = self._input_file

        parents = []
        parent_versionid = None
        if len(vcm["versioning"]["versions"]) > 0:
            parent_versionid = find_version_from_ref(self._ref, vcm["versioning"])
            parents = [parent_versionid]

        new_citymodel = load_cityjson(in_file)

        print("Appending vertices...")
        offset = len(vcm["vertices"])
        vcm["vertices"] += new_citymodel["vertices"]
        for obj_id, obj in new_citymodel["CityObjects"].items():
            for g in obj['geometry']:
                update_geom_indices_by_offset(g["boundaries"], offset)

        print("Removing duplicate vertices...")
        newids, new_ver_count = remove_duplicate_vertices(vcm, 3)

        for obj_id, obj in new_citymodel["CityObjects"].items():
                for g in obj['geometry']:
                    update_geom_indices_by_map(g["boundaries"], newids)

        new_objects = convert_to_versioned_city_objects(new_citymodel["CityObjects"])

        if parent_versionid is not None:
            old_objects = get_versioned_city_objects(vcm, parent_versionid)

            common_objects = set(new_objects).intersection(old_objects)
            if len(common_objects) == len(new_objects) and len(common_objects) == len(old_objects):
                print("Nothing changed! Skipping this...")
                return
            
            print_diff_of_versioned_objects(new_objects, old_objects)

        new_version = {
            "author": self._author,
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "message": self._message,
            "parents": parents,
            "objects": []
        }

        for new_id, new_obj in new_objects.items():
            vcm["CityObjects"][new_id] = new_obj
            new_version["objects"].append(new_id)
        
        new_versionid = get_hash_of_object(new_version)

        vcm["versioning"]["versions"][new_versionid] = new_version
        
        if is_ref_branch(self._ref, vcm["versioning"]) or len(vcm["versioning"]["versions"]) == 1:
            print("Updating {branch} to {commit}".format(branch=self._ref, commit=new_versionid))
            vcm["versioning"]["branches"][self._ref] = new_versionid
        
        print("Saving to {0}...".format(self._output_file))
        save_cityjson(vcm, self._output_file)

class BranchCommand:
    """Class that creates a branch at a given ref"""

    def __init__(self, citymodel, ref, branch_name, output_file):
        self._citymodel = citymodel
        self._ref = ref
        self._branch_name = branch_name
        self._output_file = output_file
    
    def set_ref(self, ref):
        self._ref = ref

    def execute(self):
        vcm = self._citymodel

        version = find_version_from_ref(self._ref, vcm["versioning"])

        if is_ref_branch(self._branch_name, vcm["versioning"]):
            print("Branch '{branch}' already exists! Nothing to do.".format(branch=self._branch_name))
            return

        print("Creating '{branch}' at {version}...".format(branch=self._branch_name, version=version))

        vcm["versioning"]["branches"][self._branch_name] = version

        print("Saving file at {filename}...".format(filename=self._output_file))

        save_cityjson(vcm, self._output_file)

        print("Done! Tot ziens.")

class BranchDeleteCommand:
    """Class that deletes a branch"""

    def __init__(self, citymodel, branch_name, output_file):
        self._citymodel = citymodel
        self._branch_name = branch_name
        self._output_file = output_file

    def execute(self):
        vcm = self._citymodel

        if not is_ref_branch(self._branch_name, vcm["versioning"]):
            print("Branch '{branch}' does not exist! Nothing to do.".format(branch=self._branch_name))
            return

        del vcm["versioning"]["branches"][self._branch_name]

        print("Saving file at {filename}...".format(filename=self._output_file))

        save_cityjson(vcm, self._output_file)

        print("Done! Tot ziens.")

class MergeBranchesCommand:
    """Class that merges two branches"""

    def __init__(self, citymodel, source_branch, dest_branch, author, output):
        self._citymodel = citymodel
        self._source_branch = source_branch
        self._dest_branch = dest_branch
        self._author = author
        self._output_file = output
    
    def execute(self):
        vcm = self._citymodel
        source_branch = self._source_branch
        dest_branch = self._dest_branch

        versioning = vcm["versioning"]

        # if not is_ref_branch(source_branch, versioning):
        #     print("Source branch '{branch}' does not exist! Nothing to do.".format(branch=self._source_branch))
        #     return

        # if not is_ref_branch(dest_branch, versioning):
        #     print("Destination branch '{branch}' does not exist! Nothing to do.".format(branch=self._dest_branch))
        #     return
        
        source_version = find_version_from_ref(source_branch, versioning)
        dest_version = find_version_from_ref(dest_branch, versioning)

        dag = nx.DiGraph()
        dag = build_dag_from_version(dag, versioning["versions"], source_version)
        dag = build_dag_from_version(dag, versioning["versions"], dest_version)

        if (dest_version in nx.ancestors(dag, source_version)):
            print("{dest_ref} is earlier than {source_ref}! Can't do this.".format(dest_ref=dest_branch, source_ref=source_branch))
            return

        common_ancestor = nx.lowest_common_ancestor(dag, source_version, dest_version)

        print("Common ancestor: {}".format(common_ancestor))

        source_objects = get_versioned_city_objects(vcm, source_version)
        dest_objects = get_versioned_city_objects(vcm, dest_version)
        ancestor_objects = get_versioned_city_objects(vcm, common_ancestor)

        source_changes = get_diff_of_versioned_objects(source_objects, ancestor_objects)
        dest_changes = get_diff_of_versioned_objects(dest_objects, ancestor_objects)

        source_ids_changed = set([k for k in source_changes["changed"].keys()]).union(set([k for k in source_changes["added"].keys()])).union(set([k for k in source_changes["removed"].keys()]))
        dest_ids_changed = set([k for k in dest_changes["changed"].keys()]).union(set([k for k in dest_changes["added"].keys()])).union(set([k for k in dest_changes["removed"].keys()]))

        conflicts = source_ids_changed.intersection(dest_ids_changed)
        if len(conflicts) > 0:
            print("There are conflicts!")
            for c in conflicts:
                print("- {}".format(c))
            print("Forgive me for not being able to resolve them right now...")
            return
                
        objects = set([k for k in source_objects.keys()]).intersection([k for k in dest_objects.keys()])
        
        # Given that no conflicts exist I can do the following
        objects = objects.union(set([k["new_id"] for k in source_changes["changed"].values()]))
        objects = objects.union(set([k["new_id"] for k in dest_changes["changed"].values()]))
        objects = objects.union(set([k["new_id"] for k in source_changes["added"].values()]))
        objects = objects.union(set([k["new_id"] for k in dest_changes["added"].values()]))

        objects = list(objects)

        new_version = {
            "author": self._author,
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "message": "Merge {} to {}".format(source_branch, dest_branch),
            "parents": [source_version, dest_version],
            "objects": objects
        }
        
        new_versionid = get_hash_of_object(new_version)

        vcm["versioning"]["versions"][new_versionid] = new_version
        
        if is_ref_branch(dest_branch, vcm["versioning"]):
            vcm["versioning"]["branches"][dest_branch] = new_versionid
        
        print("Saving to {0}...".format(self._output_file))
        save_cityjson(vcm, self._output_file)