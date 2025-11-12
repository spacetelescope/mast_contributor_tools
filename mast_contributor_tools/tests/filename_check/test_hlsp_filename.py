"""
Tests for mast_contributor_tools/filename_check/hlsp_filename.py

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

from mast_contributor_tools.filename_check.hlsp_filename import (
    EXTENSION_TYPES,
    FILENAME_REGEX,
    FILTERS,
    INSTRUMENTS,
    MISSIONS,
    SEMANTIC_TYPES,
    ExtensionField,
    FilterField,
    GenericField,
    HlspField,
    HlspFileName,
    HlspNameField,
    InstrumentField,
    MissionField,
    ProductField,
    TargetField,
    VersionField,
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
# Tests for each field of the file name
# =============================================
# HlspField
@pytest.mark.parametrize(
    "test_value, expected_score",
    # expected_score is: [capitalization, length, format, value, field_verdict]
    [
        # Expected to Pass
        ("hlsp", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to Fail = anything else
        ("HLSP", ["fail", "pass", "pass", "pass", "FAIL"]),  # no caps
        ("hst", ["pass", "pass", "pass", "fail", "FAIL"]),  # not "hlsp"
        ("banana", ["pass", "fail", "pass", "fail", "FAIL"]),  # not "hlsp"
        ("123-hlsp", ["pass", "fail", "pass", "fail", "FAIL"]),  # not "hlsp"
        ("", ["fail", "fail", "pass", "fail", "FAIL"]),  # empty string
        ("h.lp", ["pass", "pass", "fail", "fail", "FAIL"]),  # special characters
        ("hlsp!", ["pass", "fail", "fail", "fail", "FAIL"]),  # special characters
    ],
)
def test_HlspField(
    test_value: str,
    expected_score: list[str],
) -> None:
    """Test HlspField values"""
    # Evaluate Test Value
    field = HlspField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# HlspNameField
@pytest.mark.parametrize(
    "test_value, ref_name, expected_score",
    # expected_score is: [capitalization, length, format, value, field_verdict]
    [
        # Expected to Pass
        ("my-hlsp", "my-hlsp", ["pass", "pass", "pass", "pass", "PASS"]),
        ("tica", "tica", ["pass", "pass", "pass", "pass", "PASS"]),
        ("phangs-jwst", "phangs-jwst", ["pass", "pass", "pass", "pass", "PASS"]),
        # caps okay for ref_name, but not for field value
        ("my-hlsp", "MY-HLSP", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to Fail
        ("MY-HLSP", "my-hlsp", ["fail", "pass", "pass", "pass", "FAIL"]),  # caps
        ("wrong-name", "my-hlsp", ["pass", "pass", "pass", "fail", "FAIL"]),  # name mismatch
        # spaces, special characters
        ("my hlsp", "my hlsp", ["pass", "pass", "fail", "pass", "FAIL"]),
        ("my-hlsp!", "my-hlsp!", ["pass", "pass", "fail", "pass", "FAIL"]),
        ("my.hlsp", "my.hlsp", ["pass", "pass", "fail", "pass", "FAIL"]),
        ("2hlsp", "2-my-hlsp", ["pass", "pass", "fail", "fail", "FAIL"]),
        ("hlsp+hlsp", "hlsp+hlsp", ["pass", "pass", "fail", "pass", "FAIL"]),
        # current character limits <= 20 characters
        (
            "really-really-long-hlsp-name",
            "really-really-long-hlsp-name",
            ["pass", "fail", "pass", "pass", "FAIL"],
        ),
        ("", "", ["fail", "fail", "fail", "pass", "FAIL"]),  # empty string
    ],
)
def test_HlspNameField(
    test_value: str,
    ref_name: str,
    expected_score: list[str],
) -> None:
    """Test HlspNameField values"""
    # Evaluate Test Value
    field = HlspNameField(test_value, ref_name=ref_name)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# MissionField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("hst", ["pass", "pass", "pass", "pass", "PASS"]),
        ("jwst", ["pass", "pass", "pass", "pass", "PASS"]),
        ("hst-jwst", ["pass", "pass", "pass", "pass", "PASS"]),
        ("sdss", ["pass", "pass", "pass", "pass", "PASS"]),
        ("multi", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to give warnings
        ("roman", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
        ("fake-mission", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
        # Expected to Fail
        ("hst_jwst", ["pass", "pass", "fail", "needs review", "FAIL"]),
        ("hst.jwst", ["pass", "pass", "fail", "needs review", "FAIL"]),
        ("HST", ["fail", "pass", "pass", "pass", "FAIL"]),
        ("ReallyLongMissionName", ["fail", "fail", "pass", "needs review", "FAIL"]),
        ("", ["fail", "fail", "pass", "needs review", "FAIL"]),  # empty string
    ],
)
def test_MissionField(
    test_value: str,
    expected_score: list[str],
) -> None:
    """Test MissionField values"""
    # Evaluate Test Value
    field = MissionField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# InstrumentField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("nirspec", ["pass", "pass", "pass", "pass", "PASS"]),
        ("multi", ["pass", "pass", "pass", "pass", "PASS"]),
        ("nircam-nirspec", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected wanrings
        ("mystery-camera", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
        # Expected to Fail
        ("STIS", ["fail", "pass", "pass", "pass", "FAIL"]),
        ("my.instrument", ["pass", "pass", "fail", "needs review", "FAIL"]),
        ("", ["fail", "fail", "pass", "needs review", "FAIL"]),  # empty string
    ],
)
def test_InstrumentField(
    test_value: str,
    expected_score: list[str],
) -> None:
    """Test InstrumentField values"""
    # Evaluate Test Value
    field = InstrumentField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# TargetField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("vega", ["pass", "pass", "pass", "pass", "PASS"]),
        ("m31", ["pass", "pass", "pass", "pass", "PASS"]),
        ("multi", ["pass", "pass", "pass", "pass", "PASS"]),
        ("ngc1385", ["pass", "pass", "pass", "pass", "PASS"]),
        ("obj-123", ["pass", "pass", "pass", "pass", "PASS"]),
        ("2m04215943+1932063", ["pass", "pass", "pass", "pass", "PASS"]),
        ("j152447.75-p041919.8", ["pass", "pass", "pass", "pass", "PASS"]),
        ("2mass-j09512393-p3542490", ["pass", "pass", "pass", "pass", "PASS"]),
        ("sdssj085259.22-p031320.6", ["pass", "pass", "pass", "pass", "PASS"]),
        ("1saxj1032.3-p5051", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to Fail
        ("M31", ["fail", "pass", "pass", "pass", "FAIL"]),  # caps
        ("2M04215943+1932063", ["fail", "pass", "pass", "pass", "FAIL"]),
        ("", ["fail", "fail", "fail", "fail", "FAIL"]),  # empty string
        ("123+456", ["fail", "pass", "pass", "pass", "FAIL"]),  # all digits
    ],
)
def test_TargetField(test_value: str, expected_score: list[str]) -> None:
    """Test TargetField values"""
    # Evaluate Test Value
    field = TargetField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# FilterField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("f435w", ["pass", "pass", "pass", "pass", "PASS"]),
        ("u", ["pass", "pass", "pass", "pass", "PASS"]),
        ("multi", ["pass", "pass", "pass", "pass", "PASS"]),
        ("g102-f435w", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to give warning
        ("fakefilter", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),  # not in list
        # Expected to Fail
        ("F435W", ["fail", "pass", "pass", "pass", "FAIL"]),  # caps
        ("", ["fail", "fail", "pass", "needs review", "FAIL"]),  # empty string
    ],
)
def test_FilterField(test_value: str, expected_score: list[str]) -> None:
    """Test FilterField values"""
    # Evaluate Test Value
    field = FilterField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# VersionField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("v1", ["pass", "pass", "pass", "pass", "PASS"]),
        ("v2.3", ["pass", "pass", "pass", "pass", "PASS"]),
        ("v1.2.3", ["pass", "pass", "pass", "pass", "PASS"]),
        ("v12.34.56", ["pass", "pass", "pass", "pass", "PASS"]),
        ("v01", ["pass", "pass", "pass", "pass", "PASS"]),
        ("v1p0p1", ["pass", "pass", "pass", "pass", "PASS"]),  # "p" is allowed in place of "."
        # Expected to Fail
        ("dr1", ["pass", "pass", "fail", "fail", "FAIL"]),
        ("1.2.3", ["fail", "pass", "fail", "fail", "FAIL"]),  # does not start with v
        ("v1-1", ["pass", "pass", "fail", "fail", "FAIL"]),  # no hyphens
        ("v123.4", ["pass", "pass", "fail", "fail", "FAIL"]),  # too many digits before '.'
        ("v1.2.3.4", ["pass", "pass", "fail", "fail", "FAIL"]),  # too many periods
        ("V1", ["fail", "pass", "fail", "fail", "FAIL"]),  # caps
        ("v1.", ["pass", "pass", "fail", "fail", "FAIL"]),  # ends with period
        ("v1.a", ["pass", "pass", "fail", "fail", "FAIL"]),  # no letters allowed
        ("", ["fail", "fail", "fail", "fail", "FAIL"]),  # empty string
    ],
)
def test_VersionField(test_value: str, expected_score: list[str]) -> None:
    """Test VersionField values"""
    # Evaluate Test Value
    field = VersionField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# ProductField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("drz", ["pass", "pass", "pass", "pass", "PASS"]),
        ("lc", ["pass", "pass", "pass", "pass", "PASS"]),
        ("spec", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to give warning
        ("fake-suffix", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
        ("2dspec", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
        # Expected to Fail
        ("2DSPEC", ["fail", "pass", "pass", "needs review", "FAIL"]),
        ("", ["fail", "fail", "pass", "needs review", "FAIL"]),  # empty string
    ],
)
def test_ProductField(test_value: str, expected_score: list[str]) -> None:
    """Test ProductField values"""
    # Evaluate Test Value
    field = ProductField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# ExtensionField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("fits", ["pass", "pass", "pass", "pass", "PASS"]),
        ("pdf", ["pass", "pass", "pass", "pass", "PASS"]),
        ("png", ["pass", "pass", "pass", "pass", "PASS"]),
        ("dat", ["pass", "pass", "pass", "pass", "PASS"]),
        ("tar.gz", ["pass", "pass", "pass", "pass", "PASS"]),
        ("h5", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected Review
        ("blah", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
        # Expected to Fail
        ("JPG", ["fail", "pass", "pass", "pass", "FAIL"]),
        ("", ["fail", "fail", "pass", "needs review", "FAIL"]),  # empty string
    ],
)
def test_ExtensionField(test_value: str, expected_score: list[str]) -> None:
    """Test ExtensionField values"""
    # Evaluate Test Value
    field = ExtensionField(test_value)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# GenericField
@pytest.mark.parametrize(
    "test_value, expected_score",
    [
        # Expected to Pass
        ("anything", ["pass", "pass", "pass", "pass", "PASS"]),
        ("dashes-are-fine", ["pass", "pass", "pass", "pass", "PASS"]),
        ("multi", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to fail
        ("ANYTHING", ["fail", "pass", "pass", "pass", "FAIL"]),  # caps
        ("generic-field-name-is-too-long", ["pass", "fail", "pass", "pass", "FAIL"]),  # length
        ("pluses+are+not+fine", ["pass", "pass", "fail", "pass", "FAIL"]),
        ("", ["fail", "fail", "pass", "pass", "FAIL"]),  # empty string fails on caps
    ],
)
def test_GenericField(test_value: str, expected_score: list[str]) -> None:
    """Test GenericField values"""
    # Evaluate Test Value
    field = GenericField(value=test_value, id=1)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# ==============================================
# Full filename tests
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
            "hlsp_my-hlsp_hst_readme.txt",
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
            "hlsp_fake-hlsp_hst_wfc3_VEGA_f160w_v1_img.fits",
            "wrong-name",
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
        (
            "this_fake_file_name_has_more_than_nine_fields.fits",  # too many fields
            "fakehlsp",
            ValueError,
        ),
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


# ==============================================
# Other miscellaneous tests
# ==============================================
@pytest.mark.parametrize(
    "test_value, cfg_list",
    [
        ("fits", EXTENSION_TYPES),
        ("spec", SEMANTIC_TYPES),
        ("hst", MISSIONS),
        ("nircam", INSTRUMENTS),
        ("u", FILTERS),
    ],
)
def test_cfg(test_value: str, cfg_list: list) -> None:
    """Test certain values are in the config lists"""
    # Get meta name of cfg_list for error message - i.e., "EXTENSION_TYPES", "MISSIONS"
    for name, value in globals().items():
        if value is cfg_list:
            cfg_name = name
    # Assert value is in list
    assert test_value in cfg_list, f"Error: {test_value} not found in {cfg_name}"


# Test that all field classes are called in HlspFileName (no fields are skipped)
# Listed in backwards order because the last one is passed to function first
# For standard 9-field filename
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.ExtensionField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.ProductField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.VersionField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.FilterField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.TargetField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.InstrumentField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.MissionField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.HlspNameField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.HlspField")
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
        if i == 1:
            mock_field.assert_called_with(parts[i], parts[i])  # two args for HlspName
        else:
            mock_field.assert_called_with(parts[i])  # one for everything else


# Test that all field classes are called in HlspFileName (no fields are skipped)
# Listed in backwards order because the last one is passed to function first
# For shorter 5-field filename with Generic Fields
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.ExtensionField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.GenericField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.HlspNameField")
@mock.patch("mast_contributor_tools.filename_check.hlsp_filename.HlspField")
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
