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

def get_hash_of_object(object):
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