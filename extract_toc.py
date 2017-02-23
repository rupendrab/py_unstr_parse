#!/usr/bin/env python3.5

"""
This program is used to extract TOC entries from multiple files and consolidate them into a single list

Typical Usage:

python3.5 extract_toc.py --files ../in/*.txt --details conf/details.csv --summary conf/summary.csv --distinct conf/distinct.csv
or
./extract_toc.py --files ../in/*.txt --detail conf/details.csv --summary conf/summary.csv --distinct conf/distinct.csv

--files      Specifies all the input files that need to be processed. GLOB (*) patterns are allowed

--detail     Specifies file name where detailed information regarding the extraction is to be stored.
             This files contains the following fields in a comma delimited format:
               1. File Name (no directory)
               2. Original topic from TOC
               3. Reformatted topic (trimmed spaces, eliminated multiple . characters at the end)
               4. A flag: "OK" if parser thought everything was OK, "Unsure" if the parser wasn't sure it was a valid topic

--summary    Specifies the file name where the summary information regarding the extraction is stored.
             This file has two fields in the following order:
               1. File Name (no directories)
               2. Number of TOC entries processed

--distinct   Specifies the file name where the distinct TOC entries are stored.
             This file has two fields in the following order:
               1. Formatted topic
               2. OK/Unsure flag

*** Please note that these files will be used for the subsequent stages of TOC processing.

User needs to create a map.csv file from the distinct file that will add a third column which will be the actual topic name to
be used for further processing. This is needed to eliminate duplicate entries and train a model that can classify a TOC entry into
one of these categories.
"""

import sys
import re
import os
import csv
import nltk
from nltk import word_tokenize
from nltk import pos_tag
from nltk.tag.perceptron import PerceptronTagger
from nltk.corpus import stopwords
from collections import OrderedDict

tagger = PerceptronTagger()
stop = set(stopwords.words('english'))

tocstart = re.compile("^[0-9\s]*(table\s+of\s+contents)(\s+\S+)?\s*$", re.IGNORECASE)
blanklines = [ 
  re.compile("^\s*$"),
  re.compile("\s*page\s*$", re.IGNORECASE),
  re.compile("\s*c\s*$", re.IGNORECASE),
  re.compile("\s*li\s*$", re.IGNORECASE),
]
tocline = re.compile("^\s{0,30}([A-Z].*?)([\s\._\-/:]+[l0-9IVX]*)?\s*$")
tocendpatterns = [
  re.compile('^\s*All\s+dollar\s+amounts are reported.*$', re.IGNORECASE),
  re.compile('^\s*All\s+dollar\s+amounts.*$', re.IGNORECASE),
  re.compile('^abbreviations:\s*$', re.IGNORECASE),
  re.compile('^note:\s*$', re.IGNORECASE),
  re.compile('.*dollar.*$', re.IGNORECASE),
  re.compile('.*in thousands.*$', re.IGNORECASE),
  re.compile('^\s*Dollar\s+amounts\s+in\s+thousands.*$', re.IGNORECASE),
  re.compile('^\s*Dollar\s+amounts\s+are\s+in\s+thousands.*$', re.IGNORECASE),
  re.compile('^\x0Cexamination conclusion[s]? and comment[s]?.*$', re.IGNORECASE),
  re.compile('^.*amounts in tables are shown.*$', re.IGNORECASE),
  re.compile('^\s*FFI.*$')
]
withnumber = re.compile(".*[0-9]+.*")

debug=False

def print_debug(str):
  if (debug):
    print(str)

def readfile(filename):
  for line in open(filename, 'r', encoding='latin1'):
    yield(line[:-1])

def case_type(word):
  if word.islower():
    return 0
  elif word.istitle():
    return 1
  elif word.isupper():
    return 2
  else:
    return 3

def case_type_list(words):
  if len(words) == 0:
    return 0
  if words[0] == "IT":
    if len(words) > 1:
      return case_type(words[1])
    else:
      return None
  else:
    return case_type(words[0])

def is_toc_end(line):
  for pat in tocendpatterns:
    if pat.match(line):
      return True
  return False

def is_blank_line(line):
  for pat in blanklines:
    if pat.match(line):
      return True
  return False

