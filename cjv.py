"""Main module that defines the cjv command-line logic."""

import commands
import os.path
import sys

import click

from cityjson.versioning import VersionedCityJSON
from cityjson.citymodel import CityJSON

class PerCommandArgWantSubCmdHelp(click.Argument):
    """Class to allow for the use of '--help' with any command.

    https://stackoverflow.com/questions/47437472/in-python-click-how-do-i-see-help-for-subcommands-whose-parents-have-required
    """
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
@click.argument('v_cityjson', cls=PerCommandArgWantSubCmdHelp)
@click.pass_context
def cli(context, v_cityjson):
    """A tool to create and manipulate versioned CityJSON
    files.

    V_CITYJSON can be either a versioned CityJSON file or the word 'init'.
    """

    context.obj = {"filename": v_cityjson}

@cli.result_callback()
def process_pipeline(processor, v_cityjson):
    """Process the input versioned CityJSON file."""
    if v_cityjson == "init":
        citymodel = VersionedCityJSON()
    else:
        if not os.path.isfile(v_cityjson):
            click.secho("ERROR: This file does not exist!", fg="red")
            sys.exit()
        citymodel = VersionedCityJSON.from_file(v_cityjson)

    if "versioning" not in citymodel:
        click.secho("The file provided is not a versioned CityJSON!", fg="red")
        sys.exit()

    processor(citymodel)

@cli.command()
@click.argument('refs', nargs=-1)
@click.option('--graph', is_flag=True, help='show history as graph')
def log(refs, graph):
    """Prints the history of a versioned CityJSON file.

    REFs is a list of refs (ids, tags or branch names)
    """
    if len(refs) == 0:
        refs = ["main"]
    def processor(citymodel):
        command = commands.LogCommand(citymodel, refs, graph)
        command.execute()
    return processor

@cli.command()
@click.argument('ref')
@click.argument('output')
@click.option('--objectid_property',
              default='cityobject_id',
              show_default=True,
              help='property name of the original city object id')
@click.option('--no_objectid', is_flag=True)
def checkout(ref, output, objectid_property, no_objectid):
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
def diff(dest_ref, source_ref):
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
        output = context.obj["filename"]
    def processor(citymodel):
        command = commands.RehashCommand(citymodel, output)
        command.execute()
    return processor

@cli.command()
@click.argument('new_version')
@click.argument('ref', required=False, default='main')
@click.option('-a', '--author', prompt='Provide your name', help='name of the author')
@click.option('-m', '--message', help='decsription of the changes')
@click.option('-o', '--output')
@click.pass_context
def commit(context, new_version, ref, author, message, output):
    """Add a new version to the history based on the NEW_VERSION CityJSON file.
    """
    if output is None:
        output = context.obj["filename"]
    if message is None:
        message = click.edit('Write your message here')
        if message is None:
            click.echo("No message provided. Doei!")
            quit()
    new_citymodel = CityJSON.from_file(new_version)
    def processor(citymodel):
        command = commands.CommitCommand(citymodel,
                                         new_citymodel,
                                         ref,
                                         author,
                                         message)
        command.execute()

        click.echo("Saving {}...".format(output))
        citymodel.save(output)
    return processor

def print_branches(ctx, param, value):
    """Lists the branches available in the file"""
    def list_processor(citymodel):
        click.echo("The following branches are available:")

        for b in citymodel.versioning.branches:
            click.echo(f"- {b}")

    process_pipeline(list_processor, ctx.obj["filename"])

    ctx.exit()

@cli.command()
@click.option('-v', '--list', is_flag=True, callback=print_branches, is_eager=True,
              help="list all branches")
@click.option('-d', '--delete', is_flag=True, help="delete the branch")
@click.argument('branch')
@click.argument('ref', default='main', required=False)
@click.option('-o', '--output')
@click.pass_context
def branch(context, delete, branch_name, ref, output):
    """Create or delete branches.

    BRANCH is the name of the branch.

    REF will be used as base if a branch is
    created (default is 'main', if not provided)
    """
    if output is None:
        output = context.obj["filename"]

    def delete_processor(citymodel):
        command = commands.BranchDeleteCommand(citymodel, branch_name, output)
        command.execute()
    def create_processor(citymodel):
        command = commands.BranchCommand(citymodel, ref, branch_name, output)
        command.execute()

    if delete:
        return delete_processor
    elif list:
        click.echo("Here are the branches:")
    else:
        return create_processor

@cli.command()
@click.argument('source_branch')
@click.argument('dest_branch', default = 'main')
@click.option('-a', '--author', prompt='Provide your name', help='name of the author')
@click.option('-o', '--output')
@click.pass_context
def merge(context, source_branch, dest_branch, author, output):
    """Merges a branch to another one.

    SOURCE_BRANCH is the branch to merge.

    DEST_BRANCH is the branch to get the changes
    of SOURCE_BRANCH (default is 'main')
    """
    if output is None:
        output = context.obj["filename"]

    def processor(citymodel: 'VersionedCityJSON'):
        command = commands.MergeBranchesCommand(citymodel,
                                                source_branch,
                                                dest_branch,
                                                author,
                                                output)
        command.execute()

        citymodel.save(output)

    return processor

if __name__ == "__main__":
    cli()
