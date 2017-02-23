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

from headerutil import *

START_SUBTOPIC="Initial"

def readfile(filename):
  for line in open(filename, 'r', encoding='latin1'):
    yield(line[:-1])

def file_lines(filename):
  file_lines = []
  for line in readfile(filename):
    file_lines.append(line)
  return file_lines

def subtopic_finder(): 
  p_seq = re.compile('^[0-9]+[\.\)\-]')
  p_starting_with_space = re.compile("^\s+.*$")
  p_no_alnum = re.compile("[^a-z0-0]")
  from nltk.tag.perceptron import PerceptronTagger
  tagger = PerceptronTagger()
  ignore_tags = ['$', '(', ')', ',', '--', '.', '::', 'CC', 'CD', 'IN', 'TO']

  def pos_tag(tokens):
    return tagger.tag(tokens) 
  
  def is_invalid_topic(words):
    words = [word for word in words if word]
    tagged = pos_tag(words)
    any_not_capitalized = any([not (w.isupper() or w.istitle()) for w, tag in tagged if tag not in ignore_tags])
    all_numeric = all([tag == 'CD' for w, tag in tagged])
    return all_numeric or any_not_capitalized
 
  def is_subtopic(str):
    if p_starting_with_space.match(str):
      return False
    str = str.strip()
    if not str:
      return False
    if str[-1] == '.' or str[-1] == '"':
      return False
    words = re.split("\s+|\s*[/\-,]\s*", str)
    words_spaced_by_5_or_less = re.split("\s{1,5}|\s{0,5}[/\-]\s{0,5}", str)
    if (len(words_spaced_by_5_or_less) > len(words)):
      return False
    no_words = len(words)
    # print(words)
    if (no_words > 10):
      return False
    ### If starts with a numbered sequence, continue with matching the rest
    m = p_seq.match(words[0])
    if m:
      words = words[1:]
    if (not (words[0].isupper() or words[0].istitle())):
      return False
    return not is_invalid_topic(words)

  def normalize(topic_text):
    # In preparation for using topic text for supervised learning of categorization:
    #   Replace all . / ( ) and - characters by space
    #   Delete all all-lowercase words
    #   Delete number only words
    #   Convert all words to lowercase
    #   Return array of words
    words = re.split("\s+|\s*[\(\)\./\-,]\s*", topic_text)
    words = [p_no_alnum.sub("", word.lower()) for word in words if word and not word.isnumeric() and not word.islower()]
    words = [word for word in words if word]
    return words

  return is_subtopic, pos_tag, normalize

def get_subtopics(is_subtopic, lines, start, end):
  subtopics = OrderedDict()
  current_topic = START_SUBTOPIC
  current_topic_lines = []
  for line in lines[start:end]:
    if is_subtopic(line):
      if (len(current_topic_lines) > 0):
        subtopics[current_topic] = current_topic_lines
      current_topic = line
      current_topic_lines = []
    else:
      current_topic_lines.append(line)
  if (len(current_topic_lines) > 0):
    subtopics[current_topic] = current_topic_lines
  return subtopics

