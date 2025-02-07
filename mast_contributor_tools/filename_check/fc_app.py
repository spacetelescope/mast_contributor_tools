import os
from pathlib import Path
from typing import Union

from tqdm import tqdm

from mast_contributor_tools.filename_check.fc_db import Hlsp_SQLiteDb
from mast_contributor_tools.filename_check.hlsp_filename import FieldRule, HlspFileName
from mast_contributor_tools.utils.logger_config import setup_logger

logger = setup_logger(__name__)


def get_file_paths(
    hlsp_path: str,
    search_pattern: str = "*.*",
    exclude_pattern: Union[str, None] = None,
    max_n: Union[int, None] = None,
) -> list[Path]:
    """
    Build a list of filename Paths relative to the given directory.

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
        Maximum number of files to check, for testing purposes. For example,
        max_n=10 will only check the first 10 files found.

    Returns
    -------
    list[Path]
        A list of filename Paths contained within the given directory
    """
    # Set current directory if no directory specified
    if not hlsp_path:
        base_path = Path.cwd()
    else:
        base_path = Path(hlsp_path)

    # Search for files matching the pattern
    file_list = [p.relative_to(base_path) for p in base_path.rglob(search_pattern) if p.is_file()]

    # Exclude files
    if exclude_pattern:
        exclude_list = [p.relative_to(base_path) for p in base_path.rglob(exclude_pattern) if p.is_file()]
        file_list = [f for f in file_list if f not in exclude_list]

    # Limit number of files returned to first n rows for testing purposes
    if max_n:
        if int(max_n) < len(file_list):
            file_list = file_list[: int(max_n)]

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
    # Make sure hlsp name is valid
    if not FieldRule.hlsp_expr.match(hlsp_name):
        msg = (
            f"Invalid hlsp_name for HLSP collection: '{hlsp_name}'.\n"
            "The HLSP name must follow these rules: \n"
            "\t 1. The first character must be a lowercase letter \n"
            "\t 2. The middle characters can be lowercase letters, numbers, or a hyphen ‘-‘ \n"
            "\t 3. The last character must be a lowercase letter or a number \n"
            "\t 4. The hlsp_name must be 20 characters or less in length"
        )
        logger.error(msg)
        raise ValueError(msg)

    # Beging file name checking
    logger.critical(f"Evaluating {len(file_list)} files for HLSP collection '{hlsp_name}'")
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
        try:
            hfn = HlspFileName(f, hlsp_name)
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


def check_single_filename(file_name: str, hlsp_name: str = "") -> None:
    """HLSP filename module CLI driver.

    Parameters
    ----------
    file_name : str
        File name of an HLSP product to test: for example 'hlsp_my-hlsp_readme.txt'.
        This is a string, and does not need to be a real file.
    hlsp_name : str, optional
        Name of example HLSP collection. For example, 'my-hlsp'.
        If not supplied, the hlsp_name is inferred using the second field of the filename.
    """
    # Infer hlsp_name from the file name if it wasn't provided
    if not hlsp_name:
        if len(file_name.split("_")) > 2:
            hlsp_name = file_name.split("_")[1].lower()
        else:
            msg = f"Could not infer HLSP name from filename '{file_name}'. Not enough parts in filename."
            logger.error(msg)
            raise ValueError(msg)

    # Check file name fields
    fp = Path(file_name)
    hfn = HlspFileName(fp, hlsp_name)
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

    logger_msg = f"Evaluating filename: {file_name} \n"
    for p, v in file_rec.items():
        logger_msg += f"  {p}: {v} \n"
    logger_msg += f"Final Score: {file_rec['status'].upper()}"
    logger.critical(logger_msg)
