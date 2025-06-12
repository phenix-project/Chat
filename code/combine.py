import os
def run(args):

  fn = args[0]
  for line in open(fn).readlines():
    line = line.strip()
    print('<h2>%s</h2> \n' %(os.path.split(line)[-1].replace(".html","")) +
    '<iframe src="%s"></iframe>\n' %(line))


if __name__ == "__main__":
  import sys
  run(sys.argv[1:])
