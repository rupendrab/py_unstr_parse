#!/usr/bin/env python3.5

import sys
import re
import os
import csv

from extract_toc import parseargs
from get_ratings import Ratings, Ratings2

def nvl(v1,v2):
  if v1:
    return v1
  else:
    return v2

def process_ratings_for_file(ratings, filename):
  header_columns = ratings.get_column_headers()
  headers = ratings.all_available_ratings
  ratings.process_file(filename)
  ratings.map_ratings()
  data = ratings.get_column_data()
  if (len(data) != len(header_columns)):
    print("**** Invalid data encountered!!!!")
  for i in range(0, len(data), 5):
    print("%-30s %2s %-2s %-2s %-2s %-2s" % (headers[int(i/5)], nvl(data[i], "_"), nvl(data[i+1], "_"), nvl(data[i+2], "_"), nvl(data[i+3], "_"), nvl(data[i+4], "_")))
  
def main(args):
  argsmap = parseargs(args)
    
  files = argsmap.get('files')
  if (not files):
    sys.exit(0)

  ratings_mapper_file = argsmap.get("rmap")
  if ratings_mapper_file:
    ratings_mapper_file = ratings_mapper_file[0]
  if not ratings_mapper_file:
    print("Ratings Mapper File file name must be entered using the --rmap option...")
    sys.exit(1)

  ratings = Ratings(ratings_mapper_file)
  
  for filename in files:
    print("Processing file: " + filename)
    print("============================")
    process_ratings_for_file(ratings, filename)

if __name__ == '__main__':
  args = sys.argv[1:]
  main(args)
