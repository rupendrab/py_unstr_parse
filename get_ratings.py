#!/usr/bin/env python3.5

import re
import sys
import csv
import os
from extract_toc import parseargs

def readfile(filename):
  for line in open(filename, 'r', encoding='latin1'):
    yield(line[:-1])

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

class Ratings(object):

  def __init__(self, mapfilename=None):
    self.headpat = re.compile('^\s+(current\s+exam)[\s\.]+(prior\s+exam)[\s\.]+(prior\s+exam)\s*$', re.IGNORECASE)

    self.table_pattern_strings = [
      '^\s{5,}.*$',
      '^.\s{5,}.*$',
      '^\s*$'
    ]

    self.table_patterns = [re.compile(pat, re.IGNORECASE) for pat in self.table_pattern_strings]

    self.nm_exc_start_pattern = re.compile("^[^\s]\s{3,}(.*)$")
    self.mapfilename = mapfilename
    if mapfilename:
      self.use_mapfile(mapfilename)
      self.create_re_parser_current()

  def use_mapfile(self, mapfilename):
    self.ratings_map = {}
    mapfl = open(mapfilename, 'r')
    mapreader = csv.reader(mapfl)
    for row in mapreader:
      if (len(row) == 1):
        self.ratings_map[row[0]] = row[0]
      elif (len(row) == 2):
        self.ratings_map[row[0]] = row[1]
    if mapfl:
      mapfl.close()
    self.get_distinct_ratings()
    return self.ratings_map

  def create_re_parser_current(self):
    self.re_parser_current = []
    valid_keys = [k for k,v in self.ratings_map.items() if v != 'NA']
    # for exp in self.all_available_ratings:
    for exp in valid_keys:
      # print(exp)
      re_str = "^(%s)(\s{1,10}|\s{0,10}[\-:]{1}\s{0,10})([0-9A-Z]{1})\s*$" % (re.escape(exp))
      # print(re_str)
      re_pat = re.compile(re_str, re.IGNORECASE)
      self.re_parser_current.append(re_pat)
    # print(len(self.re_parser_current))

  def get_rating_from_anycase(self, k):
    # match = [k1 for k1 in self.all_available_ratings if k1.lower() == k.lower()]
    match = [v1 for k1,v1 in self.ratings_map.items() if k1.lower() == k.lower()]
    if match and len(match) == 1:
      return match[0]

  def match_current_rating(self, line):
    for pat in self.re_parser_current:
      m = pat.match(line)
      if m:
        # print("Matched" + str(pat))
        rating_anycase = m.group(1)
        rating_actual = self.get_rating_from_anycase(rating_anycase)
        rating_value = m.group(3)
        self.current_ratings_alt[rating_actual] = rating_value
        # print(rating_actual, rating_value)
        return(rating_actual, rating_value)

  def get_distinct_ratings(self):
    self.all_available_ratings = sorted(list(set([v for k,v in self.ratings_map.items() if v != 'NA'])))
    return self.all_available_ratings

  def get_column_headers(self):
    return [rating_name + ' ' + period for rating_name in self.all_available_ratings for period in ['current', 'from headers current', 
                                                                                                    'from table current', 'prior', 'prior prior']]

  def get_rating_value(self, rating_name, period):
    fh = self.current_ratings_alt.get(rating_name)
    data = self.ratings_mapped.get(rating_name)
    if (not data or len(data) != 3):
      data = [''] * 3
    combined = fh
    if not combined:
      combined = data[0]
    fulldata = [combined, fh] + data
    return fulldata[period]

  def get_column_data(self):
    return [self.get_rating_value(rating_name, period) for rating_name in self.all_available_ratings for period in range(5)]

  def header_start(self, ln):
    self.header = self.headpat.match(ln)
    return self.header

  def header_end(self, ln):
    for pat in self.table_patterns:
      if pat.match(ln):
        return False
    return True

  def parse_rating_line(self, ln):
    ratings = []
    for i in range(1,3):
      rating = ln[self.header.start(i):self.header.end(i)].strip().upper()
      ratings.append(rating)
    rating = ln[self.header.start(3):].strip().upper()
    ratings.append(rating)
    if any(ratings):
      ratings = [Ratings.format_rating(rating_code) for rating_code in ratings]
      rating_name = ln[0:self.header.start(1)].strip()
      rating_name = self.format_rating_name(rating_name)
      return rating_name, ratings

  @staticmethod
  def format_rating(rating_code):
    ## Remove anything other than alphanumeric characters from ratings
    return re.sub("[^0-9a-zA-Z]", "", rating_code)

  def format_rating_name(self, nm):
    nm_new = nm
    m = self.nm_exc_start_pattern.match(nm_new)
    if (m):
      nm_new = m.group(1)
    nm_new = re.sub("[0-9'\-\*\,]", "", nm_new)
    nm_new = re.sub("\(.*\)", "", nm_new)
    nm_new = re.sub("\s+", " ", nm_new)
    return nm_new.strip()

  def reveal_in_file(self, filename):
    h_start = None
    h_end = None
    for line in readfile(filename):
      if (not h_start):
        h_start = self.header_start(line)
        if h_start:
          print(line)
      else:
        h_end = self.header_end(line)
        print(line)
        if (h_end):
          break

  def process_file(self, filename):
    self.filename = filename
    self.ratings = []
    self.current_ratings_alt = {}
    h_start = None
    h_end = None
    for line in readfile(filename):
      if self.mapfilename:
        self.match_current_rating(line)
      if (not h_start):
        h_start = self.header_start(line)
      else:
        if not h_end:
          h_end = self.header_end(line)
          if (not h_end):
            rating_data = self.parse_rating_line(line)
            if (rating_data):
              self.ratings.append(rating_data)
    return self.ratings

  def map_ratings(self):
    self.ratings_mapped = {}
    if (not self.ratings):
      return
    for rating in self.ratings:
      rating_name = self.ratings_map.get(rating[0].title())
      if not rating_name:
        eprint('Warning: Rating name "%s" is ignored as it is not mapped, please handle it in your mapper file' % rating[0])
      if (rating_name != 'NA'):
        self.ratings_mapped[rating_name] = rating[1]
    return self.ratings_mapped

  def read_all_files(self, files, reveal = False, outfile = None, distinctfile = None):
    if not outfile:
      writer = csv.writer(sys.stdout)
    else:
      outfl = open(outfile, 'w')
      writer = csv.writer(outfl)

    self.ratings_set = set()
    for filename in files:
      if reveal:
        print("")
        print(filename)
        print("===========================================================================")
        self.reveal_in_file(filename)
      else:
        ratings = self.process_file(filename)
        flname = os.path.basename(filename)
        for rating in ratings:
          out_data = [flname, rating[0], rating[1][0], rating[1][1], rating[1][2]]
          writer.writerow(out_data)
          self.ratings_set.add(rating[0].title())

    if (outfl):
      outfl.close()

    if (distinctfile):
      distinctfl = open(distinctfile, 'w')
      for rat in sorted(list(self.ratings_set)):
        distinctfl.write(rat + "\n")
      distinctfl.close()

