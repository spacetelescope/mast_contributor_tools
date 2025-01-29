# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Main entry point into mast_contributor tools
"""

from typing import Union

import click

from mast_contributor_tools.filename_check.fc_app import check_filenames, check_single_filename, get_file_paths, logger


# ==========================================
# CLI commands for mast contributor tools
# click package docs: https://pypi.org/project/click/
# ==========================================
@click.group("mct")
def cli() -> None:
    """
    Command-line interface for mast_contributor_tools package.
    """


# ==========================================
# CLI commands for filename checker
# ==========================================
@cli.command("check_filenames", short_help="Check filenames against MAST HLSP standards")
@click.argument("hlsp_name")
@click.option(
    "-dir", "--directory", type=str, default=".", help="Path of HLSP directory tree; tests files in that directory"
)
@click.option("-f", "--filename", default="", help="Name of a single file to test")
@click.option("-p", "--pattern", default="*.*", help="File pattern to limit testing, for example 'hlsp_*_spec.fits'")
@click.option("-e", "--exclude", default="", help="File pattern to exclude from testing, for example '*.png'")
@click.option("-n", "--max_n", default=None, help="Maximum number of files to check, for testing purposes.")
@click.option("-db", "--dbFile", default="", help="Results database filename (defaults to: results_<hlsp_name>.db)")
@click.option("-v", "--verbose", default=False, flag_value=True, help="Enable verbose output")
def filenames_cli(
    hlsp_name: str,
    directory: str = ".",
    filename: str = "",
    pattern: str = "*.*",
    exclude: Union[str, None] = None,
    max_n: Union[str, int, None] = None,
    dbfile: str = "",
    verbose: bool = False,
) -> None:
    """
    Command for checking file names against MAST standards.

    Required Arguments:
        HLSP_NAME is the name of the HLSP collection

    Example Usage:

        To check all files in the current working directory, run the command:

            mct check_filenames <my-hlsp>

        where '<my-hlsp>' is the name of your HLSP.

        This command is also equivalent to:

            mct check_filenames my-hlsp -dir='.' -p='*.*' --dbFile='results_my-hlsp.db'

        To check all files in a specified directory matching a certain file pattern:

            mct check_filenames my-hlsp -dir='subdir' -p='*.fits'

        This example will only check files ending with ".fits" in the directory "subdir"

        To test a single filename (does not have to be a real file):

            mct check_filenames my-hlsp --filename='hlsp_my-hlsp_jwst_nirspec_starname_multi_v1_spec.fits'
    """
    # Update logger level for verbose
    if verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel(logger.level)

    # Set default db file name
    if not dbfile:
        dbfile = f"results_{hlsp_name}.db"

    # For checking a single file name
    if filename:
        check_single_filename(filename, hlsp_name)

    # For checking the whole directory:
    else:
        if max_n:
            max_n = int(max_n)
        file_list = get_file_paths(directory, search_pattern=pattern, exclude_pattern=exclude, max_n=max_n)
        check_filenames(hlsp_name, file_list, dbFile=dbfile)


# ==========================================
# Add more commands here in the future! For example:
# ==========================================
# @cli.command("check_metadata", short_help="Check file metadata information against MAST HLSP standards")


if __name__ == "__main__":
    cli()
