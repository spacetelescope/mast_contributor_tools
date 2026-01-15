"""Create and manage an SQLite database for storing results of file checking."""

import sqlite3

import astropy.io.fits as fits
import pandas as pd
from astropy.table import Table

# The following SQL will create am SQLite database
FILENAME_TABLE = """
        CREATE TABLE IF NOT EXISTS filename (
	    path	TEXT NOT NULL DEFAULT '.',
	    filename	TEXT NOT NULL UNIQUE,
	    final_verdict	TEXT CHECK("final_verdict" IN ('PASS', 'FAIL', 'NEEDS REVIEW')),
	    n_elements	INTEGER
        );
        """
FIELDS_TABLE = """
        CREATE TABLE IF NOT EXISTS fields (
        file_ref  TEXT NOT NULL,
	    name  TEXT NOT NULL,
        value TEXT NOT NULL,
	    capitalization_score  TEXT NOT NULL DEFAULT 'fail' CHECK("capitalization_score" IN ('pass', 'fail')),
	    length_score  TEXT NOT NULL DEFAULT 'fail' CHECK("length_score" IN ('pass', 'fail')),
	    format_score  TEXT NOT NULL DEFAULT 'fail' CHECK("length_score" IN ('pass', 'fail')),
	    value_score  TEXT NOT NULL DEFAULT 'fail' CHECK("value_score" IN ('pass', 'fail', 'needs review')),
	    field_verdict  TEXT NOT NULL DEFAULT 'FAIL' CHECK("field_verdict" IN ('PASS', 'FAIL', 'NEEDS REVIEW')),
	    FOREIGN KEY(file_ref) REFERENCES filename_db(filename)
        );
        """
PROBLEMS_VIEW = """
        CREATE VIEW IF NOT EXISTS potential_problems as
        select fn.path, fn.filename, fn.n_elements, fl.name, fl.value, fl.capitalization_score, fl.length_score,
        fl.value_score, fl.field_verdict
        from filename as fn, fields as fl
        where fn.filename = fl.file_ref
        AND fl.field_verdict != 'PASS';
        """

INSERT_FILE_RECORD = """INSERT INTO filename VALUES(:path,:filename,:final_verdict,:n_elements)"""
INSERT_FIELD_RECORD = """INSERT INTO fields VALUES(:file_ref,:name,:value,:capitalization_score,:length_score,:format_score,:value_score,:field_verdict)"""


