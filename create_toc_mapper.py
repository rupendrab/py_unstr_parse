#!/usr/bin/env python3.5

import pandas as pd
import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import preprocessing
from sklearn.linear_model.logistic import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.grid_search import GridSearchCV
import pickle

from extract_toc import parseargs

def create_mapper(mapfile, modelfile):
  data = pd.read_csv(mapfile, header=None)
  data2 = data[data[2]> '']

  X = np.array(data2[0])
  y = np.array(data2[2])
  origmap = dict(zip(X,y))
  vectorizer = TfidfVectorizer(stop_words='english')
  X_train = vectorizer.fit_transform(X)
  # print(y)

  le = preprocessing.LabelEncoder()
  sorted_y = sorted(set(y))
  le.fit(sorted_y)
  y_train = le.transform(y)


  # le.inverse_transform(0)
  pipeline = Pipeline([
      ('clf', SVC(kernel='rbf', gamma=0.01, C=100, probability=True))
  ])
  parameters = {
      'clf__gamma': (0.01, 0.03, 0.1, 0.3, 1),
      'clf__C': (0.1, 0.3, 1, 2, 10, 30)
  }
  grid_search = GridSearchCV(pipeline, parameters, n_jobs=2, verbose=1,
                            scoring='accuracy')
  grid_search.fit(X_train, y_train)
  
  predicted = grid_search.predict(X_train)
  
  print(classification_report(y_train, predicted))

  cnt_diff = 0
  for i,val in enumerate(y_train):
    if (val != predicted[i]):
      cnt_diff += 1
      print('Actual = %s, Predicted = %s' % (le.inverse_transform(val), le.inverse_transform(predicted[i])))

  print('Number of differences: %d' % cnt_diff)
  
  tosave = [origmap, sorted_y, vectorizer, le, grid_search]
  with open(modelfile, 'wb') as f:
    pickle.dump(tosave, f)
  print('Saved model to %s' % modelfile)

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  argsmap = parseargs(args)
  mapfile = argsmap.get("map")
  modelfile = argsmap.get("savemodel")
  if (not mapfile or not modelfile):
    print('Both map and savemodel must be specified...')
    sys.exit(1)
  mapfile = mapfile[0]
  modelfile = modelfile[0]
  create_mapper(mapfile, modelfile)

