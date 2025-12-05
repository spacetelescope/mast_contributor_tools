# Reading the File Name Checker Results: Tutorial for SQLite files
This tutorial will provide a brief overview for how to open and use SQLite files, which will be produced upon running the filename checker on your fileset. Please refer to the [`Filename Check README`](../docs/filename_check_readme.md) for additional information about running the filename checker. If this is the first time you've used the Filename Checking software, you may want to run through the [`TUTORIAL README`](../TUTORIAL/tutorial_readme.md) first to familiarize yourself with the process and the SQLite files the software produces.

## Reading and Interacting with SQLite files
Assuming you've run through the tutorial and completed [**STEP 4b**](../docs/tutorial_readme.md#step-4b:-check-all-file-names-in-a-directory), you should have a `results_mct-tutorial.db` file in the [`TUTORIAL/`](../TUTORIAL/) folder now. You can interact with this file in any way you prefer, but we suggest you:

### View with the [DB Browser for SQLite](https://sqlitebrowser.org/)
Once you've downloaded and installed the DB Browser, open it and select `Open Database` and then navigate to the folder in which your results database resides. Select and open the corresponding DB file. Your window should look something like this:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_Initial_Open_DB.png "Figure 1")

You should now be seeing the `Database Structure` tab highlighted, with a few tables populating the left panel. Those tables are `fields` and `filename`. If you click on the arrows next to the two table names, you should see the names of the columns that belong to each table. There is also a `Views` heading where you can find the `potential_problems` view, which highlights all potential problem fields within the `fields` table.

If you now click on the `Browse Data` tab next to the `Database Structure` tab, you'll be able to view the table itself, which should have the `fields` table selected:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_Table_Data_View.png "Figure 2")

The `fields` table contains the results of the file name check for every single field within each filename analyzed. For instance, if you checked 5 filenames with 9 fields each, the `fields` table should have 5*9 = 45 rows. Meanwhile, the `filename` table (which you can access by clicking on the Table box below the tabs and to the left), contains one row per file, indicating the verdict of the filename check on that filename. Finally, the `potential_problems` table lists all potential problems indicated in the `fields` table.

Within the `fields` table, your files are evaluated as follows (see [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for more details):

- Captalization: the filename must be all lower case.
- Character Length: each field has a maximum character length.
- Format: checks overall format and special characters: for example, a period `.` is allowed in the `<version>` field but not in the `<proj-id>`. Certain fields allow hyphen-separated elements. Most fields must begin and end with an ASCII alpha-numeric character.
- Value: In some cases, the contents of each field are validated against known values to the extent possible.

The evaluation scores for individual fields and the overall file names are one of `PASS`, `NEEDS REVIEW` or `FAIL`. A verdict of `FAIL` means that filename or individual field does not follow our filenaming convention (it breaks one of the above rules) and it must be changed before it will be accepted by MAST. Please review which field(s) have been scored as `FAIL` and update them to match the Capitalization, Character Length, Format, and/or Value rules. A verdict of `NEEDS REVIEW` is usually the result of an unrecognized value. This is often necessary and correct, e.g. for new product types or instruments whose data we haven't ingested before. Please consult with MAST staff (mast_contrib@stsci.edu) for review.

Within the `filename` table (`Browse Data` tab, then select table `filename` in the top left box), each filename is listed with the overall status (automatically set to the most critical of `PASS`, `NEEDS REVIEW` or `FAIL`) as well as the number of elements identified in the filename. An example is shown below in Figure 3:

![DB Browser for SQLite after opening filename check DB file](../TUTORIAL/tutorial_images/DB_Browser_filename_Table_View.png "Figure 3")

Again, please see [`filename_check_readme.md`](../docs/filename_check_readme.md) for how to run the filechecker or the HLSP [File Naming Convention](https://outerspace.stsci.edu/display/MASTDOCS/File+Naming+Convention) for detailed rules.
