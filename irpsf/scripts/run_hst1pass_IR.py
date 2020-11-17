#! /usr/bin/env python

"""Executes Jay Anderson's hst1pass.e on WFC3/IR images.

This script is a wrapper around Jay Anderson's hst1pass.F
routine, which identifies PSFs in WFC3/IR images. The script querys the QL
database for all IR exposures and will process any (new) files that are in the
QL database but not in the psf database.

The program hst1pass.e outputs two files:

(1) <filename>.stardb_xym has a list of detected stars, with 13 columns.
	1) xfit (x position)
	2) yfit (y position)
	3) mfit (instrumental magnitude)
	4) qfit (quality of fit, the absolute fractional residual, 0 = perfect fit)
	5) zfit  --- the fitted flux; 10**(-mfit/2.5)
	6) sfit (the fitted sky)
	7) cobs (the central pixel value)
	8) cexp (the fraction of light expected in the central pixel)
	9) aobs (the flux in the "a" pixels)
	10) aexp (the fraction of light expected in the "a" pixels)
	11) bobs (the flux in the "b" pixels)
	12) bexp (the fraction of light expected in the "b" pixels)
	13) N + star number

(2) <filename>.stardb_ras, 11x11 pixel cutouts around the brigtest pixel of
	each detected source (121 lines for each sources). It has 9 columns.
	1) i, pixel location for this pixel
	2) j, pixel location
	3) p, pixel value
	4) xfit, the fitted x pixel location
	5) yfit, the fitted y pixel location
	4) zfit, the fitted flux for the star
	5) sfit, the fitted sky value
	6) fexp, the fraction of light expected to be in this pixel
		 (fobs, the observed fraction will just be (p-s)/z
	7) N + star number

"""
import glob
from multiprocessing import Pool
import logging
import os
import subprocess

import argparse
from irpsf.settings.settings import *
from irpsf.psf_logging.psf_logging import setup_logging
from pyql.database.ql_database_interface import Master
from pyql.database.ql_database_interface import IR_flt_0
from pyql.database.ql_database_interface import IR_flt_1
from pyql.database.ql_database_interface import session as ql_session

def filter_psf_model_map(filt):
	filter_model_map = {'F105W' : 'PSFSTD_WFC3IR_F105W.fits',
						'F125W' : 'PSFSTD_WFC3IR_F125W.fits',
						'F098M' : 'PSFSTD_WFC3IR_F105W.fits',
						'F127M' : 'PSFSTD_WFC3IR_F125W.fits',
						'F139M' : 'PSFSTD_WFC3IR_F140W.fits',
						'F153M' : 'PSFSTD_WFC3IR_F160W.fits',
						'F126N' : 'PSFSTD_WFC3IR_F125W.fits',
						'F128N' : 'PSFSTD_WFC3IR_F127M.fits',
						'F130N' : 'PSFSTD_WFC3IR_F127M.fits',
						'F132N' : 'PSFSTD_WFC3IR_F127M.fits',
						'F164N' : 'PSFSTD_WFC3IR_F160W.fits',
						'F167N' : 'PSFSTD_WFC3IR_F160W.fits',
						'F140W' : 'PSFSTD_WFC3IR_F140W.fits',
						'F110W' : 'PSFSTD_WFC3IR_F110W.fits',
						'F160W' : 'PSFSTD_WFC3IR_F160W.fits'}

	return filter_model_map[filt]

def get_psf_records():
	"""Return a list containing filenames that already exist as raw
	outputs in the psf filesystem

	Returns
	-------
	psf_rootnames : list
		A list containing all rootnames of PSF files that already
		exist as raw outputs in the psf filesystem
	"""
	psf_files = glob.glob(os.path.join(SETTINGS['output_dir'], '*/*ras'))
	psf_rootnames = [os.path.basename(item).split('_')[0][0:8] for item in psf_files]

	return psf_rootnames

