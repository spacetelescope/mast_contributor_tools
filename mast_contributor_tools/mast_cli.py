# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Main entry point into mast_contributor tools
"""

from typing import Union

import click

from mast_contributor_tools.filename_check.fc_app import check_filenames, check_single_filename, get_file_paths, logger
from mast_contributor_tools.metadata_check import validate_fits_file  # added
from pathlib import Path


# ==========================================
# Command Line Interface (CLI) commands for mast contributor tools
# Implemented using the click pacakge: https://pypi.org/project/click/
# ==========================================
@click.group("mct")
def cli() -> None:
    """
    Command-line interface for mast_contributor_tools package.

    To see more options for each command, you can use `--help` after each command.
    For instance, `mct check_filenames --help`
    """


# ==========================================
# CLI commands for filename checker
# =========================================
@cli.command("check_filenames", short_help="Check files in a directory against MAST HLSP naming standards")
@click.argument("hlsp_name")
@click.option(
    "-dir", "--directory", type=str, default=".", help="Path of HLSP directory tree; tests all files in that directory"
)
@click.option(
    "-file",
    "--from_file",
    type=str,
    default="",
    help="Path to a text file containing a list of filenames to check, instead of scanning a directory",
)
@click.option(
    "-p", "--pattern", default="*.*", help="File pattern to limit testing, for example 'hlsp\\_\\*\\_spec.fits'"
)
@click.option("-e", "--exclude", default="", help="File pattern to exclude from testing, for example '\\*.png'")
@click.option("-n", "--max_n", default=None, help="Maximum number of files to check, for testing purposes.")
@click.option("-db", "--dbFile", default="", help="Results database filename (defaults to: results_<hlsp_name>.db)")
@click.option("-v", "--verbose", default=False, flag_value=True, help="Enable verbose output")
def filenames_cli(
    hlsp_name: str,
    directory: str = ".",
    from_file: str = "",
    pattern: str = "*.*",
    exclude: str = "",
    max_n: Union[int, None] = None,
    dbfile: str = "",
    verbose: bool = False,
) -> None:
    """
    Command for checking file names in a directory against MAST standards.

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

    """
    # Update logger level for verbose
    if verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel(logger.level)

    # Set default db file name
    if not dbfile:
        dbfile = f"results_{hlsp_name}.db"

    # make hlsp_name argument lower case
    hlsp_name = hlsp_name.lower()

    # Create list of files to check
    file_list = get_file_paths(
        directory, from_file=from_file, search_pattern=pattern, exclude_pattern=exclude, max_n=max_n
    )

    # Perform the file name check
    check_filenames(hlsp_name, file_list, dbFile=dbfile)


@cli.command("check_filename", short_help="Check a single file name against MAST HLSP naming standards")
@click.argument("filenames", nargs=-1)  # nargs=-1 allows variable number of arguments
@click.option("-v", "--verbose", default=False, flag_value=True, help="Enable verbose output")
def single_filename_cli(filenames: str = "", verbose: bool = False) -> None:
    """
    Command for checking a single file name against MAST standards.

    Required Arguments:
        FILENAMES is the name of at least one file to test. It does not need to be a real file.
        Additional files can be provided as additional arguments.

    Example Usage:

        To test a single filename (does not have to be a real file):

            mct check_filename hlsp_my-hlsp_readme.txt

        You can also test multiple filenames at once by providing them as additional arguments, for example:

            mct check_filename hlsp_my-hlsp_hst_wfc3_multi_galaxy1_v1_spec.fits hlsp_my-hlsp_hst_wfc3_multi_galaxy2_v1_spec.fits

    """
    # Update logger level for verbose
    if verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel(logger.level)

    # Check the file name
    for filename in filenames:
        check_single_filename(filename)


# ==========================================
# CLI command for metadata checker
# ==========================================
@cli.command("check_metadata", short_help="Check FITS metadata against HLSP guidelines")
@click.argument("filenames", nargs=-1)
@click.option("-hlsp", "--hlsp-name", default="", help="Expected HLSP name to cross-check with header HLSPNAME")
@click.option("-dir", "--directory", type=str, default=".", help="Path of HLSP directory tree; tests files in that directory")
@click.option(
    "-file",
    "--from_file",
    type=str,
    default="",
    help="Path to a text file containing a list of filenames to check, instead of scanning a directory",
)
@click.option("-p", "--pattern", default="*.fits", help="File pattern to limit testing, for example '*.fits'")
@click.option("-v", "--verbose", default=False, flag_value=True, help="Enable verbose output")
def metadata_cli(filenames: tuple[str, ...], hlsp_name: str = "", directory: str = ".", from_file: str = "", pattern: str = "*.fits", verbose: bool = False) -> None:
    """
    Command for checking FITS metadata for one or more files.

    Provide file names directly:
        mct check_metadata file1.fits file2.fits

    Or scan a directory / use a file list:
        mct check_metadata --directory='tutorial-data/' --pattern='*.fits'
        mct check_metadata --from_file='file_list.txt'
    """
    # Update logger level for verbose
    if verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel(logger.level)

    # Build list of files to validate
    if filenames:
        file_list = [Path(f) for f in filenames]
    else:
        # reuse existing helper to build list from directory or from_file
        file_list = get_file_paths(directory, from_file=from_file, search_pattern=pattern)

    # Validate each file and print a concise summary
    for fp in file_list:
        try:
            summary = validate_fits_file(fp, hlsp_name=hlsp_name if hlsp_name else None)
        except Exception as e:
            logger.error("Error validating %s: %s", fp, e)
            continue

        # Print top-level verdict
        logger.critical(f"Metadata evaluation for {summary.get('filepath')}: {summary.get('overall_verdict')}")
        # Print per-key verdicts (compact)
        for k in summary.get("keys", []):
            for keyname, info in k.items():
                logger.debug(f"  {keyname}: {info.get('verdict')} - {info.get('message', '')}")


# ==========================================
# Add more commands here in the future! For example:
# ==========================================
# @cli.command("check_metadata", short_help="Check file metadata information against MAST HLSP standards")


if __name__ == "__main__":
    cli()
