#!/usr/bin/env python3.5

import sys
import re
import os
import csv
import numpy as np
from operator import itemgetter
from time import time

from extract_toc import parseargs
from predict_using_toc_mapper import Mapper, get_topic, read_model_file
from find_topics import toc_entries, get_summary_map, read_topics
import dateparser
import check_309
import parse_name
from get_ratings import Ratings, Ratings2
import delimiterwriter

from predict_using_subtopic_mapper import SubtopicPredictor
from analyze_topic import SubtopicReader
from headerutil import *

# NEWLINE_WITHIN_COLUMN = '\r\n'
# NEWLINE_WITHIN_COLUMN = '\r\n'
# CSV_LINE_TERMINATOR = '\r\n'
# CSV_FIELD_DELIMITER = ','
# FD_REPLACED = None

p_region = re.compile('(^|.*\s+)region(\s*[:\']\s*|\s+)(.*)?\s*$', re.IGNORECASE)
p_region_with_other = re.compile('(.*)?\s{5,}(certificate\s+num[bh]e[ir]|certificate|charter\s+num[bh]er|charter|field\s+offic\s*e|url)\s*:?\s*(.*)?\s*$', re.IGNORECASE)

p_blank = re.compile('^\s*$')
p_from_first_uppercase_char = re.compile('^.*?([A-Z].*)$', re.MULTILINE)

p_cert_direct = re.compile('(^|^.*\s+)(certificate\s+number)(\s*:\s*|\s+)(\w+).*$', re.IGNORECASE)
p_region_direct = re.compile('(^|^.*\s+)(region)(\s*:\s*|\s+)(\w+).*$', re.IGNORECASE)

p_patterns_str = {
  'bank_name' : [
                  'bank\s+name',
                  'institution\s+name',
                  'name'
                ],
  'bank_location': [
                     'location'
                   ],
  'examiner_in_charge': [
                          'examiner[\s\-]*in[\s\-]*charge'
                        ],
  'exam_start_date': [
                       'examination[\s\-]*start[\s\-]*date'
                     ],
  'exam_date': [
                 'examination[\s\-]*date'
               ],
  'exam_as_of_date': [
                       'examination[\s\-]*as[\s\-]*of[\s\-]*date'
                     ]
}

all_matched = {}
for k,patterns in p_patterns_str.items():
  all_matched[k] = []

p_patterns = {}
for k,patterns in p_patterns_str.items():
  p_patterns[k] = [re.compile('(^|.*\s+)' + p + '(\s*[:\'][\'\s\.]*|[\'\s\.]+)' + '(.*)?\s*$', re.IGNORECASE) for p in patterns]

def get_pattern(line, pat):
  ret = []
  for i, p in enumerate(p_patterns[pat]):
    quality = 0
    m = p.match(line)
    if (m):
      st = m.group(1)
      sep = m.group(2)
      val = m.group(3)
      vals = re.split('\s{5,}', val)
      val = vals[0]
      if (not st.strip()):
        quality += 1 ## Higher quality for line starting pattern
      else:
        if (len(st) - len(st.rstrip()) < 2): ## Just one space
          # quality -= 1
          quality -= 0 ## Ignore this one for now
      if (sep.strip() ==':'):
        quality += 1 ## Higher qiuality in presence of :
      if (len(vals) == 1):
        quality += 1
      ret.append((p_patterns_str[pat][i], val, quality))
  return ret

def match_pattern(line, pat):
  global all_matched
  all_matched[pat] += get_pattern(line, pat)

def match_all_patterns(line):
  for pat in p_patterns.keys():
    match_pattern(line, pat)

"""
def best_match(pat):
  # print('In best match', pat)
  all_m = all_matched.get(pat)
  if (all_m):
    l = sorted(all_matched.get(pat), key=lambda x: (-1 * p_patterns_str[pat].index(x[0]), x[2]), reverse=True)
    # print('Best match sorted list', l)
    if (l):
      if (l[0][2] > 0): ## Quality more than zero
        return l[0]
"""

