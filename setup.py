#!/usr/bin/env python
from setuptools import find_packages, setup  # type: ignore

setup(
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
)
