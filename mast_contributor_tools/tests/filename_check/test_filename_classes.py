"""
Tests for mast_contributor_tools/filename_check/filename_classes.py

Each test recieves four scores: [capitalization, length, value, field_verdict]:
- "Captalization" checks the capitilzation rules for this field, generally
required to be lowercase
- "Length" checks the character length, with the upper limit set for each field,
for example, the "HLSP name" must be less than 20 characters.
- "Format" checks the overall format of the field against a regex pattern. For example, the
target name is allowed to include some special characters like '+' while other fields do not
- "Value" checks the value of the field for additional rules; for example,
the instrument must be valid for the telescope name.
- "Field Verdict" is the overall score, either "PASS", "NEEDS REVIEW", or "FAIL",
 decided as the lowest score from these four tests.
"""

from pathlib import Path
from unittest import mock

import pytest

from mast_contributor_tools.filename_check.filename_classes import (
    FILENAME_REGEX,
    CCSPFileName,
    HlspFileName,
    MCCMFileName,
    get_filename_class,
    identify_collection_type,
)


# ==============================================
# Helper Functions for evaluating scores
# =============================================
def assert_scores_match(recieved_score: dict[str, str], expected_score: list[str]) -> None:
    """
    Helper function to compares the recieved score to the
    expected score to make sure that they match for a given field

    Parameters:
    ------------
    recieved_score: dict[str,str]
        dictionary of recieved score
    expected_score: list[str]
        list of expected score from test input

    """
    # Convert expected_score list into dict
    expected_score_dict = {
        "capitalization_score": expected_score[0],
        "length_score": expected_score[1],
        "format_score": expected_score[2],
        "value_score": expected_score[3],
        "field_verdict": expected_score[4],
    }

    # Test each value individually
    for test_key in list(expected_score_dict.keys()):
        test_name = recieved_score["name"]
        eval_msg = (
            f"Error in field '{test_name}.{test_key}':"
            + f" recieved '{recieved_score[test_key]}', "
            + f" expected '{expected_score_dict[test_key]}' does not match"
        )
        # Assert scores match
        assert recieved_score[test_key] == expected_score_dict[test_key], eval_msg


# ==============================================
# HLSP Filename Tests
# ==============================================
# Tests for file names that are not expected to raise errors, buy may pass or fail
@pytest.mark.parametrize(
    "test_filename, hlsp_name, expected_evaluation",
    [
        # Expected to Pass
        # Fake Example
        (
            "hlsp_fake-hlsp_hst_wfc3_vega_f160w_v1_img.fits",
            "fake-hlsp",
            "PASS",
        ),
        # Real examples
        (
            "hlsp_phangs-jwst_jwst_nircam_ngc1385_f335m_v1p0p1_img.fits",
            "phangs-jwst",
            "PASS",
        ),
        (
            "hlsp_hff-deepspace_hst_acs-wfc3_all_multi_v1_readme.txt",
            "hff-deepspace",
            "PASS",
        ),
        (
            "hlsp_cos-gal_hst_cos_j152447.75-p041919.8_g130m_v1_fullspec.fits",
            "cos-gal",
            "NEEDS REVIEW",
        ),
        (
            "hlsp_tica_tess_ffi_s0084-o2-01023889-cam1-ccd1_tess_v01_img.fits",
            "tica",
            "PASS",
        ),
        (
            "hlsp_judo_hst_wfc3_jupiter-20120919_f275w_v1.0_npole-globalmap.fits",
            "judo",
            "NEEDS REVIEW",
        ),
        (  # example using multi
            "hlsp_my-hlsp_multi_multi_vega_multi_v1_spec.fits",
            "my-hlsp",
            "PASS",
        ),
        (  # example using multi in only some fields
            "hlsp_my-hlsp_hst_multi_vega_multi_v1_spec.fits",
            "my-hlsp",
            "PASS",
        ),
        (  # example readme with only 4 fields
            "hlsp_my-hlsp_readme.txt",
            "my-hlsp",
            "PASS",
        ),
        (  # example catalog
            "hlsp_my-hlsp_alltargets_v1_cat.fits",
            "my-hlsp",
            "PASS",
        ),
        (  # example with + sign
            "hlsp_specs_hst_acs_j012910+145935_f250w_v1.0_img.fits",
            "specs",
            "PASS",
        ),
        # Expected to Fail
        (
            "hlsp_fake-hlsp_hst_wfc3_VEGA_f160w_v1_img.fits",
            "fake-hlsp",
            "FAIL",
        ),
        (
            "hlsp_fake-hlsp_hst_wfc3_vega_f160w_v1_img.fits",
            "wrong-name",
            "FAIL",
        ),
        (
            "hlsp_my-hlsp_hst_wfc3_vega_f160w_more_than_nine_fields.fits",  # too many fields
            "my-hlsp",
            "FAIL",
        ),
    ],
)
def test_HlspFileName(
    test_filename: str,
    hlsp_name: str,
    expected_evaluation: list[str],
) -> None:
    """Tests for file names that are expected to run (no errors), but still pass/fail accordingly"""
    # Make sure filename matches the regex
    assert FILENAME_REGEX.match(test_filename), f"Filename {test_filename} does not match regex {FILENAME_REGEX}"
    # Test the filename
    hfn = HlspFileName(Path(test_filename), hlsp_name)
    hfn.partition()
    hfn.create_fields()
    elements = hfn.evaluate_fields()
    received_evaluation = hfn.evaluate_filename()["final_verdict"]
    assert received_evaluation == expected_evaluation, (
        f"{test_filename} recieved score {received_evaluation}, expected {expected_evaluation}, {elements}"
    )


