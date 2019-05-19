import json
import hashlib

# Code to have colors at the console output
from colorama import init, Fore, Back, Style
init()

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

    print("\nChanges:\n")

    if len(new_objects):
        print("{color}".format(color=Fore.GREEN), end='')
        for obj in new_objects:
            print("\tadded: {0}".format(obj))
    if len(old_objects):
        print("{color}".format(color=Fore.RED), end='')
        for obj in old_objects:
            print("\tdeleted: {0}".format(obj))
    
    if len(same_objects):
        print("{color}\nNot changed:\n".format(color=Style.RESET_ALL))
        for obj in same_objects:
            print("\t{0}".format(obj))

def find_version_from_ref(ref, versioning):
    """Returns the version name related to a ref"""
    if ref in versioning["versions"]:
        return ref
    elif ref in versioning["branches"]:
        return versioning["branches"][ref]
    elif ref in versioning["tags"]:
        return versioning["tags"][ref]
    
    raise KeyError("There is no {ref} in the file!".format(ref=ref))

def is_ref_branch(ref, versioning):
    return ref in versioning["branches"]

def load_cityjson(input_file):
    print("Opening %s..." % input_file)

    # Parse the CityJSON file through the json library
    cityjson_data = open(input_file)
    try:
        citymodel = json.load(cityjson_data)
    except:
        print("Oops! This is not a valid JSON file!")
        quit()
    cityjson_data.close()

    return citymodel

def save_cityjson(citymodel, output_file):
    with open(output_file, "w") as outfile:
        json.dump(citymodel, outfile)

def get_versioned_city_objects(cm, version_name):
    """Returns the versioned city objects of a given version"""
    new_objects = {}
    version = cm["versioning"]["versions"][version_name]
    for obj_id in version["objects"]:
        if obj_id not in cm["CityObjects"]:
            print("  Object '%s' not found! Skipping..." % obj_id)
            continue

        new_objects[obj_id] = cm["CityObjects"][obj_id]
    
    return new_objects

def convert_to_regular_city_objects(v_city_objects, id_property_name="cityobject_id"):
    """Converts versioned city objects to regular objects (by replacing their ids)"""
    new_objects = {}
    for obj_id, obj in v_city_objects.items():
        if id_property_name != None:
            new_id = obj[id_property_name]
            del obj[id_property_name]
        else:
            new_id = obj_id
        new_objects[new_id] = obj
    
    return new_objects

def convert_to_versioned_city_objects(city_objects, id_property_name="cityobject_id"):
    """Converts regular city objects to versioned"""
    new_objects = {}
    for obj_id, obj in city_objects.items():
        new_id = get_hash_of_object(obj)
        obj[id_property_name] = obj_id
        new_objects[new_id] = obj
    
    return new_objects

def get_hash_of_object(object):
    # TODO This has to normalise the input (sort as well)
    encoded = json.dumps(object).encode('utf-8')
    m = hashlib.new('sha1')
    m.update(encoded)
    return m.hexdigest()

def build_dag_from_version(G, versions, last_key):
    """Builds a DAG starting from a branch"""
    next_key = last_key
    next_ver = versions[last_key]
    G.add_node(next_key)
    if "parents" in next_ver:
        for parent in next_ver["parents"]:
            if not G.has_node(parent):
                G = build_dag_from_version(G, versions, parent)
            G.add_edge(parent, next_key)
        
    return G

def find_root(G, node):
    if len(list(G.predecessors(node))) > 0:  #True if there is a predecessor, False otherwise
        root = find_root(G,list(G.predecessors(node))[0])
    else:
        root = node
    return root