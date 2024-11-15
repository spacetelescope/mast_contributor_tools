# MAST_CONTRIBUTOR_TOOLS
This package contains a set of tools for use by MAST community contributors ((High Level Science Products and MAST Community Contributed Missions).

## Development Workflow
There are two main branches for mast_contributor_tools work:

- The **dev** branch contains ongoing development work and all new work should be done in branches that are merged against **dev**.

- The **main** branch contains the latest stable release of `mast_contributor_tools`.

## Installation
### Required packages and versions
- See required packages found in the [conda evn file](envs/mct_env.yml) or [pyproject.toml](pyproject.toml).

### Conda env installation
Change `env_name` below with whatever you want to name the environment.
- Download the conda installation yml file [here](envs/mct_env.yml).
- In the terminal, run these commands.

```shell
conda env create -n env_name -f mct_env.yml
conda activate env_name
```

### (Optional for Development) VSCode settings.json

If you decide to use VSCode for your development, you can use the [workspace settings.json](.vscode/settings.json). You should choose your python interpreter locally by setting your conda environment.

### mast_contributor_tools installation
The `mast_contributor_tools` directory contains the python package itself, installable via pip.
```shell
pip install -e .
```
## pre-commit for development

[pre-commit](https://pre-commit.com/) allows all collaborators push their commits compliant with the same set of lint and format rules in [pyproject.toml](pyproject.toml) by checking all files in the project at different stages of the git workflow. It runs commands specified in the [.pre-commit-config.yaml](.pre-commit-config.yaml) config file and runs checks before committing or pushing, to catch errors that would have caused a build failure before they reach CI.

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


## Quick Start
### Filename Check
To check if the filenames are compliant with the [HLSP filenaming convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention), please see [the Filename Check Guide](mast_contributor_tools/filename_check/filename_check.md) to get started.

### Metadata Check
# License


This project is Copyright (c) MAST Staff and licensed under
the terms of the BSD 3-Clause license. This package is based upon
the `Openastronomy packaging guide <https://github.com/OpenAstronomy/packaging-guide>`_
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
