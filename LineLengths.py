#!/usr/bin/env python3.5

import sys
import re

def process(file):
  charFirstLine = {}
  chardict = {}
  f = open(file, 'r')
  lineno = 0
  for line in f:
    lineno += 1
    print("%d\t%d" % (lineno, len(line)))
  f.close()

if __name__ == '__main__':
  args = sys.argv[1:]
  if (len(args) == 1):
    filename = args[0]
    process(filename)