# Tests for file names that are expected to raise errors
@pytest.mark.parametrize(
    "test_filename, hlsp_name, expected_error",
    [
        ("fakefile.fits", "fakehlsp", ValueError),
        ("fakefile.fits", "invalid_name", ValueError),  # invalid hlsp name
        ("two_fields.fits", "fakehlsp", ValueError),  # only two fields
    ],
)
def test_HlspFileName_errors(
    test_filename: str,
    hlsp_name: str,
    expected_error,
) -> None:
    """Tests for file names that are expected to raise errors"""
    try:
        hfn = HlspFileName(Path(test_filename), hlsp_name)
        hfn.partition()
        hfn.create_fields()
    except Exception as e:
        # Assert correct error was raised
        assert e.__class__ == expected_error, f"Wrong error raised: Expected {expected_error}, raised {e.__class__}"
    else:
        # if it made it this far, no errors were raised - that's a problem for this test
        assert False, f"No error was raised when evaluating filename '{test_filename}'"


# Test that all field classes are called in HlspFileName (no fields are skipped)
# Listed in backwards order because the last one is passed to function first
# For standard 9-field filename
@mock.patch("mast_contributor_tools.filename_check.filename_classes.ExtensionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.ProductField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.VersionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.FilterField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.TargetField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.InstrumentField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.MissionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.CollectionNameField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.PrefixField")
def test_field_9parts_called_in_HlspFileName(*mock_fields) -> None:
    """Test that all field classes are called in HlspFileName"""
    test_filename = "hlsp_fake-hlsp_hst_wfc3_vega_f160w_v1_img.fits"
    # Split file name into parts to test
    parts = test_filename.split("_")
    last = parts[-1].split(".", 1)
    parts = parts[:-1] + last

    # Initiate File Name Validation
    hfn = HlspFileName(Path(test_filename), "fake-hlsp")
    hfn.partition()
    hfn.create_fields()
    # Check to make sure every field was checked
    for i, mock_field in enumerate(mock_fields):
        # Assert field was checked
        (
            mock_field.assert_called_once(),
            f"Field {mock_field._extract_mock_name()} was not called",
        )
        # Assert correct value was used as arguments
        if i == 0:
            mock_field.assert_called_with(parts[i], "hlsp", i)  # two args for PrefixField
        elif i == 1:
            mock_field.assert_called_with(parts[i], parts[i], i)  # two args for HlspName
        else:
            mock_field.assert_called_with(parts[i], i)  # one for everything else


# Test that all field classes are called in HlspFileName (no fields are skipped)
# Listed in backwards order because the last one is passed to function first
# For shorter 5-field filename with Generic Fields
@mock.patch("mast_contributor_tools.filename_check.filename_classes.ExtensionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.GenericField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.CollectionNameField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.PrefixField")
def test_field_5parts_called_in_HlspFileName(*mock_fields) -> None:
    """Test that all field classes are called in HlspFileName"""
    test_filename = "hlsp_fake-hlsp_alltargets_v1_cat.fits"
    # Split file name into parts to test
    parts = test_filename.split("_")
    last = parts[-1].split(".", 1)
    parts = parts[:-1] + last

    # Initiate File Name Validation
    hfn = HlspFileName(Path(test_filename), "fake-hlsp")
    hfn.partition()
    hfn.create_fields()
    # Check to make sure every field was checked
    for i, mock_field in enumerate(mock_fields):
        # Assert field was checked
        (
            mock_field.assert_called_once(),
            f"Field {mock_field._extract_mock_name()} was not called",
        )


