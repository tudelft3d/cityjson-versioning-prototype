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
@click.argument('refs', nargs=-1)
@click.option('--graph', is_flag=True, help='show history as graph')
@click.pass_context
def log(context, refs, graph):
    """Prints the history of a versioned CityJSON file.
    
    REFs is a list of refs (ids, tags or branch names)
    """
    if len(refs) == 0:
        refs = ["master"]
    def processor(citymodel):
        vcm = citymodel

        command = commands.LogCommand(vcm, refs, graph)
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
@click.argument('dest_ref')
@click.argument('source_ref')
@click.pass_context
def diff(context, dest_ref, source_ref):
    """Show the differences between two commits."""
    def processor(citymodel):
        command = commands.DiffCommand(citymodel, dest_ref, source_ref)
        command.execute()
    return processor

@cli.command()
@click.argument("output", required=False)
@click.pass_context
def rehash(context, output):
    """Recalculate all object and commit ids as hashes."""
    if output is None:
        output=context.obj["filename"]
    def processor(citymodel):
        command = commands.RehashCommand(citymodel, output)
        command.execute()
    return processor

@cli.command()
@click.argument('new_version')
@click.argument('ref', required=False, default='master')
@click.option('-a', '--author', prompt='Provide your name', help='name of the author')
@click.option('-m', '--message', help='decsription of the changes')
@click.option('-o', '--output')
@click.pass_context
def commit(context, new_version, ref, author, message, output):
    """Add a new version to the history based on the NEW_VERSION CityJSON file."""
    if output is None:
        output = context.obj["filename"]
    if message is None:
        message = click.edit('Write your message here')
        if message is None:
            click.echo("No message provided. Doei!")
            quit()
    def processor(citymodel):
        command = commands.CommitCommand(citymodel, new_version, ref, author, message, output)
        command.execute()
    return processor

@cli.command()
@click.option('-d', '--delete', is_flag=True, help="delete the branch")
@click.argument('branch')
@click.argument('ref', default='master', required=False)
@click.option('-o', '--output')
@click.pass_context
def branch(context, delete, branch, ref, output):
    """Create or delete branches.
    
    BRANCH is the name of the branch.
    
    REF will be used as base if a branch is
    created (default is 'master', if not provided)
    """
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

@cli.command()
@click.argument('source_branch')
@click.argument('dest_branch', default = 'master')
@click.option('-a', '--author', prompt='Provide your name', help='name of the author')
@click.option('-o', '--output')
@click.pass_context
def merge(context, source_branch, dest_branch, author, output):
    """Merges a branch to another one.

    SOURCE_BRANCH is the branch to merge.

    DEST_BRANCH is the branch to get the changes
    of SOURCE_BRANCH (default is 'master')
    """
    if output is None:
        output = context.obj["filename"]

    def processor(citymodel):
        command = commands.MergeBranchesCommand(citymodel,
                                                source_branch,
                                                dest_branch,
                                                author,
                                                output)
        command.execute()
    
    return processor