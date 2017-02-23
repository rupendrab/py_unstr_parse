#!/usr/bin/env python3.5

import re

del_pattern_strings = [
  "\(.*\)",
  "\W[0-9]+\W",
  "U'end\\\\",
  "\s*-\s*[A-Z]+"
]

del_patterns = [re.compile(pat) for pat in del_pattern_strings]

comma_pattern = re.compile("^(.*),(.*)$")

non_word_chars = re.compile("[^a-z'.\-]", re.IGNORECASE)

dot_with_no_space = re.compile("\.([^\s])")

suffix = re.compile("^(.*[a-z\.])[, ]+(jr|sr|jr\.|sr\.|junior|senior|[IVX]+)\s*$", re.IGNORECASE)

ignore_end_pattern_strings = [
  "[ ,\-]+FDIC\s*$"
]

igonre_end_patterns = [re.compile(p) for p in ignore_end_pattern_strings]

def name_split(nm):
  nm_p = dot_with_no_space.sub(". \\1", nm)
  return re.split("\s+", nm_p)
  
def name_minus_bad_chars(nmpart):
  return non_word_chars.sub("", nmpart)

def del_bad_ends(nm):
  nm_new = nm
  for p in igonre_end_patterns:
    nm_new = p.sub('', nm_new)
  return nm_new

def separate_suffix_from_name(nm):
  nm = del_bad_ends(nm)
  m = suffix.match(nm)
  if (m):
    return (m.group(1), m.group(2))
  else:
    return (nm, "")
  
def parse_name(nm):
  first_name, middle_name, last_name, suffix = "", "", "", ""
  nm_p = nm
  for pat in del_patterns:
    nm_p = pat.sub(' ', nm_p)
  nm_p, suffix = separate_suffix_from_name(nm_p)
  nm_p = nm_p.strip()
  m = comma_pattern.match(nm_p)
  if (m):
    last_name = m.group(1).strip()
    remaining_names = name_split(m.group(2).strip())
    if (remaining_names and len(remaining_names) > 0):
      first_name = remaining_names[0]
      middle_name = ' '.join(remaining_names[1:])
  else:
    names = name_split(nm_p)
    if (len(names) == 1):
      last_name = names[0]
    elif (len(names) == 2):
      first_name = names[0]
      last_name = names[1]
    elif (len(names) >= 3):
      first_name = names[0]
      rem = names[1:]
      last_name = rem[-1]
      middle_name = ' '.join(rem[:-1])
  
  first_name = name_minus_bad_chars(first_name) 
  middle_name = name_minus_bad_chars(middle_name) 
  last_name = name_minus_bad_chars(last_name) 
  return (first_name, middle_name, last_name, suffix)

if __name__ == '__main__':
  print("\nParsed names below:")
  print(parse_name("Callie E. Matas (FDIC)"))
  print(parse_name("Janice 13 Lox^man"))
  print(parse_name("U'end\ R Posewitz"))
  print(parse_name("(EIC) Gene J. Pocase "))
  print(parse_name("Marleen Zhang (CDBO)"))
  print(parse_name("Mary Clark Connor - ODFI "))
  print(parse_name("Connor, Mary Clark - ODFI "))
  print(parse_name("Connor, Clark - ODFI "))
  print(parse_name("(EIC) Traore"))
  print(parse_name("Robin Lyn O'Connor"))
  print(parse_name("William M. Delaney"))
  
  print(parse_name("William M. Delaney, Jr."))
  print(parse_name("Charles J. Smith, III"))
  print(parse_name("John J. Alden II"))
  print(parse_name("William M. Delaney, Jr."))
  print(parse_name("Charles J. Smith, III"))
  print(parse_name("John J. Alden II"))
  print(parse_name("Alden, John J., II"))
  print(parse_name("Alden, John J. IV"))
  print(parse_name("Estela R. Gauna, FDIC"))
  print(parse_name("Christopher D. Blanchette - FDIC"))
  print(parse_name("James V. Boresani"))
  print(parse_name("David L Crenshaw, Jr. (FDIC)"))
  print(parse_name(""))

