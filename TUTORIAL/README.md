# MAST Contributor Tools Tutorial

This folder contains a basic tutorial for the `mast_contributor_tools` package to try out the code for yourself and follow along!

## Installation

For full installation instructions, refer to the [`README.md`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/README.md) file at the top-level of this repository. This package is installable via pip and can be installed using this command from the top-level folder of this repository:

```shell
pip install .
```

You can check if your installation was successful by starting a python session and importing the pacakge:

```python
python
>>> import mast_contributor_tools
```

If this imports successfully, you are ready to go!

# TUTORIAL 1: Filename Checker

## Introduction 
The filename checker is an automated way to test if your data filenames are compliant with the [HLSP filenaming policies](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention). 

The [Filename Checker Guide](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/docs/filename_check_readme.md) included in this repository contains full instructions on how to use the Filename Checker, so please refer to that for more detailed information! This folder contains a basic tutorial to follow-along and learn how to use the file name checker, but the [Filename Checker Guide](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/docs/filename_check_readme.md) is the best resource for more general appplications.

## Step 1: Investigating the Tutorial data.

The [`tutorial-data/`](tutorial-data/) folder included in this tutorial contains several example files that you can use for testing. Take a look in that folder and familiarize yourself with its contents! This folder contains 3 different files, for a hypothetical HLSP named "mct-tutorial". 

There are three different fake fits files containing spectra for different hypothetical galaixes:

- `hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits`
- `hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits`
- `hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits` 

One catalog file containing measurements from those galaxies:
- `hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits`

And one README file describing our fake HLSP:
- `hlsp_mct-tutorial_readme.txt`

Note that these files are totally empty and are just used for the purpose of this tutorial.

## Step 2: Use the --help command to learn about the options

Using the `--help` flag is a great option if you need to remind yourself how to run the file name checker:

```shell
mct check_filenames --help
```

This will print information in your terminal about the available options for this command!

## Step 3: Check an Individual File Name

Let's check the validity of a single file name using the `check_filename` command. The syntax to use for this is:

```shell
mct check_filename {FILE NAME}
```

We will show one example which passes, and one which fails!

### Step 3a: An example file name which passes

Run this command to check the file name of one of the spectra files:

```shell
mct check_filename hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits
```

The code will run, print out some basic information, and let you know that this filename gets a score of:

```
Final Score: PASS
```

### Step 3b: An example file name which fails

Next, here's an example of a file name which fails validation. HLSP filenames are required to be all-lowercase, so we can use some uppercase characters in our file name to check this:

```shell
mct check_filename HLSP_mct-tutorial_JWST_nirspec_GALAXY1_multi_v1_spec.fits
```

You should see that this filename will recieve:

```
Final Score: FAIL
```

But why did it fail? You can use the verbose flag (`-v`) to investigate and learn more information:

```shell
mct check_filename -v HLSP_mct-tutorial_JWST_nirspec_GALAXY1_multi_v1_spec.fits
```
This will print out a lot more information than the previous command, but specifically, it will show that this filename failed because the "`HLSP`", "`JWST`", and "`GALAXY1`" parts recieved a `capitalization_score: fail`.

## Step 4: Check all file names in a directory

Checking one filename at a time is useful for troubleshooting, but a more common application would be to check all files in a directory at the same time. 

The synatax to use for this is:

```shell
mct check_filenames {HLSP-NAME}
```

which will check all of the files in the current directory be default, but you can also specific a directory path with the `--directory={directory-path}` option.

Use this command to run the filename checker against everything in the [`tutorial-data/`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/TUTORIAL/tutorial-data/) directory:

```shell
mct check_filenames mct-tutorial --directory='tutorial-data/'
```

You should receieve an output message that 5 files were checked, and that all files passed!

Congratulations! You have completed this tutorial and now know the basic usage of the MAST Contributor's Tools Filename Checker.


# Additional Resources
More tutorials will be added here in the future! In the meantime, check out the following links for more useful information:

- [HLSP Contributor Guide](https://outerspace.stsci.edu/display/MASTDOCS/HLSP+Contributor+Guide) - Full documentation, instructions, and policies about the process of submitting an HLSP to MAST.
- [MAST Help Desk](https://outerspace.stsci.edu/display/MASTDOCS/Archive+Support) - Please contact the help desk or send an email to [mast_contrib.stsci.edu](mailto:mast_contrib.stsci.edu) if you have any questions about using this package!


