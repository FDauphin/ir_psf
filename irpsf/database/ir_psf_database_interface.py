#! /usr/bin/env python

"""Defines and creates the tables in the ir_psf database.

This script provides the Object Relational Mappings (ORMs) for the
various tables in the psf database.  Execution of this script will
create the following tables:

    (1) ir_psf
    (2) ir_psf_mast
    (2) focus

Note that the tables are only created, not populated.  See the various
scripts in the scripts / directory for software that populates the
tables.

The load_connection() function within this module allows the user
to connect to the psf database via the session, base, and engine
objects (described below).

The engine object serves as the low-level database API and perhaps most
importantly contains dialects which allows the sqlalchemy module to
communicate with the database.

The base object serves as a base class for class definitions.  It
produces Table objects and constructs ORMs.

The session object manages operations on ORM-mapped objects, as
construced by the base.  These operations include querying, for
example.

Authors
-------

    Clare Shanahan 2019

Use
---

    This script is intended to be imported from other various psf-
    related modules, but can also be executed via the command line:

        >>> python ir_psf_database_interface.py
"""

from irpsf.settings.settings import *

from sqlalchemy import Binary
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import DECIMAL
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker


def loadConnection(connection_string):
    """Returns session, base, and engine objects for connecting to ir_psf databse.

    Parameters
    ----------
    connection_string : str
        The connection string to connect to the psf database. The
        connection string should take the form:
        ``dialect+driver://username:password@host:port/database``

    Returns
    -------
    session : sesson object
        Provides a holding zone for all objects loaded or associated
        with the database.
    base : base object
        Provides a base class for declarative class definitions.
    engine : engine object
        Provides a source of database connectivity and behavior.
    """

    engine = create_engine(connection_string, echo=False, pool_timeout=259200)
    Base = declarative_base(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    return session, Base, engine

# Instantiate the session, base, and engine objects so they can easily
# be imported (e.g. from psf.database.database_interface import session)
session, Base, engine = loadConnection(SETTINGS['psf_connection_string'])

class PSFTableMAST(Base):
    """ORM for the psf_mast table."""

    __tablename__ = 'ir_psf_mast'
    id = Column(Integer(), nullable=False, primary_key=True)
    rootname = Column(String(17), nullable=False, index=True)
    filter = Column(String(25), nullable=False, index=True)
    aperture = Column(String(50), nullable=False, index=True)
    psf_x_center = Column(Float(), nullable=False, index=True)
    psf_y_center = Column(Float(), nullable=False, index=True)
    psf_ra = Column(Float(), nullable=False, index=True)
    psf_dec = Column(Float(), nullable=False, index=True)
    psf_flux = Column(Float(), nullable=False)
    sky = Column(Float(12), nullable=False)
    qfit = Column(Float(8), nullable=True)
    pixc = Column(Float(8), nullable=True)
    midexp = Column(DECIMAL(12, 5), index=True, nullable=False)
    mjd = Column(DECIMAL(12, 5), index=True, nullable=True)
    date = Column(DateTime(), index=True, nullable=True)
    focus = Column(Float(15), nullable=True)
    __table_args__ = (UniqueConstraint('rootname', 'psf_x_center',
                      'psf_y_center', name='psf_mast_uniqueness_constraint'),)


class FocusModel(Base):
    """ORM for the table storing individual focus measurement information."""

    __tablename__ = 'focus_model'
    id = Column(Integer(), primary_key=True)
    mjd = Column(DECIMAL(12, 5), index=True, nullable=False)
    date = Column(DateTime(), index=True, nullable=False)
    focus = Column(Float(), nullable=False)
    __table_args__ = (UniqueConstraint('mjd',
                      name='focus_model_uniqueness_constraint'),)


if __name__ == '__main__':

    Base.metadata.create_all()
