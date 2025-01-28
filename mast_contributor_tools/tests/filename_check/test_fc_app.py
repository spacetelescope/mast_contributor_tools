"""
Tests for mast_contributor_tools/filename_check/fc_app.py
"""

from pathlib import Path
from unittest import mock

from mast_contributor_tools.filename_check.fc_app import check_filenames, get_file_paths


def fake_directory() -> list[Path]:
    """Mock directory with some fake filenames for testing purposes"""
    file_list = [
        Path("fake-directory/file1.fits"),
        Path("fake-directory/file2.fits"),
        Path("fake-directory/file3.fits"),
    ]
    return file_list


@mock.patch("pathlib.Path.rglob")
def test_get_file_paths(mock_rglob) -> None:
    """Test get_file_paths() function"""
    # Mock rglob to return the filelist in fake_directory
    mock_rglob.return_value = fake_directory()
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
