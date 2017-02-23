#!/usr/bin/env python3.5

import check_309
from get_headers import readfile
from extract_toc import parseargs
import sys
import os
import shutil
from multiprocessing import Pool

def if_mycompany(filename):
  file_lines = [line for line in readfile(filename)]
  return (os.path.abspath(filename), check_309.has_part_309_sents(file_lines))

def write(line, f):
  if f:
    f.write(line)
    f.write("\r\n")
  else:
    print(line)

def create_list(filenames, workers, outfilename = None, moveto = None):
  outfile = None
  if outfilename:
    outfile = open(outfilename, 'w')

  if moveto:
    create_dir(moveto)

  pool = Pool(processes=workers)
  output = pool.map(if_mycompany, filenames)
  non_mycompany_files = sorted([outfilename for outfilename, is_mycompany in output if not is_mycompany])
  # print(non_mycompany)
  for filename in non_mycompany_files:
    write(filename, outfile)
    if moveto:
      shutil.move(filename, moveto)
  if outfile:
    outfile.close()

def create_dir(dirname):
  os.makedirs(dirname, exist_ok=True)

def main(args):
  argsmap = parseargs(args)

  files = argsmap.get('files')
  if (not files):
    sys.exit(0)

  outfile = argsmap.get('out')
  if not outfile:
    outfile = None
  else:
    outfile = outfile[0]

  moveto = argsmap.get('moveto')
  if moveto:
    moveto = moveto[0]
  else:
    moveto = None

  workers = argsmap.get('workers')
  if workers:
    workers = int(workers[0])
  else:
    workers = 10
  
  create_list(files, workers, outfile, moveto)

if __name__ == '__main__':
  args = sys.argv[1:]
  main(args)