def get_ql_records(filt):
	"""Return a dictionary containing rootnames, paths, and filters
	from all filenames in the QL database.

	Parameters
	----------
	filt : str
		The filter to process.	Can be 'all' to process all filters.

	Returns
	-------
	ql_records : dict
		A dictionary whose keys are image rootnames and whose values
		are a list containing the images' path and filter.
	"""

	# Build query
	ql_query = ql_session.query(IR_flt_0.filter, Master.ql_root, Master.dir)\
		.join(Master, Master.id == IR_flt_0.master_id)\
		.join(IR_flt_1, IR_flt_1.id == IR_flt_0.id)

	#Filter out subarrays
	ql_query = ql_query.filter((IR_flt_0.aperture=='IR')|(IR_flt_0.aperture=='IR-FIX'))

	#Filter out grisms & blank
	ql_query = ql_query.filter(
		(IR_flt_0.filter != 'G102') & \
		(IR_flt_0.filter != 'Blank') & \
		(IR_flt_0.filter != 'G141'))

	# filter out DARKS, FROM CLARE'S DIRECTORY
	ql_query = ql_query.filter(
		(IR_flt_0.targname != 'DARK') & \
		(IR_flt_0.targname != 'DARK-NM'))
		#(IR_flt_0.targname != 'TUNGSTEN') & \
		#(IR_flt_0.imagetyp != 'FLAT') & \

	# filter out GS failures
	ql_query = ql_query.filter(
		(IR_flt_0.quality != 'GSFAIL') & \
		(IR_flt_0.quality != 'LOCKLOST') & \
		(IR_flt_0.quality != 'ACQ2FAIL'))

	# If specific filter specified, select for that only.
	if filt != 'all':
		ql_query = ql_query.filter(IR_flt_0.filter == filt.upper())

	ql_query = ql_query.all()

	# Build ql_records list
	ql_records = []
	for record in ql_query:
		ql_records.append(record)

	return ql_records

def get_job_list(new_records):
	"""Create a list containing individual calls to hst1pass.e.

	Each item in the job_list will be a call to hst1pass.e with
	the appropriate parameters to process an image, beginning with a command
	to cd into the correct output directory.

	Parameters
	----------
	new_records : dict
		A list of tuples, containing (<input file path>, <filter>)

	Returns
	-------
	job_list : list
		A list of strings containing calls to the img2psf_wfc3uv.F
		routine with appropriate parameters.
	"""
	job_list = []
	for record in new_records:
		filt, rootname, path = record
		output_loc = os.path.join(SETTINGS['output_dir']+'/'+format(filt),'')
		exe_loc = SETTINGS['jays_code'] + '/hst1pass.e'
		path = os.path.join(path, '')
		psf_model_path=SETTINGS['psf_models'] + '/{}'.format(filter_psf_model_map(filt))
		job_list.append('cd {}; {} STARDB+ HMIN=7 FMIN=10000 PSF={}, {}'.format(output_loc, exe_loc, psf_model_path, path+rootname+'q_flt.fits'))

	return job_list

def run_process(cmd):
	"""Calls subprocess with the command cmd.

	Parameters
	----------
	cmd : str
		The subprocess command to execute.

	Returns
	-------
	subprocess.call(cmd, shell=True) : obj
		The subprocess call.
	"""
	logging.info('Beginning to process {}'.format(cmd.split()[-1]))

	return subprocess.call(cmd, shell=True)

def parse_args():
	"""Parse the command line arguments.

	Returns
	-------
	args : obj
		An agparse object containing all of the added arguments
	"""

	parser = argparse.ArgumentParser(
		description="Populate the IR psf table with data from the .psf \
		outputs of Jay's code")
	parser.add_argument(
		'-filter',
		required=False,
		default='all',
		help='The filter to the processed.')
	args = parser.parse_args()

	return args

def main_run_hst1pass_IR():

	# Parse command line args
	args = parse_args()
	logging.info('Beginning processing. Filter = {}'.format(args.filter))

	# Query QL
	ql_records = get_ql_records(args.filter)
	logging.info('{} records found in QL database.'.format(len(ql_records)))

	#Check QL files against files already in database
	psf_rootnames = get_psf_records()

	new_records = []
	for record in ql_records:
		if record[1] not in psf_rootnames:
			new_records.append(record)

	logging.info('{} new files to process.'.format(len(new_records)))
	# Make list of calls to hst1pass to be run as subprocesses
	job_list = get_job_list(new_records)

	# Run processes in parallel
	p = Pool(SETTINGS['cores'])
	p.map(run_process, job_list)

if __name__ == '__main__':
	module = os.path.basename(__file__).strip('.py')
	setup_logging(module)

	main_run_hst1pass_IR()
