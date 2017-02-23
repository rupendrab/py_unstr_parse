#!/usr/bin/env python3.5

import csv

def read(f, cols):
  r = csv.reader(f)
  # r = csv.reader(f, delimiter='~')
  for row in r:
    print([row[col-1] for col in cols])

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  if (len(args) >= 1):
    cols = [int(val) for val in args]
    f = sys.stdin
    read(f, cols)
