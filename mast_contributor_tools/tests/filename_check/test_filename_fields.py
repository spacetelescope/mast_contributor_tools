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

import pytest

from mast_contributor_tools.filename_check.filename_fields import (
    EXTENSION_TYPES,
    FILTERS,
    INSTRUMENTS,
    MISSIONS,
    SEMANTIC_TYPES,
    CollectionNameField,
    ExtensionField,
    FilterField,
    GenericField,
    InstrumentField,
    MissionField,
    PrefixField,
    ProductField,
    StringLiteralField,
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
# PrefixField
@pytest.mark.parametrize(
    "test_value, literal_str, expected_score",
    # expected_score is: [capitalization, length, format, value, field_verdict]
    [
        # Expected to Pass
        ("hlsp", "hlsp", ["pass", "pass", "pass", "pass", "PASS"]),
        ("ccsp", "ccsp", ["pass", "pass", "pass", "pass", "PASS"]),
        ("mccm", "mccm", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to Fail = anything else
        ("hlsp", "ccsp", ["pass", "pass", "pass", "fail", "FAIL"]),  # mismatch
        ("ccsp", "hlsp", ["pass", "pass", "pass", "fail", "FAIL"]),  # mismatch
        ("HLSP", "hlsp", ["fail", "pass", "pass", "pass", "FAIL"]),  # no caps
        ("hst", "hlsp", ["pass", "pass", "pass", "fail", "FAIL"]),  # not "hlsp"
        ("banana", "hlsp", ["pass", "fail", "pass", "fail", "FAIL"]),  # not "hlsp"
        ("123-hlsp", "hlsp", ["pass", "fail", "pass", "fail", "FAIL"]),  # not "hlsp"
        ("", "hlsp", ["fail", "fail", "pass", "fail", "FAIL"]),  # empty string
        ("h.lp", "hlsp", ["pass", "pass", "fail", "fail", "FAIL"]),  # special characters
        ("hlsp!", "hlsp", ["pass", "fail", "fail", "fail", "FAIL"]),  # special characters
    ],
)
def test_PrefixField(
    test_value: str,
    literal_str: str,
    expected_score: list[str],
) -> None:
    """Test PrefixField values"""
    # Evaluate Test Value
    field = PrefixField(test_value, literal_str)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


# CollectionNameField
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
def test_CollectionNameField(
    test_value: str,
    ref_name: str,
    expected_score: list[str],
) -> None:
    """Test CollectionNameField values"""
    # Evaluate Test Value
    field = CollectionNameField(test_value, ref_name=ref_name)
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
        ("roman", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to give warnings
        ("hwo", ["pass", "pass", "pass", "needs review", "NEEDS REVIEW"]),
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
        ("wfi", ["pass", "pass", "pass", "pass", "PASS"]),
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
        ("thumb", ["pass", "pass", "pass", "pass", "PASS"]),
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
        ("asdf", ["pass", "pass", "pass", "pass", "PASS"]),
        ("parquet", ["pass", "pass", "pass", "pass", "PASS"]),
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


# StringLiteralField
@pytest.mark.parametrize(
    "test_value, literal_str, expected_score",
    [
        # Expected to Pass
        ("thumb", "thumb", ["pass", "pass", "pass", "pass", "PASS"]),
        ("hlsp", "hlsp", ["pass", "pass", "pass", "pass", "PASS"]),
        # Expected to Fail = anything else
        ("hlsp", "ccsp", ["pass", "pass", "pass", "fail", "FAIL"]),  # mismatch
        ("THUMB", "thumb", ["fail", "pass", "pass", "pass", "FAIL"]),  # no caps
        ("", "", ["fail", "fail", "pass", "pass", "FAIL"]),  # empty string
        ("hlsp!", "hlsp!", ["pass", "pass", "fail", "pass", "FAIL"]),  # special characters
    ],
)
def test_StringLiteralField(
    test_value: str,
    literal_str: str,
    expected_score: list[str],
) -> None:
    """Test StringLiteralField values"""
    # Evaluate Test Value
    field = StringLiteralField(test_value, literal_str)
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
    field = GenericField(value=test_value, id=1, field_indx=1)
    field.evaluate()
    # Assert recieved scores match expected
    assert_scores_match(field.get_scores(), expected_score)


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
