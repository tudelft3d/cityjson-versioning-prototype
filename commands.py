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

class LogCommand:
    def __init__(self, citymodel, ref="master", **args):
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
        if ref in versioning["versions"]:
            next_versions.append(ref)
        elif ref in versioning["branches"]:
            next_versions.append(versioning["branches"][ref])
        elif ref in versioning["tags"]:
            next_versions.append(versioning["tags"][ref])

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

            print(Fore.YELLOW + "version %s" % version_name, end='')
            for branch_name, branch_ref in versioning["branches"].items():
                if branch_ref == version_name:
                    print(' (' + Fore.CYAN + branch_name + Fore.YELLOW + ')', end='')
            for tag_name, tag_ref in versioning["tags"].items():
                if tag_ref == version_name:
                    print(' (' + Fore.MAGENTA + 'tag: %s' % tag_name + Fore.YELLOW + ')', end='')
            print(Style.RESET_ALL)

            print("Author: %s" % current_version["author"])
            print("Date: %s" % current_version["date"])

            print("Message:\n\n" + Fore.CYAN + "%s\n" % current_version["message"] + Style.RESET_ALL)

            print("This is what changed in this version:")

            # If there is a previous version, output the differences
            if "parents" in current_version:
                next_versions.extend(current_version["parents"])
                previous_version = versioning["versions"][current_version["parents"][0]] # For now, assume only one parent

                # Find differences between the two versions
                new_objects = set(current_version["objects"]) - set(previous_version["objects"])
                old_objects = set(previous_version["objects"]) - set(current_version["objects"])
                same_objects = set(current_version["objects"]).intersection(set(previous_version["objects"]))

                for obj in new_objects:
                    print(Fore.GREEN + " + %s" % obj)
                for obj in old_objects:
                    print(Fore.RED + " - %s" % obj)
                for obj in same_objects:
                    print(Fore.WHITE + " ~ %s" % obj)
                print(Style.RESET_ALL)
            else:
                for obj in current_version["objects"]:
                    print(Fore.GREEN + " + %s" % obj)

class CheckoutCommand:
    def __init__(self, citymodel, version_name, output_file, **args):
        self._citymodel = citymodel
        self._version = version_name
        self._output = output_file

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
            new_model["CityObjects"][obj_id] = new_obj
        with open(output_file, "w") as outfile:
            json.dump(new_model, outfile)

class CommandFactory:
    """A factory to create commands from their names"""

    def __init__(self):
        self._commands = {}
    
    def register_command(self, command_name, command):
        """Registers a new command with the given name"""
        self._commands[command_name] = command
    
    def get_command(self, command_name, **args):
        """Get the command from a given name"""
        command = self._commands.get(command_name)
        if not command:
            ValueError(command_name)
        return command(**args)

factory = CommandFactory()
factory.register_command("log", LogCommand)
factory.register_command("checkout", CheckoutCommand)