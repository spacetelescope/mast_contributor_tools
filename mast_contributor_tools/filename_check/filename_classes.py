"""The main logic module to check filename compliance"""

import abc
import re
from pathlib import Path
from typing import Union

from mast_contributor_tools.filename_check.filename_fields import (
    COLLECTION_NAME_REGEX,
    CollectionNameField,
    ExtensionField,
    FieldRule,
    FilenameFieldAB,
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
from mast_contributor_tools.utils.logger_config import setup_logger

logger = setup_logger(__name__)


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


class GenericFilename:
    """
    Generic class for filename parsing for HLSPs, MCCMs, and CCSPs.

    Filenames are composed of fields separated by underscores, except
    that the last field is really composed of two fields separated by a period.
    The last part of the last field may also contain a period. Certain fields
    are further composed of elements, separated by hyphens.

    Filenames must have at least 4 and as many as 9 fields to be valid,
    but the rules can vary slightly by collection type (HLSP, CCSP, MCCM).
    """

    def __init__(self, filepath: Path, min_fields: int, max_fields: int) -> None:
        """Initialize instance of Filename class.

        Parameters
        ===========
        filepath: Path
            full filename path to check
        min_fields: int
            Minimum number of fields allowed, set by individual collection rules
        max_fields: int
            Maxmimum number of fields allowed, set by individual collection rules
        """

        self.filepath = filepath
        # Minimum/maximum number of fields allowed - set by collection rules
        self.min_fields = min_fields
        self.max_fields = max_fields
        # Check that filename is of the right form
        if not re.match(FILENAME_REGEX, self.filepath.name):
            raise ValueError(f"Invalid file name for testing: {self.filepath.name}")

    def partition(self) -> None:
        """Partition the filepath into path+filename, and filename into fields"""
        self.name = self.filepath.name
        self.path = str(self.filepath.parents[0])
        parts = self.name.split("_")
        # split the last part into the product type and the file extension
        last = parts[-1].split(".", 1)
        self.field_values = parts[:-1] + last
        self.n_fields = len(self.field_values)
        if self.n_fields < self.min_fields:
            msg = f"Filename {self.name} has less than {self.min_fields} fields"
            raise ValueError(msg)
        elif self.n_fields > self.max_fields:
            # Don't raise a ValueError here:
            # The individual fields can still be checked
            # but filename will be added to the results as a FAIL
            logger.error(
                (
                    f"Filename '{self.name}' contains more than "
                    f"{self.max_fields} fields (total {self.n_fields}). "
                    "Individual fields will still be evaulated, "
                    "but the final verdict will be 'FAIL'"
                )
            )

    @abc.abstractmethod
    def create_fields(self) -> None:
        """Abstract method to be over-written by each filename class.
        Creates Field objects for each field in the filename."""

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
        # The final verdict is determined as the worst of the individual field verdicts
        field_verdicts = [f.field_verdict for f in self.fields]
        if "FAIL" in field_verdicts:
            final_verdict = "fail"
        elif "NEEDS REVIEW" in field_verdicts:
            final_verdict = "needs review"
        else:
            final_verdict = "pass"

        # Additional last-minute checks based on the number of fields
        if self.n_fields > self.max_fields:  # more than max required fields
            final_verdict = "fail"
        elif self.n_fields < self.min_fields:  # less than min required fields
            final_verdict = "fail"

        # Final result for this filename
        attr = {
            "path": self.path,
            "filename": self.name,
            "n_elements": self.n_fields,
            "final_verdict": final_verdict.upper(),
        }
        return attr


class MCCMFileName(GenericFilename):
    """MCCM filename validation

    For more detail on MCCM filename requirements, see documentation at:
      https://outerspace.stsci.edu/spaces/DraftMASTCONTRIB/pages/340296136/.File+Naming+for+Missions+v1.0
    """

    def __init__(self, filepath: Path, mccm_name: str) -> None:
        # Initialize class
        super().__init__(filepath, min_fields=8, max_fields=9)

        # Check that the CCSP/PIT name is valid
        # Use same regex as HLSPNAME for now
        if FieldRule.match_pattern(mccm_name, COLLECTION_NAME_REGEX):
            self.mccm_name = mccm_name
        else:
            raise ValueError(f"Invalid MCCM name: {mccm_name}")

        self.fields: list[FilenameFieldAB] = []

    def create_fields(self) -> None:
        """Create Field objects for each field in the filename."""
        nf = self.n_fields

        # The first two fields are: 'ccsp' and the pit name
        self.fields.append(PrefixField(self.field_values[0], "mccm", 0))
        self.fields.append(CollectionNameField(self.field_values[1], self.mccm_name, 1))

        # If there are at least 8 fields, assume the rest of the fields are present in order
        if nf > 7:
            self.fields.append(InstrumentField(self.field_values[2], 2))
            self.fields.append(TargetField(self.field_values[3], 3))
            self.fields.append(FilterField(self.field_values[4], 4))
            self.fields.append(VersionField(self.field_values[5], 5))
            self.fields.append(ProductField(self.field_values[6], 6))

            if nf == 9:
                # If there are 9 fields, the last field must be string literal "thumb"
                # (this is a special exception for thumbnail preview files)
                self.fields.append(StringLiteralField(self.field_values[7], "thumb", 7))
            # If there are more than 9 fields, treat the extra fields as generic
            # This will fail at the filename level, but the fields can still be tested
            elif nf > 9:
                for i in range(7, nf - 1):
                    self.fields.append(GenericField(self.field_values[i], i, i))

        # The last field is the extension
        self.fields.append(ExtensionField(self.field_values[nf - 1], nf - 1))


class CCSPFileName(GenericFilename):
    """CCSP filename validation

    For more detail on CCSP filename requirements, see documentation at:
      https://outerspace.stsci.edu/spaces/DraftMASTCONTRIB/pages/344589039/.File+Naming+for+PITs+v1.0
    """

    def __init__(self, filepath: Path, ccsp_name: str) -> None:
        # Initialize class
        super().__init__(filepath, min_fields=8, max_fields=9)

        # Check that the CCSP/PIT name is valid
        # Use same regex as HLSPNAME for now
        if FieldRule.match_pattern(ccsp_name, COLLECTION_NAME_REGEX):
            self.ccsp_name = ccsp_name
        else:
            raise ValueError(f"Invalid CCSP name: {ccsp_name}")

        self.fields: list[FilenameFieldAB] = []

    def create_fields(self) -> None:
        """Create Field objects for each field in the filename."""
        nf = self.n_fields

        # The first two fields are: 'ccsp' and the pit name
        self.fields.append(PrefixField(self.field_values[0], "ccsp", 0))
        self.fields.append(CollectionNameField(self.field_values[1], self.ccsp_name, 1))

        # If there are at least 8 fields, assume the rest of the fields are present in order
        if nf > 7:
            self.fields.append(InstrumentField(self.field_values[2], 2))
            self.fields.append(TargetField(self.field_values[3], 3))
            self.fields.append(FilterField(self.field_values[4], 4))
            self.fields.append(VersionField(self.field_values[5], 5))
            self.fields.append(ProductField(self.field_values[6], 6))

            if nf == 9:
                # If there are 9 fields, the last field must be string literal "thumb"
                # (this is a special exception for thumbnail preview files)
                self.fields.append(StringLiteralField(self.field_values[7], "thumb", 7))
            # If there are more than 9 fields, treat the extra fields as generic
            # This will fail at the filename level, but the fields can still be tested
            elif nf > 9:
                for i in range(7, nf - 1):
                    self.fields.append(GenericField(self.field_values[i], i, i))

        # The last field is the extension
        self.fields.append(ExtensionField(self.field_values[nf - 1], nf - 1))


class HlspFileName(GenericFilename):
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

    For more detail on HLSP filename requirements, see documentation at:
     https://outerspace.stsci.edu/spaces/DraftMASTCONTRIB/pages/326042567/File+Naming+Convention+for+HLSPs

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
        # Initialize class
        super().__init__(filepath, min_fields=4, max_fields=9)

        # Check that the HLSP name is valid
        if FieldRule.match_pattern(hlsp_name, COLLECTION_NAME_REGEX):
            self.hlsp_name = hlsp_name
        else:
            raise ValueError(f"Invalid HLSP name: {hlsp_name}")

        self.fields: list[FilenameFieldAB] = []

    def create_fields(self) -> None:
        """Create Field objects for each field in the filename."""
        nf = self.n_fields
        # The first two fields are: 'hlsp' and the acronnym of the collection
        self.fields.append(PrefixField(self.field_values[0], "hlsp", 0))
        self.fields.append(CollectionNameField(self.field_values[1], self.hlsp_name, 1))

        # If there are 9 fields, assume the rest of the fields are present in order
        if nf == 9:
            self.fields.append(MissionField(self.field_values[2], 2))
            self.fields.append(InstrumentField(self.field_values[3], 3))
            self.fields.append(TargetField(self.field_values[4], 4))
            self.fields.append(FilterField(self.field_values[5], 5))

        # If there are 5 < nFields < 9, the other fields are treated as generic
        elif 5 < nf < 9:
            for i in range(2, nf - 3):
                self.fields.append(GenericField(self.field_values[i], i - 1, i))

        # If there are more than 9 fields, treat the extra fields as generic
        # The check will fail at the filename level, but the fields can still be tested
        elif nf > 9:
            self.fields.append(MissionField(self.field_values[2], 2))
            self.fields.append(InstrumentField(self.field_values[3], 3))
            self.fields.append(TargetField(self.field_values[4], 4))
            self.fields.append(FilterField(self.field_values[5], 5))
            for i in range(6, nf - 3):
                self.fields.append(GenericField(self.field_values[i], i - 5, i))

        # Files should have a version field unless the product_type is readme
        if self.field_values[nf - 2].lower() not in ["readme"]:
            self.fields.append(VersionField(self.field_values[nf - 3], nf - 3))

        # The last two fields are: the file semantic type and the extension
        self.fields.append(ProductField(self.field_values[nf - 2], nf - 2))
        self.fields.append(ExtensionField(self.field_values[nf - 1], nf - 1))


def identify_collection_type(file_name: str) -> str:
    """
    Identify if a file is an HLSP, CCSP, or MCCM product based on the file name prefix.

    Parameters
    ----------
    filename : Path
        File name

    Returns
    -------
    collection_type: str
        Collection Type - "HLSP", "CCSP", or "MCCM". Raises a warning and defaults to "HLSP" if unable to identify.
    """
    collection_type = file_name.split("_")[0].upper()
    if collection_type.upper() not in ["HLSP", "MCCM", "CCSP"]:
        # Default to HLSP, raise warning
        msg = f"WARNING: Could not identify collection type '{collection_type}' from filename. Assuming HLSP."
        logger.warning(msg)
        collection_type = "HLSP"
    return collection_type


def get_filename_class(file_name: Path, collection_name: str) -> Union[HlspFileName, CCSPFileName, MCCMFileName]:
    """
    Parameters
    ----------
    filename : Path
        File name path object

    collection_name : str, optional
        Name of HLSP/MCCM/CCSP collection.

    Returns:
    --------
    Filename Validator class for the appropriate collectiion: HlspFilename, CCSPFilename, or MCCMFilename
    """

    # Infer collection type from file name
    collection_type = identify_collection_type(str(file_name))

    # Initiate relevant class object
    if collection_type == "HLSP":
        filename_class = HlspFileName(file_name, collection_name)
    elif collection_type == "CCSP":
        filename_class = CCSPFileName(file_name, collection_name)
    elif collection_type == "MCCM":
        filename_class = MCCMFileName(file_name, collection_name)

    return filename_class
