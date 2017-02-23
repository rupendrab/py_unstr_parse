#!/usr/bin/env python3.5

import os
import re
import random
import shutil

filenamepat = re.compile('^([a-z]+)([0-9]+)\.(.*)$', re.IGNORECASE)

def listfiles(dirname, filepattern = None):
  if filepattern:
    pat = re.compile(filepattern)
  else:
    pat = re.compile('.*')
  for filename in os.listdir(dirname):
    matched = len([m for m in pat.finditer(filename)]) > 0
    if matched:
      fullfile = os.path.join(dirname, filename)
      if os.path.isfile(fullfile):
        yield(fullfile)

def createdict(filenames):
  file_dict = {}
  for filename in filenames:
    key = os.path.basename(filename)
    file_dict[key] = filename
  return file_dict

def getrandnum(digits):
  digits_arr = [str(random.randint(0,9)) for i in range(digits)]
  return ''.join(digits_arr)
  
def newname(filename):
  m = filenamepat.match(filename)
  if m:
    prefix = m.group(1)
    suffix = m.group(2)
    ext = m.group(3)
    digits = len(suffix)
    newsuffix = getrandnum(digits)
    while (newsuffix == suffix):
      newsuffix = getrandnum(digits)
    return prefix + newsuffix + "." + ext

def create_new_file(filename, origfiles, outdir, times = 1):
  for i in range(times):
    newfilename = os.path.join(outdir, newname(filename))
    origfile = origfiles.get(filename)
    if (origfile and newfilename):
      print("cp %s %s" % (origfile, newfilename))
      shutil.copy(origfile, newfilename)

def create_new_files(origfiles, outdir, times=1):
  for filename in origfiles.keys():
    create_new_file(filename, origfiles, outdir, times)

if __name__ == '__main__':
  import sys
  args = sys.argv[1:] 
  
  dirname = None
  filepattern = None
  if (len(args) > 0):
    dirname = args[0]
  if (len(args) > 1):
    outdir = args[1]
  if (len(args) > 2):
    times = int(args[2])
  if (len(args) > 3):
    filepattern = args[3]

  if not dirname or not outdir or not times:
    sys.exit(1)

  # for file in listfiles(dirname, filepattern):
  #   print(file)
  origfiles = createdict(listfiles(dirname, filepattern))
  create_new_files(origfiles, outdir, times)
