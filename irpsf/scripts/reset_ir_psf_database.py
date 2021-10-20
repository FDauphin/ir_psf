#! /usr/bin/env python

"""Resets all tables in the ir_psf database.

Authors
-------

   Clare Shanahan 2019

Use
---

    This script is intended to run via command line as such:
        >>> python reset_ir_psf_database.py

"""

from irpsf.database.ir_psf_database_interface import Base, engine, FocusModel, PSFTableMAST
from irpsf.settings.settings import *

if __name__ == '__main__':

    prompt = ('About to reset the deliverable tables for database instance {}. Do you '
              'wish to proceed? (y/n)\n'.format(SETTINGS['psf_connection_string']))
    response = input(prompt)

    if response.lower() == 'y':
        #RESET THE DELIVERABLE TABLES (FOCUSMODEL AND PSFTABLEMAST)
        print ('Resetting FocusModel and PSFTableMAST tables in the database')
#        Base.metadata.drop_all(engine, tables=[FocusModel.__table__])
 #       Base.metadata.create_all(engine, tables=[FocusModel.__table__])
        Base.metadata.drop_all(engine, tables=[PSFTableMAST.__table__])
        Base.metadata.create_all(engine, tables=[PSFTableMAST.__table__])

        #RESET ALL OF THE TABLES IN THE DATABASE
        #print 'Resetting database.'
        #Base.metadata.drop_all()
        #Base.metadata.create_all()
