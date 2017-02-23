#!/usr/bin/env python3.5

import sys
import pandas as pd
import math
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import preprocessing
from sklearn.linear_model.logistic import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.grid_search import GridSearchCV
import pickle
from operator import itemgetter

from extract_toc import parseargs
from extract_toc import analyze_topic

exceptions = [
  'sabal palm bank'
]

confidential_pattern_strings = [
  '^\s*confidential(\s*|\s+.*)$'
]

confidential_patterns = [re.compile(pat, re.IGNORECASE) for pat in confidential_pattern_strings]

def is_confidential(topic):
  for pat in confidential_patterns:
    if (pat.match(topic)):
      return True
  return False

def is_exception(topic):
  if (not topic):
    return True
  topic_word_list = re.split('\s+', topic.lower())
  topic_new = ' '.join(topic_word_list)
  for exception in exceptions:
    if exception == topic_new:
       return True
  return False

def read_model_file(modelfile):
  with open(modelfile, 'rb') as f:
    origmap, sorted_y, vectorizer, le, grid_search = pickle.load(f)
  return (origmap, sorted_y, vectorizer, le, grid_search)

def binarysearch(sorted_y, val):
  ylen = len(sorted_y)
  n = int(ylen / 2)
  start = 0
  end = ylen - 1
  while start >= 0 and end < ylen and start < ylen and end >= 0 and start < end:
    n = int((start + end + 1) / 2)
    # print(start, end, n)
    chk = sorted_y[n]
    if (val == chk):
      return True
    elif (val > chk):
       start = n + 1
    else:
       end = n - 1
  return False

def get_topic(input, mapper):
  input_formatted, sure = analyze_topic(input)
  if (is_exception(input_formatted)):
    return (input_formatted, -1.0, "exception")
  direct_match = mapper.origmap.get(input_formatted)
  if (not direct_match and input_formatted.isupper()):
    for k,v in mapper.origmap.items():
      if k.upper() == input_formatted:
         return(v, 1.0, "actual")
  if (direct_match):
    # print('Found directly from map')
    return (direct_match, 1.0, "actual")
  elif binarysearch(mapper.sorted_y, input_formatted):
    return (input_formatted, 1.0, "actual")
  elif (is_confidential(input_formatted)):
    return ("Confidential", 1.0, "predefined")
  else:
    X_test_transformed = mapper.vectorizer.transform([input_formatted])
    # print(X_test_transformed)
    predicted = mapper.grid_search.predict(X_test_transformed)
    # print(predicted)
    predicted_val = mapper.le.inverse_transform(predicted[0])
    predicted_proba = mapper.grid_search.predict_proba(X_test_transformed)
    prediction_score = predicted_proba[0].max(0)
    return (predicted_val, prediction_score, "guess")

def get_topic_with_proba(input, mapper):
  direct_match = mapper.origmap.get(input.strip())
  if (direct_match):
    print('Found directly from map')
    return direct_match
  elif binarysearch(mapper.sorted_y, input):
    return (input, "actual")
  else:
    X_test_transformed = mapper.vectorizer.transform([input])
    # print(X_test_transformed)
    dfo = mapper.grid_search.decision_function(X_test_transformed)
    print(dfo.shape)
    predicted_proba = mapper.grid_search.predict_proba(X_test_transformed)
    print(dir(grid_search))
    # print(grid_search.estimator.classes_)
    # print(mapper.grid_search.classes_)
    sorted_predicted_proba = sorted([(i, val) for i, val in enumerate(predicted_proba[0])], key=itemgetter(1), reverse=True)
    avg_x = predicted_proba[0].mean(0)
    best_match = [(i, val/avg_x) for i, val in sorted_predicted_proba if val/avg_x > 2][0]
    print(mapper.le.inverse_transform(best_match[0]))
    return (best_match, "guess")

class Mapper:
  def __init__(self, origmap, sorted_y,  vectorizer, le, grid_search):
    self.origmap = origmap
    self.sorted_y = sorted_y
    self.vectorizer = vectorizer
    self.le = le
    self.grid_search = grid_search

def translate_from_stdin(mapper):
  for line in sys.stdin:
    print(line, get_topic(line, mapper))
     
def unit_test_01(mapper):
  print(get_topic('Examination Conclusions and Comments', mapper))
  print(get_topic('Examiner '' s Comments and Conclusions', mapper))
  print(get_topic('Level 2/Medium Severity Violations', mapper))
  print(get_topic('Risk  Management Assessment', mapper))

def unit_test_02(mapper):
  print(get_topic_with_proba('Examination Conclusions and Comments', mapper))
  print(get_topic_with_proba('Examiner '' s Comments and Conclusions', mapper))
  print(get_topic_with_proba('Level 2/Medium Severity Violations', mapper))
  print(get_topic_with_proba('Risk Management Assessment', mapper))

if __name__ == '__main__':
  args = sys.argv[1:]
  argsmap = parseargs(args)
  modelfile = argsmap.get("model")
  if (not modelfile):
    print('Model must be specified...')
    sys.exit(1)
  modelfile = modelfile[0]
  (origmap, sorted_y, vectorizer, le, grid_search) = read_model_file(modelfile)
  mapper = Mapper(origmap, sorted_y, vectorizer, le, grid_search)
  # for i, val in enumerate(sorted_y):
  #   print("%d\t%s" % (i, val))
  unit_test_01(mapper)
  # unit_test_02(mapper)
  # translate_from_stdin(mapper)

