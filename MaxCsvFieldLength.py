#!/usr/bin/env python3.5

import sys
import re
import csv

def process(file):
  f = open(file, 'r')
  reader = csv.reader(f)
  lineno = 0
  for fields in reader:
    lineno += 1
    maxlen = 0
    maxfield = 0
    fieldno = 0
    for field in fields:
      fieldno += 1
      fieldlen = len(field)
      if (fieldlen > maxlen):
        maxlen = fieldlen
        maxfield = fieldno
    print("%d\t%d\t%d" % (lineno, maxfield, maxlen))
  f.close()

if __name__ == '__main__':
  args = sys.argv[1:]
  if (len(args) == 1):
    filename = args[0]
    process(filename)