# ==============================================
# CCSP Filename Tests
# ==============================================
# Tests for file names that are not expected to raise errors, buy may pass or fail
@pytest.mark.parametrize(
    "test_filename, ccsp_name, expected_evaluation",
    [
        # Expected to Pass
        (  # image
            "ccsp_sn_wfi_crab-nebula_f062_v1.0_img.fits",
            "sn",
            "PASS",
        ),
        (  # asdf file
            "ccsp_rapid_wfi_mwc560-r003_f062_v1_img.asdf",
            "rapid",
            "PASS",
        ),
        (  # thumbnail example
            "ccsp_sn_wfi_crab-nebula_f062_v1.0_preview_thumb.jpeg",
            "sn",
            "PASS",
        ),
        # Expected to fail
        (  # an HLSP filename
            "hlsp_fake-hlsp_hst_wfc3_vega_f160w_v1_img.fits",
            "fake-hlsp",
            "FAIL",
        ),
        (  # too many fields
            "ccsp_sn_wfi_crab-nebula_f062_v1.0_img_img.fits",
            "sn",
            "FAIL",
        ),
        (  # caps
            "ccsp_SN_wfi_crab-nebula_f062_v1.0_img_img.fits",
            "sn",
            "FAIL",
        ),
    ],
)
def test_CCSPFileName(
    test_filename: str,
    ccsp_name: str,
    expected_evaluation: list[str],
) -> None:
    """Tests for file names that are expected to run (no errors), but still pass/fail accordingly"""
    # Make sure filename matches the regex
    assert FILENAME_REGEX.match(test_filename), f"Filename {test_filename} does not match regex {FILENAME_REGEX}"
    # Test the filename
    hfn = CCSPFileName(Path(test_filename), ccsp_name)
    hfn.partition()
    hfn.create_fields()
    elements = hfn.evaluate_fields()
    received_evaluation = hfn.evaluate_filename()["final_verdict"]
    assert received_evaluation == expected_evaluation, (
        f"{test_filename} recieved score {received_evaluation}, expected {expected_evaluation}, {elements}"
    )


# Tests for file names that are expected to raise errors
@pytest.mark.parametrize(
    "test_filename, ccsp_name, expected_error",
    [
        (  # too few fields
            "ccsp_sn_wfi_crab-nebula_f062_img.fits",
            "sn",
            ValueError,
        ),
    ],
)
def test_CCSPFileName_errors(
    test_filename: str,
    ccsp_name: str,
    expected_error,
) -> None:
    """Tests for file names that are expected to raise errors"""
    try:
        hfn = CCSPFileName(Path(test_filename), ccsp_name)
        hfn.partition()
        hfn.create_fields()
    except Exception as e:
        # Assert correct error was raised
        assert e.__class__ == expected_error, f"Wrong error raised: Expected {expected_error}, raised {e.__class__}"
    else:
        # if it made it this far, no errors were raised - that's a problem for this test
        assert False, f"No error was raised when evaluating filename '{test_filename}'"


# Test that all field classes are called in CCSPFileName
# Listed in backwards order because the last one is passed to function first
@mock.patch("mast_contributor_tools.filename_check.filename_classes.ExtensionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.ProductField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.VersionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.FilterField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.TargetField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.InstrumentField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.CollectionNameField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.PrefixField")
def test_field_CCSPFileName_8fields(*mock_fields) -> None:
    """Test that all field classes are called in CCSPFileName"""
    # For standard 8-field filename
    test_filename = "ccsp_sn_wfi_crab-nebula_f062_v1.0_img.fits"
    # Split file name into parts to test
    parts = test_filename.split("_")
    last = parts[-1].split(".", 1)
    parts = parts[:-1] + last

    # Initiate File Name Validation
    hfn = CCSPFileName(Path(test_filename), "sn")
    hfn.partition()
    hfn.create_fields()
    # Check to make sure every field was checked
    for i, mock_field in enumerate(mock_fields):
        # Assert field was checked
        (
            mock_field.assert_called_once(),
            f"Field {mock_field._extract_mock_name()} was not called",
        )
        # Assert correct value was used as arguments
        if i == 0:
            mock_field.assert_called_with(parts[i], "ccsp", i)  # two args for PrefixField
        elif i == 1:
            mock_field.assert_called_with(parts[i], parts[i], i)  # two args for CCSPName
        else:
            mock_field.assert_called_with(parts[i], i)  # one for everything else


