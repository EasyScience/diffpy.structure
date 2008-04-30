########################################################################
#
# Structure         by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2006 trustees of the Michigan State University.
#                   All rights reserved.
#
# File coded by:    Pavol Juhas
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
########################################################################

"""classes related to structure of materials
Classes:
    Atom
    Lattice
    Structure
    PDFFitStructure
Exceptions:
    StructureFormatError
    LatticeError
    SymmetryError
"""

__id__ = "$Id$"

##############################################################################
# interface definitions
##############################################################################

from structure import Structure
from lattice import Lattice
from atom import Atom
from pdffitstructure import PDFFitStructure
from StructureErrors import StructureFormatError
from StructureErrors import LatticeError
from StructureErrors import SymmetryError

# obtain version information
from pkg_resources import get_distribution
__version__ = get_distribution(__name__).version

# cleanup what should not get imported
del get_distribution

# End of file