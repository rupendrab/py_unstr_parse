#!/usr/bin/env python3.5

import re
import sys
import csv
import os
from extract_toc import parseargs

cr_pat = re.compile("(^|\W)component ratings\W+([^ ]*)", re.IGNORECASE)
roca_pat = re.compile("(^|\W)roca rating\W+([^ ]*)", re.IGNORECASE)

def get_ratings(str, pat):
  try:
    return [val for p in pat.findall(str) for val in p[1].split("-")]
  except Exception as e:
    return []

def get_if_len_is(arr, l):
  if (arr and len(arr) == l):
    return arr
  else:
    return []

def get_component_ratings(str):
  return get_if_len_is(get_ratings(str, cr_pat), 6)

def get_roca_ratings(str):
  return get_if_len_is(get_ratings(str, roca_pat), 4)

def readfile(filename):
  for line in open(filename, 'r', encoding='latin1'):
    yield(line[:-1])

def get_ratings_in_file(filename):
  cr = []
  roca = []
  for line in readfile(filename):
    cr_line = get_component_ratings(line)
    if cr_line:
      cr = cr_line
    roca_line = get_roca_ratings(line)
    if roca_line:
      roca = roca_line
  return (cr, roca)

def read_all_files(files):
  no_files_with_ratings = 0
  writer = csv.writer(sys.stdout)
  for filename in files:
    cr, roca = get_ratings_in_file(filename)
    if (cr or roca):
      no_files_with_ratings += 1
    writer.writerow([os.path.basename(filename), cr, roca])
  return no_files_with_ratings

def main(args):
  argsmap = parseargs(args)
  # print(args_dict)

  files = argsmap.get('files')
  if (not files):
    sys.exit(0)

  no_files_with_ratings = read_all_files(files)
  print("\nNumber of files with ratings = %d" % no_files_with_ratings)

if __name__ == '__main__':
  from sys import argv
  args = argv[1:]
  main(args)
  sys.exit(0)
