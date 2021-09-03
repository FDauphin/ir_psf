#! /usr/bin/env python

"""Create the focus_model table in the ir_psf database.
The focus_model table stores the breathing-only focus model, which
models the focus of HST every five minutes.
The table consists of the following columns:
    (1) id - A unique integer identifier
    (2) mjd - The time of measurement (in MJD)
    (3) date - The date and time of measurement (in datetime)
    (4) focus - The focus model value
Authors
-------
    Clare Shanahan
    
Use
---
    This script is intended to be run via the command line as such:
        >>> python make_focus_model_table.py
"""

import datetime
import glob
import logging
import os

from irpsf.database.ir_psf_database_interface import engine, session, FocusModel
from irpsf.psf_logging.psf_logging import setup_logging
from irpsf.settings.settings import *
from sqlalchemy.exc import IntegrityError


def get_record_dict(record):
    """Return a dictionary containing the focus measurements.

    Parameters
    ----------
    record : list
        A list containing the focus measurements for the given record
        Each element in the list must map to a column in the
        focus_model table.

    Returns
    -------
    record_dict : dict
        A dictionary containing the focus measurements for the given
        record.  Each key in the dict is a column in the focus_model
        table.
    """

    record_dict = {}
    record_dict['mjd'] = record[0][:-1]
    date_string = '{} {} {} {}'.format(record[1], record[2], record[3], record[4])
    record_dict['date'] = datetime.datetime.strptime(date_string, '%b %d %Y %H:%M:%S')
    record_dict['focus'] = record[5]

    #print(record_dict)

    return record_dict


def make_focus_table_main():
    """The main controller for the make_focus_model_table module.

    The focus information is stored in the
    /grp/hst/wfc3p/psf/main/focus-models/Focus<year> files.
    """

    logging.info('Process Starting')
    data_files = glob.glob(SETTINGS['focus_models'] +'/*Focus*.txt')

    # Get list of mjds that already exist in the table
    results = session.query(FocusModel.mjd).all()
    mjd_list = [str(item[0]) for item in results]

    for data_file in data_files:

        logging.info('Reading data from {}'.format(data_file))

        with open(data_file, 'r') as f:
            data = f.readlines()

        for record in data:
            record = record.split()
            record_dict = get_record_dict(record)
            if record_dict['mjd'] not in mjd_list:
                #print(record_dict)
                logging.info('Inserting records for {}'.format(record_dict['date']))
                try:
                    engine.execute(FocusModel.__table__.insert(), record_dict)
                except IntegrityError:
                    print ('{} already in table'.format(record_dict['date']))

    logging.info('Process Complete')


if __name__ == '__main__':

    module = os.path.basename(__file__).strip('.py')
    setup_logging(module)

    make_focus_table_main()
