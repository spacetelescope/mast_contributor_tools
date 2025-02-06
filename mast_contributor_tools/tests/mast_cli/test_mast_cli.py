"""
Tests for mast_contributor_tools/cli.py
"""

import logging
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from mast_contributor_tools.mast_cli import filenames_cli, logger, single_filename_cli


# ================
# Define some fixtures for easier testing
# ================
@pytest.fixture
def mock_checkfiles():
    with mock.patch("mast_contributor_tools.mast_cli.check_filenames") as mock_checkfiles:
        yield mock_checkfiles


@pytest.fixture
def mock_singlefile():
    with mock.patch("mast_contributor_tools.mast_cli.check_single_filename") as mock_singlefile:
        yield mock_singlefile


@pytest.fixture
def mock_filepaths():
    with mock.patch("mast_contributor_tools.mast_cli.get_file_paths") as mock_filepaths:
        mock_filepaths.return_value = [
            Path("fake-directory/file1.fits"),
            Path("fake-directory/file2.fits"),
            Path("fake-directory/file3.fits"),
        ]
        yield mock_filepaths


# ================
# Test CLI options
# ================


def test_filenames_cli_defaults(mock_checkfiles, mock_filepaths) -> None:
    """Test default options are working as expected for the filename checker CLI"""
    # Invoke CLI
    runner = CliRunner()
    output = runner.invoke(filenames_cli, ["my-hlsp"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert logging level is correct
    assert logger.level == logging.getLevelNamesMapping()["INFO"]
    # Assert get_file_paths called with right arguments
    mock_filepaths.assert_called_with(".", search_pattern="*.*", exclude_pattern="", max_n=None)
    # Assert check_filenames was called with right arguments
    mock_checkfiles.assert_called_with("my-hlsp", mock_filepaths(), dbFile="results_my-hlsp.db")


def test_filenames_cli_logging(mock_checkfiles, mock_filepaths, mock_singlefile) -> None:
    """Test that the logging flags are working as expected for the filename checker CLI"""
    # Check logging/verbose flag for directory checking
    runner = CliRunner()
    output = runner.invoke(filenames_cli, ["my-hlsp", "-v"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert logging level is correct
    assert logger.level == logging.getLevelNamesMapping()["DEBUG"]

    # reset
    logger.level == logging.getLevelNamesMapping()["INFO"]
    # Check logging/verbose flag the single file option
    runner = CliRunner()
    output = runner.invoke(single_filename_cli, ["hlsp_my-hlsp_readme.txt", "-v"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert logging level is correct
    assert logger.level == logging.getLevelNamesMapping()["DEBUG"]


def test_filenames_cli_fileparams(mock_checkfiles, mock_singlefile, mock_filepaths) -> None:
    """Test different flags are working as expected for the filename checker CLI"""
    # Invoke CLI
    runner = CliRunner()
    output = runner.invoke(filenames_cli, ["my-hlsp", "--pattern=*.fits", "--exclude=*.png", "--max_n=2"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert get_file_paths called with right arguments
    mock_filepaths.assert_called_with(".", search_pattern="*.fits", exclude_pattern="*.png", max_n="2")
    # Assert check_filenames was called with right arguments
    mock_checkfiles.assert_called_with("my-hlsp", mock_filepaths(), dbFile="results_my-hlsp.db")
    # Assert check_single_filename was not called
    mock_singlefile.assert_not_called()


def test_filenames_cli_singlefile(mock_checkfiles, mock_singlefile, mock_filepaths) -> None:
    """Test different flags are working as expected for the single filename checker CLI"""
    # Test single file
    # equivalent to command "mct check_filename hlsp_my-hlsp_readme.txt"
    test_files = ["hlsp_my-hlsp_readme.txt"]
    # Invoke CLI for one argument
    runner = CliRunner()
    output = runner.invoke(single_filename_cli, test_files)
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert get_file_paths not called
    mock_filepaths.assert_not_called()
    # Assert check_filenames not called
    mock_checkfiles.assert_not_called()
    # Assert check_single_filename was called
    mock_singlefile.assert_called_with(test_files[0])


def test_filenames_cli_multfiles(mock_singlefile) -> None:
    # Test multiple file names
    # equivalent to command "mct check_filename file1.fits file2.fits ..."
    test_files = [
        "hlsp_my-hlsp_hst_wfc3_f160w_galaxy1_v1_spec.fits",
        "hlsp_my-hlsp_hst_wfc3_f160w_galaxy2_v1_spec.fits",
        "hlsp_my-hlsp_hst_wfc3_f160w_galaxy3_v1_spec.fits",
    ]
    runner = CliRunner()
    output = runner.invoke(single_filename_cli, test_files)
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert it checked all files
    assert mock_singlefile.call_count == len(test_files)
