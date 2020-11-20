#! /usr/bin/env python

"""Create a CSV file contaning new psf_mast table records to be
delivered to MAST.

This module reads in two files: (1) the most recently delivered
psf_mast database dump text file and (2) a new psf_mast database
dump text file.  The module will then determine which records exist
in the new text file but don't exist in the old text file and write
the new records to a separate psf_mast_YYYY_MM_DD_deliver.txt text
file.  This file can then be delivered to the MAST PSF group.

Authors
-------
    Matthew Bourque

Use
---
    This module is intended to be run via the command line as such:

    >>> python make_mast_deliverable old_table new_table

    Required arguments:
    old_table - Path to text file containing the most-recently
                delivered psf_mast table.
    new_table - Path to text file containing the most recent
                psf_mast table database dump.
"""

from __future__ import print_function
import argparse


def make_mast_deliverable(old_table, new_table):
    """The main function of the make_mast_deliverable module.  See
    module docstrings for further information.

    Parameters
    ----------
    old_table: str
        The path to the file that holds the most recent delivered
        psf_mast table.
    new_table: str
        The path to the file that holds the most recent psf_mast
        table database dump.
    """

    # Read in the old table
    print('Reading in {}'.format(old_table))
    with open(old_table, 'r') as f:
        old_tab = f.readlines()
    old_tab = [item.strip() for item in old_tab]

    # Read in the new_table
    print('Reading in {}'.format(new_table))
    with open(new_table, 'r') as f:
        new_tab = f.readlines()
    new_tab = [item.strip() for item in new_tab]

    # Build the new deliverable table
    print('Building delivery table')
    deliverable_table = new_table.replace('.txt', '_deliver.csv')
    header = 'id,rootname,filter,aperture,psf_x_center,psf_y_center,chip,'
    header += 'psf_flux,sky,qfit,pixc,midexp,mjd,date,focus\n'
    delivery_table = set(new_tab) - set(old_tab)
    nrows = len(delivery_table)
    with open(deliverable_table, 'w') as f:
        f.write(header)
        for i, row in enumerate(delivery_table):
            print('{} of {} rows: {}% Complete'.format(i, nrows,
                  round((i/nrows)*100, 2)), end='\r')
            f.write(row + '\n')
    print('Deliverable psf_mast table written to {}'.format(deliverable_table))


def parse_args():
    """Parse the command line arguments.

    Returns
    -------
    args : obj
        An agparse object containing all of the added arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'old_table',
        help='The path to the most recent delivered psf_mast table.')
    parser.add_argument(
        'new_table',
        help='The path to the most recent dump of the psf_mast table.')
    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = parse_args()
    make_mast_deliverable(args.old_table, args.new_table)
