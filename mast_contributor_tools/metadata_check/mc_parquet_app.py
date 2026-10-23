import logging
import os
import re
import subprocess
import warnings
from io import BytesIO
from pathlib import Path

import pyarrow.parquet as pq  # type: ignore
import requests
import yaml  # type: ignore
from astropy import units as u  # type: ignore
from astropy.io.votable import parse  # type: ignore
from astropy.io.votable.ucd import check_ucd  # type: ignore
from astropy.table import Table  # type: ignore
from astropy.units import UnitsWarning  # type: ignore
from astropy.units.format.vounit import VOUnit  # type: ignore

from mast_contributor_tools.utils.logger_config import setup_logger

# TODO eventually: make a few try-except exception classes more specific (see TODOs throughout)
# TODO eventually: add debug logging
# TODO eventually: make agnostic to PITs/CCSPs vs. MCCMs vs. HLSPs (mainly just validate_keys, but communication issues throughout)


def run_parqlint(parquet_file, jar_file="stilts.jar", unrecognized_unit_warnings=False):
    """
    Run STILTS parqlint in a subprocess. Requires JAR file with parqlint to run.

    Parameters
    ----------
    parquet_file : str
        Path to the Parquet file being test.

    jar_file : str, optional
        Path to the JAR file needed to run parqlint. Defaults to stilts.jar in local directory.

    unrecognized_unit_warnings : bool, optional
        Boolean to enable (over)zealous unit warnings. Defaults to False.

    Returns
    -------
    str | None
        A concatenated string of stdout from parqlint, or None if stdout is empty.

    """
    try:
        parq = subprocess.run(
            [
                "java",
                "-jar",
                str(Path(jar_file)),
                "parqlint",
                f"in={parquet_file}",
                "time=true",
                "ucd=true",
                "unit=true",
                "voparquet=true",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:  # if java not installed
        raise RuntimeError(
            "Java may not be installed in your system, or the java command may not be in your PATH. Please see the mast_contributor_tools repository README if you need help installing java."
        )

    if parq.stdout:
        lines = parq.stdout.splitlines()
        for i, line in enumerate(lines):  # escalate "bad unit grammar" warning to error
            if "(BAD_SYNTAX)" in line:  # this ERROR from parqlint is not zealous enough; escalate to ERROR
                lines[i] = line.replace("WARNING:", "ERROR:")
        if unrecognized_unit_warnings:  # if strict unit checking is turned on, keep every line
            lined_output = [line for line in lines]
            lined_output = dict.fromkeys(lined_output).keys()  # set, but preserve order
            return "\n".join(lined_output)
        else:  # if strict unit checking is turned off, compress unknown/deprecated unit warnings into a single INFO message
            lined_output = [line for line in lines if "UNKNOWN_UNIT" not in line]
            if "UNKNOWN_UNIT" in parq.stdout:
                lined_output += [
                    "INFO: unknown and/or deprecated unit warnings were suppressed; unrecognized but syntactically proper units are allowed in VOUnit. To show zealous unit warnings, re-run with unrecognized_unit_warnings = True."
                ]
            lined_output = dict.fromkeys(lined_output).keys()  # set, but preserve order
            return "\n".join(lined_output)
    else:
        return None


def download_jar_file(url) -> str:
    """
    If the JAR file isn't found in the local directory, prompt the user on whether to download it.

    Parameters
    ----------
    url : str
        URL for JAR file.

    Returns
    -------
    str
        The new path to the JAR file on the user's machine, either ./stilts.jar or
        or a path provided by the user.
    """
    # Prompt the user for confirmation
    confirm = input(
        f"VOParquet keys detected, but stilts.jar file not found. Do you want to download the file from {url} (50 MB)? (y/n, or enter the path to a stilts.jar file on your machine): "
    )

    if confirm.lower() in ("n", "no"):
        print("Proceeding without stilts.jar...")
        return "stilts.jar"

    elif confirm.lower() not in ("y", "yes"):
        if not Path(confirm.strip()).is_file():
            print(f"No file found at {confirm.strip()}. Proceeding without stilts.jar...")
            return "stilts.jar"
        else:
            print(f"Trying to use {confirm.strip()}...")
            return confirm.strip()

    else:
        try:
            print("Downloading to local directory...")
            response = requests.get(url)
            response.raise_for_status()
            with open("stilts.jar", "wb") as f:
                f.write(response.content)
            print("Download successful.")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Proceeding without stilts.jar...")
        return "stilts.jar"


class parquet_validator:
    """
    Parquet validation class, holding attributes like the list of
    evaluation results, the logger, and the key-value metadata dictionary
    from the Parquet footer.

    Parameters
    ----------
    file : str
        Path to the Parquet file being test.

    unrecognized_unit_warnings : bool, optional
        Boolean to enable (over)zealous unit warnings. Defaults to False.

    vo_required : bool, optional
        Boolean to require a VOParquet key in order to PASS a file (defaults to False, meaning that the VOParquet check can be skipped if not present without causing a fail)

    jar_file : str, optional
        Path to the JAR file needed to run parqlint. Defaults to stilts.jar in local directory.

    no_color : bool, optional
        Boolean to turn off color-coded terminal output
    """

    def __init__(
        self,
        file: str,
        unrecognized_unit_warnings: bool = False,
        vo_required: bool = False,
        jar_file: str = "stilts.jar",
        no_color: bool = False,
    ) -> None:
        self.file = file
        self.unrecognized_unit_warnings = unrecognized_unit_warnings
        self.vo_required = vo_required
        self.jar_file = jar_file
        self.no_color = no_color
        self.logger: logging.Logger = setup_logger(__name__, no_color=no_color)
        self.evaluations: list = []

        # Read the key-value dictionary in the Parquet footer
        cat_pq = pq.read_table(self.file)
        metadata_binary = cat_pq.schema.metadata
        self.metadata = {k.decode("utf-8"): v.decode("utf-8") for k, v in metadata_binary.items()}

    def validate_voparquet(self) -> str:
        """
        Validate the VOParquet aspects of the file, and their consistency with the rest of the file.

        Returns
        -------
        str
            Evaluation string (one of "PASS", "FAIL", "SKIPPED")
        """

        self.logger.critical("Validating VOParquet...")
        evaluation_voparquet = "PASS"  # default to PASS

        # if VOTable keys present, try to run parqlint and extract its messages
        if "IVOA.VOTable-Parquet.content" in self.metadata.keys():
            if not Path(self.jar_file).is_file():
                # Try to download stilts.jar to local directory, or prompt user path to their local stilts.jar file
                self.jar_file = download_jar_file("https://www.star.bristol.ac.uk/mbt/stilts/stilts.jar")

            # Validate with parqlint
            if Path(self.jar_file).is_file():
                try:
                    parqlint_out = run_parqlint(
                        self.file, unrecognized_unit_warnings=self.unrecognized_unit_warnings, jar_file=self.jar_file
                    )
                except RuntimeError as e:
                    message = "WARNING: VOParquet keys detected, but attempt to run parqlint failed. Skipping VOParquet validation."
                    self.logger.warning(message)
                    warnings.warn(
                        message + f" The parqlint subprocess produced the following message: {e}", RuntimeWarning
                    )
                else:
                    if parqlint_out is None:
                        pass
                    messages = parqlint_out.split("\n")
                    for msg in messages:
                        if msg.startswith("WARNING: "):
                            self.logger.warning(msg)
                        elif msg.startswith("ERROR: "):
                            self.logger.error(msg)
                        elif msg.startswith("INFO: "):
                            self.logger.info(msg)

                    # if any line reports an ERROR, evaluation returns FAIL
                    def any_line_contains(sub, text):
                        lines = text.splitlines()
                        return any(sub in line for line in lines)

                    if any_line_contains("ERROR:", parqlint_out):
                        evaluation_voparquet = "FAIL"

            else:
                message = (
                    "WARNING: VOParquet keys detected, but stilts.jar file not found. Skipping VOParquet validation."
                )
                self.logger.warning(message)
                # code is not behaving as intended, so raise a warning to stderr too
                warnings.warn(message)
                evaluation_voparquet = "SKIPPED"

        else:
            if not self.vo_required:
                self.logger.warning(
                    "WARNING: Not a VOParquet file. This is acceptable for catalogs (section 3 of PIT/CCSP guidelines), but not for file-based approaches (section 4)."
                )
                evaluation_voparquet = "SKIPPED"
            else:
                self.logger.error(
                    "ERROR: Not a VOParquet file. This is acceptable for catalogs (section 3 of PIT/CCSP guidelines), but not for file-based approaches (section 4)."
                )
                evaluation_voparquet = "FAIL"
        self.logger.critical(f"-------> VOParquet validation report: '{evaluation_voparquet}'")
        print()
        self.evaluations.append(evaluation_voparquet)

        return evaluation_voparquet

    def validate_table_meta_yaml(self) -> str:
        """
        Validate the table_meta_yaml aspects of the file, and their consistency with the rest of the file.

        Returns
        -------
        str
            Evaluation string (one of "PASS", "FAIL", "SKIPPED")
        """
        self.logger.critical("Validating table_meta_yaml...")
        if "table_meta_yaml" not in self.metadata.keys():
            evaluation_table_meta_yaml = "FAIL"
            self.logger.error(
                "ERROR: table_meta_yaml key was not found. This key is required for all PIT/CCSP Parquet products."
            )
        else:
            evaluation_table_meta_yaml = "PASS"  # default to PASS
            # Get column names, units, and UCDs from table_meta_yaml
            column_name_pattern = r"name:\s*([^\n,{}]+?)[\n,]"
            unit_pattern = r"unit:\s*([^\n,{}]+?)[\n,]"
            ucd_pattern = r"ucd:\s*([^\n,{}]+?)[}]"

            table_meta_yaml_columns = re.findall(column_name_pattern, self.metadata["table_meta_yaml"])
            table_meta_yaml_units = re.findall(unit_pattern, self.metadata["table_meta_yaml"])
            table_meta_yaml_ucds = re.findall(ucd_pattern, self.metadata["table_meta_yaml"])

            # Get column names from parquet schema
            parquet_schema_columns = pq.read_table(self.file).column_names

            # Check if column names match between parquet schema and table_meta_yaml
            if not (parquet_schema_columns == table_meta_yaml_columns):
                # Get columns missing from one or the other schema
                missing_from_parquet = [x for x in set(table_meta_yaml_columns) if x not in parquet_schema_columns]
                missing_from_yaml = [x for x in set(parquet_schema_columns) if x not in table_meta_yaml_columns]

                # Ignoring any missing columns and any duplicates after the first instance, check if the order of columns is the same
                common = set(parquet_schema_columns) & set(table_meta_yaml_columns)
                parquet_schema_columns_filtered = list(
                    dict.fromkeys(x for x in parquet_schema_columns if x in common).keys()
                )  # ignore duplicates
                table_meta_yaml_columns_filtered = list(
                    dict.fromkeys(x for x in table_meta_yaml_columns if x in common).keys()
                )  # ignore duplicates
                same_order = parquet_schema_columns_filtered == table_meta_yaml_columns_filtered

                # Check if duplicate columns in table_meta_yaml
                duplicates_in_yaml = len(set(table_meta_yaml_columns)) < len(table_meta_yaml_columns)

                # Construct error message
                error_message_column_match = "ERROR: mismatch between the column names in the Parquet schema and the column names in table_meta_yaml."

                if len(missing_from_parquet) > 0:
                    error_message_column_match += f" The following column names from table_meta_yaml are missing from the Parquet schema: {missing_from_parquet}"
                if len(missing_from_yaml) > 0:
                    error_message_column_match += f" The following column names from the Parquet schema are missing from table_meta_yaml: {missing_from_yaml}"
                if not same_order:
                    error_message_column_match += " The columns in table_meta_yaml are not in the same order as the columns in the Parquet schema."
                if duplicates_in_yaml:
                    error_message_column_match += " There are duplicated column names in table_meta_yaml."

                self.logger.error(error_message_column_match)
                evaluation_table_meta_yaml = "FAIL"

            # Check if UCDs in table_meta_yaml are valid
            table_meta_yaml_evalucds = []
            for ucd in table_meta_yaml_ucds:
                table_meta_yaml_evalucds.append(check_ucd(ucd, check_controlled_vocabulary=True))
            invalid = [
                column for column, evalucd in zip(table_meta_yaml_columns, table_meta_yaml_evalucds) if not evalucd
            ]
            if len(invalid) > 0:
                self.logger.error(
                    f"ERROR: the following columns have unrecognized or unparsable UCDs in table_meta_yaml: {invalid}"
                )
                evaluation_table_meta_yaml = "FAIL"

            # Check if astropy can load the file as a table
            try:
                Table.read(self.file, format="parquet", schema_only=True)
            except Exception:  # TODO Exception is too generic
                self.logger.error(
                    "ERROR: Unable to open as an astropy Table. table_meta_yaml may be improperly formatted, or something else may be wrong."
                )
                evaluation_table_meta_yaml = "FAIL"

            # check units
            if self.unrecognized_unit_warnings:
                unrecognized_unit_reported = False  # initialize
                for unit in table_meta_yaml_units:
                    try:
                        u.Unit(unit)  # try to parse as an astropy unit
                    except ValueError:
                        try:
                            VOUnit.parse(unit)  # try to parse as a VOunit
                        except Exception:  # TODO Exception is too generic
                            if not unrecognized_unit_reported:
                                self.logger.warning(
                                    f"WARNING: {unit} is not a recognized unit in astropy.units or VOUnit, or might be improperly formatted."
                                )
                                unrecognized_unit_reported = True
            else:
                try:
                    for unit in table_meta_yaml_units:
                        try:
                            u.Unit(unit)
                        except ValueError:
                            VOUnit.parse(unit)
                except Exception:  # TODO Exception is too generic
                    self.logger.info(
                        "INFO: unknown and/or deprecated unit warnings were suppressed; the table_meta_yaml convention does not have rules for which units are allowable. To show zealous unit warnings, re-run with unrecognized_unit_warnings = True."
                    )

            self.logger.critical(f"-------> table_meta_yaml validation report: '{evaluation_table_meta_yaml}'")
            print()
        self.evaluations.append(evaluation_table_meta_yaml)

        return evaluation_table_meta_yaml

    def check_keys(self) -> str:
        """
        Check for the presence of other required or optional keys.

        Returns
        -------
        str
            Evaluation string (one of "PASS", "FAIL", "SKIPPED")
        """
        self.logger.critical("Checking for the presence of other required or suggested keys...")

        evaluation_keys = "PASS"  # default to PASS
        fail_or_warning = (
            False  # assess whether guidance about table-level metadata key requirements is needed, default to False
        )

        # Load required and suggested key names from yaml file
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(BASE_DIR, "ccsp_keys.yaml"), "r") as f:
            keynames = yaml.safe_load(f)
        required = keynames["required"]
        conditional = keynames["conditional"]
        conditional_filebased = keynames["conditional_filebased"]
        suggested = keynames["suggested"]

        # Check if votable is handling coosys and timesys
        if "IVOA.VOTable-Parquet.content" not in self.metadata.keys():
            conditional += ["coordinate_reference_frame", "time_scale", "time_reference_position"]
        else:
            try:  # try to open VOTable content
                xml_object = BytesIO(self.metadata["IVOA.VOTable-Parquet.content"].encode("utf-8"))
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UnitsWarning)
                    votable = parse(xml_object, verify="ignore")
            except Exception:  # any exception; invalid voparquet is handled elsewhere
                pass
            else:  # if successfully opened VOTable content, check whether votable is handlign coosys and timesys
                if len(votable.coordinate_systems) == 0:
                    conditional += ["coordinate_reference_frame"]
                if len(votable.time_systems) == 0:
                    conditional += ["time_scale", "time_reference_position"]

        # Check for missing keys

        missing_required = []
        for key in required:
            if key not in self.metadata:
                missing_required.append(key)

        missing_conditional = []
        for key in conditional:
            if key not in self.metadata:
                missing_conditional.append(key)

        missing_conditional_filebased = []
        for key in conditional_filebased:
            if key not in self.metadata:
                missing_conditional_filebased.append(key)

        missing_suggested = []
        for key in suggested:
            if key not in self.metadata:
                missing_suggested.append(key)

        # Report on missing keys

        if len(missing_required) > 0:
            self.logger.error(
                f"ERROR: The following required keys are missing from the key-value metadata dictionary in the FileMetaData structure of the Parquet footer: {missing_required}"
            )
            fail_or_warning = True
            evaluation_keys = "FAIL"

        if len(missing_conditional) > 0:
            self.logger.warning(
                f"WARNING: The following keys, which may be required for some data products, are not present in the key-value metadata dictionary in the FileMetaData structure of the Parquet footer: {missing_conditional}"
            )
            fail_or_warning = True

        if len(missing_conditional_filebased) > 0:
            self.logger.warning(
                f"WARNING: The following keys, which may be required for some file-based products (but not true catalogs), are not present in the key-value metadata dictionary in the FileMetaData structure of the Parquet footer: {missing_conditional_filebased}"
            )
            fail_or_warning = True

        if len(missing_suggested) > 0:
            self.logger.info(
                f"INFO: The following optional keys, which may suggested for some data products, are not present in the key-value metadata dictionary in the FileMetaData structure of the Parquet footer: {missing_suggested}"
            )
            fail_or_warning = True

        if fail_or_warning:
            self.logger.info(
                "INFO: For information about required, conditionally required, and suggested keywords, please see section 3 (for true catalogs) or section 4 (for file-based approaches) of the PIT/CCSP guidelines, especially the table in the expandable under 'Click here to expand table-level metadata requirements.'"
            )

        self.logger.critical(f"-------> Keywords presence validation report: '{evaluation_keys}'")
        print()
        self.evaluations.append(evaluation_keys)

        return evaluation_keys

    @staticmethod
    def validate(*args, **kwargs) -> None:
        """
        Wrapper function creating an instance of the class, running each evaluation function, and summarizing results.

        Parameters
        ----------
        file : str
            Path to the Parquet file being test.

        unrecognized_unit_warnings : bool, optional
            Boolean to enable (over)zealous unit warnings. Defaults to False.

        vo_required : bool, optional
            Boolean to require a VOParquet key in order to PASS a file (defaults to False, meaning that the VOParquet check can be skipped if not present without causing a fail)

        jar_file : str, optional
            Path to the JAR file needed to run parqlint. Defaults to stilts.jar in local directory.

        no_color : bool, optional
            Boolean to turn off color-coded terminal output
        """
        instance = parquet_validator(*args, **kwargs)

        instance.logger.critical(f"Metadata Checker is evaluating {instance.file}...")
        print()

        # Check VOParquet, table_meta_yaml, and keywords
        evaluation_voparquet = instance.validate_voparquet()
        evaluation_table_meta_yaml = instance.validate_table_meta_yaml()
        evaluation_keys = instance.check_keys()

        # Produce summary report
        instance.logger.critical("Overview...")
        instance.logger.critical(f"VOParquet validation report: '{evaluation_voparquet}'")
        instance.logger.critical(f"table_meta_yaml validation report: '{evaluation_table_meta_yaml}'")
        instance.logger.critical(f"Keywords presence validation report: '{evaluation_keys}'")
        if "FAIL" in instance.evaluations:
            overall = "'FAIL'"
        else:
            overall = "'PASS'"
        instance.logger.critical(f"-------> Final verdict: {overall}")