def best_match(pat, validationfn = None):
  # print('In best match', pat)
  all_m = all_matched.get(pat)
  if (all_m):
    l = sorted(all_matched.get(pat), key=lambda x: (-1 * p_patterns_str[pat].index(x[0]), x[2]), reverse=True)
    # print('Best match sorted list', l)
    if (l):
      if (validationfn):
        for item in l:
          if (item[2] >= 0 and validationfn(item[1])): ## Quality more than zero
            return item
      else:
        if (l[0][2] >= 0): ## Quality more than zero
          return l[0]

"""
def best_match_text(pat):
  bm_tuple = best_match(pat)
  if (bm_tuple and len(bm_tuple) == 3):
    return bm_tuple[1]
  else:
    return ""
"""

def best_match_text(pat, validationfn = None):
  bm_tuple = best_match(pat, validationfn)
  if (bm_tuple and len(bm_tuple) == 3):
    return bm_tuple[1]
  else:
    return ""

def format_eic(eic_name):
  if (not eic_name):
    return eic_name
  words = re.split('\s+', eic_name)
  new_eic = []
  for i, word in enumerate(words):
    if word.endswith(';'):
      new_eic += [word[:-1]]
      break
    if word[0].islower():
      break
    new_eic += [word]
  return ' '.join(new_eic)

def format_date(dt):
  if (not dt):
    return dt
  parts = re.split('\s{3,}', dt)
  if (len(parts) >= 1):
    return parts[0]
  else:
    return ""

def get_cert_from_line(line):
  if not line:
    return "";
  m = p_cert_direct.match(line)
  if m:
    return m.group(4)
  else:
    return ""

def readfile(filename):
  for line in open(filename, 'r', encoding='latin1'):
    yield(line[:-1])

def remove_punct(str):
  return re.sub(r'[^\w\s]','',str).strip()

def format_cert_number(cert):
  return remove_punct(cert)

def format_region(region):
  if not region:
    return region
  split_by_extra_spaces = re.split('\s{5,}', remove_punct(region))
  return split_by_extra_spaces[0]

def format_bank_str(str):
  if not str:
    return str
  m = p_from_first_uppercase_char.match(str.strip())
  if (m):
    return singlespace(m.group(1))
  else:
    return singlespace(str)

def singlespace(sent):
  return ' '.join(re.split('\s+', sent))

def separate_cert(str):
  cert = ""
  newstr = str
  m_str_with_other = p_region_with_other.match(str)
  if (m_str_with_other):
    newstr = m_str_with_other.group(1)
    if m_str_with_other.group(2).lower() == "charter" and m_str_with_other.group(3).lower() == "bank":
      return str, cert
    if (m_str_with_other.group(2).strip().lower().startswith('certificate')):
      cert = m_str_with_other.group(3)
  return newstr, cert

def prev_nonblank_line(lines, lineno):
  # print('In prev_nonblank_line', lineno, len(lines))
  while lineno > 0:
    lineno -= 1
    line = lines[lineno]
    if (p_blank.match(line)):
      continue
    else:
      # print("Non Blank Line = ", line)
      return lineno, line
  return -1, ""

def init_all_matched():
  for k,patterns in p_patterns_str.items():
    all_matched[k] = []

