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
    
    REF is a ref to a commit (id, tag or branch name)
    """
    def processor(citymodel):
        vcm = citymodel

        command = commands.LogCommand(vcm, ref)
        command.execute()
    return processor

@cli.command()
@click.argument('ref')
@click.argument('output')
@click.option('--objectid_property', default='cityobject_id', show_default=True, help='property name of the original city object id')
@click.option('--no_objectid', is_flag=True)
@click.pass_context
def checkout(context, ref, output, objectid_property, no_objectid):
    """Extract a version from a specific commit.
    
    REF is a ref to a commit (id, tag or branch name).
    OUTPUT is the path of the output CityJSON."""
    def processor(citymodel):
        command = commands.CheckoutCommand(citymodel, ref, output)
        command.set_objectid_property(objectid_property)
        if no_objectid:
            command.set_objectid_property(None)
        command.execute()
    return processor

@cli.command()
@click.argument('source_ref')
@click.argument('dest_ref')
@click.pass_context
def diff(context, source_ref, dest_ref):
    """Show the differences between two commits."""
    def processor(citymodel):
        command = commands.DiffCommand(citymodel, dest_ref, source_ref)
        command.execute()
    return processor

@cli.command()
@click.argument("output", required=False)
@click.pass_context
def rehash(context, output):
    if output is None:
        output=context.obj["filename"]
    """Recalculate all object and commit ids as hashes."""
    def processor(citymodel):
        command = commands.RehashCommand(citymodel, output)
        command.execute()
    return processor

@cli.command()
@click.argument('new_version')
@click.argument('ref')
@click.argument('author')
@click.argument('message')
@click.argument('output', required=False)
@click.pass_context
def commit(context, new_version, ref, author, message, output):
    """Add a new version to the history based on the NEW_VERSION CityJSON file."""
    if output is None:
        output = context.obj["filename"]
    def processor(citymodel):
        command = commands.CommitCommand(citymodel, new_version, ref, author, message, output)
        command.execute()
    return processor

@cli.command()
@click.option('-d', '--delete', is_flag=True)
@click.argument('branch')
@click.argument('ref', required=False)
@click.option('-o', '--output')
@click.pass_context
def branch(context, delete, branch, ref, output):
    """Create or delete branches"""
    if output is None:
        output = context.obj["filename"]

    def delete_processor(citymodel):
        command = commands.BranchDeleteCommand(citymodel, branch, output)
        command.execute()
    def create_processor(citymodel):
        command = commands.BranchCommand(citymodel, ref, branch, output)
        command.execute()
    
    if delete:
        return delete_processor
    else:
        return create_processor