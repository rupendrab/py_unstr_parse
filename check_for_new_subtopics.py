#!/usr/bin/env python3.5

import csv
from predict_using_subtopic_mapper import SubtopicPredictor
from extract_toc import parseargs

def read_and_analyze_input(predictor, guess_file=None):
  no_actual = 0
  no_guessed = 0
  inp = csv.reader(sys.stdin)
  guessed_data = []
  for row in inp:
    case = row[2]
    prediction, score, type = predictor.get_subtopic(case)
    if type == "guess":
      no_guessed += 1
      row[1] = prediction
      guessed_data.append(row)
    elif type == "actual":
      no_actual += 1
  print("Actual Map Count: %d" % no_actual)
  print("Guessed Map Count: %d" % no_guessed)
  if (no_guessed > 0):
    if guess_file:
      print("The guessed records will be written to %s, please review and if inaccurate, append to the original model determinant and re-train the model" % guess_file)
      outf = open(guess_file, 'w')
    else:
      print("The guessed records will be written below, please review and if inaccurate, append to the original model determinant and re-train the model")
      print("")
      outf = sys.stdout
    writer = csv.writer(outf)
    for r in guessed_data:
      writer.writerow(r)
    if guess_file:
      outf.close()

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  argsmap = parseargs(args)
  modelfile = argsmap.get("model")
  if (not modelfile):
    print('Model must be specified...')
    sys.exit(1)
  outfile = argsmap.get("out")
  if outfile:
    outfile = outfile[0]
  else:
    outfile = None
  modelfile = modelfile[0]
  predictor = SubtopicPredictor(modelfile)
  read_and_analyze_input(predictor, outfile)