def get_header_for_file(filename):
  # global all_matched
  init_all_matched()
  region = ""
  cert = ""
  bank_name = ""
  bank_location = ""
  lines = []
  lineno = 0
  ff = chr(12)
  prev_region_match_quality = 0
  for line in readfile(filename):
    # if line and ord(line[0]) == 12: ## Line starts with control-L
    #  line = line[1:]
    if line: ## Delete all form feed characters
      line = line.replace(ff, "")
      # line = re.sub('\s+', ' ', line) ## Compress multile spaces to a single space character
    lines += [line]
    match_all_patterns(line)
    m_region = p_region.match(line)
    if (m_region):
      if (m_region.group(1).strip() == ""):
        if (m_region.group(2).strip() == ":"):
          region_match_quality = 3
        else:
          region_match_quality = 2
      else:
        region_match_quality = 1
      if (region_match_quality >= prev_region_match_quality):
        prev_region_match_quality = region_match_quality
        region = m_region.group(3)
        # print("Region = ", region)
        region, certx = separate_cert(region)
        if (not cert):
          cert = certx
        # print("Evaluating previous lines:", line)
        if (m_region.group(1).strip() == ""):
          location_line, bank_location = prev_nonblank_line(lines, lineno)
          bank_location, cert2 = separate_cert(bank_location)
          if (not cert):
            cert = cert2
          bank_line, bank_name = prev_nonblank_line(lines, location_line)
          # print("Bank Name = ", bank_name)
          bank_name, cert2 = separate_cert(bank_name)
          if (not cert):
            cert = cert2
          # print("Bank Name = ", bank_name)
    if (not cert):
      cert = get_cert_from_line(line)
    lineno += 1
  # print(all_matched)
  if (not bank_name):
    bank_name = best_match_text('bank_name')
  if (not bank_location):
    bank_location = best_match_text('bank_location')
  examiner_in_charge = format_eic(best_match_text('examiner_in_charge'))
  eic_first_name, eic_middle_name, eic_last_name, eic_suffix = parse_name.parse_name(examiner_in_charge)
  exam_start_date = format_date(best_match_text('exam_start_date', dateparser.get_date))
  if (not exam_start_date):
    exam_start_date = format_date(best_match_text('exam_date', dateparser.get_date))
  exam_start_year, exam_start_month, exam_start_day, exam_start_date_formatted = dateparser.get_year_month_day(exam_start_date)
  exam_as_of_date = format_date(best_match_text('exam_as_of_date', dateparser.get_date))
  exam_as_of_year, exam_as_of_month, exam_as_of_day, exam_as_of_date_formatted = dateparser.get_year_month_day(exam_as_of_date)
  return (lines, 
         format_region(region).title().replace(' ', '_'), 
         format_cert_number(cert), 
         format_bank_str(bank_name).replace(' ', '_'), 
         format_bank_str(bank_location), 
         eic_first_name,
         eic_middle_name,
         eic_last_name,
         exam_start_date_formatted,
         exam_start_year, exam_start_month,
         exam_as_of_date_formatted,
         exam_as_of_year, exam_as_of_month)

def multiply_array(arr, factor):
  if (factor > 1):
    subscript = True
  else:
    subscript = False

  if subscript:
    return [newval + '_' + str(i+1) for subarr in [[val] * factor for val in arr] for i,newval in enumerate(subarr)] 
  else:
    return [newval for subarr in [[val] * factor for val in arr] for i,newval in enumerate(subarr)] 

def format_headercol(header):
  header_new = re.sub('[\-\/]', ' ', header)
  header_new = re.sub('\'', '', header_new)
  header_new = re.sub(' +', '_', header_new)
  return header_new

def replace_list(orig, start, end, new):
  orig[start:end] = new

def find_in_list(lst, pattern):
  p = re.compile("^" + pattern + "_?[0-9]*$", re.IGNORECASE)
  inds = [i for i,val in enumerate(lst) if p.match(val)]
  if (inds and len(inds) > 0):
    return (inds[0], inds[-1] + 1)

