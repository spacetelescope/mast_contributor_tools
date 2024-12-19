# Filename Check

This application will examine each file within a user-specified directory folder for compliance with the HLSP filename requirements. See the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for details. The results are saved to an SQLite3 database. Prior to a final delivery of a HLSP collection to MAST, contributors should fix all filenames where reported failures have a severity of 'fatal'.

**Note:** Once your HLSP collection has been delivered to MAST, this same tool will be used to re-validate the product filenames. MAST staff will contact you to resolve issues.

## Calling sequence

This application is normally called from the shell, where `my-hlsp-name` is the intended identifier in MAST of the HLSP collection.

> `python fc_app.py my-hlsp-name '/path/to/files'`

The *hlsp_filename* module itself has an entry point that will evaluate any string as an HLSP filename (except for matching the HLSP collection name). It may be useful to test a set of sample files before creating too many collection files to ensure that they will be compliant.

> `python __main__.py hlsp_my-file-name_readme.md`

### Resources

The file name checking app makes use of the following:

* input: yaml file of observatory/instrument/filter combinations
* input: yaml file of recognized product semantic types (e.g., `spec`, or `drz`)and filename extensions (e.g., `fits`, `png`)
* output: SQLite3 file to store the database of evaluations

## Filename components
Names of science files must follow the naming scheme described below.

>hlsp_proj-id_observatory_instrument_target_opt-elem_version_product-type.extension

File names are divided into **fields** separated by underscores. There can be up to 9 fields, though some fields are optional for certain file semantic types. Fields are evaluated against rules for captalization, special characters, and length; the contents of each field are validated against known values to the extent possible. The results of the evaluation for each field of a file is written to an output database.

Some fields are composed of **elements**, separated by hyphens (e.g., `lmc-flows`,`hst-jwst`, `acs-wfc3`, or `f160w-f335m-f444w`). Elements in fields that specify the (observatory, instruments, filters) triplet are checked for consistency with known combinations. For instance, if observatory is `jwst` only, `wfc3` and `f775w` cannot be the instrument and filter field values respectively. The end of the last field is composed of elements delimited by periods, the last one (or two) of which comprise a file extension.

## Filename evaluation

The results are organized by field, and the fields must appear in a particular order. There must be at least 4, and may be as many as 9 fields defined for each file. Note that some file content types (e.g. source catalogs, readme file) need not include all fields. Some general rules apply:

* filenames and relative paths must be lower-case
* most fields must begin and end with an ASCII alpha-numeric character
* certain fields allow hyphen-separated elements
* length limits apply to each field

See the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for detailed rules. The results of the filename evaluation are stored in an SQLite3 database. Each recognized field is evaluated on the following criteria:

* capitalization and reserved characters
* field length in characters
* content of the text, if applicable

The evaluation values are one of `pass`, `fail`, or (for field values) `unrecognized`.

Failing evaluations do not necessarily indicate a problem. The severity is one of:

* **fatal** - correction required
* **unrecognized** - value is not recognized
* **warning** - correctionn may not be necessary
* **N/A** - no correction necessary

The results database may be examined programmatically with python or other languages. We recommend viewing it interactively with the [DB Browser for SQLite](https://sqlitebrowser.org/). The database contains three tables:

* filename - file path, name, number of fields, status
* fields - field attributes for each filename, and evaluation
* problems (view) - selects all instances where an error or warning was identified

The **problems** view may be filtered to select only fatal errors.
