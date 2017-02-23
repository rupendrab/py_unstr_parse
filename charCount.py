#!/usr/bin/env python3.5

import sys
import re

def process(file):
  charFirstLine = {}
  chardict = {}
  f = open(file, 'r', encoding='utf8')
  lineno = 0
  for line in f:
    lineno += 1
    for c in list(line):
      v = chardict.get(ord(c))
      if v:
        chardict[ord(c)] = v + 1
      else:
        chardict[ord(c)] = 1
        charFirstLine[ord(c)] = lineno
  f.close()
  return chardict, charFirstLine

if __name__ == '__main__':
  args = sys.argv[1:]
  if (len(args) == 1):
    filename = args[0]
    chardict, charFirstLine = process(filename)
    for key in sorted(chardict.keys()):
      print("%s\t(%d)\t%d\tFirst line: %d" % (chr(key), key, chardict.get(key), charFirstLine.get(key)))