def get_headers_for_files(files, topics, mapper, summary_map, outfile, exfile, nosplit, topic_split_times, ratings, smodels = None, stopics = None):
  if (not outfile):
    if (len(CSV_FIELD_DELIMITER) == 1):
      writer = csv.writer(sys.stdout, delimiter = CSV_FIELD_DELIMITER, lineterminator = CSV_LINE_TERMINATOR)
    else:
      writer = delimiterwriter.writer(sys.stdout, CSV_FIELD_DELIMITER, CSV_LINE_TERMINATOR, FD_REPLACED)
  else:
    outf = open(outfile, 'w')
    if (len(CSV_FIELD_DELIMITER) == 1):
      writer = csv.writer(outf, delimiter = CSV_FIELD_DELIMITER, lineterminator = CSV_LINE_TERMINATOR)
    else:
      writer = delimiterwriter.writer(outf, CSV_FIELD_DELIMITER, CSV_LINE_TERMINATOR, FD_REPLACED)

  exf = open(exfile, 'w')

  headerline = [
                 'serial_no',
                 'file_name',
                 'region',
                 'certificate_number',
                 'bank_name',
                 'bank_location',
                 'examiner_in_charge_first_name',
                 'examiner_in_charge_middle_name',
                 'examiner_in_charge_last_name',
                 'exam_start_date',
                 'exam_start_year',
                 'exam_start_month',
                 'exam_as_of_date',
                 'exam_as_of_year',
                 'exam_as_of_month'
               ]

  headerline += ratings.get_column_headers()

  topic_start_index = len(headerline)
  # topic_split_times = 4
  topics.append('Confidential')
  if (nosplit):
    headerline += topics
  else:
    headerline += multiply_array(topics, topic_split_times)
  # headerline_no_spaces = [headercol.replace(' ', '_') for headercol in headerline]

  smodelfile=None
  stopic=None

  if (smodels and len(smodels) > 0):
    smodelfile= smodels[0]
  if (stopics and len(stopics) > 0):
    stopic= stopics[0]
  # smodelfile = "model_sub_svc.pkl"
  # stopic = "IT Assessment"
  # print("smodelfile = %s, stopic = %s" % (smodelfile, stopic))

  if smodelfile:
    subtopicReader = SubtopicReader(stopic, mapper, summary_map)
    subtopicPredictor = SubtopicPredictor(smodelfile)
    subtopic_columns = subtopicReader.get_column_names(subtopicPredictor)
    stcol_start, stcol_end = find_in_list(headerline, stopic)
    headerline[stcol_start:stcol_end] = subtopic_columns

  headerline_no_spaces = [format_headercol(headercol) for headercol in headerline]
  writer.writerow(headerline_no_spaces)
 
  serial=0
  start_time = time()
  for filename in files:
    file_time = time()
    # print("Processing file %s at %f" % (filename, (file_time - start_time)))
    filedata = get_header_for_file(filename)
    file_time = time()
    # print("Processing file %s at %f" % (filename, (file_time - start_time)))
    rowdata = [os.path.basename(filename)]
    lines = filedata[0]

    ## Only write to exception file if part 309 is not present
    # if not check_309.has_part_309_sents(lines):
    #   exf.write(os.path.abspath(filename) + '\r\n')
    #   continue

    # print(summary_map)
    no_topics = summary_map.get(os.path.basename(filename))
    # print("No Topics", no_topics)
    guess_allowed = False
    if (not no_topics or no_topics == 0):
      guess_allowed = True
    topic_list = read_topics(filename, mapper, guess_allowed)
    # print(topic_list)
    if nosplit:
      topic_data = ["" for i in range(len(topics))]
    else:
      topic_data = ["" for i in range(len(topics) * topic_split_times)]
    # print("Topic Data length", len(topic_data))
    no_topics_in_doc = len(topic_list)
    if smodelfile:
      stcol_topic_start, stcol_topic_end = find_in_list(topics, stopic)
      if (not nosplit):
        ## Readjust for split columns
        stcol_topic_start = stcol_topic_start * topic_split_times
        stcol_topic_end = stcol_topic_start + topic_split_times

    stopic_start_line, stopic_end_line = None,None

    for i, topic_line in enumerate(topic_list):
      start_line = topic_line[0]
      if (i < no_topics_in_doc -1):
        end_line = topic_list[i+1][0]
        if nosplit:
          topic_text = NEWLINE_WITHIN_COLUMN.join(lines[start_line:end_line])
        else:
          topic_texts_split = break_into_pieces(lines[start_line:end_line], NEWLINE_WITHIN_COLUMN)
      else:
        end_line = None
        if nosplit:
          topic_text = NEWLINE_WITHIN_COLUMN.join(lines[start_line:])
        else:
          topic_texts_split = break_into_pieces(lines[start_line:], NEWLINE_WITHIN_COLUMN)
      topic_name = topic_line[2]
      topic_index = topics.index(topic_name)
      if nosplit:
        topic_data[topic_index] = topic_text
        # topic_data[topic_index] = topic_text[:32000]
      else:
        if (len(topic_texts_split) > topic_split_times):
          print('Problem in file %s for topic %s, number of splits needed is %d' % (os.path.basename(filename), topic_name, len(topic_texts_split)))
        for topic_subindex in range(len(topic_texts_split)):
          # print('Setting:', topic_index, topic_index * topic_split_times + topic_subindex)
          topic_data[topic_index * topic_split_times + topic_subindex] = topic_texts_split[topic_subindex]
      ## Handle Subtopics
      if smodelfile and topic_name == stopic:
         stopic_start_line, stopic_end_line = start_line, end_line

      # topic_data[topic_index] = topic_text[:300]
      # if (len(topic_text) > 32000):
      # print(rowdata[0], topic_name, topic_index, len(topic_text))
      # if (len(topic_text) > 32000):
      #   print(topic_text)
      # print(topic_name, topic_index)
      # print('======================================================')
      # print(topic_text)

    if smodelfile:
      ## If Subtopic lines exit
      if stopic_start_line:
        subtopics_dict = subtopicReader.mapped_subtopics_from_lines(lines, stopic_start_line, stopic_end_line, subtopicPredictor)
        subtopics_arr = subtopicReader.subtopic_array(subtopics_dict)
        topic_data[stcol_topic_start:stcol_topic_end] = subtopics_arr
      else:
        topic_data[stcol_topic_start:stcol_topic_end] = subtopicReader.empty_subtopics(subtopicPredictor)

    serial += 1
    rowdata.insert(0, serial)
    rowdata += filedata[1:]

    ratings.process_file(filename)
    ratings.map_ratings()
    rowdata += ratings.get_column_data()

    rowdata += topic_data
    writer.writerow(rowdata)

  if (outfile):
    outf.close()

  if (exf):
    exf.close()

