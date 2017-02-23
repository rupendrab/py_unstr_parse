import nltk
import re

part_309_pattern_strings = [
  "(^|^.*\s+)PART 309 OF (THE )?(FDIC|FEDERAL DEPOSIT INSURANCE CORPORATION)"
]

part_309_patterns = [re.compile(p) for p in part_309_pattern_strings]

def array_upper(arr):
  return [x.upper() for x in arr]

def look_for_in_wordarray(w_arr, sent):
  file_words = array_upper(w_arr)
  words = nltk.word_tokenize(sent)
  no_words = len(words)
  file_words_n = [file_words[i:i+no_words] for i in range(len(file_words) + 1 - no_words)] 
  try:
    ind = file_words_n.index(array_upper(words))
    return ' '.join(file_words[ind-3:ind+10])
  except ValueError:
    return ''
  
def look_for_in_sentences(sents, sent):
  sents_words = [val for line in sents for val in nltk.word_tokenize(line)] 
  return look_for_in_wordarray(sents_words, sent)

def look_for_in_file(file, sent):
  f = open(file, 'r', encoding='latin1')
  data = f.read()
  f.close()
  return look_for_in_wordarray(nltk.word_tokenize(data), sent)

def has_part_309_file(file):
  sent = look_for_in_file(file, 'part 309')
  for p in part_309_patterns:
    if (p.match(sent)):
      return True
  return False

def has_part_309_sents(sents):
  sent = look_for_in_sentences(sents, 'part 309')
  for p in part_309_patterns:
    if (p.match(sent)):
      return True
  return False
