#!/usr/local/bin/python3

import json
import sys
import commands
import utils

# Code to have colors at the console output
from colorama import init, Fore, Back, Style
init()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a (versioned) CityJSON file")
        quit()

    # The filename of the CityJSON file to be analysed
    versioned_filename = sys.argv[1]

    if len(sys.argv) < 3:
        print("Please provide a command. Available commands:\n{0}.".format('\n'.join(["- {0}".format(v) for v in commands.factory.list_commands()])))
        quit()

    command_name = sys.argv[2]

    if versioned_filename == "init":
        citymodel = utils.create_vcityjson()
    else:
        citymodel = utils.load_cityjson(versioned_filename)

    args = {}
    args["vcitymodel"] = citymodel
    args["args"] = sys.argv

    if "versioning" not in citymodel:
        print(Fore.RED + "The file provided is not a versioned CityJSON!")
        quit()
    
    try:
        command = commands.factory.create_command(command_name, **args)
    except:
        print("'%s' is not a valid command. Please try one of: %s." % (command_name, ', '.join([v for v in commands.factory.list_commands()])))
        quit()
    
    if command == None:
        print("'%s' is not a valid command. Please try one of: %s." % (command_name, ', '.join([v for v in commands.factory.list_commands()])))
        quit()

    command.execute()

    # TODO: Validate "versioning" property (should have versions, branches and tags)
