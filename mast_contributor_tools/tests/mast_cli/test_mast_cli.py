"""
Tests for mast_contributor_tools/cli.py
"""

import logging
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from mast_contributor_tools.mast_cli import filenames_cli, logger


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


def test_filenames_cli_defaults(mock_checkfiles, mock_singlefile, mock_filepaths) -> None:
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
    # Assert check_single_filename was not called
    mock_singlefile.assert_not_called()


def test_filenames_cli_verbose(mock_checkfiles, mock_singlefile, mock_filepaths) -> None:
    """Test different flags are working as expected for the filename checker CLI"""
    # Invoke CLI
    runner = CliRunner()
    output = runner.invoke(filenames_cli, ["my-hlsp", "-v"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert logging level is correct
    assert logger.level == logging.getLevelNamesMapping()["DEBUG"]


def test_filenames_cli_singlefile(mock_checkfiles, mock_singlefile, mock_filepaths) -> None:
    """Test different flags are working as expected for the filename checker CLI"""
    # Invoke CLI
    runner = CliRunner()
    output = runner.invoke(filenames_cli, ["my-hlsp", "--filename=hlsp_my-hlsp_readme.txt"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert get_file_paths not called
    mock_filepaths.assert_not_called()
    # Assert check_filenames not called
    mock_checkfiles.assert_not_called()
    # Assert check_single_filename was called
    mock_singlefile.assert_called_with("hlsp_my-hlsp_readme.txt", "my-hlsp")


def test_filenames_cli_fileparams(mock_checkfiles, mock_singlefile, mock_filepaths) -> None:
    """Test different flags are working as expected for the filename checker CLI"""
    # Invoke CLI
    runner = CliRunner()
    output = runner.invoke(filenames_cli, ["my-hlsp", "--pattern=*.fits", "--exclude=*.png", "--max_n=2"])
    # Assert it ran successfully
    assert output.exit_code == 0
    # Assert get_file_paths called with right arguments
    mock_filepaths.assert_called_with(".", search_pattern="*.fits", exclude_pattern="*.png", max_n=2)
    # Assert check_filenames was called with right arguments
    mock_checkfiles.assert_called_with("my-hlsp", mock_filepaths(), dbFile="results_my-hlsp.db")
    # Assert check_single_filename was not called
    mock_singlefile.assert_not_called()
