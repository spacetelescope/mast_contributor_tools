"""
Tests for mast_contributor_tools/filename_check/fc_db.py

Each test recieves four scores: [capitalization, length, value, severity]:
- "Captalization" checks the capitilzation rules for this field, generally
required to be lowercase
- "Length" checks the character length, with the upper limit set for each field,
for example, the "HLSP name" must be less than 20 characters.
- "Value" checks the value of the field for additional rules; for example, the
target name is allowed to include some special characters, and the instrument must
be valid for the telescope name.
- "Severity" is the overall score, combining these three tests. Generally "N/A" if
the filename passes validation, "fatal" if it fails, or "unrecognized" for non-fatal
warnings.
"""

import os
from unittest import mock

import pytest

from mast_contributor_tools.filename_check.fc_db import Hlsp_SQLiteDb

TEST_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_file.db")


# Test init functions for Hlsp_SQLiteDb
@mock.patch("sqlite3.connect")
def test_Hlsp_SQLiteDb_create(mock_connection) -> None:
    """Test that the Hlsp_SQLiteDb class creates a db"""
    test_db = Hlsp_SQLiteDb(TEST_DB_FILE)

    # Assert attribtues were set
    assert test_db.db_file == TEST_DB_FILE

    # Assert DB is created
    test_db.create_db()
    mock_connection.assert_called_once()
    assert test_db.conn == mock_connection()
    test_db.close_db()


# Test expected columns in DB
@pytest.mark.parametrize(
    "table_name, expected_column",
    [
        ("filename", "path"),
        ("filename", "filename"),
        ("filename", "status"),
        ("fields", "file_ref"),
        ("fields", "name"),
        ("fields", "value"),
        ("fields", "capitalization_score"),
        ("fields", "length_score"),
        ("fields", "value_score"),
        ("fields", "severity"),
    ],
)
def test_Hlsp_SQLiteDb_Columns(table_name: str, expected_column: str) -> None:
    """Test that the sqlite DB has the expected tables and columns"""
    test_db = Hlsp_SQLiteDb(TEST_DB_FILE)
    test_db.create_db()

    # Assert each column can be queried
    test_query = f"SELECT {expected_column} from {table_name}"
    results = test_db.conn.execute(f"{test_query}").fetchall()
    # columns should exist, but not have anything in them yet
    assert len(results) == 0
    test_db.close_db()


# Test file record can be inserted successfully
@pytest.mark.parametrize(
    "file_record",
    [
        (".", "hlsp_fake_file.fits", "pass", int(9)),
        (".", "hlsp_fake_file2.fits", "pass", int(9)),
        ("subdir", "hlsp_fake_file3.fits", "pass", int(9)),
    ],
)
def test_add_filename(file_record) -> None:
    """Test file record can be inserted successfully with add_filename()"""
    test_db = Hlsp_SQLiteDb(TEST_DB_FILE)
    test_db.create_db()
    test_db.add_filename(
        {
            "path": file_record[0],
            "filename": file_record[1],
            "status": file_record[2],
            "n_elements": file_record[3],
        }
    )
    # Assert each column can be queried
    test_query = "SELECT * from filename"
    results = test_db.conn.execute(f"{test_query}").fetchall()
    # Assert record was inserted correctly
    assert file_record in results
    test_db.close_db()


# Test field record can be inserted successfully
@pytest.mark.parametrize(
    "field_record",
    [
        ("hlsp_fake_file.fits", "hlsp_str", "hlsp", "pass", "pass", "pass", "N/A"),
        ("hlsp_fake_file.fits", "hlsp_name", "fake", "pass", "fail", "pass", "fatal"),
        (
            "hlsp_fake_file.fits",
            "mission",
            "file",
            "pass",
            "pass",
            "review",
            "unrecognized",
        ),
    ],
)
def test_add_fields(field_record) -> None:
    """Test field record can be inserted successfully with add_fields()"""
    test_db = Hlsp_SQLiteDb(TEST_DB_FILE)
    test_db.create_db()
    test_db.add_fields(
        [
            {
                "file_ref": field_record[0],
                "name": field_record[1],
                "value": field_record[2],
                "capitalization_score": field_record[3],
                "length_score": field_record[4],
                "value_score": field_record[5],
                "severity": field_record[6],
            }
        ]
    )
    # Assert each column can be queried
    test_query = "SELECT * from fields"
    results = test_db.conn.execute(f"{test_query}").fetchall()
    # Assert record was inserted correctly
    assert field_record in results
    test_db.close_db()


# Test field record check statements are failing when they are supposed to
@pytest.mark.parametrize(
    "field_record",
    [
        ("hlsp_fake_file.fits", "hlsp_str", "BAD-VALUE", "pass", "pass", "N/A"),
        ("hlsp_fake_file.fits", "mission", "pass", True, "pass", "N/A"),
        ("hlsp_fake_file.fits", "target", "pass", "pass", "pass", 1),
    ],
)
def test_add_fields_xfail(field_record) -> None:
    """Test that the sqlite DB insertion fails when a value is wrong"""
    test_db = Hlsp_SQLiteDb(TEST_DB_FILE)
    test_db.create_db()
    try:
        test_db.add_fields(
            [
                {
                    "file_ref": field_record[0],
                    "name": field_record[1],
                    "value": field_record[0].split("_")[1],
                    "capitalization_score": field_record[2],
                    "length_score": field_record[3],
                    "value_score": field_record[4],
                    "severity": field_record[5],
                }
            ]
        )
    except Exception as e:
        # Make sure error was thrown
        assert "CHECK constraint failed" in e.__str__()

    # Make sure entry was not inserted
    test_query = "SELECT * from fields"
    results = test_db.conn.execute(f"{test_query}").fetchall()
    assert field_record not in results
    test_db.close_db()


# Remove the test.db file once the tests are complete
def test_remove_test_db_file():
    """Delete the test_file.db now that the tests are complete"""
    os.remove(TEST_DB_FILE)
    assert not os.path.exists(TEST_DB_FILE)