def get_topic(line):
  topic_match = tocline.match(line)
  if (topic_match):
    print_debug('TOC: ' + line)
    print_debug(topic_match.groups())
    topic = topic_match.groups(1)[0].strip()
    topic = re.sub("\s+'\s+", "'", topic)
    return topic

def trim_topic(topic):
  return topic

def format_topic(topic):
  topic = trim_topic(topic)

def analyze_tags(topic):
  """Use NLTK to analyze tags of the words in a topic"""
  words = word_tokenize(topic)
  tagset = 'universal'
  words_tagged = nltk.tag._pos_tag(words, tagset, tagger)
  no_tags, start_tag, end_tag, no_punctuations = 0, None, None, 0
  for word, tag in words_tagged:
    if not start_tag:
      start_tag = tag
    end_tag = tag
    no_tags += 1
    if (tag == '.'):
      no_punctuations += 1
  return(words, no_tags, start_tag, end_tag, no_punctuations) 

def remove_ending_dots(words):
  if len(words) == 0:
    return
  while len(words) > 0 and words[-1] == '.' * len(words[-1]):
    words.pop()

def analyze_topic(topic):
  """
  Analyze the topic to see if something is a problem
  Return formatted topic and problems
  """
  topic_words = re.split("\s+", topic)
  remove_ending_dots(topic_words)
  ok = True
  word_pos = 0
  for word in topic_words:
    if word_pos == 0 and word.islower():
      ok = False
    if (word == '.' or word.endswith('.')):
      ok = False
    if withnumber.match(word):
      ok = False
    word_pos += 1
    if not ok:
      break
  if len(topic_words) > 0 and topic_words[-1].lower() == 'of': ### ends with of
    ok = False
  return (' '.join(topic_words).strip(), ok)

def toc_case(toc_dict):
  # for (tf, (ok, tact)) in toc_dict.items():
  #   print(tf, ok)
  cases = [case_type_list(tf.split()[0:2]) if ok else -1 for (tf, (ok, tact)) in toc_dict.items()]
  i = -1
  streak_start = False
  streak_end = False
  prev_case = -100
  keys = list(toc_dict.keys())
  for case in cases:
    i += 1
    if case == -1: ### Ignore non-existent topics
      continue
    if not streak_start and (case == 1 or case == 2):
      streak_start = True
      prev_case = case
      continue
    if streak_start and case != prev_case:
      streak_end = True
    if streak_end:
      key = keys[i]
      (ok, tact) = toc_dict[key]
      toc_dict[key] = (False, tact)
    prev_case = case
  # print(cases)
  # for (tf, (ok, tact)) in toc_dict.items():
  #   print(tf, ok)

def read_toc(filename):
  toc_topics = []
  toc_start = False
  toc_end = False
  unsure_count = 0
  toc_dict = OrderedDict()
  extended_processing = False
  for line in readfile(filename):
    if (not toc_start):
      m = tocstart.match(line)
      if (m):
        # print(m.groups(1)[0])
        # print(line)
        toc_start = True
        print_debug('TOC Started')
    elif (not toc_end):
      print_debug(line)
      is_blank = is_blank_line(line)
      if (is_blank):
        print_debug('BLANK LINE')
        continue
      if is_toc_end(line):
        toc_end = True
        break
      topic = get_topic(line)
      if topic in toc_topics:
        toc_end = True
        break
      if (topic):
        toc_topics.append(topic)
        topic_formatted, ok = analyze_topic(topic)
        toc_dict[topic_formatted] = (False, topic.strip())
        if (not ok):
          unsure_count += 1
          if (unsure_count >= 5):
            toc_end = True
            extended_processing = True
            continue
      else:
        continue
    else:
      ## Tocs are Captured, now find out if they repeat in document
      line_n = collapse_spaces(line.strip().lower())
      for (tf, (ok,tact)) in toc_dict.items():
        if not ok:
          if compare_line_with_toc(line_n, tf.lower()) or compare_line_with_toc(line_n, tact.lower()):
            toc_dict[tf] = (True, tact)
      continue
  if extended_processing:
    toc_case(toc_dict)
    return [topic for topic in toc_topics if toc_dict[analyze_topic(topic)[0]][0]]
  else:
    return toc_topics

def eleminate_non_alnum(str):
  ret = re.sub("'", "", str)
  return collapse_spaces(re.sub('[^a-zA-Z0-9]', ' ', ret))

