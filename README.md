# Chat
Code to create sources for Phenix Chat.  Current Phenix documentation, reference material (pdf of papers), Phenix newsletters, selected documentation for atom selection and Phil

documentation:  directory containing Phenix documentation as of 2025-06-11

papers:  PDF versions of many papers describing Phenix

newsletters: PDF versions of all Phenix newsletters

phil_etc: documentation on Phil and atom selections

info.txt: source describing priming the chatbot

info_for_audio.txt: Text to paste in to control the generation of default-length audio summary

videos.list:  list of youtube videos to include in documentation


HOW TO UPDATE THE DOCUMENTATION MATERIALS

The documentation PDF files were created from a nightly build Phenix documentation web site with the following
protocol:

# Work in a directory that contains crawler.py, sort_urls.py, combine.py, run_combine.csh, a.html, and b.html

# Run a web crawler to look up all the pages in this version:

python crawler.py https://phenix-online.org/version_docs/2.0-5725 urls.list >& crawler.log 

# Result is the file urls.list

# Sort the urls by category and create separate lists for each
python sort_urls.py urls.list

# Result are files with lists of urls: phenix_faqs.list	phenix_overviews.list	phenix_top_level.list
# phenix_misc.list	phenix_reference.list	phenix_tutorials.list

# Create dummy html files that contain all the web pages from each list
# Header is the file a.html, body is created from one of the files with list of urls, footer is c.html
./run_combine.csh > run_combine.log

# Result are html files that display all of the material from all the pages from one of the files 
#   with list of urls
# combine_phenix_faqs.html	combine_phenix_reference.html combine_phenix_misc.html
#  combine_phenix_top_level.html combine_phenix_overviews.html	combine_phenix_tutorials.html

# Now load each combine_phenix_xxx.html into Orion or Safari and save as PDF
# Put these files in documentation/
