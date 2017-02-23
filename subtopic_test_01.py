#!/usr/bin/env python3.5

import sys
import re
import os
import csv
import json
# import numpy as np
# import pandas as pd
from itertools import groupby
from collections import OrderedDict

from extract_toc import parseargs
import find_topics
from predict_using_toc_mapper import Mapper, get_topic, read_model_file
from predict_using_subtopic_mapper import SubtopicPredictor
from analyze_topic import SubtopicReader

def main(args):
  argsmap = parseargs(args)

  files = argsmap.get('files')
  if (not files):
    sys.exit(0)

  topic = argsmap.get("topic")
  if (not topic):
    topic = "IT Assessment"
  else:
    topic = topic[0]

  summaryfile = argsmap.get("summary")
  if (not summaryfile):
    print("Summary file must be specified...")
    sys.exit(1)
  summaryfile = summaryfile[0]
  summary_map = find_topics.get_summary_map(summaryfile)

  tmodelfile = argsmap.get("tmodel")
  if (not tmodelfile):
    print('Topic Model must be specified. using --tmmodel ..')
    sys.exit(1)
  tmodelfile = tmodelfile[0]
  (origmap, sorted_y, vectorizer, le, grid_search) = read_model_file(tmodelfile)
  topics = find_topics.toc_entries(origmap)
  # print(topics)
  mapper = Mapper(origmap, sorted_y, vectorizer, le, grid_search)

  subtopicReader = SubtopicReader(topic, mapper, summary_map)

  smodelfile = argsmap.get("smodel")
  if (not smodelfile):
    print('Subtopic Model must be specified using --smodel ...')
    sys.exit(1)
  smodelfile = smodelfile[0]
  subtopicPredictor = SubtopicPredictor(smodelfile)
  
  for filename in files:
    subtopic_dict = subtopicReader.mapped_subtopics(filename, subtopicPredictor)
    subtopic_columns = subtopicReader.get_column_names(subtopicPredictor)
    print(json.dumps(subtopic_dict, indent=2))
    print('---------------------------------------')
    print(subtopic_columns)

if __name__ == '__main__':
  args = sys.argv[1:]
  main(args)