class Hlsp_SQLiteDb:
    """Create an SQLite DB to store results.

    Parameters
    ----------
    filename : str
        name of the SQLite DB file to be created
    """

    def __init__(
        self,
        filename: str,
    ) -> None:
        self.db_file = filename

    def create_db(self) -> None:
        """Create the database and construct the tables.

        Raises
        ------
        sqlite3.Error : Error
            Raised if the DB cannot be created or the tables fail to be created.
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            for statement in [FILENAME_TABLE, FIELDS_TABLE, PROBLEMS_VIEW]:
                self.conn.execute(statement)

            # Turn on Write-Ahead Log
            # See https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = normal")
            self.conn.execute("PRAGMA journal_size_limit = 6144000")
            self.conn.commit()

        except sqlite3.Error as e:
            print(e)

    def close_db(self) -> None:
        self.conn.close()

    def add_filename(self, file_record: dict) -> None:
        """Add file metadata to the filename table

        Add file metadata to the DB in the form of a list of key:value pairs.

        Parameters
        ----------
        file_record : dict
            File attributes
        """
        self.conn.execute(INSERT_FILE_RECORD, file_record)
        self.conn.commit()

    def add_fields(self, elements: list[dict]) -> None:
        """Add metadata for each of a filename's fields to the fields table

        Add results of checking mmultiple filename fields to the fields table.
        Metadata for each field take the form of key:value pairs.

        Parameters
        ----------
        elements : list[dict]
            List of element attribute dictionaries.
        """
        self.conn.executemany(INSERT_FIELD_RECORD, elements)
        self.conn.commit()

    def print_summary(self) -> str:
        """
        Returns a string detailing some summary information on how many files have passed validation
        """
        # Get data from db
        dat = self.conn.execute("SELECT filename, final_verdict from filename").fetchall()
        # Parse numbers
        num_files = len(dat)
        num_pass = sum([1 for d in dat if d[1].upper() == "PASS"])
        num_review = sum([1 for d in dat if d[1].upper() == "NEEDS REVIEW"])
        num_fail = sum([1 for d in dat if d[1].upper() == "FAIL"])
        # Write summary message
        summary_message = "Output summary:\n    "
        summary_message += f"Files Checked: {num_files}\n    "
        summary_message += f"Files Passed: {num_pass}\n    "
        summary_message += f"Files Need Review: {num_review}\n    "
        summary_message += f"Files Failed: {num_fail}\n    "
        # All files passed
        if num_pass == num_files:
            summary_message += "All files passed!"
        elif num_review > 0:
            summary_message += "If any fields were marked with a score of 'needs review', please consult with your MAST staff contact. Unrecognized values are very often necessary and good, but require review."
        # Some files failed
        elif num_fail > 0:
            summary_message += f"See results file ({self.db_file}) for more information. Some files did not meet our criteria. Note: only fields with a final_verdict of 'fail' contributed to this result."
            # Add more detail here later? - could break down by fields, etc.

        return summary_message

    def write_to_alternate_format(self, save_format: str) -> None:
        """
        Write out the SQLite DB as an alternate format.

        Parameters
        ----------
        save_format : str
            Format to save output: 'csv', 'excel', 'html', or 'fits'
        """
        # Check that input is a valid option
        supported_formats = ["csv", "excel", "fits", "html"]
        if save_format.lower() not in supported_formats:
            msg = f"Save Format '{save_format}' is not supported."
            msg += f"Please choose from {supported_formats}"
            raise ValueError(msg)

        # Construct new filename to save to
        fileroot = self.db_file.strip(".db")

        # Read DB file as pandas dataframe
        self.conn = sqlite3.connect(self.db_file)
        filename_data = pd.read_sql_query("SELECT * FROM filename", self.conn)
        fields_data = pd.read_sql_query("SELECT * FROM fields", self.conn)
        # Close connection
        self.conn.close()

        # Save out data in new format
        # CSV files
        if save_format == "csv":
            ouput_filename1 = f"{fileroot}_filenames.csv"
            ouput_filename2 = f"{fileroot}_fields.csv"
            filename_data.to_csv(ouput_filename1)
            fields_data.to_csv(ouput_filename2)
            files_written = [ouput_filename1, ouput_filename2]
        # Excel spreadsheet
        elif save_format == "excel":
            output_filename = f"{fileroot}.xlsx"
            # Style dataframe: change color of cell depending on verdict
            filename_data = filename_data.style.map(color_formatter)
            fields_data = fields_data.style.map(color_formatter)
            # Save as one Excel document with two sheets:
            # One for filenames table and one for fields
            with pd.ExcelWriter(output_filename) as excel_writer:
                filename_data.to_excel(excel_writer, sheet_name="FileNames")
                fields_data.to_excel(excel_writer, sheet_name="Fields")
            files_written = [output_filename]

        # Fits table
        elif save_format == "fits":
            # Save as one fits file with two table extensions:
            # One for filenames table and one for fields
            output_filename = f"{fileroot}.fits"
            hdu_list = fits.HDUList(
                [
                    fits.PrimaryHDU(),  # TODO: add some metadata?
                    fits.table_to_hdu(Table.from_pandas(filename_data), name="FILENAMES"),
                    fits.table_to_hdu(Table.from_pandas(fields_data), name="FIELDS"),
                ]
            )
            hdu_list.writeto(output_filename, overwrite=True)
            files_written = [output_filename]

        # Html table
        elif save_format == "html":
            ouput_filename1 = f"{fileroot}_filenames.html"
            ouput_filename2 = f"{fileroot}_fields.html"
            # Style dataframe: change color of cell depending on verdict
            filename_data = filename_data.style.map(color_formatter)
            fields_data = fields_data.style.map(color_formatter)
            # Then write to html file
            filename_data.to_html(
                ouput_filename1,
                header=True,
            )
            fields_data.to_html(
                ouput_filename2,
                header=True,
            )
            files_written = [ouput_filename1, ouput_filename2]

        else:
            # No alternate format - only DB file
            files_written = [self.db_file]

        return files_written


def color_formatter(value: str) -> str:
    """Color mapping for use in write_to_alternate_format().
    Color-codes table cells based on verdict: green for "PASS", red for "FAIL", etc.

    Parameters
    ------
    value: str

    """
    if str(value).upper() == "PASS":
        color = "lightgreen"
    elif str(value).upper() == "FAIL":
        color = "red"
    elif str(value).upper() == "NEEDS REVIEW":
        color = "yellow"
    else:
        color = None
    return "background-color: %s" % color