def remove_str_in_paren(str):
  return collapse_spaces(re.sub('\(.*\)', '', str))

def compare_line_with_toc(line, toc):
  l_line = eleminate_non_alnum(line)
  l_toc = eleminate_non_alnum(toc)
  ret = l_line.startswith(l_toc)
  if not ret:
    l_line = eleminate_non_alnum(remove_str_in_paren(line))
    l_toc = eleminate_non_alnum(remove_str_in_paren(toc))
    ret = l_line.startswith(l_toc)
  return ret

def collapse_spaces(str):
  return re.sub('\s+', ' ', str)

def read_all_toc(files):
  toc = {}
  total_files = len(files)
  files_processed = 0
  for filename in files:
    files_processed += 1
    print('Processing file: %s (%d of %d)' % (filename, files_processed, total_files))
    file_toc = read_toc(filename)
    # print('Got %d topics' % len(file_toc))
    toc[os.path.basename(filename)] = file_toc
  return toc

def toc_summary(toc, filename):
  file = None
  if filename:
    file = open(filename, 'w')
    writer = csv.writer(file)
  else:
    writer = csv.writer(sys.stdout)

  for filename in sorted(toc.keys()):
    # print("%s,%d" % (filename, len(toc[filename])))
    writer.writerow([filename] + [len(toc[filename])])

  if (file):
    file.close()
    
def ifelse(condition, true_value, false_value):
  if (condition):
    return true_value
  else:
    return false_value
  
def toc_detail(toc, filename=None):
  file = None
  if filename:
    file = open(filename, 'w')
    writer = csv.writer(file)
  else:
    writer = csv.writer(sys.stdout)

  for filename in sorted(toc.keys()):
    for topic in toc[filename]:
      topic_formatted, ok = analyze_topic(topic)
      ### Not using NLTK for this, no added value
      # words, no_tags, start_tag, end_tag, no_punctuations = analyze_tags(topic_formatted)
      # print("%s\t%s (%s, %s, %d, %d)" % (filename, topic, start_tag, end_tag, no_tags, no_punctuations))
      # if not (start_tag == 'NOUN' and end_tag == 'NOUN'):
      #   ok = False
      sure = ifelse(ok, "OK", "Unsure")
      # print("%s\t%s\t%s\t%s" % (filename, topic, topic_formatted, sure))
      writer.writerow([filename,topic,topic_formatted,sure])

  if (file):
    file.close()

def toc_unique(toc, filename=None):
  file = None
  if filename:
    file = open(filename, 'w')
    writer = csv.writer(file)
  else:
    writer = csv.writer(sys.stdout)

  toc_set = set()
  for _, topics in toc.items():
    # toc_set.update(set(topics))
    for topic in topics:
      topic_formatted, ok = analyze_topic(topic)
      sure = ifelse(ok, "OK", "Unsure")
      toc_set.add((topic_formatted, sure))
  for topic in sorted(toc_set):
    # print(topic)
    writer.writerow([topic[0], topic[1]])

  if (file):
    file.close()
    
def parseargs(args):
  args_dict = {}
  curtag = None
  curvals = []
  for i, arg in enumerate(args):
    if (arg.startswith('--')):
      if (curtag):
         args_dict[curtag] = curvals
      curtag = arg[2:]
      curvals = []
    else:
      curvals.append(arg)
  if (curtag):
    args_dict[curtag] = curvals
  return args_dict

def main(args):
  args_dict = parseargs(args)
  # print(args_dict)

  files = args_dict.get('files')
  if (not files):
    sys.exit(0)

  toc = read_all_toc(files)
     
  summary = args_dict.get('summary')
  if (summary != None):
    summary_file = None
    if len(summary) == 1:
      summary_file = summary[0] 
    toc_summary(toc, summary_file)

  detail = args_dict.get('detail')
  if (detail != None):
    detail_file = None
    if len(detail) == 1:
      detail_file = detail[0] 
    toc_detail(toc, detail_file)

  distinct = args_dict.get('distinct')
  if (distinct != None):
    unique_file = None
    if len(distinct) == 1:
      unique_file = distinct[0] 
    toc_unique(toc, unique_file)

if __name__ == '__main__':
  from sys import argv
  args = argv[1:]
  main(args)
  sys.exit(0)
