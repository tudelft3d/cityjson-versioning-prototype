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
    def __init__(self, citymodel, ref="master"):
        self._citymodel = citymodel
        self._ref = ref
    
    def set_ref(self, ref):
        self._ref = ref

    def execute(self):
        cm = self._citymodel
        ref = self._ref

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
        
        next_versions = []

        # Find the requested ref
        next_versions.append(find_version_from_ref(ref, versioning))

        # Iterate through versions while there are next_versions to check
        while len(next_versions) > 0:
            # Find latest version
            latest_date = versioning["versions"][next_versions[0]]["date"]
            for candidate in next_versions:
                if latest_date <= versioning["versions"][candidate]["date"]:
                    latest_date = versioning["versions"][candidate]["date"]
                    version_name = candidate
            
            current_version = versioning["versions"][version_name]
            next_versions.remove(version_name)

            branches = []
            for branch_name, branch_ref in versioning["branches"].items():
                if branch_ref == version_name:
                    branches.append(branch_name)
            
            tags = []
            for tag_name, tag_ref in versioning["tags"].items():
                if tag_ref == version_name:
                    tags.append(tag_name)

            print_version(version_name, current_version, branches, tags)

            # If there is a previous version, output the differences
            if "parents" in current_version:
                # Find only new versions from parents of the current commit
                new_versions = list(set(current_version["parents"]) - set(next_versions))

                # Add new versions for the future
                next_versions.extend(new_versions)                

class LogCommandBuilder:
    def __init__(self):
        self._instance = None
    
    def __call__(self, vcitymodel, args, **kwargs):
        if len(args) > 3:
            ref = args[3]
        else:
            ref = "master"
        self._instance = LogCommand(vcitymodel, ref)
        return self._instance

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

class CheckoutCommandBuilder:
    def __init__(self):
        self._instance = None
    
    def __call__(self, vcitymodel, args, **kwargs):
        version_name = args[3]
        output_file = args[4]
        self._instance = CheckoutCommand(vcitymodel, version_name, output_file)
        if len(args) > 5:
            if args[5] == "--no-id-property":
                self._instance.set_objectid_property(None)
            else:
                self._instance.set_objectid_property(args[5])
        return self._instance

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

class DiffCommandBuilder:
    def __init__(self):
        self._instance = None
    
    def __call__(self, vcitymodel, args, **kwargs):
        if len(args) < 5:
            print("Not enough arguments: we need two versions for this!")
            raise ValueError("Two arguments needed")

        new_version = args[3]
        old_version = args[4]
        self._instance = DiffCommand(vcitymodel, new_version, old_version)
        return self._instance

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

class RehashCommandBuilder:
    def __init__(self):
        self._instance = None
    
    def __call__(self, vcitymodel, args, **kwargs):
        self._instance = RehashCommand(vcitymodel, args[3])
        return self._instance

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
        newids, new_ver_count = remove_duplicate_vertices(vcm)

        for obj_id, obj in new_citymodel["CityObjects"].items():
                for g in obj['geometry']:
                    update_geom_indices_by_map(g["boundaries"], newids)

        new_objects = convert_to_versioned_city_objects(new_citymodel["CityObjects"])

        if parent_versionid is not None:
            old_objects = get_versioned_city_objects(vcm, parent_versionid)

            if len(set(new_objects).intersection(old_objects)) == len(new_objects):
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

class CommitCommandBuilder:
    def __init__(self):
        self._instance = None
    
    def __call__(self, vcitymodel, args, **kwargs):
        in_file = args[3]
        ref = args[4]
        author = args[5]
        message = args[6]
        if len(args) > 7:
            out_file = args[7]
        else:
            out_file = args[1]
        self._instance = CommitCommand(vcitymodel, in_file, ref, author, message, out_file)
        return self._instance

class CommandFactory:
    """A factory to create commands from their names"""

    def __init__(self):
        self._builders = {}
    
    def register_builder(self, command_name, builder):
        """Registers a new command with the given name"""
        self._builders[command_name] = builder
    
    def create_command(self, command_name, **args):
        """Get the command from a given name"""
        command_builder = self._builders.get(command_name)
        if not command_builder:
            raise ValueError(command_name)
        return command_builder(**args)
    
    def list_commands(self):
        return self._builders.keys()

factory = CommandFactory()
factory.register_builder("log", LogCommandBuilder())
factory.register_builder("checkout", CheckoutCommandBuilder())
factory.register_builder("diff", DiffCommandBuilder())
factory.register_builder("rehash", RehashCommandBuilder())
factory.register_builder("commit", CommitCommandBuilder())