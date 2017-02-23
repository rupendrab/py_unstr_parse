#!/usr/bin/env python3.5

import sys
import re

def process(file, ignorelines):
  f = open(file, 'r')
  lineno = 0
  for line in f:
    lineno += 1
    lastChar = line[-1]
    rest = line[:-1]
    if lineno > ignorelines:
      rest = re.sub('[0-9]', '0', re.sub('[a-zA-Z]', 'A', rest))
    sys.stdout.write(rest)
    sys.stdout.write(lastChar)
  f.close()

if __name__ == '__main__':
  args = sys.argv[1:]
  if (len(args) == 2):
    filename = args[0]
    ignorelines = int(args[1])
    process(filename, ignorelines)
