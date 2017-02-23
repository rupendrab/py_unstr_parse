#!/usr/bin/env python

import sys

def sort_word(word):
  return ''.join(sorted(word)).lower()

def read_dict(dictfile):
  worddict = {}
  f = open(dictfile, 'r')
  for line in f:
    line = line[:-1]
    key = sort_word(line)
    ex = worddict.get(key)
    # print(key, ex)
    if not ex:
      worddict[key] = [line]
      # print(worddict.get(key))
    else:
      ex.append(line)
  f.close()
  print("Dictionary loaded, memory utilization = %d" % (sys.getsizeof(worddict)))
  return worddict

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  if (len(args) >= 1):
    worddict = read_dict('/usr/share/dict/words')
    cmdarg = args[0]
    if (cmdarg == "-cmd"):
      while (True):
        try:
          key1 = input("Enter characters for search: ")
          if (key1):
            words = worddict.get(sort_word(key1))
            if (words and len(words) > 0):
              print(", ".join(words))
        except EOFError as e:
          print("\nQuit")
          sys.exit(0)
        except KeyboardInterrupt as e:
          print("\nTerminated")
          sys.exit(0)
    else:
      key = sort_word(args[0])
      print(worddict.get(key))
