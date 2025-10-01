# SQLite Tutorial
This tutorial will provide a brief tutorial for how to use SQLite files, which will be produced upon running the filename checker on your fileset. Please refer to the [`Filename Check README`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/docs/filename_check_readme.md) for additional information about running the filename checker. If this is the first time you've used the Filename Checking software, you may want to run through the [`TUTORIAL README`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/TUTORIAL/tutorial_readme.md) first to familiarize yourself with the process and the SQLite files the software produces.

## Reading and Interacting with SQLite files
Assuming you've run through the tutorial and completed **STEP 4b**, you should have a `results_mct-tutorial.db` file in the [`TUTORIAL/`](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/TUTORIAL/tutorial_readme.md) folder now. You can interact with this file in any way you prefer, but we suggest you:

### View with the [DB Browser for SQLite](https://sqlitebrowser.org/)
Once you've downloaded and installed the DB Browser, open it and select `Open Database` and then navigate to the folder in which your results database resides. Select and open the corresponding DB file. Your window should look something like this:

![DB Browser for SQLite after opening filename check DB file](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/TUTORIAL/tutorial_images/DB_Browser_Initial_Open_DB.png)

You should now be seeing the `Database Structure` tab highlighted, with a few tables populating the left panel. Those tables are `fields` and `filename`. If you click on the arrows next to the two table names, you should see the names of the columns that belong to each table. There is also a `Views` heading where you can find the `potential_problems` view, which highlights all potential problem fields within the `fields` table.

If you now click on the `Browse Data` tab next to the `Database Structure` tab, you'll be able to view the table itself, which should have the `fields` table selected:

![DB Browser for SQLite after opening filename check DB file](https://github.com/spacetelescope/mast_contributor_tools/blob/dev/TUTORIAL/tutorial_images/mast_contributor_tools/TUTORIAL/tutorial_images/DB_Browser_Table_Data_View.png)

The `fields` table contains the results of the file name check for every single field within each filename analyzed. For instance, if you checked 5 filenames with 8 fields each, the `fields` table should have 5*8 = 40 rows. Meanwhile, the `filename` table (which you can access by clicking on the Table box below the tabs and to the left), contains one row per file, indicating the verdict of the filename check on that filename. Finally, the `potential_problems` table lists all potential problems indicated in the `fields` table.
