"""This module contains the basic logging setup.

This module uses the Python logging library to configure a logger for
logging information in various scripts.  The resulting log file is
written to <log_dir>/<module_name>/<module_name>_<YYYY-MM-DD-HH-MM>.log

Authors
-------
    Clare Shanahan
    Frederick Dauphin 2021

Use
---
    This module is intended to be imported and used by various modules
    as such:

        from ir_psf.logging.psf_logging import setup_logging
        setup_logging(module_name)
"""

import datetime
import logging
import os

from irpsf.settings.settings import *

def setup_logging(module):
    """Set up the logging.

    Parameters
    ----------
    module : str
        Name of the module.
    """

    if not os.path.isdir(os.path.join(SETTINGS['log_dir'], module)):
    	print('Making directory {}'.format(os.path.join(SETTINGS['log_dir'], module)))
    	os.makedirs(os.path.join(SETTINGS['log_dir'], module))
    log_file = os.path.join(SETTINGS['log_dir'], module,
        module + '_' + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M') + '.log')
    logging.basicConfig(filename=log_file,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S %p',
                        level=logging.INFO)
