#!/usr/bin/env python

import sys
from predict_using_toc_mapper import Mapper, get_topic, read_model_file
from find_topics import toc_entries, get_summary_map, read_topics
import csv

def print_topics(topics):
  for topic in topics:
    print(topic + '*')

if __name__ == '__main__':
  modelfile = sys.argv[1]
  (origmap, sorted_y, vectorizer, le, grid_search) = read_model_file(modelfile)
  topics = toc_entries(origmap)
  mapper = Mapper(origmap, sorted_y, vectorizer, le, grid_search)
  # print(sorted_y)
  sorted_topics = sorted(topics, key=lambda x: x.lower())
  print_topics(sorted_topics)
  # print(len(origmap))
  if (len(sys.argv) > 2):
    f = open(sys.argv[2], 'w')
    writer = csv.writer(f)
    data = [[orig,"OK",mapped] for orig,mapped in origmap.items()]
    for line in data:
      writer.writerow(line)
    f.close()

