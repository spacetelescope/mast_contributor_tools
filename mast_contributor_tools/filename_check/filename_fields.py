"""Module containing individual field logic to check filename compliance"""

import os
import re
from abc import ABC, abstractmethod

import yaml

from mast_contributor_tools.utils.logger_config import setup_logger

logger = setup_logger(__name__)

# ==========================================
# Setup some configurations for this module
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "fc_config.yaml"), "r") as f:
    cfg = yaml.safe_load(f)

EXTENSION_TYPES = cfg["ExtensionTypes"]
SEMANTIC_TYPES = cfg["SemanticTypes"]
FIELD_LENGTH = cfg["FieldLength"]

# Fetch configurations of three name fields: observation, instrument, and filter (oif)
with open(os.path.join(BASE_DIR, "oif.yaml"), "r") as f:
    oif = yaml.safe_load(f)

MISSIONS = [*oif]
INSTRUMENTS = set(sum([[*oif[m]["instruments"]] for m in MISSIONS], []))
# Tussing the list of all unique filters takes more work
# The following does not support name "aliases" in the yaml file
filt_list = []
for m in MISSIONS:
    for i in [*oif[m]["instruments"]]:
        for f in [*oif[m]["instruments"][i]["filters"]]:
            filt_list.append(f)

FILTERS = set(filt_list)

SCORE = {False: "fail", True: "pass"}
SCORE_LAX = {False: "needs review", True: "pass"}

# Define REGEX pattern rules for various fields
# Use https://regex101.com to verify these and explore more examples

# File Name Expression:
# "^[a-zA-Z0-9]": The first character must be a letter or a number
# "[\w\-\+]+": The middle characters can be word characters (\w for 'word') or a hyphen (\-) or a plus sign (\+)
# Note: \w is equivalent to [a-zA-Z0-9_]: any letter, number, or underscore.
# "(\.[\w\-\+\.]+)?": There can optionally be a period follwed by more word characters in the middle (for example "v1.0_spec"")
# "(\.[\w]+": The file should end with "." follwed by a word (like ".fits" or ."jpg")
# "(\.gz|\.zip)?)$": the file can optionally end in .gz or .zip too
# Note this expression is intentionally too generous; this is used to search for files to test, not to actually test the files
# For example, this regex allows the first character to be a number, when the rules require the name to start with 'hlsp'
# In that case, the file would match this pattern and therefore be added to the list to test, but it would fail the tests due to the value
FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9][\w\-\+]+(\.[\w\-\+\.]+)?(\.[\w]+(\.gz|\.zip)?)$")

# Collection Name Expression:
# "^[a-zA-Z]"" : The first character must be a lowercase letter
# "[a-zA-Z0-9-]*" : The middle characters can be lowercase letters, numbers, or a hyphen '-'
# "[a-zA-Z0-9]$" : The last character must be a lowercase letter or a number
COLLECTION_NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$")

# Target Name Expression:
# "^[a-zA-Z0-9]" : The first character must be a letter or a number
# "[a-zA-Z0-9+\-.]*" : middle characters can be letters, numbers, or some special characters are  allowed: '+' and '-' and '.'
# "[a-zA-Z0-9]$" : Last character must be a letter or a number (no special characters)
TARGET_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+\-.]*[a-zA-Z0-9]$")

# Version Expression:
# "^v" : must start with lowercase "v"
# "[0-9]{0,2}" Next zero to two characters must be numbers
# "([.][0-9]{0,2})": There can be up to two "." or "p" followed by up to two more numbers
# "[0-9]$" : the last character must be a number
VERSION_REGEX = re.compile(r"^v[0-9]{0,2}([.p][0-9]{0,2}){0,2}[0-9]$")


# Expression for all file extension:
# "^[a-zA-Z]"" : The first character must be a lowercase or uppercase letter
# "[a-zA-Z0-9.]*" : The middle characters can be letters, numbers, or a period '.'
# "[a-zA-Z0-9]*$" : The last character must be a letter or a number
EXTENSION_REGEX = re.compile(r"^[a-zA-Z]*[a-zA-Z0-9.]*[a-zA-Z0-9]*$")


# Expression for all other fields: telescope, instrument, filter, etc.:
# (this is purposefully generous on captilization - a different test checks for that and want to avoid confusion)
# "^[a-zA-Z]"" : The first character must be a lowercase or uppercase letter
# "[a-zA-Z0-9-]*" : The middle characters can be letters, numbers, or a hyphen '-'
# "[a-zA-Z0-9]$" : The last character must be a letter or a number
OTHER_REGEX = re.compile(r"^[a-zA-Z]*[a-zA-Z0-9-]*[a-zA-Z0-9]*$")


