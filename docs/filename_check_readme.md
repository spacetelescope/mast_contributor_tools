# Filename Check

This application will examine each file within a user-specified directory folder for compliance with the HLSP filename requirements. Refer to the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for documentation on the full requirements. The results are saved to an SQLite3 database. Prior to a final delivery of a HLSP collection to MAST, contributors should fix all filenames where reported failures have a `final_verdict` of `FAIL`. A verdict of `NEEDS REVIEW` is usually the result of an unrecognized value, which are often necessary and good, but require review by MAST staff.

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
| `-file` or `--from_file` | Path to a text file containing a list of filenames to check, instead of scanning a directory | None; the default mode is to scan a directory
| `-p` or `--pattern`     | File pattern to limit testing, for example '*.fits' to only check the fits files | `'*.*'` for all files           |
| `-e` or `--exclude`     | File pattern to exclude from testing, for example '*.jpg' to test all files except the jpgs | None                 |
| `-n` or `--max_n`       | Maximum number of files to check, for testing purposes.                       | None (all files)                   |
| `-db` or `--dbFile`     | Name of Results database file                                                 | `results_<hlsp_name>.db`           |
| `-v` or `--verbose`     | Enables verbose output for more information                                   | `False`                            |
| `--help`                | Prints information about this command                                         |                                    |

A step-by-step tutorial for learing how to use the file name checker can be found in the [`TUTORIAL/`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/TUTORIAL/tutorial_readme.md) folder.

### Example Usage: Check all files in the current directory

To check all files in the current working directory, run the command:

```shell 
mct check_filenames <my-hlsp>
```

where `<my-hlsp>` is the name of your HLSP.

This command is also equivalent to:

```shell 
mct check_filenames my-hlsp -dir='.' -p='*.*' --dbFile='results_my-hlsp.db'
```

### Example Usage: Check all files matching a pattern in a specified directory

To check all files in a specified directory matching a certain file pattern:

```shell 
mct check_filenames my-hlsp --directory='/path/to/hlsp-directory/' --pattern='*.fits'
```

This example will only check files ending with ".fits" in the directory "/path/to/hlsp-directory/"


You can also use this to check a subdirectory of the current directory, for example:

```shell 
mct check_filenames my-hlsp --directory='subdir/' --pattern='*.fits'
```

### Example Usage: Check all files supplied in a file list

If the files do not exist yet or no directory path is available, you can also supply a text file containing a list of file names to check using the `--from-file` option: 

```shell 
mct check_filenames my-hlsp --from_file='/path/to/file_list.txt'
```

In this example, the contents of `file_list.txt` should be a text file with one file name on each line. For example:
``` 
file1.fits
file2.fits
file3.fits
...
```

### Example Usage: Test a single filename

If you only want to test a single filename, use the `check_filename` command instead:

```shell 
mct check_filename hlsp_my-hlsp_readme.md
```

The file name does not have to be a real file; it is tested as a string. You can also call this command on multiple file names at once using the syntax `mct check_filename [FILE 1] [FILE 2] [FILE 3] ...`: For example:

```shell 
mct check_filename hlsp_my-hlsp_hst_wfc3_multi_galaxy1_v1_spec.fits hlsp_my-hlsp_hst_wfc3_multi_galaxy2_v1_spec.fits
```

### Resources

The file name checking application makes use of the following:

* input: yaml file of observatory/instrument/filter combinations
* input: yaml file of recognized product semantic types (e.g., `spec`, or `drz`)and filename extensions (e.g., `fits`, `png`)
* output: SQLite3 file to store the database of evaluations

## Filename components

Names of science files must follow the naming scheme described below. File names are typically divided into 9 **fields** separated by underscores (`_`). 

```html
hlsp_<proj-id>_<observatory>_<instrument>_<target>_<opt-elem>_<version>_<product-type>.<extension>
```

