# Reading the File Name Checker Results: Tutorial for SQLite files
This tutorial will provide a brief overview for how to open and use SQLite files, which will be produced upon running the filename checker on your fileset. Please refer to the [`Filename Check README`](../docs/filename_check_readme.md) for additional information about running the filename checker. If this is the first time you've used the Filename Checking software, you may want to run through the [`TUTORIAL README`](../TUTORIAL/tutorial_readme.md) first to familiarize yourself with the process and the SQLite files the software produces.

## Reading and Interacting with SQLite files
Assuming you've run through the tutorial and completed [**STEP 4b**](../TUTORIAL/tutorial_readme.md#step-4b:-check-all-file-names-in-a-directory), you should have a `results_mct-tutorial.db` file in the [`TUTORIAL/`](../TUTORIAL/) folder now. You can interact with this file in any way you prefer, but we suggest you:

### View with the [DB Browser for SQLite](https://sqlitebrowser.org/)
Once you've downloaded and installed the DB Browser, open it and select `Open Database` and then navigate to the folder in which your results database resides. Select and open the corresponding DB file. Your window should look something like what is shown in Figure 1:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_Initial_Open_DB.png "Figure 1")

Similar to Figure 1, you should now be seeing the `Database Structure` tab highlighted, with a few tables populating the left panel. Those tables are `fields` and `filename`. If you click on the arrows next to the two table names, you should see the names of the columns that belong to each table. There is also a `Views` heading where you can find the `problems` view, which highlights all potential problem fields within the `fields` table.

If you now click on the `Browse Data` tab next to the `Database Structure` tab, you'll be able to view the table itself, which should have the `fields` table selected near the top left hand corner of the window displayed in Figure 2:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_Table_Data_View.png "Figure 2")

The `fields` table contains the results of the filename check for every single field within each filename analyzed. For instance, if you checked 5 filenames with 9 fields each, the `fields` table should have 5*9 = 45 rows. Meanwhile, the `filename` table (which you can access by clicking on the Table box below the tabs and to the left), contains one row per file, indicating the verdict of the filename check on that filename. Finally, the `potential_problems` table lists all potential problems indicated in the `fields` table.

Within the `fields` table, your files are evaluated as follows (see [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for more details):

- Capitalization: the filename must be all lower case.
- Character Length: each field has a maximum character length.
- Format: checks overall format and special characters: for example, a period `.` is allowed in the `<version>` field but not in the `<proj-id>`. Certain fields allow hyphen-separated elements. Most fields must begin and end with an ASCII alpha-numeric character.
- Value: In some cases, the contents of each field are validated against known values to the extent possible.

The evaluation scores for individual fields and the overall filenames are one of `PASS`, `NEEDS REVIEW` or `FAIL`. A verdict of `FAIL` means that filename or individual field does not follow our filenaming convention (it breaks one of the above rules) and it must be changed before it will be accepted by MAST. Please review which field(s) have been scored as `FAIL` and update them to match the Capitalization, Character Length, Format, and/or Value rules. A verdict of `NEEDS REVIEW` is usually the result of an unrecognized value. This is often necessary and correct, e.g. for new product types or instruments whose data we haven't ingested before. Please consult with MAST staff (mast_contrib@stsci.edu) for review.

Within the `filename` table (`Browse Data` tab, then select table `filename` in the top left box), each filename is listed with the overall status (automatically set to the most critical of `PASS`, `NEEDS REVIEW` or `FAIL`) as well as the number of elements identified in the filename. An example is shown below in Figure 3:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_filename_Table_View.png "Figure 3")

Finally, there's the `problems` table. You can access this table using the same dropdown menu in the top left corner of the window. This table contains all filenames that could have problems, from those that need review to those that fail. An example of this table is shown in Figure 4 below. You may have to modify the window size/click and drag the window dividers to view all columns within the Browser:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_potential_problems_Table_View.png "Figure 4")

Again, please see [`filename_check_readme.md`](../docs/filename_check_readme.md) for how to run the filechecker or the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for detailed rules.

### Opening the SQLite file with Python

An alternative way to read and interact with the DB file is to open it in Python. This might be useful for large HLSPs with many files, or if you want to explore the results programmatically.

For instance, if you want to get the full list of tables and views available to query, you can use the following Python code:

```python
# load sqlite3 and pandas module
import sqlite3
import pandas as pd

# modify the path to reflect the relative path of your results_mct-tutorial.db file
dbfile = '/relative/path/to/results_mct-tutorial.db'

# Open the file using sqlite3
conn = sqlite3.connect(dbfile)

# Convert the various tables into pandas dataframes:
file_evaluations = pd.read_sql_query("SELECT * FROM filename", conn)
field_evaluations = pd.read_sql_query("SELECT * FROM fields", conn)
potential_problems = pd.read_sql_query("SELECT * FROM potential_problems", conn)

# Print to see what the results look like:
print(file_evaluations)
```