@mock.patch("mast_contributor_tools.filename_check.filename_classes.ExtensionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.StringLiteralField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.ProductField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.VersionField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.FilterField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.TargetField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.InstrumentField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.CollectionNameField")
@mock.patch("mast_contributor_tools.filename_check.filename_classes.PrefixField")
def test_field_CCSPFileName_9fields(*mock_fields) -> None:
    """Test that all field classes are called in CCSPFileName"""
    # For standard 8-field filename
    test_filename = "ccsp_sn_wfi_crab-nebula_f062_v1.0_preview_thumb.jpeg"
    # Split file name into parts to test
    parts = test_filename.split("_")
    last = parts[-1].split(".", 1)
    parts = parts[:-1] + last

    # Initiate File Name Validation
    hfn = CCSPFileName(Path(test_filename), "sn")
    hfn.partition()
    hfn.create_fields()
    # Check to make sure every field was checked
    for i, mock_field in enumerate(mock_fields):
        # Assert field was checked
        (
            mock_field.assert_called_once(),
            f"Field {mock_field._extract_mock_name()} was not called",
        )
        # Assert correct value was used as arguments
        if i == 0:
            mock_field.assert_called_with(parts[i], "ccsp", i)  # two args for PrefixField
        elif i == 1:
            mock_field.assert_called_with(parts[i], parts[i], i)  # two args for CCSPName
        elif i == 7:
            mock_field.assert_called_with(parts[i], "thumb", i)  # literal "thumb" field
        else:
            mock_field.assert_called_with(parts[i], i)  # one for everything else


# ==============================================
# MCCM Filename Tests
# ==============================================
@pytest.mark.parametrize(
    "test_filename, hlsp_name, expected_evaluation",
    [  # Expected to Pass
        (  # preview example
            "mccm_fake-mission_wfc3_m31_f062_v1.0_preview.jpeg",
            "fake-mission",
            "PASS",
        ),
        (  # thumbnail example
            "mccm_fake-mission_wfc3_m31_f062_v1.0_preview_thumb.jpeg",
            "fake-mission",
            "PASS",
        ),
        # Needs Review Examples
        (  # real example
            "mccm_fims-spear_spear-ap100_vela_long-he-ii_v1.0_img.fits",
            "fims-spear",
            "NEEDS REVIEW",
        ),
        (  # unrecognized filter name
            "mccm_fake-mission_instr_m31_filtname_v1.0_img.fits",
            "fake-mission",
            "NEEDS REVIEW",
        ),
        # Expected to fail
        (  # an HLSP filename
            "hlsp_fake-hlsp_hst_wfc3_vega_f160w_v1_img.fits",
            "fake-hlsp",
            "FAIL",
        ),
    ],
)
def test_MCCMFileName(
    test_filename: str,
    hlsp_name: str,
    expected_evaluation: list[str],
) -> None:
    """Tests for file names that are expected to run (no errors), but still pass/fail accordingly"""
    # Make sure filename matches the regex
    assert FILENAME_REGEX.match(test_filename), f"Filename {test_filename} does not match regex {FILENAME_REGEX}"
    # Test the filename
    hfn = MCCMFileName(Path(test_filename), hlsp_name)
    hfn.partition()
    hfn.create_fields()
    elements = hfn.evaluate_fields()
    received_evaluation = hfn.evaluate_filename()["final_verdict"]
    assert received_evaluation == expected_evaluation, (
        f"{test_filename} recieved score {received_evaluation}, expected {expected_evaluation}, {elements}"
    )


# ==============================================
# Misc Other Tests
# ==============================================


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
def test_get_filename_class(test_filename, expected):
    """
    Tests get_filename_class returns the correct class
    """
    with mock.patch(f"mast_contributor_tools.filename_check.filename_classes.{expected}") as expected_class:
        # Run function
        result = get_filename_class(test_filename, "my-collection")
        # Assert correct class was called
        expected_class.assert_called_once()
