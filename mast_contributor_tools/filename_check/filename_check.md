# Filename Check

This application will examine each file within a user-specified directory folder for compliance with the HLSP filename requirements (see the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention)). The results are saved to an SQLite3 database; see [Filename evaluation](#filename-evaluation) for details. Prior to a final delivery of your HLSP collection to MAST, contributors should fix all filenames where reported failures have a severity of 'fatal'. 

## Filename components

File names are divided into **fields** separated by underscores. There can be up to 9 fields, though some fields are optional for certain file semantic types. Fields are evaluated against rules for captalization, special characters, and length; the contents of each field are validated against known values to the extent possible. The results of the evaluation for each field of a file is written to an output database. 

Some fields are composed of **elements**, separated by hyphens. Elements in fields that specify the (observatory, instruments, filters) triplet are checked for consistency with known combinations. The end of the last field is composed of elements delimited by periods, the last one (or two) of which comprise a file extension. 

## Filename evaluation

The results are organized by field, and the fields must appear in a particular order. There are up to N=9 fields defined for each file (see following table). Note that some file content types (e.g. source catalogs, readme file) need not include all fields. 

| Posn | Field | Required | Width | Validation Notes |
| ---- | ----- | -------- | ----- | ---------- |
| 1 | **hlsp** | All | 4 | Match literal string |
| 2 | collection name | All | <20 | must match user-provided acroymn | 
| 3 | observatory | I,S | <20 | multi-element |
| 4 | instrument | I,S | <20 | multi-element |
| 5 | target | I,S | <20 | target names may not include periods |
| 6 | opt element | I,S | <20 | multi-element |
| N-2 | version | I,S,C | <10 | valid syntax: `vX[.Y[.Z]]` |
| N-1 | semantic type | All | <20 chars | should match pre-defined list |
| N | extension type | All | <10 | must match pre-defined list |

The results of the filename evaluation are stored in an SQLite3 database. Each recognized field is evaluated on the following criteria: 

* capitalization and reserved characters
* field length in characters
* position within the filename
* content of the text, if applicable

The evaluation values are one of: pass, fail, or (for field values) unrecognized. 

Failing evaluations do not necessarily indicate a problem. The severity may be 

* **fatal** - correction required
* **not_validated**
* **warning** - correctionn may not be necessary
* **N/A** - no correction necessary

## Calling sequence

This application is normally called from the shell, where `my_hlsp` is the intended identifier in MAST of the HLSP collection. 

> `python file_check.py my-hlsp-name '/path/to/files'`

## Resources

This file name checking app makes use of the following: 

* input tuples of recognized observatory/instrument/filter combinations. Derived from an internal MAST database. Defaults to `obs_filter.db`
* input set of recognized product semantic types and filename extensions
* ouput SQLite3 database of evaluations

The results database may be examined programmatically with python or other languages. It can also be viewed interactively with the  [DB Browser for SQLite](https://sqlitebrowser.org/). 