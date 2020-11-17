WFC3 UVIS PSF Project
---------------------

This repository contains the software to build and analyze the HST WFC3 PSF database. This pipeline is used to find, catalog, and analyze WFC3 UVIS PSF's.  Below are instructions on how to install the `psf` package and its dependencies as well as how to update the PSF database and deliver appropriate information to MAST. The timescale of the installation and procedure are around a day and a week, respectively.  This may increase or decrease due to computer skills, technical complications, and/or data size. **Last edit by Frederick Dauphin 11/11/2020.**

Installation
----------------

1. Log into the `plhstins1` server. All jobs are completed on this server because all of the `mysql` database tables that will be updated exist here.
2. Download a local clone of the `psf` repository, available here: https://github.com/spacetelescope/psf.  It is recommended to place the local clone in a directory on central storage, as it will then be easy to access the repository from the `plhstins1` machine as well as your personal machine. If the local clone cannot directly download to central storage from the server due to permissions, download it directly to central storage from your personal machine.
3. Change directory to within the `psf` repository.
4. Create the `psf` `anaconda` environment: `conda env create -f environment.yml`. If the environment cannot be created, it is because the packages are too old or cannot be found in `anaconda`; collaborate with the PSF team on how to best update the environment if necessary.
5. Activate the `psf` environment: `source activate psf`. Enter `conda list` on terminal to check everything in `environment.yml` was installed.
6. Appropriate scripts with the prefix `agpy_` contain Python3 compatible functions from the `agpy` package.  **The entire package is not required.** (Install the `agpy` package (which is not part of `anaconda`) by running `pip install agpy`.)
7. Install the `montage_wrapper` package (which is not part of `anaconda`) by running `pip install montage_wrapper`.
8. If necessary, install the `pyql` package by creating a local clone (available here https://github.com/spacetelescope/pyql) and running `python setup.py develop` or `python setup.py install` (`develop` is recommended). The path for the clone doesn't matter.
9. Install the `psf` package by running `python setup.py develop` or `python setup.py install` (`develop` is recommended).

Procedure to update and deliver the `psf_mast` table to MAST
-------------------------------------------------------------
**(1)** Retrieve the latest focus model measurements from the ‘Focus Model Annual Summary’ page (https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/hst-focus-model) and place them in a text file located at `/grp/hst/wfc3p/psf/main/focus-models/Focus*.txt` (Each year has its own file). If recent measurements are not available on the page, send an email to Colin Cox asking him for the latest measurements or ask the PSF team how the files can be retrieved. Only use focus model files from 2009 onward. The last time this procedure was run included up to 12/31/2019.

In addition, make sure the Focus History files located in `/grp/hst/wfc3p/psf/main/focus-history/` are up to date. If they are not, ask Linda Dressel for the up-to-date history or ask the PSF team how the files can be retrieved.

**(2)** Log into the `plhstins1` server if necessary.  (It is also recommended to start a `screen` session, as some of the processes take a long time and will likely run overnight.)

**(3)** Change directory to the `scripts/` directory of your local clone of the `psf` repository.

**(4)** Activate the `psf` `conda` environment: `source activate psf` (see `Installation` for further details)

**(5)** Create a yaml file with this path: `psf/psf/settings/config.yaml`. In the file, copy and paste the following text:

```yaml
build: 'rhel-build'
cores: 20
psf_connection_string: 'mysql+pymysql://<username>:<password>@localhost/psf'
ql_connection_string: 'mysql+pymysql://qldb_user:6IdJiDatmyBNZ59@tanops.stsci.edu:33306/qldb'
echo: False
make_fits_cube_chunk_size: 1
```

If you do not have a mysql account, ask ITSD to create one for you with this global privilege: `GRANT FILE ON *.* TO '<username>@localhost';` (recommended usernames follow this style: Alice Bob --> abob). This privilege allows the user to export the tables from mysql. Set `username` and `password` to the appropriate credentials of your mysql account. Note that the `cores` parameter can be increased or decreased as you see fit given the current use of the server.

**(6)** **READ THIS ENTIRE SECTION BEFORE EXECUTING ANY COMMANDS IN TERMINAL.** Execute `bash bash_scripts/run_all.bash`. The bash script executes `screen -S <FILTER> python run_img2psf.py -filter <FILTER>`, which creates a screen named `<FILTER>` for each filter to run the python script. This allows us to run all the filters at once versus typing the commands below one by one, which speeds this procedure quite a bit.

After executing the command, the terminal window will turn black (which is what is suppose to happen), and print statements will start appearing if the code is running properly. Detatch from this screen so a new filter screen starts: press `ctrl+a ctrl+d`. The terminal again will turn black, meaning a new screen was created. Repeat this process for each filter (62 times in total). Detatch from each screen not too quickly (waiting for the yaml prints is long enough). After you detach from all of them, the terminal window should return to the main window and should look like whatever it did before executing `run_all.bash`. `documents/screen_cheat_sheet.pdf` contains a list of commands useful for checking which screens are running, reattaching to screens, killing screens, etc.

If you are not comfortable running everything at once (it does seem intimidating at first glance), then run bash scripts that run filters by 10: e.g. `bash bash_scripts/run_01_10.bash`. If you would rather stay away from the screens altogether, then execute the python script for each filter: e.g. `python run_img2psf.py -filter F200LP`. Each command is listed below. It is **highly recommended** to run the first several filters manually in order to get a feel of how the script works, then work up to bash scripting screens if comfortable.

Note that Jay Anderson's FORTRAN code (`img2psf_wfc3uv.F`) contains several bugs and memory leaks, causing `run_img2psf.py` to often freeze or crash. `documents/run_img2psf_output.txt` contains all the outcomes from the last time this procedure was completed.  Below are all the possible outcomes when executing the script:

A.  It completes

B.  It prints a statement starting with `WFC3UV_FLTREAD not yet designed...`

C.  It prints `Problem File...`, meaning one of the images was not in standard fits format

D.  It prints the yaml warning and nothing else (usually the FQ filters do this)

E.  It freezes when printing out the gains

F.  It freezes and prints `Ls wants to be > 999999...`

If a script is running, it will actively print statements out, and if it freezes, it doesn't.  Freezes usually happen within the hour. When it freezes, it is recommended to stop the process altogether (i.e. `ctrl+z`) and re-execute the script.  If this keeps happening after 3-4 tries, just give up.  It is recommended to ask Jay to explain how his FORTRAN code works to gain further insight on how psfs are generated.  It is also recommended to ask Jay to fix this issue one day in the distant future.

Executing `run_img2psf.py` over all filters will create the `*.psf` and `*.xym` files in the psf filesystem (i.e. `/grp/hst/wfc3p/psf/main/outputs/raw_outputs/`).  It will also create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/run_img2psf`. When running the first few filters, it is good practice to check the contents of both raw outputs and logs to make sure everything is working.

Note that some filters may take a while to complete, especially those that are used on WFC3 frequently (i.e. `F606W` and `F814W`) while others may take only a few seconds or not have any data to process. Depending on how long it has been since the last psfs were generated, it will at most take several hours for those two filters mentioned.

`run_img2psf.py` commands to run:

    `python run_img2psf.py -filter F200LP`
    `python run_img2psf.py -filter F280N`
    `python run_img2psf.py -filter F350LP`
    `python run_img2psf.py -filter F395N`
    `python run_img2psf.py -filter F469N`
    `python run_img2psf.py -filter F502N`
    `python run_img2psf.py -filter F606W`
    `python run_img2psf.py -filter F645N`
    `python run_img2psf.py -filter F665N`
    `python run_img2psf.py -filter F763M`
    `python run_img2psf.py -filter F850LP`
    `python run_img2psf.py -filter FQ378N`
    `python run_img2psf.py -filter FQ437N`
    `python run_img2psf.py -filter FQ619N`
    `python run_img2psf.py -filter FQ727N`
    `python run_img2psf.py -filter FQ924N`
    `python run_img2psf.py -filter F218W`
    `python run_img2psf.py -filter F300X`
    `python run_img2psf.py -filter F373N`
    `python run_img2psf.py -filter F410M`
    `python run_img2psf.py -filter F475W`
    `python run_img2psf.py -filter F547M`
    `python run_img2psf.py -filter F621M`
    `python run_img2psf.py -filter F656N`
    `python run_img2psf.py -filter F673N`
    `python run_img2psf.py -filter F775W`
    `python run_img2psf.py -filter F953N`
    `python run_img2psf.py -filter FQ387N`
    `python run_img2psf.py -filter FQ492N`
    `python run_img2psf.py -filter FQ634N`
    `python run_img2psf.py -filter FQ750N`
    `python run_img2psf.py -filter FQ937N`
    `python run_img2psf.py -filter F225W`
    `python run_img2psf.py -filter F336W`
    `python run_img2psf.py -filter F390M`
    `python run_img2psf.py -filter F438W`
    `python run_img2psf.py -filter F475X`
    `python run_img2psf.py -filter F555W`
    `python run_img2psf.py -filter F625W`
    `python run_img2psf.py -filter F657N`
    `python run_img2psf.py -filter F680N`
    `python run_img2psf.py -filter F814W`
    `python run_img2psf.py -filter FQ232N`
    `python run_img2psf.py -filter FQ422M`
    `python run_img2psf.py -filter FQ508N`
    `python run_img2psf.py -filter FQ672N`
    `python run_img2psf.py -filter FQ889N`
    `python run_img2psf.py -filter F275W`
    `python run_img2psf.py -filter F343N`
    `python run_img2psf.py -filter F390W`
    `python run_img2psf.py -filter F467M`
    `python run_img2psf.py -filter F487N`
    `python run_img2psf.py -filter F600LP`
    `python run_img2psf.py -filter F631N`
    `python run_img2psf.py -filter F658N`
    `python run_img2psf.py -filter F689M`
    `python run_img2psf.py -filter F845M`
    `python run_img2psf.py -filter FQ243N`
    `python run_img2psf.py -filter FQ436N`
    `python run_img2psf.py -filter FQ575N`
    `python run_img2psf.py -filter FQ674N`
    `python run_img2psf.py -filter FQ906N`

**(7)** Execute the `make_focus_table.py` script: `python make_focus_table.py`.  This will read in the focus model text files, store the information in the `focus` table of the mysql database, and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_focus_table/`. Note since the tables are updated in a mysql database, you can sign into mysql to investigate the contents of each table, although it is not necessary: `mysql -u <username> -p` (enter appropriate username and password). `documents/mysql_cheat_sheet.pdf` contains useful commands if needed.

**(8)** Execute the `make_avg_focus_table.py` script: `python make_avg_focus_table.py`.  This will read in the focus model text files, store the information in the `avg_focus` table of the database, and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_avg_focus_table/`.

**(9)** Execute the `make_focus_model_table.py` script: `python make_focus_model_table.py`.  This will read in the focus model text files, store the information in the `focus_model` table of the database, and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_focus_model_table/` .  Note that this takes several hours to run.

**(10)** Execute the `make_psf_table.py` script over all filters: (`python make_psf_table.py`) `bash bash_scripts/run_all_psf_table.bash`.  The bash script will run all the filters separately on different screens named after each filter rather than sequentially as stated earlier.  This will add new records to the `psf` table and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_psf_table/`.

**(11)** Execute the `make_psf_mast_table.py` script over all filters: (`python make_psf_mast_table.py`) `bash bash_scripts/run_all_psf_mast_table.bash`.  This will add new records to the `psf_mast` table and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_psf_mast_table/`.

**(12)** Execute the `make_gaussian_tables.py` script: `bash bash_scripts/run_all_gaussian.bash`.  This will update the `row_gaussians` and `col_gaussians` tables and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_gaussian_tables/`.

**(13)** Execute the `make_2d_gaussian_table.py` script: `bash bash_scripts/run_all_2d.bash`.  This will update the `gauss2d` table and will create a log file located in `/grp/hst/wfc3p/psf/main/psf_logs/make_2d_gaussian_table/`. The timescale for most filters will be a day while F606W and F814W will take a few days.

**(14)** Perform a database dump on the `psf_mast` table using the following command: `mysqldump -u <username> -p --tab=/internal/data1/bourque/ --fields-terminated-by=, --lines-terminated-by='\n' psf psf_mast`  (enter appropriate username and password). Double check that you have an existing mysql account or else the .txt file will not be exported from mysql.

**(15)** Move the resulting `psf_mast.txt` file in `/internal/data1/bourque/` to `/grp/hst/wfc3p/psf/main/db_dumps/` and rename it to `psf_mast_YYYY_MM_DD.txt`.

**(16)** Execute the `make_mast_deliverable.py` script, supplying the most recently delivered database dump file and the most recent yet-to-be-delivered database dump file as command line arguments:

`python make_mast_deliverable.py /grp/hst/wfc3p/psf/main/db_dumps/<most_recent_psf_mast.txt> /grp/hst/wfc3p/psf/main/db_dumps/<psf_mast_YYYY_MM_DD.txt>`

The script will then determine which new files occurred since the last delivery and create a new table called `psf_mast_YYYY_MM_DD_deliver.csv`.

**(17)** Ask Kailash Sahu or head of the PSF team to review `psf_mast_YYYY_MM_DD_deliver.csv` so it can be approved. Once approved, email the newly created file to the MAST PSF group!  If the file is too large to email, place it in some centrally located area for MAST to grab.  

Congratulations and thank you for all your hard work!  Please be sure to edit any appropriate changes in order to make the procedure easier for the next user.

**WARNING** A lot of the subdirectories for plots do not exist within this psf directory because plotting is unnecessary for the procedure. If plotting is necessary for your use, manually create the plot subdirectories under `/grp/hst/wfc3p/psf/main/outputs/plots/<name_of_plotting_file>`. In `psf/psf/plotting/plotting_functions.py`, the file on line 136 `/grp/hst/wfc3h/bourque/psf/focus-models/breathing-only/breathing_model.dat` cannot be found at the time of this edit.
