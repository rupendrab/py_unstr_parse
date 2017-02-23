#!/usr/bin/env python3.5

import csv
import numpy as np
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.svm import SVC
import pickle

from extract_toc import parseargs
from analyze_topic import subtopic_finder

class SubtopicPredictor:

  def __init__(self, model_file):
    self.model_file = model_file
    self.read_model_file()
    self.is_subtopic, self.pos_tag, self.normalize = subtopic_finder()

  def read_model_file(self):
    with open(self.model_file, 'rb') as f:
      self.origmap, self.sorted_y, self.vectorizer, self.le, self.grid_search = pickle.load(f)

  def binarysearch(self, val):
    ylen = len(self.sorted_y)
    n = int(ylen / 2)
    start = 0
    end = ylen - 1
    while start >= 0 and end < ylen and start < ylen and end >= 0 and start < end:
      n = int((start + end + 1) / 2)
      # print(start, end, n)
      chk = self.sorted_y[n]
      if (val == chk):
        return True
      elif (val > chk):
         start = n + 1
      else:
         end = n - 1
    return False

  def get_subtopic_actual(self, input):
    input_formatted = " ".join(self.normalize(input))
    direct_match = self.origmap.get(input_formatted)
    if (direct_match):
      return (direct_match, 1.0, "actual")
    elif self.binarysearch(input_formatted):
      return (input_formatted, 1.0, "actual")
    else:
      return None

  def get_subtopic_guess(self, input):
    input_formatted = " ".join(self.normalize(input))
    X_test_transformed = self.vectorizer.transform([input_formatted])
    predicted = self.grid_search.predict(X_test_transformed)
    predicted_val = self.le.inverse_transform(predicted[0])
    predicted_proba = self.grid_search.predict_proba(X_test_transformed)
    prediction_score = predicted_proba[0].max(0)
    return (predicted_val, prediction_score, "guess")

  def get_subtopic(self, input):
    act = self.get_subtopic_actual(input)
    if act:
      return act
    else:
      return self.get_subtopic_guess(input)

def test_cases():
  cases = [
    "Active Directory/Excessive User Access Rights",
    "Compliance with Information Security Standards"
  ]
  return cases

def run_tests(predictor):
  print("Overall Prediction")
  print("==================")
  for case in test_cases():
    prediction, score, type = predictor.get_subtopic(case)
    print("%-50s: %30s - (%d, %s)" % (case, prediction, score, type))
  print("==================")
  print("")

def run_guess_tests(predictor):
  print("Guess Prediction")
  print("==================")
  for case in test_cases():
    prediction, score, type = predictor.get_subtopic_guess(case)
    print("%-50s: %30s - (%0.3f, %s)" % (case, prediction, score, type))
  print("==================")
  print("")

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  argsmap = parseargs(args)
  modelfile = argsmap.get("model")
  if (not modelfile):
    print('Model must be specified...')
    sys.exit(1)
  modelfile = modelfile[0]
  predictor = SubtopicPredictor(modelfile)
  run_tests(predictor)
  run_guess_tests(predictor)

