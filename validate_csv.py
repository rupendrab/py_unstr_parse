#!/usr/bin/env python3.5

import sys
import re
import os
import csv

def read_file(fname):
  f = open(fname, 'r')
  csv_reader = csv.reader(f)
  no_rows = 0
  for row in csv_reader:
    no_rows += 1
    no_cols = len(row)
    print("Row %d: columns = %d" % (no_rows, no_cols))
  f.close()
  print(".........")
  print("Number of records in csv file: %d" % no_rows)

if __name__ == '__main__':
  args = sys.argv[1:]
  for fl in args:
    print("File : %s" % fl)
    print("..................................")
    read_file(fl)
