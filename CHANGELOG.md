# Changelog

## [Unreleased]
### Added
[PR # 32](https://github.com/spacetelescope/mast_contributor_tools/pull/32)
    - Adding option to save filename checker output in altnerate format (csv, fits, excel, html)

### Changed

### Deprecated

### Fixed
[PR # 34](https://github.com/spacetelescope/mast_contributor_tools/pull/34)
    - Addressing bug where file names with more than 9 fields were failing silently and not added to the results file.

### Removed

### Security

## 1.0.1 (2025-11-10)
### Fixed
[PR # 29](https://github.com/spacetelescope/mast_contributor_tools/pull/29)
    - Fixed the repository URL in Documentation
[PR # 28](https://github.com/spacetelescope/mast_contributor_tools/pull/28)
    - Fixed a small bug where the final log statement incorrectly counts the number of files that passed.

## 1.0.0 (2025-10-08)

### Added
[PR # 24](https://github.com/spacetelescope/mast_contributor_tools/pull/24)
    - Added a GitHub Actions workflow to automatically create a release on pushing a tag to main branch
    - Added a readthedocs yaml config file for building docs on readthedocs.org
[PR # 23](https://github.com/spacetelescope/mast_contributor_tools/pull/23)
    - Refactoring file name checker for updated non-boolean verdicts: now 'pass', 'needs review', or 'fail'
    - added 'format_score' field test for better handling of special characters

[PR # 15](https://github.com/spacetelescope/mast_contributor_tools/pull/15)
    - Adding a tutorial with examples for the file name checker

[PR # 14](https://github.com/spacetelescope/mast_contributor_tools/pull/14)
    - Setting up Sphinx Autodoc
    - CI/CD update for docs
[PR # 7](https://github.com/spacetelescope/mast_contributor_tools/pull/7)
    - Adding unit tests for file name checker

[PR # 3](https://github.com/spacetelescope/mast_contributor_tools/pull/3)
    - GitHub CI/CD action
    - pre-commit-hook installation

[PR # 1](https://github.com/spacetelescope/mast_contributor_tools/pull/1)
    - Initial codebase commit for `filename_check`

### Changed
[PR # 24](https://github.com/spacetelescope/mast_contributor_tools/pull/24)
    - pyproject.toml: update author name and some dependencies
    - docs/conf.py: change to sphinx-book-theme from sphinx-rtd-theme
### Deprecated

### Fixed

### Removed

### Security
