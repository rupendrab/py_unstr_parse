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
  ratings.process_file(filename)
  ratings.map_ratings()
  improvement = 0
  for k in ratings.all_available_ratings:
    v = ratings.ratings_mapped.get(k)
    if not v:
      v = [None] * 3
    v_current = ratings.current_ratings_alt.get(k)
    if v_current:
      if (not v[0] or v[0] != v_current):
        improvement += 1
    elif (not v_current):
      if (v[0]):
        improvement -= 1
    print("%-30s %-2s/%-2s %-2s %-2s" % (k, nvl(v[0], "_"), nvl(v_current, "_"), nvl(v[1], "_"), nvl(v[2], "_")))
  # print(ratings.current_ratings_alt)
  print("")
  print("Number of improvements using new methodology = %d" % (improvement))
  print("")
  
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
