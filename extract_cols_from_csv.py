#!/usr/bin/env python3.5

import sys
import re
import os
import csv

rangepattern = re.compile("^([0-9]+)\-([0-9]+)$")
numberpattern = re.compile("^[0-9]+$")

def read_file(fname, cols):
  f = open(fname, 'r')
  csv_reader = csv.reader(f)
  writer = csv.writer(sys.stdout)
  no_rows = 0
  for row in csv_reader:
    no_rows += 1
    out = [row[i] for i in cols]
    writer.writerow(out)
  f.close()

def get_columns(columnargs):
  cols = []
  for arg in columnargs:
    m = rangepattern.match(arg)
    if m:
      st = int(m.group(1))
      en = int(m.group(2))
      if (en >= st):
        cols += list(range(st-1, en))
    else:
      m = numberpattern.match(arg)
      if m:
        cols.append(int(arg))
  return sorted(list(set(cols)))

def main(args):
  if (len(args) < 2):
    print("Usage: extract_cols_from_csv.py <File Name> <Columns m1-n1 m2-n2 n3>")
    sys.exit(1)
  fl = args[0]
  cols = get_columns(args[1:])
  read_file(fl, cols)

if __name__ == '__main__':
  args = sys.argv[1:]
  main(args)
