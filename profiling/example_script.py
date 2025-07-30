import os
from sys import argv

from mast_contributor_tools.filename_check.fc_app import check_filenames, get_file_paths


def run_checker(hlsp_name, directory=None):
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