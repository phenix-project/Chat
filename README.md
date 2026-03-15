# Chat

Code and materials to create sources for Phenix user Chat, CCTBX developer chat.
For CCTBX developer chat, see cctbx_dev_docs subdirectory.

phenix_docs include current Phenix user documentation, reference material (pdf of papers), Phenix newsletters, selected documentation for atom selection and Phil

cctbx_dev_docs include CCTBX developer documentation and cctbx code


## MATERIALS

phenix_docs:

| Directory/File | Contents |
|----------------|----------|
| documentation/ | ~20 categorized PDFs of Phenix documentation |
| papers/ | PDF versions of papers describing Phenix |
| newsletters/ | PDF versions of all Phenix newsletters |
| phil_etc/ | Documentation on Phil and atom selections |
| video_transcripts/ | Video transcripts obtained from videos.list |
| info.txt | Source describing priming the chatbot |
| info_for_audio.txt | Text to control audio summary generation |
| videos.list | List of youtube videos to include |


## HOW TO CREATE PHENIX DOCUMENTATION CHAT WITH NOTEBOOKLM

1. Start a new NotebookLM project. You may need to have a paid account to be allowed to use the number
of sources present here (over 100).

2. Select "Add source" in the notebook and select and drag all the PDF files in phenix_doc/ (documentation, papers, newsletters, phil_etc), as well as info.txt on to the "+" screen that appears.

3. Individually select "Add source" and then "Add youtube video" and paste in the url for each video in phenix_doc/videos.list, one at a time.

4. To generate an audio transcript, go to the Studio tab, hit Configure, and paste the contents of info_for_audio.txt (or equivalent) into the suggestion box that guides the AI.  Then generate the audio. If you are not pleased with it, delete it and add text to the suggestions box to discourage the AI from focusing on things you do not want and to encourage it to discuss things you are interested in seeing.


## HOW TO UPDATE THE DOCUMENTATION PDFs

The documentation PDFs are generated from the local Phenix documentation tree
using `build_chat_docs.py`. This script reuses the same HTML text extraction
as the AI Agent's RAG system (`rag/document_loader.py :: PhenixHTMLLoader`).

### Quick version (one command)

```bash
# From within a PHENIX environment (auto-detects docs directory):
phenix.python $PHENIX/modules/Chat/code/build_chat_docs.py

# Or specify the docs directory explicitly:
python build_chat_docs.py --docs-dir $PHENIX/doc --output-dir ./phenix_docs/documentation/
```

### What it does

1. **Loads** all HTML and TXT files from the Phenix documentation tree
   (structured extraction: headings, paragraphs, lists, code blocks)

2. **Categorizes** each document into one of ~20 topical groups by file path

3. **Rebalances** to keep every PDF between 3 and 20 pages:
   - Large categories (e.g. overview with 96 docs) are split into parts
     (overview_part1, overview_part2, ...)
   - Tiny categories (<3 docs) are merged into a "miscellaneous" PDF

4. **Generates** one PDF per group using reportlab, with cover page,
   table of contents, and structured formatting (headings, bullets,
   code blocks)

### Options

```bash
# Specify docs directory and output location
python build_chat_docs.py --docs-dir /path/to/phenix/doc --output-dir ./documentation/

# Control PDF page limits
python build_chat_docs.py --max-pages 25     # split categories above 25 docs
python build_chat_docs.py --min-pages 5      # merge categories below 5 docs
```

### Relation to the RAG system

The `build_chat_docs.py` script and the RAG database builder
(`run_build_db.py`) share the same document loading infrastructure:

```
                  rag/document_loader.py
                  load_all_docs_from_folder()
                  PhenixHTMLLoader
                         |
              +----------+----------+
              |                     |
      run_build_db.py        build_chat_docs.py
      _custom_chunker()      categorize_by_path()
      1000-char chunks       rebalance_groups()
              |                     |
       ChromaDB vectors       ~20 PDF files
       (for RAG search)    (for NotebookLM Chat)
```


## VIDEO TRANSCRIPTS

Get a free key from supadata.ai and then use it with videos.list and
code/get_youtube_transcript.py to get transcripts.

Can get titles with code/get_youtube_title.py


## OLD PIPELINE (deprecated)

The previous pipeline used:
- `crawler.py` to crawl the web documentation site -> `urls.list`
- `sort_urls.py` to sort into 6 category lists
- `combine.py` + `run_combine.csh` to create combined HTML files
- Manual browser "Save as PDF" for each HTML file

This has been replaced by `build_chat_docs.py` which:
- Works from local files (no web crawling needed)
- Produces structured PDFs (headings, code blocks, bullets)
- Automatically splits large and merges small categories
- Runs as a single command
