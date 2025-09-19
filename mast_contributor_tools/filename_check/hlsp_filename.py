"""The main logic module to check filename compliance"""

import os
import re
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

# ==========================================
# Setup some configurations for this module
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "fc_config.yaml"), "r") as f:
    cfg = yaml.safe_load(f)

EXTENSION_TYPES = cfg["ExtensionTypes"]
SEMANTIC_TYPES = cfg["SemanticTypes"]
fieldLengthPolicy = cfg["FieldLength"]

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

# HLSP Name Expression:
# "^[a-z]"" : The first character must be a lowercase letter
# "[a-z0-9-]*" : The middle characters can be lowercase letters, numbers, or a hyphen '-'
# "[a-z0-9]$" : The last character must be a lowercase letter or a number
HLSPNAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$")

# Target Name Expression:
# "^[a-zA-Z0-9]" : The first character must be a letter or a number
# "[a-zA-Z0-9+\-.]*" : middle characters can be letters, numbers, or some special characters are  allowed: '+' and '-' and '.'
# "[a-zA-Z0-9]$" : Last character must be a letter or a number (no special characters)
TARGET_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+\-.]*[a-zA-Z0-9]$")

# Version Expression:
# "^v" : must start with "v"
# "[0-9]{0,2}" Next zero to two characters must be numbers
# "([.][0-9]{0,2})": There can be up to two "." or "p" followed by up to two more numbers
# "[0-9]$" : the last character must be a number
VERSION_REGEX = re.compile(r"^v[0-9]{0,2}([.p][0-9]{0,2}){0,2}[0-9]$")


# Expression for all file extension:
# "^[a-zA-Z]"" : The first character must be a lowercase or uppercase letter
# "[a-z0-9.]*" : The middle characters can be letters, numbers, or a period '.'
# "[a-z0-9]$" : The last character must be a letter or a number
EXTENSION_REGEX = re.compile(r"^[a-zA-Z]*[a-zA-Z0-9.]*[a-zA-Z0-9]*$")


# Expression for all other fields: telescope, instrument, filter, etc.:
# (this is purposefully generous on captilization - a different test checks for that and want to avoid confusion)
# "^[a-zA-Z]"" : The first character must be a lowercase or uppercase letter
# "[a-z0-9-]*" : The middle characters can be letters, numbers, or a hyphen '-'
# "[a-z0-9]$" : The last character must be a letter or a number
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

    def length(value: str, max_length: int) -> bool:
        """Test if the character count is non-zero and within the limit for that field.
        Returns 'pass' or 'fail' based on results."""
        return SCORE[(len(value) <= max_length) and (len(value) > 0)]

    def capitalization(value: str) -> bool:
        """Test the captilizaiton: the entire filename must be lowercase.
        Returns 'pass' or 'fail' based on results."""
        return SCORE[value.islower()]

    def match_pattern(value: str, regex_expr: re.Pattern) -> bool:
        """Test that the field contains no forbidden characters.
        Returns 'pass' or 'fail' based on results."""
        return SCORE[regex_expr.match(value) is not None]

    def match_choice(value: str, choice_list: list[str], score_level="lax") -> bool:
        """Checks value against a list, typically from oif.yaml.
        Returns 'pass' or 'needs review' or 'fail' based on results.
        The optional 'score_level' argument determins if 'fail' or 'needs review' is returned (default lax)"""
        if score_level == "lax":
            return SCORE_LAX[value.lower() in choice_list]
        else:
            return SCORE[value.lower() in choice_list]

    def match_multi_choice(value: str, choice_list: list[str], score_level="lax") -> bool:
        """Checks multiple values against a list, typically from oif.yaml.
        Returns 'pass' or 'needs review' or 'fail' based on results.
        The optional 'score_level' argument determins if 'fail' or 'needs review' is returned (default lax)"""
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

    def __init__(self, field_name: str, field_value: str) -> None:
        self.name = field_name
        self.value = field_value
        self.max_len = fieldLengthPolicy[field_name]

        # Set regex pattern based on field name
        if self.name == "hlsp_name":
            self.regex_pattern = HLSPNAME_REGEX
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
        # Final Verdict
        self.field_verdict = "fail"

    @abstractmethod
    def evaluate(self):
        """Evaluate the field for each rule"""
        self.cap_eval = FieldRule.capitalization(self.value)
        self.len_eval = FieldRule.length(self.value, self.max_len)
        self.format_eval = FieldRule.match_pattern(self.value, self.regex_pattern)

    def get_scores(self):
        """Return final scores"""
        # Determine the final verdict as the worst of the four scores
        all_scores = [self.cap_eval, self.len_eval, self.format_eval, self.value_eval]
        self.field_verdict = FieldRule.field_verdict(all_scores)
        return {
            # Name of Field: for example 'mission' or 'product_type'
            "name": self.name,
            # value of the field: for example 'jwst' or 'spec'
            "value": self.value,
            # Results from each validation check
            "capitalization_score": self.cap_eval,
            "length_score": self.len_eval,
            "format_score": self.format_eval,
            "value_score": self.value_eval,
            # Final Score
            "field_verdict": self.field_verdict,
        }


