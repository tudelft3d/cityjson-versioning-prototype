#!/usr/local/bin/python3

import json
import sys

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

def show_history(cm, ref="master"):
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
            
def extract_version(cm, version_name, output_filename):
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
    with open(output_filename, "w") as outfile:
        json.dump(new_model, outfile)

# THE SCRIPT STARTS HERE

if len(sys.argv) < 2:
    print("Please provide a (versioned) CityJSON file")
    quit()

# The filename of the CityJSON file to be analysed
versioned_filename = sys.argv[1]

if len(sys.argv) < 3:
    print("Please provide a command.")
    quit()

command = sys.argv[2]

print("Opening %s..." % versioned_filename)

# Parse the CityJSON file through the json library
cityjson_data = open(versioned_filename)
try:
    citymodel = json.load(cityjson_data)
except:
    print("Oops! This is not a valid JSON file!")
    quit()
cityjson_data.close()

if "versioning" not in citymodel:
    print(Fore.RED + "The file provided is not a versioned CityJSON!")
    quit()

if command == "log":
    if len(sys.argv) > 3:
        ref = sys.argv[3]
    else:
        ref = "master"
    show_history(citymodel, ref)
elif command == "extract":
    if len(sys.argv) < 5:
        print("The 'extract' command needs a version and an output filename!")
        quit()
    version_name = sys.argv[3]
    output = sys.argv[4]
    extract_version(citymodel, version_name, output)
else:
    print("'%s' is not a valid command. Please try one of: log." % command)
    quit()

# TODO: Validate "versioning" property (should have versions, branches and tags)
