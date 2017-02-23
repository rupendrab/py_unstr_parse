import re

NEWLINE_WITHIN_COLUMN = '\r\n'
CSV_LINE_TERMINATOR = '\r\n'
CSV_FIELD_DELIMITER = ','
FD_REPLACED = None

def is_header(str):
  return all([x.isupper() or x.istitle() for x in re.split('\W+', str)])