class ExtensionField(FilenameFieldAB):
    def __init__(self, value: str) -> None:
        super().__init__("extension", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_choice(self.value, EXTENSION_TYPES)


class FilterField(FilenameFieldAB):
    """A container for attributes of the filename Filtername field."""

    def __init__(self, value: str) -> None:
        super().__init__("filter", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, FILTERS)


class HlspField(FilenameFieldAB):
    """A container for attributes of the literal 'hlsp' prefix field."""

    def __init__(self, value: str) -> None:
        super().__init__("hlsp_str", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_choice(self.value, ["hlsp"], score_level="fatal")


class HlspNameField(FilenameFieldAB):
    """A container for attributes of the HLSP name field."""

    def __init__(self, value: str, ref_name: str) -> None:
        super().__init__("hlsp_name", value)
        self.hlsp_ref_name = ref_name.lower()

    def evaluate(self):
        super().evaluate()
        # Assume a valid HLSP name was passed to the constructor
        self.value_eval = FieldRule.match_choice(self.value, [self.hlsp_ref_name], score_level="fatal")


class InstrumentField(FilenameFieldAB):
    """A container for attributes of the filename Instrument field."""

    def __init__(self, value: str) -> None:
        super().__init__("instrument", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, INSTRUMENTS)


class MissionField(FilenameFieldAB):
    """A container for attributes of the filename Mission (or observatory) field."""

    def __init__(self, value: str) -> None:
        super().__init__("mission", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, MISSIONS)


class ProductField(FilenameFieldAB):
    """A container for attributes of the filename ProductType field."""

    def __init__(self, value: str) -> None:
        super().__init__("product_type", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_multi_choice(self.value, SEMANTIC_TYPES)


class TargetField(FilenameFieldAB):
    """A container for attributes of the filename TargetName field."""

    def __init__(self, value: str) -> None:
        super().__init__("target_name", value)

    def evaluate(self):
        super().evaluate()
        # A valid target name may contain the following characters in addition to
        # alpha-numeric: + - .
        # but must begin and end with a purely alphanumeric character.
        self.value_eval = FieldRule.match_pattern(self.value, self.regex_pattern)


class VersionField(FilenameFieldAB):
    """A container for attributes of the filename Version field."""

    def __init__(self, value: str) -> None:
        super().__init__("version_id", value)

    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.match_pattern(self.value, self.regex_pattern)


class GenericField(FilenameFieldAB):
    """Generic field concrete class.

    Since some filename fields are optional, this class handles the case of fields
    that are not identifiable with the standard set. In this case the field will be
    validated for length and capitalization, but not for value.
    """

    def __init__(self, value: str, id: int) -> None:
        super().__init__("generic" + str(id), value)

    def evaluate(self):
        super().evaluate()
        # No restriction on generic field values
        self.value_eval = "pass"


class HlspFileName:
    """HLSP filename validation

    Filenames are composed of fields separated by underscores, except
    that the last field is really composed of two fields separated by a period.
    The last part of the last field may also contain a period. Certain fields
    are further composed of elements, separated by hyphens.

    Filenames must have at least 4 and as many as 9 fields to be valid.
    For valid filenames:
      - The first two and the last two fields are required
      - the third from last (N-2) is always required except when the value of
        N-1 is 'readme'

    Unless all 9 fields are present, or only 4 are present, it is not possible
    to determine robustly what the other fields (if present) contain.

    Parameters
    ----------
    path : str
        Filesystem path relative to the root of the HLSP collection files
    filename : str
        Filename of a collection product
    hlsp_name : str
        Official abbreviation/acronym/initialism of this HLSP collection

    Raises
    ------
    ValueError
        If the number of fields falls outside the limits.
    """

    def __init__(self, filepath: Path, hlsp_name: str) -> None:
        self.filepath = filepath
        # Check that filename is of the right form
        if not re.match(FILENAME_REGEX, self.filepath.name):
            raise ValueError(f"Invalid file name for testing: {self.filepath.name}")

        # Check that the HLSP name is valid
        if FieldRule.match_pattern(hlsp_name, HLSPNAME_REGEX):
            self.hlspName = hlsp_name
        else:
            raise ValueError(f"Invalid HLSP name: {hlsp_name}")
        self.fields: list[FilenameFieldAB] = []

    def partition(self) -> None:
        """Partition the filepath into path+filename, and filename into fields"""
        self.name = self.filepath.name
        self.path = str(self.filepath.parents[0])
        parts = self.name.split("_")
        # split the last part into the product type and the file extension
        last = parts[-1].split(".", 1)
        self.fieldvals = parts[:-1] + last
        self.nFields = len(self.fieldvals)
        if self.nFields < 4:
            raise ValueError(f"Filename {self.name} has less than 4 fields")
        elif self.nFields > 9:
            raise ValueError(f"Filename {self.name} has more than 9 fields")

    def create_fields(self) -> None:
        """Create Field objects for each field in the filename."""
        nf = self.nFields
        # The first two fields are: 'hslp' and the acronnym of the collection
        self.fields.append(HlspField(self.fieldvals[0]))
        self.fields.append(HlspNameField(self.fieldvals[1], self.hlspName))
        # The last two fields are: the file semantic type and the extension
        self.fields.append(ExtensionField(self.fieldvals[nf - 1]))
        self.fields.append(ProductField(self.fieldvals[nf - 2]))
        # Files should have a version field unless the product_type is readme
        if self.fieldvals[nf - 2].lower() not in ["readme"]:
            self.fields.append(VersionField(self.fieldvals[nf - 3]))
        # If there are 9 fields, assume the rest of the fields are present in order
        if nf == 9:
            self.fields.append(MissionField(self.fieldvals[2]))
            self.fields.append(InstrumentField(self.fieldvals[3]))
            self.fields.append(TargetField(self.fieldvals[4]))
            self.fields.append(FilterField(self.fieldvals[5]))

        # If there are 5 < nFields < 9, the other fields are treated as generic
        elif 5 < nf < 9:
            for i in range(2, nf - 3):
                self.fields.append(GenericField(self.fieldvals[i], i - 1))

    def evaluate_fields(self):
        """Evaluate attributes of each field

        Returns:
        --------
        List of result dictionaries for each field
        """
        for f in self.fields:
            f.evaluate()
        # If the field evaluations succeeded, set a positive status
        self.field_status = "pass"
        return [f.get_scores() for f in self.fields]

    def evaluate_filename(self):
        """Evaluate attributes of the filename.

        Note that the filename 'status' depends upon having evaluated the fields.

        Returns:
        --------
        dict[str, Any]
            Dictionary of file name attributes
        """
        field_verdicts = [f.field_verdict for f in self.fields]
        if "FAIL" in field_verdicts:
            final_verdict = "fail"
        elif "NEEDS REVIEW" in field_verdicts:
            final_verdict = "needs review"
        else:
            final_verdict = "pass"
        attr = {
            "path": self.path,
            "filename": self.name,
            "n_elements": self.nFields,
            "final_verdict": final_verdict.upper(),
        }
        return attr