def break_into_pieces(lines, newlinechar, chunksize=32000):
  fields = []
  field = ""
  fieldlen = 0
  newlinelen = len(newlinechar)
  for i, line in enumerate(lines):
    if (fieldlen + len(line) + newlinelen) > chunksize:
      fields.append(field)
      field = ""
      fieldlen = 0
    if (field):
      field += newlinechar
    field += line
    fieldlen = fieldlen + len(line) + newlinelen
  if field:
    fields.append(field)
  return fields

def main(args):
  global NEWLINE_WITHIN_COLUMN
  argsmap = parseargs(args)

  files = argsmap.get('files')
  if (not files):
    sys.exit(0)

  summaryfile = argsmap.get("summary")
  if (not summaryfile or len(summaryfile) == 0):
    print('Summary file must be specified...')
    sys.exit(1)
  summary_map = get_summary_map(summaryfile[0])
  # print(summary_map)

  modelfile = argsmap.get("model")
  if (not modelfile):
    print('Model must be specified...')
    sys.exit(1)
  modelfile = modelfile[0]
  (origmap, sorted_y, vectorizer, le, grid_search) = read_model_file(modelfile)
  topics = toc_entries(origmap)
  mapper = Mapper(origmap, sorted_y, vectorizer, le, grid_search)

  nosplit = argsmap.get('nosplit')
  if nosplit == []:
    nosplit = True
  else:
    nosplit = False

  if not nosplit:
    topic_split_times = argsmap.get('split')
    if (not topic_split_times):
      topic_split_times = 4
    else:
      topic_split_times = int(topic_split_times[0])
  else:
    topic_split_times = 0

  NL = argsmap.get('NL') ## Set newline character for multiline columns
  if (NL):
    NL = NL[0]
    if (NL):
      NEWLINE_WITHIN_COLUMN = NL

  outfile = argsmap.get("out")
  if (outfile):
    outfile = outfile[0]

  exfile = argsmap.get("err")
  if exfile:
    exfile = exfile[0]
  if not exfile:
    print("Exception file name must be entered using the --err option...")
    sys.exit(1)

  ratings_mapper_file = argsmap.get("rmap")
  if ratings_mapper_file:
    ratings_mapper_file = ratings_mapper_file[0]
  if not ratings_mapper_file:
    print("Ratings Mapper File file name must be entered using the --rmap option...")
    sys.exit(1)

  ratings = Ratings(ratings_mapper_file)

  global CSV_FIELD_DELIMITER
  field_delim = argsmap.get('fd')
  if field_delim:
    field_delim = field_delim[0]
    if field_delim:
      CSV_FIELD_DELIMITER = field_delim

  global FD_REPLACED
  fd_replaced = argsmap.get('fdr')
  if fd_replaced:
    fd_replaced = fd_replaced[0]
    if fd_replaced:
      FD_REPLACED = fd_replaced
  
  smodels = argsmap.get("smodels")
  stopics = argsmap.get("stopics")
  get_headers_for_files(files, topics, mapper, summary_map, outfile, exfile, nosplit, topic_split_times, ratings, smodels, stopics)


if __name__ == '__main__':
  args = sys.argv[1:]
  main(args)
