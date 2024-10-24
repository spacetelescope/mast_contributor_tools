import argparse
from pathlib import Path
import re
from fc_db import Hlsp_SQLiteDb
from hlsp_filename import HlspFileName

FILE_REGEX = re.compile(r'^[a-zA-Z0-9][\w\-]+(\.\w+)?(\.[\w]+(\.gz|\.zip)?)$')

def get_file_paths(hlsp_path):
    """Build a list of filename Paths relative to the given directory
    
    Parameters
    ----------
    base_dir : str
        Head of directory containing HLSP collection files. The base directory 
        defaults to the current working directory.
    
    Returns
    -------
    paths : list(Path)
        A list of filename Paths contained within the given directory
    """
    if not hlsp_path:
        base_path = Path.cwd()
    else:
        base_path = Path(hlsp_path)
    return [p.relative_to(base_path) for p in base_path.rglob('*.*') if re.match(FILE_REGEX, p.name)]

def check_filenames(base_dir, hlsp_name, dbFile, verbose):
    """Recursively check filenames in a directory tree of HLSP products

    Parameters
    ----------
    base_dir : str
        Head of directory containing HLSP collection files
    hlsp_name : str
        Official identifier (abbreviation/acronym/initialism) for the HLSP collection
    dbFile : str
        Name of SQLite database file to contain results
    """
    print(f'\nChecking files for HLSP collection {hlsp_name}')
    files = get_file_paths(base_dir)
    print(f'  Creating results database {dbFile}')
    if Path(dbFile).is_file():
        print(f'  WARNING: Database file {dbFile} already exists')
    db = Hlsp_SQLiteDb(dbFile)
    db.create_db()

    # Evaluate each filename
    for f in files:
        if verbose:
            print(f'  Examining {f.name}')
        hfn = HlspFileName(f,hlsp_name)
        try:
            hfn.partition()
        except:
            print(f'  Invalid name: {f.name}, skipping...')
        else:
            hfn.create_fields()
            elements = hfn.evaluate_fields()
            # Link elements to parent filename in db
            for e in elements:
                e['file_ref'] = f.name
            file_rec = hfn.evaluate_filename()
            # Record the results in the db
            try:
               db.add_filename(file_rec)
            except:
                print(f'Error adding {f.name}')
            else:
                db.add_fields(elements)
    
    db.close_db()

if __name__ == '__main__':
    """HLSP filename validator top-level application.
    """
    descr_text = 'Validate names for a directory of HLSP science products'
    parser = argparse.ArgumentParser(description=descr_text)
    parser.add_argument('base_dir', type=str, default='.',
                        help='Path of HLSP directory tree')
    parser.add_argument('hlsp_name', type=str, 
                        help='Name of HLSP collection')
    parser.add_argument('-d', '--dbFile', type=str, default='results.db',
                        help='Results database filename')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable diagnostic output')
    args = parser.parse_args()
    
    check_filenames(args.base_dir, args.hlsp_name, args.dbFile, args.verbose)
