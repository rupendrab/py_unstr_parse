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
    arr = list(line)
    i = 0
    for c in arr:
      if ord(c) > 127:
        arr[i] = ' '
      i += 1
    sys.stdout.write(''.join(arr))

if __name__ == '__main__':
  args = sys.argv[1:]
  if (len(args) == 1):
    filename = args[0]
    process(filename)
