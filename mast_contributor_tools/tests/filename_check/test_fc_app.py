"""
Tests for mast_contributor_tools/filename_check/fc_app.py
"""

from pathlib import Path
from unittest import mock

import pytest

from mast_contributor_tools.filename_check.fc_app import (
    check_filenames,
    check_single_filename,
    get_file_paths,
    identify_collection_type,
)


def fake_directory() -> list[Path]:
    """Mock directory with some fake filenames for testing purposes"""
    file_list = [
        Path("fake-directory/file1.fits"),
        Path("fake-directory/file2.fits"),
        Path("fake-directory/file3.fits"),
    ]
    return file_list


@mock.patch("pathlib.Path.rglob")
@mock.patch("pathlib.Path.is_file")
def test_get_file_paths(mock_isfile, mock_rglob) -> None:
    """Test get_file_paths() function"""
    # Mock rglob to return the filelist in fake_directory
    mock_rglob.return_value = fake_directory()
    mock_isfile.return_value = True
    # Run function
    output = get_file_paths("fake-directory")
    # assert rglob was called
    mock_rglob.assert_called_once()
    # assert the filenames were returned (without the path)
    for fake_file in fake_directory():
        assert Path(fake_file.name) in output
    # Test the max_n argument performs as expected
    output = get_file_paths("fake-directory", max_n=2)
    assert len(output) == 2
    # Test that the search_pattern argument performs as expected
    output = get_file_paths("fake-directory", search_pattern="*1.fits")
    assert len(output) == 1
    # Test that the exclude_pattern argument performs as expected
    output = get_file_paths("fake-directory", exclude_pattern="*1.fits")
    assert len(output) == 2


@pytest.mark.parametrize(
    "test_filename, expected",
    [
        ("hlsp_my-hlsp_file.txt", "HLSP"),
        ("ccsp_my-hlsp_file.txt", "CCSP"),
        ("mccm_my-hlsp_file.txt", "MCCM"),
        # Defaults to HLSP when not recognized
        ("mast_my-hlsp_file.txt", "HLSP"),
    ],
)
def test_identify_collection_type(test_filename, expected) -> None:
    """Test that the identify_collection_type() function works correctly"""
    assert identify_collection_type(test_filename) == expected


@mock.patch("mast_contributor_tools.filename_check.fc_app.HlspFileName")
@mock.patch("mast_contributor_tools.filename_check.fc_app.Hlsp_SQLiteDb")
def test_check_filenames(mock_Hlsp_SQLiteDb, mock_HlspFileName) -> None:
    """Test that the check_filenames() function calls the right classes"""
    # Run function
    check_filenames("hlsp-name", file_list=fake_directory(), dbFile="test_file.db")
    # Assert expected calls were made
    # assert mock_Hlsp_SQLiteDb object was made
    mock_Hlsp_SQLiteDb.assert_called_once()
    # Assert HlspFileName was called once for each file
    assert mock_HlspFileName.call_count == len(fake_directory())


# Test the the right filename class is called for HLSPs, CCSPs, and MCCMs
@pytest.mark.parametrize(
    "test_filename, expected",
    [
        ("hlsp_my-hlsp_file.txt", "HlspFileName"),
        ("ccsp_my-hlsp_file.txt", "CCSPFileName"),
        ("mccm_my-hlsp_file.txt", "MCCMFileName"),
        # Defaults to HLSP when not recognized
        ("mast_my-hlsp_file.txt", "HlspFileName"),
    ],
)
def test_check_single_filename(test_filename, expected) -> None:
    """Test that the test_check_single_filename() function calls the right classes"""
    with mock.patch(f"mast_contributor_tools.filename_check.fc_app.{expected}") as expected_class:
        # Run function
        check_single_filename(test_filename)
        # Assert correct class was called
        expected_class.assert_called_once()
