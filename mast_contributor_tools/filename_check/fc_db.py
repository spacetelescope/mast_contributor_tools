"""Create and manage an SQLite database for storing results of file checking."""

import sqlite3

# The following SQL will create am SQLite database
FILENAME_TABLE = """
        CREATE TABLE IF NOT EXISTS filename (
	    path	TEXT NOT NULL DEFAULT '.',
	    filename	TEXT NOT NULL UNIQUE,
	    status	TEXT CHECK("status" IN ('pass', 'fail')),
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
	    value_score  TEXT NOT NULL DEFAULT 'fail' CHECK("value_score" IN ('pass', 'review')),
	    severity  TEXT NOT NULL DEFAULT 'N/A' CHECK("severity" IN ('fatal', 'unrecognized',
            'warning', 'N/A')),
	    FOREIGN KEY(file_ref) REFERENCES filename_db(filename)
        );
        """
PROBLEMS_VIEW = """
        CREATE VIEW IF NOT EXISTS potential_problems as
        select fn.path, fn.filename, fn.n_elements, fl.name, fl.value, fl.capitalization_score, fl.length_score,
        fl.value_score, fl.severity
        from filename as fn, fields as fl
        where fn.filename = fl.file_ref
        AND fl.severity != 'N/A';
        """

INSERT_FILE_RECORD = """INSERT INTO filename VALUES(:path,:filename,:status,:n_elements)"""
INSERT_FIELD_RECORD = (
    """INSERT INTO fields VALUES(:file_ref,:name,:value,:capitalization_score,:length_score,:value_score,:severity)"""
)


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
        dat = self.conn.execute("SELECT filename, status from filename").fetchall()
        # Parse numbers
        num_files = len(dat)
        num_pass = sum([1 for d in dat if d[1] == "pass"])
        num_fail = sum([1 for d in dat if d[1] == "fail"])
        # Write summary message
        summary_message = "Output summary:\n    "
        summary_message += f"Files Checked: {num_files}\n    "
        summary_message += f"Files Passed: {num_pass}\n    "
        summary_message += f"Files Failed: {num_fail}\n    "
        # All files passed
        if num_pass == num_files:
            summary_message += "All files passed! If any fields were marked with a score of 'review' (e.g. with a severity of 'unrecognized'), please consult with your MAST staff contact. Unrecognized values are very often necessary and good, but require review."
        # Some files failed
        else:
            summary_message += f"See results file ({self.db_file}) for more information. Some files did not meet our criteria. Note: only fields with a score of 'fail' and a severity of 'fatal' contributed to this result."
            # Add more detail here later? - could break down by fields, etc.

        return summary_message
