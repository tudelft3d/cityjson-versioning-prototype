import json

# Code to have colors at the console output
from colorama import init, Fore, Back, Style
init()

minimal_json = "{\
  \"type\": \"CityJSON\",\
  \"version\": \"1.0\",\
  \"extensions\": {},\
  \"metadata\": {},\
  \"transform\": {\
    \"scale\": [],\
    \"translate\": []\
  },\
  \"CityObjects\": {}\
}"

def print_version(version_name, version, branches, tags):
    """Prints a description of a version to the terminal"""
    print(Fore.YELLOW + "version %s" % version_name, end='')
    for branch in branches:
        print(' (' + Fore.CYAN + branch + Fore.YELLOW + ')', end='')
    for tag in tags:
        print(' (' + Fore.MAGENTA + 'tag: %s' % tag + Fore.YELLOW + ')', end='')
    print(Style.RESET_ALL)

    print("Author: %s" % version["author"])
    print("Date: %s" % version["date"])

    print("Message:\n\n" + Fore.CYAN + "%s\n" % version["message"] + Style.RESET_ALL)

def print_diff_of_versions(new_version, old_version):
    """Prints a diff of two versions to the terminal"""
    # Find differences between the two versions
    new_objects = set(new_version["objects"]) - set(old_version["objects"])
    old_objects = set(old_version["objects"]) - set(new_version["objects"])
    same_objects = set(new_version["objects"]).intersection(set(old_version["objects"]))

    for obj in new_objects:
        print(Fore.GREEN + " + %s" % obj)
    for obj in old_objects:
        print(Fore.RED + " - %s" % obj)
    for obj in same_objects:
        print(Fore.WHITE + " ~ %s" % obj)
    print(Style.RESET_ALL)

def find_version_from_ref(ref, versioning):
    """Returns the version name related to a ref"""
    if ref in versioning["versions"]:
        return ref
    elif ref in versioning["branches"]:
        return versioning["branches"][ref]
    elif ref in versioning["tags"]:
        return versioning["tags"][ref]

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
        cm = self._citymodel
        version_name = self._version
        output_file = self._output

        versioning = cm["versioning"]
        if version_name not in versioning["versions"]:
            print("There is no version '%s' in the provided versioned CityJSON" % version_name)
            quit()
        
        new_model = json.loads(minimal_json)
        print("Extracting version '%s':" % version_name)
        version = versioning["versions"][version_name]
        for obj_id in version["objects"]:
            if obj_id not in cm["CityObjects"]:
                print("  Object '%s' not found! Skipping..." % obj_id)
                continue

            new_obj = cm["CityObjects"][obj_id]
            if self._objectid_property != None:
                new_id = new_obj[self._objectid_property]
            else:
                new_id = obj_id
            new_model["CityObjects"][new_id] = new_obj
        with open(output_file, "w") as outfile:
            json.dump(new_model, outfile)

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

        versioning = cm["versioning"]

        new_version = find_version_from_ref(new_version, versioning)
        old_version = find_version_from_ref(old_version, versioning)

        print("This is the diff between %s and %s" % (new_version, old_version))

        print_diff_of_versions(versioning["versions"][new_version], versioning["versions"][old_version])

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
            ValueError(command_name)
        return command_builder(**args)
    
    def list_commands(self):
        return self._builders.keys()

factory = CommandFactory()
factory.register_builder("log", LogCommandBuilder())
factory.register_builder("checkout", CheckoutCommandBuilder())
factory.register_builder("diff", DiffCommandBuilder())