# =============================
# Classes for field rules
# =============================


class FieldRule:
    """Rules for filename validation.

    This class embodies rules for validating attributes of field names. The
    approach to validiting field *values* varies by field. The expressions that
    validate the version or target fields can be verified at https://regex101.com
    """

    def length(value: str, max_length: int) -> str:
        """Test if the character count is non-zero and within the limit for that field.
        Returns 'pass' or 'fail' based on results."""
        return SCORE[(len(value) <= max_length) and (len(value) > 0)]

    def capitalization(value: str) -> str:
        """Test the captilizaiton: the entire filename must be lowercase.
        Returns 'pass' or 'fail' based on results."""
        return SCORE[value.islower()]

    def nfields(field_index: int) -> str:
        """Tests that the field index is less than 9;
        Returns 'pass' or 'fail' based on results."""
        return SCORE[field_index < 10]

    def match_pattern(value: str, regex_expr: re.Pattern) -> str:
        """Test that the field contains no forbidden characters.
        Returns 'pass' or 'fail' based on results."""
        return SCORE[regex_expr.match(value) is not None]

    def match_choice(value: str, choice_list: list[str], score_level="lax") -> str:
        """Checks value against a list, typically from oif.yaml.
        Returns 'pass' or 'needs review' or 'fail' based on results.
        The optional 'score_level' argument determines if 'fail' or 'needs review' is returned (default lax)"""
        if score_level == "lax":
            return SCORE_LAX[value.lower() in choice_list]
        else:
            return SCORE[value.lower() in choice_list]

    def match_multi_choice(value: str, choice_list: list[str], score_level="lax") -> str:
        """Checks multiple values against a list, typically from oif.yaml.
        Returns 'pass' or 'needs review' or 'fail' based on results.
        The optional 'score_level' argument determines if 'fail' or 'needs review' is returned (default lax)"""
        # match all elements in a hyphenated value to the choice_list
        if score_level == "lax":
            return SCORE_LAX[all([(v.lower() in choice_list) for v in value.split("-")])]
        else:
            return SCORE[all([(v.lower() in choice_list) for v in value.split("-")])]

    def field_verdict(scores: list[str]) -> str:
        """Determine the final verdict for this field: 'pass', 'needs review' or 'fail',
        determined as the worst of the input scores."""
        if "fail" in scores:
            verdict = "fail"
        elif "needs review" in scores:
            verdict = "needs review"
        else:
            verdict = "pass"

        return verdict.upper()


class FilenameFieldAB(ABC):
    """Template for Filename Field classes.

    Each field of a filename in an HLSP collection will be evaluated for:
    length, capitalization, content, and often a match against valid values.
    Each evaluation results in a score, which is one of:
    - 'pass' for no detected problems
    - 'fail' for a detected problem that must be fixed
    - 'needs review' for a possible but non-fatal problem that requires review by MAST Staff

    The final verdict of the set of evaluations is determined as the worst of the input scores.

    Parameters
    ----------
    field_name : str
        Internal name for the field being created
    field_value : str
        Value of the field (i.e. text of the field in the filename)
    """

    def __init__(self, field_name: str, field_value: str, field_indx: int) -> None:
        self.name = field_name
        self.value = field_value
        self.max_len = FIELD_LENGTH[field_name]
        self.field_indx = field_indx + 1  # index from 1 instead of 0

        # Set regex pattern based on field name
        if self.name == "collection_name":
            self.regex_pattern = COLLECTION_NAME_REGEX
        elif self.name == "target_name":
            self.regex_pattern = TARGET_REGEX
        elif self.name == "version_id":
            self.regex_pattern = VERSION_REGEX
        elif self.name == "extension":
            self.regex_pattern = EXTENSION_REGEX
        else:
            self.regex_pattern = OTHER_REGEX

        # Capitalization Evaluation
        self.cap_eval = False
        # Character Length Evaluation
        self.len_eval = False
        # Format Evaluation (no forbidden characters)
        self.format_eval = False
        # Value Evaluation (recognized entries for telescope, filter, etc.)
        self.value_eval = False
        # Field number index evaluation (must be less than 9)
        self.nfield_eval = False
        # Final Verdict
        self.field_verdict = "fail"

    @abstractmethod
    def evaluate(self):
        """Evaluate the field for each rule"""
        self.cap_eval = FieldRule.capitalization(self.value)
        self.len_eval = FieldRule.length(self.value, self.max_len)
        self.format_eval = FieldRule.match_pattern(self.value, self.regex_pattern)
        self.nfield_eval = FieldRule.nfields(self.field_indx)

    def get_scores(self):
        """Return final scores"""
        # Determine the final verdict as the worst of the four scores
        all_scores = [self.cap_eval, self.len_eval, self.format_eval, self.value_eval, self.nfield_eval]
        self.field_verdict = FieldRule.field_verdict(all_scores)
        return {
            # Name of Field: for example 'mission' or 'product_type'
            "name": self.name,
            # value of the field: for example 'jwst' or 'spec'
            "value": self.value,
            # Index of the field: location in file name
            "nfield": self.field_indx,
            # Results from each validation check
            "capitalization_score": self.cap_eval,
            "length_score": self.len_eval,
            "format_score": self.format_eval,
            "value_score": self.value_eval,
            "nfield_score": self.nfield_eval,
            # Final Score
            "field_verdict": self.field_verdict,
        }


