#! /usr/bin/env python

"""Resets all tables in the ir_psf database.

Authors
-------

   Clare Shanahan 2019

Use
---

    This script is intended to run via command line as such:
        >>> python reset_psf_database.py
"""

from irpsf.database.ir_psf_database_interface import Base
from irpsf.settings.settings import *

if __name__ == '__main__':

    prompt = ('About to reset all tables for database instance {}. Do you '
              'wish to proceed? (y/n)\n'.format(SETTINGS['psf_connection_string']))
    response = input(prompt)

    if response.lower() == 'y':
        print('Resetting database.')
        #Base.metadata.drop_all()
        Base.metadata.create_all()
