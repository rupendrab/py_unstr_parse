#!/usr/bin/env python3.5

import sys
import re
import os
import csv
import numpy as np
import pandas as pd

from extract_toc import parseargs
from predict_using_toc_mapper import Mapper, get_topic, read_model_file

ignore = [
  re.compile('.*\(\s*continued\s*\).*', re.IGNORECASE),
  re.compile('(^|\s+)Table\s*of\s*Contents(\s+|$)', re.IGNORECASE),
  re.compile('^\s*$')
]

ending_with_numbers = re.compile('^\s*(.*)?\s{20,}[\-/a-zA-Z0-9\s]*$')

debug=True

def print_debug(*args):
  if (debug):
    print(args)

def eleminate_ending_numbers(line):
  matched = ending_with_numbers.match(line.strip())
  if matched:
    return eleminate_ending_numbers(matched.group(1))
  else:
    return line

def readfile(filename):
  for line in open(filename, 'r', encoding='latin1'):
    yield(line[:-1])

def read_topics(filename, mapper, guess_allowed):
  # print("Guess allowed", guess_allowed)
  lineno = 0
  start_char = 0
  topic_list = []
  ff = chr(12)
  for line in readfile(filename):
    lineno += 1
    linelen = len(line.replace(ff, ""))
    start_char += linelen + 2
    # if re.match('^.*Examination Conclusions and Comments.*$', line):
    if (line and len(line) > 1 and ord(line[0]) == 12): ## Line starts with a control-L
      line_act = line[1:]
      # print("May be header:", line_act)
      ignore_line = False
      for pat in ignore:
        if (pat.match(line_act)):
          ignore_line = True
          break
      # if (line_act.isupper()): ## Ignore all uppercase lines
      #   ignore_line = True
        
      if not ignore_line:
        topic = eleminate_ending_numbers(line_act)
        if (not topic):
          continue
        translated_topic, score, determination_type = get_topic(topic, mapper)
        # print(translated_topic)
        if (score <= 0):
          continue
        # print_debug(topic, translated_topic, score, determination_type)
        if (not guess_allowed and determination_type == 'guess'):
          continue
        if (determination_type == 'guess'):  ## If guess, should not start with whitespace ???
          if re.match('^\s+.*', topic):
             continue
        if (len(topic_list) > 0 and topic_list[-1][2] == translated_topic): ## Ignore if same topic repeated
          continue
        # print_debug(lineno, topic, translated_topic)
        topic_list.append((lineno - 1, topic, translated_topic, start_char - linelen))
  return topic_list

def read_all_files(files, mapper, summary_map):
  writer = csv.writer(sys.stdout)
  for filename in files:
    no_topics = summary_map.get(os.path.basename(filename))
    guess_allowed = False
    if (not no_topics or no_topics == 0):
      guess_allowed = True
    topic_list = read_topics(filename, mapper, guess_allowed)
    for topic in topic_list:
      print(topic)
    writer.writerow([os.path.basename(filename), len(topic_list)])

def ifelse(condition, true_value, false_value):
  if (condition):
    return true_value
  else:
    return false_value
  
def get_summary_map(summaryfile):
  summary_map = {}
  if not summaryfile:
    return summary_map
  data = pd.read_csv(summaryfile, header=None)
  summary_map = dict(zip(np.array(data[0]),np.array(data[1])))
  return summary_map

def toc_entries(origmap):
  return sorted(set(v for v in origmap.values()))

def main(args):
  argsmap = parseargs(args)
  # print(args_dict)

  files = argsmap.get('files')
  if (not files):
    sys.exit(0)

  summaryfile = argsmap.get("summary")[0]
  summary_map = get_summary_map(summaryfile)
  # print(summary_map)

  modelfile = argsmap.get("model")
  if (not modelfile):
    print('Model must be specified...')
    sys.exit(1)
  modelfile = modelfile[0]
  (origmap, sorted_y, vectorizer, le, grid_search) = read_model_file(modelfile)
  topics = toc_entries(origmap)
  # print(topics)
  mapper = Mapper(origmap, sorted_y, vectorizer, le, grid_search)

  read_all_files(files, mapper, summary_map) 

if __name__ == '__main__':
  from sys import argv
  args = argv[1:]
  main(args)
  sys.exit(0)
