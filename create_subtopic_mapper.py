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

class SubtopicMapper:

  def __init__(self, map_file, model_file, alg = 'svc'):
    self.map_file = map_file
    self.model_file = model_file
    self.alg = alg
    self.valid = True
    self.read_map_file()
    self.transform_X()
    self.transform_Y()
    self.create_model_framework()
    if (self.valid):
      self.generate_model()
      self.validate_model()
      self.save_model()

  def read_map_file(self):
    data = csv.reader(open(self.map_file))
    self.lines = [line for line in data]
    self.X = np.array([line[0] for line in self.lines])
    self.y = np.array([line[1] for line in self.lines])
    self.origmap = dict(zip(self.X,self.y))

  def transform_X(self):
    # self.vectorizer = TfidfVectorizer(analyzer='word', stop_words='english')
    self.vectorizer = CountVectorizer(analyzer='char_wb', ngram_range=(5, 10), min_df=1, stop_words='english')
    self.X_train = self.vectorizer.fit_transform(self.X)

  def transform_Y(self):
    self.le = preprocessing.LabelEncoder()
    self.sorted_y = sorted(set(self.y))
    self.le.fit(self.sorted_y)
    self.y_train = self.le.transform(self.y)

  def create_svc_model_framework(self):
    self.pipeline = Pipeline([
      ('clf', SVC(kernel='rbf', gamma=0.01, C=100, probability=True))
    ])

    self.parameters = {
      'clf__gamma': (0.01, 0.03, 0.1, 0.3, 1),
      'clf__C': (0.1, 0.3, 1, 2, 10, 30)
    }
    self.grid_search = GridSearchCV(self.pipeline, self.parameters, n_jobs=2, verbose=1,
                              scoring='accuracy')

  def create_rf_model_framework(self):
    self.pipeline = Pipeline([
      ('clf', RandomForestClassifier(criterion='entropy'))
    ])

    self.parameters = {
      'clf__n_estimators': (5, 10, 20, 50),
      'clf__max_depth': (50, 150, 250),
      'clf__min_samples_split': (1, 2, 3),
      'clf__min_samples_leaf': (1, 2, 3)
    }
    self.grid_search = GridSearchCV(self.pipeline, self.parameters, n_jobs=2, verbose=1,
                              scoring='precision')


  def create_model_framework(self):
    if self.alg == 'svc':
      self.create_svc_model_framework()
    elif self.alg == 'rf':
      self.create_rf_model_framework()
    else:
      sys.stderr.write('Alg must be svc or rf\n')
      self.valid = False

  def generate_model(self):
    self.grid_search.fit(self.X_train, self.y_train)

  def validate_model(self):
    self.predicted = self.grid_search.predict(self.X_train)
    print(classification_report(self.y_train, self.predicted))

    cnt_diff = 0
    for i,val in enumerate(self.y_train):
      if (val != self.predicted[i]):
        cnt_diff += 1
        print('Input = %s, Actual = %s, Predicted = %s' % (self.X[i], self.le.inverse_transform(val), self.le.inverse_transform(self.predicted[i])))
    print('Number of differences: %d' % cnt_diff)

  def save_model(self):
    tosave = [self.origmap, self.sorted_y, self.vectorizer, self.le, self.grid_search]
    with open(self.model_file, 'wb') as f:
      pickle.dump(tosave, f)
    print('Saved model to %s' % self.model_file)

def main(args):
  argsmap = parseargs(args)
  mapfile = argsmap.get("map")
  modelfile = argsmap.get("savemodel")
  if (not mapfile or not modelfile):
    print('Both map and savemodel must be specified...')
    sys.exit(1)
  mapfile = mapfile[0]
  modelfile = modelfile[0]
  alg = argsmap.get("alg")
  if(not alg):
    alg = 'svc'
  else:
    alg = alg[0]
  mapper = SubtopicMapper(mapfile, modelfile, alg)

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  main(args)