## Class Ratings2 is defined to handle another format for the Ratings table(e.g. CHI04022015091020.txt) . 
## This is not fully implemeneted as these are state exam files and do not need to be parsed currently.
class Ratings2(Ratings):

  def __init__(self, mapfilename):
    self.headpat_1 = re.compile('^\s+(current)[\s\.]+(prior)[\s\.]+(prior)\s*$', re.IGNORECASE)
    self.headpat_2 = re.compile('^.*\s+(Examination)[\s\.]+(Examination)[\s\.]+(Examination)\s*$', re.IGNORECASE)

    ## Blank line or a line containing 5 or more spaces
    self.table_pattern_strings = [
      '^.*\s{5,}.*$',
      '^\s*$'
    ]

    self.table_patterns = [re.compile(pat, re.IGNORECASE) for pat in self.table_pattern_strings]

    self.nm_exc_start_pattern = re.compile("^[^\s]\s{3,}(.*)$")
    self.use_mapfile(mapfilename)
    self.header = None
    self.header_1 = None
    self.header_2 = None
    self.header_lno = 0

  def header_start(self, ln):
    if re.match('^\s*$', ln):
      return None
    self.header_lno += 1
    if (not self.header_1):
      self.header_1 = self.headpat_1.match(ln)
      self.header_1_lno = self.header_lno
    else:
      self.header_2 = self.headpat_2.match(ln)
      self.header_2_lno = self.header_lno
      if (self.header_2 and self.header_2_lno == self.header_1_lno + 1):
        self.header = self.header_2
      else:
        self.header_1 = None
        self.header_2 = None
    return self.header

  def header_end(self, ln):
    for pat in self.table_patterns:
      if pat.match(ln):
        return False
    return True

def main(args):
  argsmap = parseargs(args)
  # print(args_dict)

  files = argsmap.get('files')
  if (not files):
    sys.exit(0)
 
  reveal = argsmap.get('reveal')
  if (reveal == []):
    read_all_files(files, True)
  else:
    outfile = argsmap.get('out')
    if (outfile):
      outfile = outfile[0]
    distinctfile = argsmap.get('distinct')
    if (distinctfile):
      distinctfile = distinctfile[0]
    ratings = Ratings()
    ratings.read_all_files(files, False, outfile, distinctfile)

if __name__ == '__main__':
  from sys import argv
  args = argv[1:]
  main(args)
  sys.exit(0)
