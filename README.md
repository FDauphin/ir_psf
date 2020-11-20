WFC3 IR PSF Project
---------------------

This repository contains the software to build and analyze the HST WFC3 PSF database. This pipeline is used to find, catalog, and analyze WFC3 IR PSF's.  Below are instructions on how to install the `irpsf` package and its dependencies as well as how to update the PSF database and deliver appropriate information to MAST. The timescale of the installation and procedure are around a day and a week, respectively.  This may increase or decrease due to computer skills, technical complications, and/or data size. This repository compliments the UVIS pipeline, available here: https://github.com/spacetelescope/psf. **Last edit by Frederick Dauphin 11/20/2020.**

Installation
----------------

1. Log into the `plhstins1` server. All jobs are completed on this server because all of the `mysql` database tables that will be updated exist here.
2. Download a local clone of the `ir_psf` repository, available here: https://github.com/spacetelescope/ir_psf.  It is recommended to place the local clone in a directory on central storage, as it will then be easy to access the repository from the `plhstins1` machine as well as your personal machine. If the local clone cannot directly download to central storage from the server due to permissions, download it directly to central storage from your personal machine.
3. Change directory to within the `ir_psf` repository.
4. If necessary, create the `psf` `anaconda` environment: `conda env create -f environment.yml`. If the environment cannot be created, it is because the packages cannot be found in `anaconda` or `pip`; collaborate with the PSF team on how to best update the environment if necessary.
5. Activate the `psf` environment: `source activate psf`. Enter `conda list` on terminal to check everything in `environment.yml` was installed. `montage_wrapper` package (which is not part of `anaconda`) should be installed, but if not, run `pip install montage_wrapper`.
6. If necessary, install the `pyql` package by creating a local clone (available here https://github.com/spacetelescope/pyql) and running `python setup.py develop` or `python setup.py install` (`develop` is recommended).
7. Install the `irpsf` package by running `python setup.py develop` or `python setup.py install` (`develop` is recommended).

**Note:** Appropriate scripts with the prefix `agpy_` contain Python3 compatible functions from the `agpy` package (which is a part of `pip`). If Python3 is not supported anymore, update the syntax for the `agpy_` scripts as needed.

Procedure to update and deliver the `ir_psf_mast` table to MAST
-------------------------------------------------------------
**(1)** Retrieve the latest focus model measurements from the ‘Focus Model Annual Summary’ page (https://www.stsci.edu/hst/instrumentation/focus-and-pointing/focus/hst-focus-model) and place them in a text file located at `/grp/hst/wfc3p/psf/main/focus-models/Focus*.txt` (Each year has its own file). If recent measurements are not available on the page, send an email to Colin Cox asking him for the latest measurements or ask the PSF team how the files can be retrieved. Only use focus model files from 2009 onward. The last time this procedure was run included up to 12/31/2019.

**(2)** Log into the `plhstins1` server if necessary.  (It is also recommended to start a `screen` session, as some of the processes take a long time and will likely run overnight.)

**(3)** Change directory to the `irpsf/scripts/` directory of your local clone of the `ir_psf` repository.

**(4)** Activate the `psf` `conda` environment: `source activate psf` (see `Installation` for further details)

**(5)** Create a yaml file in `irpsf/scripts/` named `config.yaml`. In the file, copy and paste the following text:

```yaml
cores: 20
psf_connection_string: 'mysql+pymysql://<username>:<password>@localhost/ir_psf'
ql_connection_string: 'mysql+pymysql://qldb_user:6IdJiDatmyBNZ59@tanops.stsci.edu:33306/qldb'
output_dir : '/grp/hst/wfc3p/psf/main_ir/raw_outputs'
jays_code : '/grp/hst/wfc3p/psf/main_ir/hst1pass'
focus_models : '/grp/hst/wfc3p/psf/main/focus-models'
psf_models : '/grp/hst/wfc3p/psf/main_ir/psf_models'
log_dir : '/grp/hst/wfc3p/psf/main_ir/psf_logs'
```

If you do not have a mysql account, ask ITSD to create one for you with this global privilege: `GRANT FILE ON *.* TO '<username>@localhost';` (recommended usernames follow this style: Alice Bob --> abob). This privilege allows the user to export the tables from mysql. Set `username` and `password` to the appropriate credentials of your mysql account. Note that the `cores` parameter can be increased or decreased as you see fit given the current use of the server.

**(6) READ THIS ENTIRE SECTION BEFORE EXECUTING ANY COMMANDS IN TERMINAL.** Execute `bash bash_scripts/run_all.bash`. The bash script executes `screen -S <FILTER> python run_hst1pass_IR.py -filter <FILTER>`, which creates a screen named `<FILTER>` for each filter to run the python script. Therefore, it run all the filters at once versus typing the commands below one by one, which speeds this procedure quite a bit.

After executing the command, the terminal window will turn black (which is what is suppose to happen), and print statements will start appearing if the code is running properly. Detatch from this screen so a new filter screen starts: press `ctrl+a ctrl+d`. The terminal again will turn black, meaning a new screen was created. Repeat this process for each filter (15 times in total). Detatch from each screen not too quickly (waiting for the yaml prints is long enough). After you detach from all of them, the terminal window should return to the main window and should look like whatever it did before executing `run_all.bash`. `documents/screen_cheat_sheet.pdf` contains a list of commands useful for checking which screens are running, reattaching to screens, killing screens, etc.

If you would rather stay away from the screens altogether, then execute the python script for each filter individually: e.g. `python run_hst1pass_IR.py -filter F105W`. Each command is listed below. It is **highly recommended** to run the first few filters manually in order to get a feel of how the script works, then work up to bash scripting if comfortable.

**Temporary Start**

Note that Jay Anderson's FORTRAN code (`hst1pass.F`) contains several bugs and memory leaks, causing `run_hst1pass_IR.py` to often freeze or crash. `documents/run_hst1pass_IR_output.txt` contains all the outcomes from the last time this procedure was completed.  Below are all the possible outcomes when executing the script:

A.  N/A

If a script is running, it will actively print statements out, and if it freezes, it doesn't.  Freezes usually happen within the hour. When it freezes, it is recommended to stop the process altogether (i.e. `ctrl+z` in a main window; `ctrl+a :quit` in a screen) and re-execute the script.  If this keeps happening after 3-4 tries, just give up.  It is recommended to ask Jay to explain how his FORTRAN code works to gain further insight on how psfs are generated.  It is also recommended to ask Jay to fix this issue one day in the distant future.

**Temporary End**

Executing `run_hst1pass_IR.py` over all filters will create the `*.stardb_ras` and `*.stardb_xym` files in the ir_psf filesystem (i.e. `/grp/hst/wfc3p/psf/main_ir/raw_outputs/`).  It will also create a log file located in `/grp/hst/wfc3p/psf/main_ir/psf_logs/run_hst1pass_IR`. When running the first few filters, it is good practice to check the contents of both raw outputs and logs to make sure everything is working.

Note that some filters may take a while to complete, especially those that are used on WFC3 frequently **(i.e. `Example1`)** while others may take only a few seconds or not have any data to process. Depending on how long it has been since the last psfs were generated, it will at most take several hours for the filters mentioned.

`run_img2psf.py` commands to run:

    `python run_hst1pass_IR.py -filter F105W
     python run_hst1pass_IR.py -filter F110W
     python run_hst1pass_IR.py -filter F125W
     python run_hst1pass_IR.py -filter F140W
     python run_hst1pass_IR.py -filter F160W
     python run_hst1pass_IR.py -filter F098M
     python run_hst1pass_IR.py -filter F127M
     python run_hst1pass_IR.py -filter F139M
     python run_hst1pass_IR.py -filter F153M
     python run_hst1pass_IR.py -filter F126N
     python run_hst1pass_IR.py -filter F128N
     python run_hst1pass_IR.py -filter F130N
     python run_hst1pass_IR.py -filter F132N
     python run_hst1pass_IR.py -filter F164N
     python run_hst1pass_IR.py -filter F167N`

**(7)** Execute the `make_focus_model_table.py` script: `python make_focus_model_table.py`.  This will read in the focus model text files, store the information in the `focus_model` table of the mysql database, and will create a log file located in `/grp/hst/wfc3p/psf/main_ir/psf_logs/make_focus_model_table/`. Note since the tables are updated in a mysql database, you can sign into mysql to investigate the contents of each table, although it is not necessary: `mysql -u <username> -p` (enter appropriate username and password). `documents/mysql_cheat_sheet.pdf` contains useful commands if needed.

**(8)** Execute the `make_ir_psf_table.py` script over all filters: `bash bash_scripts/run_all_ir_psf_table.bash`.  The bash script will run all the filters separately on different screens named after each filter rather than sequentially as stated earlier.  This will add new records to the `ir_psf` table and will create a log file located in `/grp/hst/wfc3p/psf/main_ir/psf_logs/make_ir_psf_table/`. Note that this takes several hours to run.

**(9) this is a guess, ask Clare** Perform a database dump on the `ir_psf_mast` table using the following command: `mysqldump -u <username> -p --tab=/internal/data1/psf/ir --fields-terminated-by=, --lines-terminated-by='\n' ir_psf ir_psf_mast`  (enter appropriate username and password). Double check that you have an existing mysql account or else the .txt file will not be exported from mysql.

**(10)** Move the resulting `ir_psf_mast.txt` file in `/internal/data1/psf/ir` to `/grp/hst/wfc3p/psf/main_ir/db_dumps/` and rename it to `ir_psf_mast_YYYY_MM_DD.txt`.

**(11) check make_mast_deliverable to make sure this will work with ir data** Execute the `make_mast_deliverable.py` script, supplying the most recently delivered database dump file and the most recent yet-to-be-delivered database dump file as command line arguments:

`python make_mast_deliverable.py /grp/hst/wfc3p/psf/main_ir/db_dumps/<most_recent_ir_psf_mast.txt> /grp/hst/wfc3p/psf/main_ir/db_dumps/<ir_psf_mast_YYYY_MM_DD.txt>`

The script will then determine which new files occurred since the last delivery and create a new table called `ir_psf_mast_YYYY_MM_DD_deliver.csv`.

**(12)** Ask Kailash Sahu or head of the PSF team to review `ir_psf_mast_YYYY_MM_DD_deliver.csv` so it can be approved. Once approved, email the newly created file to the MAST PSF group!  If the file is too large to email, place it in some centrally located area for MAST to grab.  

Congratulations and thank you for all your hard work!  Please be sure to edit any appropriate changes in order to make the procedure easier for the next user.
