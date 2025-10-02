# MAST_CONTRIBUTOR_TOOLS
This package contains a set of tools for use by MAST community contributors preparing High Level Science Products (HLSP) or MAST Community Contributed Missions (MCCM) data collections. It is a work in progress. Currently, `Filename Check` is available, and `Metadata Check` will be coming soon.

Visit the [HLSP Contributor Guide](https://outerspace.stsci.edu/display/MASTDOCS/HLSP+Contributor+Guide) for full documentation, instructions, and policies about the process of submitting data to MAST.

## Development Workflow
There are two main branches for mast_contributor_tools work:

- The **dev** branch contains ongoing development work. All new work should be done in branches that are merged into **dev**.

- The **main** branch contains the latest stable release of `mast_contributor_tools`.

- MAJOR.MINOR.PATCH versioning is used for releases. New features and bug fixes are merged into **dev** and released to **main** as new versions when ready. Refer to [Semantic versioning](https://semver.org/) for more details, but in brief:
    - MAJOR version: Big changes, breaking changes
    - MINOR version: New features, backwards compatible
    - PATCH version: Bug fixes, backwards compatible
    - New releases are tagged in git with the version number, e.g. `v1.0.0`.
    - Release notes are maintained in the `CHANGELOG.md`

## Installation
### Required packages and versions
- See required packages found in the [conda evn file](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/envs/mct_env.yml) or [pyproject.toml](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/pyproject.toml).

### Conda environment
Replace `env_name` with the desired name for your environment.
- In the terminal, run the following commands.


```shell
conda create -n env_name python=3.11
conda activate env_name
```

### mast_contributor_tools
#### Installation for regular users
The **mast_contributor_tools** directory contains the python package itself, which can be installable via pip. This will also install the core dependencies defined in `pyproject.toml`.
```shell
pip install .
```
#### Installation for developers
If you are interested in developing and contributing to **mast_contributor_tools**, you should install this package with `-e` flag, it allows you to work on the package's source code and see changes reflected immediately without needing to reinstall.

```shell
pip install -e . # install editable mode
```
To install the optional dependencies for pytest or Sphinx autodoc, run the command below in addition to the `pip install` command in editable mode above.

```shell
pip install -e .[dev,test,docs] # install the dependencies of dev, test, docs
```
or
```shell
pip install .[all] # "all" includes the dependencies of dev, test, docs
```

### (Optional for Development) VSCode settings.json

If you decide to use VSCode for your development, you can use the **.vscode/settings.json**. You should choose your python interpreter locally by setting your conda environment.

## pre-commit for development

[pre-commit](https://pre-commit.com/) allows all collaborators push their commits compliant with the same set of lint and format rules in **pyproject.toml** by checking all files in the project at different stages of the git workflow. It runs commands specified in the **.pre-commit-config.yaml** config file and runs checks before committing or pushing, to catch errors that would have caused a build failure before they reach CI.

### Install pre-commit
You will need to install `pre-commit` manually.
```bash
pip install pre-commit # if you haven't already installed the package
```

```bash
pre-commit install # install default hooks, `pre-commit`, `pre-push`, and `commit-msg`, as specified in the config file.
```

If this is your first time running, you should run the hooks against for all files and it will fix all files based on your setting.
```bash
pre-commit run --all-files
```
Finally, you will need to update `pre-commit` regularly by running
```bash
pre-commit autoupdate
```
For other configuration options and more detailed information, check out at the [pre-commit](https://pre-commit.com/) page.

### Testing

This package includes a test suite built with `pytest`. After installing, you can ensure the code is working correctly by running:

```
pytest
```

This command will run all test scripts in the `tests` directory and output the results. Each `.py` file in the source code directory has a corresponding `test_*.py` file in the tests directory. The tests can also be called on a single file, for example:

```
pytest tests/filename_check/test_hlsp_filename.py
```
### Sphinx documentation set up
Sphinx will create the documentation automatically using the module docstrings.
Use `sphinx-apidoc` to automatically generate API documentation from your docstrings.

Run this command in the main project level,
```shell

sphinx-apidoc -o docs/api mast_contributor_tools mast_contributor_tools/tests/* # the last pattern indicates all test modules excluded from API Doc
```
For one time build,
```shell
make -C docs html
```

Then navigate to `docs/_build/html` and open `index.html` on your browser to see the built documentation.

To build live-reload documentation, run the following command. You need to open a web browser and enter the URL that sphinx-build serves to veiw the live, auto-updating Sphinx docs, for instance, `http://127.0.0.1:8000`.

```shell
sphinx-autobuild docs docs/_build/html
```

To remove existing output,

```shell
make clean
```


## Quick Start
### Tutorials

The [`TUTORIAL/`](https://github.com/spacetelescope/mast_contributor_tools/tree/dev/TUTORIAL/) folder of this repository contains some example data and step-by-step instructions for how to run this code.

### Filename Check
To check if the filenames comply with the [HLSP filenaming convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention), please refer to [Filename Checker Guide](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/docs/filename_check_readme.md) to get started.

### Metadata Checker

Under development - check back later!

# License

This project is Copyright (c) MAST Staff and licensed under
the terms of the BSD 3-Clause license. This package is based upon
the `Openastronomy packaging guide <https://github.com/OpenAstronomy/packaging-guide>`
which is licensed under the BSD 3-clause licence. See the licenses folder for
more information.

# Contributing

We love contributions! mast_contributor_tools is open source,
built on open source, and we'd love to have you hang out in our community.

**Imposter syndrome disclaimer**: We want your help. No, really.

There may be a little voice inside your head that is telling you that you're not
ready to be an open source contributor; that your skills aren't nearly good
enough to contribute. What could you possibly offer a project like this one?

We assure you - the little voice in your head is wrong. If you can write code at
all, you can contribute code to open source. Contributing to open source
projects is a fantastic way to advance one's coding skills. Writing perfect code
isn't the measure of a good developer (that would disqualify all of us!); it's
trying to create something, making mistakes, and learning from those
mistakes. That's how we all improve, and we are happy to help others learn.

Being an open source contributor doesn't just mean writing code, either. You can
help out by writing documentation, tests, or even giving feedback about the
project (and yes - that includes giving feedback about the contribution
process). Some of these contributions may be the most valuable to the project as
a whole, because you're coming to the project with fresh eyes, so you can see
the errors and assumptions that seasoned contributors have glossed over.

Note: This disclaimer was originally written by
`Adrienne Lowe <https://github.com/adriennefriend>`_ for a
`PyCon talk <https://www.youtube.com/watch?v=6Uj746j9Heo>`_, and was adapted by
mast_contributor_tools based on its use in the README file for the
`MetPy project <https://github.com/Unidata/MetPy>`_.

# Additional Resources

For more useful information, check out the following links:

- [HLSP Contributor Guide](https://outerspace.stsci.edu/display/MASTDOCS/HLSP+Contributor+Guide) - Full documentation, instructions, and policies about the process of submitting an HLSP to MAST.
- [MAST Help Desk](https://outerspace.stsci.edu/display/MASTDOCS/Archive+Support) - Please contact the help desk or send an email to [mast_contrib@stsci.edu](mailto:mast_contrib@stsci.edu) if you have any questions about using this package!
