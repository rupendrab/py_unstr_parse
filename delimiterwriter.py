#!/usr/bin/env python3.5

class writer:

  def __init__(self, fd, CSV_FIELD_DELIMITER, CSV_LINE_TERMINATOR, fd_replaced = None):
    self.fd = fd
    self.delimiter = CSV_FIELD_DELIMITER 
    self.lineterminator = CSV_LINE_TERMINATOR
    self.fd_replaced = fd_replaced

  def to_string(self, fields):
    if (not self.fd_replaced):
      return [str(f) for f in fields]
    else:
      return [str(f).replace(self.delimiter, self.fd_replaced) for f in fields]

  def writerow(self, fields):
    if (fields):
      self.fd.write(self.delimiter.join(self.to_string(fields)))
      self.fd.write(self.lineterminator)

  def close(self):
     if (self.fd):
       try:
         self.fd.close()
       except Exception as e:
         None

if __name__ == '__main__':
  import sys
  args = sys.argv[1:]
  if (len(args) >= 2):
    if (args[0] == '-'):
      outf = sys.stdout
    else:
      outf = open(args[0], 'w')
    delimiter = args[1]
    if (len(args) == 3):
      fd_replaced = args[2]
    else:
      fd_replaced = None
    csv_writer = writer(outf, delimiter, '\r\n', fd_replaced)
    csv_writer.writerow([1, '2', '3~4'])
    csv_writer.close()
