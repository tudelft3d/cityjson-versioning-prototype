import os.path
import click
import json
import sys
import commands
import utils

# Code to have colors at the console output
from colorama import init, Fore, Back, Style
init()

#-- https://stackoverflow.com/questions/47437472/in-python-click-how-do-i-see-help-for-subcommands-whose-parents-have-required
class PerCommandArgWantSubCmdHelp(click.Argument):
    def handle_parse_result(self, ctx, opts, args):
        # check to see if there is a --help on the command line
        if any(arg in ctx.help_option_names for arg in args):
            # if asking for help see if we are a subcommand name
            for arg in opts.values():
                if arg in ctx.command.commands:
                    # this matches a sub command name, and --help is
                    # present, let's assume the user wants help for the
                    # subcommand
                    args = [arg] + args
        return super(PerCommandArgWantSubCmdHelp, self).handle_parse_result(
            ctx, opts, args)

@click.group()
@click.argument('input', cls=PerCommandArgWantSubCmdHelp)
@click.pass_context
def cli(context, input):
    """A tool to create and manipulate versioned CityJSON
    files.

    INPUT can be either a versioned CityJSON file or the word 'init'.
    """

    context.obj = {"filename": input}

@cli.resultcallback()
def process_pipeline(processor, input):
    if input == "init":
        citymodel = utils.create_vcityjson()
    else:
        if not os.path.isfile(input):
            click.echo(Fore.RED + "ERROR: This file does not exist!")
            quit()
        citymodel = utils.load_cityjson(input)
    
    if "versioning" not in citymodel:
        print(Fore.RED + "The file provided is not a versioned CityJSON!")
        quit()

    processor(citymodel)

@cli.command()
@click.argument('ref', default="master")
@click.pass_context
def log(context, ref):
    """Prints the history of a versioned CityJSON file.
    
    REF is a valid reference to a commit (its id, a tag or a branch)
    """
    def processor(citymodel):
        vcm = citymodel

        command = commands.LogCommand(vcm, ref)
        command.execute()
    return processor

def something():
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
