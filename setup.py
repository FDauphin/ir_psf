#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

setup(name = 'irpsf',
      description = 'WFC3 IR PSF Library Package',
      author = 'Space Telescope Science Institute',
      url = 'https://github.com/spacetelescope/ir_psf',
      packages = find_packages(),
      install_requires = ['astropy', 'matplotlib', 'numpy', 'pyyaml', 'scipy', 'sqlalchemy'])
