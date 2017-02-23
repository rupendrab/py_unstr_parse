#!/usr/bin/env python3.5

from datetime import datetime
import re

date_pattern_strings = [
  '([0-9]{1,2})[/\-\.]([0-9]{1,2})[/\-\.]([0-9]{2})([0-9]{2})?(\s*$|\s+.*$)',
  '([a-z]+)\s+([0-9 a-z]+)\s*[/\-\.,]\s*([0-9]{2})([0-9]{2})?(\s*$|\s+.*$)',
  '[0-9]{4}'
]

date_patterns = [re.compile(p, re.IGNORECASE) for p in date_pattern_strings]

def replace_alpha_in_num(val):
  val = val.replace('Q', '0')
  val = val.replace('I', '1')
  val = val.replace('l', '1')
  val = val.replace('o', '0')
  val = val.replace('O', '0')
  return val

def get_date(str):
  str = re.sub('^\W+', '', str)
  dt = None
  for i, p in enumerate(date_patterns):
    # print(i)
    m = p.match(str)
    if (m):
      # print('Matched')
      try:
        if (i == 0): ## mm/dd/yy or mm/dd/yyyy like format
          if m.group(4):
            datestr = '%s.%s.%s%s' % (replace_alpha_in_num(m.group(1)), 
                                      replace_alpha_in_num(m.group(2)), 
                                      replace_alpha_in_num(m.group(3)), 
                                      replace_alpha_in_num(m.group(4)))
            dt = datetime.strptime(datestr, '%m.%d.%Y')
          else:
            datestr = '%s.%s.%s' % (replace_alpha_in_num(m.group(1)), 
                                    replace_alpha_in_num(m.group(2)), 
                                    replace_alpha_in_num(m.group(3)))
            dt = datetime.strptime(datestr, '%m.%d.%y')
        elif (i == 1): ## Month Day, Year like format
          month = m.group(1)
          day = re.sub('\s+', '', m.group(2))
          day = replace_alpha_in_num(day)
          day = re.sub('[a-zA-Z]', '', day)
          if (int(day) == 0):
            day = '1'
          if (m.group(4)):
            datestr = '%s %s, %s%s' % (month, 
                                       day, 
                                       replace_alpha_in_num(m.group(3)), 
                                       replace_alpha_in_num(m.group(4)))
            dt = datetime.strptime(datestr, '%B %d, %Y')
          else:
            datestr = '%s %s, %s' % (month, 
                                     day, 
                                     replace_alpha_in_num(m.group(3)))
            dt = datetime.strptime(datestr, '%B %d, %y')
        elif (i==2): ## yyyy format
          datestr = str
          dt = datetime.strptime(datestr, '%Y')
      except ValueError:
        return None
      break
  return dt
      

def get_year_month(str):
  dt = get_date(str)
  if (dt):
    return (dt.year, dt.month)
  else:
    return ("", "")

def get_year_month_day(str):
  dt = get_date(str)
  if (dt):
    return (dt.year, dt.month, dt.day, "%d/%d/%d" % (dt.month, dt.day, dt.year))
  else:
    return ("", "", "", "")


if __name__ == '__main__':
  print(get_year_month_day('--March 3Q,2015'))
  print(get_year_month_day('04/04/2011'))
  print(get_year_month_day('04/04/11'))
  print(get_year_month_day('April 06. 2015'))
  print(get_year_month_day('July 2 1. 2014'))
  print(get_year_month_day('December 08. 2014'))
  print(get_year_month_day('2015'))

