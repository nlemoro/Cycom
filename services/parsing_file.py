# -*- coding: utf8 -*-

from abc import ABCMeta, abstractmethod
import csv
import os
from werkzeug.datastructures import FileStorage

import xlrd
import xlwt

__author__ = 'linard_f'


class ParsingInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def append_line(self, line):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __getitem__(self, item):
        pass


class ParsingFile(ParsingInterface):

    def __init__(self, file):
        try:
            self.file = ParsingXls(file)
        except xlrd.XLRDError:
            self.file = ParsingCsv(file)

    def __iter__(self):
        return self

    def next(self):
        return self.file.next()

    def append_line(self, line):
        self.file.append_line(line)

    def __len__(self):
        return self.file.__len__()

    def __getitem__(self, item):
        return self.file.__getitem__(item.stop)


class ParsingXls(ParsingInterface):
    def __init__(self, file):
        self.file = file
        try:
            if type(file) is FileStorage or os.stat(file.name).st_size != 0:
                self.book = xlrd.open_workbook(file_contents=file.read())
                worksheetsList = self.book.sheet_names()
                self.worksheet = self.book.sheet_by_name(worksheetsList[0])
                self.nb_rows = self.worksheet.nrows
                self.nb_cols = self.worksheet.ncols
                file.seek(0)
            else:
                self.book = xlwt.Workbook()
                self.worksheet = self.book.add_sheet('Export')
                self.nb_rows = 0
                self.nb_cols = 0
        except TypeError:
            file.seek(0)
            raise xlrd.XLRDError()
        self.i = 0

    def __iter__(self):
        return self

    def next(self):
        if self.i == self.nb_rows:
            self.file.seek(0)
            raise StopIteration
        row = []
        j = 0
        while j != self.nb_cols:
            if type(self.worksheet.cell_value(self.i, j)) is float:
                cel = '{:g}'.format(self.worksheet.cell_value(self.i, j))
            else:
                cel = self.worksheet.cell_value(self.i, j)
            row.append(cel)
            j += 1
        self.i += 1
        return row

    def append_line(self, line):
        row, col = self.nb_rows, 0
        for it in line:
            self.worksheet.write(row, col, it)
            col += 1
        self.nb_rows += 1

    def __len__(self):
        return self.nb_rows

    def __getitem__(self, item):
        self.i = item
        return self


class ParsingCsv(ParsingInterface):
    def __init__(self, file):
        self.file = file
        self.writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
        self.reader = csv.reader(file, delimiter=";")
        file.seek(0)
        try:
            self.list = list(self.reader)
            self.len = len(self.list)
            file.seek(0)
        except IOError:
            self.len = 0
        self.i = 0

    def append_line(self, line):
        for i in range(0, len(line)):
            if type(line[i]) is unicode:
                line[i] = line[i].encode("utf-8")
        self.writer.writerow(line)

    def __iter__(self):
        return self

    def next(self):
        if self.i == self.len:
            self.i = 0
            raise StopIteration
        else:
            ret = self.list[self.i]
            self.i += 1
            return ret

    def __len__(self):
        return self.len

    def __getitem__(self, item):
        self.i = item
        return self