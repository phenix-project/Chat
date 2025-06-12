"""sort_urls:  group urls according to function  Specific for Phenix docs"""

def is_top_level(url, top_level_kw):
  for t in top_level_kw:
    if url.find(t) > -1:
      return True
  return False

def is_skip(url, skip_kw):
  for kw in skip_kw:
    if url.find(kw) > -1:
      return True
  return False

def get_url_type(url, url_types, top_level_kw, skip_kw):
  if is_skip(url, skip_kw):
    return None
  if is_top_level(url, top_level_kw):
    return 'top_level'
  else:
    for url_type in url_types:
      if url.find(url_type) > -1:
        return url_type
  return 'misc'

def run(args):
  if len(args) != 1:
    print("python sort_urls output.dat")
    return
  fn = args[0]
  url_dict = {}
  url_types = ['top_level','faqs', 'misc', 'overviews','reference','tutorials']
  for url_type in url_types:
    url_dict[url_type] = []
  top_level_kw = ['what-is-phenix', 'phenix-modules',
     'phenix_gui', 'phenix_programs']

  skip_kw = ['phenix_index']  # just skip the index

  for url in open(fn).readlines():
     url = url.strip()
     url_type = get_url_type(url, url_types, top_level_kw, skip_kw)
     if url_type and url:
       url_dict[url_type].append(url)

  for url_type in url_types:
    url_dict[url_type].sort()

  for url_type in url_types:
    f = open("phenix_%s.list" %(url_type), "w")
    for url in url_dict[url_type]:
      print(url, file= f)
    f.close()
    print("Wrote %s urls to %s" %(len(url_dict[url_type]), f.name))


if __name__ == "__main__":
  import sys
  run(sys.argv[1:])
