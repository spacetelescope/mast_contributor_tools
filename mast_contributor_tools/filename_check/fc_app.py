import os
import re
from pathlib import Path
from typing import Union

from tqdm import tqdm

from mast_contributor_tools.filename_check.fc_db import Hlsp_SQLiteDb
from mast_contributor_tools.filename_check.hlsp_filename import FieldRule, HlspFileName
from mast_contributor_tools.utils.logger_config import setup_logger

logger = setup_logger(__name__)

FILE_REGEX = re.compile(r"^[a-zA-Z0-9][\w\-]+(\.[\w\-]+)?(\.[\w]+(\.gz|\.zip)?)$")


def get_file_paths(
    hlsp_path: str,
    search_pattern: str = "*.*",
    exclude_pattern: Union[str, None] = None,
    max_n: Union[int, None] = None,
) -> list[Path]:
    """Build a list of filename Paths relative to the given directory

    The filenames are matched to a regex to filter out non-relevant files. The
    expression can be tested at: https://regex101.com/

    Parameters
    ----------
    hlsp_path : str
        Head of directory containing HLSP collection files. The base directory
        defaults to the current working directory.

    search_pattern : str, optional
        Search pattern to limit files to test. For example, '*.fits' will only
        return the fits files. Default value is '*.*' for all files

    exclude_pattern : str, optional
        Search pattern to exclude files from testing. For example, '*.png' will only
        skip all of the png files.

    max_n : int, optional
        Search pattern to exclude files from testing. For example, '*.png' will only
        skip all of the png files.

    Returns
    -------
    list[Path]
        A list of filename Paths contained within the given directory
    """
    if not hlsp_path:
        base_path = Path.cwd()
    else:
        base_path = Path(hlsp_path)

    # Search for files matching the pattern
    file_list = [p.relative_to(base_path) for p in base_path.rglob(search_pattern)]

    # Exclude files
    if exclude_pattern:
        exclude_list = [p.relative_to(base_path) for p in base_path.rglob(exclude_pattern)]
        file_list = [f for f in file_list if f not in exclude_list]

    # Limit number of files returned to first n rows for testing purposes
    if max_n:
        if max_n < len(file_list):
            file_list = file_list[:max_n]

    # Raise error if no files are found
    if len(file_list) == 0:
        msg = f"No files found to check against filename rules in directory ({base_path})."
        logger.error(msg)
        raise FileNotFoundError(msg)

    return file_list


def check_filenames(hlsp_name: str, file_list: list[Path], dbFile: str) -> None:
    """Recursively check filenames in a directory tree of HLSP products

    Parameters
    ----------
    hlsp_name : str
        Official identifier (abbreviation/acronym/initialism) for the HLSP collection
    file_list: list[str]
        List of files to check, typically output from get_file_paths()
    dbFile : str, optional
        Name of SQLite database file to contain results
    """
    # Make sure hlsp name is valid:
    if not FieldRule.matchHlspName(hlsp_name):
        msg = f"Invalid name for HLSP collection: {hlsp_name}"
        logger.error(msg)
        raise ValueError(msg)

    # Make sure all files in list match expected regex pattern
    file_list_match = [f for f in file_list if re.match(FILE_REGEX, f.name)]
    if len(file_list_match) != len(file_list):
        logger.warning(
            f"Skipping {len(file_list) - len(file_list_match)} of {len(file_list)} files which have invalid names."
        )
        file_list = file_list_match

    # Beging file name checking
    logger.critical(f"Evaluating {len(file_list)} files for HLSP collection {hlsp_name}")
    if Path(dbFile).is_file():
        logger.warning(f"Database file {dbFile} already exists. Overwriting File.")
        os.remove(dbFile)
    db = Hlsp_SQLiteDb(dbFile)
    logger.debug(f"Creating results database {dbFile}")
    db.create_db()

    # Evaluate each filename
    # tqdm creates the progress bar: https://tqdm.github.io/docs/tqdm/
    for f in tqdm(file_list):
        logger.debug(f"Examining {f.name}")
        hfn = HlspFileName(f, hlsp_name)
        try:
            hfn.partition()
        except ValueError:
            logger.error(f"Invalid name: {f.name}, skipping...")
        else:
            hfn.create_fields()
            elements = hfn.evaluate_fields()
            # Link elements to parent filename in db
            for e in elements:
                e["file_ref"] = f.name
            # Order is important here: evaluating filename requries fields to be evaluated
            file_rec = hfn.evaluate_filename()
            # Record the results in the db
            try:
                db.add_filename(file_rec)
            except Exception as e:
                logger.error(f"Error adding {f.name}: {e}")
            else:
                db.add_fields(elements)
            logger.debug(f"    Score for {f.name}: {file_rec['status']}")

    logger.critical(db.print_summary())  # print summary information on how many files passed
    db.close_db()
    logger.critical(f"\nFilename checking complete. Results written to {dbFile}")


def check_single_filename(inFile, hlspName) -> None:
    """HLSP filename module CLI driver.

    Parameters
    ----------
    inFile : str
        Name of example HLSP product
    hlspName : str
        Name of example HLSP collection
    """
    fp = Path(inFile)
    hfn = HlspFileName(fp, hlspName)
    hfn.partition()
    hfn.create_fields()
    elements = hfn.evaluate_fields()
    file_rec = hfn.evaluate_filename()

    # Display resuls
    for e in elements:
        logger_msg = "Individual Field evaluations: \n"
        for p, v in e.items():
            logger_msg += f"  {p}: {v} \n"
        logger.debug(logger_msg)

    logger_msg = "Evaluating filename: \n"
    for p, v in file_rec.items():
        logger_msg += f"  {p}: {v} \n"
    logger_msg += f"Final Score: {file_rec['status'].upper()}"
    logger.critical(logger_msg)
