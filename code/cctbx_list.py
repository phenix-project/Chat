import os
from libtbx import group_args

def run(main_directory, max_files):
  # For each sub-directory, list all the python files recursively
  here = os.getcwd()
  all_text_dict = {}  # Dict to hold names of files as keys and text as values
  dd = {}
  os.chdir(main_directory)
  for fn in os.listdir(main_directory):
    if os.path.isdir(fn):
      directory = fn
      os.chdir(directory)
      file_list = list_python_files('.')
      os.chdir(main_directory)
      dd[directory] = file_list
  os.chdir(here)
  for directory in list(dd.keys()):
    file_list = dd[directory]
    if file_list:
      all_text_dict = read_files(
         directory, main_directory, all_text_dict,  file_list)

  # Now go through all text and write out in groups to max of max_files
  n = total_lines(all_text_dict)
  print("Total lines of code: %s" %(n))
  # See if we can get them in this size file...
  file_groups = adjust_lines_per_file(all_text_dict, n, max_files)

  # Write out the file groups
  # Start file names in .txt files with last word of main_directory
  path = main_directory.split(os.path.sep)
  while path and path[-1]=='':
    path = path[:-1]
  remove_text = os.path.sep.join(path[:-1])
  last_word = path[-1]
  print("Writing out %s .txt files with code" %(len(file_groups)))
  i = 0
  for fg in file_groups:
    i += 1
    f = open('%s_%s.txt' %(last_word,i), 'w')
    for fn, text in zip(fg.file_name_list, fg.text_list):
      local_fn = fn.replace(remove_text,"")
      if local_fn.startswith(os.path.sep):
        local_fn = local_fn[1:]
      print("\n",78*"*","\n",local_fn,"\n",78*"*","\n",text,"\n", file = f)
    f.close()

def adjust_lines_per_file(all_text_dict, n, max_files):
  """Figure out how many lines per file to fit everything in max_files"""
  lines_per_file = int(n/max_files)  #starting guess
  while lines_per_file > 1:
    file_groups =  create_file_groups(all_text_dict, lines_per_file)
    print("%s File groups with %s lines per file" %(
      len(file_groups), lines_per_file))
    if len(file_groups) <= max_files:
      break
    lines_per_file = int(lines_per_file * 1.1)
  return file_groups

def create_file_group():
  fg = group_args(group_args_type = 'file_group',
     file_name_list = [],
     file_length_list = [],
     text_list = [],
     total_length = 0)
  return fg

def create_file_groups(all_text_dict, lines_per_file):
  file_groups = []
  fg = create_file_group()
  file_groups.append(fg)

  for key in all_text_dict.keys():
    text = all_text_dict[key]
    n_lines = len(text.splitlines())
    fg_to_use = None
    for fg in file_groups:
      if fg_to_use: break
      if n_lines + fg.total_length <= lines_per_file:
        fg_to_use = fg
    if not fg_to_use:  # make a new group
      fg_to_use = create_file_group()
      file_groups.append(fg_to_use)

    fg_to_use.file_name_list.append(key)
    fg_to_use.file_length_list.append(n_lines)
    fg_to_use.text_list.append(text)
    fg_to_use.total_length += n_lines
  return file_groups




def total_lines(all_text_dict):
  n = 0
  for key in all_text_dict.keys():
    n += len(all_text_dict[key].splitlines())
  return n

def get_file_groups(file_list, directory):
  file_groups = {}
  for fn in file_list:
    spl = fn.split(os.path.sep)
    if spl[0] == '.':
      spl = spl[1:]
    if len(spl) == 1:
      dir = 'main'
      remainder = spl[0]
    else:
      dir = spl[0]
      remainder = spl[1]
    for x in spl[2:]:
      remainder = os.path.join(remainder, x)
    if not dir in list(file_groups.keys()):
      file_groups[dir] = []
    file_groups[dir].append(remainder)
  return file_groups

def read_files(directory, main_directory, all_text_dict, file_list,
       max_words_in_file = 100000):
    file_list.sort()
    for fn in file_list:
      if fn.startswith("./"):
        fn = fn[2:]
      read_fn = os.path.join(main_directory, directory, fn)
      text = open(read_fn).read()
      text_words = len(text.split())
      if text_words > max_words_in_file:
        print("Skipping file %s with %s words" %(read_fn, text_words))
      elif text_words == 0:
        print("Skipping file %s with %s words" %(read_fn, text_words))
      else:
        print("Keeping file %s with %s words" %(read_fn, text_words))
        all_text_dict[read_fn] = text
    return all_text_dict

def list_python_files(directory):
  """
  Recursively finds and lists all Python (.py) files in a given directory.

  Args:
    directory: The path to the directory to search.
  """
  file_list = []
  for root, _, files in os.walk(directory):
    for file in files:
      if file.endswith(".py"):
        file_list.append(os.path.join(root, file))
  return file_list

if __name__ == "__main__":
  import sys
  main_directory = sys.argv[1]
  if len(sys.argv)> 2:
    max_files = int(sys.argv[2])
  else:
    max_files = 300
  run(main_directory, max_files)
