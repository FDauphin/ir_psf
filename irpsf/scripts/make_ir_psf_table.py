import argparse
from astropy.io import ascii, fits
from astropy.wcs import WCS
import datetime
import glob
import numpy as np
import logging
import os 

from irpsf.database.ir_psf_database_interface import engine, session, FocusModel, PSFTableMAST
from irpsf.psf_logging.psf_logging import setup_logging
from irpsf.settings.settings import *

from pyql.database.ql_database_interface import Master
from pyql.database.ql_database_interface import IR_flt_0
from pyql.database.ql_database_interface import IR_flt_1
from pyql.database.ql_database_interface import session as ql_session


"""
| id           | int(11)       | NO   | PRI | NULL    | auto_increment |
| rootname     | varchar(17)   | NO   | MUL | NULL    |                |
| filter       | varchar(25)   | NO   | MUL | NULL    |                |
| aperture     | varchar(50)   | NO   | MUL | NULL    |                |
| psf_x_center | int(11)       | NO   | MUL | NULL    |                |
| psf_y_center | int(11)       | NO   | MUL | NULL    |                |
| psf_flux     | int(11)       | NO   |     | NULL    |                |
| sky          | float         | NO   |     | NULL    |                |
| qfit         | float         | YES  |     | NULL    |                |
| pixc         | float         | YES  |     | NULL    |                |
| midexp       | decimal(12,5) | NO   | MUL | NULL    |                |
| mjd          | decimal(12,5) | YES  | MUL | NULL    |                |
| date         | datetime      | YES  | MUL | NULL    |                |
| focus		   | float         | YES  |     | NULL    |                |
"""
def parse_args():
    """Parse the command line arguments.

    Returns
    -------
    args : obj
        An agparse object containing all of the added arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-filter',
        required=False,
        default='all',
        help='The filter to the processed.')
    args = parser.parse_args()

    return args

def get_new_files_to_ingest(filt):
	"""For a given filter, checks files in filesystem against files already in database. Returns
	   a list of rootnames of files in filesystem but NOT in database, i.e. new files, to process.
	   Next, checks if files are out of the proprietary period."""

	logging.info('Getting list of new files to ingest for {}'.format(filt))

	#Determine which rootnames are in the filesystem
	files_in_psf_filesystem = glob.glob(SETTINGS['output_dir'] + '/{}/*ras'.format(filt))	
	rootnames_in_psf_filesystem = set([os.path.basename(x)[0:9] for x in files_in_psf_filesystem])

	# #Determine which rootnames are already in the database
	# psf_session, psf_base, psf_engine = loadConnection(SETTINGS['psf_connection_string'])
	# rootnames_in_database = psf_session.query(distinct(PSFTableMAST.rootname)).all()
	# rootnames_in_database = [item[0] for item in rootnames_in_database]
	# new_rootnames = set(rootnames_in_psf_filesystem) - rootnames_in_database

	new_rootnames = list(rootnames_in_psf_filesystem) #delete once block above is uncommented
	logging.info('{} total new files for {}'.format(len(new_rootnames), filt))

	# Remove any new rootnames that are proprietary
	today = datetime.datetime.today()
	one_year_ago = today.replace(year=today.year-1)
	new_rootnames_public = []

	for rootname in new_rootnames:
		results = ql_session.query(IR_flt_0.ql_root, IR_flt_0.date_obs)\
			.filter(IR_flt_0.ql_root == rootname[:-1]).one()
		date_obs = datetime.datetime.combine(results[1], datetime.time.min)
		if date_obs < one_year_ago:
			new_rootnames_public.append(rootname)
	logging.info('{} new non-proprietary files to ingest for {}'.format(len(new_rootnames_public), filt))

	return new_rootnames_public

def parse_xym_file(xym_file_path, include_saturated_stars=False):
	""" Reads in <filename>.stardb_xym file, returns an `astropy.table.Table`
	with data. Each row is a psf detected in <filename>.

	<filename>.stardb_xym has a list of detected stars, with 13 columns.
	1) xfit (x position)
	2) yfit (y position)
	3) mfit (instrumental magnitude)
	4) qfit (quality of fit, the absolute fractional residual, 0 = perfect fit)
	5) zfit  --- the fitted flux; 10**(-mfit/2.5)
	6) sfit (the fitted sky)
	7) cobs (the central pixel value) aka pixc
	8) cexp (the fraction of light expected in the central pixel)
	9) aobs (the flux in the "a" pixels)
	10) aexp (the fraction of light expected in the "a" pixels)
	11) bobs (the flux in the "b" pixels)
	12) bexp (the fraction of light expected in the "b" pixels)
	13) N + star number
	"""

	root = os.path.basename(xym_file_path)[0:9]
	colnames = ['psf_x_center' ,'psf_y_center', 'mfit', 'qfit', 'psf_flux', 'sky', 'pixc', 'cexp', 'aobs', 'aexp', 'bobs', 'bexp', 'N', 'sat']
	try:
		xym_tab = ascii.read(xym_file_path, names = colnames, guess=False, data_start=0, header_start=None, Reader=ascii.NoHeader)
		xym_tab['rootname'] = [root] * len(xym_tab)
		if include_saturated_stars is False:
			logging.info('Omiting {} saturated stars from table.'.format(len(xym_tab[xym_tab['sat'] == 1])))
			print(xym_file_path, 'Omiting {} saturated stars from table.'.format(len(xym_tab[xym_tab['sat'] == 1])))
			xym_tab = xym_tab[xym_tab['sat'] == 0]
		xym_tab.remove_columns(['mfit', 'cexp', 'aobs', 'aexp', 'bobs', 'bexp', 'N'])
		#xym_tab.remove_columns(['psf_y_center', 'mfit', 'qfit', 'psf_flux', 'sky', 'pixc', 'cexp', 'aobs', 'aexp', 'bobs', 'bexp', 'N' ])
		logging.info('{} PSFs in {}'.format(len(xym_tab), root))
	except ValueError:
		logging.info('No PSFs in {}'.format(root))
		return 1 

	#table has columns : ['psf_x_center' ,'psf_y_center', 'mfit', 'qfit', 'psf_flux', 'sky']
	return xym_tab


def get_files_metadata(rootnames):

	logging.info('Getting metadata from QL database.')
	
	midexps, filterss, apertures, ql_dirs, sun_angs, exptimes, fgs_locks = [], [], [], [], [], [], []
	for root in rootnames:
		results = ql_session.query(IR_flt_0.expstart, IR_flt_0.expend, IR_flt_0.filter, IR_flt_0.aperture, Master.dir, IR_flt_0.sunangle, IR_flt_0.exptime, IR_flt_0.fgslock).join(Master).filter(IR_flt_0.ql_root == root[0:8]).all()

		midexps.append(np.mean([results[0][0], results[0][1]]))
		filterss.append(results[0][2])
		apertures.append(results[0][3])
		ql_dirs.append(results[0][4])
		sun_angs.append(results[0][5])
		exptimes.append(results[0][6])
		fgs_locks.append(results[0][7])

	return (ql_dirs, midexps, filterss, apertures, exptimes, sun_angs, fgs_locks)


def get_ra_dec_wcs(file_path, x, y):

	hdu = fits.open(file_path)
	wcss = WCS(hdu[1].header, hdu)

	ra, dec = wcss.all_pix2world(x, y, 1)

	return(ra, dec)

def get_focus_parameters(midexp):
    """Update the psf_dict with focus model related information.

    The focus related parameters include the date/mjd of the closest
    model measurement in time to the observation, the time of the
    middle of the observation ('midexp', used to match against the
    model measurements) and the focus value.

    Parameters
    ----------
    rootnames: list 
    	list of 9 character file rootnames
    midexp : float
        The time of the middle of the observation, in MJD.

    Returns
    -------
    psf_dict : dict
        The dictionary that contains various psf parameters, now with
        focus information.
    """

    # Find all of the focus values within six minutes
    # Note that a separate session and engine must be created and closed
    # as to allow many parallel connections
    six_minutes = 0.00416667  # six minutes in units of days
  
    results = session.query(FocusModel.mjd, FocusModel.date, FocusModel.focus)\
        .filter(FocusModel.mjd >= float(midexp - six_minutes))\
        .filter(FocusModel.mjd <= float(midexp + six_minutes)).all()

    if len(results) > 0:
        mjds = [item[0] for item in results]
        dates = [item[1] for item in results]
        focus_values = [item[2] for item in results]

        # Find the focus closest in time to the observation
        delta_times = [abs(float(midexp) - float(mjd)) for mjd in mjds]
        index = delta_times.index(min(delta_times))
        mjd = float(mjds[index])
        date = dates[index]
        focus = focus_values[index]

    # If there are no surrounding focus measurements, then set the focus
    # measurements to NULL
    else:
        date, mjd, focus = None, None, None

    return (date, mjd, focus)


def main_make_ir_psf_table(filt='all'):

	filter_list = [filt]
	if filt == 'all':
		filter_list = [os.path.basename(x) for x in glob.glob(SETTINGS['output_dir']+'/F*')]

	for filt in filter_list:
		duplicate_entries = 0
		logging.info('Starting Processing for {}'.format(filt))
		#Get list of new rootnames to ingest 
		new_rootnames = get_new_files_to_ingest(filt)

		new_xym_file_paths = [SETTINGS['output_dir'] + '/{}/{}_flt.stardb_xym'.format(filt, root) for root in new_rootnames]
		ql_dirs, midexps, filterss, apertures, exptimes, sun_angs, fgs_locks = get_files_metadata(new_rootnames)

		for i, xym_file_path in enumerate(new_xym_file_paths):
			root = os.path.basename(xym_file_path)[0:9]
			ql_path = glob.glob(ql_dirs[i] + '/{}*flt.fits'.format(root))[0]
			psf_tab = parse_xym_file(xym_file_path)
			if psf_tab == 1:
				continue
			ra_psfs, dec_psfs = get_ra_dec_wcs(ql_path, psf_tab['psf_x_center'], psf_tab['psf_y_center'])

			psf_tab['psf_ra'] = ra_psfs
			psf_tab['psf_dec'] = dec_psfs
			psf_tab['midexp'] = [midexps[i]] * len(psf_tab)
			psf_tab['filter'] = [filterss[i]] * len(psf_tab)
			psf_tab['aperture'] = [apertures[i]] * len(psf_tab)
			psf_tab['exptime'] = [exptimes[i]] * len(psf_tab)
			psf_tab['sun_ang'] = [sun_angs[i]] * len(psf_tab)
			psf_tab['fgs_lock'] = [fgs_locks[i]] * len(psf_tab)

			# #focus model values
			date, mjd, focus = get_focus_parameters(midexps[i])
			psf_tab['date'] = [date] * len(psf_tab)
			psf_tab['mjd'] = [mjd] * len(psf_tab)
			psf_tab['focus'] = [focus] * len(psf_tab)

			#insert each psf into database
			for i, roww in enumerate(psf_tab):
				#Make row into dictionary 
				psf_record = dict()
				dict_keys = psf_tab.colnames
				for key in dict_keys:
					if str(psf_tab[key][i]) != 'None':
						psf_record[key] = str(psf_tab[key][i])
					else:
						psf_record[key] = None

				engine.execute(PSFTableMAST.__table__.insert(), psf_record)
			logging.info('Inserted {} psf records for {} into database'.format(len(psf_tab), root))
			
		
		# try:
		# 	engine.execute(PSFTableMAST.__table__.insert(), psf_record)
		# 	logging.info('Inserted {} psf records for {} into database'.format(len(psf_tab), root))
		# except:
		# 	duplicate_entries += 1



if __name__ == '__main__':


	module = os.path.basename(__file__).strip('.py')
	setup_logging(module)

	args = parse_args()
	main_make_ir_psf_table(args.filter)
	