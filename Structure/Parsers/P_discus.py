########################################################################
#
# Structure         by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2007 trustees of the Michigan State University.
#                   All rights reserved.
#
# File coded by:    Pavol Juhas
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
########################################################################

"""Parser for DISCUS structure format
"""

__id__ = "$Id$"

import sys
import numpy

from import_helper import PDFFitStructure, Lattice, Atom
from import_helper import InvalidStructureFormat
from StructureParser import StructureParser

class P_discus(StructureParser):
    """Parser for DISCUS structure format.  The parser chokes
    on molecule and generator records.
    """

    def __init__(self):
        StructureParser.__init__(self)
        self.format = "discus"
        # helper variables
        self.nl = None
        self.lines = None
        self.line = None
        self.stru = None
        self.cell_read = False
        self.ncell_read = False
        return

    def parseLines(self, lines):
        """Parse list of lines in DISCUS format.

        Return PDFFitStructure instance or raise InvalidStructureFormat.
        """
        self.lines = lines
        ilines = self.linesIterator()
        self.stru = PDFFitStructure()
        record_parsers = {
            "cell" : self._parse_cell,
            "format" : self._parse_format,
            "generator" : self._parse_not_implemented,
            "molecule" : self._parse_not_implemented,
            "ncell" : self._parse_ncell,
            "spcgr" : self._parse_spcgr,
            "symmetry" : self._parse_not_implemented,
            "title" : self._parse_title,
        }
        try:
            # parse header
            for self.line in ilines:
                words = self.line.split()
                if not words or words[0][0] == '#': continue
                if words[0] == 'atoms':             break
                rp = record_parsers.get(words[0], self._parse_invalid_record)
                rp(words)
            # check if cell has been defined
            if not self.cell_read:
                emsg = "%d: unit cell not defined" % self.nl
                raise InvalidStructureFormat, emsg
            # parse atoms
            for self.line in ilines:
                words = self.line.split()
                if not words or words[0][0] == '#': continue
                self._parse_atom(words)
            # self consistency check
            exp_natoms = reduce(lambda x,y : x*y, self.stru.pdffit['ncell'])
            # only check if ncell record exists
            if self.ncell_read and exp_natoms != len(self.stru):
                emsg = 'Expected %d atoms, read %d.' % \
                    (exp_natoms, len(self.stru))
                raise InvalidStructureFormat, emsg
            # take care of superlattice
            if self.stru.pdffit['ncell'][:3] != [1,1,1]:
                latpars = list(self.stru.lattice.abcABG())
                superlatpars = [ latpars[i]*self.stru.pdffit['ncell'][i]
                                 for i in range(3) ] + latpars[3:]
                superlattice = Lattice(*superlatpars)
                self.stru.placeInLattice(superlattice)
                self.stru.pdffit['ncell'] = [1, 1, 1, exp_natoms]
        except (ValueError, IndexError):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            emsg = "%d: file is not in DISCUS format" % self.nl
            raise InvalidStructureFormat, emsg, exc_traceback
        return self.stru
    # End of parseLines

    def toLines(self, stru):
        """Convert Structure stru to a list of lines in DISCUS format.
        Return list of strings.
        """
        self.stru = stru
        # if necessary, convert self.stru to PDFFitStructure
        if not isinstance(stru, PDFFitStructure):
            self.stru = PDFFitStructure(stru)
        # here we can start
        self.lines = lines = []
        lines.append( "title   " + self.stru.title.strip() )
        lines.append( "spcgr   " + self.stru.pdffit["spcgr"] )
        lines.append( "cell   %9.6f, %9.6f, %9.6f, %9.6f, %9.6f, %9.6f" %
                self.stru.lattice.abcABG() )
        lines.append( "ncell  %9i, %9i, %9i, %9i" % (1, 1, 1, len(self.stru)) )
        lines.append( "atoms" )
        for a in self.stru:
            lines.append( "%-4s %17.8f %17.8f %17.8f %12.4f" % (
                a.element.upper(), a.xyz[0], a.xyz[1], a.xyz[2], a.Biso() ))
        return lines
    # End of toLines

    def linesIterator(self):
        """Iterator over self.lines, which increments self.nl
        """
        # ignore trailing empty lines 
        stop = len(self.lines)
        while stop > 0 and self.lines[stop-1].strip() == "":
            stop -= 1
        self.nl = 0
        # read header of PDFFit file
        for self.line in self.lines[:stop]:
            self.nl += 1
            yield self.line
        # end of linesIterator

    def _parse_cell(self, words):
        """Process the cell record from DISCUS structure file.
        """
        # split again on spaces or commas
        words = self.line.replace(',', ' ').split()
        latpars = [ float(w) for w in words[1:7] ]
        try:
            self.stru.lattice.setLatPar(*latpars)
        except ZeroDivisionError:
            emsg = "%d: Invalid lattice parameters - zero cell volume" % \
                    self.nl
            raise InvalidStructureFormat, emsg
        self.cell_read = True
        return

    def _parse_format(self, words):
        """Process the format record from DISCUS structure file.
        """
        if words[1] == 'pdffit':
            emsg = "%d: file is not in DISCUS format" % self.p_nl
            raise InvalidStructureFormat, emsg
        return

    def _parse_ncell(self, words):
        """Process the ncell record from DISCUS structure file.
        """
        # split again on spaces or commas
        words = self.line.replace(',', ' ').split()
        self.stru.pdffit['ncell'] = [ int(w) for w in words[1:5] ]
        self.ncell_read = True
        return

    def _parse_spcgr(self, words):
        """Process the spcgr record from DISCUS structure file.
        """
        self.stru.pdffit['spcgr'] = ''.join(words[1:])
        return

    def _parse_title(self, words):
        """Process the title record from DISCUS structure file.
        """
        self.stru.title = self.line.lstrip()[5:].strip()
        return

    def _parse_atom(self, words):
        """Process atom records in DISCUS structure file.
        """
        element = words[0][0:1].upper() + words[0][1:].lower()
        xyz = [float(w) for w in words[1:4]]
        Biso = float(words[4])
        a = Atom(element, xyz)
        a.setBiso(Biso)
        self.stru.append(a)
        return

    def _parse_invalid_record(self, words):
        """Process invalid record in DISCUS structure file.
        Raises InvalidStructureFormat.
        """
        emsg = "%d: Invalid DISCUS record %r." % \
                (self.nl, words[0])
        raise InvalidStructureFormat, emsg

    def _parse_not_implemented(self, words):
        """Process the unimplemented records from DISCUS structure file.
        Raises NotImplementedError.
        """
        emsg = "%d: reading of DISCUS record %r is not implemented." % \
                (self.nl, words[0])
        raise NotImplementedError, emsg

# End of class P_pdffit

# Routines

def getParser():
    return P_discus()

# End of file