class SubtopicReader:

  def __init__(self, topic, mapper, summary_map):
    self.topic = topic
    self.mapper = mapper
    self.summary_map = summary_map
    self.is_subtopic, self.pos_tag, self.normalize = subtopic_finder()

  def read_file(self, filename, print_details=False):
    retval = {}
    lines = file_lines(filename)
    no_topics = self.summary_map.get(os.path.basename(filename))
    guess_allowed = False
    if (not no_topics or no_topics == 0):
      guess_allowed = True
    topic_list = find_topics.read_topics(filename, self.mapper, guess_allowed)
    # topic_imp = [topic for topic in topic_list if topic[2] == 'IT Assessment']
    # topic_imp = [(t1 + (t2[0],)) for (t1, t2) in list(zip(*[topic_list[i:] for i in range(2)])) if t1[2] ==  'IT Assessment']
    topic_imp = []
    for i in range(len(topic_list)):
      if topic_list[i][2] == self.topic:
        topic_imp.append(topic_list[i])
        if (i < len(topic_list) - 1):
          nextLine = topic_list[i+1][0]
        else:
          nextLine = None
        topic_imp[0] += (nextLine,)
    data = [os.path.basename(filename)]
    if (len(topic_imp) == 1):
      data += list(topic_imp[0])
      subtopics = get_subtopics(self.is_subtopic, lines, data[1], data[-1])
      if (subtopics and len(subtopics) > 0):
        retval= {"file": os.path.basename(filename), "topic": self.topic, "subtopics": subtopics}
      # writer.writerow(data)
      if print_details:
        print("File: " + data[0])
        print("%s%s" % (' ' * 10, self.topic + " Subtopics"))
        print("%s%s" % (' ' * 10, "-----------------------"))
        for subtopic in subtopics.keys():
          print("%s%s [%s] [Lines = %d]" % (' ' * 15, subtopic, ",".join(self.normalize(subtopic)), len(subtopics[subtopic])))
    return retval

  def get_column_names(self, subtopicPredictor):
    columns = sorted(list(set(subtopicPredictor.sorted_y)))
    return [self.topic + "_" + colname for colname in columns]
    
  def mapped_subtopics_from_file(self, filename, subtopicPredictor):
    file_subtopics = self.read_file(filename, False)
    return self.mapped_subtopics(file_subtopics['subtopics'], subtopicPredictor)

  def mapped_subtopics_from_lines(self, lines, start, end, subtopicPredictor):
    subtopics = get_subtopics(self.is_subtopic, lines, start, end)
    return self.mapped_subtopics(subtopics, subtopicPredictor)

  def empty_subtopics(self, subtopicPredictor):
    columns = self.get_column_names(subtopicPredictor)
    outdict = OrderedDict.fromkeys(columns)
    return outdict

  def mapped_subtopics(self, subtopics, subtopicPredictor):
    columns = self.get_column_names(subtopicPredictor)
    outdict = OrderedDict.fromkeys(columns)
    for subtopic, subtopic_text in subtopics.items():
      predicted, score, type = subtopicPredictor.get_subtopic(subtopic)
      colname = self.topic + "_" + predicted
      if (not outdict[colname]):
        outdict[colname] = OrderedDict()
      outdict[colname][subtopic] = NEWLINE_WITHIN_COLUMN.join(subtopic_text)
    return outdict

  def subtopic_array(self, subtopic_dict):
    return [json.dumps(val) for val in subtopic_dict.values()]

  def read_all_files(self, files, print_details=False):
    self.all_subtopics = []
    writer = csv.writer(sys.stdout)
    for filename in files:
      file_subtopics = self.read_file(filename, print_details)
      if (file_subtopics):
        self.all_subtopics.append(file_subtopics)
    return self.all_subtopics

  def print_summary(self):
    subtopics = [key for data in self.all_subtopics for key in data["subtopics"].keys()]
    subtopics_with_norm = sorted([(" ".join(self.normalize(subtopic)), subtopic) for subtopic in subtopics], key=lambda x: x[0])
    dict_by_norm = dict([(key,[v for k,v in val]) for key, val in groupby(subtopics_with_norm, key=lambda x: x[0])])
    # print(dict_by_norm)
    writer = csv.writer(sys.stdout)
    # for subtopic in sorted(subtopics, key = lambda x: x.lower()):
      # writer.writerow([subtopic, " ".join(normalize(subtopic))])
    #   writer.writerow([subtopic])
    for key in sorted(dict_by_norm.keys()):
      line = [key, ""]
      for ex in sorted(set(dict_by_norm[key])):
        line.append(ex)
      writer.writerow(line)
      # writer.writerow([key, "\n".join(dict_by_norm[key])])

def main(args):
  argsmap = parseargs(args)
  # print(args_dict)

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
  # print(summary_map)

  modelfile = argsmap.get("model")
  if (not modelfile):
    print('Model must be specified...')
    sys.exit(1)
  modelfile = modelfile[0]
  (origmap, sorted_y, vectorizer, le, grid_search) = read_model_file(modelfile)
  topics = find_topics.toc_entries(origmap)
  # print(topics)
  mapper = Mapper(origmap, sorted_y, vectorizer, le, grid_search)

  subtopicReader = SubtopicReader(topic, mapper, summary_map)
  all_subtopics = subtopicReader.read_all_files(files, 'print_detail' in argsmap.keys()) 
  if 'print_summary' in argsmap.keys():
    subtopicReader.print_summary()

if __name__ == '__main__':
  from sys import argv
  args = argv[1:]
  main(args)
  sys.exit(0)
