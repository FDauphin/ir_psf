"""Read in a yaml configuration file that contains database
credentials and other parameters.

The yaml file should be placed in irpsf/scripts/config.yaml within
the local clone of the psf repository.

Authors
-------
    Alex Viana
    Clare Shanahan
    Frederick Dauphin 2021

Use
---
    This module is intended to be used by various modules, for example:

    from irpsf.settings.settings import SETTINGS
    my_connection_string = SETTINGS['connection_string']
"""

import os
import yaml

def get_settings():
    """Gets the setting information that we don't want burned into the repo.
    """

    with open('config.yaml', 'r') as f:
        data = yaml.load(f)
    return data

SETTINGS = get_settings()