class ExtensionField(FilenameFieldAB):
    def __init__(self, value: str, field_indx: int = 8) -> None:
        super().__init__("extension", value, field_indx)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_choice(self.value, EXTENSION_TYPES)


class FilterField(FilenameFieldAB):
    """A container for attributes of the filename Filtername field."""

    def __init__(self, value: str, field_indx: int = 5) -> None:
        super().__init__("filter", value, field_indx)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, FILTERS)


class PrefixField(FilenameFieldAB):
    """A container for attributes of the literal 'hlsp', 'ccsp', or 'mccm' prefix field."""

    def __init__(self, value: str, string_match: str = "hlsp", field_indx: int = 0) -> None:
        super().__init__("hlsp_str", value, field_indx)
        self.string_match = [string_match]

    def evaluate(self) -> None:
        super().evaluate()
        self.value_eval = FieldRule.match_choice(self.value, self.string_match, score_level="fatal")


class CollectionNameField(FilenameFieldAB):
    """A container for attributes of the HLSP/CCSP/MMCM collection name field."""

    def __init__(self, value: str, ref_name: str, field_indx: int = 1) -> None:
        super().__init__("collection_name", value, field_indx)
        self.collection_ref_name = ref_name.lower()

    def evaluate(self):
        super().evaluate()
        # Assume a valid HLSP name was passed to the constructor
        self.value_eval = FieldRule.match_choice(self.value, [self.collection_ref_name], score_level="fatal")


class InstrumentField(FilenameFieldAB):
    """A container for attributes of the filename Instrument field."""

    def __init__(self, value: str, field_indx: int = 3) -> None:
        super().__init__("instrument", value, field_indx)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, INSTRUMENTS)


class MissionField(FilenameFieldAB):
    """A container for attributes of the filename Mission (or observatory) field."""

    def __init__(self, value: str, field_indx: int = 2) -> None:
        super().__init__("mission", value, field_indx)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, MISSIONS)


class ProductField(FilenameFieldAB):
    """A container for attributes of the filename ProductType field."""

    def __init__(self, value: str, field_indx: int = 7) -> None:
        super().__init__("product_type", value, field_indx)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, SEMANTIC_TYPES)


class StringLiteralField(FilenameFieldAB):
    """
    A container for attributes of the 'StringLiteral' field, matching
    against an exact string (for example '_thumb' for thumbnail previews)
    """

    def __init__(self, value: str, string_match: str, field_indx: int = 0) -> None:
        super().__init__("str_literal", value, field_indx)
        self.string_match = [string_match]

    def evaluate(self) -> None:
        super().evaluate()
        self.value_eval = FieldRule.match_choice(self.value, self.string_match, score_level="fatal")


class TargetField(FilenameFieldAB):
    """A container for attributes of the filename TargetName field."""

    def __init__(self, value: str, field_indx: int = 4) -> None:
        super().__init__("target_name", value, field_indx)

    def evaluate(self):
        super().evaluate()
        # A valid target name may contain the following characters in addition to
        # alpha-numeric: + - .
        # but must begin and end with a purely alphanumeric character.
        self.value_eval = FieldRule.match_pattern(self.value, self.regex_pattern)


class VersionField(FilenameFieldAB):
    """A container for attributes of the filename Version field."""

    def __init__(self, value: str, field_indx: int = 6) -> None:
        super().__init__("version_id", value, field_indx)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_pattern(self.value, self.regex_pattern)


class GenericField(FilenameFieldAB):
    """Generic field concrete class.

    Since some filename fields are optional, this class handles the case of fields
    that are not identifiable with the standard set. In this case the field will be
    validated for length and capitalization, but not for value.
    """

    def __init__(self, value: str, id: int, field_indx: int) -> None:
        super().__init__("generic" + str(id), value, field_indx)

    def evaluate(self) -> None:
        super().evaluate()
        # No restriction on generic field values
        self.value_eval = "pass"
