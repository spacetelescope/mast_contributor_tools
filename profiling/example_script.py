"""
example_script.py

This script is intended to be called using cProfile in bash. For Example:

>>> python -m cProfile -s tottime example_script.py phast > profiling_phast.txt
>>> python -m cProfile -s tottime example_script.py t16 /ifs/archive/ops/mast/public/hlsp/t16/s0003/cam1-ccd1 > profiling_t16.txt

There is an executable bash script `profile_mct.sh` in this folder for convienience.
"""

import os
from sys import argv

from mast_contributor_tools.filename_check.fc_app import check_filenames, get_file_paths


def run_checker(hlsp_name, directory=None):
    """
    If `directory` is not specified, just assume the HLSP's directory on the Test Isilon.
    """
    if directory is None:
        directory = os.path.join("/ifs/archive/test/mast/public/hlsp", hlsp_name)

    # Set default db file name
    dbfile = f"results_{hlsp_name}.db"

    # make hlsp_name argument lower case
    hlsp_name = hlsp_name.lower()

    # Check all files in the directory
    file_list = get_file_paths(directory, search_pattern="*.fits")
    check_filenames(hlsp_name, file_list, dbFile=dbfile)


if __name__ == "__main__":
    try:
        arg1, arg2 = argv[1:]
    except:
        arg1 = argv[1]
        arg2 = None

    run_checker(arg1, arg2)