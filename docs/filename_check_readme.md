# Filename Check

This application will examine each file within a user-specified directory folder for compliance with the HLSP filename requirements. Refer to the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for details. The results are saved to an SQLite3 database. Prior to a final delivery of a HLSP collection to MAST, contributors should fix all filenames where reported failures have a severity of 'fatal'.

**Note:** Once your HLSP collection has been delivered to MAST, this same tool will be used to re-validate the product filenames. MAST staff will contact you to resolve issues.

## Calling sequence

This application can be called from the command line using the `mct` command. To view information on the arguments and options for this command, you can use:

```shell
mct check_filenames --help
```

The various options for this command are described below:

| Flag                       | Description                                                                | Default Value                      |
| ---------------------------| -------------------------------------------------------------------------- | ---------------------------------- |
| `-dir` or `--directory` | Path of HLSP directory tree; tests files in that directory                    | `'.'`, the current directory       |
| `-p` or `--pattern`     | File pattern to limit testing, for example '*.fits' to only check the fits files | `'*.*'` for all files           |
| `-e` or `--exclude`     | File pattern to exclude from testing, for example '*.jpg' to test all files except the jpgs | None                 |
| `-n` or `--max_n`       | Maximum number of files to check, for testing purposes.                       | None (all files)                   |
| `-db` or `--dbFile`     | Name of Results database file                                                 | `results_<hlsp_name>.db`           |
| `-v` or `--verbose`     | Enables verbose output for more information                                   | `False`                            |
| `--help`                | Prints information about this command                                         |                                    |


### Example Usage: Check all files in the current directory

To check all files in the current working directory, run the command:

```
mct check_filenames <my-hlsp>
```

where `<my-hlsp>` is the name of your HLSP.

This command is also equivalent to:

```
mct check_filenames my-hlsp -dir='.' -p='*.*' --dbFile='results_my-hlsp.db'
```

### Example Usage: Check all files matching a pattern in a specified directory

To check all files in a specified directory matching a certain file pattern:

```
mct check_filenames my-hlsp --directory='/path/to/hlsp-directory/' --pattern='*.fits'
```

This example will only check files ending with ".fits" in the directory "/path/to/hlsp-directory/"


You can also use this to check a subdirectory of the current directory, for example:

```
mct check_filenames my-hlsp --directory='subdir/' --pattern='*.fits'
```


### Example Usage: Test a single filename

If you only want to test a single filename, use the `check_filename` command instead:

```
mct check_filename hlsp_my-hlsp_readme.md
```

The file name does not have to be a real file; it is tested as a string. You can also call this command on multiple file names at once using the syntax `mct check_filename [FILE 1] [FILE 2] [FILE 3] ...`: For example:

```
mct check_filename hlsp_my-hlsp_hst_wfc3_multi_galaxy1_v1_spec.fits hlsp_my-hlsp_hst_wfc3_multi_galaxy2_v1_spec.fits
```

### Resources

The file name checking application makes use of the following:

* input: yaml file of observatory/instrument/filter combinations
* input: yaml file of recognized product semantic types (e.g., `spec`, or `drz`)and filename extensions (e.g., `fits`, `png`)
* output: SQLite3 file to store the database of evaluations

## Filename components
Names of science files must follow the naming scheme described below.

`hlsp_proj-id_observatory_instrument_target_opt-elem_version_product-type.extension`

File names are divided into **fields** separated by underscores (`_`). There can be up to 9 fields, though some fields are optional for certain file semantic types. Fields are evaluated against rules for captalization, special characters, and length; the contents of each field are validated against known values to the extent possible. The results of the evaluation for each field of a file is written to an output database.

Some fields are composed of **elements**, separated by hyphens (e.g., `lmc-flows`,`hst-jwst`, `acs-wfc3`, or `f160w-f335m-f444w`). Elements in fields that specify the (observatory, instruments, filters) triplet are checked for consistency with known combinations. For instance, if observatory is `jwst` only, `wfc3` and `f775w` cannot be the instrument and filter field values respectively. Refer to the `mast_contributor_tools/filename_ckeck/oif.yaml` file for the list of the combinations. The end of the last field is composed of elements delimited by periods, the last one (or two) of which comprise a file extension.

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

The evaluation values are one of `pass`, `fail`, or (for field values) `review` and `unrecognized`.

Failing evaluations do not necessarily indicate a problem. The severity is one of:

* **fatal** - correction required
* **unrecognized** - value is not recognized. This is often unavoidable and correct, e.g. for new product types or instruments whose data we haven't ingested before. Please consult with MAST staff for review.
* **warning** - correction may not be necessary
* **N/A** - no correction necessary

The results database may be examined programmatically with python or other languages. We recommend viewing it interactively with the [DB Browser for SQLite](https://sqlitebrowser.org/). The database contains three tables:

* filename - file path, name, number of fields, status
* fields - field attributes for each filename, and evaluation
* potential_problems (view) - selects all instances where an error, warning, or unrecognized value was identified. Non-fatal warnings and unrecognized values are not always real problems; these will be reviewed by MAST staff.

The **potential_problems** view may be filtered to select only fatal errors.