where the fields are defined as follows. Refer to the [HLSP Contributor Guide](https://outerspace.stsci.edu/display/DraftMASTCONTRIB/File+Naming+Convention+for+HLSPs) for more detail.


| Field | Description | Example Values |
| ---------------------------| -------------------------------------------------------------------------- | ---------------------------------- |
| `hlsp` | A literal string that identifies the file as a community-contributed data product | `hlsp` |
| `<proj-id>` | An agreed upon acronym or initializm for the HLSP collection. This name is also used in MAST as a directory name and as a database keyword. This field may contain a hyphen. | `candels`, `jades`, `phangs`, `rocky-worlds`, `tica`, `ulysses`, `wide` |
| `<observatory>` | Observatory or mission used to acquire the data, or for which the data were simulated. May include multiple elements If multiple observatories were used. | `hst-iue`, `galex`, `jwst`, `tess`|
| `<instrument>` | Name of Instrument used to obtain the data, or for which the data were simulated. May include multiple elements if multiple instruments were used. When not applicable (e.g. for GALEX data), use a descriptive tag like img or spec. | `nircam`, `cos-stis` |
| `<target>` | Field name or target as designated by the team, or as a general identifier where a specific target designation is not relevant. Parts, counter numbers, and epochs are allowed in this field and should be separated by hyphens. May include hyphen, period, and plus sign. | `m57`, `m101-ep1`, `m101-ep2`, `ngc1385`, `obj-123`, `j152447.75-p041919.8`|
| `<opt-elem>` | Names of optical element(s) (i.e., filter or disperser) used to obtain the data. May include field elements if multiple filters/dispersers were used. Clear or empty filter elements need not be included. | `f606w`, `f606w-f814w`, `ugriz`, `multi`|
| `<version>` | Version designation used by the team for the HLSP delivery, Versions in the file name may relate in some way to data release or software versions, but ultimately they must represent the version of a file, and must be incremented with any delivery that replaces that file. The value must begin with the literal "v" and contain an alphanumeric value, with the syntax vX[.Y[.Z]] where X and Y are numeric values with up to 2 digits, X cannot have a leading zero, and Z is alphanumeric (a-z,0-9) up to 2 characters. | `v2`, `v1.2.2a`|
| `<product-type>` | Type of data as designated by the team (models/simulations can be indicated here). Use a widely recognized type. Be sure to distinguish products of similar type, possibly by using a simple compound type. e.g., a photometric catalog (phot-cat) vs. a catalog of simulated object morphologies (sim-cat). Hyphens are allowed for compound product types. | `img`, `cat`, `drz`, `lc`, `model-spec`, `sci`, `spec`, `spec2d`, `wht`, `sim-img`, `map`|
| `<extension>` | Standard extension name for the file format, which must include standard notation for compression if applicable. | `.asdf`, `.txt`., `.md`, `.png`, `.fits`, `.fits.gz`|

For each file name, the fields are evaluated against four criteria: captalization, character Length: each field has a maximum character length, format, and value, which are described in detail in the next section of thie README ("Filename evaluation").

The results of the evaluation for each field of a file name is written to an output database.

Some fields are composed of **elements**, separated by hyphens (e.g., `lmc-flows`,`hst-jwst`, `acs-wfc3`, or `f160w-f335m-f444w`). Elements in fields that specify the (observatory, instruments, filters) triplet are checked for consistency with known combinations. For instance, if observatory is `jwst` only, `wfc3` (an HST instrument) and `f775w` (an HST filter) cannot be the instrument and filter field values respectively. Refer to the [`mast_contributor_tools/filename_ckeck/oif.yaml`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/mast_contributor_tools/filename_check/oif.yaml) file for the list of currently-recognized combinations. 

## Filename evaluation

The results are organized by field, and the fields must appear in a particular order. There must be at least 4, and may be as many as 9 fields defined for each file. Note that some file content types (e.g. source catalogs, readme file) need not include all fields. 

See the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for detailed rules. The results of the filename evaluation are stored in an SQLite3 database. Each recognized field is evaluated on the following criteria:

- Captalization: the filename must be all lower case.
- Character Length: each field has a maximum character length.
- Format: checks overall format and special characters: for example, a period `.` is allowed in the `<version>` field but not in the `<proj-id>`. Certain fields allow hyphen-separated elements. Most fields must begin and end with an ASCII alpha-numeric character.
- Value: In some cases, the contents of each field are validated against known values to the extent possible.

The evaluation scores for individual fielda and the overall file names are one of `PASS`, `NEEDS REVIEW` or `FAIL`. A verdict of `NEEDS REVIEW` is usually the result of an unrecognized value. This is often necessary and correct, e.g. for new product types or instruments whose data we haven't ingested before. Please consult with MAST staff for review.


## Reading the Results

The results are written out in a database file (named `results_<proj-id>.db`). The database may be examined programmatically with python or other languages. We recommend viewing it interactively with the [DB Browser for SQLite](https://sqlitebrowser.org/). The database contains three tables:

* filename - file path, name, number of fields, status
* fields - field attributes for each filename, and evaluation
* potential_problems (view) - selects all instances where an 'fail', or 'needs review' value was identified. Non-fatal warnings and unrecognized values are not always real problems; these will be reviewed by MAST staff.

The **potential_problems** view may be filtered to select only fatal errors.
