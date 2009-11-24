#    Copyright (C) 2006 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##############################################################################

# $Id$

"""This module contains routines for importing CSV data files
in an easy-to-use manner."""

import numpy as N

import datasets
import veusz.utils as utils

class _FileReaderCols(object):
    """Read a CSV file in rows. This acts as an iterator.

    This is a very simple wrapper around the csv module
    """

    def __init__(self, csvreader):
        self.csvreader = csvreader

    def next(self):
        """Return next row."""
        return self.csvreader.next()

class _FileReaderRows(object):
    """Read a CSV file in columns. This acts as an iterator.

    This means we have to read the whole file in, then return cols :-(
    """

    def __init__(self, csvreader):
        self.data = []
        self.maxlength = 0

        for line in csvreader:
            self.maxlength = max(self.maxlength, len(line))
            self.data.append(line)

        self.counter = 0

    def next(self):
        """Return the next column."""

        if self.counter == self.maxlength:
            raise StopIteration

        # probably is a better way to do this
        retn = []
        for row in self.data:
            if self.counter >= len(row):
                retn.append('')
            else:
                retn.append(row[self.counter])

        self.counter += 1
        return retn

class ReadCSV(object):
    """A class to import data from CSV files."""

    def __init__(self, filename, readrows=False, 
                 delimiter=',', textdelimiter='"',
                 encoding='utf_8',
                 prefix='', suffix=''):
        """Initialise the reader to import data from filename.

        If readrows is True, then data are read from columns, rather than
        rows

        prefix is a prefix to prepend to the name of datasets from this file
        """

        self.filename = filename
        self.readrows = readrows
        self.delimiter = delimiter
        self.textdelimiter = textdelimiter
        self.encoding = encoding
        self.prefix = prefix
        self.suffix = suffix

        # datasets. Each name is associated with a list
        self.data = {}

    def _generateName(self, column):
        """Generate a name for a column."""
        if self.readrows:
            prefix = 'row'
        else:
            prefix = 'col'

        name = '%s%s%i%s' % (self.prefix, prefix, column+1, self.suffix)
        return name

    def _getNameAndColType(self, colnum, colval):
        """Get column name and type."""

        s = colval.strip().split()
        name = s[0]
        coltype = s[-1]

        if name in ('+', '-', '+-'):
            # loop to find previous valid column
            prevcol = colnum - 1
            while prevcol >= 0:
                n = self.colnames[prevcol]
                if len(n) > 0 and n[-1] not in "+-":
                    name = n + name
                    return self.coltypes[prevcol], name
                prevcol -= 1
            else:
                # did not find anything
                name = self._generateName(colnum)

        if coltype == '(string)' or coltype == '(text)':
            t = 'string'
        elif coltype == '(date)' or coltype == '(time)':
            t = 'date'
        else:
            t = 'float'
        return t, self.prefix + name + self.suffix

    def _setNameAndType(self, colnum, colname, coltype):
        """Set a name for column number given column name and type."""
        while colnum >= len(self.coltypes):
            self.coltypes.append('')
        self.coltypes[colnum] = coltype
        self.nametypes[colname] = coltype
        self.colnames[colnum] = colname
        if colname not in self.data:
            self.data[colname] = []

    def readData(self):
        """Read the data into the document."""

        # FIXME: this is far too long
        # open the csv file
        csvf = utils.UnicodeCSVReader( open(self.filename),
                                       delimiter=self.delimiter,
                                       quotechar=self.textdelimiter,
                                       encoding=self.encoding )

        # make in iterator for the file
        if self.readrows:
            it = _FileReaderRows(csvf)
        else:
            it = _FileReaderCols(csvf)

        # dataset names for each column
        self.colnames = {}

        # type of column (float, string or date)
        self.coltypes = []
        # type of names of columns
        self.nametypes = {}

        # iterate over each line (or column)
        while True:
            try:
                line = it.next()
            except StopIteration:
                break

            # iterate over items on line
            for colnum, col in enumerate(line):

                if colnum >= len(self.coltypes) or self.coltypes[colnum] == '':
                    ctype = 'float'
                else:
                    ctype = self.coltypes[colnum]

                try:
                    # do any necessary conversion
                    if ctype == 'float':
                        v = float(col)
                    elif ctype == 'date':
                        v = utils.dateStringToDate(col)
                    elif ctype == 'string':
                        v = col

                except ValueError:
                    # not a number, so generate a dataset name

                    # skip blanks
                    col = col.strip()
                    if col == '':
                        continue

                    coltype, name = self._getNameAndColType(colnum, col)
                    self._setNameAndType(colnum, name, coltype)

                else:
                    # generate a name if required
                    if colnum not in self.colnames:
                        self._setNameAndType(colnum, self._generateName(colnum),
                                             'float')

                    # conversion okay
                    # append number to data
                    coldata = self.data[self.colnames[colnum]]
                    coldata.append(v)

    def setData(self, document, linkedfile=None):
        """Set the read-in datasets in the document."""

        # iterate over each read-in dataset
        dsnames = []
        for name in self.data.iterkeys():

            # skip error data here, they are used below
            if name[-1] in '+-':
                continue

            dsnames.append(name)

            # get data and errors (if any)
            data = self.data[name]
            serr = self.data.get(name+'+-', None)
            perr = self.data.get(name+'+', None)
            nerr = self.data.get(name+'-', None)

            # normal dataset
            if self.nametypes[name] == 'string':
                ds = datasets.DatasetText(data=data, linked=linkedfile)
            else:
                ds = datasets.Dataset(data=data, serr=serr, perr=perr,
                                      nerr=nerr, linked=linkedfile)
            document.setData(name, ds)

        dsnames.sort()
        return dsnames