|    | path   | filename                                                      | final_verdict   |   n_elements |
|---:|:-------|:--------------------------------------------------------------|:----------------|-------------:|
|  0 | .      | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | NEEDS REVIEW    |            9 |
|  1 | .      | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | PASS            |            9 |
|  2 | .      | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | PASS            |            9 |
|  3 | .      | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | PASS            |            9 |
|  4 | .      | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | PASS            |            9 |
|  5 | .      | hlsp_mct-tutorial_readme.txt                                  | PASS            |            4 |

```python
print(field_evaluations)
```

|    | file_ref                                                      | name         | value        |   nfield | capitalization_score   | length_score   | format_score   | value_score   | nfield_score   | field_verdict   |
|---:|:--------------------------------------------------------------|:-------------|:-------------|---------:|:-----------------------|:---------------|:---------------|:--------------|:---------------|:----------------|
|  0 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | hlsp_str     | hlsp         |        1 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  1 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | hlsp_name    | mct-tutorial |        2 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  2 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | mission      | jwst         |        3 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  3 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | instrument   | nirspec      |        4 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  4 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | target_name  | galaxy3      |        5 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  5 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | filter       | multi        |        6 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  6 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | version_id   | v1           |        7 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  7 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | product_type | a-spec       |        8 | pass                   | pass           | pass           | needs review  | pass           | NEEDS REVIEW    |
|  8 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits   | extension    | fits         |        9 | pass                   | pass           | pass           | pass          | pass           | PASS            |
|  9 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | hlsp_str     | hlsp         |        1 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 10 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | hlsp_name    | mct-tutorial |        2 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 11 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | mission      | jwst         |        3 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 12 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | instrument   | nirspec      |        4 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 13 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | target_name  | galaxy3      |        5 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 14 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | filter       | multi        |        6 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 15 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | version_id   | v1           |        7 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 16 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | product_type | spec         |        8 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 17 | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_spec.fits     | extension    | fits         |        9 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 18 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | hlsp_str     | hlsp         |        1 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 19 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | hlsp_name    | mct-tutorial |        2 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 20 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | mission      | jwst         |        3 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 21 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | instrument   | nirspec      |        4 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 22 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | target_name  | all-galaxies |        5 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 23 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | filter       | multi        |        6 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 24 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | version_id   | v1           |        7 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 25 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | product_type | cat          |        8 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 26 | hlsp_mct-tutorial_jwst_nirspec_all-galaxies_multi_v1_cat.fits | extension    | fits         |        9 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 27 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | hlsp_str     | hlsp         |        1 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 28 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | hlsp_name    | mct-tutorial |        2 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 29 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | mission      | jwst         |        3 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 30 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | instrument   | nirspec      |        4 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 31 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | target_name  | galaxy1      |        5 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 32 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | filter       | multi        |        6 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 33 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | version_id   | v1           |        7 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 34 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | product_type | spec         |        8 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 35 | hlsp_mct-tutorial_jwst_nirspec_galaxy1_multi_v1_spec.fits     | extension    | fits         |        9 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 36 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | hlsp_str     | hlsp         |        1 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 37 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | hlsp_name    | mct-tutorial |        2 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 38 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | mission      | jwst         |        3 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 39 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | instrument   | nirspec      |        4 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 40 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | target_name  | galaxy2      |        5 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 41 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | filter       | multi        |        6 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 42 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | version_id   | v1           |        7 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 43 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | product_type | spec         |        8 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 44 | hlsp_mct-tutorial_jwst_nirspec_galaxy2_multi_v1_spec.fits     | extension    | fits         |        9 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 45 | hlsp_mct-tutorial_readme.txt                                  | hlsp_str     | hlsp         |        1 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 46 | hlsp_mct-tutorial_readme.txt                                  | hlsp_name    | mct-tutorial |        2 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 47 | hlsp_mct-tutorial_readme.txt                                  | product_type | readme       |        3 | pass                   | pass           | pass           | pass          | pass           | PASS            |
| 48 | hlsp_mct-tutorial_readme.txt                                  | extension    | txt          |        4 | pass                   | pass           | pass           | pass          | pass           | PASS            |

```python
print(problems)
```

|    | path   | filename                                                    |   n_elements | name         | value   |   nfield | capitalization_score   | length_score   | format_score   | value_score   | nfield_score   | field_verdict   |
|---:|:-------|:------------------------------------------------------------|-------------:|:-------------|:--------|---------:|:-----------------------|:---------------|:---------------|:--------------|:---------------|:----------------|
|  0 | .      | hlsp_mct-tutorial_jwst_nirspec_galaxy3_multi_v1_a-spec.fits |            9 | product_type | a-spec  |        8 | pass                   | pass           | pass           | needs review  | pass           | NEEDS REVIEW    |

```python
# Close connection:
conn.close()
```

The tables should appear exactly the same as those in the screenshots above, and you can use pandas functions and filtering to find and analyze the results. As always, if you have any questions, please don't hesitate to reach out to mast_contrib@stsci.edu.
