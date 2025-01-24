import argparse
import re
from pathlib import Path

from mast_contributor_tools.filename_check.fc_db import Hlsp_SQLiteDb
from mast_contributor_tools.filename_check.hlsp_filename import FieldRule, HlspFileName
from mast_contributor_tools.utils.logger_config import setup_logger

logger = setup_logger(__name__)

FILE_REGEX = re.compile(r"^[a-zA-Z0-9][\w\-]+(\.\w+)?(\.[\w]+(\.gz|\.zip)?)$")


def get_file_paths(hlsp_path: str, search_pattern: str = "*.*") -> list[Path]:
    """Build a list of filename Paths relative to the given directory

    The filenames are matched to a regex to filter out non-relevant files. The
    expression can be tested at: https://regex101.com/

    Parameters
    ----------
    hlsp_path : str
        Head of directory containing HLSP collection files. The base directory
        defaults to the current working directory.

    search_pattern : str, optional
        Search pattern to limit files to test. For example, "*.fits" will only
        return the fits files. Default value is "*.*" for all files

    Returns
    -------
    list[Path]
        A list of filename Paths contained within the given directory
    """
    if not hlsp_path:
        base_path = Path.cwd()
    else:
        base_path = Path(hlsp_path)
    return [p.relative_to(base_path) for p in base_path.rglob(search_pattern) if re.match(FILE_REGEX, p.name)]


def check_filenames(base_dir: str, hlsp_name: str, search_pattern: str, dbFile: str) -> None:
    """Recursively check filenames in a directory tree of HLSP products

    Parameters
    ----------
    base_dir : str
        Head of directory containing HLSP collection files
    hlsp_name : str
        Official identifier (abbreviation/acronym/initialism) for the HLSP collection
    search_pattern : str, optional
        Search pattern to limit files to test. For example, "*.fits" will only
        return the fits files. Default value is "*.*" for all files
    dbFile : str, optional
        Name of SQLite database file to contain results
    """
    logger.info(f"\nChecking files for HLSP collection {hlsp_name}")
    files = get_file_paths(base_dir, search_pattern)
    logger.info(f"  Found {len(files)} files to check against filename rules")
    if Path(dbFile).is_file():
        logger.warning(f"  WARNING: Database file {dbFile} already exists")
    db = Hlsp_SQLiteDb(dbFile)
    logger.info(f"  Creating results database {dbFile}")
    db.create_db()

    # Evaluate each filename
    for f in files:
        logger.debug(f"  Examining {f.name}")
        hfn = HlspFileName(f, hlsp_name)
        try:
            hfn.partition()
        except ValueError:
            logger.error(f"  Invalid name: {f.name}, skipping...")
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


if __name__ == "__main__":
    """HLSP filename validator top-level application.
    """

    def validHlspName(hlsp_name: str):
        if not FieldRule.matchHlspName(hlsp_name):
            raise argparse.ArgumentTypeError(f"Invalid name for HLSP collection: {hlsp_name}")
        return hlsp_name

    descr_text = "Validate names for a directory of HLSP science products"
    parser = argparse.ArgumentParser(description=descr_text)
    parser.add_argument("hlsp_name", type=validHlspName, help="Name of HLSP collection")
    parser.add_argument("base_dir", type=str, default=".", help="Path of HLSP directory tree")
    parser.add_argument(
        "-p", "--pattern", type=str, default="*.*", help="File name search pattern to limit which files to test"
    )
    parser.add_argument(
        "-d",
        "--dbFile",
        type=str,
        default="",
        help="Results database filename (defaults to: results_<hlsp_name>.db)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable diagnostic output")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")

    logger.info(f"HLSP name = {args.hlsp_name}")
    if not args.dbFile:
        args.dbFile = f"results_{args.hlsp_name}.db"
    check_filenames(args.base_dir, args.hlsp_name, args.pattern, args.dbFile)
