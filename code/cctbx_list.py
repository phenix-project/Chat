import os

def run(main_directory, cutoff = 300):
  # For each sub-directory, list all the python files recursively
  here = os.getcwd()
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
    if not file_list: continue
    if len(file_list) < cutoff:
      print_files(directory, main_directory, None,  file_list)
    else:
      file_groups = get_file_groups(file_list, directory)
      for dir in list(file_groups.keys()):
        files = file_groups[dir]
        print_files(directory, main_directory, dir, files)

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

def print_files(directory, main_directory, sub_directory, file_list,
     max_words = 25000, max_words_in_file = 100000):
    if sub_directory is None:
      f = open("%s.txt" %(directory), 'w')
    else: # usual
      f = open("%s_%s.txt" %(directory,sub_directory), 'w')
    file_list.sort()
    words = 0
    n = 0
    for fn in file_list:
      if fn.startswith("./"):
        fn = fn[2:]
      print("\n\n",79*"*", file = f)
      if sub_directory in [None,'main']: # usual
        read_fn = os.path.join(main_directory, directory, fn)
        text = open(read_fn).read()
        print(os.path.join(directory,fn), file = f)
      else:
        read_fn = os.path.join(main_directory, directory,
             sub_directory, fn)
        text = open(read_fn).read()
        print(os.path.join(directory,sub_directory,fn), file = f)
      text_words = len(text.split())
      if text_words > max_words_in_file:
        print("Skipping file %s with %s words" %(read_fn, text_words))
      else:
        print(text, file = f)
        words += len(text.split())
      print("\n",79*"*", file = f)
      if words > max_words:  # new file
        n += 1
        words = 0
        f.close()
        if n == 1:
          f = open("%s_%s.txt" %(os.path.splitext(f.name)[0], n), 'w')
        elif n < 11:
          f = open("%s_%s.txt" %(os.path.splitext(f.name)[0][:-2], n), 'w')
        elif n < 101:
          f = open("%s_%s.txt" %(os.path.splitext(f.name)[0][:-3], n), 'w')
    f.close()

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
  run(sys.argv[1])
